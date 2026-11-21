from datetime import date, datetime
from decimal import Decimal
from typing import List

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.models import BookingStatus, RoomType
from app.validation import validate_stay_dates


class RoomCreate(BaseModel):
    number: str = Field(min_length=1)
    type: RoomType
    base_price: Decimal = Field(gt=0)

    @field_validator("number")
    @classmethod
    def number_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("number cannot be blank")
        return v


class RoomOut(BaseModel):
    id: int
    number: str
    type: RoomType
    capacity: int
    base_price: float


class BookingCreate(BaseModel):
    room_id: int
    guest_name: str
    guest_email: EmailStr
    check_in: date
    check_out: date
    guests: int = Field(ge=1)

    @field_validator("guest_name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("guest_name cannot be empty")
        return v

    @model_validator(mode="after")
    def check_dates(self):
        validate_stay_dates(self.check_in, self.check_out)
        return self


class NightPriceOut(BaseModel):
    night: date
    multiplier: float
    price: float


class BreakdownOut(BaseModel):
    nights: List[NightPriceOut]
    subtotal: float
    discount_percent: int
    discount_amount: float
    total: float


class BookingOut(BaseModel):
    id: int
    room_id: int
    guest_name: str
    guest_email: str
    check_in: date
    check_out: date
    guests: int
    status: BookingStatus
    total_price: float
    created_at: datetime
    breakdown: BreakdownOut


class CancelOut(BaseModel):
    id: int
    status: BookingStatus
    total_price: float
    refund_percent: int
    refund_amount: float
