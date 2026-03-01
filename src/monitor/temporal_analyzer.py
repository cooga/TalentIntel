"""Temporal Analyzer for detecting time-based anomalies."""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

import structlog
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.entity import Entity
from src.models.event import Event, EventType
from src.models.signal import Signal, SignalType, SignalCreate

logger = structlog.get_logger()


class TemporalAnomaly:
    """Represents a detected temporal anomaly."""

    def __init__(
        self,
        anomaly_type: str,
        severity: float,
        description: str,
        details: dict[str, Any],
    ) -> None:
        self.anomaly_type = anomaly_type
        self.severity = severity  # 0-1, higher = more severe
        self.description = description
        self.details = details

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.anomaly_type,
            "severity": self.severity,
            "description": self.description,
            "details": self.details,
        }


class TemporalAnalyzer:
    """Analyze temporal patterns and detect anomalies."""

    # Thresholds for anomaly detection
    COMMIT_SPIKE_THRESHOLD = 3.0  # 3x baseline
    COMMIT_DROP_THRESHOLD = 0.2  # 20% of baseline
    UNUSUAL_HOUR_THRESHOLD = 0.1  # 10% activity at unusual hours
    WEEKEND_ACTIVITY_BOOST = 2.0  # 2x normal weekend activity

    def __init__(self, session: AsyncSession) -> None:
        """Initialize temporal analyzer.

        Args:
            session: Database session.
        """
        self.session = session

    async def analyze_entity(
        self,
        entity_id: str,
        lookback_days: int = 7,
    ) -> list[TemporalAnomaly]:
        """Analyze temporal patterns for an entity.

        Args:
            entity_id: Entity ID to analyze.
            lookback_days: Number of days to analyze.

        Returns:
            List of detected anomalies.
        """
        logger.info(
            "analyzing_entity_temporal",
            entity_id=entity_id,
            lookback_days=lookback_days,
        )

        # Get entity baseline
        entity = await self._get_entity(entity_id)
        if not entity:
            return []

        # Get recent events
        events = await self._get_recent_events(entity_id, lookback_days)

        if not events:
            return []

        anomalies: list[TemporalAnomaly] = []

        # Run various anomaly checks
        anomalies.extend(await self._check_commit_time_anomaly(entity, events))
        anomalies.extend(await self._check_commit_frequency_anomaly(entity, events))
        anomalies.extend(await self._check_activity_pattern_anomaly(entity, events))
        anomalies.extend(await self._check_weekend_activity_anomaly(entity, events))

        logger.info(
            "temporal_analysis_complete",
            entity_id=entity_id,
            anomalies_found=len(anomalies),
        )

        return anomalies

    async def analyze_and_create_signals(
        self,
        entity_id: str,
        lookback_days: int = 7,
    ) -> list[Signal]:
        """Analyze entity and create signals for detected anomalies.

        Args:
            entity_id: Entity ID to analyze.
            lookback_days: Number of days to analyze.

        Returns:
            List of created signals.
        """
        anomalies = await self.analyze_entity(entity_id, lookback_days)
        signals = []

        for anomaly in anomalies:
            signal_create = self._anomaly_to_signal(entity_id, anomaly)
            if signal_create:
                signal = Signal(
                    entity_id=signal_create.entity_id,
                    signal_type=signal_create.signal_type,
                    confidence=signal_create.confidence,
                    source_platform=signal_create.source_platform,
                    source_data=signal_create.source_data,
                    description=signal_create.description,
                    fingerprint=signal_create.fingerprint,
                )
                self.session.add(signal)
                signals.append(signal)

        if signals:
            await self.session.flush()

        return signals

    async def _get_entity(self, entity_id: str) -> Entity | None:
        """Get entity by ID."""
        query = select(Entity).where(Entity.id == entity_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def _get_recent_events(
        self,
        entity_id: str,
        days: int,
    ) -> list[Event]:
        """Get recent events for an entity."""
        start_date = datetime.utcnow() - timedelta(days=days)

        query = (
            select(Event)
            .where(Event.entity_id == entity_id)
            .where(Event.timestamp >= start_date)
            .order_by(Event.timestamp.asc())
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def _check_commit_time_anomaly(
        self,
        entity: Entity,
        events: list[Event],
    ) -> list[TemporalAnomaly]:
        """Check for unusual commit times.

        Args:
            entity: Entity to check.
            events: Recent events.

        Returns:
            List of time anomalies.
        """
        anomalies = []
        baseline = entity.baseline_active_hours or {}
        baseline_active_hours = set(baseline.get("active_hours", []))

        if not baseline_active_hours:
            # No baseline established yet
            return []

        # Find commits at unusual hours
        unusual_commits = []
        for event in events:
            if event.event_type not in [EventType.GITHUB_COMMIT.value, "PushEvent"]:
                continue

            commit_hour = event.timestamp.hour
            if commit_hour not in baseline_active_hours:
                unusual_commits.append({
                    "hour": commit_hour,
                    "timestamp": event.timestamp.isoformat(),
                    "event_id": event.event_id,
                })

        # Check if unusual activity is significant
        total_commits = sum(
            1 for e in events
            if e.event_type in [EventType.GITHUB_COMMIT.value, "PushEvent"]
        )

        if total_commits > 0 and len(unusual_commits) > 0:
            unusual_ratio = len(unusual_commits) / total_commits
            if unusual_ratio > self.UNUSUAL_HOUR_THRESHOLD:
                anomalies.append(TemporalAnomaly(
                    anomaly_type="commit_time_anomaly",
                    severity=min(1.0, unusual_ratio * 2),
                    description=f"Unusual commit times detected: {len(unusual_commits)} commits outside normal hours",
                    details={
                        "unusual_commits": unusual_commits,
                        "baseline_hours": sorted(baseline_active_hours),
                        "unusual_ratio": round(unusual_ratio, 3),
                    },
                ))

        return anomalies

    async def _check_commit_frequency_anomaly(
        self,
        entity: Entity,
        events: list[Event],
    ) -> list[TemporalAnomaly]:
        """Check for commit frequency anomalies.

        Args:
            entity: Entity to check.
            events: Recent events.

        Returns:
            List of frequency anomalies.
        """
        anomalies = []
        baseline = entity.baseline_commit_pattern or {}
        baseline_daily_avg = baseline.get("avg_commits_per_day", 0)

        if baseline_daily_avg == 0:
            return []

        # Calculate current daily average
        commit_events = [
            e for e in events
            if e.event_type in [EventType.GITHUB_COMMIT.value, "PushEvent"]
        ]

        if not commit_events:
            # No commits - potential drop
            if baseline_daily_avg > 0:
                anomalies.append(TemporalAnomaly(
                    anomaly_type="commit_frequency_drop",
                    severity=0.6,
                    description="No commit activity detected in analysis period",
                    details={
                        "baseline_daily_avg": baseline_daily_avg,
                        "current_commits": 0,
                    },
                ))
            return anomalies

        # Group by day
        daily_counts: dict[str, int] = defaultdict(int)
        for event in commit_events:
            date_key = event.timestamp.strftime("%Y-%m-%d")
            daily_counts[date_key] += 1

        current_daily_avg = sum(daily_counts.values()) / len(daily_counts)

        # Check for spike
        if current_daily_avg > baseline_daily_avg * self.COMMIT_SPIKE_THRESHOLD:
            anomalies.append(TemporalAnomaly(
                anomaly_type="commit_frequency_spike",
                severity=min(1.0, current_daily_avg / baseline_daily_avg / 5),
                description=f"Commit frequency spike: {current_daily_avg:.1f}/day vs baseline {baseline_daily_avg:.1f}/day",
                details={
                    "baseline_daily_avg": baseline_daily_avg,
                    "current_daily_avg": round(current_daily_avg, 2),
                    "spike_factor": round(current_daily_avg / baseline_daily_avg, 2),
                },
            ))

        # Check for drop
        elif current_daily_avg < baseline_daily_avg * self.COMMIT_DROP_THRESHOLD:
            anomalies.append(TemporalAnomaly(
                anomaly_type="commit_frequency_drop",
                severity=0.7,
                description=f"Commit frequency drop: {current_daily_avg:.1f}/day vs baseline {baseline_daily_avg:.1f}/day",
                details={
                    "baseline_daily_avg": baseline_daily_avg,
                    "current_daily_avg": round(current_daily_avg, 2),
                    "drop_percent": round((1 - current_daily_avg / baseline_daily_avg) * 100, 1),
                },
            ))

        return anomalies

    async def _check_activity_pattern_anomaly(
        self,
        entity: Entity,
        events: list[Event],
    ) -> list[TemporalAnomaly]:
        """Check for changes in activity patterns.

        Args:
            entity: Entity to check.
            events: Recent events.

        Returns:
            List of pattern anomalies.
        """
        anomalies = []
        baseline = entity.baseline_commit_pattern or {}
        baseline_days = baseline.get("days", {})

        if not baseline_days:
            return []

        # Calculate current day distribution
        day_counts: dict[int, int] = defaultdict(int)
        for event in events:
            day_counts[event.timestamp.weekday()] += 1

        total_events = sum(day_counts.values())
        if total_events == 0:
            return []

        # Compare day distributions
        current_distribution = {
            str(day): round(count / total_events * 100, 2)
            for day, count in day_counts.items()
        }

        # Calculate distribution shift
        shifts = []
        for day_str, baseline_pct in baseline_days.items():
            current_pct = current_distribution.get(day_str, 0)
            shift = abs(current_pct - baseline_pct)
            if shift > 20:  # 20% shift threshold
                shifts.append({
                    "day": day_str,
                    "baseline_pct": baseline_pct,
                    "current_pct": current_pct,
                    "shift": shift,
                })

        if shifts:
            anomalies.append(TemporalAnomaly(
                anomaly_type="activity_pattern_shift",
                severity=min(1.0, max(s["shift"] for s in shifts) / 50),
                description="Activity pattern has shifted significantly",
                details={
                    "shifts": shifts,
                    "baseline_distribution": baseline_days,
                    "current_distribution": current_distribution,
                },
            ))

        return anomalies

    async def _check_weekend_activity_anomaly(
        self,
        entity: Entity,
        events: list[Event],
    ) -> list[TemporalAnomaly]:
        """Check for unusual weekend activity.

        Args:
            entity: Entity to check.
            events: Recent events.

        Returns:
            List of weekend anomalies.
        """
        anomalies = []
        baseline = entity.baseline_commit_pattern or {}
        baseline_days = baseline.get("days", {})

        # Get baseline weekend activity (Saturday=5, Sunday=6)
        baseline_weekend = (
            baseline_days.get("5", 0) + baseline_days.get("6", 0)
        ) / 2 if baseline_days else 0

        baseline_weekday = sum(
            baseline_days.get(str(d), 0)
            for d in range(5)
        ) / 5 if baseline_days else 0

        if baseline_weekday == 0:
            return []

        # Calculate current weekend activity
        weekend_events = sum(
            1 for e in events
            if e.timestamp.weekday() in [5, 6]
        )
        weekday_events = sum(
            1 for e in events
            if e.timestamp.weekday() not in [5, 6]
        )

        total_events = len(events)
        if total_events == 0:
            return []

        current_weekend_ratio = weekend_events / total_events
        baseline_weekend_ratio = baseline_weekend / (baseline_weekday + baseline_weekend) if (baseline_weekday + baseline_weekend) > 0 else 0

        # Check for significant weekend activity increase
        if current_weekend_ratio > 0.3 and current_weekend_ratio > baseline_weekend_ratio * self.WEEKEND_ACTIVITY_BOOST:
            anomalies.append(TemporalAnomaly(
                anomaly_type="weekend_activity_increase",
                severity=min(1.0, current_weekend_ratio),
                description=f"Increased weekend activity detected: {current_weekend_ratio:.1%} of activity on weekends",
                details={
                    "current_weekend_ratio": round(current_weekend_ratio, 3),
                    "baseline_weekend_ratio": round(baseline_weekend_ratio, 3),
                    "weekend_events": weekend_events,
                    "weekday_events": weekday_events,
                },
            ))

        return anomalies

    def _anomaly_to_signal(
        self,
        entity_id: str,
        anomaly: TemporalAnomaly,
    ) -> SignalCreate | None:
        """Convert anomaly to signal.

        Args:
            entity_id: Entity ID.
            anomaly: Detected anomaly.

        Returns:
            SignalCreate or None if not signal-worthy.
        """
        signal_type_map = {
            "commit_time_anomaly": SignalType.COMMIT_TIME_ANOMALY,
            "commit_frequency_spike": SignalType.COMMIT_FREQUENCY_SPIKE,
            "commit_frequency_drop": SignalType.COMMIT_FREQUENCY_DROP,
            "activity_pattern_shift": SignalType.COMMIT_PATTERN_ANOMALY,
            "weekend_activity_increase": SignalType.COMMIT_PATTERN_ANOMALY,
        }

        signal_type = signal_type_map.get(anomaly.anomaly_type)
        if not signal_type:
            return None

        # Generate fingerprint for deduplication
        fingerprint = self._generate_fingerprint(entity_id, anomaly.anomaly_type)

        return SignalCreate(
            entity_id=entity_id,
            signal_type=signal_type,
            confidence=anomaly.severity,
            source_platform="github",
            source_data=anomaly.details,
            description=anomaly.description,
            fingerprint=fingerprint,
        )

    def _generate_fingerprint(self, entity_id: str, anomaly_type: str) -> str:
        """Generate fingerprint for deduplication.

        Args:
            entity_id: Entity ID.
            anomaly_type: Type of anomaly.

        Returns:
            Fingerprint string.
        """
        import hashlib

        # Use current date for daily deduplication
        today = datetime.utcnow().strftime("%Y-%m-%d")
        content = f"{entity_id}:{anomaly_type}:{today}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]

    async def get_recent_anomaly_summary(
        self,
        entity_id: str,
        days: int = 30,
    ) -> dict[str, Any]:
        """Get summary of recent anomalies for an entity.

        Args:
            entity_id: Entity ID.
            days: Number of days to look back.

        Returns:
            Summary of recent anomalies.
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        query = (
            select(Signal)
            .where(Signal.entity_id == entity_id)
            .where(Signal.detected_at >= start_date)
            .where(Signal.source_platform == "github")
            .order_by(Signal.detected_at.desc())
        )

        result = await self.session.execute(query)
        signals = list(result.scalars().all())

        # Group by type
        by_type: dict[str, int] = defaultdict(int)
        for signal in signals:
            by_type[signal.signal_type] += 1

        return {
            "entity_id": entity_id,
            "period_days": days,
            "total_anomalies": len(signals),
            "by_type": dict(by_type),
            "recent_high_severity": [
                {
                    "type": s.signal_type,
                    "confidence": s.confidence,
                    "detected_at": s.detected_at.isoformat(),
                    "description": s.description,
                }
                for s in signals
                if s.confidence >= 0.7
            ][:5],
        }
