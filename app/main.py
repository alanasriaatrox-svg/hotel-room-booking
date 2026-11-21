from fastapi import FastAPI

from app.routes import bookings, rooms

app = FastAPI(title="Hotel Room Booking API", version="1.0.0")
app.include_router(rooms.router)
app.include_router(bookings.router)
