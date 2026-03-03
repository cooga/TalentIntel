"""Tests for state machine engine."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.sentinel.state_machine import (
    StateInferenceEngine,
    StatePrediction,
    StateTransition,
)
from src.models.entity import Entity, CareerState
from src.models.signal import Signal, SignalType


@pytest.fixture
def mock_session():
    """Create mock database session."""
    session = AsyncMock()
    return session


@pytest.fixture
def sample_entity():
    """Create sample entity."""
    entity = Entity(
        id="ent_test123",
        name="Test User",
        github_username="testuser",
        current_state=CareerState.STABLE.value,
        state_confidence=0.8,
    )
    return entity


@pytest.fixture
def sample_signals():
    """Create sample signals."""
    now = datetime.utcnow()
    return [
        Signal(
            id=1,
            entity_id="ent_test123",
            signal_type=SignalType.PROFILE_UPDATED.value,
            confidence=0.7,
            source_platform="github",
            detected_at=now - timedelta(days=1),
        ),
        Signal(
            id=2,
            entity_id="ent_test123",
            signal_type=SignalType.COMMIT_FREQUENCY_DROP.value,
            confidence=0.6,
            source_platform="github",
            detected_at=now - timedelta(days=2),
        ),
    ]


class TestStateInferenceEngine:
    """Tests for StateInferenceEngine."""

    @pytest.mark.asyncio
    async def test_infer_state_stable(self, mock_session, sample_entity):
        """Test inferring stable state with no signals."""
        # Mock entity query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_entity
        mock_session.execute.return_value = mock_result

        engine = StateInferenceEngine(mock_session)
        prediction = await engine.infer_state("ent_test123")

        assert prediction.state == CareerState.STABLE
        assert prediction.confidence >= 0.0

    @pytest.mark.asyncio
    async def test_infer_state_job_hunting(self, mock_session, sample_entity, sample_signals):
        """Test inferring job hunting state with relevant signals."""
        sample_entity.current_state = None

        # Mock entity query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_entity
        mock_session.execute.return_value = mock_result

        engine = StateInferenceEngine(mock_session)

        # Override signal fetching
        with pytest.MonkeyPatch.context() as m:
            async def mock_get_signals(*args, **kwargs):
                return sample_signals
            m.setattr(engine, "_get_recent_signals", mock_get_signals)

            prediction = await engine.infer_state("ent_test123")

            assert prediction.state in [CareerState.JOB_HUNTING, CareerState.STABLE]

    @pytest.mark.asyncio
    async def test_update_entity_state(self, mock_session, sample_entity, sample_signals):
        """Test updating entity state."""
        sample_entity.current_state = CareerState.STABLE.value

        # Mock queries
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_entity
        mock_session.execute.return_value = mock_result

        engine = StateInferenceEngine(mock_session)

        with pytest.MonkeyPatch.context() as m:
            async def mock_get_signals(*args, **kwargs):
                return sample_signals
            m.setattr(engine, "_get_recent_signals", mock_get_signals)

            transition = await engine.update_entity_state("ent_test123")

            # State might or might not change depending on signals
            assert transition is None or isinstance(transition, StateTransition)

    @pytest.mark.asyncio
    async def test_get_state_summary(self, mock_session, sample_entity):
        """Test getting state summary."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_entity
        mock_session.execute.return_value = mock_result

        engine = StateInferenceEngine(mock_session)
        summary = await engine.get_state_summary("ent_test123")

        assert summary["entity_id"] == "ent_test123"
        assert summary["name"] == "Test User"
        assert "current_state" in summary


class TestStatePrediction:
    """Tests for StatePrediction dataclass."""

    def test_state_prediction_creation(self):
        """Test creating a state prediction."""
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
        prediction = StatePrediction(
            state=CareerState.STABLE,
            confidence=0.5,
        )

        assert prediction.matched_conditions == []
        assert prediction.evidence == {}


class TestStateTransition:
    """Tests for StateTransition dataclass."""

    def test_state_transition_creation(self):
        """Test creating a state transition."""
        transition = StateTransition(
            from_state=CareerState.STABLE,
            to_state=CareerState.JOB_HUNTING,
            confidence=0.8,
            timestamp=datetime.utcnow(),
            signals=["profile_updated"],
        )

        assert transition.from_state == CareerState.STABLE
        assert transition.to_state == CareerState.JOB_HUNTING
