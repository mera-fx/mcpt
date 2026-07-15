# EXP-006 — NQ/MNQ Structured ORB Optimization

**Status:** Pre-registered before any EXP-006 result  
**Relationship:** Separate experiment; EXP-005 remains the frozen control

## Research question

Can a deliberately small ORB grid improve risk-adjusted NQ/MNQ
performance without relying on a large parameter hunt?

Historical 2019–2025 data has already been seen during EXP-005.
Therefore, EXP-006 historical work is explicitly exploratory. Its
strongest permitted conclusion is to nominate one candidate for a
new forward paper comparison. Historical EXP-006 results cannot
authorize live trading.

## Locked grid: exactly 27 combinations

| Variable | Candidates |
|---|---|
| Opening range | 5, 15, 30 minutes |
| Final entry time | 10:30, 11:15, 12:00 New York |
| Direction | Long only, short only, both |

The frozen EXP-005 control—15-minute range, entry allowed through
12:00, both directions—is included exactly once.

Everything else remains fixed: strict completed-bar breakout,
next-open entry, opposite-range stop, entry-bar stop, one trade
per day, no reversal, 15:55 forced flat, no overnight position,
and the existing NQ/MNQ cost model.

## Selection method

Candidates must first pass minimum profitability, trade-count and
calendar-year eligibility. Eligible candidates are ranked by the
median of six locked ranks:

1. NQ Profit Factor
2. NQ net-profit-to-drawdown
3. NQ average-trade-to-cost
4. MNQ Profit Factor
5. Profitable NQ calendar years
6. Anchored walk-forward NQ net profit

A candidate cannot be accepted as an isolated peak. At least half
of its immediately adjacent grid neighbours must also be profitable.

## Walk-forward structure

Five anchored annual folds select parameters using training data
only and test them on the following year: 2021, 2022, 2023, 2024
and 2025. Test-fold reselection is prohibited.

## Selection-aware MCPT

The full test uses 1,000 NQ session-aware permutations. All 27
candidates must be evaluated inside every permutation so the null
distribution includes the same selection process used on the real
market. Optimizing only the real market is prohibited.

## Decision boundary

A historical pass may lock one candidate for future forward paper
comparison against EXP-005. Failure rejects EXP-006 and leaves the
EXP-005 control unchanged.

No live orders, new parameters, post-result filters, alternative
stops, targets, sizing changes or claims of untouched historical
confirmation are permitted.
