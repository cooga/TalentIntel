"""Entity model - represents a monitored person."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import JSON, Boolean, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin, generate_id


class CareerState(str, Enum):
    """Career state enumeration."""

    STABLE = "stable"  # In position, no abnormal signals
    OBSERVING = "observing"  # Some signals worth watching
    JOB_HUNTING = "job_hunting"  # Clear job seeking signals
    INTERVIEWING = "interviewing"  # Interview phase
    HANDING_OVER = "handing_over"  # Transition/handoff period
    TRANSITIONED = "transitioned"  # Confirmed new position
    STARTUP_READY = "startup_ready"  # May be starting a company
    SABBATICAL = "sabbatical"  # On break/sabbatical
    UNKNOWN = "unknown"  # Insufficient information


class Entity(Base, TimestampMixin):
    """Entity model representing a monitored person."""

    __tablename__ = "entities"

    id: Mapped[str] = mapped_column(
        String(50), primary_key=True, default=lambda: generate_id("ent")
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Platform accounts
    github_username: Mapped[str | None] = mapped_column(String(255), unique=True)
    twitter_handle: Mapped[str | None] = mapped_column(String(255), unique=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(512))
    personal_website: Mapped[str | None] = mapped_column(String(512))

    # Current state
    current_state: Mapped[str | None] = mapped_column(String(50))
    state_confidence: Mapped[float | None] = mapped_column(Float)
    state_updated_at: Mapped[datetime | None] = mapped_column()

    # Current position
    current_company: Mapped[str | None] = mapped_column(String(255))
    current_title: Mapped[str | None] = mapped_column(String(255))

    # Baseline data (JSON)
    baseline_commit_pattern: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    baseline_active_hours: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    # Metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=5)  # 1-10, higher = more priority
    tags: Mapped[list[str] | None] = mapped_column(JSON)

    # Notes
    notes: Mapped[str | None] = mapped_column(Text)


class EntityCreate(BaseModel):
    """Schema for creating a new entity."""

    name: str = Field(..., min_length=1, max_length=255)
    github_username: str | None = Field(None, max_length=255)
    twitter_handle: str | None = Field(None, max_length=255)
    linkedin_url: str | None = Field(None, max_length=512)
    personal_website: str | None = Field(None, max_length=512)
    current_company: str | None = Field(None, max_length=255)
    current_title: str | None = Field(None, max_length=255)
    priority: int = Field(default=5, ge=1, le=10)
    tags: list[str] | None = Field(default=None)
    notes: str | None = Field(None)

    @field_validator("github_username", "twitter_handle")
    @classmethod
    def validate_username(cls, v: str | None) -> str | None:
        """Trim and validate username."""
        if v:
            return v.strip().lstrip("@")
        return v


class EntityUpdate(BaseModel):
    """Schema for updating an entity."""

    name: str | None = Field(None, min_length=1, max_length=255)
    github_username: str | None = Field(None, max_length=255)
    twitter_handle: str | None = Field(None, max_length=255)
    linkedin_url: str | None = Field(None, max_length=512)
    personal_website: str | None = Field(None, max_length=512)
    current_company: str | None = Field(None, max_length=255)
    current_title: str | None = Field(None, max_length=255)
    current_state: CareerState | None = Field(None)
    state_confidence: float | None = Field(None, ge=0, le=1)
    priority: int | None = Field(None, ge=1, le=10)
    tags: list[str] | None = Field(None)
    notes: str | None = Field(None)
    is_active: bool | None = Field(None)


class EntityResponse(BaseModel):
    """Schema for entity API response."""

    id: str
    name: str
    github_username: str | None
    twitter_handle: str | None
    linkedin_url: str | None
    personal_website: str | None
    current_state: str | None
    state_confidence: float | None
    current_company: str | None
    current_title: str | None
    is_active: bool
    priority: int
    tags: list[str] | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
