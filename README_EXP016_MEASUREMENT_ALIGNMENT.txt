EXP-016 PREREGISTERED MEASUREMENT ALIGNMENT
============================================

Apply this package only after commit
a76e4ee00b07b03b6f1c6e61ed32cc1db1b16f37 and before the amended remote retry
or local audit.

The correction is based only on the locked preregistration and implementation
review. No vendor bar values or audit measurements were inspected.

It aligns three implementation details:

1. The 99.5% close-within-one-tick requirement is evaluated only on the two
   non-roll/ordinary windows:
   - 2021_thanksgiving
   - 2024_thanksgiving

2. expected_minute_completeness is explicitly recorded and independently
   checked at 99.9%. The frozen Quantower timestamp axis defines expected
   minutes, so this is matched_rows / reference_rows.

3. Exact, 0–0.25, 0.25–1.0, and over-1.0 point buckets are emitted separately
   for open, high, low, and close.

No sample window, numeric threshold, raw file, request lock, access allowance,
strategy rule, Quantower file, or trading authorization changes.
