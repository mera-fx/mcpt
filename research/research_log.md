# Experiment 001

## Date
2026-07-10

## Hypothesis
What do I believe?

## Reason
Why do I believe it?

## Strategy
What strategy am I testing?

## Data
What market?
What timeframe?
What dates?

## Tests Performed
- In-sample
- Walk-forward
- Monte Carlo
- Parameter sensitivity
- etc.

## Results

Profit Factor:

Max Drawdown:

Trades:

P-Value:

Notes:

## Conclusion

Accepted?

Rejected?

Needs more investigation?

# EXP-001 — Donchian Baseline

## Hypothesis

BTCUSDT may exhibit trend persistence that can be captured using a
Donchian closing-price breakout.

## Data

- Instrument: BTCUSDT spot
- Exchange data source: Binance
- Timeframe: 1 hour
- Test period: 2018-01-01 through 2021-12-31
- Rows in complete dataset: 77,856
- Duplicate timestamps: 0
- Detected gaps in complete dataset: 28

## Method

Tested Donchian lookbacks from 12 through 168 and selected the value
with the highest in-sample return profit factor.

## Baseline Results

- Best lookback: 49
- In-sample profit factor: 1.049
- Trading costs included: No
- Monte Carlo permutation test: Not yet
- Walk-forward test: Not yet

## Initial Conclusion

The in-sample result is weak and is not sufficient evidence of an edge.
The strategy requires Monte Carlo, walk-forward, parameter-sensitivity,
data-quality, and transaction-cost testing.

## Next Idea

## MCPT Results — Initial Run

- Permutations: 100
- Best real lookback: 49
- Best real profit factor: 1.0488
- Median optimized permutation PF: 1.0247
- Maximum optimized permutation PF: 1.0633
- Permutations equal to or better than real: 4
- MCPT p-value: 0.0495

## Interpretation

The real optimized result exceeded approximately 95% of the optimized
randomized-market results. This is preliminary evidence that the real
market ordering may contain exploitable trend structure.

However, the result is borderline, based on only 100 permutations, and
the Profit Factor is weak before trading costs. No conclusion about
tradability can be made yet.

## Status

Needs further investigation.

## MCPT Results — Final Run

- Permutations: 1,000
- Best real lookback: 49
- Best real profit factor: 1.0488
- Median optimized permutation PF: 1.0239
- Maximum optimized permutation PF: 1.0889
- Permutations equal to or better than real: 52
- MCPT p-value: 0.0529

## Interpretation

The optimized real-market result was stronger than approximately
94.8% of the optimized randomized-market results.

The result is close to, but does not pass, the conventional 5%
significance threshold. The earlier 100-permutation result of 0.0495
was not stable enough to support a conclusion.

The in-sample Profit Factor of 1.0488 is also economically weak before
fees and slippage.

## Status

Borderline statistical evidence. Continue to walk-forward testing,
but do not treat the strategy as validated or tradable.

## Walk-Forward Results

- Training period per optimization: approximately 4 years
- Re-optimization frequency: every 720 hourly bars
- Walk-forward period: 2022-01-05 through 2025-12-31
- Walk-forward rows: 34,966
- Walk-forward profit factor: 0.9840
- Total return before costs: -62.01%
- Maximum drawdown: -76.55%
- Position changes: 384
- Data gaps in full sample: 27

## Interpretation

The optimized Donchian approach did not remain profitable during the
walk-forward period. Its losses exceeded its gains, and it suffered a
large drawdown even before trading costs.

The earlier in-sample result and borderline MCPT result did not
translate into successful unseen performance.

## Conclusion

The current strategy specification is rejected as a robust trading
strategy.

This conclusion applies only to the exact rules, market, timeframe,
optimization range, and walk-forward process tested here.

## Status

Rejected in its current form.

## Out-of-Sample Comparison

Period: 2022-01-05 through 2025-12-31

| Method | PF | Return | Maximum Drawdown | Position Changes |
|---|---:|---:|---:|---:|
| Fixed Donchian 49 | 0.9972 | -15.36% | -65.72% | 495 |
| Walk-Forward Donchian | 0.9840 | -62.01% | -76.55% | 384 |
| Buy and Hold | 1.0108 | 90.08% | -67.38% | 1 |

## Findings

The fixed 49-hour Donchian rule did not retain its in-sample
performance, although it performed considerably better than monthly
walk-forward optimization.

Monthly re-optimization damaged performance rather than improving
adaptation. Buy and hold benefited from BTC's upward movement but
experienced a severe drawdown.

The current Profit Factor is calculated from hourly returns rather
than completed trades. Proper transaction-level accounting and costs
must be added before final conclusions about economic performance.

## Final EXP-001 Conclusion

The tested Donchian specification is rejected.

The evidence consists of:

- Weak in-sample performance
- Borderline and non-significant MCPT result
- Negative fixed-parameter out-of-sample performance
- Worse walk-forward performance
- No allowance yet for trading costs

No further parameter adjustment should be used to rescue EXP-001.

## Completed-Trade and Cost Analysis

Execution assumptions:

- Signal calculated at candle close
- Execution at next candle open
- Starting capital: 100,000
- Commission: 5 basis points per transaction side
- Slippage: 2 basis points per transaction side
- Total round-trip cost: 14 basis points

| Strategy | Trades | Win Rate | Trade PF | Avg Trade | Return | Max DD |
|---|---:|---:|---:|---:|---:|---:|
| Fixed Donchian 49 | 495 | 30.51% | 0.914 | -0.053% | -57.55% | -75.12% |
| Walk-Forward Donchian | 384 | 27.60% | 0.769 | -0.265% | -77.82% | -84.94% |
| Buy and Hold | 1 | 100.00% | Not meaningful | 89.16% | 89.16% | -67.38% |

### Long/Short Breakdown

Fixed Donchian:

- Long net profit: -8,841.68
- Short net profit: -48,709.78

Walk-forward Donchian:

- Long net profit: -51,667.28
- Short net profit: -26,147.97

## Final Interpretation

Proper completed-trade accounting and execution costs confirm that the
tested Donchian strategy has no usable out-of-sample edge.

The weak gross result was insufficient to absorb realistic trading
friction. Walk-forward re-optimization reduced performance further.

## Final Status

REJECTED.

## Robustness Analysis

### Cost Sensitivity

Both strategies were already unprofitable before transaction costs.

| Strategy | Zero-Cost Return | Zero-Cost Trade PF |
|---|---:|---:|
| Fixed Donchian 49 | -15.12% | 0.982 |
| Walk-Forward Donchian | -62.02% | 0.839 |

Transaction costs worsened the results but did not cause the failure.

### Long and Short Decomposition

Fixed Donchian:

- Long-only return: -10.27%
- Long-only PF: 0.972
- Short-only return: -52.69%
- Short-only PF: 0.866

Walk-forward Donchian:

- Long-only return: -35.06%
- Long-only PF: 0.838
- Short-only return: -65.84%
- Short-only PF: 0.764

The short side caused greater losses, but the long side was also
unprofitable.

### Year-by-Year Stability

The fixed strategy was profitable only in 2024:

- 2022: -7.83%
- 2023: -20.74%
- 2024: +49.10%
- 2025: -61.03%

The walk-forward strategy lost money in every tested year.

### Final Decision

EXP-001 is rejected.

The strategy showed weak and borderline in-sample evidence, failed
out of sample, failed walk-forward testing, failed both long and short
decomposition, and was not profitable even before trading costs.

No further parameter tuning will be used to rescue this experiment.
Any materially changed rules must be recorded as a separate experiment.

# EXP-002 — BTCUSDT Hourly Long-Only Z-Score Mean Reversion

## Hypothesis

After an unusually large hourly downside deviation from its rolling
mean, BTCUSDT may rebound enough to support a long-only
mean-reversion trade.

## Rule

- Calculate rolling mean and standard deviation
- Enter long when z-score falls below the entry threshold
- Exit when price recovers to the rolling mean
- Execute at the next candle open
- Remain flat otherwise
- No short selling

## In-Sample Optimization

Best tested parameters:

- Lookback: 48 hours
- Entry threshold: 2.5 standard deviations
- Best bar-return Profit Factor: 0.9835

The best optimized in-sample version was already unprofitable.

## Out-of-Sample Results

| Test | Return | Max DD | Trades | Win Rate | Trade PF | Avg Trade |
|---|---:|---:|---:|---:|---:|---:|
| Fixed | -58.06% | -62.69% | 225 | 64.00% | 0.695 | -0.311% |
| Walk-forward | -52.57% | -63.10% | 418 | 67.70% | 0.760 | -0.135% |

## Interpretation

The strategy produced a high percentage of winning trades, but its
losing trades were substantially larger than its winning trades.

This is consistent with a mean-reversion strategy that collects many
small recoveries but suffers large losses when price continues moving
against the position.

The walk-forward process did not create a profitable result.

## MCPT Quick Check

- Permutations: 25
- p-value: 1.0000

The quick permutation check provided no evidence that the real market
contained a stronger optimized result than randomized markets.

A full 1,000-permutation run was not required because the strategy
already failed both in-sample and out-of-sample profitability tests.

## Final Decision

REJECTED.

No further parameter tuning will be used to rescue EXP-002.
A materially different rule must be recorded as a new experiment.

## Trade-Loss Diagnostics

### Fixed Parameters

- Trades: 225
- Win rate: 64.00%
- Average winner: +1.559%
- Average loser: -3.637%
- Payoff ratio: 0.429
- Largest loss: -23.282%
- Five largest losses represented 34.51% of gross losses
- Maximum consecutive losses: 7

The strategy required approximately a 70% win rate to offset its
average winner-to-loser relationship, but achieved only 64%.

### Walk-Forward

- Trades: 418
- Win rate: 67.70%
- Average winner: +1.087%
- Average loser: -2.698%
- Payoff ratio: 0.403
- Largest loss: -25.448%
- Five largest losses represented 27.60% of gross losses
- Maximum consecutive losses: 4

The walk-forward strategy increased the win rate but still failed to
reach the approximate 71% break-even win rate required by its payoff
ratio.

### Diagnostic Interpretation

EXP-002 displayed negative skew:

- Frequent small winning trades
- Fewer but substantially larger losing trades
- Severe tail losses exceeding 20%
- Negative expectancy despite a high win rate

The mean-reversion hypothesis produced frequent rebounds but did not
control losses when price continued trending downward.

EXP-002 remains REJECTED.