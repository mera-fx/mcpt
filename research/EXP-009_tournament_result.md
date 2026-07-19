# EXP-009 multi-strategy discovery result

Lifecycle result: `REVIEW`

EXP-009 measured all 24 preregistered candidates across six strategy
families on the frozen 1,639-session NQ/MNQ dataset. It was a discovery and
comparison experiment, not a pass/fail validation.

## Tournament overview

- 24 of 24 candidates were measured.
- 6 of 6 strategy families were retained in the report.
- 12 candidates produced positive base-cost NQ net profit.
- 10 remained profitable with two ticks of slippage per side.
- 5 candidates appeared on the locked multi-dimensional Pareto frontier.
- 9 candidates carried none of the preregistered reliability flags.
- No automatic winner was selected.
- No MCPT, bootstrap or family optimization was run.
- No paper or live trading was authorized.

## Main discovery

The opening-drive continuation family was the strongest measured family.
All four candidates were profitable, remained profitable under the
two-tick NQ stress, had NQ and MNQ Profit Factors above 1.0, carried no
reliability flags and appeared on the Pareto frontier.

| Candidate | Trades | PF | Win rate | Net profit | Max drawdown | Profitable years |
|---|---:|---:|---:|---:|---:|---:|
| 0.5 drive, time exit | 775 | 1.350073 | 49.29% | $213,905 | -$25,280 | 6/7 |
| 0.5 drive, 1.5R | 775 | 1.315847 | 52.00% | $187,850 | -$24,930 | 7/7 |
| 0.75 drive, time exit | 312 | 1.300486 | 50.96% | $78,445 | -$19,050 | 6/7 |
| 0.75 drive, 1.5R | 312 | 1.242274 | 51.60% | $62,677.50 | -$14,975 | 5/7 |

The user-preferred reference for deeper validation is the `0.5 / 1.5R`
candidate because it combined a 52% win rate, seven of seven profitable
calendar years, lower drawdown than the unrestricted time-exit version and
strong cost and MNQ measurements.

## Interpretation boundary

EXP-009 used historical data that had already been viewed and selected the
opening-drive family after comparing six families. These measurements do
not confirm an edge. The next experiment must keep all four opening-drive
candidates inside walk-forward selection and selection-aware MCPT, retain
the discovery-selection limitation in its interpretation, and make no
automatic trading authorization.

The complete candidate and family CSV files and protected manifest are
tracked with the closure commit. The local detailed trade ledgers and
visual report remain protected generated artifacts.
