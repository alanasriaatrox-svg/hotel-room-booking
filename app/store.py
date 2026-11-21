"""In-memory repository. A re-entrant lock makes check-then-insert atomic (AC-3.7)."""
import threading
from typing import Dict


class Store:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.reset()

    def reset(self) -> None:
        self.rooms: Dict[int, object] = {}
        self.bookings: Dict[int, object] = {}
        self._room_seq = 0
        self._booking_seq = 0

    def next_room_id(self) -> int:
        self._room_seq += 1
        return self._room_seq

    def next_booking_id(self) -> int:
        self._booking_seq += 1
        return self._booking_seq


store = Store()
