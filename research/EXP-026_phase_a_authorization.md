# EXP-026 Phase A Execution Authorisation

**Experiment:** EXP-026

**Phase:** A ? Development

**Authorised date:** 2026-07-28

**Status:** `AUTHORIZED`

**Locked implementation commit:** `13ee0683dfcbbb5d763f7254f3b245ecc8e6d9cd`

**Authorisation SHA-256:** `527fdbba75095d9b987e0e64dd6410e6fa79d1bff5916049c933e4f6aa8a9dcc`

## Authorised execution

One Phase A development run is authorised on the frozen backward-adjusted
EXP-022 series.

Permitted session period:

`2010-06-07` through `2017-12-31`

The run must measure:

- 22 frozen development candidates;
- two fixed non-selectable controls;
- a maximum of two selected survivors per strategy family.

## Explicitly not authorised

- Phase B internal-validation access;
- Phase C known-comparison access;
- protected 2026 access;
- the unadjusted representation;
- candidate or parameter changes;
- new Databento downloads or API requests;
- network or order access;
- paper or live trading.

## Required outputs

- `development_summary.json`
- `candidate_registry.csv`
- `development_metrics.csv`
- `development_annual_results.csv`
- `phase_a_survivors.json`
- `output_hashes.json`
- `report.md`
- `PHASE_A_COMPLETE.json`

Phase A survivors are exploratory measurement leaders only. Phase B requires
a separately committed Phase A completion record and a separate Phase B
authorisation.
