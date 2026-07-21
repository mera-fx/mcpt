EXP-016 PROTECTED IMPLEMENTATION
================================

This package implements the protected six-window NQ.F sample audit.

It does not access London Strategic Edge when extracted or tested.
It does not set or read an API key during tests.
It does not rerun the catalog.
It does not download data automatically.
It does not run a strategy.

Files:

- exp016_implementation.py
- exp016_lse_history_worker.py
- exp016_measurements.py
- run_exp016_audit.py
- research/EXP-016_implementation.md
- tests/test_exp016_implementation.py
- tests/test_exp016_measurements.py
- tests/test_exp016_runner_boundary.py

After extraction, run the focused and full framework tests. Commit and
push the implementation before running --preflight.

Do not set LSE_API_KEY or run --download-samples yet.
