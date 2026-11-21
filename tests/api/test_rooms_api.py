"""US-1: AC-1.1 .. AC-1.4"""
import pytest


def test_create_room_ok(client):  # AC-1.1
    r = client.post("/rooms", json={"number": "101", "type": "SUITE", "base_price": 250.5})
    assert r.status_code == 201
    body = r.json()
    assert body["number"] == "101" and body["capacity"] == 4 and body["base_price"] == 250.5


@pytest.mark.parametrize("type_,cap", [("SINGLE", 1), ("DOUBLE", 2), ("SUITE", 4)])
def test_capacity_by_type(client, type_, cap):
    r = client.post("/rooms", json={"number": "X", "type": type_, "base_price": 10})
    assert r.json()["capacity"] == cap


def test_duplicate_number_conflict(client, room):  # AC-1.2
    r = client.post("/rooms", json={"number": "101", "type": "SINGLE", "base_price": 50})
    assert r.status_code == 409


@pytest.mark.parametrize("payload", [
    {"number": "1", "type": "DOUBLE", "base_price": 0},
    {"number": "1", "type": "DOUBLE", "base_price": -5},
    {"number": "1", "type": "PENTHOUSE", "base_price": 50},
    {"number": "", "type": "DOUBLE", "base_price": 50},
    {"number": "   ", "type": "DOUBLE", "base_price": 50},
    {"type": "DOUBLE", "base_price": 50},
    {"number": "1", "type": "DOUBLE", "base_price": "abc"},
])
def test_invalid_room_payloads(client, payload):  # AC-1.3
    assert client.post("/rooms", json=payload).status_code == 422


def test_list_and_get_rooms(client, make):  # AC-1.4
    a, b = make("1"), make("2")
    assert len(client.get("/rooms").json()) == 2
    assert client.get(f"/rooms/{a['id']}").json()["number"] == "1"
    assert client.get("/rooms/9999").status_code == 404
