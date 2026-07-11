# EXP-003 Preregistration

## BTCUSDT Hourly Long-Only Volatility-Compression Breakout

**Status:** PRE_REGISTERED  
**Locked:** 2026-07-11  
**Implementation status:** Not implemented  
**Results viewed:** None

This document fixes the hypothesis, signal rules, parameter grid,
research periods, costs, validation sequence and pass/fail criteria
before the strategy is coded or tested.

## 1. Research question

After an unusually quiet realized-volatility regime, does an upside
price-range breakout produce positive continuation strong enough to
remain profitable after realistic costs?

### Null hypothesis

Conditioning an upside breakout on prior volatility compression does
not produce returns distinguishable from chance and does not remain
profitable out of sample after costs.

## 2. Market and position constraints

- Market: BTCUSDT spot
- Timeframe: 1 hour
- Data: `data/BTCUSDT_1h.parquet`
- Direction: long-only
- Position: either 100% long or flat
- Leverage: 1.0
- Pyramiding: prohibited
- Starting capital: 100,000
- Commission: 5 basis points per side
- Slippage: 2 basis points per side

## 3. Locked research periods

| Stage | Period |
|---|---|
| In-sample | 2018-01-01 00:00 through 2021-12-31 23:00 |
| Out-of-sample | 2022-01-01 00:00 through 2025-12-31 23:00 |
| Walk-forward training | 35,040 bars |
| Walk-forward retraining | Every 720 bars |

The effective out-of-sample start may move forward only by the
minimum number of bars needed to provide the locked walk-forward
training window. No other date changes are permitted.

## 4. Exact signal definition

At hourly close `t`:

1. Calculate `log_return[t] = log(close[t] / close[t-1])`.
2. Calculate realized volatility as the rolling population standard
   deviation of log returns over `vol_lookback` bars.
3. Calculate the compression threshold as the trailing
   `compression_quantile` of realized volatility over the previous
   2,160 bars. The threshold is shifted by one bar.
4. Mark bar `t` compressed when current realized volatility is at or
   below that threshold.
5. Mark recent compression true when at least one compressed state
   occurred during bars `t-23` through `t`.
6. Calculate the breakout level as the maximum high over the prior
   `breakout_lookback` bars, excluding bar `t`.
7. While flat, signal a long entry when recent compression is true
   and `close[t]` is above the breakout level.
8. Calculate the exit level as the minimum low over the prior
   24 bars, excluding bar `t`.
9. While long, signal an exit when `close[t]` is below the exit level
   or the position has been held for 168 bars.
10. An exit takes priority over a new entry. No same-bar exit and
    re-entry is allowed.
11. All signals execute at the next hourly open.
12. Any final open trade closes at the last available close and is
    labelled `end_of_data`.

## 5. Locked parameter grid

| Parameter | Values |
|---|---|
| `vol_lookback` | 24, 48, 72 |
| `compression_quantile` | 0.10, 0.20, 0.30 |
| `breakout_lookback` | 24, 48, 72 |

Total combinations: **27**

### Fixed preselected parameters

```text
vol_lookback = 48
compression_quantile = 0.20
breakout_lookback = 48
```

The fixed parameters are selected before viewing any EXP-003 result.

## 6. Statistical plan

- Optimization objective: in-sample next-bar log-return Profit Factor
- Quick MCPT: 25 permutations
- Full MCPT: 1,000 permutations
- Random seed: 42
- Every one of the 27 parameter combinations must be retained and
  displayed.
- Benchmarks: Cash and Buy and Hold over the same period

## 7. Quick-screen protocol

The quick screen may use **only the in-sample period**. Out-of-sample
strategy results must not be calculated or displayed before the
quick-screen decision is locked.

All gates must pass:

| Gate | Requirement |
|---|---:|
| Best in-sample bar PF | Strictly above 1.00 |
| Grid combinations with PF ≥ 1.00 | At least 6 of 27 |
| Median immediate-neighbour score | At least 95% of best score |
| 25-permutation MCPT p-value | At most 0.20 |
| Fixed-parameter in-sample completed trades | At least 50 |

### Quick-screen decision

- **Fail any gate:** mark EXP-003 REJECTED and do not inspect
  out-of-sample strategy results.
- **Pass every gate:** advance to FULL_VALIDATION and reveal the
  locked out-of-sample period once.

## 8. Full-validation protocol

All gates must pass:

| Gate | Requirement |
|---|---:|
| 1,000-permutation MCPT p-value | At most 0.05 |
| Fixed OOS total return | Above 0% |
| Fixed OOS trade PF | Above 1.00 |
| Fixed OOS completed trades | At least 30 |
| Walk-forward total return | Above 0% |
| Walk-forward trade PF | Above 1.00 |
| Walk-forward completed trades | At least 30 |
| Fixed OOS absolute maximum drawdown | At most 50% |
| Profitable OOS calendar years | At least 2 |

Cash and Buy and Hold must be reported, but Buy-and-Hold
outperformance is not mandatory because strategy exposure may differ.

### Full-validation decision

- **Fail any gate:** mark EXP-003 REJECTED and preserve it as a
  completed negative result.
- **Pass every gate:** advance to REVIEW. Paper-testing acceptance
  requires a documented review confirming every gate.

## 9. Prohibited post-result changes

The following cannot be changed after results are viewed:

- Signal definitions
- Parameter grid or fixed parameters
- Research dates
- Trading costs
- Quick-screen or full-validation gates
- Compression measure
- Entry or exit logic
- Addition of trend filters, stops or profit targets

Any altered rule set must receive a new experiment ID and a fresh
preregistration. It cannot be presented as a repaired version of
EXP-003.
