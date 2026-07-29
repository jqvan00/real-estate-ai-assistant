from __future__ import annotations

from datetime import datetime, timedelta, timezone
import re
from statistics import median
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.integrations.census.geocoder import CensusGeocoderConnector
from app.integrations.rentcast import RentCastConnector
from app.integrations.rapidapi_zillow import RapidAPIZillowConnector
from app.integrations.zillow_live_data import ZillowLiveDataConnector
from app.integrations.zillapi import ZillAPIConnector
from app.integrations.realtor16 import Realtor16Connector
from app.integrations.demo import DemoPropertyConnector
from app.integrations.nearby_schools import NearbySchoolsConnector
from app.integrations.url_parser import (
    extract_address_from_listing_url,
    extract_zillow_zpid,
)
from app.models.property import Property
from app.models.property_api_cache import PropertyApiCache
from app.models.property_raw_source import PropertyRawSource
from app.models.property_verified_profile import PropertyVerifiedProfile
from app.schemas.property import PropertyAnalyzeRequest


# Keep successful upstream responses for one week. This prevents repeated
# property searches during testing (or multiple showings for the same home)
# from spending another provider credit each time.
CACHE_TTL_HOURS = 24 * 7


def _normalize_address(address: str) -> str:
    suffixes = {
        "street": "st",
        "avenue": "ave",
        "boulevard": "blvd",
        "drive": "dr",
        "lane": "ln",
        "road": "rd",
        "court": "ct",
        "circle": "cir",
        "parkway": "pkwy",
        "place": "pl",
        "terrace": "ter",
        "trail": "trl",
    }
    tokens = re.findall(r"[a-z0-9]+", address.lower())
    return " ".join(suffixes.get(token, token) for token in tokens)


def _addresses_match(first: str | None, second: str | None) -> bool:
    if not first or not second:
        return False
    return _normalize_address(first) == _normalize_address(second)


def _cache_key(source_name: str, endpoint: str, address: str) -> str:
    return f"{source_name}:{endpoint}:{_normalize_address(address)}"


def _get_cached_response(db: Session, source_name: str, endpoint: str, address: str) -> dict[str, Any] | None:
    key = _cache_key(source_name, endpoint, address)
    now = datetime.now(timezone.utc)

    entry = (
        db.query(PropertyApiCache)
        .filter(PropertyApiCache.cache_key == key)
        .filter(PropertyApiCache.expires_at > now)
        .first()
    )
    if not entry:
        return None

    if entry.response_json.get("status") == "error":
        return None

    return entry.response_json


def _set_cached_response(
    db: Session,
    property_id: int,
    source_name: str,
    endpoint: str,
    address: str,
    response_json: dict[str, Any],
) -> None:
    key = _cache_key(source_name, endpoint, address)
    now = datetime.now(timezone.utc)

    entry = db.query(PropertyApiCache).filter(PropertyApiCache.cache_key == key).first()
    if not entry:
        entry = PropertyApiCache(
            property_id=property_id,
            source_name=source_name,
            endpoint=endpoint,
            cache_key=key,
            response_json=response_json,
            expires_at=now + timedelta(hours=CACHE_TTL_HOURS),
        )
        db.add(entry)
        return

    entry.property_id = property_id
    entry.source_name = source_name
    entry.endpoint = endpoint
    entry.response_json = response_json
    entry.expires_at = now + timedelta(hours=CACHE_TTL_HOURS)


def _latest_tax_info(property_taxes: Any) -> tuple[int | None, float | int | None]:
    if not isinstance(property_taxes, dict) or not property_taxes:
        return None, None

    latest_year_key = sorted(property_taxes.keys())[-1]
    latest_entry = property_taxes.get(latest_year_key, {}) or {}
    tax_total = latest_entry.get("total")
    return int(latest_year_key), tax_total


def _listing_market_activity(
    property_record: dict[str, Any],
) -> tuple[Any, Any]:
    listed_date = property_record.get("listedDate")
    latest_price_change_date = None
    price_history = property_record.get("priceHistory")
    if not isinstance(price_history, list):
        return listed_date, latest_price_change_date

    for entry in price_history:
        if not isinstance(entry, dict):
            continue
        event = str(entry.get("event") or "").lower()
        event_date = entry.get("date") or entry.get("time")
        if not listed_date and "listed" in event:
            listed_date = event_date
        if latest_price_change_date is None and (
            "price change" in event
            or "price cut" in event
            or "price decreased" in event
            or "price increased" in event
            or entry.get("priceChangeRate") not in (None, 0, 0.0)
        ):
            latest_price_change_date = event_date

    return listed_date, latest_price_change_date


def _latest_price_change(price_history: Any) -> dict[str, Any]:
    if not isinstance(price_history, list):
        return {}

    for index, entry in enumerate(price_history):
        if not isinstance(entry, dict):
            continue
        event = str(entry.get("event") or "").lower()
        if not any(
            label in event
            for label in (
                "price change",
                "price cut",
                "price decreased",
                "price increased",
            )
        ):
            continue

        current_price = entry.get("price")
        if not isinstance(current_price, (int, float)) or current_price <= 0:
            continue

        previous_price = None
        for older_entry in price_history[index + 1 :]:
            if not isinstance(older_entry, dict):
                continue
            older_price = older_entry.get("price")
            if isinstance(older_price, (int, float)) and older_price > 0:
                previous_price = float(older_price)
                break

        rate = entry.get("priceChangeRate")
        if (
            previous_price is None
            and isinstance(rate, (int, float))
            and rate != -1
        ):
            previous_price = float(current_price) / (1 + float(rate))

        if previous_price is None or previous_price <= 0:
            return {
                "date": entry.get("date") or entry.get("time"),
                "current_price": round(float(current_price)),
            }

        signed_percent = (
            (float(current_price) - previous_price) / previous_price * 100
        )
        direction = (
            "increase"
            if signed_percent > 0
            else "decrease"
            if signed_percent < 0
            else "no change"
        )
        return {
            "date": entry.get("date") or entry.get("time"),
            "previous_price": round(previous_price),
            "current_price": round(float(current_price)),
            "percent": round(abs(signed_percent), 1),
            "direction": direction,
        }

    return {}


def _normalized_price_history(price_history: Any) -> list[dict[str, Any]]:
    if not isinstance(price_history, list):
        return []

    normalized: list[dict[str, Any]] = []
    for index, entry in enumerate(price_history):
        if not isinstance(entry, dict):
            continue
        price = entry.get("price")
        if not isinstance(price, (int, float)) or price <= 0:
            continue

        previous_price = None
        for older_entry in price_history[index + 1 :]:
            if not isinstance(older_entry, dict):
                continue
            older_price = older_entry.get("price")
            if isinstance(older_price, (int, float)) and older_price > 0:
                previous_price = float(older_price)
                break

        event = str(entry.get("event") or "Price event")
        event_lower = event.lower()
        is_price_change = any(
            label in event_lower
            for label in (
                "price change",
                "price cut",
                "price decreased",
                "price increased",
            )
        )
        dollar_change = None
        percent_change = None
        direction = None
        if is_price_change and previous_price:
            dollar_change = round(float(price) - previous_price)
            signed_percent = dollar_change / previous_price * 100
            percent_change = round(abs(signed_percent), 1)
            direction = (
                "increase"
                if dollar_change > 0
                else "decrease"
                if dollar_change < 0
                else "no change"
            )

        normalized.append(
            {
                "date": entry.get("date") or entry.get("time"),
                "event": event,
                "price": round(float(price)),
                "dollar_change": dollar_change,
                "percent_change": percent_change,
                "direction": direction,
            }
        )

    return normalized


def _median_comparable_value(
    comparables: list[dict[str, Any]],
    radius_miles: float,
) -> tuple[int | None, int]:
    prices = [
        float(comparable["price"])
        for comparable in comparables
        if comparable.get("price") is not None
        and comparable.get("distance") is not None
        and float(comparable["distance"]) <= radius_miles
    ]
    return (round(median(prices)), len(prices)) if prices else (None, 0)


def analyze_property(db: Session, payload: PropertyAnalyzeRequest) -> Property:
    # If listing_url is provided, try to extract address from it
    search_address = payload.address

    if payload.listing_url and not search_address:
        # Try to extract address from URL
        extracted = extract_address_from_listing_url(payload.listing_url)
        if extracted:
            search_address = extracted
        else:
            raise ValueError(
                "Could not extract address from listing URL. "
                "Please paste the property address directly instead."
            )

    if not search_address:
        raise ValueError("Address is required")

    prop = next(
        (
            candidate
            for candidate in db.query(Property).all()
            if _addresses_match(candidate.address, search_address)
        ),
        None,
    )
    if not prop:
        prop = Property(address=search_address, listing_url=payload.listing_url)
        db.add(prop)
        db.commit()
        db.refresh(prop)
    else:
        prop.listing_url = payload.listing_url

    existing_profile = (
        db.query(PropertyVerifiedProfile)
        .filter(PropertyVerifiedProfile.property_id == prop.id)
        .first()
    )

    raw_sources: list[dict[str, Any]] = []

    # Check if demo mode is enabled
    if settings.demo_mode:
        # Use demo data instead of real APIs
        demo_connector = DemoPropertyConnector()
        rentcast_record = demo_connector.fetch_property_record(search_address)
        rentcast_value = demo_connector.fetch_value_estimate(search_address)

        raw_sources.append(rentcast_record)
        raw_sources.append(rentcast_value)

        # Use demo data for geocoding too
        record = rentcast_record.get("record", {})
        if record:
            raw_geo = {
                "source": "demo_geocoder",
                "status": "matched",
                "formatted_address": record.get("formattedAddress"),
                "latitude": record.get("latitude"),
                "longitude": record.get("longitude"),
                "county": record.get("county"),
                "state": record.get("state"),
                "zip_code": record.get("zipCode"),
            }
        else:
            raw_geo = {"source": "demo_geocoder", "status": "no_match"}
    else:
        # Use real APIs
        # Census geocoder: cache it too (with error handling)
        cached_geo = _get_cached_response(db, "census_geocoder", "geocoding", search_address)
        if cached_geo:
            raw_geo = cached_geo
        else:
            try:
                geocoder = CensusGeocoderConnector()
                raw_geo = geocoder.fetch(search_address)
            except Exception as e:
                # Census geocoder failed (DNS or other error), use fallback
                print(f"Census geocoder failed: {e}")
                raw_geo = {
                    "source": "census_geocoder",
                    "status": "error",
                    "formatted_address": search_address,
                    "latitude": None,
                    "longitude": None,
                    "county": None,
                    "state": None,
                    "zip_code": None,
                }
            _set_cached_response(db, prop.id, "census_geocoder", "geocoding", search_address, raw_geo)

    raw_sources.append(raw_geo)

    db.add(
        PropertyRawSource(
            property_id=prop.id,
            source_name=raw_geo.get("source", "census_geocoder"),
            source_type="geocoding",
            raw_payload=raw_geo,
            confidence=1.0 if raw_geo.get("status") == "matched" else 0.0,
        )
    )

    rentcast_record: dict[str, Any]
    rentcast_value: dict[str, Any]

    if settings.demo_mode:
        # Already set above in demo mode block - don't overwrite!
        pass
    elif settings.zillapi_key:
        endpoint = (
            "properties/by-url"
            if payload.listing_url and "zillow.com" in payload.listing_url.lower()
            else "properties/by-address"
        )
        cached_property_record = _get_cached_response(
            db, "zillapi", endpoint, search_address
        )
        if cached_property_record:
            rentcast_record = cached_property_record
            cached_raw = (
                (rentcast_record.get("record") or {}).get("rawZillAPI")
                if isinstance(rentcast_record, dict)
                else None
            )
            if isinstance(cached_raw, dict) and cached_raw:
                rentcast_record["record"] = ZillAPIConnector._normalize_property(
                    cached_raw
                )
        else:
            try:
                zillapi = ZillAPIConnector()
                rentcast_record = zillapi.fetch_property_record(
                    search_address, payload.listing_url
                )
            except Exception as exc:
                print(f"ZillAPI property lookup failed: {exc}")
                rentcast_record = {
                    "source": "zillapi",
                    "endpoint": endpoint,
                    "status": "error",
                    "error": str(exc),
                    "record": {},
                }
            _set_cached_response(
                db,
                prop.id,
                "zillapi",
                endpoint,
                search_address,
                rentcast_record,
            )

        if rentcast_record.get("status") == "matched":
            rentcast_value = ZillAPIConnector().fetch_value_estimate(
                rentcast_record.get("record", {})
            )
        else:
            rentcast_value = {
                "source": "zillapi",
                "endpoint": "property-detail",
                "status": "no_match",
                "value": {},
            }

        zillapi_comps: dict[str, Any] | None = None
        comparable_limit = min(max(payload.max_comparables, 1), 5)
        comparable_cache_endpoint = (
            f"search/recently-sold:{comparable_limit}"
        )
        if (
            payload.include_comparables
            and rentcast_record.get("status") == "matched"
        ):
            cached_comps = _get_cached_response(
                db,
                "zillapi",
                comparable_cache_endpoint,
                search_address,
            )
            if cached_comps:
                zillapi_comps = cached_comps
            else:
                try:
                    zillapi_comps = (
                        ZillAPIConnector().fetch_recently_sold_comparables(
                            rentcast_record.get("record", {}),
                            max_items=comparable_limit,
                        )
                    )
                except Exception as exc:
                    print(f"ZillAPI comparable search failed: {exc}")
                    zillapi_comps = {
                        "source": "zillapi",
                        "endpoint": "search/recently-sold",
                        "status": "error",
                        "error": str(exc),
                        "comparables": [],
                    }
                _set_cached_response(
                    db,
                    prop.id,
                    "zillapi",
                    comparable_cache_endpoint,
                    search_address,
                    zillapi_comps,
                )

            if zillapi_comps.get("status") == "ok":
                rentcast_value.setdefault("value", {})["comparables"] = (
                    zillapi_comps.get("comparables", [])
                )
                rentcast_value["value"]["comparablesSource"] = (
                    "ZillAPI recently sold"
                )
            raw_sources.append(zillapi_comps)

        # RentCast is now only a fallback when ZillAPI returns no usable closed
        # sales. Its Zestimate-equivalent never overrides ZillAPI's value.
        if (
            payload.include_comparables
            and
            settings.rentcast_api_key
            and (
                not zillapi_comps
                or zillapi_comps.get("status") != "ok"
            )
        ):
            try:
                comparable_value = RentCastConnector().fetch_value_estimate(
                    search_address
                )
                if comparable_value.get("status") == "ok":
                    zillapi_value = rentcast_value.get("value", {})
                    rentcast_avm = comparable_value.get("value", {})
                    zillapi_value["comparables"] = rentcast_avm.get(
                        "comparables", []
                    )
                    zillapi_value["comparablesSource"] = "RentCast fallback"
                    raw_sources.append(comparable_value)
            except Exception as exc:
                print(f"RentCast comparable lookup failed: {exc}")

        _set_cached_response(
            db,
            prop.id,
            "zillapi",
            "property-detail",
            search_address,
            rentcast_value,
        )
    elif settings.use_rapidapi and settings.rapidapi_key:
        # Try multiple RapidAPI sources in order: Zillow Live Data -> Real Estate Zillow -> RentCast
        rentcast_record = {"source": "none", "status": "no_match", "record": {}}
        rentcast_value = {"source": "none", "status": "no_match", "value": {}}

        # Try 1: Zillow Live Data Scraper (best coverage)
        try:
            zillow_live = ZillowLiveDataConnector()
            rentcast_record = zillow_live.fetch_property_record(search_address)
            if rentcast_record.get("status") == "matched":
                rentcast_value = zillow_live.fetch_value_estimate(
                    search_address,
                    rentcast_record.get("record", {}),
                )
                print(f"SUCCESS: Got data from Zillow Live Data")
        except Exception as e:
            print(f"Zillow Live Data failed: {e}")

        # Try 2: Real Estate Zillow (if first failed)
        if rentcast_record.get("status") != "matched":
            try:
                zillow_api = RapidAPIZillowConnector()
                rentcast_record = zillow_api.fetch_property_record(search_address)
                if rentcast_record.get("status") == "matched":
                    rentcast_value = zillow_api.fetch_value_estimate(search_address)
                    print(f"SUCCESS: Got data from Real Estate Zillow")
            except Exception as e:
                print(f"Real Estate Zillow failed: {e}")

        # Try 3: Realtor16 (if both failed)
        if rentcast_record.get("status") != "matched":
            try:
                realtor = Realtor16Connector()
                rentcast_record = realtor.fetch_property_record(search_address)
                if rentcast_record.get("status") == "matched":
                    rentcast_value = realtor.fetch_value_estimate(search_address)
                    print(f"SUCCESS: Got data from Realtor16")
            except Exception as e:
                print(f"Realtor16 failed: {e}")

        # A configured RapidAPI key should not prevent the reliable property
        # record provider from acting as the final fallback.
        if (
            rentcast_record.get("status") != "matched"
            and settings.rentcast_api_key
        ):
            try:
                rentcast = RentCastConnector()
                rentcast_record = rentcast.fetch_property_record(search_address)
                if rentcast_record.get("status") == "matched":
                    rentcast_value = rentcast.fetch_value_estimate(search_address)
                    print("SUCCESS: Got data from RentCast")
            except Exception as e:
                print(f"RentCast fallback failed: {e}")

        # Lightweight listing searches do not always include county-record
        # fields such as year built. Enrich only missing values from RentCast.
        if (
            rentcast_record.get("status") == "matched"
            and settings.rentcast_api_key
            and not (rentcast_record.get("record") or {}).get("yearBuilt")
        ):
            cached_enrichment = _get_cached_response(
                db,
                "rentcast",
                "properties",
                search_address,
            )
            if cached_enrichment:
                property_enrichment = cached_enrichment
            else:
                try:
                    property_enrichment = RentCastConnector().fetch_property_record(
                        search_address
                    )
                except Exception as e:
                    print(f"RentCast property enrichment failed: {e}")
                    property_enrichment = {
                        "source": "rentcast",
                        "status": "error",
                        "record": {},
                    }
                _set_cached_response(
                    db,
                    prop.id,
                    "rentcast",
                    "properties",
                    search_address,
                    property_enrichment,
                )

            enrichment_record = property_enrichment.get("record", {})
            primary_record = rentcast_record.get("record", {})
            for field, value in enrichment_record.items():
                if primary_record.get(field) in (None, "", []):
                    primary_record[field] = value
            raw_sources.append(property_enrichment)

        # Cache the results
        _set_cached_response(db, prop.id, rentcast_record.get("source", "rapidapi"), "search", search_address, rentcast_record)
        _set_cached_response(db, prop.id, rentcast_value.get("source", "rapidapi"), "estimate", search_address, rentcast_value)
    elif settings.rentcast_api_key:
        cached_property_record = _get_cached_response(db, "rentcast", "properties", search_address)
        cached_value_estimate = _get_cached_response(db, "rentcast", "avm/value", search_address)

        if cached_property_record:
            rentcast_record = cached_property_record
        else:
            rentcast = RentCastConnector()
            try:
                rentcast_record = rentcast.fetch_property_record(search_address)
            except ConnectionError as conn_err:
                # Network/connection issue
                rentcast_record = {
                    "source": "rentcast",
                    "endpoint": "properties",
                    "status": "connection_error",
                    "error": str(conn_err),
                    "record": {},
                }
            except Exception as exc:
                rentcast_record = {
                    "source": "rentcast",
                    "endpoint": "properties",
                    "status": "error",
                    "error": str(exc),
                    "record": {},
                }
            _set_cached_response(db, prop.id, "rentcast", "properties", search_address, rentcast_record)

        if cached_value_estimate:
            rentcast_value = cached_value_estimate
        else:
            rentcast = RentCastConnector()
            try:
                rentcast_value = rentcast.fetch_value_estimate(search_address)
            except ConnectionError as conn_err:
                # Network/connection issue
                rentcast_value = {
                    "source": "rentcast",
                    "endpoint": "avm/value",
                    "status": "connection_error",
                    "error": str(conn_err),
                    "value": {},
                }
            except Exception as exc:
                rentcast_value = {
                    "source": "rentcast",
                    "endpoint": "avm/value",
                    "status": "error",
                    "error": str(exc),
                    "value": {},
                }
            _set_cached_response(db, prop.id, "rentcast", "avm/value", search_address, rentcast_value)
    else:
        rentcast_record = {"source": "rentcast", "endpoint": "properties", "status": "skipped", "record": {}}
        rentcast_value = {"source": "rentcast", "endpoint": "avm/value", "status": "skipped", "value": {}}

    raw_sources.extend([rentcast_record, rentcast_value])

    active_listing: dict[str, Any] | None = None
    if (
        payload.listing_url
        and settings.rentcast_api_key
        and rentcast_record.get("source") != "zillapi"
    ):
        cached_listing = _get_cached_response(
            db,
            "rentcast",
            "listings/sale",
            search_address,
        )
        if cached_listing:
            active_listing = cached_listing
        else:
            try:
                active_listing = RentCastConnector().fetch_active_sale_listing(
                    search_address
                )
            except Exception as e:
                print(f"Active listing lookup failed: {e}")
                active_listing = {
                    "source": "rentcast",
                    "endpoint": "listings/sale",
                    "status": "error",
                    "record": {},
                }
            _set_cached_response(
                db,
                prop.id,
                "rentcast",
                "listings/sale",
                search_address,
                active_listing,
            )
        raw_sources.append(active_listing)

    db.add(
        PropertyRawSource(
            property_id=prop.id,
            source_name=rentcast_record.get("source", "rentcast"),
            source_type="property_record",
            raw_payload=rentcast_record,
            confidence=1.0 if rentcast_record.get("status") == "matched" else 0.5,
        )
    )
    db.add(
        PropertyRawSource(
            property_id=prop.id,
            source_name=rentcast_value.get("source", "rentcast"),
            source_type="valuation",
            raw_payload=rentcast_value,
            confidence=1.0 if rentcast_value.get("status") == "ok" else 0.5,
        )
    )

    property_record = rentcast_record.get("record", {}) if isinstance(rentcast_record, dict) else {}
    if active_listing and active_listing.get("status") == "matched":
        listing_record = active_listing.get("record", {})
        for field, value in listing_record.items():
            if field in {
                "price",
                "status",
                "listingType",
                "listedDate",
                "daysOnMarket",
                "mlsName",
                "mlsNumber",
            } or property_record.get(field) in (None, "", []):
                property_record[field] = value
    avm = rentcast_value.get("value", {}) if isinstance(rentcast_value, dict) else {}
    subject_property = avm.get("subjectProperty", {}) if isinstance(avm, dict) else {}
    comparables = avm.get("comparables", []) if isinstance(avm, dict) else []
    listed_date, last_price_change_date = _listing_market_activity(
        property_record
    )
    latest_price_change = _latest_price_change(
        property_record.get("priceHistory")
    )
    normalized_price_history = _normalized_price_history(
        property_record.get("priceHistory")
    )
    listing_is_authoritative = bool(
        rentcast_record.get("source") == "zillapi"
        and rentcast_record.get("status") == "matched"
    ) or bool(
        payload.listing_url
        and active_listing
        and active_listing.get("status") == "matched"
    )

    # Handle tax info from different sources
    if settings.demo_mode:
        # Demo mode has direct fields
        tax_year = property_record.get("taxYear")
        tax_total = property_record.get("taxTotal")
    else:
        # RentCast API has nested propertyTaxes array
        tax_year, tax_total = _latest_tax_info(property_record.get("propertyTaxes"))

    verified_payload = {
        "address": search_address,
        "listing_url": payload.listing_url,
        "zillow_zpid": extract_zillow_zpid(payload.listing_url or ""),
        "formatted_address": (
            property_record.get("formattedAddress")
            if listing_is_authoritative
            else raw_geo.get("formatted_address")
        )
        or property_record.get("formattedAddress")
        or raw_geo.get("formatted_address")
        or subject_property.get("formattedAddress"),
        "latitude": (
            property_record.get("latitude")
            if listing_is_authoritative
            else raw_geo.get("latitude")
        )
        or property_record.get("latitude")
        or raw_geo.get("latitude")
        or subject_property.get("latitude"),
        "longitude": (
            property_record.get("longitude")
            if listing_is_authoritative
            else raw_geo.get("longitude")
        )
        or property_record.get("longitude")
        or raw_geo.get("longitude")
        or subject_property.get("longitude"),
        "county": (
            property_record.get("county")
            if listing_is_authoritative
            else raw_geo.get("county")
        )
        or property_record.get("county")
        or raw_geo.get("county")
        or subject_property.get("county"),
        "state": (
            property_record.get("state")
            if listing_is_authoritative
            else raw_geo.get("state")
        )
        or property_record.get("state")
        or raw_geo.get("state")
        or subject_property.get("state"),
        "zip_code": (
            property_record.get("zipCode")
            if listing_is_authoritative
            else raw_geo.get("zip_code")
        )
        or property_record.get("zipCode")
        or raw_geo.get("zip_code")
        or subject_property.get("zipCode"),
        "property_type": property_record.get("propertyType") or subject_property.get("propertyType") or "Single Family",
        "bedrooms": property_record.get("bedrooms") or subject_property.get("bedrooms"),
        "bathrooms": property_record.get("bathrooms") or subject_property.get("bathrooms"),
        "square_footage": property_record.get("squareFootage") or subject_property.get("squareFootage"),
        "lot_size": property_record.get("lotSize") or subject_property.get("lotSize") or "N/A",
        "year_built": property_record.get("yearBuilt") or subject_property.get("yearBuilt"),
        "listing_status": subject_property.get("status") or property_record.get("status"),
        "listing_price": subject_property.get("price") or property_record.get("price"),
        "estimated_value": avm.get("price"),
        "estimated_value_source": (
            "ZillAPI Zestimate"
            if rentcast_record.get("source") == "zillapi"
            and property_record.get("zestimate") is not None
            else None
        ),
        "estimated_value_low": avm.get("priceRangeLow"),
        "estimated_value_high": avm.get("priceRangeHigh"),
        "last_sale_date": property_record.get("lastSaleDate") or subject_property.get("lastSaleDate"),
        "last_sale_price": property_record.get("lastSalePrice") or subject_property.get("lastSalePrice"),
        "owner_names": (property_record.get("owner") or {}).get("names", []),
        "owner_occupied": (property_record.get("owner") or {}).get("ownerOccupied"),
        "hoa_fee": property_record.get("hoaFee"),
        "tax_year": tax_year,
        "tax_total": tax_total,
        "comparables_count": len(comparables),
        "comparables_source": avm.get("comparablesSource")
        or (
            "ZillAPI recently sold"
            if comparables and rentcast_record.get("source") == "zillapi"
            else None
        ),
        "nearby_1_mile": property_record.get("nearby_1_mile"),
        "nearby_3_mile": property_record.get("nearby_3_mile"),
        "nearby_5_mile": property_record.get("nearby_5_mile"),
        "source": (
            "zillapi + census_geocoder"
            if rentcast_record.get("source") == "zillapi"
            else "census_geocoder + rentcast"
        )
        if not settings.demo_mode
        else "demo",
        "listing_source": property_record.get("mlsName"),
        "mls_number": property_record.get("mlsNumber"),
        "days_on_market": property_record.get("daysOnMarket"),
        "listed_date": listed_date,
        "last_price_change_date": latest_price_change.get("date")
        or last_price_change_date,
        "last_price_previous": latest_price_change.get("previous_price"),
        "last_price_current": latest_price_change.get("current_price"),
        "last_price_change_percent": latest_price_change.get("percent"),
        "last_price_change_direction": latest_price_change.get("direction"),
        "price_history": normalized_price_history,
        "listing_description": (
            property_record.get("description")
            or property_record.get("remarks")
            or property_record.get("publicRemarks")
        ),
        "remodeled_year": (
            property_record.get("remodeledYear")
            or property_record.get("yearRemodeled")
        ),
        "roof": property_record.get("roof"),
        "heating": property_record.get("heating"),
        "cooling": property_record.get("cooling"),
        "flooring": property_record.get("flooring"),
        "interior_features": property_record.get("interiorFeatures"),
        "appliances": property_record.get("appliances"),
    }

    # Calculate tax estimate if missing (AFTER verified_payload is created)
    if not verified_payload["tax_total"] and verified_payload.get("estimated_value"):
        verified_payload["tax_total"] = int(verified_payload["estimated_value"] * 0.015)
        verified_payload["tax_year"] = 2023

    # Use closed-sale comparable prices grouped by exact distance from the
    # subject. RentCast data only reaches this point as an explicit fallback.
    nearby_1_value, nearby_1_count = _median_comparable_value(comparables, 1)
    nearby_3_value, nearby_3_count = _median_comparable_value(comparables, 3)
    nearby_5_value, nearby_5_count = _median_comparable_value(comparables, 5)
    if not verified_payload["nearby_1_mile"]:
        verified_payload["nearby_1_mile"] = nearby_1_value
    if not verified_payload["nearby_3_mile"]:
        verified_payload["nearby_3_mile"] = nearby_3_value
    if not verified_payload["nearby_5_mile"]:
        verified_payload["nearby_5_mile"] = nearby_5_value
    verified_payload["nearby_1_mile_count"] = nearby_1_count
    verified_payload["nearby_3_mile_count"] = nearby_3_count
    verified_payload["nearby_5_mile_count"] = nearby_5_count
    verified_payload["nearby_metric"] = (
        "median sold price"
        if verified_payload.get("comparables_source") == "ZillAPI recently sold"
        else "median comparable value"
    )

    # External listing providers occasionally return a sparse record for a
    # previously successful lookup. A refresh may update known values, but it
    # should not erase verified facts with empty provider responses.
    existing_formatted_address = (
        existing_profile.verified_payload.get("formatted_address")
        if existing_profile and isinstance(existing_profile.verified_payload, dict)
        else None
    )
    preserve_existing_profile = (
        existing_profile is not None
        and (
            not existing_formatted_address
            or _addresses_match(existing_formatted_address, search_address)
        )
    )
    if preserve_existing_profile and isinstance(existing_profile.verified_payload, dict):
        for field, previous_value in existing_profile.verified_payload.items():
            if (
                field == "listing_price"
                and verified_payload.get("listing_price") is None
                and previous_value
                == existing_profile.verified_payload.get("last_sale_price")
            ):
                continue
            if verified_payload.get(field) in (None, "", []):
                verified_payload[field] = previous_value

    # A normal property lookup intentionally does not request paid comparable
    # records. Clear any older comparable snapshot so the UI never implies
    # that comparables were refreshed as part of the subject-property lookup.
    if not payload.include_comparables:
        verified_payload["comparables_count"] = 0
        verified_payload["comparables_source"] = None
        verified_payload["nearby_1_mile"] = None
        verified_payload["nearby_3_mile"] = None
        verified_payload["nearby_5_mile"] = None
        verified_payload["nearby_1_mile_count"] = 0
        verified_payload["nearby_3_mile_count"] = 0
        verified_payload["nearby_5_mile_count"] = 0
        verified_payload["nearby_metric"] = "not requested"

    schools_payload = _get_cached_response(
        db,
        "nces",
        "nearby_schools",
        search_address,
    )
    if (
        schools_payload is None
        and verified_payload.get("latitude") is not None
        and verified_payload.get("longitude") is not None
    ):
        try:
            schools_payload = NearbySchoolsConnector().fetch(
                float(verified_payload["latitude"]),
                float(verified_payload["longitude"]),
            )
        except Exception as e:
            print(f"Nearby school lookup failed: {e}")
            schools_payload = {
                "source": "nces",
                "status": "error",
                "schools": [],
            }
        _set_cached_response(
            db,
            prop.id,
            "nces",
            "nearby_schools",
            search_address,
            schools_payload,
        )

    nearby_schools = []
    provider_schools = property_record.get("schools", [])
    if isinstance(provider_schools, list):
        for school in provider_schools:
            if not isinstance(school, dict):
                continue
            name = school.get("name")
            distance = school.get("distance")
            rating = school.get("rating")
            if not name:
                continue
            details = []
            if distance is not None:
                details.append(f"{distance} mi")
            if rating is not None:
                details.append(f"{rating}/10")
            nearby_schools.append(
                f"{name} — {', '.join(details)}" if details else name
            )
    if schools_payload:
        if not nearby_schools:
            nearby_schools = [
                f"{school['name']} — {school['distance_miles']:.1f} mi"
                for school in schools_payload.get("schools", [])
                if school.get("name") and school.get("distance_miles") is not None
            ]
        raw_sources.append(schools_payload)
    if not nearby_schools and preserve_existing_profile:
        nearby_schools = [
            school
            for school in existing_profile.analysis_payload.get("schools", [])
            if "(ZIP " not in school
        ]

    analysis_payload = {
        "briefing": f"Location and property facts retrieved for {verified_payload['formatted_address'] or search_address}.",
        "highlights": [
            f"{verified_payload.get('bedrooms') or 'Unknown'} bed / {verified_payload.get('bathrooms') or 'Unknown'} bath",
            f"{verified_payload.get('square_footage') or 'Unknown'} sqft",
            f"Listing price: {verified_payload.get('listing_price') or 'Unknown'}",
            f"Zestimate: {verified_payload.get('estimated_value') or 'Unknown'}",
        ],
        "schools": nearby_schools,
        "next_step": "Add FEMA flood data using latitude and longitude.",
        "comps": {
            "count": verified_payload["comparables_count"],
        },
    }

    profile = existing_profile
    if not profile:
        profile = PropertyVerifiedProfile(
            property_id=prop.id,
            verified_payload=verified_payload,
            analysis_payload=analysis_payload,
            source_breakdown={"sources": raw_sources},
            notes=f"{verified_payload['source']} property result",
        )
        db.add(profile)
    else:
        profile.verified_payload = verified_payload
        profile.analysis_payload = analysis_payload
        profile.source_breakdown = {"sources": raw_sources}
        profile.notes = f"{verified_payload['source']} property result"

    prop.city = property_record.get("city") or subject_property.get("city")
    prop.state = verified_payload.get("state")
    prop.zip_code = verified_payload.get("zip_code")
    prop.verified_summary = verified_payload.get("formatted_address")

    db.commit()
    db.refresh(prop)
    return prop
