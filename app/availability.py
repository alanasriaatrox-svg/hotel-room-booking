"""Availability rules BR-5 .. BR-7."""
from datetime import date
from typing import Iterable

from app.models import Booking, BookingStatus


def overlaps(a_in: date, a_out: date, b_in: date, b_out: date) -> bool:
    """Half-open intervals [in, out): back-to-back stays do not overlap (BR-5, BR-7)."""
    return a_in < b_out and b_in < a_out


def is_room_available(bookings: Iterable[Booking], room_id: int,
                      check_in: date, check_out: date) -> bool:
    for b in bookings:
        if b.room_id != room_id or b.status != BookingStatus.CONFIRMED:
            continue
        if overlaps(check_in, check_out, b.check_in, b.check_out):
            return False
    return True
