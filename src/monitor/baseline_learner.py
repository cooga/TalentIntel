"""Baseline Learner for establishing normal behavior patterns."""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

import structlog
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.models.entity import Entity
from src.models.event import Event, EventType

logger = structlog.get_logger()


class BaselineLearner:
    """Learn and maintain baseline behavior patterns for entities."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize baseline learner.

        Args:
            session: Database session.
        """
        self.session = session
        self.settings = get_settings()
        self.learning_period_days = self.settings.baseline_learning_period

    async def learn_baseline(self, entity_id: str) -> dict[str, Any]:
        """Learn baseline patterns for an entity.

        Analyzes historical events to establish normal behavior patterns.

        Args:
            entity_id: Entity ID to learn baseline for.

        Returns:
            Dictionary with learned baseline data.
        """
        logger.info("learning_baseline", entity_id=entity_id)

        # Get events within learning period
        start_date = datetime.utcnow() - timedelta(days=self.learning_period_days)

        query = (
            select(Event)
            .where(Event.entity_id == entity_id)
            .where(Event.timestamp >= start_date)
            .order_by(Event.timestamp.asc())
        )

        result = await self.session.execute(query)
        events = list(result.scalars().all())

        if not events:
            logger.info("no_events_for_baseline", entity_id=entity_id)
            return self._get_empty_baseline()

        # Analyze commit patterns
        commit_pattern = await self._analyze_commit_patterns(events)

        # Analyze active hours
        active_hours = await self._analyze_active_hours(events)

        # Analyze activity frequency
        frequency = await self._analyze_activity_frequency(events)

        # Combine into baseline
        baseline = {
            "commit_pattern": commit_pattern,
            "active_hours": active_hours,
            "frequency": frequency,
            "learned_at": datetime.utcnow().isoformat(),
            "sample_size": len(events),
            "learning_period_days": self.learning_period_days,
        }

        # Update entity with baseline
        await self._update_entity_baseline(entity_id, baseline)

        logger.info(
            "baseline_learned",
            entity_id=entity_id,
            sample_size=len(events),
            commit_days=len(commit_pattern.get("days", {})),
        )

        return baseline

    async def get_baseline(self, entity_id: str) -> dict[str, Any] | None:
        """Get baseline for an entity.

        Args:
            entity_id: Entity ID.

        Returns:
            Baseline data or None.
        """
        query = select(Entity).where(Entity.id == entity_id)
        result = await self.session.execute(query)
        entity = result.scalar_one_or_none()

        if not entity:
            return None

        if entity.baseline_commit_pattern or entity.baseline_active_hours:
            return {
                "commit_pattern": entity.baseline_commit_pattern or {},
                "active_hours": entity.baseline_active_hours or {},
            }

        return None

    async def update_all_baselines(self) -> dict[str, Any]:
        """Update baselines for all active entities.

        Returns:
            Summary of baseline updates.
        """
        logger.info("updating_all_baselines")

        query = select(Entity).where(Entity.is_active == True)
        result = await self.session.execute(query)
        entities = list(result.scalars().all())

        summary = {
            "total": len(entities),
            "updated": 0,
            "failed": 0,
            "skipped": 0,
        }

        for entity in entities:
            try:
                baseline = await self.learn_baseline(entity.id)
                if baseline.get("sample_size", 0) > 0:
                    summary["updated"] += 1
                else:
                    summary["skipped"] += 1
            except Exception as e:
                logger.error(
                    "baseline_update_failed",
                    entity_id=entity.id,
                    error=str(e),
                )
                summary["failed"] += 1

        logger.info("baselines_updated", summary=summary)
        return summary

    async def _analyze_commit_patterns(self, events: list[Event]) -> dict[str, Any]:
        """Analyze commit patterns from events.

        Args:
            events: List of events to analyze.

        Returns:
            Commit pattern analysis.
        """
        # Filter commit events
        commit_events = [
            e for e in events
            if e.event_type in [EventType.GITHUB_COMMIT.value, "PushEvent"]
        ]

        if not commit_events:
            return {"days": {}, "repos": {}}

        # Analyze commits by day of week
        day_counts: dict[int, int] = defaultdict(int)
        hour_counts: dict[int, int] = defaultdict(int)
        repo_counts: dict[str, int] = defaultdict(int)

        for event in commit_events:
            # Get day of week (0 = Monday, 6 = Sunday)
            day_counts[event.timestamp.weekday()] += 1

            # Get hour
            hour_counts[event.timestamp.hour] += 1

            # Get repo
            repo = event.payload.get("repo", "unknown")
            if repo:
                repo_counts[repo] += 1

        # Normalize to percentages
        total = len(commit_events)
        day_percentages = {
            str(day): round(count / total * 100, 2)
            for day, count in day_counts.items()
        }
        hour_percentages = {
            str(hour): round(count / total * 100, 2)
            for hour, count in hour_counts.items()
        }

        return {
            "total_commits": total,
            "days": day_percentages,
            "hours": hour_percentages,
            "top_repos": dict(sorted(repo_counts.items(), key=lambda x: x[1], reverse=True)[:5]),
            "avg_commits_per_day": round(total / self.learning_period_days, 2),
        }

    async def _analyze_active_hours(self, events: list[Event]) -> dict[str, Any]:
        """Analyze active hours from events.

        Args:
            events: List of events to analyze.

        Returns:
            Active hours analysis.
        """
        if not events:
            return {"hours": {}, "peak_hours": []}

        # Count events by hour
        hour_counts: dict[int, int] = defaultdict(int)

        for event in events:
            hour_counts[event.timestamp.hour] += 1

        # Find peak hours (top 25% activity)
        total = len(events)
        threshold = total / 24 * 1.5  # Above average

        peak_hours = [
            hour for hour, count in hour_counts.items()
            if count >= threshold
        ]

        # Calculate working hours (based on activity concentration)
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
        active_hours = [h for h, _ in sorted_hours[:8]]  # Top 8 hours

        return {
            "hours": {str(h): c for h, c in hour_counts.items()},
            "peak_hours": sorted(peak_hours),
            "active_hours": sorted(active_hours),
            "total_events": total,
        }

    async def _analyze_activity_frequency(self, events: list[Event]) -> dict[str, Any]:
        """Analyze activity frequency from events.

        Args:
            events: List of events to analyze.

        Returns:
            Activity frequency analysis.
        """
        if not events:
            return {"daily_avg": 0, "weekly_pattern": {}}

        # Group events by day
        daily_counts: dict[str, int] = defaultdict(int)

        for event in events:
            date_key = event.timestamp.strftime("%Y-%m-%d")
            daily_counts[date_key] += 1

        # Calculate statistics
        counts = list(daily_counts.values())
        if not counts:
            return {"daily_avg": 0, "weekly_pattern": {}}

        avg_daily = sum(counts) / len(counts)
        max_daily = max(counts)
        min_daily = min(counts)

        # Weekly pattern (last 7 days average)
        recent_days = sorted(daily_counts.keys())[-7:]
        recent_avg = sum(daily_counts[d] for d in recent_days) / len(recent_days) if recent_days else 0

        return {
            "daily_avg": round(avg_daily, 2),
            "max_daily": max_daily,
            "min_daily": min_daily,
            "recent_weekly_avg": round(recent_avg, 2),
            "active_days": len(daily_counts),
            "total_days": self.learning_period_days,
        }

    async def _update_entity_baseline(
        self,
        entity_id: str,
        baseline: dict[str, Any],
    ) -> None:
        """Update entity with learned baseline.

        Args:
            entity_id: Entity ID.
            baseline: Learned baseline data.
        """
        query = select(Entity).where(Entity.id == entity_id)
        result = await self.session.execute(query)
        entity = result.scalar_one_or_none()

        if entity:
            entity.baseline_commit_pattern = baseline.get("commit_pattern")
            entity.baseline_active_hours = baseline.get("active_hours")
            await self.session.flush()

    def _get_empty_baseline(self) -> dict[str, Any]:
        """Get empty baseline structure.

        Returns:
            Empty baseline dictionary.
        """
        return {
            "commit_pattern": {
                "total_commits": 0,
                "days": {},
                "hours": {},
                "top_repos": {},
                "avg_commits_per_day": 0,
            },
            "active_hours": {
                "hours": {},
                "peak_hours": [],
                "active_hours": [],
                "total_events": 0,
            },
            "frequency": {
                "daily_avg": 0,
                "recent_weekly_avg": 0,
            },
            "learned_at": datetime.utcnow().isoformat(),
            "sample_size": 0,
            "learning_period_days": self.learning_period_days,
        }

    async def compare_to_baseline(
        self,
        entity_id: str,
        current_activity: dict[str, Any],
    ) -> dict[str, Any]:
        """Compare current activity to baseline.

        Args:
            entity_id: Entity ID.
            current_activity: Current activity metrics.

        Returns:
            Comparison results with anomaly scores.
        """
        baseline = await self.get_baseline(entity_id)

        if not baseline:
            return {
                "has_baseline": False,
                "anomalies": [],
            }

        anomalies = []

        # Check commit frequency deviation
        baseline_freq = baseline.get("commit_pattern", {}).get("avg_commits_per_day", 0)
        current_freq = current_activity.get("commits_today", 0)

        if baseline_freq > 0:
            deviation = (current_freq - baseline_freq) / baseline_freq
            if abs(deviation) > 0.5:  # 50% deviation
                anomalies.append({
                    "type": "commit_frequency_deviation",
                    "baseline": baseline_freq,
                    "current": current_freq,
                    "deviation_percent": round(deviation * 100, 2),
                })

        # Check for unusual active hours
        baseline_hours = set(baseline.get("active_hours", {}).get("active_hours", []))
        current_hours = set(current_activity.get("active_hours", []))

        unusual_hours = current_hours - baseline_hours
        if len(unusual_hours) > 2:
            anomalies.append({
                "type": "unusual_active_hours",
                "baseline_hours": sorted(baseline_hours),
                "unusual_hours": sorted(unusual_hours),
            })

        return {
            "has_baseline": True,
            "anomalies": anomalies,
            "baseline": baseline,
        }
