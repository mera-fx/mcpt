# EXP-008 Structured Exit-Geometry Optimization Result

**Decision:** Reject EXP-008 and preserve it as a completed negative
historical result.

## Locked search

EXP-008 searched 27 long-only ORB combinations:

- Opening range: 15, 30 or 45 minutes
- Profit target: 0.5R, 1.0R or 1.5R
- Forced flat: 12:00, 14:00 or 15:55 New York
- One fixed contract
- NQ primary evidence and MNQ implementation check
- No short side, delta confirmation or volatility sizing

## Selected candidate

The locked selection procedure chose:

**45-minute opening range / 1.5R target / 15:55 forced flat**

All 27 candidates were eligible and neighbour-stable. The selected
corner candidate had three profitable immediate neighbours and a median
neighbour NQ Profit Factor of 1.116297.

| Metric | NQ | MNQ |
|---|---:|---:|
| Completed trades | 994 | 994 |
| Profit Factor | 1.156583 | 1.131375 |
| Net profit | $102,802.50 | $8,729.25 |
| Average trade | $103.42 | $8.78 |
| Maximum drawdown | -$26,640.00 | -$2,680.00 |

The NQ Profit Factor exceeded frozen EXP-007 by 0.039767. No fixed
minimum improvement amount was imposed.

## Temporal and cost evidence

Four of five anchored test folds were profitable, with combined
fold-selected NQ net profit of $59,132.50.

The final selected candidate was profitable in four of 2021–2025 and
generated $89,640 combined NQ net profit over those years.

At two ticks of slippage per side, NQ remained profitable with
Profit Factor 1.140491 and net profit of $92,862.50.

## Statistical evidence

The locked selection-aware NQ MCPT used 1,000 permutations and seed 48.
Every permutation ran all 27 candidates and repeated the same eligibility,
neighbour-stability and selection procedure.

One hundred thirty-eight permuted optimizations produced a selected
Profit Factor at least as high as the real selected value.

`p = (1 + 138) / (1 + 1000) = 0.138861`

The locked maximum passing value was 0.050000. This was the only failed
gate.

The report-only trade bootstrap also retained uncertainty: the 95%
interval for average trade crossed zero and the Profit Factor interval
crossed 1.0.

## Interpretation

The selected geometry was profitable, cost-resilient, neighbour-stable,
stronger than EXP-007 and reasonably consistent through time. However,
similarly strong selected outcomes were not rare enough after accounting
for the complete 27-candidate search.

The grid, seed, permutation count, selection procedure and decision
threshold may not be changed after observing the result. Historical
2019–2025 evidence was exploratory because those years had already been
viewed.

No live trading is authorized. Any further strategy or position-sizing
research must be a separate preregistered experiment.
