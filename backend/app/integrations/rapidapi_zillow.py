"""RapidAPI Zillow connector for property data."""
from __future__ import annotations
from typing import Any
import requests
from app.core.config import settings


class RapidAPIZillowConnector:
    """Connector for RapidAPI Zillow API."""
    
    name = "rapidapi_zillow"
    
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.rapidapi_key
        self.base_url = "https://real-estate-zillow-com.p.rapidapi.com"
        if not self.api_key:
            raise ValueError("RAPIDAPI_KEY is missing from .env")
    
    def _get(self, endpoint: str, params: dict[str, Any]) -> Any:
        """Make GET request to RapidAPI Zillow."""
        headers = {
            "x-rapidapi-host": "real-estate-zillow-com.p.rapidapi.com",
            "x-rapidapi-key": self.api_key,
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
            
            # Handle errors
            if response.status_code == 404:
                return {
                    "error": "not_found",
                    "message": "Property not found in Zillow database",
                    "status_code": 404
                }
            
            if response.status_code != 200:
                return {
                    "error": "api_error",
                    "message": f"API returned status {response.status_code}",
                    "status_code": response.status_code
                }
            
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to fetch data from RapidAPI Zillow: {str(e)}"
            raise ConnectionError(error_msg) from e
    
    def fetch_property_record(self, address: str) -> dict[str, Any]:
        """
        Fetch property data by address.
        
        Uses the /v1/search endpoint to find property by address,
        then returns the first match.
        """
        # Extract city/stafrom address for search
        # Format: "5335 W Cardinal St, Rogers, AR 72758"
        parts = address.split(",")
        if len(parts) < 2:
            return {
                "source": self.name,
                "endpoint": "search",
                "status": "no_match",
                "message": "Invalid address format",
                "record": {},
                "raw": {},
            }
        
        # Use full address as location
        location = address.strip()
        
        # Search for the property
        payload = self._get("/v1/search", {
            "location": location,
            "status": "forSale",
            "page": 1
        })
        
        # Handle error responses
        if isinstance(payload, dict) and payload.get('error'):
            return {
                "source": self.name,
                "endpoint": "search",
                "status": "no_match",
                "message": payload.get('message'),
                "record": {},
                "raw": payload,
            }
        
        # Extract results
        results = payload.get("results", []) if isinstance(payload, dict) else []
        
        if not results or len(results) == 0:
            return {
                "source": self.name,
                "endpoint": "search",
                "status": "no_match",
                "message": f"No properties found for '{address}'",
                "record": {},
                "raw": payload,
            }
        
        # Get first result and transform to standard format
        prop = results[0]
        
        # Transform Zillow format to our standard format
        record = {
            "formattedAddress": prop.get("address"),
            "bedrooms": prop.get("bedrooms"),
            "bathrooms": prop.get("bathrooms"),
            "squareFootage": prop.get("livingArea"),
            "lotSize": f"{prop.get('lotAreaValue', 0)} {prop.get('lotAreaUnit', 'sqft')}",
            "yearBuilt": prop.get("yearBuilt"),
            "propertyType": prop.get("propertyType"),
            "price": prop.get("price"),
            "lastSalePrice": prop.get("price"),
            "lastSaleDate": None,  # Not in search results
            "taxYear": None,  # Need property details endpoint
            "taxTotal": None,
            "county": None,
            "state": prop.get("state"),
            "zipCode": prop.get("zipcode"),
            "latitude": prop.get("latitude"),
            "longitude": prop.get("longitude"),
            "zpid": prop.get("zpid"),  # Zillow property ID
            "listingUrl": prop.get("detailUrl"),
        }
        
        return {
            "source": self.name,
            "endpoint": "search",
            "status": "matched",
            "record": record,
            "raw": payload,
        }
    
    def fetch_value_estimate(self, address: str) -> dict[str, Any]:
        """
        Fetch property value estimate.
        
        For Zillow, the price is already in the search results.
        This creates a compatible response.
        """
        # Get property record first
        prop_result = self.fetch_property_record(address)
        record = prop_result.get("record", {})
        
        if not record or prop_result.get("status") != "matched":
            return {
                "source": self.name,
                "endpoint": "estimate",
                "status": "no_match",
                "value": {},
                "raw": {},
            }
        
        price = record.get("price", 0)
        
        # Create estimate with +/- 5% range
        value_data = {
            "price": price,
            "priceRangeLow": int(price * 0.95) if price else 0,
            "priceRangeHigh": int(price * 1.05) if price else 0,
            "rent": None,  # Not available in search
            "rentRangeLow": None,
            "rentRangeHigh": None,
        }
        
        return {
            "source": self.name,
            "endpoint": "estimate",
            "status": "ok",
            "value": value_data,
            "raw": value_data,
        }
