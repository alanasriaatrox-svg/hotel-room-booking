"""Developer smoke tests only. The Testers' full suite lives in tests/unit and tests/api."""
from datetime import date
from decimal import Decimal

from app.pricing import calculate_price


def test_weekday_low_season_costs_base_price():
    # Mon 2027-01-11, 1 night
    b = calculate_price(Decimal("100"), date(2027, 1, 11), date(2027, 1, 12))
    assert b.total == Decimal("100.00")


def test_weekend_high_season_stacks():
    # Fri 2027-07-02 is high season + weekend => x1.8
    b = calculate_price(Decimal("100"), date(2027, 7, 2), date(2027, 7, 3))
    assert b.total == Decimal("180.00")


def test_create_and_cancel_flow(client, room):
    payload = {"room_id": room["id"], "guest_name": "Amine", "guest_email": "a@b.tn",
               "check_in": "2027-02-01", "check_out": "2027-02-03", "guests": 2}
    r = client.post("/bookings", json=payload)
    assert r.status_code == 201
    assert client.post("/bookings", json=payload).status_code == 409
    c = client.post(f"/bookings/{r.json()['id']}/cancel")
    assert c.status_code == 200 and c.json()["refund_percent"] == 100
    assert client.post("/bookings", json=payload).status_code == 201
