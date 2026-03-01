"""Event model for event sourcing."""

from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, generate_id


class EventType(str, Enum):
    """Event type enumeration."""

    # Profile events
    PROFILE_CREATED = "profile_created"
    PROFILE_UPDATED = "profile_updated"
    PROFILE_DELETED = "profile_deleted"

    # GitHub events
    GITHUB_PROFILE_CHANGED = "github_profile_changed"
    GITHUB_REPO_CREATED = "github_repo_created"
    GITHUB_REPO_DELETED = "github_repo_deleted"
    GITHUB_COMMIT = "github_commit"
    GITHUB_ORG_JOINED = "github_org_joined"
    GITHUB_ORG_LEFT = "github_org_left"

    # State events
    STATE_CHANGED = "state_changed"
    SIGNAL_DETECTED = "signal_detected"

    # System events
    FETCH_COMPLETED = "fetch_completed"
    FETCH_FAILED = "fetch_failed"
    BASELINE_ESTABLISHED = "baseline_established"


class Event(Base):
    """Event log model for event sourcing."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, default=lambda: generate_id("evt")
    )
    entity_id: Mapped[str | None] = mapped_column(String(50), index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False, index=True
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Source tracking
    source_platform: Mapped[str | None] = mapped_column(String(50))
    source_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)


class EventCreate:
    """Internal class for creating events."""

    def __init__(
        self,
        event_type: EventType | str,
        payload: dict[str, Any],
        entity_id: str | None = None,
        source_platform: str | None = None,
        source_data: dict[str, Any] | None = None,
    ):
        self.event_id = generate_id("evt")
        self.entity_id = entity_id
        self.event_type = event_type if isinstance(event_type, str) else event_type.value
        self.payload = payload
        self.source_platform = source_platform
        self.source_data = source_data
