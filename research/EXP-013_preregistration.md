# EXP-013 preregistration

## Extended-context three-finalist deep validation

EXP-013 deeply measures three candidates retained after reviewing EXP-012:

1. `gap_fade_0p50_1r`
2. `premarket_continuation_0p50_time`
3. `premarket_continuation_0p75_time`

No new parameters, strategies or exits are introduced.

## Why these three were retained

The gap-fade 0.50 / 1R candidate best matched the user's preference for a
higher win rate and lower drawdown. In EXP-012 it had 186 NQ trades, a
59.68% win rate, PF 1.530924, $34,810 net profit and $5,080 maximum
drawdown.

The premarket 0.50 time-exit candidate had the strongest broader-sample
performance: 291 NQ trades, PF 1.736374, $121,255 net profit and $20,695
maximum drawdown.

The premarket 0.75 time-exit candidate had the strongest raw PF and
net-profit-to-drawdown measurement: PF 2.023738 and 7.98 net/DD. It had
only 88 NQ trades, so its low-sample warning is permanently retained.

These are post-result judgments. The candidates were not independently
preselected, and none is called a winner.

## Locked strategy rules

### Gap fade 0.50 / 1R

- Calculate the opening gap from the immediately preceding complete cash
  session close.
- Divide the absolute gap by that prior cash session's high-low range.
- Require a gap fraction of at least 0.50.
- Require the completed 09:30-09:35 bar to move opposite the gap.
- Enter at the 09:35 bar open toward the prior close.
- Stop at the outer extreme of the first cash bar.
- Target 1R from actual entry; otherwise exit at 15:55.

### Premarket continuation 0.50 and 0.75 / time

- Measure the final 90-minute premarket move.
- Divide absolute premarket close-minus-open by the premarket high-low range.
- Require a drive fraction of at least 0.50 or 0.75.
- Require the completed 09:30-09:35 bar to agree with the premarket direction.
- Enter at the 09:35 bar open.
- Stop at the opposite extreme of the first cash bar.
- Use no profit target; exit at 15:55.

All entries remain in the cash session. Each candidate can make at most one
trade per session.

## Common data and execution

- Frozen 1,331-session NQ/MNQ sample from 2020-01-03 through 2025-12-31.
- NQ primary measurement and MNQ implementation comparison.
- Extended-session information is context only.
- Five-minute completed signals and chronological one-minute execution.
- Conservative stop-first handling when stop and target occur in one minute.
- Fixed one-contract sizing.
- One tick of base slippage per side and the existing commissions.
- NQ zero-, one- and two-tick cost sensitivity.
- No volatility targeting.

## Anchored walk-forward measurement

Four folds test 2022, 2023, 2024 and 2025. Each fold trains on all earlier
available sessions and reselects among the three locked candidates. Training
eligibility requires at least 20 trades, PF above 1.0 and positive net profit.
If none qualifies, the fold is preserved as unselected with zero test trades.

These folds are temporal measurements, not untouched out-of-sample evidence,
because the full 2020-2025 results were already viewed in EXP-012.

## Discovery-wide permutation test

The primary MCPT runs 1,000 session-aware NQ permutations using seed 53.
Every permutation reruns all 24 EXP-012 candidates under the same rules and
costs. The primary statistic is the maximum Profit Factor across all 24.

The null is constructed from the frozen 1,320 active one-minute slots in each
18:00-15:59 extended session. For every exact time-of-day slot, log open gaps,
log close moves, high excursions, low excursions and volume are independently
shuffled across complete sessions. Prices are then reconstructed
chronologically from the first-session open. This preserves each slot's
time-of-day distribution while destroying the cross-slot and cross-session
alignment that the strategies attempt to exploit.

This directly adjusts the null distribution for searching 24 candidates by
Profit Factor. Fixed-candidate p-values for the three finalists are secondary
diagnostics.

The MCPT still cannot make the work independent: its statistic and the
finalist-review rules were locked after viewing EXP-012. That limitation must
remain visible in every conclusion.

## Bootstrap and evidence context

Each finalist receives 10,000 bootstrap resamples using seed 5301. Intervals
are measurements, not standalone gates.

The report may use secondary context labels:

- **Strong historical evidence:** discovery-wide p-value at most 0.05, at
  least three profitable walk-forward folds, positive combined fold profit,
  profitable selected NQ and MNQ results, and positive two-tick NQ profit.
- **Promising but uncertain:** p-value at most 0.10, at least two profitable
  folds, positive combined fold profit, profitable selected NQ result and
  positive two-tick NQ profit.
- Otherwise: weak or inconclusive historical evidence.

No threshold creates a lifecycle rejection or trading authorization. All
measurements and all three candidates remain visible.

## Reporting standard

The report must explain what was tested, how it was tested, what happened and
why in plain English. It includes strategy and normalized NQ benchmark equity,
drawdown, annual/monthly/rolling measurements, trade distributions, profit
concentration, costs, NQ/MNQ agreement, walk-forward folds, bootstrap
intervals and discovery-wide MCPT.

Charts use solid opaque white canvases. Positive numbers are neutral, adverse
values use red text, and green is reserved for status words.

## Limits

EXP-013 is exploratory historical deep validation. It cannot independently
confirm an edge, authorize paper trading or authorize live trading. New
parameters, changed seeds, changed costs or a different shortlist require a
new experiment.
