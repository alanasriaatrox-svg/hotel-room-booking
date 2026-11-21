"""Pricing rules BR-9 .. BR-14. All money maths uses Decimal."""
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import List

HIGH_SEASON_MULTIPLIER = Decimal("1.5")
WEEKEND_MULTIPLIER = Decimal("1.2")
ONE = Decimal("1")


@dataclass(frozen=True)
class NightPrice:
    night: date
    multiplier: Decimal
    price: Decimal


@dataclass(frozen=True)
class PriceBreakdown:
    nights: List[NightPrice]
    subtotal: Decimal          # unrounded sum of night prices
    discount_percent: int
    discount_amount: Decimal   # display value (rounded)
    total: Decimal             # authoritative, rounded half-up once (BR-14)


def round_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def season_multiplier(night: date) -> Decimal:
    """High season: 15 June .. 15 September inclusive (BR-10)."""
    if (6, 15) <= (night.month, night.day) <= (9, 15):
        return HIGH_SEASON_MULTIPLIER
    return ONE


def weekend_multiplier(night: date) -> Decimal:
    """Nights starting on Friday (4) or Saturday (5) (BR-11)."""
    return WEEKEND_MULTIPLIER if night.weekday() in (4, 5) else ONE


def long_stay_discount_percent(nights: int) -> int:
    """BR-13: 7-13 nights = 10%, 14+ nights = 15%."""
    if nights >= 14:
        return 15
    if nights >= 7:
        return 10
    return 0


def calculate_price(base_price: Decimal, check_in: date, check_out: date) -> PriceBreakdown:
    base_price = Decimal(base_price)
    n_nights = (check_out - check_in).days
    night_prices: List[NightPrice] = []
    subtotal = Decimal("0")
    for i in range(n_nights):
        night = check_in + timedelta(days=i)
        multiplier = season_multiplier(night) * weekend_multiplier(night)
        price = base_price * multiplier
        night_prices.append(NightPrice(night, multiplier, price))
        subtotal += price

    pct = long_stay_discount_percent(n_nights)
    total_raw = subtotal * (Decimal(100) - pct) / Decimal(100)
    total = round_money(total_raw)
    discount_amount = round_money(subtotal - total_raw)
    return PriceBreakdown(night_prices, subtotal, pct, discount_amount, total)
