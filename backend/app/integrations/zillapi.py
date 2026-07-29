from __future__ import annotations

from math import asin, cos, radians, sin, sqrt
from typing import Any

import requests

from app.core.config import settings


def _first_present(source: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = source.get(key)
        if value not in (None, "", [], {}):
            return value
    return None


def _as_list(value: Any) -> list[Any]:
    if value in (None, ""):
        return []
    return value if isinstance(value, list) else [value]


def _money_value(value: Any) -> float | int | None:
    if isinstance(value, dict):
        value = value.get("amount") or value.get("value") or value.get("formatted")
    if isinstance(value, str):
        cleaned = value.replace("$", "").replace(",", "").strip()
        if not cleaned:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None
    return value if isinstance(value, (int, float)) else None


class ZillAPIConnector:
    """Server-side connector for ZillAPI's single-property endpoints."""

    name = "zillapi"

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or settings.zillapi_key
        self.base_url = (base_url or settings.zillapi_base_url).rstrip("/")
        if not self.api_key:
            raise ValueError("ZILLAPI_KEY is missing from .env")

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            response = requests.get(
                f"{self.base_url}{path}",
                params=params or {},
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
                timeout=60,
            )
            if response.status_code in (400, 404):
                return {
                    "error": "not_found",
                    "status_code": response.status_code,
                }
            response.raise_for_status()
            payload = response.json()
            return payload if isinstance(payload, dict) else {"data": payload}
        except requests.exceptions.RequestException as exc:
            raise ConnectionError(f"ZillAPI request failed: {exc}") from exc

    def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        try:
            response = requests.post(
                f"{self.base_url}{path}",
                json=body,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
                timeout=60,
            )
            if response.status_code == 400:
                payload = response.json() if response.content else {}
                return {
                    "error": payload.get("error", "invalid_filters"),
                    "message": payload.get("message"),
                    "status_code": response.status_code,
                }
            response.raise_for_status()
            payload = response.json()
            return payload if isinstance(payload, dict) else {"data": payload}
        except requests.exceptions.RequestException as exc:
            raise ConnectionError(f"ZillAPI request failed: {exc}") from exc

    @staticmethod
    def _distance_miles(
        first_latitude: float,
        first_longitude: float,
        second_latitude: float,
        second_longitude: float,
    ) -> float:
        """Great-circle distance between two coordinates."""
        lat1, lon1, lat2, lon2 = map(
            radians,
            (
                first_latitude,
                first_longitude,
                second_latitude,
                second_longitude,
            ),
        )
        delta_latitude = lat2 - lat1
        delta_longitude = lon2 - lon1
        haversine = (
            sin(delta_latitude / 2) ** 2
            + cos(lat1) * cos(lat2) * sin(delta_longitude / 2) ** 2
        )
        return 3958.8 * 2 * asin(sqrt(haversine))

    @staticmethod
    def _normalize_property(raw: dict[str, Any]) -> dict[str, Any]:
        address = raw.get("address") if isinstance(raw.get("address"), dict) else {}
        reso = raw.get("resoFacts") if isinstance(raw.get("resoFacts"), dict) else {}

        street = _first_present(address, "streetAddress", "street")
        city = _first_present(address, "city")
        state = _first_present(address, "state")
        zip_code = _first_present(address, "zipcode", "zipCode")
        formatted_address = _first_present(raw, "formattedAddress")
        if not formatted_address:
            formatted_address = ", ".join(
                part
                for part in (
                    street,
                    city,
                    " ".join(part for part in (state, zip_code) if part),
                )
                if part
            )

        flooring = _first_present(raw, "flooring") or _first_present(reso, "flooring")
        appliances = _first_present(raw, "appliances") or _first_present(
            reso, "appliances"
        )
        interior_features = _first_present(
            raw, "interiorFeatures"
        ) or _first_present(reso, "interiorFeatures")

        return {
            "formattedAddress": formatted_address,
            "city": city,
            "state": state,
            "zipCode": zip_code,
            "county": _first_present(raw, "county", "countyName")
            or _first_present(address, "county"),
            "latitude": _first_present(raw, "latitude"),
            "longitude": _first_present(raw, "longitude"),
            "propertyType": _first_present(raw, "homeType", "propertyType"),
            "bedrooms": _first_present(raw, "bedrooms"),
            "bathrooms": _first_present(raw, "bathrooms"),
            "squareFootage": _first_present(raw, "livingArea", "livingAreaValue"),
            "lotSize": _first_present(raw, "lotSize", "lotAreaValue"),
            "yearBuilt": _first_present(raw, "yearBuilt"),
            "status": _first_present(raw, "homeStatus", "listingStatus"),
            "price": _first_present(raw, "price", "unformattedPrice"),
            "zestimate": _first_present(raw, "zestimate"),
            "rentZestimate": _first_present(raw, "rentZestimate"),
            "lastSaleDate": _first_present(raw, "lastSoldDate", "lastSaleDate"),
            "lastSalePrice": _first_present(raw, "lastSoldPrice", "lastSalePrice"),
            "hoaFee": _first_present(raw, "monthlyHoaFee", "hoaFee"),
            "daysOnMarket": _first_present(raw, "daysOnZillow", "daysOnMarket"),
            "listedDate": _first_present(
                raw, "datePostedString", "datePosted", "listedDate"
            ),
            "description": _first_present(
                raw, "description", "publicRemarks", "marketingRemarks"
            ),
            "remodeledYear": _first_present(raw, "yearRemodeled", "remodeledYear"),
            "roof": _first_present(raw, "roof") or _first_present(reso, "roofType"),
            "heating": _first_present(raw, "heating") or _first_present(
                reso, "heating"
            ),
            "cooling": _first_present(raw, "cooling") or _first_present(
                reso, "cooling"
            ),
            "flooring": _as_list(flooring),
            "interiorFeatures": _as_list(interior_features),
            "appliances": _as_list(appliances),
            "schools": raw.get("schools") if isinstance(raw.get("schools"), list) else [],
            "priceHistory": raw.get("priceHistory")
            if isinstance(raw.get("priceHistory"), list)
            else [],
            "resoFacts": reso,
            "zpid": str(raw.get("zpid")) if raw.get("zpid") is not None else None,
            "listingUrl": _first_present(raw, "url", "detailUrl"),
            "rawZillAPI": raw,
        }

    def fetch_property_record(
        self, address: str, listing_url: str | None = None
    ) -> dict[str, Any]:
        if listing_url and "zillow.com" in listing_url.lower():
            endpoint = "properties/by-url"
            payload = self._get(
                "/properties/by-url",
                {"url": listing_url, "status": "FOR_SALE"},
            )
        else:
            endpoint = "properties/by-address"
            payload = self._get(
                "/properties/by-address",
                {"address": address, "status": "FOR_SALE"},
            )

        raw = payload.get("data")
        if not isinstance(raw, dict) or not raw:
            return {
                "source": self.name,
                "endpoint": endpoint,
                "status": "no_match",
                "record": {},
                "raw": payload,
            }

        return {
            "source": self.name,
            "endpoint": endpoint,
            "status": "matched",
            "record": self._normalize_property(raw),
            "raw": payload,
        }

    def fetch_value_estimate(
        self, property_record: dict[str, Any]
    ) -> dict[str, Any]:
        zestimate = property_record.get("zestimate")
        return {
            "source": self.name,
            "endpoint": "property-detail",
            "status": "ok" if zestimate is not None else "no_match",
            "value": {
                "price": zestimate,
                "subjectProperty": property_record,
                "comparables": [],
            },
            "raw": {
                "zestimate": zestimate,
                "rentZestimate": property_record.get("rentZestimate"),
            },
        }

    def fetch_recently_sold_comparables(
        self,
        property_record: dict[str, Any],
        radius_miles: float = 5.0,
        max_items: int = 25,
    ) -> dict[str, Any]:
        latitude = property_record.get("latitude")
        longitude = property_record.get("longitude")
        if latitude is None or longitude is None:
            return {
                "source": self.name,
                "endpoint": "search/recently-sold",
                "status": "no_match",
                "comparables": [],
                "message": "Subject coordinates are unavailable.",
            }

        latitude = float(latitude)
        longitude = float(longitude)
        latitude_delta = radius_miles / 69.0
        longitude_delta = radius_miles / max(
            1.0, 69.0 * cos(radians(latitude))
        )

        sqft = property_record.get("squareFootage")
        beds = property_record.get("bedrooms")
        property_type = str(property_record.get("propertyType") or "").upper()
        home_type = {
            "SINGLE_FAMILY": "house",
            "SINGLE FAMILY": "house",
            "CONDO": "condo",
            "TOWNHOUSE": "townhouse",
            "MULTI_FAMILY": "multi_family",
            "MANUFACTURED": "manufactured",
        }.get(property_type, "house")

        filters: dict[str, Any] = {
            "status": "sold",
            "bbox": {
                "west": longitude - longitude_delta,
                "south": latitude - latitude_delta,
                "east": longitude + longitude_delta,
                "north": latitude + latitude_delta,
            },
            "homeTypes": [home_type],
        }
        if beds is not None:
            filters["beds"] = {
                "min": max(0, int(float(beds)) - 1),
                "max": int(float(beds)) + 1,
            }
        if sqft is not None and float(sqft) > 0:
            filters["sqft"] = {
                "min": round(float(sqft) * 0.75),
                "max": round(float(sqft) * 1.25),
            }

        payload = self._post(
            "/search",
            {
                "filters": filters,
                "extractionMethod": "PAGINATION",
                "maxItems": min(max(1, max_items), 50),
                "async": False,
            },
        )

        # Support the legacy request shape still shown in ZillAPI's CMA guide.
        if payload.get("status_code") == 400:
            payload = self._post(
                "/search",
                {
                    "bbox": filters["bbox"],
                    "listingStatus": "RECENTLY_SOLD",
                    "homeType": [property_type or "SINGLE_FAMILY"],
                    "maxItems": min(max(1, max_items), 50),
                },
            )

        rows = payload.get("data")
        if not isinstance(rows, list):
            rows = []

        comparables: list[dict[str, Any]] = []
        subject_sqft = float(sqft) if sqft not in (None, 0) else None
        subject_year = property_record.get("yearBuilt")
        subject_zpid = str(property_record.get("zpid") or "")

        for row in rows:
            if not isinstance(row, dict):
                continue
            home_info = (
                (row.get("hdpData") or {}).get("homeInfo") or {}
                if isinstance(row.get("hdpData"), dict)
                else {}
            )
            zpid = str(_first_present(row, "zpid") or _first_present(home_info, "zpid") or "")
            if zpid and zpid == subject_zpid:
                continue

            price = None
            for candidate in (
                row.get("soldPrice"),
                row.get("listingSoldPrice"),
                row.get("unformattedPrice"),
                row.get("price"),
                home_info.get("soldPrice"),
                home_info.get("price"),
            ):
                price = _money_value(candidate)
                if price is not None:
                    break

            comp_sqft = _first_present(row, "area", "livingArea") or _first_present(
                home_info, "livingArea"
            )
            comp_beds = _first_present(row, "beds", "bedrooms") or _first_present(
                home_info, "bedrooms"
            )
            comp_baths = _first_present(row, "baths", "bathrooms") or _first_present(
                home_info, "bathrooms"
            )
            comp_year = _first_present(row, "yearBuilt") or _first_present(
                home_info, "yearBuilt"
            )
            coordinates = row.get("latLong")
            if not isinstance(coordinates, dict):
                coordinates = (
                    row.get("coordinates")
                    if isinstance(row.get("coordinates"), dict)
                    else {}
                )
            comp_latitude = _first_present(coordinates, "latitude") or _first_present(
                home_info, "latitude"
            )
            comp_longitude = _first_present(
                coordinates, "longitude"
            ) or _first_present(home_info, "longitude")

            if (
                price is None
                or comp_latitude is None
                or comp_longitude is None
            ):
                continue
            if subject_sqft and comp_sqft:
                if abs(float(comp_sqft) - subject_sqft) / subject_sqft > 0.25:
                    continue
            if beds is not None and comp_beds is not None:
                if abs(float(comp_beds) - float(beds)) > 1:
                    continue
            if subject_year and comp_year:
                if abs(int(comp_year) - int(subject_year)) > 20:
                    continue

            distance = self._distance_miles(
                latitude,
                longitude,
                float(comp_latitude),
                float(comp_longitude),
            )
            if distance > radius_miles:
                continue

            address = _first_present(row, "address")
            if isinstance(address, dict):
                address = _first_present(address, "streetAddress")
            comparables.append(
                {
                    "source": self.name,
                    "zpid": zpid or None,
                    "address": address,
                    "city": _first_present(row, "addressCity")
                    or _first_present(home_info, "city"),
                    "state": _first_present(row, "addressState")
                    or _first_present(home_info, "state"),
                    "price": round(float(price)),
                    "squareFootage": round(float(comp_sqft))
                    if comp_sqft is not None
                    else None,
                    "bedrooms": comp_beds,
                    "bathrooms": comp_baths,
                    "yearBuilt": comp_year,
                    "distance": round(distance, 3),
                    "soldDate": _first_present(row, "dateSold", "lastSoldDate")
                    or _first_present(home_info, "dateSold", "lastSoldDate"),
                    "status": _first_present(row, "statusType")
                    or _first_present(home_info, "homeStatus")
                    or "RECENTLY_SOLD",
                    "pricePerSquareFoot": (
                        round(float(price) / float(comp_sqft), 2)
                        if comp_sqft not in (None, 0)
                        else None
                    ),
                }
            )

        comparables.sort(key=lambda item: item["distance"])
        return {
            "source": self.name,
            "endpoint": "search/recently-sold",
            "status": "ok" if comparables else "no_match",
            "comparables": comparables,
            "raw_count": len(rows),
            "raw": payload,
        }
