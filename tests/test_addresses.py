"""Tests for the address book CRUD and proximity-search endpoints."""

from __future__ import annotations

CHICAGO = {
    "street": "233 S Wacker Dr",
    "city": "Chicago",
    "state": "IL",
    "postal_code": "60606",
    "country": "USA",
    "latitude": 41.8788,
    "longitude": -87.6359,
}

MILWAUKEE = {
    "street": "301 W Michigan St",
    "city": "Milwaukee",
    "state": "WI",
    "postal_code": "53203",
    "country": "USA",
    "latitude": 43.0349,
    "longitude": -87.9062,
}

TOKYO = {
    "street": "1 Chome-1-2 Oshiage",
    "city": "Tokyo",
    "state": None,
    "postal_code": "131-0045",
    "country": "Japan",
    "latitude": 35.7101,
    "longitude": 139.8107,
}


def test_create_address(client):
    response = client.post("/addresses", json=CHICAGO)
    assert response.status_code == 201
    body = response.json()
    assert body["city"] == "Chicago"
    assert "id" in body


def test_create_address_rejects_invalid_latitude(client):
    bad = {**CHICAGO, "latitude": 200}
    response = client.post("/addresses", json=bad)
    assert response.status_code == 422


def test_create_address_rejects_blank_city(client):
    bad = {**CHICAGO, "city": "   "}
    response = client.post("/addresses", json=bad)
    assert response.status_code == 422


def test_get_address(client):
    created = client.post("/addresses", json=CHICAGO).json()
    response = client.get(f"/addresses/{created['id']}")
    assert response.status_code == 200
    assert response.json()["street"] == CHICAGO["street"]


def test_get_missing_address_returns_404(client):
    response = client.get("/addresses/999")
    assert response.status_code == 404


def test_list_addresses(client):
    client.post("/addresses", json=CHICAGO)
    client.post("/addresses", json=MILWAUKEE)
    response = client.get("/addresses")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_update_address(client):
    created = client.post("/addresses", json=CHICAGO).json()
    response = client.put(f"/addresses/{created['id']}", json={"city": "Chicago Loop"})
    assert response.status_code == 200
    assert response.json()["city"] == "Chicago Loop"
    # Unrelated fields are left untouched.
    assert response.json()["state"] == CHICAGO["state"]


def test_delete_address(client):
    created = client.post("/addresses", json=CHICAGO).json()
    response = client.delete(f"/addresses/{created['id']}")
    assert response.status_code == 204
    assert client.get(f"/addresses/{created['id']}").status_code == 404


def test_nearby_search_filters_by_radius(client):
    client.post("/addresses", json=CHICAGO)
    client.post("/addresses", json=MILWAUKEE)
    client.post("/addresses", json=TOKYO)

    # Chicago and Milwaukee are ~130km apart; Tokyo is on the other side of the world.
    response = client.get(
        "/addresses/nearby",
        params={"latitude": CHICAGO["latitude"], "longitude": CHICAGO["longitude"], "radius_km": 200},
    )
    assert response.status_code == 200
    cities = {row["city"] for row in response.json()}
    assert cities == {"Chicago", "Milwaukee"}


def test_nearby_search_orders_nearest_first(client):
    client.post("/addresses", json=MILWAUKEE)
    client.post("/addresses", json=CHICAGO)

    response = client.get(
        "/addresses/nearby",
        params={"latitude": CHICAGO["latitude"], "longitude": CHICAGO["longitude"], "radius_km": 500},
    )
    cities_in_order = [row["city"] for row in response.json()]
    assert cities_in_order == ["Chicago", "Milwaukee"]
