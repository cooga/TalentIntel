"""Signal model for detected signals."""

from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class SignalType(str, Enum):
    """Signal type enumeration."""

    # Commit pattern signals
    COMMIT_PATTERN_ANOMALY = "commit_pattern_anomaly"
    COMMIT_TIME_ANOMALY = "commit_time_anomaly"
    COMMIT_FREQUENCY_DROP = "commit_frequency_drop"
    COMMIT_FREQUENCY_SPIKE = "commit_frequency_spike"

    # Profile signals
    PROFILE_UPDATED = "profile_updated"
    COMPANY_CHANGED = "company_changed"
    BIO_CHANGED = "bio_changed"
    LOCATION_CHANGED = "location_changed"

    # Organization signals
    ORG_JOINED = "org_joined"
    ORG_LEFT = "org_left"

    # Social signals
    FOLLOW_PATTERN_CHANGE = "follow_pattern_change"
    INTERACTION_WITH_TARGET_COMPANY = "interaction_with_target_company"

    # Code signals
    NEW_TECH_STACK = "new_tech_stack"
    REPO_VISIBILITY_CHANGE = "repo_visibility_change"
    INTERVIEW_PREP_COMMITS = "interview_prep_commits"


class Signal(Base):
    """Signal detection model."""

    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    signal_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    source_platform: Mapped[str] = mapped_column(String(50), nullable=False)
    source_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    description: Mapped[str | None] = mapped_column(Text)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False, index=True
    )
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    processed_at: Mapped[datetime | None]

    # For deduplication
    fingerprint: Mapped[str | None] = mapped_column(String(64), index=True)


class SignalCreate:
    """Internal class for creating signals."""

    def __init__(
        self,
        entity_id: str,
        signal_type: SignalType | str,
        confidence: float,
        source_platform: str,
        source_data: dict[str, Any] | None = None,
        description: str | None = None,
        fingerprint: str | None = None,
    ):
        self.entity_id = entity_id
        self.signal_type = signal_type if isinstance(signal_type, str) else signal_type.value
        self.confidence = min(1.0, max(0.0, confidence))
        self.source_platform = source_platform
        self.source_data = source_data
        self.description = description
        self.fingerprint = fingerprint
