# EXP-024 Evidence-Only Recovery Implementation

**Required base commit:** `7acf180c9640079c560c992a00c4fd413f3b13b7`

## Purpose

This implementation can publish the nine artifacts preserved after EXP-024
attempt 002 without reading market Parquet files or recalculating attribution.

## Locked input

- Attempt-002 failure record SHA-256:
  `d58e747db36ae3c5e80a034e3b6de127d9771184805470a16f0d3adbbab77359`
- Preserved partial artifacts: 9
- Candidate-session rows: 51
- Frozen classification: `ATTRIBUTION_DIAGNOSTIC_NOT_QUALIFIED`

## Permitted recovery

After a separate authorization commit, the runner may:

1. verify the attempt-002 failure record;
2. verify the exact size and SHA-256 of all nine partial artifacts;
3. read the five preserved CSV files;
4. generate the missing summary, Markdown report, HTML report, hash manifest
   and completion marker;
5. verify the original nine files remain unchanged;
6. atomically rename the partial directory to the final directory.

## Prohibited operations

- market Parquet access;
- Databento API or network access;
- feature reconstruction;
- attribution recalculation;
- chart rebuilding;
- strategy replay or performance evaluation;
- optimization, MCPT, bootstrap or walk-forward analysis;
- paper or live trading authorization;
- retrying either attribution attempt.

## Execution gates

The implementation exposes:

- `--preflight` before authorization;
- `--authorized-preflight` after a separate authorization commit;
- `--recover --confirm-evidence-only-recovery` for one publication recovery.

No recovery is authorized by this implementation commit itself.
