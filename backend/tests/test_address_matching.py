from app.integrations.zillow_live_data import ZillowLiveDataConnector
from app.integrations.url_parser import extract_zillow_zpid
from app.services.llm_assistant_service import PropertyAssistant
from app.services.property_service import (
    _addresses_match,
    _latest_price_change,
    _listing_market_activity,
    _median_comparable_value,
    _normalized_price_history,
)


def test_address_matching_accepts_case_and_common_suffix_variants():
    assert _addresses_match(
        "806 copper street, lowell, ar 72745",
        "806 Copper St, Lowell, AR 72745",
    )


def test_zillow_search_does_not_substitute_an_unrelated_zip_result(monkeypatch):
    connector = ZillowLiveDataConnector(api_key="test-key")
    monkeypatch.setattr(
        connector,
        "_get",
        lambda *_args, **_kwargs: {
            "results": [
                {
                    "address": "1519 Lancelot St, Lowell, AR 72745",
                    "beds": 3,
                }
            ]
        },
    )

    response = connector.fetch_property_record(
        "806 Copper Street, Lowell, AR 72745"
    )

    assert response["status"] == "no_match"
    assert response["record"] == {}


def test_extracts_zillow_property_id_from_listing_url():
    assert (
        extract_zillow_zpid(
            "https://www.zillow.com/homedetails/"
            "208-Cowans-St-Lowell-AR-72745/83151774_zpid/"
        )
        == "83151774"
    )


def test_nearby_values_use_median_of_comparables_within_subject_radius():
    comparables = [
        {"price": 300_000, "distance": 0.5},
        {"price": 400_000, "distance": 0.9},
        {"price": 2_000_000, "distance": 1.5},
    ]

    value, count = _median_comparable_value(comparables, 1)

    assert value == 350_000
    assert count == 2


def test_listing_market_activity_uses_posted_date_and_latest_price_change():
    listed_date, price_change_date = _listing_market_activity(
        {
            "listedDate": "2026-07-01",
            "priceHistory": [
                {
                    "date": "2026-07-20",
                    "event": "Price change",
                    "priceChangeRate": -0.03,
                },
                {"date": "2026-07-01", "event": "Listed for sale"},
            ],
        }
    )

    assert listed_date == "2026-07-01"
    assert price_change_date == "2026-07-20"


def test_latest_price_change_reports_previous_current_percent_and_direction():
    change = _latest_price_change(
        [
            {
                "date": "2026-07-20",
                "event": "Price change",
                "price": 675_000,
                "priceChangeRate": -0.0357,
            },
            {
                "date": "2026-07-01",
                "event": "Listed for sale",
                "price": 700_000,
            },
        ]
    )

    assert change == {
        "date": "2026-07-20",
        "previous_price": 700_000,
        "current_price": 675_000,
        "percent": 3.6,
        "direction": "decrease",
    }


def test_latest_price_change_recognizes_realtor_decreased_wording():
    change = _latest_price_change(
        [
            {
                "date": "2026-07-18",
                "event": "Price decreased",
                "price": 237_550,
            },
            {
                "date": "2026-07-01",
                "event": "Price decreased",
                "price": 238_900,
            },
            {
                "date": "2026-06-23",
                "event": "Price increased",
                "price": 240_550,
            },
        ]
    )

    assert change == {
        "date": "2026-07-18",
        "previous_price": 238_900,
        "current_price": 237_550,
        "percent": 0.6,
        "direction": "decrease",
    }


def test_normalized_price_history_calculates_each_change():
    history = _normalized_price_history(
        [
            {
                "date": "2026-07-18",
                "event": "Price decreased",
                "price": 237_550,
            },
            {
                "date": "2026-07-01",
                "event": "Price decreased",
                "price": 238_900,
            },
            {
                "date": "2026-06-23",
                "event": "Price increased",
                "price": 240_550,
            },
        ]
    )

    assert history[0]["dollar_change"] == -1_350
    assert history[0]["percent_change"] == 0.6
    assert history[0]["direction"] == "decrease"
    assert history[1]["dollar_change"] == -1_650


def test_briefing_prompt_forbids_advice_and_unsupported_updates():
    assistant = PropertyAssistant.__new__(PropertyAssistant)

    prompt = assistant._build_briefing_prompt(
        {
            "formatted_address": "208 Cowans St, Lowell, AR 72745",
            "listing_price": 450_000,
            "bedrooms": 4,
            "bathrooms": 2,
            "square_footage": 2_141,
            "year_built": 2012,
            "listing_description": "A covered patio opens to the fenced backyard.",
            "interior_features": ["Granite Counters", "Walk-In Closet(s)"],
            "flooring": ["Tile", "Wood"],
        }
    )

    assert "Do not give recommendations, advice" in prompt
    assert "Never infer or invent a feature" in prompt
    assert "you MUST summarize its documented home" in prompt
    assert "Property Snapshot" in prompt
    assert "Listing Highlights" in prompt
    assert "Always include all seven Property Snapshot bullets" in prompt
    assert "A covered patio opens to the fenced backyard." in prompt
    assert "Granite Counters" in prompt
    assert "Tile" in prompt
