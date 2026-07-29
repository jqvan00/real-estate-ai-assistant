from __future__ import annotations

import csv
import io
import time
from functools import lru_cache

import requests
from fastapi import APIRouter, HTTPException, Query

from app.core.config import settings


router = APIRouter()

CENSUS_BASE_URL = "https://api.census.gov/data/2024/acs/acs5"
FRED_MORTGAGE_RATE_URL = (
    "https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US"
)
MORTGAGE_RATE_CACHE_SECONDS = 6 * 60 * 60
_mortgage_rate_cache: dict = {}

# State-level planning assumptions expressed as an annual percentage of the
# purchase price. They are deliberately conservative, editable in the UI, and
# are not insurance quotes.
INSURANCE_RATE_BY_STATE = {
    "AL": 0.58, "AK": 0.32, "AZ": 0.42, "AR": 0.62, "CA": 0.36,
    "CO": 0.57, "CT": 0.40, "DE": 0.34, "DC": 0.35, "FL": 1.05,
    "GA": 0.52, "HI": 0.28, "ID": 0.36, "IL": 0.48, "IN": 0.45,
    "IA": 0.47, "KS": 0.70, "KY": 0.50, "LA": 0.92, "ME": 0.38,
    "MD": 0.40, "MA": 0.38, "MI": 0.44, "MN": 0.50, "MS": 0.70,
    "MO": 0.58, "MT": 0.50, "NE": 0.67, "NV": 0.36, "NH": 0.34,
    "NJ": 0.38, "NM": 0.44, "NY": 0.40, "NC": 0.48, "ND": 0.58,
    "OH": 0.40, "OK": 0.82, "OR": 0.34, "PA": 0.38, "RI": 0.42,
    "SC": 0.55, "SD": 0.57, "TN": 0.50, "TX": 0.78, "UT": 0.34,
    "VT": 0.38, "VA": 0.38, "WA": 0.34, "WV": 0.42, "WI": 0.42,
    "WY": 0.42,
}

STATES = [
    ("01", "AL", "Alabama"), ("02", "AK", "Alaska"),
    ("04", "AZ", "Arizona"), ("05", "AR", "Arkansas"),
    ("06", "CA", "California"), ("08", "CO", "Colorado"),
    ("09", "CT", "Connecticut"), ("10", "DE", "Delaware"),
    ("11", "DC", "District of Columbia"), ("12", "FL", "Florida"),
    ("13", "GA", "Georgia"), ("15", "HI", "Hawaii"),
    ("16", "ID", "Idaho"), ("17", "IL", "Illinois"),
    ("18", "IN", "Indiana"), ("19", "IA", "Iowa"),
    ("20", "KS", "Kansas"), ("21", "KY", "Kentucky"),
    ("22", "LA", "Louisiana"), ("23", "ME", "Maine"),
    ("24", "MD", "Maryland"), ("25", "MA", "Massachusetts"),
    ("26", "MI", "Michigan"), ("27", "MN", "Minnesota"),
    ("28", "MS", "Mississippi"), ("29", "MO", "Missouri"),
    ("30", "MT", "Montana"), ("31", "NE", "Nebraska"),
    ("32", "NV", "Nevada"), ("33", "NH", "New Hampshire"),
    ("34", "NJ", "New Jersey"), ("35", "NM", "New Mexico"),
    ("36", "NY", "New York"), ("37", "NC", "North Carolina"),
    ("38", "ND", "North Dakota"), ("39", "OH", "Ohio"),
    ("40", "OK", "Oklahoma"), ("41", "OR", "Oregon"),
    ("42", "PA", "Pennsylvania"), ("44", "RI", "Rhode Island"),
    ("45", "SC", "South Carolina"), ("46", "SD", "South Dakota"),
    ("47", "TN", "Tennessee"), ("48", "TX", "Texas"),
    ("49", "UT", "Utah"), ("50", "VT", "Vermont"),
    ("51", "VA", "Virginia"), ("53", "WA", "Washington"),
    ("54", "WV", "West Virginia"), ("55", "WI", "Wisconsin"),
    ("56", "WY", "Wyoming"),
]

STATE_BY_FIPS = {
    fips: {"fips": fips, "code": code, "name": name}
    for fips, code, name in STATES
}


def _census_get(params: dict[str, str]) -> list[list[str]]:
    if not settings.census_api_key:
        raise RuntimeError(
            "CENSUS_API_KEY is required for county estimates. "
            "Request a free key at api.census.gov/data/key_signup.html."
        )
    response = requests.get(
        CENSUS_BASE_URL,
        params={**params, "key": settings.census_api_key},
        timeout=12,
        allow_redirects=False,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list) or len(payload) < 2:
        raise ValueError("Census returned no matching data")
    return payload


@lru_cache(maxsize=60)
def _counties_for_state(state_fips: str) -> tuple[tuple[str, str], ...]:
    payload = _census_get({
        "get": "NAME",
        "for": "county:*",
        "in": f"state:{state_fips}",
    })
    header = payload[0]
    name_index = header.index("NAME")
    county_index = header.index("county")
    return tuple(
        sorted(
            (
                (row[county_index], row[name_index].split(",")[0])
                for row in payload[1:]
            ),
            key=lambda item: item[1],
        )
    )


@lru_cache(maxsize=4000)
def _county_tax_statistics(state_fips: str, county_fips: str) -> dict:
    payload = _census_get({
        "get": "NAME,B25103_001E,B25077_001E",
        "for": f"county:{county_fips}",
        "in": f"state:{state_fips}",
    })
    header, row = payload[0], payload[1]
    median_tax = float(row[header.index("B25103_001E")])
    median_value = float(row[header.index("B25077_001E")])
    if median_tax <= 0 or median_value <= 0:
        raise ValueError("County tax statistics are unavailable")
    effective_rate = median_tax / median_value
    return {
        "county_name": row[header.index("NAME")].split(",")[0],
        "median_annual_tax": median_tax,
        "median_home_value": median_value,
        "effective_tax_rate": effective_rate,
    }


def _latest_mortgage_rate() -> dict:
    cached_at = float(_mortgage_rate_cache.get("cached_at") or 0)
    if (
        _mortgage_rate_cache.get("data")
        and time.time() - cached_at < MORTGAGE_RATE_CACHE_SECONDS
    ):
        return _mortgage_rate_cache["data"]

    response = requests.get(
        FRED_MORTGAGE_RATE_URL,
        timeout=12,
        allow_redirects=True,
    )
    response.raise_for_status()
    rows = list(csv.DictReader(io.StringIO(response.text)))
    for row in reversed(rows):
        raw_rate = row.get("MORTGAGE30US")
        if raw_rate and raw_rate != ".":
            data = {
                "rate_percent": float(raw_rate),
                "observation_date": row.get("observation_date"),
                "loan_type": "30-year fixed-rate mortgage",
                "source": "Freddie Mac Primary Mortgage Market Survey via FRED",
                "series": "MORTGAGE30US",
                "is_benchmark": True,
                "disclaimer": (
                    "National weekly benchmark, not a personalized rate quote. "
                    "Actual rates vary by borrower, lender, points, property, "
                    "occupancy, loan program, and market conditions."
                ),
            }
            _mortgage_rate_cache.update(
                {"cached_at": time.time(), "data": data}
            )
            return data
    raise ValueError("FRED returned no current mortgage-rate observation")


@router.get("/states")
def states():
    return {"states": list(STATE_BY_FIPS.values())}


@router.get("/mortgage-rate")
def mortgage_rate():
    try:
        return _latest_mortgage_rate()
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Mortgage-rate benchmark unavailable: {exc}",
        ) from exc


@router.get("/counties")
def counties(state: str = Query(..., min_length=2, max_length=2)):
    if state not in STATE_BY_FIPS:
        raise HTTPException(status_code=400, detail="Unknown state FIPS code")
    try:
        rows = _counties_for_state(state)
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail=f"County directory unavailable: {exc}"
        ) from exc
    return {
        "state": STATE_BY_FIPS[state],
        "counties": [
            {"fips": county_fips, "name": name}
            for county_fips, name in rows
        ],
    }


@router.get("/estimate")
def estimate(
    state: str = Query(..., min_length=2, max_length=2),
    county: str = Query(..., min_length=3, max_length=3),
    purchase_price: float = Query(..., gt=0),
):
    state_info = STATE_BY_FIPS.get(state)
    if not state_info:
        raise HTTPException(status_code=400, detail="Unknown state FIPS code")
    try:
        statistics = _county_tax_statistics(state, county)
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail=f"County tax estimate unavailable: {exc}"
        ) from exc

    tax_rate = statistics["effective_tax_rate"]
    insurance_rate = INSURANCE_RATE_BY_STATE.get(state_info["code"], 0.50) / 100
    return {
        "state": state_info,
        "county": {
            "fips": county,
            "name": statistics["county_name"],
        },
        "purchase_price": purchase_price,
        "property_tax": {
            "annual_estimate": round(purchase_price * tax_rate),
            "effective_rate_percent": round(tax_rate * 100, 3),
            "median_annual_tax": round(statistics["median_annual_tax"]),
            "median_home_value": round(statistics["median_home_value"]),
            "source": "U.S. Census ACS 2024 5-year county estimate",
            "method": "county median annual real estate tax divided by county median owner-occupied home value",
        },
        "homeowners_insurance": {
            "annual_estimate": round(purchase_price * insurance_rate),
            "planning_rate_percent": round(insurance_rate * 100, 3),
            "source": "state-level planning assumption",
            "method": "purchase price multiplied by an editable state planning rate; not an insurance quote",
        },
    }
