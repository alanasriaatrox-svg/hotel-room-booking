# Hotel Room Booking System

## 1. Project Description

A backend REST API for managing hotel rooms and reservations. Guests can search for available rooms, book a stay, view the price breakdown, and cancel with a refund that depends on how close the cancellation is to check-in.

The project is intentionally rule-heavy (dates, overlaps, seasonal pricing, discounts, refunds) so that testing must go beyond happy paths.

**Team roles:** 2 Developers, 2 Testers. *(fill in names + GitHub usernames)*

## 2. Technology Stack

| Layer | Choice |
|---|---|
| Language | Python 3.11+ |
| Framework | FastAPI |
| Validation | Pydantic |
| Storage | SQLite (via SQLAlchemy) or in-memory repository |
| Unit/API tests | pytest, pytest-cov, httpx (FastAPI TestClient) |
| Test data | Faker, parametrized pytest |
| AI tools | *(fill in: model + tool, e.g. Claude via web, Copilot in VS Code)* |

## 3. Domain Model

- **Room**: `id`, `number` (unique), `type` (`SINGLE` | `DOUBLE` | `SUITE`), `capacity`, `base_price` (per night, in TND).
- **Booking**: `id`, `room_id`, `guest_name`, `guest_email`, `check_in`, `check_out`, `guests`, `total_price`, `status` (`CONFIRMED` | `CANCELLED`), `created_at`.

Capacity by type: SINGLE = 1, DOUBLE = 2, SUITE = 4.

## 4. Business Rules

### 4.1 Dates and stay length
- **BR-1** Dates are `YYYY-MM-DD`. `check_out` must be strictly after `check_in`.
- **BR-2** `check_in` cannot be in the past (today is allowed).
- **BR-3** Minimum stay is 1 night, maximum stay is 30 nights.
- **BR-4** Number of nights = `check_out - check_in` in days.

### 4.2 Availability
- **BR-5** A stay occupies the half-open interval `[check_in, check_out)`.
- **BR-6** Two bookings on the same room **overlap** if their intervals intersect. Cancelled bookings never block a room.
- **BR-7** Back-to-back stays are allowed: a booking may start on the same day another one on the same room ends.
- **BR-8** `guests` must be between 1 and the room's capacity.

### 4.3 Pricing (per night, then summed)
- **BR-9** Night price = `base_price` x season multiplier x weekend multiplier.
- **BR-10** **High season** (nights from 15 June to 15 September inclusive): x1.5. Otherwise x1.0.
- **BR-11** **Weekend** (nights starting on Friday or Saturday): x1.2. Multipliers stack (high season weekend = x1.8).
- **BR-12** The season and weekday are determined by the **night's date**, so a stay can cross seasons (e.g. 13-18 June is priced night by night).
- **BR-13** **Long-stay discount** on the subtotal: 7-13 nights = 10%, 14 or more nights = 15%.
- **BR-14** Prices are rounded to 2 decimals (round half up) **only on the final total**.

### 4.4 Cancellation and refund
- **BR-15** Only `CONFIRMED` bookings can be cancelled. Cancelling twice is an error.
- **BR-16** Refund depends on days between cancellation date and `check_in`:
  - 7 days or more: 100% refund
  - 2 to 6 days: 50% refund
  - fewer than 2 days: 0% refund
- **BR-17** A booking cannot be cancelled once `check_in` has passed (the date is before today).
- **BR-18** Refund is computed from `total_price` (after discount).

## 5. Core Features

1. Manage rooms (create, list, get)
2. Search available rooms for a date range and guest count
3. Create a booking
4. Get booking details with price breakdown
5. Cancel a booking and receive the refund amount
6. List bookings (filter by room and/or status)

*Stretch (only if time allows):* modify booking dates; guest booking history by email.

## 6. User Stories and Acceptance Criteria

### US-1: Manage rooms
*As a hotel manager, I want to add rooms so that guests can book them.*

- **AC-1.1** `POST /rooms` with valid data returns `201` and the created room.
- **AC-1.2** Duplicate room `number` returns `409`.
- **AC-1.3** `base_price` <= 0 or unknown `type` returns `422`.
- **AC-1.4** `GET /rooms` returns all rooms; `GET /rooms/{id}` returns `404` if not found.

### US-2: Search availability
*As a guest, I want to see which rooms are free on my dates so that I can choose one.*

- **AC-2.1** `GET /rooms/available?check_in=&check_out=&guests=` returns only rooms free for the whole interval and with capacity >= `guests`.
- **AC-2.2** A room with a `CONFIRMED` booking overlapping the range is excluded (BR-6).
- **AC-2.3** A room whose only overlapping booking is `CANCELLED` is included.
- **AC-2.4** A room whose booking ends on `check_in` of the search is included (BR-7).
- **AC-2.5** Invalid dates follow BR-1 to BR-3 and return `422`.

### US-3: Create a booking
*As a guest, I want to book a room so that it is reserved for me.*

- **AC-3.1** `POST /bookings` with valid data returns `201`, status `CONFIRMED`, and the computed `total_price`.
- **AC-3.2** Booking an unavailable room returns `409`.
- **AC-3.3** Booking a non-existing room returns `404`.
- **AC-3.4** `guests` greater than capacity or less than 1 returns `422`.
- **AC-3.5** Invalid email format or empty guest name returns `422`.
- **AC-3.6** Date violations (BR-1 to BR-3) return `422`.
- **AC-3.7** Two simultaneous requests for the same room and dates must not both succeed.

### US-4: Price calculation
*As a guest, I want a correct and transparent price so that I know what I pay.*

- **AC-4.1** A 1-night weekday stay in low season costs exactly `base_price`.
- **AC-4.2** A Friday or Saturday night costs `base_price x 1.2`.
- **AC-4.3** A night in high season costs `base_price x 1.5`; a weekend night in high season costs `base_price x 1.8`.
- **AC-4.4** A stay crossing a season boundary (e.g. 14-17 June) is priced night by night.
- **AC-4.5** 7 nights get 10% off the subtotal; 6 nights get none; 14 nights get 15%.
- **AC-4.6** `GET /bookings/{id}` returns a breakdown: nightly prices, subtotal, discount, total.
- **AC-4.7** Rounding is applied only to the final total (BR-14).

### US-5: Cancel a booking
*As a guest, I want to cancel and know how much I get back.*

- **AC-5.1** `POST /bookings/{id}/cancel` on a `CONFIRMED` booking returns `200`, status `CANCELLED`, and `refund_amount`.
- **AC-5.2** Refund percentage follows BR-16 exactly at the boundaries (7 days, 6 days, 2 days, 1 day, 0 days).
- **AC-5.3** Cancelling an already cancelled booking returns `409`.
- **AC-5.4** Cancelling a booking whose `check_in` is in the past returns `409` (BR-17).
- **AC-5.5** After cancellation, the room becomes available again for those dates.
- **AC-5.6** Unknown booking id returns `404`.

### US-6: List bookings
*As a hotel manager, I want to list bookings so that I can monitor occupancy.*

- **AC-6.1** `GET /bookings` returns all bookings.
- **AC-6.2** Filters `room_id` and `status` work alone and combined.
- **AC-6.3** An invalid `status` value returns `422`.

## 7. API Summary

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/rooms` | Create room |
| GET | `/rooms` | List rooms |
| GET | `/rooms/{id}` | Get room |
| GET | `/rooms/available` | Search availability |
| POST | `/bookings` | Create booking |
| GET | `/bookings` | List bookings (filters) |
| GET | `/bookings/{id}` | Booking details + price breakdown |
| POST | `/bookings/{id}/cancel` | Cancel booking |

Error format: `{"detail": "<message>"}` with standard HTTP codes (`404` not found, `409` conflict, `422` validation).

## 8. Out of Scope
Authentication, payments, a frontend UI, multi-hotel support, time zones (all dates are treated as local calendar dates).

## 9. Testing Notes (for Testers)
Focus areas where bugs are most likely: date boundaries (leap years, month/year end), overlap logic (BR-5 to BR-7), season-crossing stays, discount thresholds (6/7/13/14 nights), refund thresholds, rounding, and concurrent bookings. Each test case should reference the AC or BR it verifies.

## 10. Repository Structure (proposed)

```
hotel-booking/
├── app/
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── pricing.py
│   ├── availability.py
│   └── routes/
├── tests/
│   ├── unit/
│   └── api/
├── docs/
│   ├── ai_log_dev.md
│   ├── ai_log_test.md
│   └── test_plan.md
├── SPEC.md
├── requirements.txt
└── README.md
```
