from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.property import Property
from app.models.property_profile import PropertyProfile


def get_property_analysis(db: Session, property_id: int) -> dict:
    prop = db.query(Property).filter(Property.id == property_id).first()
    profile = db.query(PropertyProfile).filter(PropertyProfile.property_id == property_id).first()
    if not prop or not profile:
        return {"status": "not_found"}

    return {
        "property_id": prop.id,
        "address": prop.address,
        "verified_profile": profile.verified_payload,
        "analysis": profile.analysis_payload,
        "source_breakdown": profile.source_breakdown,
        "notes": profile.notes,
    }
