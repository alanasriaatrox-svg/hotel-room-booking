from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from app import clock
from app.availability import is_room_available
from app.models import Booking, BookingStatus
from app.pricing import calculate_price, round_money
from app.schemas import (BookingCreate, BookingOut, BreakdownOut, CancelOut,
                         NightPriceOut)
from app.store import store

router = APIRouter(prefix="/bookings", tags=["bookings"])


def to_out(b: Booking) -> BookingOut:
    br = b.breakdown
    return BookingOut(
        id=b.id, room_id=b.room_id, guest_name=b.guest_name,
        guest_email=b.guest_email, check_in=b.check_in, check_out=b.check_out,
        guests=b.guests, status=b.status, total_price=float(b.total_price),
        created_at=b.created_at,
        breakdown=BreakdownOut(
            nights=[NightPriceOut(night=n.night, multiplier=float(n.multiplier),
                                  price=float(round_money(n.price)))
                    for n in br.nights],
            subtotal=float(round_money(br.subtotal)),
            discount_percent=br.discount_percent,
            discount_amount=float(br.discount_amount),
            total=float(br.total)))


def refund_percent(days_before_check_in: int) -> int:
    """BR-16."""
    if days_before_check_in >= 7:
        return 100
    if days_before_check_in >= 2:
        return 50
    return 0


@router.post("", response_model=BookingOut, status_code=201)
def create_booking(data: BookingCreate):
    with store.lock:  # check + insert must be atomic (AC-3.7)
        room = store.rooms.get(data.room_id)
        if room is None:
            raise HTTPException(404, "Room not found")
        if data.guests > room.capacity:
            raise HTTPException(422, f"Room capacity is {room.capacity}")
        if not is_room_available(store.bookings.values(), room.id,
                                 data.check_in, data.check_out):
            raise HTTPException(409, "Room not available for these dates")
        breakdown = calculate_price(room.base_price, data.check_in, data.check_out)
        booking = Booking(store.next_booking_id(), room.id, data.guest_name,
                          str(data.guest_email), data.check_in, data.check_out,
                          data.guests, breakdown)
        store.bookings[booking.id] = booking
        return to_out(booking)


@router.get("", response_model=List[BookingOut])
def list_bookings(room_id: Optional[int] = None,
                  status: Optional[BookingStatus] = None):
    items = list(store.bookings.values())
    if room_id is not None:
        items = [b for b in items if b.room_id == room_id]
    if status is not None:
        items = [b for b in items if b.status == status]
    return [to_out(b) for b in items]


@router.get("/{booking_id}", response_model=BookingOut)
def get_booking(booking_id: int):
    booking = store.bookings.get(booking_id)
    if booking is None:
        raise HTTPException(404, "Booking not found")
    return to_out(booking)


@router.post("/{booking_id}/cancel", response_model=CancelOut)
def cancel_booking(booking_id: int):
    with store.lock:
        booking = store.bookings.get(booking_id)
        if booking is None:
            raise HTTPException(404, "Booking not found")
        if booking.status != BookingStatus.CONFIRMED:
            raise HTTPException(409, "Booking is already cancelled")
        days = (booking.check_in - clock.today()).days
        if days < 0:
            raise HTTPException(409, "Cannot cancel after check-in date")
        pct = refund_percent(days)
        refund = round_money(booking.total_price * Decimal(pct) / Decimal(100))
        booking.status = BookingStatus.CANCELLED
        booking.refund_amount = refund
        return CancelOut(id=booking.id, status=booking.status,
                         total_price=float(booking.total_price),
                         refund_percent=pct, refund_amount=float(refund))
