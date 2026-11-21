# Notes for the Final Report (AI strengths and weaknesses)

Fill this in WHILE you work, with real examples. The report grade depends on concrete evidence.

## Development: where did the AI struggle?
- [ ] Example 1 (prompt, what it generated, what was wrong, how we fixed it)
- [ ] Did it forget any SPEC requirement? Which?
- [ ] Anything inefficient? (e.g. O(n) scan of all bookings for each availability check)
- [ ] Design choices we disagreed with (in-memory store, float in JSON for money)

## Testing: where did the AI struggle?
- [ ] Wrong expected values in tests? (verify prices by hand!)
- [ ] Missed edge cases that a human added
- [ ] Tests that only mirror the implementation
- [ ] Flaky tests (concurrency)
- [ ] Did the AI find any non-obvious bug?

## Candidate things to investigate (honest leads)
1. Money is returned as JSON `float`. Check values like 0.1+0.2 style drift on large stays.
2. Availability search scans every booking (performance with many bookings).
3. Data is lost on restart (in-memory).
4. Concurrency is only safe because of a process-wide lock; test with multiple uvicorn workers (`--workers 2`): the lock no longer protects across processes.
5. Spec gaps the AI silently filled: is Sunday a weekend night? Is the refund based on calendar days or hours? Time zones?
