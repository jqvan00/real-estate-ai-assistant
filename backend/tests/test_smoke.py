from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_property_analyze():
    response = client.post(
        "/properties/analyze",
        json={"address": "123 Main St, Bentonville, AR", "listing_url": None},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["property_id"] >= 1
    assert body["verified_profile"]["address"] == "123 Main St, Bentonville, AR"
