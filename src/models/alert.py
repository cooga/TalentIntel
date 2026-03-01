"""Alert model for system alerts."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel
from sqlalchemy import JSON, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, generate_id


class AlertSeverity(str, Enum):
    """Alert severity enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """Alert type enumeration."""

    STATE_CHANGE = "state_change"
    HIGH_CONFIDENCE_SIGNAL = "high_confidence_signal"
    MULTI_SIGNAL_CLUSTER = "multi_signal_cluster"
    FETCH_ERROR = "fetch_error"
    BASELINE_READY = "baseline_ready"


class Alert(Base):
    """Alert model."""

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alert_id: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, default=lambda: generate_id("alt")
    )
    entity_id: Mapped[str | None] = mapped_column(String(50), index=True)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float)
    evidence: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False, index=True
    )

    # Acknowledgment
    acknowledged_at: Mapped[datetime | None]
    acknowledged_by: Mapped[str | None] = mapped_column(String(100))

    # Notification status
    notified_at: Mapped[datetime | None]
    notification_channel: Mapped[str | None] = mapped_column(String(50))


class AlertResponse(BaseModel):
    """Schema for alert API response."""

    id: int
    alert_id: str
    entity_id: str | None
    alert_type: str
    severity: str
    title: str
    description: str | None
    confidence: float | None
    evidence: dict[str, Any] | None
    triggered_at: datetime
    acknowledged_at: datetime | None
    acknowledged_by: str | None

    class Config:
        from_attributes = True
