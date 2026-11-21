from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional

from app.pricing import PriceBreakdown


class RoomType(str, Enum):
    SINGLE = "SINGLE"
    DOUBLE = "DOUBLE"
    SUITE = "SUITE"


CAPACITY = {RoomType.SINGLE: 1, RoomType.DOUBLE: 2, RoomType.SUITE: 4}


class BookingStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


@dataclass
class Room:
    id: int
    number: str
    type: RoomType
    base_price: Decimal

    @property
    def capacity(self) -> int:
        return CAPACITY[self.type]


@dataclass
class Booking:
    id: int
    room_id: int
    guest_name: str
    guest_email: str
    check_in: date
    check_out: date
    guests: int
    breakdown: PriceBreakdown
    status: BookingStatus = BookingStatus.CONFIRMED
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    refund_amount: Optional[Decimal] = None

    @property
    def total_price(self) -> Decimal:
        return self.breakdown.total
