from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, Mapping
from unittest.mock import patch

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import exp009_report as shared_report
from exp009_engine import Exp009Result
from exp012_engine import Exp012Arrays
from exp012_measurements import family_measurement_summary
from exp012_preregistration import get_exp012_preregistration
from report_chart_style import save_report_figure


FAMILY_LABELS = {
    "gap_continuation": "Gap continuation",
    "gap_fade": "Gap fade",
    "overnight_momentum_continuation": (
        "Overnight momentum continuation"
    ),
    "overnight_inventory_reversal": "Overnight inventory reversal",
    "overnight_range_breakout": "Overnight range breakout",
    "premarket_momentum_continuation": (
        "Premarket momentum continuation"
    ),
}


def _candidate_parameter_table(family_id: str) -> str:
    prereg = get_exp012_preregistration()
    candidates = [
        candidate
        for candidate in prereg["candidate_budget"]["candidates"]
        if candidate["family_id"] == family_id
    ]
    return shared_report._table_html(pd.DataFrame(candidates))


def _save_context_distributions(
    arrays: Exp012Arrays,
    report_dir: Path,
) -> Path:
    figure, axes = plt.subplots(1, 3, figsize=(14, 4.8))
    series = [
        (
            arrays.gap_fraction,
            "Opening-gap fraction",
            "Gap / previous cash range",
        ),
        (
            arrays.overnight_drive_fraction,
            "Overnight drive fraction",
            "|18:00 to 09:29 move| / overnight range",
        ),
        (
            arrays.premarket_drive_fraction,
            "Premarket drive fraction",
            "|08:00 to 09:29 move| / premarket range",
        ),
    ]
    for axis, (values, title, x_label) in zip(axes, series):
        finite = values[np.isfinite(values)]
        axis.hist(finite, bins=35, color="#60a5fa", alpha=0.86)
        axis.axvline(0.50, color="#f59e0b", linewidth=1.2)
        axis.axvline(0.75, color="#ef4444", linewidth=1.2)
        axis.set_title(title)
        axis.set_xlabel(x_label)
        axis.set_ylabel("Sessions")
        axis.grid(alpha=0.18)
    figure.tight_layout()
    path = report_dir / "extended_context_distributions.png"
    save_report_figure(figure, path, dpi=160)
    plt.close(figure)
    return path


def _save_context_coverage(
    candidate_table: pd.DataFrame,
    report_dir: Path,
) -> Path:
    local = candidate_table.sort_values(
        ["family_id", "candidate_id"], kind="stable"
    )
    positions = np.arange(len(local))
    figure, axis = plt.subplots(figsize=(14, 7))
    axis.bar(
        positions,
        local["feature_eligible_rate"],
        color="#94a3b8",
        label="Feature eligible",
    )
    axis.bar(
        positions,
        local["session_participation_rate"],
        color="#60a5fa",
        label="Completed trade",
    )
    axis.set_xticks(positions)
    axis.set_xticklabels(
        local["candidate_id"], rotation=65, ha="right", fontsize=7
    )
    axis.set_ylabel("Share of included sessions")
    axis.set_title(
        "Context eligibility and completed-trade coverage"
    )
    axis.grid(axis="y", alpha=0.2)
    axis.legend(frameon=False)
    figure.tight_layout()
    path = report_dir / "extended_context_coverage.png"
    save_report_figure(figure, path, dpi=160)
    plt.close(figure)
    return path


def build_exp012_report(
    *,
    candidate_table: pd.DataFrame,
    nq_results: Mapping[str, Exp009Result],
    arrays: Exp012Arrays,
    report_dir: Path,
    metadata: Mapping[str, Any],
) -> Path:
    if len(candidate_table) != 24:
        raise ValueError("EXP-012 report requires all 24 candidates.")
    if set(candidate_table["candidate_id"]) != set(nq_results):
        raise ValueError("EXP-012 report candidate results are incomplete.")
    if set(candidate_table["family_id"]) != set(FAMILY_LABELS):
        raise ValueError("EXP-012 report family coverage changed.")

    report_dir.mkdir(parents=True, exist_ok=True)
    family_table = family_measurement_summary(candidate_table)
    shared_report._save_pareto_charts(candidate_table, report_dir)
    shared_report._save_equity_benchmark_chart(
        nq_results, arrays.cash, report_dir
    )
    with patch.object(shared_report, "FAMILY_LABELS", FAMILY_LABELS):
        shared_report._save_family_chart(family_table, report_dir)
        for family_id in FAMILY_LABELS:
            shared_report._save_family_diagnostics(
                family_id=family_id,
                results=[
                    nq_results[candidate_id]
                    for candidate_id in candidate_table.loc[
                        candidate_table["family_id"] == family_id,
                        "candidate_id",
                    ]
                ],
                arrays=arrays.cash,
                candidate_table=candidate_table,
                report_dir=report_dir,
            )
    _save_context_distributions(arrays, report_dir)
    _save_context_coverage(candidate_table, report_dir)

    visible_columns = [
        "candidate_id",
        "family_id",
        "feature_eligible_rate",
        "signal_confirmation_rate",
        "completed_trades",
        "win_rate",
        "trade_profit_factor",
        "average_trade_usd",
        "net_profit_usd",
        "maximum_drawdown_usd",
        "net_profit_to_drawdown",
        "two_tick_net_profit_usd",
        "mnq_profit_factor",
        "profitable_year_fraction",
        "average_holding_minutes",
        "pareto_nondominated",
        "reliability_flag_count",
    ]
    prereg = get_exp012_preregistration()
    definitions = prereg["family_definitions"]
    family_sections: list[str] = []
    for family_id, label in FAMILY_LABELS.items():
        subset = candidate_table.loc[
            candidate_table["family_id"] == family_id
        ]
        profitable = int((subset["net_profit_usd"] > 0).sum())
        resilient = int(
            (subset["two_tick_net_profit_usd"] > 0).sum()
        )
        definition = definitions[family_id]
        family_sections.append(
            f'<section id="family-{html.escape(family_id)}">'
            f"<h2>{html.escape(label)}</h2>"
            f'<div class="explanation">'
            f"<h3>How this strategy works</h3>"
            f"<p>{html.escape(definition['plain_english'])}</p>"
            f"<ul>"
            f"<li><strong>Setup:</strong> "
            f"{html.escape(str(definition.get('setup', definition.get('frozen_range', 'Locked context rule.'))))}</li>"
            f"<li><strong>Signal:</strong> "
            f"{html.escape(str(definition['signal']))}</li>"
            f"<li><strong>Entry:</strong> "
            f"{html.escape(str(definition['entry']))}</li>"
            f"<li><strong>Stop:</strong> "
            f"{html.escape(str(definition['stop']))}</li>"
            f"<li><strong>Target:</strong> "
            f"{html.escape(str(definition['target']))}</li>"
            f"</ul></div>"
            f"<p><strong>What happened:</strong> {profitable} of 4 "
            f"candidates produced positive base-cost NQ net profit and "
            f"{resilient} of 4 remained positive at two ticks of "
            f"slippage per side. This describes the family; it does not "
            f"confirm an edge.</p>"
            f"<h3>Four locked versions</h3>"
            f"{_candidate_parameter_table(family_id)}"
            f'<div class="grid">'
            f'<img class="chart" src="{family_id}_equity_benchmark.png" '
            f'alt="{html.escape(label)} equity and NQ benchmark">'
            f'<img class="chart" src="{family_id}_monthly_heatmap.png" '
            f'alt="{html.escape(label)} monthly heatmap">'
            f'<img class="chart" src="{family_id}_trade_behaviour.png" '
            f'alt="{html.escape(label)} trade behaviour">'
            f'<img class="chart" src="{family_id}_profit_concentration.png" '
            f'alt="{html.escape(label)} profit concentration">'
            f"</div>"
            f"{shared_report._table_html(subset, columns=visible_columns)}"
            f"</section>"
        )

    positive = int((candidate_table["net_profit_usd"] > 0).sum())
    resilient = int(
        (candidate_table["two_tick_net_profit_usd"] > 0).sum()
    )
    nondominated = int(candidate_table["pareto_nondominated"].sum())
    flagged = int(
        (candidate_table["reliability_flag_count"] > 0).sum()
    )
    metadata_text = html.escape(
        json.dumps(dict(metadata), indent=2, default=str)
    )
    document = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>EXP-012 Extended-Hours Context Discovery</title>
<style>
:root {{
  color-scheme:dark; --bg:#07101d; --panel:#0f1b2d;
  --panel2:#132238; --text:#e5edf7; --muted:#94a3b8;
  --line:#263850; --accent:#60a5fa; --adverse:#f87171;
  --status:#4ade80;
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--text);
  font:14px/1.55 Inter,Segoe UI,Arial,sans-serif; }}
main {{ max-width:1500px; margin:auto; padding:30px; }}
section {{ background:var(--panel); border:1px solid var(--line);
  border-radius:14px; padding:22px; margin:0 0 22px; }}
h1 {{ font-size:34px; margin:0 0 8px; }}
h2 {{ color:var(--accent); margin-top:0; }}
h3 {{ margin-bottom:8px; }}
p,li {{ max-width:1100px; }}
.muted {{ color:var(--muted); }}
.status-good {{ color:var(--status); font-weight:inherit; }}
.adverse {{ color:var(--adverse); font-weight:inherit; }}
.grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr));
  gap:18px; }}
.chart {{ width:100%; border-radius:10px; background:#ffffff; }}
.table-scroll {{ overflow:auto; }}
table {{ border-collapse:collapse; width:100%; min-width:1050px; }}
th,td {{ border-bottom:1px solid var(--line); padding:9px 10px;
  text-align:right; white-space:nowrap; font-weight:400; }}
th {{ color:#bfdbfe; background:var(--panel2); position:sticky; top:0; }}
th:first-child,td:first-child,th:nth-child(2),td:nth-child(2) {{
  text-align:left;
}}
.explanation {{ background:#0a1627; border:1px solid var(--line);
  border-radius:10px; padding:16px; margin-bottom:16px; }}
pre {{ background:#081321; border:1px solid var(--line);
  border-radius:8px; padding:15px; overflow:auto; color:var(--muted); }}
@media(max-width:900px) {{ .grid {{ grid-template-columns:1fr; }}
  main {{ padding:14px; }} }}
</style>
</head>
<body><main>
<section>
  <h1>EXP-012 - Extended-Hours Context Discovery</h1>
  <p class="muted">Six families · 24 locked candidates · 1,331 aligned
  2020-2025 NQ/MNQ sessions · extended-hours context · cash-session entries</p>
  <p><span class="status-good">Measured, not validated.</span> This report
  compares strategy characteristics. It does not declare a winner, confirm
  an edge, or authorize paper or live trading.</p>
</section>
<section id="strategy-rules">
  <h2>What we tested and how</h2>
  <p>We asked whether the opening gap, the full overnight move, the final
  90-minute premarket move, or a break beyond the overnight range provides
  useful context for a cash-session trade. Overnight and premarket prices
  create the setup, but every entry and exit occurs during the regular cash
  session.</p>
  <p>Every candidate uses completed five-minute signals, enters at the next
  five-minute open, sequences stops and targets with one-minute bars, uses
  one fixed contract, applies the same base costs, and closes no later than
  15:55 New York. A same-minute stop and target is counted as a stop.</p>
  <p>The overnight cost model is not being tested. Keeping execution in the
  cash session lets the new context be measured without making an unsupported
  fill assumption about thin overnight liquidity.</p>
</section>
<section>
  <h2>How to read the fractions</h2>
  <p>A gap fraction of 0.50 means the opening gap is half as large as the
  previous cash session's full range. An overnight drive fraction of 0.75
  means the net 18:00-to-09:29 move covers 75% of that overnight session's
  total high-low range. The premarket fraction uses the same idea over
  08:00-to-09:29.</p>
  <p>Higher fractions describe a more directional move. They do not
  automatically mean a better strategy; the report measures that question.</p>
  <div class="grid">
    <img class="chart" src="extended_context_distributions.png"
         alt="Extended context feature distributions">
    <img class="chart" src="extended_context_coverage.png"
         alt="Feature eligibility and trade coverage">
  </div>
</section>
<section>
  <h2>What happened</h2>
  <p>{positive} of 24 candidates produced positive base-cost NQ net profit.
  {resilient} remained positive at two ticks of slippage per side.
  {nondominated} appear on the multi-dimensional Pareto frontier, while
  {flagged} carry at least one reliability warning. These are measurements,
  not pass/fail labels.</p>
</section>
<section>
  <h2>All candidate equity paths versus NQ</h2>
  <p>The NQ line is a normalized session-close price benchmark beginning at
  $100,000. It is not literal one-contract futures buy-and-hold P&amp;L because
  contract rolls, leverage, margin and financing are not modeled.</p>
  <img class="chart" src="candidate_equity_vs_nq_benchmark.png"
       alt="All candidate equity paths and NQ benchmark">
</section>
<section>
  <h2>Family-level measurements</h2>
  <img class="chart" src="family_measurement_comparison.png"
       alt="Family comparison">
  {shared_report._table_html(family_table)}
</section>
<section>
  <h2>Pareto comparisons</h2>
  <p>These charts show trade-offs rather than one mysterious overall score.</p>
  <div class="grid">
    <img class="chart" src="pareto_profit_factor_drawdown.png"
         alt="Profit Factor versus drawdown">
    <img class="chart" src="pareto_win_rate_payoff.png"
         alt="Win rate versus payoff">
    <img class="chart" src="pareto_trade_quality_count.png"
         alt="Average trade to cost versus count">
    <img class="chart" src="pareto_efficiency_duration.png"
         alt="Efficiency versus drawdown duration">
  </div>
</section>
<section>
  <h2>All 24 candidates</h2>
  {shared_report._table_html(candidate_table, columns=visible_columns)}
</section>
{''.join(family_sections)}
<section>
  <h2>What happens next</h2>
  <p>Review every family for profitability, win rate, payoff, drawdown,
  consistency, cost resilience and practical fit. Up to three personally
  attractive finalists may later receive separate preregistered deep
  validation.</p>
  <p class="adverse">EXP-012 cannot authorize paper or live trading.</p>
</section>
<section>
  <h2>Protected run metadata</h2>
  <pre>{metadata_text}</pre>
</section>
</main></body></html>"""
    path = report_dir / "report.html"
    path.write_text(document, encoding="utf-8")
    return path
