"""Single source of 'today' so tests can freeze time (monkeypatch app.clock.today)."""
from datetime import date


def today() -> date:
    return date.today()
