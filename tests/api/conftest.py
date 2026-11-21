import pytest


def make_room(client, number="101", type_="DOUBLE", price=100):
    r = client.post("/rooms", json={"number": number, "type": type_, "base_price": price})
    assert r.status_code == 201, r.text
    return r.json()


def booking_payload(room_id, check_in="2027-02-01", check_out="2027-02-03",
                    guests=2, name="Amine", email="amine@example.com"):
    return {"room_id": room_id, "guest_name": name, "guest_email": email,
            "check_in": check_in, "check_out": check_out, "guests": guests}


@pytest.fixture
def make(client):
    return lambda *a, **k: make_room(client, *a, **k)
