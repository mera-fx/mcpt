# EXP-027 Protected 2026 Measurement

## Boundary

- Period: `2026-01-01` through `2026-07-23`
- Candidate selection: `False`
- Parameter optimisation: `False`
- Winner declaration: `False`
- Databento API calls: `0`
- Paper/live trading authorised: `False`

## All 24 evidence rows

| Candidate | Cohort | Trades | Net profit | Profit Factor | Win rate | Maximum drawdown |
|---|---|---:|---:|---:|---:|---:|
| gap_fade_0p25_prior_close | SECONDARY_MEASUREMENT_CONTEXT | 48 | -11,580.000 | 0.780 | 35.417% | -24,490.000 |
| gap_fade_0p25_1r | SECONDARY_MEASUREMENT_CONTEXT | 48 | -4,055.000 | 0.908 | 43.750% | -16,090.000 |
| gap_fade_0p50_prior_close | SECONDARY_MEASUREMENT_CONTEXT | 31 | 3,470.000 | 1.109 | 35.484% | -13,440.000 |
| gap_fade_0p50_1r | SECONDARY_MEASUREMENT_CONTEXT | 31 | 5,080.000 | 1.210 | 45.161% | -9,340.000 |
| gap_fade_0p75_prior_close | SECONDARY_MEASUREMENT_CONTEXT | 15 | 580.000 | 1.030 | 26.667% | -9,245.000 |
| gap_fade_0p75_1r | PRIMARY_CONFIRMATION_COHORT | 15 | 6,240.000 | 1.530 | 46.667% | -6,215.000 |
| premarket_continuation_0p50_time | SECONDARY_MEASUREMENT_CONTEXT | 25 | -4,080.000 | 0.841 | 28.000% | -20,640.000 |
| premarket_continuation_0p50_1p5r | SECONDARY_MEASUREMENT_CONTEXT | 25 | -9,537.500 | 0.629 | 28.000% | -19,522.500 |
| premarket_continuation_0p625_time | SECONDARY_MEASUREMENT_CONTEXT | 18 | -6,435.000 | 0.675 | 22.222% | -17,600.000 |
| premarket_continuation_0p625_1p5r | SECONDARY_MEASUREMENT_CONTEXT | 18 | -10,482.500 | 0.470 | 22.222% | -16,227.500 |
| premarket_continuation_0p75_time | SECONDARY_MEASUREMENT_CONTEXT | 9 | -10,860.000 | 0.000 | 0.000% | -10,860.000 |
| premarket_continuation_0p75_1p5r | SECONDARY_MEASUREMENT_CONTEXT | 9 | -10,860.000 | 0.000 | 0.000% | -10,860.000 |
| premarket_continuation_0p875_time | SECONDARY_MEASUREMENT_CONTEXT | 0 | 0.000 | — | —% | 0.000 |
| premarket_continuation_0p875_1p5r | PRIMARY_CONFIRMATION_COHORT | 0 | 0.000 | — | —% | 0.000 |
| opening_drive_0p25_time | SECONDARY_MEASUREMENT_CONTEXT | 106 | 2,590.000 | 1.017 | 47.170% | -45,395.000 |
| opening_drive_0p25_1p5r | SECONDARY_MEASUREMENT_CONTEXT | 106 | 9,127.500 | 1.060 | 50.943% | -45,697.500 |
| opening_drive_0p50_time | SECONDARY_MEASUREMENT_CONTEXT | 69 | -6,505.000 | 0.940 | 47.826% | -43,730.000 |
| opening_drive_0p50_1p5r | SECONDARY_MEASUREMENT_CONTEXT | 69 | 1,782.500 | 1.016 | 50.725% | -46,832.500 |
| opening_drive_0p75_time | PRIMARY_CONFIRMATION_COHORT | 27 | 7,770.000 | 1.187 | 51.852% | -12,605.000 |
| opening_drive_0p75_1p5r | SECONDARY_MEASUREMENT_CONTEXT | 27 | 10,340.000 | 1.249 | 51.852% | -13,712.500 |
| opening_drive_1p00_time | SECONDARY_MEASUREMENT_CONTEXT | 0 | 0.000 | — | —% | 0.000 |
| opening_drive_1p00_1p5r | SECONDARY_MEASUREMENT_CONTEXT | 0 | 0.000 | — | —% | 0.000 |
| orb_control_exp005_15m_both_time | FIXED_CONTROL | 139 | -23,820.000 | 0.885 | 45.324% | -74,605.000 |
| orb_control_exp007_30m_long_1r | FIXED_CONTROL | 90 | 25,715.000 | 1.324 | 63.333% | -28,920.000 |

## Interpretation

The three primary candidates were declared before protected 2026 access. The remaining strategy variants are comparison evidence and cannot replace the primary cohort under EXP-027.

This report describes measured behaviour. It does not automatically validate an edge, reject a strategy, choose one winner or authorise trading.

## Reproducibility

- Independent rebuild: `True`
- Serial/parallel parity: `True`
- Protected source rows, primary: `198,240`
- Protected source rows, unadjusted: `198,240`
