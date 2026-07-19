# EXP-010 protected implementation

Status: `IMPLEMENTED_NOT_RUN`

The implementation contains no EXP-010 strategy result. It must be committed
with a clean working tree before the protected preflight or one-time run.

## Implemented measurements

- All four locked EXP-009 opening-drive candidates.
- NQ base results and MNQ implementation comparison.
- NQ zero-, one- and two-tick cost sensitivity.
- Five anchored annual walk-forward folds with training-only reselection.
- Ten-thousand-resample bootstrap diagnostics for the full-sample measurement
  leader and the user-preferred `opening_drive_0p5_1p5r` reference.
- One-thousand session-aware NQ permutations with all four candidates
  reselected inside every permutation.
- A secondary fixed-reference MCPT diagnostic.
- A vertical report with plain-English context, all four candidates, normalized
  NQ comparison, drawdowns, annual results, cost sensitivity, walk-forward,
  bootstrap and MCPT visuals.

## Protected boundaries

- No new candidate or opening-drive parameter.
- No changed frozen data, cleaning, costs or execution.
- Fixed one-contract sizing.
- No claim that the four-candidate MCPT corrects the earlier choice among six
  families in EXP-009.
- No automatic accept/reject lifecycle decision.
- No paper or live trading authorization.
