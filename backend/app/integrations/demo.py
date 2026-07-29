"""Demo property data provider - returns realistic sample data for testing."""
from __future__ import annotations
from typing import Any


DEMO_PROPERTIES = {
    # Rogers, AR properties
    "5335 w cardinal st, rogers, ar 72758": {
        "formattedAddress": "5335 W Cardinal St, Rogers, AR 72758",
        "bedrooms": 4,
        "bathrooms": 2.5,
        "squareFootage": 2340,
        "lotSize": "0.25 acres",
        "yearBuilt": 2015,
        "propertyType": "Single Family",
        "price": 385000,
        "estimatedValue": 398000,
        "lastSaleDate": "2020-05-15",
        "lastSalePrice": 325000,
        "taxYear": 2023,
        "taxTotal": 4200,
        "county": "Benton",
        "state": "AR",
        "zipCode": "72758",
        "latitude": 36.3320,
        "longitude": -94.1185,
        # Nearby comparable averages
        "nearby_1_mile": 405000,
        "nearby_3_mile": 392000,
        "nearby_5_mile": 378000,
        # Schools nearby
        "schools": [
            "Rogers High School (0.8 mi)",
            "Elmwood Middle School (1.2 mi)",
            "Bonnie Grimes Elementary (0.5 mi)",
        ],
    },
    
    # New York properties
    "123 main st, new york, ny 10001": {
        "formattedAddress": "123 Main St, New York, NY 10001",
        "bedrooms": 2,
        "bathrooms": 2,
        "squareFootage": 1100,
        "lotSize": "Condo",
        "yearBuilt": 2005,
        "propertyType": "Condo",
        "price": 1250000,
        "estimatedValue": 1300000,
        "lastSaleDate": "2021-08-20",
        "lastSalePrice": 980000,
        "taxYear": 2023,
        "taxTotal": 18500,
        "county": "New York",
        "state": "NY",
        "zipCode": "10001",
        "latitude": 40.7506,
        "longitude": -73.9971,
        "nearby_1_mile": 1320000,
        "nearby_3_mile": 1280000,
        "nearby_5_mile": 1150000,
        "schools": [
            "PS 11 William T Harris School (0.3 mi)",
            "MS 391 Manhattan West (0.6 mi)",
            "Fashion Industries High School (0.8 mi)",
        ],
    },
    
    # Los Angeles property
    "456 sunset blvd, los angeles, ca 90028": {
        "formattedAddress": "456 Sunset Blvd, Los Angeles, CA 90028",
        "bedrooms": 5,
        "bathrooms": 4,
        "squareFootage": 3200,
        "lotSize": "0.35 acres",
        "yearBuilt": 1985,
        "propertyType": "Single Family",
        "price": 2850000,
        "estimatedValue": 2900000,
        "lastSaleDate": "2019-03-10",
        "lastSalePrice": 2100000,
        "taxYear": 2023,
        "taxTotal": 32000,
        "county": "Los Angeles",
        "state": "CA",
        "zipCode": "90028",
        "latitude": 34.0989,
        "longitude": -118.3267,
        "nearby_1_mile": 3100000,
        "nearby_3_mile": 2750000,
        "nearby_5_mile": 2400000,
        "schools": [
            "Hollywood High School (1.1 mi)",
            "Selma Avenue Elementary (0.7 mi)",
            "Le Conte Middle School (0.9 mi)",
        ],
    },
    
    # Austin, TX property
    "789 oak ave, austin, tx 78701": {
        "formattedAddress": "789 Oak Ave, Austin, TX 78701",
        "bedrooms": 3,
        "bathrooms": 2,
        "squareFootage": 1850,
        "lotSize": "0.18 acres",
        "yearBuilt": 2010,
        "propertyType": "Single Family",
        "price": 675000,
        "estimatedValue": 695000,
        "lastSaleDate": "2022-11-05",
        "lastSalePrice": 580000,
        "taxYear": 2023,
        "taxTotal": 9200,
        "county": "Travis",
        "state": "TX",
        "zipCode": "78701",
        "latitude": 30.2672,
        "longitude": -97.7431,
        "nearby_1_mile": 715000,
        "nearby_3_mile": 680000,
        "nearby_5_mile": 625000,
        "schools": [
            "Austin High School (0.9 mi)",
            "O. Henry Middle School (0.6 mi)",
            "Maplewood Elementary (0.4 mi)",
        ],
    },
    
    # Seattle property
    "321 pine st, seattle, wa 98101": {
        "formattedAddress": "321 Pine St, Seattle, WA 98101",
        "bedrooms": 3,
        "bathrooms": 2.5,
        "squareFootage": 2100,
        "lotSize": "0.22 acres",
        "yearBuilt": 2012,
        "propertyType": "Single Family",
        "price": 1150000,
        "estimatedValue": 1200000,
        "lastSaleDate": "2023-02-18",
        "lastSalePrice": 950000,
        "taxYear": 2023,
        "taxTotal": 13500,
        "county": "King",
        "state": "WA",
        "zipCode": "98101",
        "latitude": 47.6097,
        "longitude": -122.3331,
        "nearby_1_mile": 1280000,
        "nearby_3_mile": 1150000,
        "nearby_5_mile": 1050000,
        "schools": [
            "Garfield High School (1.3 mi)",
            "Washington Middle School (0.8 mi)",
            "Stevens Elementary (0.5 mi)",
        ],
    },
    
    # Miami property
    "555 ocean dr, miami, fl 33139": {
        "formattedAddress": "555 Ocean Dr, Miami, FL 33139",
        "bedrooms": 4,
        "bathrooms": 3.5,
        "squareFootage": 2800,
        "lotSize": "0.28 acres",
        "yearBuilt": 2008,
        "propertyType": "Single Family",
        "price": 1950000,
        "estimatedValue": 2050000,
        "lastSaleDate": "2021-06-12",
        "lastSalePrice": 1650000,
        "taxYear": 2023,
        "taxTotal": 24000,
        "county": "Miami-Dade",
        "state": "FL",
        "zipCode": "33139",
        "latitude": 25.7617,
        "longitude": -80.1918,
        "nearby_1_mile": 2180000,
        "nearby_3_mile": 1950000,
        "nearby_5_mile": 1750000,
        "schools": [
            "Miami Beach Senior High (1.2 mi)",
            "Nautilus Middle School (0.7 mi)",
            "South Pointe Elementary (0.4 mi)",
        ],
    },
    
    # Chicago property
    "900 michigan ave, chicago, il 60611": {
        "formattedAddress": "900 Michigan Ave, Chicago, IL 60611",
        "bedrooms": 2,
        "bathrooms": 2,
        "squareFootage": 1400,
        "lotSize": "Condo",
        "yearBuilt": 2000,
        "propertyType": "Condo",
        "price": 750000,
        "estimatedValue": 780000,
        "lastSaleDate": "2020-09-25",
        "lastSalePrice": 620000,
        "taxYear": 2023,
        "taxTotal": 11000,
        "county": "Cook",
        "state": "IL",
        "zipCode": "60611",
        "latitude": 41.8987,
        "longitude": -87.6238,
        "nearby_1_mile": 820000,
        "nearby_3_mile": 760000,
        "nearby_5_mile": 690000,
        "schools": [
            "Lincoln Park High School (1.5 mi)",
            "Ogden International School (0.9 mi)",
            "Hubbard Elementary (0.6 mi)",
        ],
    },
    
    # Boston property
    "100 beacon st, boston, ma 02108": {
        "formattedAddress": "100 Beacon St, Boston, MA 02108",
        "bedrooms": 3,
        "bathrooms": 2,
        "squareFootage": 1650,
        "lotSize": "Townhouse",
        "yearBuilt": 1920,
        "propertyType": "Townhouse",
        "price": 1450000,
        "estimatedValue": 1500000,
        "lastSaleDate": "2022-04-08",
        "lastSalePrice": 1200000,
        "taxYear": 2023,
        "taxTotal": 16500,
        "county": "Suffolk",
        "state": "MA",
        "zipCode": "02108",
        "latitude": 42.3601,
        "longitude": -71.0589,
        "nearby_1_mile": 1580000,
        "nearby_3_mile": 1450000,
        "nearby_5_mile": 1320000,
        "schools": [
            "Boston Latin School (1.0 mi)",
            "Josiah Quincy Upper School (0.5 mi)",
            "Josiah Quincy Elementary (0.5 mi)",
        ],
    },
}


class DemoPropertyConnector:
    """Demo connector that returns realistic sample data."""
    
    name = "demo"
    
    def fetch_property_record(self, address: str) -> dict[str, Any]:
        """Fetch demo property data by address."""
        # Normalize address for lookup
        normalized = address.lower().strip()
        
        # Try exact match first
        if normalized in DEMO_PROPERTIES:
            record = DEMO_PROPERTIES[normalized]
            return {
                "source": self.name,
                "endpoint": "properties",
                "status": "matched",
                "record": record,
                "raw": [record],
            }
        
        # Try partial match (first property that contains search terms)
        search_terms = normalized.replace(",", "").split()
        for demo_addr, record in DEMO_PROPERTIES.items():
            demo_terms = demo_addr.replace(",", "").split()
            if any(term in demo_terms for term in search_terms if len(term) > 2):
                return {
                    "source": self.name,
                    "endpoint": "properties",
                    "status": "matched",
                    "record": record,
                    "raw": [record],
                }
        
        # No match found
        return {
            "source": self.name,
            "endpoint": "properties",
            "status": "no_match",
            "message": f"No demo data for '{address}'. Try: 5335 W Cardinal St, Rogers, AR 72758",
            "record": {},
            "raw": {},
        }
    
    def fetch_value_estimate(self, address: str) -> dict[str, Any]:
        """Fetch demo value estimate."""
        result = self.fetch_property_record(address)
        record = result.get("record", {})
        
        if record:
            value_data = {
                "price": record.get("estimatedValue"),
                "priceRangeLow": int(record.get("estimatedValue", 0) * 0.95),
                "priceRangeHigh": int(record.get("estimatedValue", 0) * 1.05),
                "rent": int(record.get("estimatedValue", 0) * 0.004),  # ~0.4% of value per month
                "rentRangeLow": int(record.get("estimatedValue", 0) * 0.0035),
                "rentRangeHigh": int(record.get("estimatedValue", 0) * 0.0045),
            }
            
            return {
                "source": self.name,
                "endpoint": "avm/value",
                "status": "ok",
                "value": value_data,
                "raw": value_data,
            }
        
        return {
            "source": self.name,
            "endpoint": "avm/value",
            "status": "no_match",
            "value": {},
            "raw": {},
        }
