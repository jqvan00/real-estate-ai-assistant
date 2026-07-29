from __future__ import annotations

from typing import Any

import requests

from app.core.config import settings


class RentCastConnector:
    name = "rentcast"

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or settings.rentcast_api_key
        self.base_url = base_url or settings.rentcast_api_base_url
        if not self.api_key:
            raise ValueError("RENTCAST_API_KEY is missing from .env")

    def _get(self, path: str, params: dict[str, Any]) -> Any:
        """Make GET request to RentCast API."""
        # Force DNS refresh by clearing socket cache
        import socket
        if hasattr(socket, '_dnscache'):
            socket._dnscache = {}
        
        headers = {
            "Accept": "application/json",
            "X-Api-Key": self.api_key,
        }
        
        url = f"{self.base_url}{path}"
        
        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=30.0,
                proxies={"http": None, "https": None}  # Explicitly disable proxies
            )
            
            # Handle 400/404 errors gracefully (address not found)
            if response.status_code in [400, 404]:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                return {
                    "error": "address_not_found",
                    "message": error_data.get('message', f"Address not found in RentCast database (HTTP {response.status_code})"),
                    "status_code": response.status_code
                }
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                # Already handled above
                raise
            error_msg = f"Failed to fetch data from RentCast API: {str(e)}"
            raise ConnectionError(error_msg) from e

    def fetch_property_record(self, address: str) -> dict[str, Any]:
        payload = self._get("/properties", {"address": address, "limit": 1})

        # Handle error responses
        if isinstance(payload, dict) and payload.get('error') == 'address_not_found':
            return {
                "source": self.name,
                "endpoint": "properties",
                "status": "no_match",
                "message": payload.get('message'),
                "record": {},
                "raw": payload,
            }

        record: dict[str, Any] = {}
        if isinstance(payload, list):
            record = payload[0] if payload else {}
        elif isinstance(payload, dict):
            records = payload.get("properties") or payload.get("results") or payload.get("data")
            if isinstance(records, list) and records:
                record = records[0]
            else:
                record = payload

        return {
            "source": self.name,
            "endpoint": "properties",
            "status": "matched" if record else "no_match",
            "record": record,
            "raw": payload,
        }

    def fetch_value_estimate(self, address: str) -> dict[str, Any]:
        payload = self._get(
            "/avm/value",
            {
                "address": address,
                "lookupSubjectAttributes": "true",
            },
        )

        return {
            "source": self.name,
            "endpoint": "avm/value",
            "status": "ok",
            "value": payload,
            "raw": payload,
        }

    def fetch_active_sale_listing(self, address: str) -> dict[str, Any]:
        payload = self._get(
            "/listings/sale",
            {
                "address": address,
                "status": "Active",
                "limit": 5,
            },
        )
        records = payload if isinstance(payload, list) else []
        normalized_address = " ".join(address.lower().replace(",", " ").split())
        listing = next(
            (
                record
                for record in records
                if " ".join(
                    (record.get("formattedAddress") or "")
                    .lower()
                    .replace(",", " ")
                    .split()
                )
                == normalized_address
            ),
            records[0] if len(records) == 1 else {},
        )
        return {
            "source": self.name,
            "endpoint": "listings/sale",
            "status": "matched" if listing else "no_match",
            "record": listing,
            "raw": payload,
        }
