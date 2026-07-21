EXP-016 RATE-LIMIT AMENDMENT A1
===============================

Observed state:
- five fixed samples completed;
- the sixth fixed sample received HTTP 429;
- the original failed lock is preserved;
- the API key is absent;
- Git is clean;
- no local data audit has run.

This package adds one narrowly controlled retry mode:

    --retry-rate-limited-window

It does not access the vendor when extracted or tested.
It does not set or read the API key during tests.
It does not modify the original request locks or raw files.
It does not change sample windows, measurements or qualification gates.
It does not run a strategy.

Test, commit and push this amendment before using the retry mode.
Do not run --download-samples again.
