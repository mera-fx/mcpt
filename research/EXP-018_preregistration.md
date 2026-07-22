# EXP-018 Databento Exact-Contract Structural and Repeatability Qualification

**Locked date:** 2026-07-22

**Stage:** `PRE_REGISTERED`

**OHLCV bar values viewed:** none

## Objective

Test whether Databento `GLBX.MDP3` exact-contract NQ one-minute data is
structurally valid, sufficiently complete and canonically repeatable for new
research.

This cannot prove exchange accuracy, identify the best vendor or validate
strategy performance.

## Locked requests

| Contract | Raw | ID | Start | End exclusive |
|---|---|---:|---|---|
| NQH24 | `NQH4` | 750 | 2024-02-05 | 2024-02-17 |
| NQM24 | `NQM4` | 13,743 | 2024-05-06 | 2024-05-18 |
| NQU24 | `NQU4` | 4,358 | 2024-08-05 | 2024-08-17 |
| NQZ24 | `NQZ4` | 106,364 | 2024-11-22 | 2024-12-07 |
| NQH25 | `NQH5` | 42,288,528 | 2025-03-07 | 2025-03-15 |
| NQM25 | `NQM5` | 42,005,804 | 2025-05-12 | 2025-05-24 |

Six first-pass requests are allowed. Thanksgiving and March DST are repeated
at least 24 hours later. Maximum successful bar requests: **8**.

Automatic retries are prohibited. Total cost cap: **$1.00**.

## Data handling

Use the official Databento API only. Credentials remain in
`DATABENTO_API_KEY`. Raw files remain local and gitignored.

`ts_event` is UTC and labels the inclusive start of the minute. Timestamps
may not be shifted. Databento omits minutes without trades; absent minutes
are measured but not automatically called vendor errors.

No bars may be filled, deleted, rounded, repaired or offset. Duplicates are
reported rather than silently removed. Raw and canonical SHA-256 hashes are
required.

## Measurements and gates

Measure identity, timestamps, duplicates, finite OHLCV, OHLC invariants,
negative volume, off-tick prices, regular and extended trade-minute coverage,
missing-minute runs, and separate holiday/DST behaviour.

Locked gates:

- all six initial windows;
- zero identity mismatches;
- zero duplicate timestamps and full rows;
- zero invalid OHLC, negative volume, non-finite values or off-tick OHLC;
- regular trade-minute coverage at least 99.9%;
- extended trade-minute coverage at least 99.5%;
- both repeats after at least 24 hours;
- exact repeat canonical hashes;
- total cost no more than $1.00.

Highest possible result:

`QUALIFIED_AS_ACCESSIBLE_EXACT_CONTRACT_SOURCE`

That is not an exchange-accuracy or best-vendor claim. Full history, roll
construction, strategy replay, optimization, paper trading and live trading
remain prohibited.
