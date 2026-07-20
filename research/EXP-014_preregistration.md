# EXP-014 — Finalist Behaviour and Complementarity Preregistration

## Purpose

EXP-014 will explain the three frozen EXP-013 finalists rather than search
for another winning parameter. It will measure why their win rates,
drawdowns and payoff profiles differ, what weakened during 2025, and
whether gap fade and premarket continuation tend to make and lose money at
different times.

No EXP-014 result was viewed before this document was locked.

## Strategies remain unchanged

1. `gap_fade_0p50_1r`
2. `premarket_continuation_0p50_time`
3. `premarket_continuation_0p75_time`

The entries, stops, targets, time exits, costs and fixed one-contract
exposure remain exactly as measured in EXP-013. Exact trade ledgers may be
reconstructed only with the frozen EXP-012 engine and data. Their summary
measurements must match EXP-013 before the study can write a final result.

## What will be measured

For each strategy, the report will show performance by year, month,
direction, exit reason, holding-time band and locked context-strength band.
It will measure trade concentration, losing streaks, drawdown duration,
recovery, MFE, MAE and results after removing the best 1, 5 and 10 trades.

The 2025 loss will be compared with both 2020–2024 and 2022–2024. The
comparison will separate changes in trade count, win rate, average winner,
average loser, payoff, direction and exit mix.

Two entry-known market descriptions are locked:

- Trend: the sign of the prior 20-session NQ close-to-close return.
- Volatility: the prior 20-session return standard deviation, split at the
  median measured only in the 2020–2021 calibration period.

These are descriptive labels only. EXP-014 may not turn a favourable
historical regime into a new trading filter.

## Overlap and complementarity

All three strategy pairs will be measured on the same 1,331-session axis,
using zero P&L when a strategy does not trade. The report will show P&L and
drawdown correlation, overlapping signals, same- and opposite-direction
signals, joint wins/losses and simultaneous underwater periods.

Two arithmetic research-sleeve pairs are locked:

1. gap fade 0.50 / 1R plus premarket continuation 0.50 / time
2. gap fade 0.50 / 1R plus premarket continuation 0.75 / time

Each active sleeve contributes one contract. No weights are optimized. The
two nested premarket candidates are not combined, and all three strategies
are not combined. Opposing same-instrument trades may offset economically,
so these arithmetic sleeves are diagnostics—not an executable single
netting-account design.

## Interpretation boundary

EXP-014 has no pass/fail gate, composite score or automatic winner. It will
reuse EXP-013's frozen MCPT, bootstrap and walk-forward evidence without
rerunning them. It cannot claim independent confirmation and cannot
authorize paper or live trading.

The final report must explain the rules and fraction thresholds in plain
English, keep positive numbers neutral, use red for adverse measurements,
reserve green for status words and save every chart on an opaque white
canvas.
