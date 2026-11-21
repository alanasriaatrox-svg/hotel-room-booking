"""US-3, US-4, US-6: booking creation, validation, price breakdown, listing."""
from concurrent.futures import ThreadPoolExecutor

import pytest

from tests.api.conftest import booking_payload


def test_create_booking_ok(client, room):  # AC-3.1
    r = client.post("/bookings", json=booking_payload(room["id"]))
    assert r.status_code == 201
    b = r.json()
    assert b["status"] == "CONFIRMED"
    assert b["total_price"] == 200.0          # Mon+Tue 1 Feb 2027, base 100
    assert b["check_in"] == "2027-02-01"


def test_unknown_room_404(client):  # AC-3.3
    assert client.post("/bookings", json=booking_payload(999)).status_code == 404


@pytest.mark.parametrize("second,expected", [
    (("2027-02-01", "2027-02-03"), 409),   # identical
    (("2027-02-02", "2027-02-04"), 409),   # partial overlap end
    (("2027-01-31", "2027-02-02"), 409),   # partial overlap start
    (("2027-02-01", "2027-02-02"), 409),   # contained, same start
    (("2027-01-25", "2027-02-10"), 409),   # containing
    (("2027-02-03", "2027-02-05"), 201),   # back-to-back after (BR-7)
    (("2027-01-30", "2027-02-01"), 201),   # back-to-back before
    (("2027-02-10", "2027-02-12"), 201),   # far away
])
def test_overlap_rules_via_api(client, room, second, expected):  # AC-3.2, BR-5..7
    client.post("/bookings", json=booking_payload(room["id"], "2027-02-01", "2027-02-03"))
    r = client.post("/bookings", json=booking_payload(room["id"], *second))
    assert r.status_code == expected


def test_same_dates_different_rooms_ok(client, make):
    a, b = make("1"), make("2")
    assert client.post("/bookings", json=booking_payload(a["id"])).status_code == 201
    assert client.post("/bookings", json=booking_payload(b["id"])).status_code == 201


@pytest.mark.parametrize("type_,guests,expected", [
    ("SINGLE", 1, 201), ("SINGLE", 2, 422),
    ("DOUBLE", 2, 201), ("DOUBLE", 3, 422),
    ("SUITE", 4, 201), ("SUITE", 5, 422),
    ("SINGLE", 0, 422), ("DOUBLE", -1, 422),
])
def test_guest_capacity(client, make, type_, guests, expected):  # AC-3.4, BR-8
    room = make("R", type_)
    r = client.post("/bookings", json=booking_payload(room["id"], guests=guests))
    assert r.status_code == expected


@pytest.mark.parametrize("override", [
    {"guest_email": "not-an-email"}, {"guest_email": ""}, {"guest_email": "a@"},
    {"guest_name": ""}, {"guest_name": "   "},
    {"check_in": "2027-02-03", "check_out": "2027-02-01"},
    {"check_in": "2027-02-01", "check_out": "2027-02-01"},
    {"check_in": "2027-01-09", "check_out": "2027-01-12"},   # past
    {"check_in": "2027-02-01", "check_out": "2027-03-04"},   # 31 nights
    {"check_in": "01/02/2027"},                               # wrong format
    {"check_in": "2027-02-30"},                               # impossible date
])
def test_invalid_booking_payloads(client, room, override):  # AC-3.5, AC-3.6
    payload = {**booking_payload(room["id"]), **override}
    assert client.post("/bookings", json=payload).status_code == 422


def test_missing_fields_422(client, room):
    assert client.post("/bookings", json={"room_id": room["id"]}).status_code == 422


def test_check_in_today_is_allowed(client, room):  # BR-2
    r = client.post("/bookings", json=booking_payload(room["id"], "2027-01-10", "2027-01-11"))
    assert r.status_code == 201


def test_thirty_nights_allowed(client, room):  # BR-3
    r = client.post("/bookings", json=booking_payload(room["id"], "2027-02-01", "2027-03-03"))
    assert r.status_code == 201


def test_concurrent_requests_only_one_succeeds(client, room):  # AC-3.7
    payload = booking_payload(room["id"])
    with ThreadPoolExecutor(max_workers=10) as pool:
        codes = list(pool.map(lambda _: client.post("/bookings", json=payload).status_code,
                              range(20)))
    assert codes.count(201) == 1
    assert codes.count(409) == 19


# ---------- US-4 price breakdown via API ----------
def test_breakdown_contents(client, room):  # AC-4.6
    # Fri 15 Jan -> Mon 18 Jan 2027: Fri 120, Sat 120, Sun 100
    r = client.post("/bookings", json=booking_payload(room["id"], "2027-01-15", "2027-01-18"))
    b = client.get(f"/bookings/{r.json()['id']}").json()["breakdown"]
    assert [n["price"] for n in b["nights"]] == [120.0, 120.0, 100.0]
    assert b["subtotal"] == 340.0 and b["discount_percent"] == 0 and b["total"] == 340.0


def test_breakdown_with_discount(client, room):
    r = client.post("/bookings", json=booking_payload(room["id"], "2027-01-11", "2027-01-18"))
    b = r.json()
    assert b["total_price"] == 666.0
    assert b["breakdown"]["discount_percent"] == 10
    assert b["breakdown"]["subtotal"] == 740.0
    assert b["breakdown"]["discount_amount"] == 74.0


def test_get_unknown_booking_404(client):
    assert client.get("/bookings/12345").status_code == 404


# ---------- US-6 listing ----------
def test_list_and_filters(client, make):  # AC-6.1, AC-6.2
    a, b = make("1"), make("2")
    b1 = client.post("/bookings", json=booking_payload(a["id"])).json()
    client.post("/bookings", json=booking_payload(b["id"]))
    client.post(f"/bookings/{b1['id']}/cancel")

    assert len(client.get("/bookings").json()) == 2
    assert len(client.get("/bookings", params={"room_id": a["id"]}).json()) == 1
    assert len(client.get("/bookings", params={"status": "CANCELLED"}).json()) == 1
    assert len(client.get("/bookings", params={"status": "CONFIRMED", "room_id": a["id"]}).json()) == 0
    assert len(client.get("/bookings", params={"status": "CONFIRMED", "room_id": b["id"]}).json()) == 1


def test_invalid_status_filter(client):  # AC-6.3
    assert client.get("/bookings", params={"status": "WHATEVER"}).status_code == 422
