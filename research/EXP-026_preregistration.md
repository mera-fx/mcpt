# EXP-026 Preregistration

**Experiment:** EXP-026

**Title:** Databento-Native NQ Multi-Family Strategy Development Tournament

**Locked date:** 2026-07-27

**Status:** `PRE_REGISTERED`

**Preregistration SHA-256:** `bbd2e6d8bb50c135d0c6ca04873eed2876c4e7db6a2714b91a934dcf554331a0`

## Purpose

EXP-026 develops and compares a bounded set of NQ intraday strategies using
only the frozen EXP-022 Databento-derived continuous series.

The experiment is exploratory and measurement-first. It does not treat the
known 2020-2025 results as independent evidence and it does not authorise paper
or live trading.

## Frozen data

Primary research representation:

`selected_roll_backward_adjusted.parquet`

Secondary post-selection audit representation:

`selected_roll_unadjusted.parquet`

Both representations contain 5,457,606 rows and use the frozen
`VOL_GT_OUT_2S_E3` roll schedule.

No Databento API call or new download is authorised.

## Research sequence

| Phase | Period | Candidate access | Selection |
|---|---|---|---|
| Phase A | 2010-06-07 through 2017-12-31 | 22 candidates + 2 controls | Up to 2 per family |
| Phase B | 2018-01-01 through 2019-12-31 | Phase-A survivors + controls | Up to 1 per family |
| Phase C | 2020-01-03 through 2025-12-31 | Frozen finalists + controls | No reselection |
| EXP-027 | 2026-01-01 through 2026-07-23 | Prohibited in EXP-026 | Separate preregistration |

Each phase requires its own authorisation and completion commit. A later phase
cannot be accessed before the preceding selection record is frozen.

## Development candidates

| Candidate | Family | Threshold | Exit | Selectable |
|---|---|---:|---|---|
| gap_fade_0p25_prior_close | gap_fade | 0.25 | prior_cash_close_or_time | Yes |
| gap_fade_0p25_1r | gap_fade | 0.25 | 1r_or_time | Yes |
| gap_fade_0p50_prior_close | gap_fade | 0.5 | prior_cash_close_or_time | Yes |
| gap_fade_0p50_1r | gap_fade | 0.5 | 1r_or_time | Yes |
| gap_fade_0p75_prior_close | gap_fade | 0.75 | prior_cash_close_or_time | Yes |
| gap_fade_0p75_1r | gap_fade | 0.75 | 1r_or_time | Yes |
| premarket_continuation_0p50_time | premarket_momentum_continuation | 0.5 | time | Yes |
| premarket_continuation_0p50_1p5r | premarket_momentum_continuation | 0.5 | 1p5r_or_time | Yes |
| premarket_continuation_0p625_time | premarket_momentum_continuation | 0.625 | time | Yes |
| premarket_continuation_0p625_1p5r | premarket_momentum_continuation | 0.625 | 1p5r_or_time | Yes |
| premarket_continuation_0p75_time | premarket_momentum_continuation | 0.75 | time | Yes |
| premarket_continuation_0p75_1p5r | premarket_momentum_continuation | 0.75 | 1p5r_or_time | Yes |
| premarket_continuation_0p875_time | premarket_momentum_continuation | 0.875 | time | Yes |
| premarket_continuation_0p875_1p5r | premarket_momentum_continuation | 0.875 | 1p5r_or_time | Yes |
| opening_drive_0p25_time | opening_drive_continuation | 0.25 | time | Yes |
| opening_drive_0p25_1p5r | opening_drive_continuation | 0.25 | 1p5r_or_time | Yes |
| opening_drive_0p50_time | opening_drive_continuation | 0.5 | time | Yes |
| opening_drive_0p50_1p5r | opening_drive_continuation | 0.5 | 1p5r_or_time | Yes |
| opening_drive_0p75_time | opening_drive_continuation | 0.75 | time | Yes |
| opening_drive_0p75_1p5r | opening_drive_continuation | 0.75 | 1p5r_or_time | Yes |
| opening_drive_1p00_time | opening_drive_continuation | 1.0 | time | Yes |
| opening_drive_1p00_1p5r | opening_drive_continuation | 1.0 | 1p5r_or_time | Yes |

## Fixed controls

| Candidate | Family | Threshold | Exit | Selectable |
|---|---|---:|---|---|
| orb_control_exp005_15m_both_time | opening_range_breakout_control | Fixed | 15:55_time | No |
| orb_control_exp007_30m_long_1r | opening_range_breakout_control | Fixed | 1r_or_14:00_time | No |

The controls are reported for comparison but cannot participate in candidate
selection.

## Selection method

Phase A uses a fixed lexicographic rank:

1. Trade Profit Factor
2. Net profit divided by maximum drawdown
3. Net profit
4. Completed trades
5. Candidate ID

Up to two candidates per family continue to Phase B.

Phase B uses:

1. Profitable internal-validation years
2. Internal-validation Profit Factor
3. Internal-validation net-profit-to-drawdown
4. Internal-validation net profit
5. Development Profit Factor
6. Candidate ID

Up to one candidate per family becomes an EXP-026 finalist.

There is no minimum-profit gate and no weighted composite score. A candidate
must produce at least one completed trade in the relevant phase to be
selectable.

## Robustness

EXP-026 requires:

- 1,000 selection-aware market permutations;
- 10,000 session-block bootstrap resamples;
- anchored yearly walk-forward measurement from 2014 through 2019;
- zero-, one-, two- and three-tick slippage sensitivity;
- threshold-neighbour and exit-mode-neighbour stability;
- backward-adjusted versus unadjusted representation sensitivity after
  finalist selection.

These measurements provide context. They are not automatic pass/fail gates.

## Reporting

The report must use a vertical full-width layout:

1. Strategy rules and candidate grid
2. All / Long / Short metric table
3. Full-width equity curves
4. Full-width drawdown curves
5. Annual results
6. Monthly results
7. Trade distributions and concentration
8. Cost sensitivity
9. Parameter stability
10. Walk-forward results
11. Bootstrap intervals
12. Selection-aware MCPT
13. Known 2020-2025 comparison
14. Protected 2026 boundary

All candidates remain visible even when they are not selected.

## Interpretation boundary

EXP-026 may identify measurement leaders and measured trade-offs.

It cannot establish independent confirmation because the family concepts and
2020-2025 evidence are already known.

Only a separately preregistered EXP-027 may access the protected 2026 period.

EXP-026 does not authorise paper trading, live trading, order access or capital
deployment.
