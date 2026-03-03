"""Key Person Analyzer for comprehensive entity intelligence analysis."""

from datetime import datetime, timedelta
from typing import Any
from dataclasses import dataclass, field

import structlog
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.entity import Entity, CareerState
from src.models.signal import Signal
from src.models.event import Event
from src.graph.relationship_graph import RelationshipGraph, NodeType, EdgeType
from src.graph.network_analyzer import NetworkAnalyzer

logger = structlog.get_logger()


@dataclass
class PersonIntelligence:
    """Comprehensive intelligence about a person."""
    entity_id: str
    name: str

    # Current status
    current_state: CareerState = CareerState.UNKNOWN
    state_confidence: float = 0.0
    current_company: str | None = None
    current_title: str | None = None

    # Risk assessment
    departure_risk: float = 0.0  # 0-1, higher = more likely to leave
    risk_factors: list[str] = field(default_factory=list)

    # Activity summary
    recent_signals: list[dict[str, Any]] = field(default_factory=list)
    signal_summary: dict[str, int] = field(default_factory=dict)

    # Network position
    network_centrality: float = 0.0
    key_connections: list[str] = field(default_factory=list)
    community_id: int | None = None

    # Timeline
    last_activity: datetime | None = None
    predicted_next_state: CareerState | None = None
    prediction_confidence: float = 0.0

    # Metadata
    analysis_timestamp: datetime = field(default_factory=datetime.utcnow)


class KeyPersonAnalyzer:
    """Analyzer for key person intelligence."""

    # Risk factor weights
    RISK_WEIGHTS = {
        "commit_frequency_drop": 0.25,
        "commit_time_anomaly": 0.15,
        "profile_updated": 0.20,
        "company_changed": 0.10,  # Already changed, lower risk
        "bio_changed": 0.15,
        "interaction_with_target_company": 0.30,
        "org_joined": 0.10,
        "org_left": 0.20,
    }

    # State transition predictions
    STATE_TRANSITIONS = {
        CareerState.STABLE: [
            (CareerState.OBSERVING, 0.3),
            (CareerState.JOB_HUNTING, 0.1),
        ],
        CareerState.OBSERVING: [
            (CareerState.JOB_HUNTING, 0.4),
            (CareerState.STABLE, 0.2),
        ],
        CareerState.JOB_HUNTING: [
            (CareerState.INTERVIEWING, 0.5),
            (CareerState.OBSERVING, 0.2),
        ],
        CareerState.INTERVIEWING: [
            (CareerState.HANDING_OVER, 0.4),
            (CareerState.JOB_HUNTING, 0.2),
        ],
        CareerState.HANDING_OVER: [
            (CareerState.TRANSITIONED, 0.6),
            (CareerState.INTERVIEWING, 0.1),
        ],
        CareerState.TRANSITIONED: [
            (CareerState.STABLE, 0.8),
        ],
    }

    def __init__(
        self,
        session: AsyncSession,
        graph: RelationshipGraph | None = None,
    ) -> None:
        """Initialize key person analyzer.

        Args:
            session: Database session.
            graph: Optional relationship graph for network analysis.
        """
        self.session = session
        self.graph = graph
        self.network_analyzer = NetworkAnalyzer(graph) if graph else None

    async def analyze_person(
        self,
        entity_id: str,
        include_network: bool = True,
    ) -> PersonIntelligence | None:
        """Perform comprehensive analysis of a person.

        Args:
            entity_id: Entity ID to analyze.
            include_network: Whether to include network analysis.

        Returns:
            PersonIntelligence or None if entity not found.
        """
        entity = await self._get_entity(entity_id)
        if not entity:
            return None

        logger.info("analyzing_person", entity_id=entity_id, name=entity.name)

        # Build base intelligence
        intelligence = PersonIntelligence(
            entity_id=entity_id,
            name=entity.name,
            current_state=CareerState(entity.current_state) if entity.current_state else CareerState.UNKNOWN,
            state_confidence=entity.state_confidence or 0.0,
            current_company=entity.current_company,
            current_title=entity.current_title,
        )

        # Analyze signals
        await self._analyze_signals(entity_id, intelligence)

        # Calculate departure risk
        self._calculate_departure_risk(intelligence)

        # Predict next state
        self._predict_next_state(intelligence)

        # Network analysis
        if include_network and self.graph and self.network_analyzer:
            self._analyze_network_position(entity_id, intelligence)

        return intelligence

    async def analyze_batch(
        self,
        entity_ids: list[str] | None = None,
        min_priority: int = 5,
    ) -> list[PersonIntelligence]:
        """Analyze multiple entities.

        Args:
            entity_ids: Optional list of entity IDs. If None, analyze all active.
            min_priority: Minimum priority to include.

        Returns:
            List of PersonIntelligence.
        """
        if entity_ids is None:
            query = (
                select(Entity)
                .where(Entity.is_active == True)
                .where(Entity.priority >= min_priority)
                .order_by(Entity.priority.desc())
            )
            result = await self.session.execute(query)
            entities = list(result.scalars().all())
            entity_ids = [e.id for e in entities]

        intelligences = []
        for entity_id in entity_ids:
            intel = await self.analyze_person(entity_id)
            if intel:
                intelligences.append(intel)

        return intelligences

    async def get_high_risk_persons(
        self,
        threshold: float = 0.6,
        limit: int = 20,
    ) -> list[PersonIntelligence]:
        """Get persons with high departure risk.

        Args:
            threshold: Risk threshold (0-1).
            limit: Maximum number to return.

        Returns:
            List of high-risk persons.
        """
        intelligences = await self.analyze_batch()

        high_risk = [
            intel for intel in intelligences
            if intel.departure_risk >= threshold
        ]

        high_risk.sort(key=lambda x: x.departure_risk, reverse=True)
        return high_risk[:limit]

    async def get_attention_needed(
        self,
        limit: int = 10,
    ) -> list[PersonIntelligence]:
        """Get persons that need immediate attention.

        Args:
            limit: Maximum number to return.

        Returns:
            List of persons needing attention.
        """
        intelligences = await self.analyze_batch()

        # Score based on multiple factors
        def attention_score(intel: PersonIntelligence) -> float:
            score = 0.0

            # High departure risk
            score += intel.departure_risk * 0.4

            # Recent signals
            score += min(len(intel.recent_signals) / 10, 0.3)

            # Certain states need more attention
            if intel.current_state in [CareerState.INTERVIEWING, CareerState.HANDING_OVER]:
                score += 0.3
            elif intel.current_state == CareerState.JOB_HUNTING:
                score += 0.2

            return score

        intelligences.sort(key=attention_score, reverse=True)
        return intelligences[:limit]

    async def get_state_distribution(self) -> dict[str, int]:
        """Get distribution of career states.

        Returns:
            Dictionary of state -> count.
        """
        query = select(Entity).where(Entity.is_active == True)
        result = await self.session.execute(query)
        entities = list(result.scalars().all())

        distribution: dict[str, int] = {}
        for entity in entities:
            state = entity.current_state or "unknown"
            distribution[state] = distribution.get(state, 0) + 1

        return distribution

    async def _get_entity(self, entity_id: str) -> Entity | None:
        """Get entity by ID."""
        query = select(Entity).where(Entity.id == entity_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def _analyze_signals(
        self,
        entity_id: str,
        intelligence: PersonIntelligence,
    ) -> None:
        """Analyze recent signals for an entity."""
        # Get recent signals (last 30 days)
        start_date = datetime.utcnow() - timedelta(days=30)

        query = (
            select(Signal)
            .where(Signal.entity_id == entity_id)
            .where(Signal.detected_at >= start_date)
            .order_by(desc(Signal.detected_at))
            .limit(50)
        )

        result = await self.session.execute(query)
        signals = list(result.scalars().all())

        intelligence.recent_signals = [
            {
                "type": s.signal_type,
                "confidence": s.confidence,
                "detected_at": s.detected_at.isoformat(),
                "description": s.description,
            }
            for s in signals[:10]
        ]

        # Signal summary by type
        intelligence.signal_summary = {}
        for signal in signals:
            intelligence.signal_summary[signal.signal_type] = \
                intelligence.signal_summary.get(signal.signal_type, 0) + 1

        # Last activity
        if signals:
            intelligence.last_activity = signals[0].detected_at

    def _calculate_departure_risk(self, intelligence: PersonIntelligence) -> None:
        """Calculate departure risk score."""
        if intelligence.current_state == CareerState.TRANSITIONED:
            intelligence.departure_risk = 0.0  # Already left
            intelligence.risk_factors.append("Already transitioned")
            return

        if intelligence.current_state == CareerState.STABLE:
            base_risk = 0.1
        elif intelligence.current_state == CareerState.OBSERVING:
            base_risk = 0.3
        elif intelligence.current_state == CareerState.JOB_HUNTING:
            base_risk = 0.6
        elif intelligence.current_state == CareerState.INTERVIEWING:
            base_risk = 0.8
        elif intelligence.current_state == CareerState.HANDING_OVER:
            base_risk = 0.9
        else:
            base_risk = 0.2

        # Add signal-based risk
        signal_risk = 0.0
        for signal_type, count in intelligence.signal_summary.items():
            weight = self.RISK_WEIGHTS.get(signal_type, 0.1)
            signal_risk += weight * min(count / 3, 1.0)

        # Combine
        intelligence.departure_risk = min(base_risk + signal_risk * 0.3, 1.0)

        # Identify risk factors
        if intelligence.current_state in [CareerState.JOB_HUNTING, CareerState.INTERVIEWING]:
            intelligence.risk_factors.append(f"Current state: {intelligence.current_state.value}")

        for signal_type, count in intelligence.signal_summary.items():
            if count >= 2:
                intelligence.risk_factors.append(f"Multiple {signal_type} signals")

    def _predict_next_state(self, intelligence: PersonIntelligence) -> None:
        """Predict next career state."""
        current = intelligence.current_state

        if current not in self.STATE_TRANSITIONS:
            return

        transitions = self.STATE_TRANSITIONS[current]
        if not transitions:
            return

        # Find most likely transition
        best_transition = max(transitions, key=lambda x: x[1])
        intelligence.predicted_next_state = best_transition[0]
        intelligence.prediction_confidence = best_transition[1]

    def _analyze_network_position(
        self,
        entity_id: str,
        intelligence: PersonIntelligence,
    ) -> None:
        """Analyze network position."""
        if not self.network_analyzer:
            return

        # Get centrality scores
        centrality = self.network_analyzer.calculate_degree_centrality()
        intelligence.network_centrality = centrality.get(entity_id, 0.0)

        # Get key connections
        neighbors = self.graph.get_neighbors(entity_id)
        intelligence.key_connections = [
            n.label for n in neighbors[:5]
            if n.type == NodeType.PERSON
        ]

        # Get community
        communities = self.network_analyzer.detect_communities()
        for community in communities:
            if entity_id in community.nodes:
                intelligence.community_id = community.community_id
                break
