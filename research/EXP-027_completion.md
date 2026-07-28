# EXP-027 Completion Record

**Experiment:** EXP-027

**Completion date:** 2026-07-28

**Classification:** `PROTECTED_2026_MEASUREMENT_COMPLETE`

**Completion-record SHA-256:** `13a550c0d72649d4775ac6472e0976695790ad09a303055de5df229cbc44e9ec`

## Frozen ancestry

| Item | Value |
|---|---|
| Preregistration commit | `21c182e119cde651e6c4fe22b1e4e8d6b99def5b` |
| Implementation commit | `591cdf43b4c23abc312ae3d50b7d7948f88c90b2` |
| Authorization commit | `88d6f4f7addad0e5ad9db6134987875ff1a7df10` |
| Authorization SHA-256 | `d0745af1570530772ec8b647aedb81c4c0a88f4358c087b9dd72765d694ff383` |

## Completed measurement

| Item | Value |
|---|---:|
| Protected period | 2026-01-01 through 2026-07-23 |
| Strategy variants | 22 |
| Fixed controls | 2 |
| Canonical series | 24 |
| Backward-adjusted source rows | 198,240 |
| Unadjusted source rows | 198,240 |
| Backward-adjusted decision rows | 3,480 |
| Unadjusted decision rows | 3,480 |
| Backward-adjusted trades | 925 |
| Unadjusted trades | 927 |
| Output files | 111 |

## Integrity

Independent rebuild and serial/parallel parity passed. All 111 output files
were independently byte-hashed. The output manifest SHA-256 is:

`fd8823bea6a04407da5f574552e4b17a79d8c21ec949a93c693421ef743e51d7`

## Boundary

The protected 2026 period has been consumed and EXP-027 cannot be rerun.
The completion record freezes evidence before performance interpretation.
It does not validate an edge, establish strategy failure, select one winner,
or authorise paper or live trading.

No Databento API call, new download, network access or historical 2010-2025
market-row access occurred.
