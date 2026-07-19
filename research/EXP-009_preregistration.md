# EXP-009 Preregistration

## NQ/MNQ Multi-Strategy Discovery Tournament

Locked on 2026-07-19 before any EXP-009 strategy result was calculated.

## Purpose

EXP-009 measures several structurally different intraday strategies under
one common standard. It is not a pass/fail validation and will not name an
automatic winner.

The main question is:

> Which reproducible strategy families offer the most attractive combination
> of profitability, win rate, average trade, drawdown, consistency, cost
> resilience and practical trading behaviour?

## Data boundary

- NQ is the primary measurement market.
- MNQ is a secondary implementation comparison, not independent confirmation.
- The frozen EXP-005 sessions from 2019-05-06 through 2025-12-31 are reused.
- There are 1,639 complete cash sessions and 390 one-minute bars per session.
- Available fields are OHLCV, session date and minute slot.
- The files cover 09:30-16:00 New York only.

Overnight gap continuation and gap-fade strategies are excluded because the
frozen files do not contain a verified overnight session or prior settlement.
Order-flow delta strategies are excluded because delta is absent from OHLCV.

## Common execution

- Signals use completed five-minute bars.
- Entries occur at the next five-minute opening price.
- Stops and targets are evaluated chronologically with one-minute bars.
- A gap through a stop fills at the one-minute opening price.
- When a one-minute bar contains both stop and target, the stop is applied first.
- Every candidate is flat by the 15:55 one-minute opening price.
- Maximum one completed trade per candidate per session.
- Fixed one NQ or MNQ contract; no volatility targeting.
- Base costs are unchanged from EXP-008.
- NQ is also reported at zero and two ticks of slippage per side.

## Candidate budget

Exactly six families and four candidates per family are locked: 24 candidates.

### 1. ORB pullback continuation

Use a 30-minute opening range. After the first completed close outside the
range, wait up to 30 minutes for a retest that trades through the broken
boundary but closes beyond it again. Enter next open, stop at the opening-range
midpoint and test 1R/1.5R targets with long-only and both-direction variants.

### 2. Failed ORB reversal

Use a 30-minute opening range. After the first close outside, require a close
back inside within 30 or 60 minutes. Enter the reversal next open, stop beyond
the excursion extreme and test 1R/1.5R targets.

### 3. VWAP mean reversion

After 10:30, identify closes outside a 1.5 or 2.0 session VWAP standard-deviation
band. Enter toward VWAP after the first completed close back inside the band.
Stop beyond the excursion extreme and exit at VWAP or at 1R.

### 4. VWAP trend pullback

After 10:00, define trend by close position relative to VWAP and VWAP slope
over three completed five-minute bars. Enter after a VWAP touch and either one
or two confirming closes. Stop beyond the pullback extreme and test 1R/1.5R.

### 5. Intraday compression breakout

After 10:30, find the earliest completed rolling 30-minute range no wider than
0.50 or 0.75 of the initial 30-minute opening range. Watch for a breakout for
60 minutes, stop at the opposite compression boundary and test 1R/1.5R.

### 6. Opening-drive continuation

Measure the first-30-minute close-to-open move relative to that period's total
range. Trade the direction of the drive when the fraction reaches 0.50 or 0.75.
Use the opposite opening-range boundary as the stop and compare time-only exits
with a 1.5R-or-time exit.

The exact machine-readable candidate list is stored in
`exp009_preregistration.py`.

## Measurement standard

Every candidate receives the same detailed report:

- Profit Factor, net profit, win rate, average/median trade and payoff ratio
- Drawdown depth, duration and recovery
- Losing streaks and worst rolling 20/50/100-trade results
- Annual, monthly and rolling consistency
- Trades per year, session participation and holding time
- Entry times, exit times and exit reasons
- Profit concentration and trade distribution
- NQ/MNQ agreement and NQ cost sensitivity
- Normalized NQ benchmark comparison

Reliability flags are context, not rejection:

- fewer than 150 trades;
- activity in fewer than three years;
- non-positive NQ net profit at two ticks;
- NQ and MNQ Profit Factors on opposite sides of 1.0.

## Review and later validation

EXP-009 has no composite score, automatic winner or formal acceptance gate.
All 24 candidates remain visible. Pareto views compare return, win rate,
drawdown, consistency, cost resilience and practical behaviour.

After reviewing the full evidence, the user may choose at most three personally
attractive finalists. That choice does not confirm an edge. Each finalist must
receive a new experiment ID and its own preregistered optimization,
selection-aware MCPT, bootstrap and deeper validation.

EXP-009 cannot authorize paper or live trading.

