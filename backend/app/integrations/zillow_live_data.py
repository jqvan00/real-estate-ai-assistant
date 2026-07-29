"""Zillow Live Data Scraper API connector."""
from __future__ import annotations
import re
from typing import Any
import requests
from app.core.config import settings


class ZillowLiveDataConnector:
    """Connector for Zillow Live Data Scraper API."""
    
    name = "zillow_live_data"

    _street_suffixes = {
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
        "way": "way",
    }
    
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.rapidapi_key
        self.base_url = "https://zillow-com-live-data-scraper-api.p.rapidapi.com"
        if not self.api_key:
            raise ValueError("RAPIDAPI_KEY is missing from .env")

    @classmethod
    def _normalize_address(cls, address: str) -> str:
        tokens = re.findall(r"[a-z0-9]+", address.lower())
        return " ".join(cls._street_suffixes.get(token, token) for token in tokens)
    
    def _get(self, endpoint: str, params: dict[str, Any]) -> Any:
        """Make GET request to Zillow Live Data API."""
        headers = {
            "x-rapidapi-host": "zillow-com-live-data-scraper-api.p.rapidapi.com",
            "x-rapidapi-key": self.api_key,
            "Content-Type": "application/json",
        }
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=30.0,
                proxies={"http": None, "https": None},
                verify=True  # Keep SSL verification for security
            )
            
            if response.status_code == 404:
                return {"error": "not_found", "message": "Property not found"}
            
            if response.status_code != 200:
                return {"error": "api_error", "message": f"API returned status {response.status_code}"}
            
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to fetch from Zillow Live Data: {str(e)}") from e
    
    def fetch_property_record(self, address: str) -> dict[str, Any]:
        """Search for property by address."""
        # Extract zip code from address
        parts = address.split(",")
        zip_code = parts[-1].strip().split()[-1] if len(parts) > 2 else None
        
        # Search by zip code
        if not zip_code or not zip_code.isdigit():
            return {
                "source": self.name,
                "status": "no_match",
                "message": "Could not extract zip code from address",
                "record": {},
                "raw": {},
            }
        
        payload = self._get("/bymlsid", {"mlsid": zip_code, "page": 1})
        
        if isinstance(payload, dict) and payload.get('error'):
            return {
                "source": self.name,
                "status": "no_match",
                "message": payload.get('message'),
                "record": {},
                "raw": payload,
            }
        
        results = payload.get("results", [])
        
        if not results:
            return {
                "source": self.name,
                "status": "no_match",
                "message": f"No properties found",
                "record": {},
                "raw": payload,
            }
        
        # Find best match by address
        best_match = None
        normalized_search_address = self._normalize_address(address)

        for prop in results:
            normalized_property_address = self._normalize_address(
                prop.get("address", "")
            )
            if normalized_property_address == normalized_search_address:
                best_match = prop
                break

        if not best_match:
            return {
                "source": self.name,
                "status": "no_match",
                "message": "No exact address match found",
                "record": {},
                "raw": payload,
            }
        
        # Transform to standard format
        record = {
            "formattedAddress": best_match.get("address"),
            "bedrooms": best_match.get("beds"),
            "bathrooms": best_match.get("baths"),
            "squareFootage": best_match.get("sqft"),
            "lotSize": None,
            "yearBuilt": None,
            "propertyType": best_match.get("property_type"),
            "price": best_match.get("price"),
            "lastSalePrice": best_match.get("price"),
            "latitude": best_match.get("latitude"),
            "longitude": best_match.get("longitude"),
            "zpid": best_match.get("zpid"),
            "listingUrl": best_match.get("url"),
            "photoUrl": best_match.get("photo_url"),
        }
        
        return {
            "source": self.name,
            "status": "matched",
            "record": record,
            "raw": payload,
        }
    
    def fetch_value_estimate(
        self,
        address: str,
        property_record: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get value estimate."""
        if property_record is None:
            prop_result = self.fetch_property_record(address)
            record = prop_result.get("record", {})
            matched = prop_result.get("status") == "matched"
        else:
            record = property_record
            matched = bool(record)

        if not record or not matched:
            return {
                "source": self.name,
                "status": "no_match",
                "value": {},
                "raw": {},
            }
        
        price = record.get("price", 0)
        
        value_data = {
            "price": price,
            "priceRangeLow": int(price * 0.95) if price else 0,
            "priceRangeHigh": int(price * 1.05) if price else 0,
        }
        
        return {
            "source": self.name,
            "status": "ok",
            "value": value_data,
            "raw": value_data,
        }
