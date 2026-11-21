# Hotel Room Booking API

FastAPI backend for room search, booking, price calculation and cancellation.
Full requirements: see [SPEC.md](SPEC.md).

## Run
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Interactive docs: http://127.0.0.1:8000/docs

## Test
```bash
pytest --cov=app --cov-report=term-missing
```

## Layout
- `app/pricing.py` - seasonal/weekend pricing, discount (BR-9..14)
- `app/availability.py` - overlap logic (BR-5..7)
- `app/validation.py` - date rules (BR-1..3)
- `app/routes/` - HTTP endpoints
- `app/clock.py` - `today()` wrapper so tests can freeze time
- `docs/` - AI interaction logs and test plan

## Documentation
- [SPEC.md](SPEC.md) - requirements
- [docs/test_plan.md](docs/test_plan.md) - test plan and traceability
- [docs/bug_reports.md](docs/bug_reports.md) - defect log
- [docs/ai_log_dev.md](docs/ai_log_dev.md), [docs/ai_log_test.md](docs/ai_log_test.md) - AI interaction logs
- [docs/ai_findings_notes.md](docs/ai_findings_notes.md) - evidence for the final report
