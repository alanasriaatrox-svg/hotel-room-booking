"""Unit tests for overlap logic, refund tiers and date validation. BR-1..8, BR-16"""
from datetime import date

import pytest

from app.availability import overlaps
from app.routes.bookings import refund_percent
from app.validation import validate_stay_dates

d = lambda day: date(2027, 3, day)  # noqa: E731


@pytest.mark.parametrize("a,b,expected", [
    ((1, 5), (3, 8), True),     # partial overlap
    ((3, 8), (1, 5), True),     # partial overlap (reversed)
    ((1, 10), (3, 5), True),    # contained
    ((3, 5), (1, 10), True),    # containing
    ((1, 5), (1, 5), True),     # identical
    ((1, 5), (5, 8), False),    # back-to-back  (BR-7)
    ((5, 8), (1, 5), False),    # back-to-back reversed
    ((1, 5), (6, 9), False),    # gap
    ((1, 2), (2, 3), False),    # one-night adjacent
    ((1, 3), (2, 3), True),     # same checkout
    ((1, 3), (1, 2), True),     # same checkin
])
def test_overlaps(a, b, expected):  # BR-5, BR-6, BR-7
    assert overlaps(d(a[0]), d(a[1]), d(b[0]), d(b[1])) is expected


@pytest.mark.parametrize("days,pct", [
    (30, 100), (8, 100), (7, 100), (6, 50), (3, 50), (2, 50), (1, 0), (0, 0),
])
def test_refund_tiers(days, pct):  # BR-16 / AC-5.2
    assert refund_percent(days) == pct


class TestDateValidation:
    # frozen today = 2027-01-10 (see conftest)
    def test_valid_one_night(self):
        validate_stay_dates(date(2027, 1, 11), date(2027, 1, 12))

    def test_checkin_today_allowed(self):  # BR-2
        validate_stay_dates(date(2027, 1, 10), date(2027, 1, 11))

    def test_checkin_yesterday_rejected(self):  # BR-2
        with pytest.raises(ValueError):
            validate_stay_dates(date(2027, 1, 9), date(2027, 1, 11))

    def test_checkout_equals_checkin_rejected(self):  # BR-1
        with pytest.raises(ValueError):
            validate_stay_dates(date(2027, 1, 11), date(2027, 1, 11))

    def test_checkout_before_checkin_rejected(self):  # BR-1
        with pytest.raises(ValueError):
            validate_stay_dates(date(2027, 1, 12), date(2027, 1, 11))

    def test_thirty_nights_allowed(self):  # BR-3
        validate_stay_dates(date(2027, 1, 11), date(2027, 2, 10))

    def test_thirty_one_nights_rejected(self):  # BR-3
        with pytest.raises(ValueError):
            validate_stay_dates(date(2027, 1, 11), date(2027, 2, 11))
