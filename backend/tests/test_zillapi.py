from app.integrations.zillapi import ZillAPIConnector


def test_zillapi_normalizes_property_detail_fields():
    record = ZillAPIConnector._normalize_property(
        {
            "zpid": 12345,
            "address": {
                "streetAddress": "4004 Wittenburg Dr",
                "city": "McKinney",
                "state": "TX",
                "zipcode": "75071",
            },
            "price": 830_000,
            "bedrooms": 5,
            "bathrooms": 4,
            "livingArea": 3_613,
            "yearBuilt": 2019,
            "zestimate": 825_000,
            "description": "Hardwood floors and a covered patio.",
            "schools": [{"name": "Example Elementary", "distance": 0.8}],
            "resoFacts": {
                "flooring": ["Carpet", "Ceramic Tile", "Wood"],
                "appliances": ["Dishwasher", "Gas Cooktop"],
            },
        }
    )

    assert record["formattedAddress"] == "4004 Wittenburg Dr, McKinney, TX 75071"
    assert record["price"] == 830_000
    assert record["squareFootage"] == 3_613
    assert record["yearBuilt"] == 2019
    assert record["flooring"] == ["Carpet", "Ceramic Tile", "Wood"]
    assert record["schools"][0]["name"] == "Example Elementary"

    estimate = ZillAPIConnector(api_key="test-key").fetch_value_estimate(record)
    assert estimate["value"]["price"] == 825_000


def test_zillapi_prefers_url_lookup_for_zillow_links(monkeypatch):
    connector = ZillAPIConnector(api_key="test-key")
    calls = []

    def fake_get(path, params=None):
        calls.append((path, params))
        return {"data": {"zpid": "83151774", "price": 450_000}}

    monkeypatch.setattr(connector, "_get", fake_get)

    result = connector.fetch_property_record(
        "208 Cowans St, Lowell, AR 72745",
        "https://www.zillow.com/homedetails/208-Cowans-St/83151774_zpid/",
    )

    assert result["status"] == "matched"
    assert calls[0][0] == "/properties/by-url"
    assert calls[0][1]["status"] == "FOR_SALE"


def test_zillapi_recent_sales_are_filtered_and_given_exact_distances(monkeypatch):
    connector = ZillAPIConnector(api_key="test-key")
    monkeypatch.setattr(
        connector,
        "_post",
        lambda *_args, **_kwargs: {
            "data": [
                {
                    "zpid": "comp-1",
                    "address": "100 Similar St",
                    "listingSoldPrice": {
                        "amount": 700_000,
                        "currency": "USD",
                    },
                    "beds": 4,
                    "baths": 3,
                    "area": 2_600,
                    "yearBuilt": 2021,
                    "latLong": {"latitude": 33.2420, "longitude": -96.8100},
                    "statusType": "RECENTLY_SOLD",
                },
                {
                    "zpid": "too-large",
                    "address": "200 Oversized St",
                    "unformattedPrice": 1_400_000,
                    "beds": 6,
                    "area": 5_500,
                    "yearBuilt": 2021,
                    "latLong": {"latitude": 33.2430, "longitude": -96.8110},
                },
            ]
        },
    )

    result = connector.fetch_recently_sold_comparables(
        {
            "zpid": "subject",
            "latitude": 33.2400,
            "longitude": -96.8100,
            "propertyType": "SINGLE_FAMILY",
            "bedrooms": 4,
            "bathrooms": 3,
            "squareFootage": 2_506,
            "yearBuilt": 2023,
        }
    )

    assert result["status"] == "ok"
    assert len(result["comparables"]) == 1
    assert result["comparables"][0]["price"] == 700_000
    assert 0 < result["comparables"][0]["distance"] < 1
    assert result["comparables"][0]["pricePerSquareFoot"] == 269.23
    assert result["comparables"][0]["cmaAdjustedValue"] == 674_692
    assert result["comparables"][0]["cmaScore"] >= 80
    assert result["comparables"][0]["matchQuality"] == "strong"
