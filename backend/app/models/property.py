from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    address: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    listing_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    state: Mapped[str | None] = mapped_column(String(255), nullable=True)
    zip_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    verified_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    raw_sources = relationship(
        "PropertyRawSource",
        back_populates="property",
        cascade="all, delete-orphan",
    )
    verified_profile = relationship(
        "PropertyVerifiedProfile",
        back_populates="property",
        uselist=False,
        cascade="all, delete-orphan",
    )
    api_cache_entries = relationship(
        "PropertyApiCache",
        back_populates="property",
        cascade="all, delete-orphan",
    )
    reports = relationship("Report", back_populates="property")
    conversations = relationship("Conversation", back_populates="prop")
    saved_by = relationship("SavedProperty", back_populates="property")