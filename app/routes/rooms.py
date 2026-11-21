from datetime import date
from typing import List

from fastapi import APIRouter, HTTPException, Query

from app.availability import is_room_available
from app.models import Room
from app.schemas import RoomCreate, RoomOut
from app.store import store
from app.validation import validate_stay_dates

router = APIRouter(prefix="/rooms", tags=["rooms"])


def to_out(room: Room) -> RoomOut:
    return RoomOut(id=room.id, number=room.number, type=room.type,
                   capacity=room.capacity, base_price=float(room.base_price))


@router.post("", response_model=RoomOut, status_code=201)
def create_room(data: RoomCreate):
    with store.lock:
        if any(r.number == data.number for r in store.rooms.values()):
            raise HTTPException(409, "Room number already exists")
        room = Room(store.next_room_id(), data.number, data.type, data.base_price)
        store.rooms[room.id] = room
        return to_out(room)


@router.get("", response_model=List[RoomOut])
def list_rooms():
    return [to_out(r) for r in store.rooms.values()]


# NOTE: must be declared before "/{room_id}" or "available" is parsed as an id.
@router.get("/available", response_model=List[RoomOut])
def available_rooms(check_in: date = Query(...), check_out: date = Query(...),
                    guests: int = Query(1, ge=1)):
    try:
        validate_stay_dates(check_in, check_out)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    with store.lock:
        bookings = list(store.bookings.values())
        return [to_out(r) for r in store.rooms.values()
                if r.capacity >= guests
                and is_room_available(bookings, r.id, check_in, check_out)]


@router.get("/{room_id}", response_model=RoomOut)
def get_room(room_id: int):
    room = store.rooms.get(room_id)
    if room is None:
        raise HTTPException(404, "Room not found")
    return to_out(room)
