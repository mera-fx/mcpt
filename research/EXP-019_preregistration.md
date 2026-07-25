# EXP-019 Databento NQ Maximum-History Exact-Contract Archive Planning

**Locked date:** 2026-07-25

**Stage:** `PRE_REGISTERED`

**OHLCV bar values viewed under EXP-019:** none

## Objective

Obtain an exact cost estimate for a roll-ready archive of quarterly NQ
one-minute contracts across the maximum Databento `GLBX.MDP3` history
currently selected for this project.

The cost phase cannot qualify the archive, construct a continuous series,
validate a strategy, establish exchange accuracy or identify the best vendor.

## Planning reference

A metadata-only quote for continuous symbol `NQ.v.0` from 2010-06-06 to
2026-07-24 exclusive returned **$19.940800**. No bars were downloaded.

EXP-019 will not use that continuous symbol for acquisition because its
contract selection and rollover are controlled by the vendor.

## Locked exact-contract scope

| Item | Locked value |
|---|---|
| Dataset | `GLBX.MDP3` |
| Schema | `ohlcv-1m` |
| Input symbology | `raw_symbol` |
| First contract | `NQM10` |
| Last contract | `NQU26` |
| Quarterly contracts | 66 |
| Start | 2010-06-06 |
| End exclusive | 2026-07-24 |
| Contract months | March, June, September, December |
| Transition overlap | 30 calendar days |
| Exact-contract download cap | $35.00 |

Each incoming contract begins 30 calendar days before the preceding
quarterly contract's third-Friday expiration. Completed contracts extend
through their expiration date. The final NQU26 window ends at the locked
dataset end.

This overlap is collected so that any later rollover decision can compare
the outgoing and incoming contracts directly.

## Cost-estimation phase

The first implementation may call only Databento
`metadata.get_cost` for the 66 locked contract windows.

It must:

- issue no OHLCV download;
- request no bar records;
- perform no automatic retry;
- stop on the first error;
- save every per-contract quote;
- report the summed exact-contract estimate;
- compare it with the $19.940800 continuous-symbol planning quote;
- remove the API key from the PowerShell session.

Completing the quote does not authorize acquisition.

## Acquisition boundary

The download implementation does not yet exist.

A later acquisition requires:

- a successful protected estimator;
- a total quote no greater than $35.00;
- separate explicit approval;
- a clean committed implementation;
- no automatic retries;
- raw files kept local and gitignored.

## Future archive audit

Before the archive can be used, it must pass checks covering instrument
identity, raw and canonical hashes, timestamps, duplicates, finite OHLCV,
OHLC invariants, volume, tick alignment, missing-minute runs, contract
coverage and rollover overlaps.

## Prohibited under EXP-019 cost estimation

- downloading the continuous symbol;
- constructing a continuous series;
- back-adjusting or forward-adjusting prices;
- replaying or optimizing strategies;
- paper trading;
- live trading;
- changing any frozen earlier experiment.
