# EXP-006 Protected Implementation

**Status:** Locked before any EXP-006 result  
**Source preregistration commit:** `799a758`  
**Historical interpretation:** Exploratory; new forward data remains required

## Implemented components

1. A vectorized, parameterized NQ/MNQ ORB engine for the exact 27-combination grid.
2. Global candidate eligibility, six-component median-rank scoring and immediate-neighbour stability.
3. Five anchored annual walk-forward folds. Each fold selects parameters from training data only and tests the chosen parameters on the following year.
4. A selection-aware NQ MCPT. Every one of the 27 candidates is evaluated inside each of 1,000 session-aware permutations.
5. Checkpoint/resume and deterministic worker seeds.
6. A protected one-time runner and vertical research report.

## MCPT statistic

For the real market and each permutation, candidates must have NQ Profit Factor above 1, positive NQ net profit and at least 1,000 completed trades. Each eligible candidate receives a bounded composite of:

- Profit Factor excess above 1;
- net-profit-to-maximum-drawdown;
- average-trade-to-round-trip-cost; and
- profitable-year fraction.

The maximum candidate composite is the selection-aware statistic. The p-value uses the locked plus-one formula.

## Boundaries

EXP-005 remains unchanged as the control. EXP-006 cannot authorize live trading. A historical pass may lock at most one candidate for a separate forward paper comparison.
