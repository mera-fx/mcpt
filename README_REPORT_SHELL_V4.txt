RESEARCH REPORT SHELL V4
========================

Fixes
-----
- Metric names, statistic labels and strategy-rule labels use muted bronze.
- EXP-011 summary statistics remain three compact cards instead of becoming
  long full-width bars.
- Remaining report-specific blue panels are neutralized.
- The left menu has no plus/minus markers and no expanded box styling.
- Main section titles are white, bronze while active.
- Subsection titles appear only for the active/clicked main section.
- Scroll position automatically opens and highlights the current section.
- Tables with three records or fewer use a direct metric-by-record matrix.
- Larger related sets may be grouped; groups of three or fewer use matrices.
- Compare all and Compare group open complete comparison pages in new tabs.
- The new-tab implementation writes the document directly, with Blob fallback.

Metrics scope
-------------
This package reorganizes measurements already present in each saved report.
It does not fabricate unavailable Sharpe, Sortino, MAE/MFE, time exposure,
trade-series or benchmark measurements.

A separate validated analytics expansion is required to calculate every
applicable metric family from each experiment's frozen ledgers and equity
series.

Safety
------
No strategy, optimization, MCPT, bootstrap, walk-forward, paper simulation,
live trading or market-data request is run.
