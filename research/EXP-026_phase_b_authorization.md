# EXP-026 Phase B Execution Authorisation

**Experiment:** EXP-026

**Phase:** B — Internal Validation

**Authorised date:** 2026-07-28

**Status:** `AUTHORIZED`

**Locked implementation commit:** `13ee0683dfcbbb5d763f7254f3b245ecc8e6d9cd`

**Phase A completion commit:** `28bd4209711f0c9b98a7650ab91f6408c2bdf4b7`

**Authorisation SHA-256:** `3522b27be25a3f3dced19492d1043dda69b3a134e480453f0b868e9ae310eee5`

## Authorised execution

One Phase B internal-validation run is authorised on the frozen
backward-adjusted EXP-022 series.

The loader may materialise only:

`2010-06-07` through `2019-12-31`

The finalist-selection window is only:

`2018-01-01` through `2019-12-31`

The 2010-2017 rows are permitted only for the frozen development-reference,
anchored walk-forward and selection-aware robustness calculations required by
the preregistration.

## Frozen Phase A survivors

- `gap_fade_0p75_1r`
- `gap_fade_0p25_1r`
- `opening_drive_0p75_1p5r`
- `opening_drive_0p75_time`
- `premarket_continuation_0p875_1p5r`
- `premarket_continuation_0p625_1p5r`

The two frozen ORB controls are reported but remain ineligible for selection.
At most one finalist per strategy family and at most three finalists overall
may be selected. There is no minimum-profit gate.

## Robustness measurements

- Selection-aware MCPT: 1,000 permutations, seed 26,026
- Session-block bootstrap: 10,000 resamples, seed 26,027
- Confidence level: 95%
- Anchored walk-forward test years: 2014 through 2019
- Parameter-neighbour stability: enabled
- These are context measurements, not pass/fail gates

## Runtime dependency

The existing runner uses pandas `DataFrame.to_markdown()` for `report.md`.
This authorisation therefore locks `tabulate==0.10.0` and requires a successful
markdown smoke test before execution.

## Required outputs

- `internal_validation_summary.json`
- `internal_validation_metrics.csv`
- `selected_finalists.json`
- `walk_forward_results.csv`
- `bootstrap_summary.csv`
- `mcpt_summary.json`
- `parameter_stability.csv`
- `output_hashes.json`
- `report.md`
- `report.html`
- `PHASE_B_COMPLETE.json`

## Explicitly not authorised

- 2020-2025 known-comparison access;
- Phase C execution;
- protected 2026 access;
- the unadjusted representation;
- candidate, parameter or position-sizing changes;
- new Databento downloads or API calls;
- network or order access during the run;
- paper or live trading.

Phase B finalists are internal-validation leaders only. They are not confirmed
edges and do not authorise Phase C, EXP-027, paper trading or live trading.
