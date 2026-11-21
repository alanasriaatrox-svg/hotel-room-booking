from datetime import date

import pytest
from fastapi.testclient import TestClient

from app import clock
from app.main import app
from app.store import store

FROZEN_TODAY = date(2027, 1, 10)  # a Sunday, low season


@pytest.fixture(autouse=True)
def frozen_today(monkeypatch):
    monkeypatch.setattr(clock, "today", lambda: FROZEN_TODAY)


@pytest.fixture(autouse=True)
def clean_store():
    store.reset()
    yield
    store.reset()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def room(client):
    r = client.post("/rooms", json={"number": "101", "type": "DOUBLE", "base_price": 100})
    assert r.status_code == 201
    return r.json()
