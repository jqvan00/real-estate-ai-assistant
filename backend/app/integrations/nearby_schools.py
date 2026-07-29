from __future__ import annotations

from math import asin, cos, radians, sin, sqrt
from typing import Any

import requests


class NearbySchoolsConnector:
    """Find nearby public schools using the current NCES school layer."""

    name = "nces"
    endpoint = (
        "https://services1.arcgis.com/Ua5sjt3LWTPigjyD/ArcGIS/rest/services/"
        "Public_School_Locations_Current/FeatureServer/0/query"
    )

    @staticmethod
    def _distance_miles(
        origin_latitude: float,
        origin_longitude: float,
        latitude: float,
        longitude: float,
    ) -> float:
        earth_radius_miles = 3958.8
        lat_delta = radians(latitude - origin_latitude)
        lon_delta = radians(longitude - origin_longitude)
        origin_lat = radians(origin_latitude)
        destination_lat = radians(latitude)
        haversine = (
            sin(lat_delta / 2) ** 2
            + cos(origin_lat) * cos(destination_lat) * sin(lon_delta / 2) ** 2
        )
        return 2 * earth_radius_miles * asin(sqrt(haversine))

    def fetch(
        self,
        latitude: float,
        longitude: float,
        radius_miles: float = 10,
        limit: int = 6,
    ) -> dict[str, Any]:
        latitude_delta = radius_miles / 69
        longitude_delta = radius_miles / max(
            1,
            69 * cos(radians(latitude)),
        )
        response = requests.get(
            self.endpoint,
            params={
                "f": "json",
                "where": "1=1",
                "geometry": (
                    f"{longitude - longitude_delta},{latitude - latitude_delta},"
                    f"{longitude + longitude_delta},{latitude + latitude_delta}"
                ),
                "geometryType": "esriGeometryEnvelope",
                "inSR": "4326",
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "NAME,LAT,LON,CITY,STATE,SCHOOLYEAR",
                "returnGeometry": "false",
                "resultRecordCount": "250",
            },
            headers={"User-Agent": "RealEstateShowingAssistant/1.0"},
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("error"):
            raise ConnectionError(f"NCES school lookup failed: {payload['error']}")

        schools_by_name: dict[str, dict[str, Any]] = {}
        for feature in payload.get("features", []):
            attributes = feature.get("attributes") or {}
            name = attributes.get("NAME")
            school_latitude = attributes.get("LAT")
            school_longitude = attributes.get("LON")
            if not name or school_latitude is None or school_longitude is None:
                continue

            distance = self._distance_miles(
                latitude,
                longitude,
                float(school_latitude),
                float(school_longitude),
            )
            if distance > radius_miles:
                continue
            school = {
                "name": name,
                "distance_miles": round(distance, 1),
                "city": attributes.get("CITY"),
                "state": attributes.get("STATE"),
                "school_year": attributes.get("SCHOOLYEAR"),
            }
            previous = schools_by_name.get(name)
            if previous is None or distance < previous["distance_miles"]:
                schools_by_name[name] = school

        schools = sorted(
            schools_by_name.values(),
            key=lambda school: school["distance_miles"],
        )[:limit]
        return {
            "source": self.name,
            "status": "ok" if schools else "no_match",
            "schools": schools,
        }
