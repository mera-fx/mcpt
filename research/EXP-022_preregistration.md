# EXP-022 Preregistration

**Locked date:** 2026-07-26

**Status:** `PRE_REGISTERED`

**Implementation:** `NOT_IMPLEMENTED`

**Execution:** `NOT_RUN`

## Title

NQ Selected Volume-Roll Continuous-Series Construction

## Frozen selection

EXP-021 is closed and frozen at commit:

`253ef695bae819102ec75c3e0cadfa99c8f78d3f`

The selected operational rule is `VOL_GT_OUT_2S_E3`. EXP-022 does not repeat
the candidate comparison or recalculate roll dates. It consumes the 65 frozen
effective roll dates from EXP-021.

| Locked property | Value |
|---|---:|
| Source contracts | 66 |
| Source records | 6,276,486 |
| Adjacent transitions | 65 |
| Volume-driven transitions | 40 |
| Calendar fallbacks | 25 |
| Provider-warning fallbacks | 23 |
| Clean fallbacks | 2 |
| Databento API calls | 0 |

## Construction objective

Construct exactly two representations of one selected roll schedule:

1. `selected_roll_unadjusted.parquet`
2. `selected_roll_backward_adjusted.parquet`

This is one roll schedule with adjusted and unadjusted representations, not
two independently selected schedules.

## Stitching

For every frozen effective roll trading date:

- use the outgoing contract before that trading date;
- use the incoming contract on and after that trading date;
- do not roll intraday;
- do not fill missing minutes or create synthetic bars;
- preserve source OHLCV in the unadjusted series.

## Backward adjustment

For each adjacent pair, use the latest timestamp present in both contracts
strictly before the effective roll-session boundary.

The roll difference is:

`incoming close - outgoing close`

Apply cumulative differences to all earlier open, high, low and close values.
Do not adjust volume, instrument ID, source contract, roll method or trading
date.

## Outputs

- `roll_ledger.csv`
- `contract_contribution.csv`
- `selected_roll_unadjusted.parquet`
- `selected_roll_backward_adjusted.parquet`
- `construction_summary.json`
- `output_hashes.json`
- `report.md`
- `CONSTRUCTION_COMPLETE.json`

## Qualification boundary

All 20 hard checks and the independent rebuild must pass. Successful
construction qualifies a dataset only. It does not test strategy edge or
authorise strategy use, optimisation, MCPT, paper trading or live trading.

EXP-019, EXP-020 and EXP-021 remain frozen and may not be rerun.
