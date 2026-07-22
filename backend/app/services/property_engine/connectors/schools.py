from __future__ import annotations

import hashlib


class SchoolsConnector:
    name = "schools"
    source_kind = "enrichment"

    def fetch(self, address: str, listing_url: str | None = None) -> dict:
        digest = hashlib.sha256(address.encode("utf-8")).hexdigest()
        seed = int(digest[:8], 16)

        beds = 2 + (seed % 4)
        baths = 1.5 + ((seed // 3) % 3) * 0.5
        sqft = 1200 + (seed % 1800)
        year_built = 1985 + (seed % 35)
        lot_size_acres = round(0.10 + ((seed % 25) / 100), 2)
        estimated_value = 200000 + (seed % 600000)
        annual_taxes = round(estimated_value * 0.012, 2)

        return {
            "source_name": self.name,
            "source_type": self.source_kind,
            "confidence": 0.65,
            "address": {
                "street": address,
                "city": "Demo City",
                "state": "AR",
                "zip_code": "72712",
            },
            "structure": {
                "beds": beds,
                "baths": baths,
                "sqft": sqft,
                "year_built": year_built,
                "property_type": "Single-family home",
                "condition": "Estimated / demo",
            },
            "parcel": {
                "lot_size_acres": lot_size_acres,
            },
            "valuation": {
                "estimated_value": estimated_value,
                "annual_taxes": annual_taxes,
            },
            "amenities": {
                "schools": [
                    "Demo Elementary",
                    "Demo Middle",
                    "Demo High",
                ],
                "nearby_places": [
                    "Grocery store",
                    "Park",
                    "Hospital",
                ],
            },
            "environment": {
                "flood_risk": "Unknown",
                "walkability": "Moderate",
            },
            "listing_url": listing_url,
            "status": "local-demo",
        }
