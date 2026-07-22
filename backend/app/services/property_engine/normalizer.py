from __future__ import annotations

from collections import Counter
from typing import Any


def _most_common(values: list[Any]) -> Any:
    if not values:
        return None
    counts = Counter([jsonable(v) for v in values if v is not None])
    if not counts:
        return None
    most_common_value = counts.most_common(1)[0][0]
    return most_common_value


def jsonable(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return tuple(sorted((k, jsonable(v)) for k, v in value.items()))
    if isinstance(value, list):
        return tuple(jsonable(v) for v in value)
    return repr(value)


def normalize_property_sources(address: str, listing_url: str | None, raw_sources: list[dict]) -> tuple[dict, dict, dict, str]:
    if not raw_sources:
        verified = {
            "address": address,
            "listing_url": listing_url,
            "property_type": "Unknown",
            "beds": None,
            "baths": None,
            "sqft": None,
            "lot_size_acres": None,
            "year_built": None,
            "estimated_value": None,
            "annual_taxes": None,
            "school_names": [],
            "nearby_places": [],
            "flood_risk": "Unknown",
        }
        analysis = {
            "briefing": "No property sources returned data.",
            "investment_snapshot": {},
            "schools": [],
            "flood_zone": "Unknown",
            "nearby_places": [],
            "commute": {},
            "neighborhood": {},
            "price_history": [],
            "renovation_value": {},
            "voice_prompt": "Ask me about the home, neighborhood, or value.",
            "pdf_report": {"status": "not_generated"},
        }
        return verified, analysis, {"sources": []}, "No raw sources available."

    beds = [src.get("structure", {}).get("beds") for src in raw_sources]
    baths = [src.get("structure", {}).get("baths") for src in raw_sources]
    sqft = [src.get("structure", {}).get("sqft") for src in raw_sources]
    year_built = [src.get("structure", {}).get("year_built") for src in raw_sources]
    property_types = [src.get("structure", {}).get("property_type") for src in raw_sources]
    lot_sizes = [src.get("parcel", {}).get("lot_size_acres") for src in raw_sources]
    estimated_values = [src.get("valuation", {}).get("estimated_value") for src in raw_sources]
    annual_taxes = [src.get("valuation", {}).get("annual_taxes") for src in raw_sources]
    schools = []
    nearby = []
    flood_risk = []
    source_names = []

    for src in raw_sources:
        source_names.append(src.get("source_name", "unknown"))
        schools.extend(src.get("amenities", {}).get("schools", []))
        nearby.extend(src.get("amenities", {}).get("nearby_places", []))
        flood_risk.append(src.get("environment", {}).get("flood_risk"))

    verified = {
        "address": address,
        "listing_url": listing_url,
        "property_type": _most_common(property_types) or "Unknown",
        "beds": _most_common(beds),
        "baths": _most_common(baths),
        "sqft": _most_common(sqft),
        "lot_size_acres": _most_common(lot_sizes),
        "year_built": _most_common(year_built),
        "estimated_value": _most_common(estimated_values),
        "annual_taxes": _most_common(annual_taxes),
        "school_names": sorted(set(schools)),
        "nearby_places": sorted(set(nearby)),
        "flood_risk": _most_common(flood_risk) or "Unknown",
        "source_count": len(raw_sources),
    }

    estimated_monthly_payment = round((verified["estimated_value"] or 0) * 0.0065, 2) if verified["estimated_value"] else None
    rent_estimate = round((verified["estimated_value"] or 0) * 0.0068, 2) if verified["estimated_value"] else None

    analysis = {
        "briefing": f"Verified profile assembled for {address}.",
        "investment_snapshot": {
            "estimated_monthly_payment": estimated_monthly_payment,
            "estimated_rent": rent_estimate,
            "cap_rate_estimate": round(((rent_estimate or 0) * 12 / (verified["estimated_value"] or 1)) * 100, 2) if verified["estimated_value"] else None,
            "note": "Estimate only; validate with real lender and rent comps.",
        },
        "schools": verified["school_names"],
        "flood_zone": verified["flood_risk"],
        "nearby_places": verified["nearby_places"],
        "commute": {
            "to_downtown_minutes": 18,
            "to_airport_minutes": 28,
            "note": "Estimated from demo engine. Replace with live routing later.",
        },
        "neighborhood": {
            "summary": "Family-friendly suburban demo profile with basic amenities nearby.",
            "market_position": "Balanced",
        },
        "price_history": [
            {"year": 2022, "value": verified["estimated_value"] and int(verified["estimated_value"] * 0.85) or None},
            {"year": 2023, "value": verified["estimated_value"] and int(verified["estimated_value"] * 0.92) or None},
            {"year": 2024, "value": verified["estimated_value"]},
        ],
        "renovation_value": {
            "light_refresh_roi": "Moderate",
            "kitchen_refresh": "Potentially strong",
            "bath_refresh": "Potentially strong",
            "note": "Demo estimates only.",
        },
        "voice_prompt": f"Ask me anything about {address}.",
        "pdf_report": {
            "status": "ready_to_generate",
            "file_name": "showing_report.pdf",
        },
        "sources_used": source_names,
    }

    source_breakdown = {
        "sources": [
            {"name": src.get("source_name"), "type": src.get("source_type"), "confidence": src.get("confidence", 0.5)}
            for src in raw_sources
        ]
    }

    notes = "Values are merged from local demo engines. Replace connectors with live APIs later."
    return verified, analysis, source_breakdown, notes
