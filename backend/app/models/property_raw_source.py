from __future__ import annotations

from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class PropertyRawSource(Base):
    __tablename__ = "property_raw_sources"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), nullable=False, index=True)
    source_name: Mapped[str] = mapped_column(String(100), nullable=False)
    source_type: Mapped[str] = mapped_column(String(100), nullable=False)
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    confidence: Mapped[float] = mapped_column(default=0.5)

    property = relationship("Property", back_populates="raw_sources")