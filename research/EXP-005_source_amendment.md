# EXP-005 Source Amendment A1

**Experiment:** EXP-005  
**Amendment:** EXP-005-A1  
**Locked:** 2026-07-13  
**Status:** Locked before full quick-period export  
**Strategy results viewed:** None

## Reason

EXP-005 originally named a paid historical futures source. The
project has a strict zero-cost requirement, while the researcher
already has a Lucid Trading account with Rithmic historical data.

The source is therefore changed to:

```text
Lucid Trading / Rithmic
accessed through Quantower History Exporter
using provider-managed front-month NQ and MNQ
at zero additional data cost
```

This amendment was made after only one-day source-validation
exports and before the complete 2019–2022 quick dataset was
exported or any ORB result was calculated.

## Changed fields

| Item | Original | Amended |
|---|---|---|
| Provider | Databento | Lucid/Rithmic through Quantower |
| Symbols | NQ.v.0, MNQ.v.0 | NQ, MNQ provider front month |
| Roll statement | Volume-ranked | Provider-defined; not exposed |
| Adjustment statement | Unadjusted | Unknown/provider-defined |
| Additional data cost | Potentially paid | $0 |

## Unchanged fields

The hypothesis, fixed signal, periods, costs, MCPT, pass/fail
gates and confirmation lock are unchanged.

## One-day evidence

Both 9 August 2019 samples contained exactly 390 complete
09:30–16:00 ET one-minute bars and aggregated to 78 five-minute
bars. Neither contained missing cash minutes, duplicate
timestamps, invalid OHLC rows or tick violations.

No trades or performance statistics were calculated.

## Roll-risk treatment

The CSV does not disclose the exact historical contract mapping.
EXP-005 does not infer one.

The ORB is same-session only, and NQ/MNQ alignment is required.
A session is excluded from both datasets when the median absolute
one-minute close difference exceeds 5 points or any absolute
close difference exceeds 20 points.

Zero such sessions may be included in a valid research run.

## Protection

Only 2019-05-06 through 2022-12-30 may be exported next.
The 2023-01-03 through 2025-12-31 confirmation period remains
prohibited until every quick-transfer gate passes.
