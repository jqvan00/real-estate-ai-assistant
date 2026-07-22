from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.property_profile import PropertyProfile
from app.services.analysis_service import get_property_analysis

router = APIRouter()


@router.get("/{property_id}")
def property_analysis(property_id: int, db: Session = Depends(get_db)):
    return get_property_analysis(db, property_id)


@router.get("/{property_id}/investment")
def investment(property_id: int, db: Session = Depends(get_db)):
    analysis = get_property_analysis(db, property_id)
    return analysis.get("analysis", {}).get("investment_snapshot", {})


@router.get("/{property_id}/schools")
def schools(property_id: int, db: Session = Depends(get_db)):
    analysis = get_property_analysis(db, property_id)
    return analysis.get("analysis", {}).get("schools", [])


@router.get("/{property_id}/flood")
def flood(property_id: int, db: Session = Depends(get_db)):
    analysis = get_property_analysis(db, property_id)
    return {"flood_zone": analysis.get("analysis", {}).get("flood_zone", "Unknown")}


@router.get("/{property_id}/nearby")
def nearby(property_id: int, db: Session = Depends(get_db)):
    analysis = get_property_analysis(db, property_id)
    return analysis.get("analysis", {}).get("nearby_places", [])


@router.get("/{property_id}/commute")
def commute(property_id: int, db: Session = Depends(get_db)):
    analysis = get_property_analysis(db, property_id)
    return analysis.get("analysis", {}).get("commute", {})


@router.get("/{property_id}/neighborhood")
def neighborhood(property_id: int, db: Session = Depends(get_db)):
    analysis = get_property_analysis(db, property_id)
    return analysis.get("analysis", {}).get("neighborhood", {})


@router.get("/{property_id}/price-history")
def price_history(property_id: int, db: Session = Depends(get_db)):
    analysis = get_property_analysis(db, property_id)
    return analysis.get("analysis", {}).get("price_history", [])


@router.get("/{property_id}/renovation")
def renovation(property_id: int, db: Session = Depends(get_db)):
    analysis = get_property_analysis(db, property_id)
    return analysis.get("analysis", {}).get("renovation_value", {})


@router.get("/{property_id}/voice")
def voice(property_id: int, db: Session = Depends(get_db)):
    analysis = get_property_analysis(db, property_id)
    return {"voice_prompt": analysis.get("analysis", {}).get("voice_prompt", "")}
