from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.property import Property
from app.models.property_profile import PropertyProfile
from app.models.property_raw_source import PropertyRawSource
from app.schemas.property import PropertyAnalyzeRequest
from app.services.property_engine.connectors.attom import ATTOMConnector
from app.services.property_engine.connectors.environment import EnvironmentConnector
from app.services.property_engine.connectors.estated import EstatedConnector
from app.services.property_engine.connectors.maps import MapsConnector
from app.services.property_engine.connectors.rentcast import RentCastConnector
from app.services.property_engine.connectors.regrid import RegridConnector
from app.services.property_engine.connectors.schools import SchoolsConnector
from app.services.property_engine.normalizer import normalize_property_sources


CONNECTORS = [
    ATTOMConnector(),
    RentCastConnector(),
    EstatedConnector(),
    RegridConnector(),
    MapsConnector(),
    SchoolsConnector(),
    EnvironmentConnector(),
]


def analyze_property(db: Session, payload: PropertyAnalyzeRequest) -> Property:
    prop = db.query(Property).filter(Property.address == payload.address).first()
    if not prop:
        prop = Property(address=payload.address, listing_url=payload.listing_url)
        db.add(prop)
        db.commit()
        db.refresh(prop)
    else:
        prop.listing_url = payload.listing_url

    raw_sources: list[dict] = []
    for connector in CONNECTORS:
        raw = connector.fetch(payload.address, payload.listing_url)
        raw_sources.append(raw)
        db.add(
            PropertyRawSource(
                property_id=prop.id,
                source_name=raw.get("source_name", connector.name),
                source_type=raw.get("source_type", "property"),
                raw_payload=raw,
                confidence=float(raw.get("confidence", 0.5)),
            )
        )

    verified, analysis, source_breakdown, notes = normalize_property_sources(
        payload.address,
        payload.listing_url,
        raw_sources,
    )

    summary = (
        f"{verified['property_type']} | "
        f"{verified['beds']} bd | "
        f"{verified['baths']} ba | "
        f"{verified['sqft']} sqft | "
        f"Est. value: {verified['estimated_value']}"
    )

    prop.city = "Demo City"
    prop.state = "AR"
    prop.zip_code = "72712"
    prop.verified_summary = summary

    profile = db.query(PropertyProfile).filter(PropertyProfile.property_id == prop.id).first()
    if not profile:
        profile = PropertyProfile(
            property_id=prop.id,
            verified_payload=verified,
            analysis_payload=analysis,
            source_breakdown=source_breakdown,
            notes=notes,
        )
        db.add(profile)
    else:
        profile.verified_payload = verified
        profile.analysis_payload = analysis
        profile.source_breakdown = source_breakdown
        profile.notes = notes

    db.commit()
    db.refresh(prop)
    return prop
