# EXP-026 Closure

**Closed date:** 2026-07-28

**Research status:** `REVIEW`

**Classification:** `COMPLETED_MEASUREMENT_REVIEW`

**Closure record SHA-256:** `8ec79810a26b58f2d445d47d3f496539f121d6f3e139eae4a9fd38ef029a386f`

## Objective

EXP-026 compared a bounded, preregistered set of NQ gap-fade,
premarket-continuation and opening-drive candidates on the frozen
Databento-derived EXP-022 continuous series.

The experiment was measurement-first. It had no formal automatic strategy
acceptance gate and kept protected 2026 outside EXP-026.

## Repository chain

- Preregistration: `ce661c7785fa6d8d409378ee2ad63a00f0e0a9b9`
- Locked implementation: `13ee0683dfcbbb5d763f7254f3b245ecc8e6d9cd`
- Phase A authorisation: `5fa417ed56c2d620c5d348e9ab43f3d7634518b8`
- Phase A recovery: `d54289659ffa058ae31558ad3b99b646c31d0bf7`
- Phase A completion: `28bd4209711f0c9b98a7650ab91f6408c2bdf4b7`
- Phase B authorisation: `20ed5ba203f2e4bb3940de389afface6b749d7c7`
- Phase B completion: `da8456d254dc710336806ad5940afcec649be016`
- Phase C authorisation: `5e03bb449468b980e003c133ce076cf1b87b3ac7`
- Phase C completion: `a400a373b87b780c21dc2d15048b1e1a5ad1050a`

## Phase A — development

Phase A measured 22 development candidates and two unchanged controls over
`2010-06-07` through `2017-12-31`.

- Decision rows: 46,584
- Trade rows: 11,502
- Survivors: 6
- Maximum survivors per family: 2
- Independent rebuild: Yes

The original calculation completed before markdown report generation failed
because `tabulate` was absent. Recovery `EXP-026-A-R1` was presentation-only:
it read no market values and recalculated no strategy result.

## Phase B — internal validation

Phase B evaluated the six frozen survivors over `2018-01-01` through
`2019-12-31` and selected one finalist per family:

- `gap_fade_0p75_1r`
- `opening_drive_0p75_time`
- `premarket_continuation_0p875_1p5r`

Selection-aware MCPT used 1,000 permutations. There were 465 permuted
statistics greater than or equal to the real statistic, producing a plus-one
p-value of `0.46553446553446554`.

The MCPT, bootstrap, walk-forward and stability measurements were contextual
evidence rather than decision gates.

## Phase C — known comparison

Phase C measured the three frozen finalists and two controls over
`2020-01-03` through `2025-12-31`.

- Candidate reselection: No
- Parameter changes: No
- Primary representation: `BACKWARD_ADJUSTED`
- Sensitivity representation: `UNADJUSTED`
- Independent rebuild: Yes
- Frozen output files: 14

The 2020–2025 period was already-known historical information. It is not
independent confirmation. The unadjusted sensitivity could not alter finalist
identity.

## Research conclusion

EXP-026 completed the intended bounded comparison and produced three
family-level measurement leaders.

It does not establish that any finalist is a confirmed edge. It also does not
establish formal strategy failure, because EXP-026 had no automatic
accept/reject gates and the known comparison was not independent confirmation.

No candidate is accepted for paper or live trading by EXP-026.

## Protected boundary

- Protected 2026 market values accessed: No
- Protected 2026 strategy calculations performed: No
- Databento API calls: 0
- New Databento download: No
- Network or order API access: No
- Paper trading authorised: No
- Live trading authorised: No

## Next research boundary

EXP-026 is frozen. Do not rerun Phase A, B or C and do not modify its
preregistration, implementation, authorisations, completion records or result
outputs.

The three finalists remain separate evidence rows for future research.
Protected 2026 remains reserved for a new experiment. EXP-027 requires its own
preregistration and separate execution authorisation.

This closure does not authorise EXP-027, a new Databento download, paper
trading, live trading, order access or capital deployment.
