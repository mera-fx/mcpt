# EXP-022 Closure

**Closed date:** 2026-07-26

**Classification:** `QUALIFIED_AS_SELECTED_VOLUME_ROLL_CONTINUOUS_SERIES`

**Closure record SHA-256:** `1cc01baddeeae3acf81b0785923b581fad6aac0b6e36071d07d0d83d35bf588d`

## Result

EXP-022 constructed the two locked representations of the
EXP-021-selected `VOL_GT_OUT_2S_E3` schedule.

| Property | Result |
|---|---:|
| Source contracts | 66 |
| Source records | 6,276,486 |
| Transitions | 65 |
| Volume-driven transitions | 40 |
| Calendar fallbacks | 25 |
| Warning fallbacks | 23 |
| Clean fallbacks | 2 |
| Rows per series | 5,457,606 |
| Representations | 2 |
| Hard checks | 20/20 |
| Databento API calls | 0 |
| Strategy runs | 0 |

## Qualified outputs

- `selected_roll_unadjusted.parquet`
- `selected_roll_backward_adjusted.parquet`

The unadjusted and backward-adjusted files are two representations of one
frozen roll schedule.

## Interpretation

The dataset construction qualified. The roll rule was selected operationally
in EXP-021, not by strategy performance. EXP-022 did not test strategy edge,
verify exchange accuracy, select a best vendor, or authorize paper/live
trading.

## Frozen boundary

EXP-022 is permanently frozen. Do not rerun its preflight or construction and
do not modify any file under:

`results/EXP-022/selected_continuous_series`

A separately preregistered EXP-023 is required before strategy research uses
either series.
