# EXP-012 extended-hours context discovery result

Lifecycle result: `REVIEW`

EXP-012 measured all 24 preregistered candidates across six extended-hours
strategy families on 1,331 aligned NQ/MNQ sessions from 2020-01-03 through
2025-12-31. It was a discovery and comparison experiment, not a pass/fail
validation.

## Tournament overview

- 24 of 24 candidates were measured.
- 6 of 6 strategy families remain visible.
- 18 candidates produced positive base-cost NQ net profit.
- The same 18 remained profitable with two ticks of slippage per side.
- 3 candidates appeared on the locked multi-dimensional Pareto frontier.
- 10 candidates carried none of the preregistered reliability flags.
- No automatic winner was selected.
- No MCPT, bootstrap, walk-forward or family optimization was run.
- No paper or live trading was authorized.

## Main discoveries

Gap fade was the most consistently attractive family for the user's stated
preference for higher win rate and lower drawdown. All four candidates were
profitable, the family carried no reliability flags, and both 0.50-gap
candidates were Pareto nondominated.

Premarket momentum continuation had the highest median family Profit Factor
and contained the strongest raw individual results. Its strict 0.75 threshold
had only 88 NQ trades, so its impressive result retains an explicit low-sample
warning.

| Review candidate | Trades | PF | Win rate | Net profit | Max drawdown | NQ two-tick net | MNQ PF |
|---|---:|---:|---:|---:|---:|---:|---:|
| Gap fade 0.50, 1R | 186 | 1.530924 | 59.68% | $34,810 | -$5,080 | $32,950 | 1.484381 |
| Premarket 0.50, time | 291 | 1.736374 | 27.84% | $121,255 | -$20,695 | $118,345 | 1.670738 |
| Premarket 0.75, time | 88 | 2.023738 | 31.82% | $44,205 | -$5,540 | $43,325 | 2.098280 |

These three candidates are retained for deeper validation for different,
predeclared reasons:

1. Gap fade 0.50 / 1R best matches the user's win-rate and drawdown preference.
2. Premarket 0.50 / time has the strongest broader-sample performance.
3. Premarket 0.75 / time has the strongest raw PF and efficiency, but must be
   challenged because its sample is small.

They are review candidates, not confirmed winners.

## Weak evidence

The overnight range-breakout family was negative in all four configurations.
Its median Profit Factor was 0.893476 and median net profit was -$55,620.
That family remains visible as a useful negative discovery result.

## Interpretation boundary

The three review candidates were chosen after viewing all 24 historical
measurements. They are not independent preselected hypotheses. A later
experiment must preserve that limitation, keep all three visible, repeat
selection within anchored walk-forward folds, and use a discovery-wide
24-candidate permutation diagnostic for the maximum Profit Factor.

Even that diagnostic cannot erase the fact that its rules were designed after
viewing EXP-012. The complete candidate and family CSV files and protected
manifest are hash-frozen with the closure commit. Detailed local ledgers and
the visual report remain protected generated artifacts.
