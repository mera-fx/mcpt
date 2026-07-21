# EXP-014 protected implementation

This implementation measures the behaviour and complementarity definitions
locked in the EXP-014 preregistration. It reconstructs the three unchanged
EXP-013 NQ strategies from the frozen one-minute data and refuses to write a
final result unless their trade counts, long/short counts, Profit Factors,
win rates, average trades, net profits, drawdowns and net-profit-to-drawdown
ratios match the frozen EXP-013 record.

The engine produces:

- enriched candidate trade ledgers with entry-known regimes, holding bands,
  context bands and pre-exit MFE/MAE;
- year, month, direction, exit, holding-time, context and regime breakdowns;
- explicit 2025 comparisons against 2020-2024 and 2022-2024;
- rolling 20-trade and 50-trade diagnostics fixed before the result;
- profit-concentration, best-trade-removal and worst-window measurements;
- session-based drawdown duration, recovery and underwater diagnostics;
- pairwise P&L, signal-direction and drawdown-overlap measurements;
- two unweighted arithmetic research-sleeve comparisons; and
- a plain-English, vertically arranged report with opaque white chart canvases.

Every one of the 1,331 included sessions remains on the session P&L axis, with
zero on no-trade days. Monthly tables include zero-trade months. Trend and
volatility labels use only prior completed sessions. The 2020-2021 volatility
median is reported but cannot be turned into a trading filter under EXP-014.

EXP-013's MCPT, bootstrap and walk-forward evidence is hash-verified and shown
as frozen context. Those expensive tests are not rerun.

No parameter, regime filter, weight, candidate or winner is selected. The two
sleeve pairs are arithmetic research sleeves, not executable netting-account
instructions. No paper or live trading is authorized.
