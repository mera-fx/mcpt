# EXP-027 Preregistration

**Experiment:** EXP-027

**Title:** Protected 2026 Databento NQ Multi-Strategy Measurement

**Locked date:** 2026-07-28

**Status:** `PRE_REGISTERED`

**Preregistration SHA-256:** `3177e5bb81bbf330b8a020c3bfee56b584cd284da3546fcdad4b90df5ffd76bd`

## Purpose

EXP-027 measures the unchanged EXP-026 strategy population on the untouched
2026 section of the frozen EXP-022 Databento-derived NQ continuous series.

This is a measurement experiment. It is not an optimisation tournament and it
does not search for one winner.

## Protected period

| Field | Locked value |
|---|---|
| Session start | 2026-01-01 |
| Session end | 2026-07-23 |
| Primary representation | Backward adjusted |
| Sensitivity representation | Unadjusted |
| Databento API calls | 0 |
| New download | No |

No 2026 market value or strategy result was viewed before this preregistration.

Only 2026 session rows may be deserialised under EXP-027. Historical 2010-2025
market rows remain outside the EXP-027 execution scope. Frozen EXP-026 aggregate
reports may be read for descriptive context.

## Candidate population

EXP-027 reports all 24 fixed rows:

- 22 unchanged EXP-026 strategy variants;
- two unchanged ORB controls.

No candidate can be added, removed, tuned, reselected or promoted after 2026 is
viewed.

### Primary confirmation cohort

These three candidates were selected before protected 2026 access:

1. `gap_fade_0p75_1r`
2. `opening_drive_0p75_time`
3. `premarket_continuation_0p875_1p5r`

They are labelled as the primary cohort, not ranked as a single winner.

### Secondary measurement cohort

The other 19 fixed strategy variants remain visible as separate evidence rows.
They provide comparison and family-shape context, but EXP-027 cannot promote one
of them into the primary cohort based on its 2026 result.

### Fixed controls

1. `orb_control_exp005_15m_both_time`
2. `orb_control_exp007_30m_long_1r`

Controls remain comparison rows and cannot become selected strategies.

## Rules and costs

Every signal, entry, stop, target, time exit and eligibility rule remains
unchanged from EXP-026.

| Item | Locked value |
|---|---:|
| Market | NQ |
| Position | One contract |
| Point value | $20 |
| Tick size | 0.25 points |
| Tick value | $5 |
| Fee | $2.50 per side |
| Base slippage | One tick per side |
| Base round-trip cost | $15 |
| Cost sensitivity | Zero through three ticks per side |
| Same-minute stop/target | Stop first, conservative |

No position-size or portfolio-weight optimisation is allowed.

## Measurements

Each candidate and control must report:

- all-trade, long-trade and short-trade metrics;
- net profit, Profit Factor, trade count and win rate;
- average and median trade;
- maximum drawdown and recovery information;
- monthly results;
- cost sensitivity;
- backward-adjusted versus unadjusted sensitivity;
- trade distribution and concentration;
- entry-time and exit-reason distributions.

Sample-size bands are descriptive only. They are not pass/fail gates.

## Canonical evidence requirement

Unlike EXP-026, EXP-027 must preserve reusable evidence for every one of the 24
rows:

```text
series/<candidate_id>/trades.csv
series/<candidate_id>/equity.csv
series/<candidate_id>/comparison_timeseries.csv
series/<candidate_id>/metrics.csv
```

A zero-trade candidate still requires a header-only trade ledger and a flat
equity series. This allows future dashboard and analytics views without
reconstructing or rerunning EXP-027.

## Interpretation boundary

EXP-027 may show continuity, degradation, divergence, cost fragility or an
insufficient sample.

It may not:

- declare one universal best strategy;
- optimise or reselect after viewing 2026;
- promote a secondary candidate into the primary cohort;
- automatically prove an edge;
- automatically prove strategy failure;
- authorise paper trading;
- authorise live trading or capital deployment.

## Execution boundary

Preregistration does not authorise execution.

The next step is a result-free implementation and preflight. Protected 2026 may
only be opened after that implementation is committed and a separate one-time
execution authorisation is committed.
