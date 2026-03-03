"""State Machine Engine for career state inference."""

from datetime import datetime
from enum import Enum
from typing import Any
from dataclasses import dataclass, field

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.entity import Entity, CareerState
from src.models.signal import Signal, SignalType

logger = structlog.get_logger()


@dataclass
class StatePrediction:
    """Represents a predicted career state."""
    state: CareerState
    confidence: float
    matched_conditions: list[str] = field(default_factory=list)
    rule_name: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class StateTransition:
    """Represents a state transition event."""
    from_state: CareerState
    to_state: CareerState
    confidence: float
    timestamp: datetime
    signals: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)


class StateInferenceEngine:
    """Engine for inferring career state from signals."""

    # Inference rules mapping signals to states
    INFERENCE_RULES = [
        # Rule 1: Job hunting signals
        {
            "name": "job_hunting_profile",
            "conditions": [
                SignalType.PROFILE_UPDATED.value,
                SignalType.BIO_CHANGED.value,
            ],
            "state": CareerState.JOB_HUNTING,
            "confidence": 0.65,
            "min_matches": 1,
            "description": "Profile updates suggest job hunting",
        },
        {
            "name": "job_hunting_activity",
            "conditions": [
                SignalType.COMMIT_FREQUENCY_DROP.value,
                SignalType.INTERVIEW_PREP_COMMITS.value,
            ],
            "state": CareerState.JOB_HUNTING,
            "confidence": 0.70,
            "min_matches": 1,
            "description": "Activity pattern changes suggest job hunting",
        },
        # Rule 2: Interviewing signals
        {
            "name": "interviewing_pattern",
            "conditions": [
                SignalType.COMMIT_TIME_ANOMALY.value,
                SignalType.COMMIT_FREQUENCY_DROP.value,
                SignalType.INTERACTION_WITH_TARGET_COMPANY.value,
            ],
            "state": CareerState.INTERVIEWING,
            "confidence": 0.80,
            "min_matches": 2,
            "description": "Time anomalies and reduced activity suggest interviewing",
        },
        # Rule 3: Handing over signals
        {
            "name": "handover_signals",
            "conditions": [
                SignalType.COMMIT_FREQUENCY_SPIKE.value,
                SignalType.REPO_VISIBILITY_CHANGE.value,
            ],
            "state": CareerState.HANDING_OVER,
            "confidence": 0.70,
            "min_matches": 1,
            "description": "Activity spike may indicate handover preparation",
        },
        # Rule 4: Transitioned signals
        {
            "name": "company_change_confirmed",
            "conditions": [
                SignalType.COMPANY_CHANGED.value,
            ],
            "state": CareerState.TRANSITIONED,
            "confidence": 0.95,
            "min_matches": 1,
            "description": "Company change detected in profile",
        },
        {
            "name": "org_change_confirmed",
            "conditions": [
                SignalType.ORG_JOINED.value,
                SignalType.ORG_LEFT.value,
            ],
            "state": CareerState.TRANSITIONED,
            "confidence": 0.85,
            "min_matches": 1,
            "description": "Organization membership change detected",
        },
        # Rule 5: Stable state
        {
            "name": "stable_no_signals",
            "conditions": [],
            "state": CareerState.STABLE,
            "confidence": 0.50,
            "min_matches": 0,
            "description": "No concerning signals detected",
        },
    ]

    def __init__(self, session: AsyncSession) -> None:
        """Initialize state inference engine.

        Args:
            session: Database session.
        """
        self.session = session

    async def infer_state(
        self,
        entity_id: str,
        lookback_days: int = 30,
    ) -> StatePrediction:
        """Infer the current career state for an entity.

        Args:
            entity_id: Entity ID to analyze.
            lookback_days: Number of days to look back for signals.

        Returns:
            StatePrediction with the inferred state.
        """
        logger.info("inferring_state", entity_id=entity_id, lookback_days=lookback_days)

        # Get recent signals
        signals = await self._get_recent_signals(entity_id, lookback_days)
        signal_types = {s.signal_type for s in signals}

        # Evaluate all rules
        predictions = []

        for rule in self.INFERENCE_RULES:
            matched = []
            for condition in rule["conditions"]:
                if condition in signal_types:
                    matched.append(condition)

            if len(matched) >= rule["min_matches"]:
                coverage = len(matched) / len(rule["conditions"]) if rule["conditions"] else 1.0
                confidence = rule["confidence"] * min(coverage + 0.5, 1.0)

                predictions.append(StatePrediction(
                    state=rule["state"],
                    confidence=confidence,
                    matched_conditions=matched,
                    rule_name=rule["name"],
                    evidence={"rule_description": rule["description"]},
                ))

        # Sort by confidence and return best prediction
        if predictions:
            predictions.sort(key=lambda p: p.confidence, reverse=True)
            best = predictions[0]
            best.evidence["all_predictions"] = [
                {"state": p.state.value, "confidence": p.confidence}
                for p in predictions[:3]
            ]
            return best

        # Default to stable if no signals
        return StatePrediction(
            state=CareerState.STABLE,
            confidence=0.50,
            matched_conditions=[],
            rule_name="default_stable",
            evidence={"reason": "No significant signals detected"},
        )

    async def update_entity_state(
        self,
        entity_id: str,
        lookback_days: int = 30,
    ) -> StateTransition | None:
        """Update entity state based on signal analysis.

        Args:
            entity_id: Entity ID to update.
            lookback_days: Number of days to analyze.

        Returns:
            StateTransition if state changed, None otherwise.
        """
        # Get current entity
        entity = await self._get_entity(entity_id)
        if not entity:
            return None

        old_state = CareerState(entity.current_state) if entity.current_state else CareerState.UNKNOWN

        # Infer new state
        prediction = await self.infer_state(entity_id, lookback_days)

        # Check if state has changed
        if prediction.state != old_state and prediction.confidence >= 0.6:
            # Update entity
            entity.current_state = prediction.state.value
            entity.state_confidence = prediction.confidence
            entity.state_updated_at = datetime.utcnow()

            await self.session.flush()

            transition = StateTransition(
                from_state=old_state,
                to_state=prediction.state,
                confidence=prediction.confidence,
                timestamp=datetime.utcnow(),
                signals=prediction.matched_conditions,
                evidence=prediction.evidence,
            )

            logger.info(
                "state_transition",
                entity_id=entity_id,
                from_state=old_state.value,
                to_state=prediction.state.value,
                confidence=prediction.confidence,
            )

            return transition

        # Update confidence even if state unchanged
        entity.state_confidence = prediction.confidence
        entity.state_updated_at = datetime.utcnow()
        await self.session.flush()

        return None

    async def batch_update_states(self) -> list[StateTransition]:
        """Update states for all active entities.

        Returns:
            List of state transitions.
        """
        logger.info("batch_updating_states")

        query = select(Entity).where(Entity.is_active == True)
        result = await self.session.execute(query)
        entities = list(result.scalars().all())

        transitions = []
        for entity in entities:
            transition = await self.update_entity_state(entity.id)
            if transition:
                transitions.append(transition)

        logger.info(
            "batch_update_complete",
            total_entities=len(entities),
            transitions=len(transitions),
        )

        return transitions

    async def _get_entity(self, entity_id: str) -> Entity | None:
        """Get entity by ID."""
        query = select(Entity).where(Entity.id == entity_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def _get_recent_signals(
        self,
        entity_id: str,
        days: int,
    ) -> list[Signal]:
        """Get recent signals for an entity."""
        from datetime import timedelta

        start_date = datetime.utcnow() - timedelta(days=days)

        query = (
            select(Signal)
            .where(Signal.entity_id == entity_id)
            .where(Signal.detected_at >= start_date)
            .order_by(Signal.detected_at.desc())
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_state_summary(self, entity_id: str) -> dict[str, Any]:
        """Get comprehensive state summary for an entity.

        Args:
            entity_id: Entity ID.

        Returns:
            State summary dictionary.
        """
        entity = await self._get_entity(entity_id)
        if not entity:
            return {"error": "Entity not found"}

        prediction = await self.infer_state(entity_id)

        return {
            "entity_id": entity_id,
            "name": entity.name,
            "current_state": entity.current_state,
            "state_confidence": entity.state_confidence,
            "state_updated_at": entity.state_updated_at.isoformat() if entity.state_updated_at else None,
            "inferred_state": prediction.state.value,
            "inference_confidence": prediction.confidence,
            "matched_signals": prediction.matched_conditions,
            "rule_name": prediction.rule_name,
            "current_company": entity.current_company,
            "current_title": entity.current_title,
        }
