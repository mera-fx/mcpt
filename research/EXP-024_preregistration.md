# EXP-024 Preregistration

**Locked date:** 2026-07-26

**Research status:** `PRE_REGISTERED`

**Implementation status:** `NOT_IMPLEMENTED`

**Execution status:** `NOT_RUN`

**Canonical preregistration SHA-256:** `6bc6b7b493aa5eb4a58699fd8cd2c0af15d6c8cfe5323edf9cb3bba1193e3871`

## Title

NQ Cross-Source Signal-Disagreement Attribution

## Purpose

EXP-024 will attribute the 51 frozen primary candidate-session decision
mismatches from EXP-023 to prespecified entry-decision components.

This is a known-overlap diagnostic. It does not replay trades, simulate exits,
calculate profitability, rank candidates, select a vendor, or access the
protected pre-2020 or 2026 history.

## Prior results disclosed before lock

EXP-018 through EXP-023 have already been reviewed. Some mismatch dates and
some Databento transfer-context values were seen before this preregistration.
No complete cross-source feature attribution has been calculated or viewed.
EXP-024 therefore cannot claim blind attribution or independent confirmation.

The frozen EXP-023 result is
`TRANSFER_DIAGNOSTIC_COMPLETE_WITH_MATERIAL_DIFFERENCES`.

| Candidate | Primary mismatch rows | Reference only | Transfer only | Direction mismatch |
|---|---:|---:|---:|---:|
| `gap_fade_0p50_1r` | 48 | 2 | 46 | 0 |
| `premarket_continuation_0p50_time` | 2 | 2 | 0 | 0 |
| `premarket_continuation_0p75_time` | 1 | 1 | 0 | 0 |
| **Total** | **51** | **5** | **46** | **0** |

All 51 candidate-session rows must remain visible. No candidate or mismatch
may be removed after attribution.

## Frozen source context

The Quantower reference is a Lucid/Rithmic provider-managed front-month NQ
series. Its exact roll trigger and historical adjustment method are not
exposed.

The Databento source contains exact quarterly NQ contracts. EXP-022 joined
them using the frozen `VOL_GT_OUT_2S_E3` schedule, with 40 volume-driven
transitions and 25 calendar fallbacks, including 23 warning fallbacks.

Neither source is assumed to be ground truth. Roll proximity is reported as
context and may not be treated automatically as the cause of a mismatch.

## Frozen inputs

| Evidence | Locked value |
|---|---|
| EXP-023 closure commit | `d9843656d764c3146c87220489a762a6e89eb37c` |
| EXP-023 closure record | `e3addce87c97b3cbaf1b5bddee0c9be2be0c75fedb45d3267ae293556e2f2c11` |
| EXP-023 output manifest | `05731ab19c85eff57750dc126da9b2227937094b8bbb1d7da31c38847392194b` |
| EXP-022 closure commit | `9d157c8e7a6ba584a96cb5d37086672ad5b64ea1` |
| Quantower NQ one-minute rows | 1,849,560 |
| Quantower NQ one-minute SHA-256 | `b1679f833d03c2f2aedeaf4ec442a34a284edd307942e13918a0488c71a669cc` |
| Quantower NQ five-minute rows | 369,912 |
| Quantower NQ five-minute SHA-256 | `06598e2dd4cf2b89cd6777fb85881db7feb00faa0a5b4cda435e664a4c3c660a` |
| Databento backward-adjusted rows | 5,457,606 |
| Databento backward-adjusted SHA-256 | `61ccb3621b53fa313147a866948ec1f2c7a6b36956d2ba26090162b518c30c84` |
| Databento unadjusted rows | 5,457,606 |
| Databento unadjusted SHA-256 | `606a69bbba4f4a5db3e0356d7b2849f9481e4555dc24cae4c6b9d1d12f673ab1` |

All source, construction and result evidence is read-only.

## Permitted data access

Only the 51 frozen mismatch sessions may be inspected. Gap-fade rows may also
use their immediately prior frozen reference cash session.

For a mismatch session, the implementation may read only:

- 08:00:00 through 09:29:59 New York premarket OHLC;
- 09:30:00 through 09:34:59 first-cash-bar OHLC;
- the 09:35:00 open price only, for positive-risk validation.

For the immediately prior gap-fade session, it may read only 09:30:00 through
15:59:59 cash-session OHLC.

Databento row filters and column projections must be applied before Parquet
materialization. Current-session OHLCV after entry, all non-mismatch sessions,
and every date outside 2020-2025 remain prohibited. Full-file hashes and
Parquet metadata may be verified without deserializing protected OHLCV.

## Feature reconstruction

Quantower one-minute bars will be independently aggregated and must match the
frozen Quantower five-minute rows for every inspected bin.

For each source, the following locked decision components are reconstructed:

- eligibility;
- normalized gap or premarket context and its threshold margin;
- context direction;
- first 09:30 five-minute bar direction and confirmation;
- 09:35 entry risk and positive-risk validity;
- final setup-pass decision.

No stop, target, exit, P&L, return, equity or drawdown may be evaluated.

## Attribution rule

The component pass/fail vectors are compared for each source.

| Differing decision components | Primary category |
|---|---|
| Eligibility only | `ELIGIBILITY_DIFFERENCE` |
| Normalized threshold only | `NORMALIZED_CONTEXT_THRESHOLD_CROSSING` |
| Context direction only | `CONTEXT_DIRECTION_DIFFERENCE` |
| First-bar confirmation only | `FIRST_CASH_BAR_CONFIRMATION_DIFFERENCE` |
| Positive-risk validity only | `ENTRY_RISK_VALIDITY_DIFFERENCE` |
| More than one component | `MULTIPLE_DECISION_COMPONENT_DIFFERENCES` |
| No component explains a frozen mismatch | `UNRESOLVED_WITH_LOCKED_FEATURES` |

Every candidate-session receives exactly one primary category. Manual
relabelling and statistical attribution models are prohibited.

Raw strategy-input price differences are reported in NQ ticks. Source
contract, selected-roll distance, calendar fallback and provider-warning
context are descriptive tags only.

## Classification

- `ATTRIBUTION_COMPLETE_WITH_IDENTIFIED_COMPONENTS` when all hard checks pass
  and all 51 mismatches are attributed without an unresolved row.
- `ATTRIBUTION_COMPLETE_WITH_UNRESOLVED_CASES` when all hard checks pass but
  one or more rows remain unresolved.
- `ATTRIBUTION_DIAGNOSTIC_NOT_QUALIFIED` when any hard check fails.

No classification qualifies a best vendor, validates strategy edge, unlocks
protected history, selects a candidate, or authorizes paper/live trading.

## Required outputs

- `attribution_summary.json`
- `mismatch_attribution.csv`
- `feature_comparison.csv`
- `raw_component_differences.csv`
- `roll_context.csv`
- `aggregation_check.csv`
- `output_hashes.json`
- `report.md`
- `report.html`
- `ATTRIBUTION_DIAGNOSTIC_COMPLETE.json`

The visual report must show attribution categories, paired threshold margins,
raw component differences in ticks and roll context. It must keep all three
candidates separate and contain no profitability or equity table.

## Execution boundary

This preregistration calculates no EXP-024 result. Before any diagnostic:

1. A result-free implementation must be committed.
2. A protected preflight must pass.
3. Separate one-time execution authorization must be committed.

Only one attribution run is permitted. Rerunning EXP-023, modifying frozen
evidence, changing a threshold, reading protected history, downloading new
data, optimization, MCPT, bootstrap, walk-forward, paper trading and live
trading remain prohibited.
