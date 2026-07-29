from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class PropertyApiCache(Base):
    __tablename__ = "property_api_cache"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), nullable=False, index=True)

    source_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    endpoint: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    cache_key: Mapped[str] = mapped_column(String(500), nullable=False, unique=True, index=True)

    response_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    property = relationship("Property", back_populates="api_cache_entries")