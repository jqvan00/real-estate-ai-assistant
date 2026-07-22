from sqlalchemy import ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class PropertyProfile(Base):
    __tablename__ = "property_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), unique=True, nullable=False, index=True)
    verified_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    analysis_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    source_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    property = relationship("Property", back_populates="profile")
