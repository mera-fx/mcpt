# EXP-023 Closure

**Closed date:** 2026-07-26

**Classification:** `TRANSFER_DIAGNOSTIC_COMPLETE_WITH_MATERIAL_DIFFERENCES`

**Closure record SHA-256:** `e3addce87c97b3cbaf1b5bddee0c9be2be0c75fedb45d3267ae293556e2f2c11`

## Result

The single authorized EXP-023 run completed on the already-known 2020-2025
overlap. All 20 hard process and evidence-integrity checks passed, the
independent rebuild matched, all 1,331 reference sessions were accounted for,
and no protected earlier or 2026 strategy history was accessed.

The transfer result was mixed. One of the three frozen finalists passed every
primary transfer gate; two did not. EXP-023 therefore does not qualify all
three finalists as a group and does not select a winner.

| Primary candidate | Eligible | Decision agreement | Trade-count difference | Common-trade match | Result |
|---|---:|---:|---:|---:|---|
| `gap_fade_0p50_1r` | 99.62% | 96.46% | 23.66% | 79.31% | FAIL |
| `premarket_continuation_0p50_time` | 99.85% | 99.85% | 0.69% | 99.31% | PASS |
| `premarket_continuation_0p75_time` | 99.85% | 99.92% | 1.14% | 98.86% | FAIL |

The locked gates required at least 99% eligible sessions, at least 99%
decision-and-direction agreement, no more than 1% relative trade-count
difference, at least 98% common-trade match, at least 99% entry-time agreement,
at least 0.995 common-trade gross-P&L correlation, and at least 99% gross-P&L
sign agreement.

The gap-fade row failed decision agreement, trade-count difference and
common-trade match. The 0.75 premarket row missed only the trade-count gate:
one missing transfer trade produced a 1.136% difference against the locked
1.000% maximum.

## Measured transfer performance

These figures describe the known-overlap replay. Profitability was not a
qualification gate and is not independent evidence of edge.

| Primary candidate | Trades | Profit factor | Net P&L | Maximum drawdown |
|---|---:|---:|---:|---:|
| `gap_fade_0p50_1r` | 230 | 1.367 | $30,905 | -$8,735 |
| `premarket_continuation_0p50_time` | 289 | 1.718 | $117,960 | -$20,715 |
| `premarket_continuation_0p75_time` | 87 | 1.923 | $39,840 | -$5,555 |

## Representation sensitivity

The unadjusted representation produced the same pass/fail pattern as the
primary backward-adjusted representation. Adjusted-versus-unadjusted
decision agreement was 99.70% for gap fade and 100% for both premarket rows.
This does not cure the cross-source gap-fade mismatch or the 0.75 row's
trade-count-gate miss.

## Evidence integrity

- Exactly one authorized transfer run completed.
- All 20 hard checks passed; hard failures: 0.
- The independent rebuild reproduced all seven semantic frame hashes.
- All 18 manifested outputs and the two manifest/marker files are locked by
  size and SHA-256 in `exp023_closure.py`.
- Seven report images were visually inspected and were readable.
- Databento/API calls, network access, optimization, MCPT, bootstrap,
  walk-forward, strategy ranking, paper trading and live trading all remained
  disabled.
- The protected pre-2020 and 2026 strategy history remains unaccessed.

## Interpretation

All three EXP-014 finalists remain separate evidence rows. The passing
0.50 premarket row is not automatically promoted, and the two failed rows
must not be rescued through threshold changes or retuning. EXP-023 is a
known-overlap cross-source diagnostic, not independent edge confirmation.

The frozen HTML report is:

`results/EXP-023/transfer_qualification/report.html`

## Frozen boundary

EXP-023 is permanently frozen. Do not rerun the preflight or transfer runner
and do not modify any file under:

`results/EXP-023/transfer_qualification`

Any root-cause investigation, candidate decision, or protected-history
validation requires a new experiment ID, a separate preregistration, and
separate execution authorization. EXP-023 authorizes neither paper nor live
trading.
