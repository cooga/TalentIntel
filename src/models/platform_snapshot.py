"""Platform snapshot model for storing platform data snapshots."""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class PlatformSnapshot(Base):
    """Platform snapshot model for differential storage."""

    __tablename__ = "platform_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)  # github, twitter, etc.
    snapshot_hash: Mapped[str | None] = mapped_column(String(64))  # SHA256 hash for quick compare
    snapshot_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    etag: Mapped[str | None] = mapped_column(String(255))  # For conditional requests
    captured_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # Change detection
    has_changes: Mapped[bool] = mapped_column(default=False)
    changes: Mapped[dict[str, Any] | None] = mapped_column(JSON)  # Diff from previous


class SnapshotCreate:
    """Internal class for creating snapshots."""

    def __init__(
        self,
        entity_id: str,
        platform: str,
        snapshot_data: dict[str, Any],
        snapshot_hash: str | None = None,
        etag: str | None = None,
        has_changes: bool = False,
        changes: dict[str, Any] | None = None,
    ):
        self.entity_id = entity_id
        self.platform = platform
        self.snapshot_data = snapshot_data
        self.snapshot_hash = snapshot_hash
        self.etag = etag
        self.has_changes = has_changes
        self.changes = changes
