"""Realtor16 API connector."""
from __future__ import annotations
from typing import Any
import requests
from app.core.config import settings


class Realtor16Connector:
    """Connector for Realtor16 API."""
    
    name = "realtor16"
    
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.rapidapi_key
        self.base_url = "https://realtor16.p.rapidapi.com"
        if not self.api_key:
            raise ValueError("RAPIDAPI_KEY is missing from .env")
    
    def _get(self, endpoint: str, params: dict[str, Any]) -> Any:
        """Make GET request to Realtor16 API."""
        headers = {
            "x-rapidapi-host": "realtor16.p.rapidapi.com",
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
                proxies={"http": None, "https": None}
            )
            
            if response.status_code == 404:
                return {"error": "not_found", "message": "Property not found"}
            
            if response.status_code != 200:
                return {"error": "api_error", "message": f"API returned status {response.status_code}"}
            
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to fetch from Realtor16: {str(e)}") from e
    
    def fetch_property_record(self, address: str) -> dict[str, Any]:
        """Search for property by address (requires coordinates)."""
        # This API needs coordinates, so we return no_match
        # In a real implementation, you'd geocode the address first
        return {
            "source": self.name,
            "status": "no_match",
            "message": "Realtor16 requires coordinates - not implemented yet",
            "record": {},
            "raw": {},
        }
    
    def fetch_value_estimate(self, address: str) -> dict[str, Any]:
        """Get value estimate."""
        return {
            "source": self.name,
            "status": "no_match",
            "value": {},
            "raw": {},
        }
