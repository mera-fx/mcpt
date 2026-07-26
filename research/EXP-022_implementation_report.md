# EXP-022 Protected Construction Implementation

**Implementation base:** `73c1255bcb904e71d927ed1097788de9b791bb54`

**Status:** `IMPLEMENTED_NOT_AUTHORIZED_NOT_RUN`

## Scope

This implementation constructs exactly two representations of the one frozen
EXP-021-selected `VOL_GT_OUT_2S_E3` schedule:

- `selected_roll_unadjusted.parquet`
- `selected_roll_backward_adjusted.parquet`

It reads the 65 effective roll dates from the frozen EXP-021 transition
evidence and does not recalculate or reselect them.

## Protection

The implementation:

- requires a separate authorization commit locked to the implementation SHA;
- requires clean and synchronized `main`;
- refuses if any EXP-022 output directory exists;
- refuses while `DATABENTO_API_KEY` is present;
- makes zero Databento API calls;
- verifies EXP-019 source evidence and frozen EXP-020/EXP-021 outputs;
- builds the selected dataset twice and compares semantic and byte hashes;
- snapshots frozen inputs before and after construction;
- never authorizes strategy, optimisation, MCPT, paper or live trading.

## Outputs

- `roll_ledger.csv`
- `contract_contribution.csv`
- `selected_roll_unadjusted.parquet`
- `selected_roll_backward_adjusted.parquet`
- `construction_summary.json`
- `output_hashes.json`
- `report.md`
- `CONSTRUCTION_COMPLETE.json`

## Hard checks

All 20 preregistered hard checks are represented explicitly. Successful
construction qualifies the dataset only and does not establish strategy edge.
