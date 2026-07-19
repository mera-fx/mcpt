# EXP-010 preregistration

## NQ/MNQ opening-drive deep validation

EXP-010 deeply measures the four opening-drive candidates discovered in
EXP-009. It does not add a fifth candidate, optimize a new parameter or change
the frozen data, execution, costs or position sizing.

## Why this experiment exists

The opening-drive family was the clearest measured family in EXP-009:
all four candidates were profitable, Pareto nondominated and free of the
predefined reliability flags. The `opening_drive_0p5_1p5r` candidate is the
user's preferred reference because it combined a 52% win rate with seven of
seven profitable calendar years in the historical measurement.

That preference is useful, but it was formed after viewing EXP-009. It is not
an independent preselection. EXP-010 therefore keeps all four candidates
visible and repeats candidate selection inside the walk-forward process and
inside every primary permutation.

## Locked candidates

| Candidate | Minimum opening drive | Exit |
|---|---:|---|
| `opening_drive_0p5_time` | 0.50 | 15:55 time exit |
| `opening_drive_0p5_1p5r` | 0.50 | 1.5R or 15:55 |
| `opening_drive_0p75_time` | 0.75 | 15:55 time exit |
| `opening_drive_0p75_1p5r` | 0.75 | 1.5R or 15:55 |

The opening drive is the absolute 09:30–10:00 close-minus-open move divided by
that half-hour's high-low range. Direction follows the sign of the move. Entry
is the 10:00 five-minute open, the stop is the opposite side of the opening
range, and every position is flat by the 15:55 one-minute open.

## Common measurement conditions

- Frozen 1,639-session NQ/MNQ dataset from 2019-05-06 through 2025-12-31.
- NQ primary measurement and MNQ implementation comparison.
- Five-minute signals with chronological one-minute execution.
- Conservative stop-first handling when stop and target occur in one minute.
- Fixed one-contract sizing.
- Existing EXP-009 commissions and one-tick-per-side base slippage.
- NQ zero-, one- and two-tick cost sensitivity.
- No volatility targeting.

## Anchored walk-forward measurement

Five folds test 2021, 2022, 2023, 2024 and 2025. Each fold trains on all
earlier available sessions and reselects among all four candidates using the
locked deterministic ranking. A candidate must have more than 1.0 Profit
Factor, positive net profit and at least 100 training trades to be eligible.
If none qualifies, that test fold is recorded as unselected with zero trades.

These folds are useful temporal measurements, but they are not described as
untouched out-of-sample evidence because the full 2019–2025 family results
were already viewed in EXP-009.

## Statistical measurements

The primary MCPT runs 1,000 session-aware NQ permutations using seed 50.
Every permutation runs and reselects all four candidates. The statistic is the
selected candidate's Profit Factor, with the plus-one p-value convention.

A fixed-candidate MCPT for `opening_drive_0p5_1p5r` is reported only as a
secondary diagnostic. Neither test corrects the earlier human choice of the
opening-drive family after comparing six families and 24 candidates.

Ten-thousand-resample bootstrap intervals using seed 5001 are reported for
the full-sample measurement leader and the user-preferred reference. Bootstrap
outputs are measurements, not standalone decision gates.

## Interpretation

The report presents performance, risk, consistency, costs, NQ/MNQ agreement,
walk-forward results, bootstrap uncertainty and MCPT evidence before any
classification.

Secondary context labels are locked:

- **Strong historical evidence:** selection-aware p-value at most 0.05,
  at least four profitable walk-forward folds, positive combined fold profit,
  profitable NQ and MNQ selected results, and positive two-tick NQ profit.
- **Promising but uncertain:** p-value at most 0.10, at least three profitable
  folds, positive combined fold profit, profitable selected NQ result, and
  positive two-tick NQ profit.
- Otherwise: weak or inconclusive historical evidence.

No single threshold converts EXP-010 into a lifecycle rejection. Whatever
happens, every candidate and every measurement remains visible.

## Limits

EXP-010 is exploratory historical deep validation. It cannot independently
confirm an edge, authorize paper trading or authorize live trading. New
parameters, changed seeds, changed costs or further family selection require a
new experiment.
