"""US-2: AC-2.1 .. AC-2.5"""
from tests.api.conftest import booking_payload

Q = "/rooms/available"


def numbers(resp):
    return sorted(r["number"] for r in resp.json())


def test_empty_hotel_returns_empty_list(client):
    assert client.get(Q, params={"check_in": "2027-02-01", "check_out": "2027-02-03"}).json() == []


def test_all_free_rooms_listed(client, make):
    make("1"), make("2")
    r = client.get(Q, params={"check_in": "2027-02-01", "check_out": "2027-02-03"})
    assert numbers(r) == ["1", "2"]


def test_booked_room_excluded(client, make):  # AC-2.2
    a, _ = make("1"), make("2")
    client.post("/bookings", json=booking_payload(a["id"]))
    r = client.get(Q, params={"check_in": "2027-02-02", "check_out": "2027-02-04"})
    assert numbers(r) == ["2"]


def test_cancelled_booking_does_not_block(client, make):  # AC-2.3
    a = make("1")
    b = client.post("/bookings", json=booking_payload(a["id"])).json()
    client.post(f"/bookings/{b['id']}/cancel")
    r = client.get(Q, params={"check_in": "2027-02-01", "check_out": "2027-02-03"})
    assert numbers(r) == ["1"]


def test_back_to_back_is_available(client, make):  # AC-2.4
    a = make("1")
    client.post("/bookings", json=booking_payload(a["id"], "2027-02-01", "2027-02-03"))
    r = client.get(Q, params={"check_in": "2027-02-03", "check_out": "2027-02-05"})
    assert numbers(r) == ["1"]
    r = client.get(Q, params={"check_in": "2027-01-30", "check_out": "2027-02-01"})
    assert numbers(r) == ["1"]


def test_guest_count_filters_by_capacity(client, make):  # AC-2.1
    make("S", "SINGLE"), make("D", "DOUBLE"), make("U", "SUITE")
    p = {"check_in": "2027-02-01", "check_out": "2027-02-03"}
    assert numbers(client.get(Q, params={**p, "guests": 1})) == ["D", "S", "U"]
    assert numbers(client.get(Q, params={**p, "guests": 2})) == ["D", "U"]
    assert numbers(client.get(Q, params={**p, "guests": 3})) == ["U"]
    assert numbers(client.get(Q, params={**p, "guests": 5})) == []


def test_invalid_search_parameters(client, make):  # AC-2.5
    make("1")
    bad = [
        {"check_in": "2027-02-03", "check_out": "2027-02-01"},
        {"check_in": "2027-02-01", "check_out": "2027-02-01"},
        {"check_in": "2027-01-01", "check_out": "2027-01-05"},   # past
        {"check_in": "2027-02-01", "check_out": "2027-03-05"},   # > 30 nights
        {"check_in": "not-a-date", "check_out": "2027-02-01"},
        {"check_in": "2027-02-01"},                               # missing
        {"check_in": "2027-02-01", "check_out": "2027-02-03", "guests": 0},
    ]
    for params in bad:
        assert client.get(Q, params=params).status_code == 422, params
