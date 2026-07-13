# EXP-004 Preregistration

## QQQ 5-Minute Opening Range Breakout

**Status:** PRE_REGISTERED  
**Locked:** 2026-07-13  
**Implementation status:** Not implemented  
**Data downloaded for EXP-004:** No  
**Results viewed:** None

This document fixes the QQQ opening-range hypothesis, data rules,
session handling, signal and fill assumptions, parameter grid,
research periods, session-aware permutation method and pass/fail
gates before implementation or result inspection.

## 1. Research question

After QQQ establishes its opening range, does the first confirmed
break outside that range continue far enough during the same
regular session to remain profitable after realistic costs?

### Null hypothesis

A confirmed QQQ opening-range break does not produce results
distinguishable from a session-aware random market and does not
remain profitable out of sample after costs.

## 2. Primary discovery market

- Instrument: QQQ ETF
- Bar size: 5 minutes
- Historical provider: Alpaca Market Data API
- Feed: SIP
- Adjustment: split-adjusted
- Source timestamps: UTC
- Research timezone: America/New_York
- Included session: 09:30–16:00 ET regular session
- Complete full session: exactly 78 bars
- Scheduled early closes: excluded
- Missing or incomplete sessions: excluded
- Missing-bar filling: prohibited
- Overnight positions: prohibited
- Maximum trades: one per session
- Position: 100% long, 100% short, or flat
- Leverage: 1.0
- Pyramiding: prohibited

The downloader must explicitly request historical SIP data. No
trading API permissions or brokerage connection are part of this
experiment.

## 3. Locked research periods

| Stage | Sessions |
|---|---|
| In-sample | 2019-01-02 through 2022-12-30 |
| Out-of-sample | 2023-01-03 through 2025-12-31 |
| Walk-forward training | Previous 504 complete sessions |
| Walk-forward retraining | Every 21 complete sessions |

The OOS start may move forward only by the minimum number of
official full sessions required for the 504-session training
window. No other date changes are permitted.

## 4. Exact strategy definition

For each complete QQQ regular session:

1. Build the opening range from the first `opening_range_minutes`
   beginning at 09:30 ET.
2. Fix the range high and low after its final opening-range bar.
3. The first eligible signal is the first completed 5-minute bar
   after the opening-range window.
4. Signal long when an eligible bar closes strictly above the
   opening-range high.
5. Signal short when an eligible bar closes strictly below the
   opening-range low.
6. `direction_mode` controls whether long, short, or the first
   breakout in either direction is allowed.
7. The final eligible signal bar closes at 11:55 ET. Its trade
   executes at 12:00 ET. No entry is permitted after 12:00 ET.
8. Execute the first eligible signal at the next 5-minute open.
   No maximum-gap filter is allowed.
9. Long stop: opening-range low.
10. Short stop: opening-range high.
11. A gap through the stop fills at the bar open. Otherwise the
    fill is the range boundary when that bar reaches it.
12. The entry bar may stop out after entry at its open.
13. Force any remaining position flat at the 15:55 ET bar open.
14. No reversal or second trade is allowed that session.
15. Every included session must finish flat.

No profit target, trailing stop, volume filter, gap filter, ATR
filter, trend filter, news filter or day-of-week filter is part of
EXP-004.

## 5. Locked parameter grid

| Parameter | Values |
|---|---|
| `opening_range_minutes` | 5, 15, 30 |
| `direction_mode` | long_only, short_only, both |

Total combinations: **9**

### Fixed preselected parameters

```text
opening_range_minutes = 15
direction_mode = both
```

## 6. Costs and sizing

```text
Starting capital:                 100,000
Commission/fees per side:        0.5 bps
Slippage per side:               1.0 bps
Total modeled cost per side:     1.5 bps
Gross exposure while positioned: 100%
```

QQQ is assumed available to borrow for an unlevered intraday
short during historical research. Borrow-availability failures
must be monitored during any later paper test.

## 7. Optimization and session-aware MCPT

Primary objective: completed-trade Profit Factor after costs.

A parameter combination is valid only with at least 100 completed
in-sample trades.

Tie-break order:

1. Higher completed-trade Profit Factor
2. Higher total net return
3. Lower absolute maximum drawdown
4. Original preregistered grid order

### Permutation method

Standard continuous-market permutation is not valid for ORB
because the strategy depends on time of day and session boundaries.

EXP-004 uses a **time-of-day-stratified session permutation**:

- Relative OHLC components for each 5-minute slot are independently
  permuted across complete sessions.
- Session-opening/overnight gaps are permuted separately.
- Synthetic sessions are rebuilt in chronological slot order.
- Every synthetic session retains exactly 78 bars.
- The 09:30 distribution remains 09:30 data, the 09:35
  distribution remains 09:35 data, and so on.
- Regular-session and overnight components are never mixed.
- All nine parameter combinations are optimized on every
  permutation.
- Numbered deterministic seeds and serial/multicore parity are
  required.

```text
Quick MCPT: 25 permutations
Full MCPT:  1,000 permutations
Random seed: 44
```

## 8. Quick-screen gates

The quick screen may use only in-sample sessions. OOS trades,
returns, charts and parameter scores must not be calculated or
displayed before the decision is locked.

All gates must pass:

| Gate | Requirement |
|---|---:|
| Best IS completed-trade PF | Strictly above 1.10 |
| Fixed IS completed-trade PF | Strictly above 1.05 |
| Parameter combinations with PF ≥ 1.00 | At least 3 of 9 |
| 25-permutation MCPT p-value | At most 0.20 |
| Fixed IS completed trades | At least 250 |
| Fixed IS long trades | At least 50 |
| Fixed IS short trades | At least 50 |
| Invalid sessions included | 0 |

Fail any gate: mark EXP-004 `REJECTED` and do not inspect OOS
strategy results.

Pass all gates: advance once to `FULL_VALIDATION`.

## 9. Full-validation gates

All gates must pass:

| Gate | Requirement |
|---|---:|
| 1,000-permutation MCPT p-value | At most 0.05 |
| Fixed OOS total return | Above 0% |
| Fixed OOS trade PF | Strictly above 1.05 |
| Fixed OOS completed trades | At least 150 |
| Walk-forward total return | Above 0% |
| Walk-forward trade PF | Above 1.00 |
| Walk-forward completed trades | At least 150 |
| Fixed OOS absolute maximum drawdown | At most 25% |
| Profitable OOS calendar years | At least 2 |
| Invalid sessions included | 0 |

Report Cash, QQQ Buy and Hold and a regular-session always-long
benchmark. Buy-and-Hold outperformance is context rather than a
mandatory gate because EXP-004 carries no overnight exposure.

## 10. Cross-market plan

EXP-004 is a **QQQ-only discovery experiment**. SPY, NQ, MNQ, ES
and MES results cannot influence its parameters or rules.

After EXP-004 is finished, separate locked transfer experiments
are planned:

| Experiment | Markets | Rule |
|---|---|---|
| EXP-005 | NQ and MNQ | Apply fixed EXP-004 signal rules without reoptimization |
| EXP-006 | SPY | Apply fixed EXP-004 signal rules without reoptimization |
| EXP-007 | ES and MES | Apply fixed EXP-004 signal rules without reoptimization |

Futures experiments require separately locked contract-roll and
futures-cost assumptions, but may not change the ORB signal rules
merely because transfer results are weak.

## 11. Prohibited post-result changes

After results are viewed, EXP-004 cannot add or alter:

- Opening-range duration values
- Direction modes
- Entry deadline
- Next-open execution
- Range-boundary stop
- Forced-flat time
- One-trade-per-session limit
- Costs, dates or validation gates
- Volume, gap, ATR, moving-average or news filters
- Profit targets or trailing stops

Any altered rule set requires a new experiment ID and a new
preregistration.
