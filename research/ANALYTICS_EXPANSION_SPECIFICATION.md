# Protected Analytics Expansion Specification

## Purpose

The analytics expansion calculates every applicable measurement from the
project's existing frozen trade ledgers, equity series and aligned benchmark
evidence. It changes reporting only. It does not change a strategy, candidate,
parameter, cost model, lifecycle decision or research result.

No strategy, optimization, walk-forward selection, MCPT, bootstrap, paper
simulation, live-trading process or market-data request may run as part of the
analytics rebuild.

## Metric families

1. Performance summary with All / Long / Short columns
2. Total trade analysis
3. Performance ratios
4. Time and market-exposure analysis
5. Equity and drawdown analysis
6. Winning and losing trade distributions
7. Streak and trade-series analysis
8. Outlier and concentration analysis
9. MAE and MFE
10. Monthly and annual analysis
11. Benchmark and value-added analysis
12. Existing frozen robustness evidence

## Availability language

If a metric cannot be calculated from a particular frozen dataset, its report
must display:

> **Not available from this experiment’s frozen evidence**

For EXP-015 through EXP-018, strategy-performance sections must display:

> **Not applicable — data-source qualification experiment**

Unavailable values may not be silently omitted, estimated from unrelated
evidence or reconstructed through a new strategy or market-data run.

## Evidence boundaries

- EXP-001 through EXP-014 expose strategy series.
- EXP-015 through EXP-018 are data-source qualification experiments.
- EXP-004 has no aligned frozen benchmark in the permitted reporting evidence.
- Only EXP-014 enriched ledgers contain frozen pre-exit MAE and MFE.
- EXP-009 and EXP-012 tournament candidates remain separate.
- EXP-010 and EXP-013 finalists remain separate.
- The six EXP-011 signal-by-sizing rows remain separate.
- EXP-014 arithmetic sleeve pairs remain diagnostics and are not executable
  portfolios.
- NQ and MNQ measurements remain separate.

## Ratio conventions

- Percentage return, CAGR, Calmar and percentage drawdown use an explicitly
  labelled normalized reference-capital model.
- Return on maximum strategy drawdown is net profit divided by the absolute
  maximum cash drawdown. The All column uses the registered equity path;
  Long and Short use clearly labelled direction-only closed-trade paths.
- Annual rate of return is CAGR over the registered analysis span. Monthly
  rate of return is its equivalent compound monthly rate:
  `(1 + annual rate)^(1/12) - 1`.
- Sharpe, Sortino and downside deviation use aligned daily or session returns,
  not raw trade P&L presented as returns.
- BTC and exchange-session strategies use separately declared annualization
  assumptions.
- SQN is labelled as a trade-series measurement.
- A normalized futures price benchmark is not described as a literal
  one-contract buy-and-hold futures portfolio.

### Declared reference capital

- NQ and the BTC/QQQ series use USD 100,000.
- Ordinary MNQ transfer, tournament and finalist series use USD 10,000,
  matching their frozen equity construction.
- The EXP-011 equal-risk sizing rows use USD 100,000 for both NQ and MNQ,
  matching that experiment's frozen sizing design.

The reference capital is a reporting denominator. It does not change a
contract quantity, trade ledger or saved research result.

## Calculated measurements

The implementation emits the following measurements when their registered
evidence supports them:

1. All / Long / Short completed trades, gross profit and loss, net profit,
   Profit Factor, win rate, average and median trade, winner and loser
   distributions, payoff, extremes, costs, trade-series drawdown, streaks and
   holding time. The summary also includes return on initial capital, maximum
   strategy drawdown in cash and percent, return on maximum strategy drawdown,
   maximum simultaneous contracts held, annual and equivalent monthly rates
   of return, and aligned buy-and-hold return when benchmark evidence exists.
2. Total trade counts, outcome and direction splits, exit-reason splits,
   transaction-cost drag and trading-session counts.
3. Normalized total return and CAGR; annualized volatility, zero-risk-free
   Sharpe, zero-target Sortino, downside deviation, Calmar, recovery factor,
   Profit Factor, payoff, expectancy, Omega and trade-series SQN.
4. Analysis duration, session participation, trade frequency, merged market
   time, market exposure and local entry-hour behaviour.
5. Ending, highest and lowest equity; cash and percentage drawdown; Ulcer and
   Pain indices; current drawdown; complete drawdown episodes and recovery
   duration.
6. Separate all-trade, winner and loser quantiles, dispersion, skewness and
   excess kurtosis.
7. Winning and losing run counts and lengths, current streak, lag-one P&L
   autocorrelation, outcome sign changes and trade-series SQN.
8. Top and bottom 1%, 5% and 10% contribution, results with the best trades
   removed, winner HHI and Gini concentration, z-score and IQR outliers.
9. For EXP-014 only: frozen pre-exit MAE, MFE, capture, realization
   efficiency, giveback and outcome splits.
10. Compounded monthly and annual normalized returns, P&L, trade counts,
    win rate, profitable-period rates, extremes and a monthly P&L matrix.
11. Aligned strategy and normalized price-benchmark return, CAGR and
    drawdown; value added, correlation, beta, zero-risk-free alpha, tracking
    error, information ratio, active win rate and up/down capture.
12. A hashed catalogue of existing decision, cost, walk-forward, grid,
    bootstrap, MCPT, calendar and review artifacts. These artifacts are not
    recomputed.

Sharpe, Sortino, downside deviation, alpha, beta, information ratio and
capture use UTC daily returns for the continuously traded BTC series and
exchange-session returns for the other series. Raw trade P&L is never treated
as a percentage-return series.

## Derived output

Calculated analytics are written outside frozen experiment result
directories:

```text
results/analytics_expansion/EXP-001/
...
results/analytics_expansion/EXP-014/
```

Each strategy series has its own `analytics.json`, `report.html` and CSV
tables. Each experiment has a summary report and machine-readable index. The
root has a cross-experiment summary, evidence manifest and navigable index.
EXP-015 through EXP-018 receive status-only pages with the required
not-applicable message; they receive no invented strategy measurements.

Long series reports provide a sticky left-hand section menu on desktop and a
responsive in-flow menu on narrow screens. Negative results and loss or
drawdown amounts are displayed in red accounting notation. The benchmark
difference formerly labelled "excess return" is displayed as "strategy minus
buy-and-hold return".

The Performance Summary includes side-by-side strategy-equity and
buy-and-hold panels. When benchmark evidence exists, both panels use the same
USD scale and aligned dates; the dashed line marks registered reference
capital. When benchmark evidence is unavailable, the frozen strategy-equity
curve remains visible and the buy-and-hold panel states that it is
unavailable. Full strategy-equity points are exported as a deterministic CSV.

The research dashboard links directly to the root analytics index. Its normal
artifact library keeps only each experiment's analytics report, summary and
machine-readable index; the per-series tables remain reachable through the
analytics report without flooding the general artifact list.

Frozen trade, equity, benchmark and existing robustness evidence is hashed
before calculation, after calculation and after output generation. Any change
aborts the build. Output is timestamp-free, deterministic and written only
beneath `results/analytics_expansion`; unchanged files are not rewritten.

## Safe commands

Read and validate every source without writing output:

```powershell
.\.venv\Scripts\python.exe build_analytics_expansion.py --preflight
```

Build the complete derived analytics:

```powershell
.\.venv\Scripts\python.exe build_analytics_expansion.py
```

An optional repeated `--experiment EXP-004` argument limits a diagnostic
build. It does not relax the frozen-evidence protections.
