from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.property import Property
from app.models.property_verified_profile import PropertyVerifiedProfile
from app.schemas.property import PropertyAnalyzeRequest, PropertyAnalyzeResponse, PropertyOut
from app.services.analysis_service import get_property_analysis
from app.services.property_service import analyze_property

router = APIRouter()


@router.post("/analyze", response_model=PropertyAnalyzeResponse)
def analyze(payload: PropertyAnalyzeRequest, db: Session = Depends(get_db)):
    prop = analyze_property(db, payload)
    profile = db.query(PropertyVerifiedProfile).filter(PropertyVerifiedProfile.property_id == prop.id).first()
    if not profile:
        raise HTTPException(status_code=500, detail="Property verified profile was not created")
    return PropertyAnalyzeResponse(
        property_id=prop.id,
        address=prop.address,
        verified_profile=profile.verified_payload,
        analysis=profile.analysis_payload,
        source_breakdown=profile.source_breakdown,
    )


@router.get("/{property_id}", response_model=PropertyOut)
def get_property(property_id: int, db: Session = Depends(get_db)):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    profile = db.query(PropertyVerifiedProfile).filter(PropertyVerifiedProfile.property_id == property_id).first()
    return PropertyOut(
        id=prop.id,
        address=prop.address,
        listing_url=prop.listing_url,
        city=prop.city,
        state=prop.state,
        zip_code=prop.zip_code,
        verified_summary=prop.verified_summary,
        profile=profile.verified_payload if profile else None,
    )


@router.post("/{property_id}/refresh")
def refresh(property_id: int, db: Session = Depends(get_db)):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return get_property_analysis(db, property_id)