# EXP-010 — Opening-Drive Deep Validation Result

## Status

EXP-010 is complete and preserved in **REVIEW** with the secondary
classification **STRONG_HISTORICAL_EVIDENCE**.

This is measurement-first historical research. It is not independent
confirmation: the opening-drive family was selected after viewing the
six-family EXP-009 tournament, and the 2019–2025 data had already been
examined. No paper or live trading is authorized automatically.

## What was tested

- Four opening-drive candidates locked from EXP-009
- 1,639 frozen NQ and MNQ sessions from 2019-05-06 to 2025-12-31
- Fixed one-contract exposure and the common execution/cost model
- Five anchored annual walk-forward folds covering 2021–2025
- Zero-, one- and two-tick cost measurements
- 10,000-resample trade bootstraps for the measurement leader and user
  reference
- 1,000 session-aware permutations, with all four candidates reselected
  inside every permutation

## Main measurement

The measurement leader was `opening_drive_0p5_time`:

- NQ Profit Factor: **1.350073**
- NQ net profit: **$213,905**
- Completed trades: **775**
- Win rate: **49.29%**
- Average trade: **$276.01**
- Maximum drawdown: **-$25,280**
- Net profit / maximum drawdown: **8.46**
- MNQ Profit Factor: **1.332155**
- Two-tick NQ net profit: **$206,155**
- Profitable years: **6 of 7**

The user-preferred `opening_drive_0p5_1p5r` remains a distinct reference:

- NQ Profit Factor: **1.315847**
- NQ net profit: **$187,850**
- Completed trades: **775**
- Win rate: **52.00%**
- Maximum drawdown: **-$24,930**
- Profitable years: **7 of 7**

## Forward-style and statistical evidence

- Profitable anchored walk-forward folds: **4 of 5**
- Combined walk-forward net profit: **$114,695**
- Selection-aware exceedances: **25 of 1,000**
- Selection-aware MCPT p-value: **0.025974**
- Fixed-reference exceedances: **0 of 1,000**
- Fixed-reference diagnostic p-value: **0.000999**

The selection-aware test corrects for choosing among the four
opening-drive candidates. It does **not** correct for selecting the
opening-drive family after seeing the earlier six-family tournament.

## Interpretation

All locked strong-evidence checks passed. The opening-drive family now
has materially stronger historical support than it had after EXP-009
alone. The correct claim is still limited to strong exploratory
historical evidence, not independent confirmation or trading approval.
