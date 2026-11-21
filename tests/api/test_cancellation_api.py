"""US-5: AC-5.1 .. AC-5.6. Frozen today = 2027-01-10 (see tests/conftest.py)."""
from datetime import date

import pytest

from app import clock
from tests.api.conftest import booking_payload


def book(client, room, check_in, check_out):
    r = client.post("/bookings", json=booking_payload(room["id"], check_in, check_out, guests=1))
    assert r.status_code == 201, r.text
    return r.json()


def test_cancel_ok(client, room):  # AC-5.1
    b = book(client, room, "2027-02-01", "2027-02-02")
    r = client.post(f"/bookings/{b['id']}/cancel")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "CANCELLED" and body["refund_amount"] == 100.0
    assert client.get(f"/bookings/{b['id']}").json()["status"] == "CANCELLED"


@pytest.mark.parametrize("check_in,check_out,days,pct,refund", [
    ("2027-01-17", "2027-01-18", 7, 100, 100.0),   # Sun night 100
    ("2027-01-16", "2027-01-17", 6, 50, 60.0),     # Sat night 120
    ("2027-01-12", "2027-01-13", 2, 50, 50.0),     # Tue night 100
    ("2027-01-11", "2027-01-12", 1, 0, 0.0),       # Mon night 100
    ("2027-01-10", "2027-01-11", 0, 0, 0.0),       # today
    ("2027-03-01", "2027-03-02", 50, 100, 100.0),
])
def test_refund_boundaries(client, room, check_in, check_out, days, pct, refund):  # AC-5.2
    b = book(client, room, check_in, check_out)
    r = client.post(f"/bookings/{b['id']}/cancel").json()
    assert r["refund_percent"] == pct
    assert r["refund_amount"] == refund


def test_refund_computed_on_discounted_total(client, room):  # BR-18
    b = book(client, room, "2027-02-01", "2027-02-08")   # 7 nights, discounted
    r = client.post(f"/bookings/{b['id']}/cancel").json()
    assert r["total_price"] == b["total_price"]
    assert r["refund_amount"] == b["total_price"]       # 100% tier


def test_refund_rounding_half_up(client, make):
    room = make("R", "DOUBLE", price=33.33)
    b = book(client, room, "2027-01-12", "2027-01-13")  # 2 days before -> 50%
    r = client.post(f"/bookings/{b['id']}/cancel").json()
    assert r["refund_amount"] == 16.67                  # 16.665 -> 16.67


def test_double_cancel_conflict(client, room):  # AC-5.3
    b = book(client, room, "2027-02-01", "2027-02-02")
    assert client.post(f"/bookings/{b['id']}/cancel").status_code == 200
    assert client.post(f"/bookings/{b['id']}/cancel").status_code == 409


def test_cancel_after_check_in_conflict(client, room, monkeypatch):  # AC-5.4, BR-17
    b = book(client, room, "2027-02-01", "2027-02-05")
    monkeypatch.setattr(clock, "today", lambda: date(2027, 2, 2))
    assert client.post(f"/bookings/{b['id']}/cancel").status_code == 409


def test_cancel_on_check_in_day_allowed_zero_refund(client, room, monkeypatch):
    b = book(client, room, "2027-02-01", "2027-02-05")
    monkeypatch.setattr(clock, "today", lambda: date(2027, 2, 1))
    r = client.post(f"/bookings/{b['id']}/cancel")
    assert r.status_code == 200 and r.json()["refund_amount"] == 0.0


def test_room_available_again_after_cancel(client, room):  # AC-5.5
    b = book(client, room, "2027-02-01", "2027-02-03")
    client.post(f"/bookings/{b['id']}/cancel")
    r = client.post("/bookings", json=booking_payload(room["id"], "2027-02-01", "2027-02-03"))
    assert r.status_code == 201


def test_cancel_unknown_404(client):  # AC-5.6
    assert client.post("/bookings/999/cancel").status_code == 404
