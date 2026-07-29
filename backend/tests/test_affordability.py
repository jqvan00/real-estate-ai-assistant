from app.routers import affordability


def test_state_directory_contains_arkansas():
    payload = affordability.states()
    arkansas = next(
        state for state in payload["states"] if state["code"] == "AR"
    )
    assert arkansas == {"fips": "05", "code": "AR", "name": "Arkansas"}


def test_county_estimate_uses_effective_tax_rate(monkeypatch):
    monkeypatch.setattr(
        affordability,
        "_county_tax_statistics",
        lambda state, county: {
            "county_name": "Benton County",
            "median_annual_tax": 1500.0,
            "median_home_value": 250000.0,
            "effective_tax_rate": 0.006,
        },
    )

    payload = affordability.estimate(
        state="05",
        county="007",
        purchase_price=400000,
    )

    assert payload["property_tax"]["annual_estimate"] == 2400
    assert payload["property_tax"]["effective_rate_percent"] == 0.6
    assert payload["homeowners_insurance"]["annual_estimate"] == 2480
