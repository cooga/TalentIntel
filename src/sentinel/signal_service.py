"""Signal Service for managing detected signals."""

from datetime import datetime, timedelta
from typing import Any

import structlog
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.signal import Signal, SignalType, SignalCreate

logger = structlog.get_logger()


class SignalService:
    """Service layer for signal operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize signal service.

        Args:
            session: Database session.
        """
        self.session = session

    async def create_signal(self, signal_create: SignalCreate) -> Signal:
        """Create a new signal.

        Args:
            signal_create: Signal creation data.

        Returns:
            Created signal.
        """
        # Check for duplicate fingerprint
        if signal_create.fingerprint:
            existing = await self._find_by_fingerprint(signal_create.fingerprint)
            if existing:
                logger.debug(
                    "signal_duplicate_skipped",
                    fingerprint=signal_create.fingerprint,
                    entity_id=signal_create.entity_id,
                )
                return existing

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
        await self.session.flush()
        await self.session.refresh(signal)

        logger.info(
            "signal_created",
            signal_id=signal.id,
            entity_id=signal.entity_id,
            signal_type=signal.signal_type,
            confidence=signal.confidence,
        )

        return signal

    async def get_signal(self, signal_id: int) -> Signal | None:
        """Get signal by ID.

        Args:
            signal_id: Signal ID.

        Returns:
            Signal if found, None otherwise.
        """
        result = await self.session.execute(
            select(Signal).where(Signal.id == signal_id)
        )
        return result.scalar_one_or_none()

    async def list_signals(
        self,
        entity_id: str | None = None,
        signal_type: SignalType | str | None = None,
        min_confidence: float | None = None,
        processed: bool | None = None,
        days: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Signal]:
        """List signals with optional filters.

        Args:
            entity_id: Filter by entity ID.
            signal_type: Filter by signal type.
            min_confidence: Minimum confidence threshold.
            processed: Filter by processed status.
            days: Only include signals from last N days.
            limit: Maximum number of results.
            offset: Offset for pagination.

        Returns:
            List of matching signals.
        """
        query = select(Signal).order_by(desc(Signal.detected_at))

        # Apply filters
        filters = []

        if entity_id:
            filters.append(Signal.entity_id == entity_id)

        if signal_type:
            if isinstance(signal_type, SignalType):
                signal_type = signal_type.value
            filters.append(Signal.signal_type == signal_type)

        if min_confidence is not None:
            filters.append(Signal.confidence >= min_confidence)

        if processed is not None:
            filters.append(Signal.is_processed == processed)

        if days is not None:
            start_date = datetime.utcnow() - timedelta(days=days)
            filters.append(Signal.detected_at >= start_date)

        if filters:
            query = query.where(and_(*filters))

        query = query.limit(limit).offset(offset)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_unprocessed_signals(
        self,
        min_confidence: float = 0.5,
        limit: int = 100,
    ) -> list[Signal]:
        """Get unprocessed signals above confidence threshold.

        Args:
            min_confidence: Minimum confidence threshold.
            limit: Maximum number of results.

        Returns:
            List of unprocessed signals.
        """
        query = (
            select(Signal)
            .where(Signal.is_processed == False)
            .where(Signal.confidence >= min_confidence)
            .order_by(desc(Signal.confidence), desc(Signal.detected_at))
            .limit(limit)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def mark_processed(
        self,
        signal_id: int,
        processed: bool = True,
    ) -> Signal | None:
        """Mark a signal as processed.

        Args:
            signal_id: Signal ID.
            processed: Processed status.

        Returns:
            Updated signal or None if not found.
        """
        signal = await self.get_signal(signal_id)
        if not signal:
            return None

        signal.is_processed = processed
        if processed:
            signal.processed_at = datetime.utcnow()

        await self.session.flush()
        await self.session.refresh(signal)

        logger.info(
            "signal_processed",
            signal_id=signal_id,
            processed=processed,
        )

        return signal

    async def mark_all_processed(
        self,
        entity_id: str | None = None,
        signal_type: str | None = None,
    ) -> int:
        """Mark all matching signals as processed.

        Args:
            entity_id: Filter by entity ID.
            signal_type: Filter by signal type.

        Returns:
            Number of signals updated.
        """
        query = select(Signal).where(Signal.is_processed == False)

        if entity_id:
            query = query.where(Signal.entity_id == entity_id)
        if signal_type:
            query = query.where(Signal.signal_type == signal_type)

        result = await self.session.execute(query)
        signals = list(result.scalars().all())

        count = 0
        now = datetime.utcnow()
        for signal in signals:
            signal.is_processed = True
            signal.processed_at = now
            count += 1

        await self.session.flush()

        logger.info(
            "signals_marked_processed",
            count=count,
            entity_id=entity_id,
            signal_type=signal_type,
        )

        return count

    async def get_signal_stats(
        self,
        entity_id: str | None = None,
        days: int = 30,
    ) -> dict[str, Any]:
        """Get signal statistics.

        Args:
            entity_id: Filter by entity ID.
            days: Number of days to include.

        Returns:
            Dictionary with signal statistics.
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        # Base query
        base_query = select(Signal).where(Signal.detected_at >= start_date)
        if entity_id:
            base_query = base_query.where(Signal.entity_id == entity_id)

        # Get all signals in period
        result = await self.session.execute(base_query)
        signals = list(result.scalars().all())

        # Calculate statistics
        total = len(signals)
        by_type: dict[str, int] = {}
        by_entity: dict[str, int] = {}
        processed_count = 0
        high_confidence_count = 0
        confidence_sum = 0.0

        for signal in signals:
            # By type
            by_type[signal.signal_type] = by_type.get(signal.signal_type, 0) + 1

            # By entity
            by_entity[signal.entity_id] = by_entity.get(signal.entity_id, 0) + 1

            # Processed
            if signal.is_processed:
                processed_count += 1

            # High confidence
            if signal.confidence >= 0.7:
                high_confidence_count += 1

            confidence_sum += signal.confidence

        return {
            "period_days": days,
            "entity_id": entity_id,
            "total_signals": total,
            "processed": processed_count,
            "unprocessed": total - processed_count,
            "high_confidence": high_confidence_count,
            "avg_confidence": round(confidence_sum / total, 3) if total > 0 else 0,
            "by_type": by_type,
            "by_entity": by_entity if not entity_id else None,
        }

    async def get_recent_high_confidence_signals(
        self,
        limit: int = 10,
    ) -> list[Signal]:
        """Get recent high confidence signals across all entities.

        Args:
            limit: Maximum number of results.

        Returns:
            List of high confidence signals.
        """
        query = (
            select(Signal)
            .where(Signal.confidence >= 0.7)
            .order_by(desc(Signal.detected_at))
            .limit(limit)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def delete_old_signals(self, days: int = 90) -> int:
        """Delete signals older than specified days.

        Args:
            days: Delete signals older than this many days.

        Returns:
            Number of signals deleted.
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        query = select(Signal).where(Signal.detected_at < cutoff_date)
        result = await self.session.execute(query)
        signals = list(result.scalars().all())

        count = 0
        for signal in signals:
            await self.session.delete(signal)
            count += 1

        await self.session.flush()

        logger.info(
            "old_signals_deleted",
            count=count,
            older_than_days=days,
        )

        return count

    async def _find_by_fingerprint(self, fingerprint: str) -> Signal | None:
        """Find signal by fingerprint.

        Args:
            fingerprint: Signal fingerprint.

        Returns:
            Signal if found, None otherwise.
        """
        result = await self.session.execute(
            select(Signal).where(Signal.fingerprint == fingerprint)
        )
        return result.scalar_one_or_none()

    async def bulk_create_signals(
        self,
        signals_data: list[SignalCreate],
    ) -> list[Signal]:
        """Create multiple signals at once.

        Args:
            signals_data: List of signal creation data.

        Returns:
            List of created signals (excluding duplicates).
        """
        created_signals = []

        for signal_create in signals_data:
            try:
                signal = await self.create_signal(signal_create)
                created_signals.append(signal)
            except Exception as e:
                logger.error(
                    "bulk_signal_create_failed",
                    entity_id=signal_create.entity_id,
                    error=str(e),
                )

        logger.info(
            "bulk_signals_created",
            requested=len(signals_data),
            created=len(created_signals),
        )

        return created_signals

    async def get_entity_signal_summary(
        self,
        entity_id: str,
        days: int = 30,
    ) -> dict[str, Any]:
        """Get signal summary for a specific entity.

        Args:
            entity_id: Entity ID.
            days: Number of days to include.

        Returns:
            Entity signal summary.
        """
        stats = await self.get_signal_stats(entity_id=entity_id, days=days)

        # Get recent signals
        recent_signals = await self.list_signals(
            entity_id=entity_id,
            limit=10,
        )

        return {
            "entity_id": entity_id,
            "stats": stats,
            "recent_signals": [
                {
                    "id": s.id,
                    "type": s.signal_type,
                    "confidence": s.confidence,
                    "description": s.description,
                    "detected_at": s.detected_at.isoformat(),
                    "is_processed": s.is_processed,
                }
                for s in recent_signals
            ],
        }
