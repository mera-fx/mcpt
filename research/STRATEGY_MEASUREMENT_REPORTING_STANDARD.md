# Strategy Measurement Reporting Standard

## Purpose

A strategy report must first explain and measure the strategy. A lifecycle decision
or failed gate limits the claim that can be made about the evidence; it must not
replace the underlying performance, risk, consistency, robustness and practical
trading measurements.

This reporting upgrade is read-only with respect to frozen research. It may rebuild
derived HTML, charts and comparison tables from saved files, but it may not rerun a
strategy, optimization, walk-forward selection, bootstrap or MCPT.

## Required report order

1. Plain-English overview
2. What happened and why
3. What and how was tested
4. All / long / short performance table
5. Strategy versus normalized market benchmark
6. Equity, drawdown and recovery
7. Monthly, annual and rolling consistency
8. Entry, exit and holding-time behaviour
9. Trade distribution and profit concentration
10. Cost, walk-forward, parameter and statistical robustness
11. Formal lifecycle and decision-gate context

The layout is single-column and full-width from top to bottom.

## Required comparison benchmark

The report includes a normalized NQ session-close price path beginning at the same
$100,000 reporting value as the NQ strategy equity. This is a descriptive
buy-and-hold-style price comparator. It is not a tradable one-contract
continuous-futures backtest because contract-roll, financing, margin and
position-sizing assumptions are not modeled.

The benchmark is used to make the following visually clear:

- whether the strategy kept pace with the underlying market price path;
- whether it reduced drawdown;
- when strategy performance diverged from the market;
- whether the strategy's value is return, risk reduction, or both.

## Continuous measurements

The dashboard compares strategies using continuous measurements rather than only
accepted/rejected labels:

- Profit Factor
- win rate
- average trade
- net profit
- maximum drawdown in dollars and percent
- net profit divided by maximum drawdown
- average trade relative to average cost
- profitable months
- maximum losing streak
- holding time
- longest drawdown
- session participation and trades per year
- strategy and benchmark return
- cost stress
- walk-forward evidence
- MCPT p-value and percentile

Lifecycle status and failed gates remain visible as research context.

## Frozen-result protection

The rebuild command hashes every decision, trade, equity and diagnostic input before
and after report generation. A change to any protected input stops the build.
The lifecycle registry is read but never edited.

## Dashboard separation and colour semantics

The research hub remains a compact experiment and artifact index. Strategy comparison
is generated as a separate page at
`reports/research_dashboard/strategy_comparison.html` and is opened from a dedicated
navigation tab. The full comparison table and charts must not be inserted into the
main dashboard flow.

Colour is used only on selected printed text:

- green is reserved for status words such as Pass, Accepted and Locked;
- favourable numeric values remain in the normal text colour;
- losses, drawdowns, failed evidence and rejected decisions use red text;
- cells, rows, cards, status pills, borders and backgrounds remain neutral;
- blue remains reserved for navigation, headings and row labels.

Every coloured value retains its exact printed number and label so the report remains
readable without colour.
