# EXP-007 Preregistration

## Fixed 30-Minute Long-Only 1R Opening Range Breakout

**Locked:** 17 July 2026  
**Status:** Pre-registered; not implemented; no EXP-007 result viewed  
**Primary evidence market:** NQ  
**Secondary implementation check:** MNQ

## Research question

Does the fixed opening-range breakout described below generate a positive,
temporally robust post-cost edge on the frozen 2019–2025 NQ/MNQ sessions?

This is a replication and independent reconstruction of a strategy idea
described in the supplied video:

`https://youtu.be/wm6XQFw1GHI`

The video's reported performance is not imported as evidence.

## Research context

Gao, Han, Li and Zhou, *Market Intraday Momentum*, Journal of Financial
Economics 129(2), 2018, DOI `10.1016/j.jfineco.2018.05.009`, provides
context for an intraday-momentum mechanism. It does not directly validate
this exact NQ breakout implementation.

Moreira and Muir, *Volatility-Managed Portfolios*, and Harvey et al.,
*The Impact of Volatility Targeting*, motivate a later sizing experiment.
EXP-007 deliberately excludes volatility targeting so signal validity and
leverage are not mixed.

## Exact fixed strategy

| Component | Locked rule |
|---|---|
| Session | 09:30–16:00 America/New_York |
| Opening range | High and low of the six complete 5-minute bars from 09:30 to 10:00 |
| Direction | Long only |
| Signal | First completed 5-minute candle closing strictly above the opening-range high |
| Entry | Next 5-minute bar open |
| Latest signal | Bar covering 13:50–13:55 |
| Latest entry | 13:55 |
| Stop | Opening-range low |
| Risk | Actual entry minus opening-range low |
| Target | Actual entry plus 1R |
| Time exit | 14:00 one-minute bar open |
| Trades | Maximum one per session |
| Re-entry | Disabled |
| Delta confirmation | Disabled |
| Other filters | None |
| Position size | Fixed one NQ or one MNQ contract |

A trade with nonpositive risk is not entered. Entry gaps are not filtered;
stop distance and target are calculated from the actual entry price.

## One-minute execution rules

Five-minute bars determine the completed breakout signal. Frozen one-minute
bars determine stop, target and time-exit ordering.

Minutes are evaluated chronologically, including the entry minute.

- A stop gap fills at the one-minute opening price.
- A stop touch otherwise fills at the stop.
- A target gap receives no favourable price improvement and fills at target.
- A target touch fills at target.
- When stop and target both appear inside the same one-minute bar, the stop
  is assumed first.
- A position still open exits at the 14:00 one-minute opening price.

## Costs

The frozen EXP-005 contract and cost model is reused:

| Market | Multiplier | Fees/side | Base slippage/side | Base round trip |
|---|---:|---:|---:|---:|
| NQ | $20/point | $2.50 | 1 tick | $15 |
| MNQ | $2/point | $1.00 | 1 tick | $3 |

Cost sensitivity is reported at 0, 1 and 2 ticks per side. Positive NQ
performance at two ticks per side is a locked decision gate.

## Temporal robustness

Parameters never change and are never reselected.

The full historical result is reported, together with five annual evaluation
blocks: 2021, 2022, 2023, 2024 and 2025. At least three of the five NQ blocks
and their combined NQ result must be profitable.

These blocks are not described as untouched out-of-sample data because the
2019–2025 history has already been viewed during prior experiments.

## Session-aware MCPT

NQ receives 1,000 session-aware one-minute permutations using seed 47.

There is no optimization inside a permutation because EXP-007 has exactly
one fixed rule set. The test statistic is completed-trade Profit Factor.

`p = (1 + permutations with PF >= real PF) / (1 + 1000)`

The maximum passing p-value is 0.05.

## Bootstrap diagnostics

Ten thousand completed-trade bootstrap resamples use seed 4701. The 95%
percentile intervals for average trade and Profit Factor are reported but
are not decision gates.

## Locked decision gates

Every gate is required:

1. NQ post-cost Profit Factor strictly above 1.0.
2. NQ net profit strictly above zero.
3. NQ average trade strictly above zero.
4. At least 500 completed NQ trades.
5. At least three of five annual NQ evaluation blocks profitable.
6. Combined 2021–2025 NQ net profit strictly above zero.
7. NQ session-aware MCPT p-value no greater than 0.05.
8. NQ net profit remains positive at two ticks of slippage per side.
9. MNQ post-cost Profit Factor strictly above 1.0.
10. MNQ net profit strictly above zero.

There is deliberately **no required Profit Factor improvement over EXP-005**.
EXP-007 is judged as a fixed strategy on absolute evidence, not as a
replacement optimization.

Passing can only lock the fixed rules for forward paper comparison. It
cannot authorize live trading. Failure preserves EXP-007 as a negative
result without changing its rules.

## Separate future experiments

Exit-geometry optimization and volatility-targeted position sizing are not
part of EXP-007. Each requires its own preregistration after EXP-007 is
frozen.

## Prohibited actions

EXP-005 and EXP-006 may not be changed. EXP-007 parameters, exits, filters,
direction, sizing, decision gates and permutation count may not be changed
after results are viewed. No historical EXP-007 result may authorize live
trading.
