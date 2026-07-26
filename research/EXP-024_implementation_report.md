# EXP-024 Result-Free Implementation Report

**Implemented:** 2026-07-26

**Research status:** `PRE_REGISTERED`

**Implementation status:** `IMPLEMENTED`

**Execution status:** `NOT_AUTHORIZED_NOT_RUN`

## Outcome

EXP-024 now has a result-free, protected implementation for attributing the
51 frozen EXP-023 candidate-session decision mismatches.

This implementation commit does not calculate or reveal any attribution
result. It does not create `results/EXP-024`, read market values during its
preflight, rerun EXP-023, or authorize execution.

## Implemented files

- `exp024_attribution_core.py` contains the frozen candidate rules,
  source-neutral entry-feature reconstruction, deterministic attribution
  mapping, raw price-difference calculations, Quantower one-to-five-minute
  aggregation comparison, and final classification logic.
- `exp024_attribution.py` contains frozen-evidence verification, the protected
  Parquet scanner, result-free and authorized preflights, the separately gated
  one-time runner, independent rebuild checking, atomic output publication,
  charts, and reports.
- `tests/test_exp024_attribution.py` exercises the feature formulas,
  attribution boundaries, exact 51-row selector, Arrow filtering and
  projection, aggregation comparison, absent authorization gate, and
  result-directory guard.

## Protected market-data boundary

All value-level Parquet access is centralized in
`scan_parquet_intervals`. It attaches the UTC row predicate and explicit
column projection to the Arrow scanner before converting a table to pandas.

The only permitted projections are:

- current mismatch sessions, 08:00 through 09:34 New York: OHLC;
- current mismatch sessions, 09:35: open only;
- immediately prior frozen reference sessions needed by gap fade, 09:30
  through 15:59: OHLC.

Volume, later current-session values, non-mismatch sessions, pre-2020 values,
and 2026 values are not projected. Full-file byte hashes and Parquet
metadata/schema checks remain permitted and occur without materializing
market values.

Frozen Quantower session-quality evidence and frozen EXP-023 transfer
eligibility are used for the eligibility component. Re-reading the full cash
session merely to reconstruct completeness would violate the locked
post-entry boundary.

## Decision-only reconstruction

The implementation reconstructs:

- eligibility;
- normalized gap or premarket movement and threshold margin;
- context direction;
- first 09:30 five-minute bar direction and confirmation;
- the 09:35 open, entry risk, and positive-risk validity;
- the final setup-pass decision.

It contains no trade-exit simulation, target evaluation, P&L, return, equity,
drawdown, ranking, optimization, MCPT, bootstrap, walk-forward, paper-trading,
or live-trading path.

Each candidate-session is mapped mechanically to exactly one preregistered
category. Roll distance, calendar fallback, and provider-warning fields are
reported only as descriptive context and cannot alter the category.

## Result-free preflight

After this four-file implementation commit is pushed to synchronized `main`,
the protected preflight is:

```powershell
.venv\Scripts\python.exe exp024_attribution.py --preflight
```

It requires:

- a clean `main` branch synchronized with `origin/main`;
- the locked EXP-024 preregistration as an ancestor and unchanged;
- exactly the four implementation files in the implementation commit;
- all frozen byte hashes, closure identities, Parquet row counts, and schemas
  to match;
- the exact 51-row mismatch selector and frozen candidate counts;
- both final and partial EXP-024 result directories to be absent;
- `DATABENTO_API_KEY` to be unset;
- the separate authorization file to be absent.

Its successful status is
`IMPLEMENTED_NOT_AUTHORIZED_NOT_RUN`. It performs no attribution and
materializes no market values.

## Separate execution gate

`--run` remains blocked until a later commit adds exactly:

- `exp024_attribution_authorization.py`;
- `research/EXP-024_attribution_authorization.md`;
- `tests/test_exp024_attribution_authorization.py`.

That record must lock this implementation commit and explicitly authorize one
attribution run while keeping protected dates, current post-entry values,
strategy replay, network access, optimization, and trading disabled.

The internal independent rebuild is part of that single authorized diagnostic
run. A completed output directory permanently blocks rerun.
