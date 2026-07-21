# EXP-014 Finalist Behaviour and Complementarity Result

## Status

EXP-014 is a completed descriptive historical measurement and is closed to
`REVIEW`.

It is not an independent confirmation, pass/fail test, winner selection,
portfolio optimization, paper-trading authorization or live-trading
authorization.

## Frozen provenance

- Result implementation commit:
  `f56c1e0137b3c902cc0c25d8c29e7a01a13b62b2`
- Source data: frozen EXP-012 extended-session data
- Included sessions: 1,331
- Historical period: 2020-01-03 through 2025-12-31
- Source finalists: the exact three EXP-013 finalists
- Strategy, parameter, cost and position-sizing changes: none
- EXP-013 MCPT, bootstrap and walk-forward reruns: none

All three reconstructed headline measurements matched the frozen EXP-013
records exactly before the final EXP-014 outputs were written.

## Finalists

| Candidate | Trades | Profit Factor | Net profit | Maximum drawdown | Profitable years |
|---|---:|---:|---:|---:|---:|
| Gap fade 0.50, 1R | 186 | 1.531 | $34,810 | -$5,080 | 6 of 6 |
| Premarket continuation 0.50, time exit | 291 | 1.736 | $121,255 | -$20,695 | 5 of 6 |
| Premarket continuation 0.75, time exit | 88 | 2.024 | $44,205 | -$5,540 | 5 of 6 |

The 0.75 premarket candidate retains the frozen low-sample warning because it
contains 88 NQ trades.

## What happened in 2025

| Candidate | 2025 trades | 2025 net profit | 2025 Profit Factor | 2025 maximum drawdown |
|---|---:|---:|---:|---:|
| Gap fade 0.50, 1R | 38 | $6,070 | 1.336 | -$5,060 |
| Premarket continuation 0.50, time exit | 44 | $9,635 | 1.264 | -$20,695 |
| Premarket continuation 0.75, time exit | 10 | -$2,890 | 0.525 | -$3,945 |

The premarket 0.50 strategy remained profitable in 2025, but its result was
less efficient and included an 18-trade losing streak. The premarket 0.75
strategy had only ten 2025 trades and lost money. These observations remain
descriptive and do not create a regime filter or rule change.

## Behavioural differences

Gap fade had the highest win rate at 59.7% and the shortest average holding
time at about 28 minutes. Its payoff ratio was close to one, so its edge was
primarily associated with frequent wins rather than very large winners.

The two premarket-continuation variants had lower win rates and much larger
winner-to-loser payoff ratios. Their median trades were losses, while their
average results depended on less frequent large winners. The 0.50 variant had
the broadest participation and the largest absolute net profit, but also the
largest drawdown and longest losing streak.

The 0.75 variant had the smallest sample and the largest top-trade
concentration. Its top five trades contributed about 60.9% of net profit.

## Overlap and dependence

Cross-family overlap was limited:

| Pair | Overlap sessions | All-session P&L correlation | Opposite-direction overlaps |
|---|---:|---:|---:|
| Gap fade + premarket 0.50 | 15 | 0.041 | 0 |
| Gap fade + premarket 0.75 | 6 | 0.021 | 0 |

The two nested premarket variants overlapped on all 88 sessions taken by the
0.75 variant. Their active-overlap P&L correlation was effectively one,
confirming that they are nested variants rather than independent sleeves.

Low cross-family all-session correlation describes different timing and
participation. It does not prove independence, causality or future
diversification.

## Fixed arithmetic sleeve pairs

The preregistered pairs used one NQ contract per active sleeve and no weight
search, pair selection or portfolio optimization.

| Diagnostic pair | Net profit | Maximum drawdown | Net / drawdown | Profitable years | Worst year |
|---|---:|---:|---:|---:|---:|
| Gap fade + premarket 0.50 | $156,065 | -$23,365 | 6.679 | 5 of 6 | -$1,915 |
| Gap fade + premarket 0.75 | $79,015 | -$8,045 | 9.822 | 6 of 6 | $1,750 |

These are arithmetic research sleeves on the same instrument. They are not
an executable netting-account simulation and do not authorize a portfolio.

## Documented result-review correction

The first generated report incorrectly showed zero total and profitable years
for both sleeve pairs. The cause was pandas index alignment while grouping
session P&L by year.

The correction changed only annual sleeve-pair aggregation. It did not alter
strategy trades, standalone P&L, pair session P&L, pair net profit, pair
drawdown, strategy rules, parameters, costs or sizing.

After the correction:

- Gap fade + premarket 0.50: 5 profitable years out of 6; worst year
  -$1,915.
- Gap fade + premarket 0.75: 6 profitable years out of 6; worst year
  +$1,750.

The correction was committed before the final result was regenerated.

## Frozen supporting outputs

The final lock covers:

- `study_result.json`
- all standalone, period, behaviour, concentration and drawdown tables
- monthly and rolling measurements
- regime context
- all-session strategy and pair P&L
- pairwise overlap measurements
- corrected sleeve-pair measurements
- all three enriched NQ trade ledgers

The visual report is expected at
`reports/EXP-014-research-lab/report.html` with its 18 registered chart
assets.

## Interpretation boundary

EXP-014 preserves all three finalists as different measured trade-offs.

It does not:

- select a winner;
- introduce a pass/fail gate or composite score;
- select a regime filter;
- optimize pair membership or weights;
- combine the nested premarket candidates;
- claim independent confirmation;
- define an executable portfolio;
- authorize paper or live trading.

Any new rule, filter, weighting, sizing choice, pair-selection procedure or
execution design requires a separate preregistered experiment ID.
