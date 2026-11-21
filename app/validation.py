"""Date rules BR-1 .. BR-3."""
from datetime import date

from app import clock

MIN_NIGHTS = 1
MAX_NIGHTS = 30


def validate_stay_dates(check_in: date, check_out: date) -> None:
    if check_out <= check_in:
        raise ValueError("check_out must be after check_in")
    if check_in < clock.today():
        raise ValueError("check_in cannot be in the past")
    nights = (check_out - check_in).days
    if not (MIN_NIGHTS <= nights <= MAX_NIGHTS):
        raise ValueError(f"stay must be between {MIN_NIGHTS} and {MAX_NIGHTS} nights")
