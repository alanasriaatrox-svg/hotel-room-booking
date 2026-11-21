# Test Plan: Hotel Room Booking API

**Version:** 1.0  **Testers:** *(names)*  **Developers:** *(names)*
**Reference:** [SPEC.md](../SPEC.md) (business rules BR-x, acceptance criteria AC-x.y)

## 1. Objectives
- Verify that the API behaves as specified for every acceptance criterion.
- Find defects in date handling, overlap detection, pricing, refunds and concurrency.
- Evaluate how well an AI assistant can generate test ideas, data and automation (core goal of the assignment).

## 2. Scope
**In scope:** rooms, availability search, booking creation, price calculation, cancellation/refund, booking listing, input validation, error codes.
**Out of scope:** authentication, payments, UI, performance/load testing, persistence (in-memory store), time zones.

## 3. Test Approach
| Level | Technique | Tooling | Location |
|---|---|---|---|
| Unit | Boundary value analysis, equivalence partitioning, decision tables (pricing/refund) | pytest, parametrize | `tests/unit/` |
| API (integration) | Black-box against the spec, negative testing, state-based testing (booking lifecycle) | pytest + FastAPI TestClient | `tests/api/` |
| Concurrency | 20 parallel requests for the same room/dates | ThreadPoolExecutor | `tests/api/test_bookings_api.py` |
| Manual / exploratory | Swagger UI at `/docs`, odd inputs, long strings, unicode names, huge ids | Browser | session notes below |

**Time control:** `app.clock.today()` is frozen to **2027-01-10 (Sunday)** in tests so refunds and "no past dates" are deterministic.

**Principles**
1. Tests are derived from the **SPEC**, not from the implementation. A mismatch is a bug in the code (or an ambiguity in the spec to be raised).
2. Every test references the BR/AC it verifies.
3. Boundaries are tested on both sides (6/7/13/14 nights, 1/2/6/7 days, 15 June / 15 Sept, 30/31 nights).

## 4. Test Design Techniques and Key Boundaries
| Area | Rules | Boundary values tested |
|---|---|---|
| Stay length | BR-1..4 | 0, 1, 30, 31 nights; checkout before/equal to checkin |
| Past dates | BR-2 | yesterday (reject), today (accept) |
| Overlap | BR-5..7 | identical, partial (both sides), contained, containing, back-to-back (both sides), gap |
| Capacity | BR-8 | 0, 1, capacity, capacity+1 for each room type |
| Season | BR-10 | 14 Jun, 15 Jun, 15 Sep, 16 Sep |
| Weekend | BR-11 | Thu, Fri, Sat, Sun; stacking with high season (x1.8) |
| Discount | BR-13 | 6, 7, 13, 14 nights |
| Rounding | BR-14 | half-up (x.xx5), rounding only on final total |
| Refund | BR-16..18 | 7, 6, 2, 1, 0 days; after check-in; already cancelled |
| Calendar | | leap year (28 Feb 2028), year-end crossing, impossible dates (30 Feb) |
| Concurrency | AC-3.7 | 20 simultaneous identical bookings: exactly 1 succeeds |

## 5. Entry / Exit Criteria
- **Entry:** developers deliver a runnable build on `main`; `pytest` smoke tests pass.
- **Exit:** all AC covered by at least one automated or manual test; no open Critical/High bugs; line coverage >= 90%; all bug reports closed or accepted.

## 6. Environment and Resources
Python 3.11+, FastAPI, pytest, pytest-cov, httpx; GitHub repo; Discord for bug triage. AI assistant: *(fill in model + tool)*.

## 7. Schedule
| Week | Activity |
|---|---|
| 1 | Test plan, test case design, AI-assisted test idea generation |
| 2 | Automation of unit + API tests, first execution against dev build |
| 3 | Bug reporting, retest, regression, exploratory session, report writing |

## 8. Risks
| Risk | Mitigation |
|---|---|
| Spec ambiguity (e.g. is Sunday a weekend night?) | Raise as spec question, record decision in SPEC.md |
| AI-generated tests copy implementation behaviour | Derive expected values by hand from the spec (see worked examples in tests) |
| In-memory storage loses data on restart | Out of scope; documented limitation |
| Flaky concurrency test | Run it repeatedly (`pytest --count`, or a loop) |

## 9. Bug Reporting
Use `docs/bug_reports.md`. Severity: Critical (wrong money/double booking), High (wrong status code or rule), Medium (validation gap), Low (cosmetic/message).

## 10. Traceability Matrix
| Requirement | Tests |
|---|---|
| AC-1.1..1.4 | `tests/api/test_rooms_api.py` |
| AC-2.1..2.5 | `tests/api/test_availability_api.py` |
| AC-3.1..3.7 | `tests/api/test_bookings_api.py` (overlap, capacity, payload validation, concurrency) |
| AC-4.1..4.7 | `tests/unit/test_pricing.py`, breakdown tests in `test_bookings_api.py` |
| AC-5.1..5.6 | `tests/api/test_cancellation_api.py`, `tests/unit/test_availability_and_rules.py` (refund tiers) |
| AC-6.1..6.3 | `test_bookings_api.py` (listing/filters) |
| BR-1..3 | `test_availability_and_rules.py::TestDateValidation`, API payload tests |
| BR-5..7 | `test_availability_and_rules.py::test_overlaps`, API overlap tests |

## 11. Execution Results (fill in after each run)
| Date | Build/commit | Tests run | Passed | Failed | Coverage | Notes |
|---|---|---|---|---|---|---|
| | | 138 | 138 | 0 | 99% | Initial run on first build |

### Mutation sanity check (do the tests really detect bugs?)
We injected three deliberate faults and confirmed the suite fails: refund threshold `>= 7` changed to `> 7` (2 tests failed); overlap check changed to inclusive (6 failed); high season start moved to 16 June (2 failed). All were reverted.

## 12. Exploratory Testing Sessions (manual)
Charter ideas to run in Swagger UI (`/docs`) and record findings:
1. Unicode / very long guest names and emails.
2. Extremely large `room_id`, negative ids, float ids.
3. Booking far in the future (year 9999), `base_price` with many decimals (e.g. 99.999).
4. Create booking, restart server, check data (persistence limitation).
5. Send JSON with extra/unknown fields, wrong content-type, empty body.
