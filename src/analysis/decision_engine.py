"""Decision Engine for talent intelligence recommendations."""

from datetime import datetime
from typing import Any
from dataclasses import dataclass, field
from enum import Enum

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.entity import Entity, CareerState
from src.analysis.key_person_analyzer import KeyPersonAnalyzer, PersonIntelligence

logger = structlog.get_logger()


class RecommendationType(str, Enum):
    """Types of recommendations."""
    MONITOR_CLOSER = "monitor_closer"
    REACH_OUT = "reach_out"
    ALERT_MANAGER = "alert_manager"
    NO_ACTION = "no_action"
    UPDATE_INFO = "update_info"
    SCHEDULE_CHECK = "schedule_check"


class Priority(str, Enum):
    """Priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Recommendation:
    """A decision recommendation."""
    entity_id: str
    entity_name: str
    type: RecommendationType
    priority: Priority
    confidence: float
    reason: str
    actions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DecisionReport:
    """Comprehensive decision report."""
    generated_at: datetime = field(default_factory=datetime.utcnow)

    # Summary
    total_analyzed: int = 0
    high_priority_count: int = 0

    # Recommendations by type
    recommendations: list[Recommendation] = field(default_factory=list)

    # State distribution
    state_distribution: dict[str, int] = field(default_factory=dict)

    # Risk summary
    average_risk: float = 0.0
    high_risk_entities: list[str] = field(default_factory=list)


class DecisionEngine:
    """Engine for generating actionable recommendations."""

    # Decision rules
    DECISION_RULES = [
        # Rule 1: High departure risk + interviewing state
        {
            "conditions": {
                "min_departure_risk": 0.8,
                "states": [CareerState.INTERVIEWING, CareerState.HANDING_OVER],
            },
            "recommendation": RecommendationType.ALERT_MANAGER,
            "priority": Priority.CRITICAL,
            "reason": "High risk of departure with advanced interview stage",
            "actions": [
                "Immediately notify hiring manager",
                "Review retention options",
                "Prepare succession plan",
            ],
        },
        # Rule 2: Job hunting signals
        {
            "conditions": {
                "min_departure_risk": 0.6,
                "states": [CareerState.JOB_HUNTING, CareerState.OBSERVING],
            },
            "recommendation": RecommendationType.MONITOR_CLOSER,
            "priority": Priority.HIGH,
            "reason": "Active job hunting signals detected",
            "actions": [
                "Increase monitoring frequency",
                "Check for target company interactions",
                "Consider proactive outreach",
            ],
        },
        # Rule 3: Multiple signals
        {
            "conditions": {
                "min_signal_count": 5,
                "min_departure_risk": 0.4,
            },
            "recommendation": RecommendationType.REACH_OUT,
            "priority": Priority.MEDIUM,
            "reason": "Multiple concerning signals detected",
            "actions": [
                "Schedule casual check-in",
                "Review recent work satisfaction",
                "Discuss career development",
            ],
        },
        # Rule 4: Recent profile updates
        {
            "conditions": {
                "signal_types": ["profile_updated", "bio_changed"],
                "min_departure_risk": 0.3,
            },
            "recommendation": RecommendationType.UPDATE_INFO,
            "priority": Priority.LOW,
            "reason": "Profile changes may indicate preparation",
            "actions": [
                "Review profile changes",
                "Check for LinkedIn updates",
                "Note any company mentions",
            ],
        },
        # Rule 5: Stable state, low risk
        {
            "conditions": {
                "max_departure_risk": 0.3,
                "states": [CareerState.STABLE],
            },
            "recommendation": RecommendationType.NO_ACTION,
            "priority": Priority.LOW,
            "reason": "No concerning signals",
            "actions": [
                "Continue regular monitoring",
                "No immediate action needed",
            ],
        },
    ]

    def __init__(
        self,
        session: AsyncSession,
        analyzer: KeyPersonAnalyzer | None = None,
    ) -> None:
        """Initialize decision engine.

        Args:
            session: Database session.
            analyzer: Optional key person analyzer.
        """
        self.session = session
        self.analyzer = analyzer or KeyPersonAnalyzer(session)

    async def generate_recommendations(
        self,
        entity_ids: list[str] | None = None,
        min_priority: int = 5,
    ) -> DecisionReport:
        """Generate recommendations for entities.

        Args:
            entity_ids: Optional specific entity IDs.
            min_priority: Minimum entity priority.

        Returns:
            DecisionReport with recommendations.
        """
        logger.info("generating_recommendations", entity_count=len(entity_ids) if entity_ids else "all")

        # Analyze all relevant entities
        intelligences = await self.analyzer.analyze_batch(
            entity_ids=entity_ids,
            min_priority=min_priority,
        )

        report = DecisionReport(total_analyzed=len(intelligences))

        # Generate recommendations for each entity
        for intel in intelligences:
            recommendation = self._evaluate_rules(intel)
            if recommendation:
                report.recommendations.append(recommendation)
                if recommendation.priority in [Priority.CRITICAL, Priority.HIGH]:
                    report.high_priority_count += 1

        # Sort by priority
        priority_order = {
            Priority.CRITICAL: 0,
            Priority.HIGH: 1,
            Priority.MEDIUM: 2,
            Priority.LOW: 3,
        }
        report.recommendations.sort(
            key=lambda r: (priority_order.get(r.priority, 99), -r.confidence)
        )

        # Calculate summary stats
        if intelligences:
            report.average_risk = sum(i.departure_risk for i in intelligences) / len(intelligences)
            report.high_risk_entities = [
                i.entity_id for i in intelligences
                if i.departure_risk >= 0.7
            ]

        # Get state distribution
        report.state_distribution = await self.analyzer.get_state_distribution()

        logger.info(
            "recommendations_generated",
            total=report.total_analyzed,
            high_priority=report.high_priority_count,
        )

        return report

    async def get_entity_recommendation(
        self,
        entity_id: str,
    ) -> Recommendation | None:
        """Get recommendation for a specific entity.

        Args:
            entity_id: Entity ID.

        Returns:
            Recommendation or None.
        """
        intel = await self.analyzer.analyze_person(entity_id)
        if not intel:
            return None

        return self._evaluate_rules(intel)

    async def get_actionable_items(
        self,
        max_items: int = 20,
    ) -> list[Recommendation]:
        """Get actionable items sorted by priority.

        Args:
            max_items: Maximum items to return.

        Returns:
            List of actionable recommendations.
        """
        report = await self.generate_recommendations()

        # Filter to actionable items only
        actionable = [
            r for r in report.recommendations
            if r.type not in [RecommendationType.NO_ACTION]
        ]

        return actionable[:max_items]

    def _evaluate_rules(self, intel: PersonIntelligence) -> Recommendation | None:
        """Evaluate decision rules for an intelligence report.

        Args:
            intel: Person intelligence.

        Returns:
            Best matching recommendation or None.
        """
        for rule in self.DECISION_RULES:
            if self._matches_rule(intel, rule):
                return Recommendation(
                    entity_id=intel.entity_id,
                    entity_name=intel.name,
                    type=rule["recommendation"],
                    priority=rule["priority"],
                    confidence=intel.departure_risk,
                    reason=rule["reason"],
                    actions=rule["actions"],
                    metadata={
                        "current_state": intel.current_state.value,
                        "departure_risk": intel.departure_risk,
                        "signal_count": sum(intel.signal_summary.values()),
                        "risk_factors": intel.risk_factors,
                    },
                )

        # Default recommendation if no rules match
        return Recommendation(
            entity_id=intel.entity_id,
            entity_name=intel.name,
            type=RecommendationType.SCHEDULE_CHECK,
            priority=Priority.LOW,
            confidence=0.5,
            reason="Regular check recommended",
            actions=["Schedule periodic review"],
            metadata={
                "current_state": intel.current_state.value,
                "departure_risk": intel.departure_risk,
            },
        )

    def _matches_rule(
        self,
        intel: PersonIntelligence,
        rule: dict[str, Any],
    ) -> bool:
        """Check if intelligence matches a rule.

        Args:
            intel: Person intelligence.
            rule: Decision rule.

        Returns:
            True if matches.
        """
        conditions = rule.get("conditions", {})

        # Check departure risk
        min_risk = conditions.get("min_departure_risk")
        if min_risk and intel.departure_risk < min_risk:
            return False

        max_risk = conditions.get("max_departure_risk")
        if max_risk and intel.departure_risk > max_risk:
            return False

        # Check states
        states = conditions.get("states")
        if states and intel.current_state not in states:
            return False

        # Check signal count
        min_signals = conditions.get("min_signal_count")
        if min_signals:
            total_signals = sum(intel.signal_summary.values())
            if total_signals < min_signals:
                return False

        # Check signal types
        signal_types = conditions.get("signal_types")
        if signal_types:
            if not any(st in intel.signal_summary for st in signal_types):
                return False

        return True

    async def generate_dashboard_data(self) -> dict[str, Any]:
        """Generate data for decision support dashboard.

        Returns:
            Dashboard data dictionary.
        """
        report = await self.generate_recommendations()

        # Group recommendations by type
        by_type: dict[str, int] = {}
        for rec in report.recommendations:
            type_name = rec.type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1

        # Group by priority
        by_priority: dict[str, int] = {}
        for rec in report.recommendations:
            priority_name = rec.priority.value
            by_priority[priority_name] = by_priority.get(priority_name, 0) + 1

        return {
            "generated_at": report.generated_at.isoformat(),
            "summary": {
                "total_analyzed": report.total_analyzed,
                "high_priority_count": report.high_priority_count,
                "average_risk": round(report.average_risk, 3),
                "high_risk_count": len(report.high_risk_entities),
            },
            "state_distribution": report.state_distribution,
            "recommendations_by_type": by_type,
            "recommendations_by_priority": by_priority,
            "top_recommendations": [
                {
                    "entity_id": r.entity_id,
                    "entity_name": r.entity_name,
                    "type": r.type.value,
                    "priority": r.priority.value,
                    "reason": r.reason,
                    "actions": r.actions[:3],
                }
                for r in report.recommendations[:10]
            ],
            "high_risk_entities": report.high_risk_entities[:20],
        }
