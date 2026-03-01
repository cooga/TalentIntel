"""GitHub Monitor for automated event monitoring and change detection."""

import hashlib
from datetime import datetime
from typing import Any

import structlog
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.collectors.github import (
    GitHubCollector,
    GitHubProfile,
    GitHubEvent,
    GitHubAPIError,
    NotFoundError,
    RateLimitError,
)
from src.models.entity import Entity
from src.models.event import Event, EventType, EventCreate
from src.models.platform_snapshot import PlatformSnapshot, SnapshotCreate
from src.models.signal import SignalType

logger = structlog.get_logger()


class GitHubMonitor:
    """Monitor for GitHub profiles and events with change detection."""

    def __init__(self, session: AsyncSession, collector: GitHubCollector | None = None) -> None:
        """Initialize GitHub monitor.

        Args:
            session: Database session.
            collector: Optional GitHub collector instance.
        """
        self.session = session
        self.collector = collector or GitHubCollector()

    async def close(self) -> None:
        """Close the collector connection."""
        await self.collector.close()

    async def monitor_entity(self, entity: Entity) -> dict[str, Any]:
        """Monitor a single entity's GitHub activity.

        Args:
            entity: Entity to monitor.

        Returns:
            Dictionary with monitoring results.
        """
        if not entity.github_username:
            return {
                "entity_id": entity.id,
                "status": "skipped",
                "reason": "no_github_username",
            }

        logger.info(
            "monitoring_entity",
            entity_id=entity.id,
            github_username=entity.github_username,
        )

        result = {
            "entity_id": entity.id,
            "github_username": entity.github_username,
            "status": "success",
            "profile_changes": [],
            "new_events": 0,
            "signals": [],
        }

        try:
            # Get previous snapshot
            previous_snapshot = await self._get_latest_snapshot(entity.id)

            # Fetch current profile
            etag = previous_snapshot.etag if previous_snapshot else None
            profile, new_etag = await self.collector.fetch_profile(
                entity.github_username, etag=etag
            )

            if profile:
                # Detect changes
                changes = self.collector.detect_changes(
                    profile,
                    previous_snapshot.snapshot_data if previous_snapshot else None,
                )

                # Save new snapshot
                await self._save_snapshot(
                    entity.id,
                    profile,
                    new_etag,
                    changes,
                )

                # Create events for changes
                for change in changes:
                    event = await self._create_change_event(entity.id, change, profile)
                    result["profile_changes"].append({
                        "field": change.field,
                        "old": change.old_value,
                        "new": change.new_value,
                    })

                    # Generate signal for significant changes
                    signal_type = self._map_change_to_signal(change)
                    if signal_type:
                        result["signals"].append({
                            "type": signal_type,
                            "field": change.field,
                            "confidence": self._calculate_change_confidence(change),
                        })

            # Fetch events
            events = await self._fetch_and_store_events(entity)
            result["new_events"] = len(events)

            logger.info(
                "entity_monitored",
                entity_id=entity.id,
                changes=len(result["profile_changes"]),
                events=result["new_events"],
            )

        except RateLimitError as e:
            logger.warning("rate_limit_exceeded", reset_time=e.reset_time)
            result["status"] = "rate_limited"
            result["error"] = str(e)

        except NotFoundError:
            logger.warning("github_user_not_found", username=entity.github_username)
            result["status"] = "not_found"

        except GitHubAPIError as e:
            logger.error("github_api_error", error=str(e))
            result["status"] = "error"
            result["error"] = str(e)

        return result

    async def monitor_all_active(self) -> list[dict[str, Any]]:
        """Monitor all active entities with GitHub usernames.

        Returns:
            List of monitoring results for each entity.
        """
        logger.info("starting_bulk_monitoring")

        # Get all active entities with GitHub usernames
        query = (
            select(Entity)
            .where(Entity.is_active == True)
            .where(Entity.github_username.isnot(None))
            .order_by(Entity.priority.desc())
        )

        result = await self.session.execute(query)
        entities = list(result.scalars().all())

        logger.info("entities_to_monitor", count=len(entities))

        results = []
        for entity in entities:
            try:
                monitor_result = await self.monitor_entity(entity)
                results.append(monitor_result)
                await self.session.commit()
            except Exception as e:
                logger.error(
                    "monitoring_failed",
                    entity_id=entity.id,
                    error=str(e),
                )
                results.append({
                    "entity_id": entity.id,
                    "status": "error",
                    "error": str(e),
                })
                await self.session.rollback()

        logger.info("bulk_monitoring_complete", total=len(results))
        return results

    async def _get_latest_snapshot(self, entity_id: str) -> PlatformSnapshot | None:
        """Get the latest snapshot for an entity.

        Args:
            entity_id: Entity ID.

        Returns:
            Latest snapshot or None.
        """
        query = (
            select(PlatformSnapshot)
            .where(PlatformSnapshot.entity_id == entity_id)
            .where(PlatformSnapshot.platform == "github")
            .order_by(desc(PlatformSnapshot.captured_at))
            .limit(1)
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def _save_snapshot(
        self,
        entity_id: str,
        profile: GitHubProfile,
        etag: str | None,
        changes: list,
    ) -> PlatformSnapshot:
        """Save a new snapshot.

        Args:
            entity_id: Entity ID.
            profile: GitHub profile data.
            etag: ETag for conditional requests.
            changes: List of detected changes.

        Returns:
            Created snapshot.
        """
        snapshot_data = profile.raw_data
        snapshot_hash = self.collector.compute_hash(snapshot_data)

        changes_dict = None
        if changes:
            changes_dict = {
                "detected_at": datetime.utcnow().isoformat(),
                "changes": [
                    {
                        "field": c.field,
                        "old_value": c.old_value,
                        "new_value": c.new_value,
                        "change_type": c.change_type,
                    }
                    for c in changes
                ],
            }

        snapshot_create = SnapshotCreate(
            entity_id=entity_id,
            platform="github",
            snapshot_data=snapshot_data,
            snapshot_hash=snapshot_hash,
            etag=etag,
            has_changes=len(changes) > 0,
            changes=changes_dict,
        )

        snapshot = PlatformSnapshot(
            entity_id=snapshot_create.entity_id,
            platform=snapshot_create.platform,
            snapshot_data=snapshot_create.snapshot_data,
            snapshot_hash=snapshot_create.snapshot_hash,
            etag=snapshot_create.etag,
            has_changes=snapshot_create.has_changes,
            changes=snapshot_create.changes,
        )

        self.session.add(snapshot)
        await self.session.flush()

        return snapshot

    async def _create_change_event(
        self,
        entity_id: str,
        change: Any,
        profile: GitHubProfile,
    ) -> Event:
        """Create an event for a detected change.

        Args:
            entity_id: Entity ID.
            change: Detected change.
            profile: GitHub profile.

        Returns:
            Created event.
        """
        event_type = self._map_change_to_event_type(change.field)

        event_create = EventCreate(
            event_type=event_type,
            entity_id=entity_id,
            payload={
                "field": change.field,
                "old_value": change.old_value,
                "new_value": change.new_value,
                "change_type": change.change_type,
            },
            source_platform="github",
            source_data={
                "username": profile.username,
                "profile_url": profile.html_url,
            },
        )

        event = Event(
            event_id=event_create.event_id,
            entity_id=event_create.entity_id,
            event_type=event_create.event_type,
            payload=event_create.payload,
            source_platform=event_create.source_platform,
            source_data=event_create.source_data,
        )

        self.session.add(event)
        await self.session.flush()

        return event

    async def _fetch_and_store_events(self, entity: Entity) -> list[GitHubEvent]:
        """Fetch and store GitHub events for an entity.

        Args:
            entity: Entity to fetch events for.

        Returns:
            List of new events.
        """
        try:
            events, _ = await self.collector.fetch_events(entity.github_username)

            new_events = []
            for gh_event in events:
                # Check if event already exists
                existing = await self._event_exists(gh_event.event_id)
                if existing:
                    continue

                # Store new event
                event = await self._store_github_event(entity.id, gh_event)
                new_events.append(event)

            return new_events

        except GitHubAPIError:
            logger.warning(
                "failed_to_fetch_events",
                entity_id=entity.id,
                username=entity.github_username,
            )
            return []

    async def _event_exists(self, event_id: str) -> bool:
        """Check if an event already exists.

        Args:
            event_id: GitHub event ID.

        Returns:
            True if event exists.
        """
        query = select(Event).where(Event.source_data["id"].as_string() == event_id).limit(1)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def _store_github_event(self, entity_id: str, gh_event: GitHubEvent) -> Event:
        """Store a GitHub event.

        Args:
            entity_id: Entity ID.
            gh_event: GitHub event data.

        Returns:
            Created event.
        """
        event_type = self._map_github_event_type(gh_event.event_type)

        event_create = EventCreate(
            event_type=event_type,
            entity_id=entity_id,
            payload={
                "github_event_id": gh_event.event_id,
                "event_type": gh_event.event_type,
                "repo": gh_event.repo,
                "payload": gh_event.payload,
            },
            source_platform="github",
            source_data=gh_event.raw_data,
        )

        event = Event(
            event_id=event_create.event_id,
            entity_id=event_create.entity_id,
            event_type=event_create.event_type,
            payload=event_create.payload,
            source_platform=event_create.source_platform,
            source_data=event_create.source_data,
        )

        self.session.add(event)
        await self.session.flush()

        return event

    def _map_change_to_event_type(self, field: str) -> EventType:
        """Map change field to event type.

        Args:
            field: Changed field name.

        Returns:
            EventType for the change.
        """
        mapping = {
            "company": EventType.GITHUB_PROFILE_CHANGED,
            "bio": EventType.GITHUB_PROFILE_CHANGED,
            "location": EventType.GITHUB_PROFILE_CHANGED,
            "name": EventType.GITHUB_PROFILE_CHANGED,
            "email": EventType.GITHUB_PROFILE_CHANGED,
            "blog": EventType.GITHUB_PROFILE_CHANGED,
        }
        return mapping.get(field, EventType.GITHUB_PROFILE_CHANGED)

    def _map_change_to_signal(self, change: Any) -> SignalType | None:
        """Map a change to a signal type.

        Args:
            change: Detected change.

        Returns:
            SignalType or None if not signal-worthy.
        """
        if change.field == "company":
            return SignalType.COMPANY_CHANGED
        elif change.field == "bio":
            return SignalType.BIO_CHANGED
        elif change.field == "location":
            return SignalType.LOCATION_CHANGED
        return None

    def _calculate_change_confidence(self, change: Any) -> float:
        """Calculate confidence score for a change.

        Args:
            change: Detected change.

        Returns:
            Confidence score (0-1).
        """
        # Company changes are high confidence signals
        if change.field == "company":
            return 0.9

        # Bio changes are medium confidence
        if change.field == "bio":
            return 0.6

        # Other changes are lower confidence
        return 0.4

    def _map_github_event_type(self, gh_event_type: str) -> EventType:
        """Map GitHub event type to our event type.

        Args:
            gh_event_type: GitHub event type string.

        Returns:
            EventType enum value.
        """
        mapping = {
            "PushEvent": EventType.GITHUB_COMMIT,
            "CreateEvent": EventType.GITHUB_REPO_CREATED,
            "DeleteEvent": EventType.GITHUB_REPO_DELETED,
            "WatchEvent": EventType.GITHUB_PROFILE_CHANGED,
            "ForkEvent": EventType.GITHUB_PROFILE_CHANGED,
            "MemberEvent": EventType.GITHUB_ORG_JOINED,
        }
        return mapping.get(gh_event_type, EventType.GITHUB_PROFILE_CHANGED)
