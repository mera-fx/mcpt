# EXP-026 Phase C Execution Authorisation

**Experiment:** EXP-026

**Phase:** C — Known 2020–2025 Comparison

**Authorised date:** 2026-07-28

**Status:** `AUTHORIZED`

**Locked implementation commit:** `13ee0683dfcbbb5d763f7254f3b245ecc8e6d9cd`

**Phase B completion commit:** `da8456d254dc710336806ad5940afcec649be016`

**Authorisation SHA-256:** `7b3e59989061ac9f907d8e6ff749fedc6b40a71a4e03ab1b5ff045096c63b4ce`

## Authorised execution

One Phase C known-comparison run is authorised using the frozen Phase B
finalists and two unchanged controls.

Both frozen EXP-022 representations may be materialised only from:

`2019-12-01` through `2025-12-31`

The reported known-comparison period is:

`2020-01-03` through `2025-12-31`

The December 2019 source overlap is authorised only for prior-session context
needed by the fixed strategy rules.

## Frozen finalists

- `gap_fade_0p75_1r`
- `opening_drive_0p75_time`
- `premarket_continuation_0p875_1p5r`

## Fixed controls

- `orb_control_exp005_15m_both_time`
- `orb_control_exp007_30m_long_1r`

No candidate may be added, removed, reselected or reparameterised. Finalist
identity cannot change as a result of the 2020–2025 measurements.

## Representation boundary

- `BACKWARD_ADJUSTED` is the primary representation.
- `UNADJUSTED` is a post-selection sensitivity only.
- Both inputs remain read-only.
- The unadjusted result cannot alter finalist identity.
- Roll-rule or adjustment-method changes are not authorised.

## Measurements

The run reports all/long/short metrics, annual and monthly results, costs at
0–3 ticks of slippage per side, representation sensitivity, trade
distribution, drawdown episodes, full-width equity curves and drawdown curves.

## Required outputs

- `known_comparison_summary.json`
- `known_comparison_metrics.csv`
- `annual_results.csv`
- `monthly_results.csv`
- `cost_sensitivity.csv`
- `representation_sensitivity.csv`
- `trade_distribution.csv`
- `drawdown_episodes.csv`
- `output_hashes.json`
- `report.md`
- `report.html`
- `PHASE_C_COMPLETE.json`

## Interpretation

The 2020–2025 period is already known historical information and is not
independent confirmation. Phase C finalists remain measurement leaders rather
than confirmed trading edges.

## Explicitly not authorised

- protected 2026 access or calculation;
- EXP-027 execution;
- candidate reselection or parameter changes;
- position-size or portfolio-weight optimisation;
- new Databento downloads or API calls;
- network or order access;
- paper or live trading.
