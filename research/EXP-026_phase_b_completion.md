# EXP-026 Phase B Completion Record

**Experiment:** EXP-026

**Phase:** B — Internal Validation

**Completion date:** 2026-07-28

**Status:** `COMPLETED`

**Locked implementation commit:** `13ee0683dfcbbb5d763f7254f3b245ecc8e6d9cd`

**Phase A completion commit:** `28bd4209711f0c9b98a7650ab91f6408c2bdf4b7`

**Phase B authorisation commit:** `20ed5ba203f2e4bb3940de389afface6b749d7c7`

**Completion-record SHA-256:** `bbc5e38f4f08ef87d423f1d7890fd2dc87c5afd2068287f4272c7f46bcb1b3de`

## Completed evidence

- Materialised source: `2010-06-07` through `2019-12-31`
- Internal-validation selection: `2018-01-01` through `2019-12-31`
- Phase A survivors evaluated: 6
- Fixed controls reported: 2
- Finalists selected: 3
- Maximum finalists per family: 1
- Independent deterministic rebuild: Yes
- Anchored walk-forward folds: 6
- Bootstrap resamples: 10,000
- MCPT permutations: 1,000
- MCPT plus-one p-value: `0.46553446553446554`

## Frozen Phase B finalists

- `gap_fade_0p75_1r`
- `opening_drive_0p75_time`
- `premarket_continuation_0p875_1p5r`

These are internal-validation leaders, not confirmed trading edges.

## MCPT interpretation

The selection-aware MCPT used a session-shared post-entry path-sign
permutation, repeated Phase A and Phase B selection, and conditioned on the
entry-known setup schedule. The p-value is contextual evidence rather than a
pass/fail gate.

## Frozen output files

- `PHASE_B_COMPLETE.json` — 1,534 bytes — `02fdd3fc5f8387d0daeee43b4da5d75a032cdf756d1c19783e067bbeb41343e0`
- `assets/drawdown_curves.png` — 286,339 bytes — `24609b848f24fd72ab6d4e51e0e7f5abb12b0a034ad68bf255fed32dac16cb0f`
- `assets/equity_curves.png` — 254,566 bytes — `6e2e99f073e4426c1e98f078e397193143ae58bb7c2e71d132e33341de5d414e`
- `bootstrap_summary.csv` — 705 bytes — `8ed99915e58cd211441580d345ff933a5734ff8a0e9ecfece60f857d71fee2fd`
- `internal_validation_metrics.csv` — 8,042 bytes — `9efb6a32d1991938a76aa910c739d3a2e8d9511dead6bf16f16eaa71d4a17f31`
- `internal_validation_summary.json` — 731 bytes — `fc94abdfe9027c497003918642e848aebd1694095107410ee283be904dbbea55`
- `mcpt_summary.json` — 769 bytes — `ab9fc4c63a970c4e00fda819139612d7191e9afe6e63ad9b1d1b334f0b1f8d6f`
- `output_hashes.json` — 1,694 bytes — `c26b20ceadfec332e9dd72870bc25b37554e184216515a8b8f868c24c0e621a9`
- `parameter_stability.csv` — 4,891 bytes — `ba5b475b1683058e26e18067c37e8a9b028c638407b705645a828068fc300c1c`
- `report.html` — 20,503 bytes — `7dd21d377d1217c347d629d494bddb83106bfa3a2f9c6986e4dc8bdf3b38e514`
- `report.md` — 6,197 bytes — `8c02b66565c06c7fd06b607bc5f3775425691fabcac949af8b5dbc08ca782728`
- `selected_finalists.json` — 504 bytes — `6c23d1b52501fafa3b966d9f4060421cad65e789b90651d25ca0ab582a1acc77`
- `walk_forward_results.csv` — 2,674 bytes — `ac52ce63ff9301be7791e9e9eb39318bbb5996264eff1ae4da693be0c9bb0a3f`

## Protected boundary

- Known 2020–2025 comparison accessed: No
- Known 2020–2025 access authorised: No
- Phase C execution authorised: No
- Protected 2026 accessed: No
- Protected 2026 access authorised: No
- New Databento download authorised: No
- Databento API calls: 0
- Network access: No
- Paper trading authorised: No
- Live trading authorised: No

A separate committed Phase C authorisation is required before the
2020–2025 known-comparison period or unadjusted representation may be read.
