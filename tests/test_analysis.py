"""Tests for key person analyzer and decision engine."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.models.entity import Entity, CareerState
from src.models.signal import Signal, SignalType
from src.graph.relationship_graph import RelationshipGraph, NodeType


@pytest.fixture
def mock_session():
    """Create mock database session."""
    session = AsyncMock()
    return session


@pytest.fixture
def sample_entity():
    """Create sample entity."""
    return Entity(
        id="ent_test123",
        name="Test User",
        github_username="testuser",
        current_state=CareerState.STABLE.value,
        state_confidence=0.8,
        current_company="Test Corp",
        current_title="Engineer",
        priority=7,
    )


@pytest.fixture
def sample_graph():
    """Create sample relationship graph."""
    graph = RelationshipGraph()
    graph.add_node("ent_test123", NodeType.PERSON, "Test User")
    graph.add_node("ent_other", NodeType.PERSON, "Other User")
    graph.add_node("company_test_corp", NodeType.COMPANY, "Test Corp")
    return graph


class TestKeyPersonAnalyzerDataclasses:
    """Tests for analyzer dataclasses."""

    def test_person_intelligence_creation(self):
        """Test PersonIntelligence creation."""
        from src.analysis.key_person_analyzer import PersonIntelligence

        intel = PersonIntelligence(
            entity_id="test_123",
            name="Test User",
            current_state=CareerState.JOB_HUNTING,
            state_confidence=0.75,
            departure_risk=0.6,
        )

        assert intel.entity_id == "test_123"
        assert intel.current_state == CareerState.JOB_HUNTING
        assert intel.departure_risk == 0.6

    def test_person_intelligence_defaults(self):
        """Test PersonIntelligence default values."""
        from src.analysis.key_person_analyzer import PersonIntelligence

        intel = PersonIntelligence(
            entity_id="test",
            name="Test",
        )

        assert intel.current_state == CareerState.UNKNOWN
        assert intel.departure_risk == 0.0
        assert intel.risk_factors == []
        assert intel.recent_signals == []


class TestDecisionEngineDataclasses:
    """Tests for decision engine dataclasses."""

    def test_recommendation_creation(self):
        """Test creating a recommendation."""
        from src.analysis.decision_engine import (
            Recommendation,
            RecommendationType,
            Priority,
        )

        rec = Recommendation(
            entity_id="test_123",
            entity_name="Test User",
            type=RecommendationType.ALERT_MANAGER,
            priority=Priority.CRITICAL,
            confidence=0.9,
            reason="High departure risk",
            actions=["Notify manager", "Prepare succession plan"],
        )

        assert rec.entity_id == "test_123"
        assert rec.type == RecommendationType.ALERT_MANAGER
        assert rec.priority == Priority.CRITICAL
        assert len(rec.actions) == 2

    def test_recommendation_defaults(self):
        """Test default values."""
        from src.analysis.decision_engine import (
            Recommendation,
            RecommendationType,
            Priority,
        )

        rec = Recommendation(
            entity_id="test",
            entity_name="Test",
            type=RecommendationType.NO_ACTION,
            priority=Priority.LOW,
            confidence=0.5,
            reason="No action needed",
        )

        assert rec.actions == []
        assert rec.metadata == {}

    def test_decision_report_creation(self):
        """Test creating a decision report."""
        from src.analysis.decision_engine import DecisionReport

        report = DecisionReport(
            total_analyzed=10,
            high_priority_count=2,
            average_risk=0.35,
        )

        assert report.total_analyzed == 10
        assert report.high_priority_count == 2
        assert report.average_risk == 0.35

    def test_decision_report_defaults(self):
        """Test default values."""
        from src.analysis.decision_engine import DecisionReport

        report = DecisionReport()

        assert report.total_analyzed == 0
        assert report.recommendations == []
        assert report.state_distribution == {}


class TestStatePrediction:
    """Tests for StatePrediction dataclass."""

    def test_state_prediction_creation(self):
        """Test creating state prediction."""
        from src.sentinel.state_machine import StatePrediction

        prediction = StatePrediction(
            state=CareerState.JOB_HUNTING,
            confidence=0.75,
            matched_conditions=["profile_updated"],
            rule_name="job_hunting_profile",
        )

        assert prediction.state == CareerState.JOB_HUNTING
        assert prediction.confidence == 0.75
        assert len(prediction.matched_conditions) == 1

    def test_state_prediction_defaults(self):
        """Test state prediction default values."""
        from src.sentinel.state_machine import StatePrediction

        prediction = StatePrediction(
            state=CareerState.STABLE,
            confidence=0.5,
        )

        assert prediction.matched_conditions == []
        assert prediction.evidence == {}


class TestStateTransition:
    """Tests for StateTransition dataclass."""

    def test_state_transition_creation(self):
        """Test creating state transition."""
        from src.sentinel.state_machine import StateTransition

        transition = StateTransition(
            from_state=CareerState.STABLE,
            to_state=CareerState.JOB_HUNTING,
            confidence=0.8,
            timestamp=datetime.utcnow(),
            signals=["profile_updated"],
        )

        assert transition.from_state == CareerState.STABLE
        assert transition.to_state == CareerState.JOB_HUNTING
        assert transition.confidence == 0.8
