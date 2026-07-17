# EXP-008 Preregistration

## Structured Long-Only ORB Exit-Geometry Optimization

**Locked before any EXP-008 result is calculated:** 17 July 2026

EXP-008 is a new experiment. It does not reopen or alter EXP-007. The
fixed EXP-007 strategy remains a rejected historical result after missing
its locked session-aware MCPT gate.

## Research question

Can a deliberately small search over opening-range length, profit-target
distance and forced-flat time identify a stable long-only NQ opening-range
breakout geometry with stronger evidence than the frozen EXP-007 baseline?

The historical evidence is exploratory because the 2019–2025 period has
already been viewed. Even a passing result can only nominate a candidate
for comparison on genuinely new forward paper data.

## Frozen data

- Primary evidence market: NQ
- Secondary implementation check: MNQ
- Source: frozen EXP-005 Quantower/Lucid-Rithmic data
- Period: 6 May 2019 through 31 December 2025
- Expected sessions: 1,639
- Signal resolution: five minutes
- Execution resolution: one minute
- No new cleaning, missing-bar filling or raw-data editing

## Locked 27-candidate grid

| Parameter | Values |
|---|---|
| Opening range | 15, 30, 45 minutes |
| Profit target | 0.5R, 1.0R, 1.5R |
| Forced flat | 12:00, 14:00, 15:55 New York |
| Direction | Long only |
| Position size | One fixed contract |

The frozen EXP-007 baseline, `30 minutes / 1.0R / 14:00`, appears exactly
once.

No value may be added, removed or changed after any EXP-008 result is
viewed.

## Shared strategy rules

Each candidate uses the first completed five-minute close strictly above
its opening-range high. Entry occurs at the next five-minute opening
price. The protective stop is the candidate opening-range low. The target
is the entry plus the candidate R multiple of actual entry risk.

There is at most one long trade per session. There are no short trades,
reentries, indicators, delta confirmation, discretionary filters, gap
filters or volatility targeting.

The final eligible signal closes five minutes before the candidate
forced-flat time, allowing entry at that same timestamp and five minutes
before the forced exit.

## Intrabar execution

Minutes are evaluated chronologically. A stop gap fills at the one-minute
open. Otherwise the stop fills at its boundary. A target gap receives no
favourable improvement. When both stop and target occur inside the same
minute, the stop is assumed first. A trade may exit during its entry
minute.

## Candidate eligibility and selection

Candidate selection is performed on NQ using the base one-tick slippage
model.

A candidate is eligible only when all of the following hold:

- Profit Factor is strictly above 1.0.
- Net profit is strictly positive.
- At least 100 completed trades are available in the selection sample.
- At least half of its immediate ordered-grid neighbours have Profit
  Factor above 1.0 and positive net profit.
- The median immediate-neighbour Profit Factor is strictly above 1.0.

Immediate neighbours differ by one adjacent step in one parameter and are
identical in the other two parameters.

Eligible candidates are ranked by:

1. Profit Factor, descending.
2. Net-profit-to-drawdown ratio, descending.
3. Net profit, descending.
4. Completed trades, descending.
5. Parameter key, ascending.

This exact procedure is repeated in every training fold and inside every
MCPT permutation.

## Anchored annual walk-forward evaluation

Five expanding training folds are locked:

| Fold | Training period | Test year |
|---:|---|---:|
| 1 | 2019-05-06 through 2020-12-31 | 2021 |
| 2 | 2019-05-06 through 2021-12-31 | 2022 |
| 3 | 2019-05-06 through 2022-12-31 | 2023 |
| 4 | 2019-05-06 through 2023-12-31 | 2024 |
| 5 | 2019-05-06 through 2024-12-31 | 2025 |

Each fold selects using training data only and evaluates that selected
candidate on the next calendar year. At least three test folds must be
profitable, and combined fold-selected NQ net profit must be positive.

Because these years have already been viewed in prior research, this is a
temporal robustness diagnostic rather than untouched out-of-sample proof.

## Selection-aware MCPT

The primary statistical test uses 1,000 session-aware NQ permutations and
seed 48. All 27 candidates are run inside every permutation, including the
same eligibility, neighbour and ranking procedure.

The statistic is the selected candidate's trade Profit Factor.

`p = (1 + permuted selected PF values at least as large as the real
selected PF) / 1001`

Passing requires `p <= 0.05`.

## Cost, MNQ and bootstrap checks

The final selected candidate is evaluated at zero, one and two ticks of
slippage per side. NQ net profit must remain positive at two ticks.

MNQ is an implementation consistency check rather than independent
evidence. Its Profit Factor and net profit must both be positive under the
base model.

A 10,000-resample completed-trade bootstrap using seed 4801 reports
average-trade and Profit Factor intervals. It is descriptive and is not a
decision gate.

## Locked historical decision gates

Every gate must pass:

- The selected candidate satisfies the neighbour-stability eligibility.
- Selected NQ Profit Factor is strictly above the frozen EXP-007 value of
  1.1168167521220216.
- Selected NQ net profit and average trade are positive.
- At least 500 selected NQ trades are completed.
- The final selected candidate is profitable in at least three of
  2021–2025, with positive combined net profit.
- At least three anchored test folds are profitable, with positive
  combined fold-selected net profit.
- Selection-aware MCPT p-value is no greater than 0.05.
- Two-tick-stress NQ net profit is positive.
- Selected MNQ Profit Factor is above 1.0 and MNQ net profit is positive.

A failure preserves EXP-008 as a negative result. A pass only locks the
selected geometry for a new forward paper comparison. Historical EXP-008
results never authorize live trading.

## Reporting

The report must be vertical, top-to-bottom and full width. It must include
the complete 27-candidate table, parameter slices, neighbour evidence,
anchored folds, annual results, cost sensitivity, NQ and MNQ summaries,
equity and drawdown curves, MCPT distribution, bootstrap intervals and a
direct comparison with the frozen EXP-007 baseline.
