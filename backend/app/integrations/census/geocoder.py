from __future__ import annotations

import httpx


class CensusGeocoderConnector:
    name = "census_geocoder"

    def fetch(self, address: str) -> dict:
        url = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
        params = {
            "address": address,
            "benchmark": "2020",
            "format": "json",
        }

        with httpx.Client(timeout=20.0) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        matches = data.get("result", {}).get("addressMatches", [])
        if not matches:
            return {
                "source": self.name,
                "input_address": address,
                "status": "no_match",
            }

        best = matches[0]
        coords = best.get("coordinates", {})
        components = best.get("addressComponents", {})

        return {
            "source": self.name,
            "input_address": address,
            "status": "matched",
            "formatted_address": best.get("matchedAddress"),
            "latitude": coords.get("y"),
            "longitude": coords.get("x"),
            "state": components.get("state"),
            "county": components.get("county"),
            "zip_code": components.get("zip"),
            "raw": best,
        }