"""Unit tests for pricing rules. Traceability: BR-9..BR-14, AC-4.x"""
from datetime import date
from decimal import Decimal

import pytest

from app.pricing import (calculate_price, long_stay_discount_percent,
                         season_multiplier, weekend_multiplier)

D = Decimal


@pytest.mark.parametrize("night,expected", [
    (date(2027, 6, 14), D("1")),     # day before high season
    (date(2027, 6, 15), D("1.5")),   # first high-season day
    (date(2027, 7, 20), D("1.5")),
    (date(2027, 9, 15), D("1.5")),   # last high-season day
    (date(2027, 9, 16), D("1")),     # day after
    (date(2027, 1, 1), D("1")),
    (date(2027, 12, 31), D("1")),
])
def test_season_multiplier_boundaries(night, expected):  # BR-10
    assert season_multiplier(night) == expected


@pytest.mark.parametrize("night,expected", [
    (date(2027, 1, 11), D("1")),    # Mon
    (date(2027, 1, 14), D("1")),    # Thu
    (date(2027, 1, 15), D("1.2")),  # Fri
    (date(2027, 1, 16), D("1.2")),  # Sat
    (date(2027, 1, 17), D("1")),    # Sun
])
def test_weekend_multiplier(night, expected):  # BR-11
    assert weekend_multiplier(night) == expected


@pytest.mark.parametrize("nights,pct", [
    (1, 0), (6, 0), (7, 10), (8, 10), (13, 10), (14, 15), (30, 15),
])
def test_discount_thresholds(nights, pct):  # BR-13 / AC-4.5
    assert long_stay_discount_percent(nights) == pct


@pytest.mark.parametrize("ci,co,expected", [
    (date(2027, 1, 11), date(2027, 1, 12), "100.00"),   # AC-4.1 Mon, low
    (date(2027, 1, 15), date(2027, 1, 16), "120.00"),   # AC-4.2 Fri
    (date(2027, 1, 16), date(2027, 1, 17), "120.00"),   # AC-4.2 Sat
    (date(2027, 1, 17), date(2027, 1, 18), "100.00"),   # Sun is not weekend
    (date(2027, 7, 1), date(2027, 7, 2), "150.00"),     # AC-4.3 Thu, high
    (date(2027, 7, 2), date(2027, 7, 3), "180.00"),     # AC-4.3 Fri, high
    (date(2027, 7, 3), date(2027, 7, 4), "180.00"),     # Sat, high
    (date(2027, 6, 14), date(2027, 6, 17), "400.00"),   # AC-4.4 100+150+150
    (date(2027, 9, 14), date(2027, 9, 17), "400.00"),   # 150+150+100 (exit season)
])
def test_total_price(ci, co, expected):
    assert calculate_price(D("100"), ci, co).total == D(expected)


@pytest.mark.parametrize("ci,co,total,pct", [
    (date(2027, 1, 11), date(2027, 1, 17), "640.00", 0),     # 6 nights
    (date(2027, 1, 11), date(2027, 1, 18), "666.00", 10),    # 7 nights: 740 * 0.9
    (date(2027, 1, 11), date(2027, 1, 24), "1242.00", 10),   # 13 nights: 1380 * 0.9
    (date(2027, 1, 11), date(2027, 1, 25), "1258.00", 15),   # 14 nights: 1480 * 0.85
])
def test_long_stay_discount_applied(ci, co, total, pct):  # AC-4.5
    b = calculate_price(D("100"), ci, co)
    assert b.discount_percent == pct
    assert b.total == D(total)


def test_rounding_is_half_up():  # BR-14
    b = calculate_price(D("10.005"), date(2027, 1, 11), date(2027, 1, 12))
    assert b.total == D("10.01")


def test_rounding_only_on_final_total():  # AC-4.7
    # 3 nights x 0.004 = 0.012 -> 0.01. Rounding each night first would give 0.00.
    b = calculate_price(D("0.004"), date(2027, 1, 11), date(2027, 1, 14))
    assert b.total == D("0.01")


def test_leap_year_february():
    # 2028 is a leap year: 28 Feb -> 1 Mar = 2 nights (Mon, Tue)
    b = calculate_price(D("100"), date(2028, 2, 28), date(2028, 3, 1))
    assert len(b.nights) == 2
    assert b.total == D("200.00")


def test_year_end_crossing():
    # Thu 30 Dec 2027 -> Mon 3 Jan 2028 : Thu, Fri(x1.2), Sat(x1.2), Sun
    b = calculate_price(D("100"), date(2027, 12, 30), date(2028, 1, 3))
    assert len(b.nights) == 4
    assert b.total == D("440.00")
