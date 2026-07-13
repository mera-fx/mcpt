from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from exp004_orb_engine import (
    OrbBacktestResult,
)
from exp004_quick_screen import (
    Exp004QuickEvaluation,
)


def _format_value(
    value: Any,
) -> str:
    if isinstance(value, float):
        if np.isnan(value):
            return "N/A"
        if np.isinf(value):
            return "∞"
        return f"{value:,.4f}"

    return str(value)


def _parameter_list(
    parameters: dict[str, Any],
) -> str:
    items = [
        f"<li><strong>{html.escape(str(name))}</strong>: "
        f"{html.escape(str(value))}</li>"
        for name, value in (
            parameters.items()
        )
    ]

    return (
        "<ul class='parameter-list'>"
        + "".join(items)
        + "</ul>"
    )


def _table_html(
    frame: pd.DataFrame,
    *,
    columns: list[str],
    labels: dict[str, str],
) -> str:
    view = frame[
        columns
    ].copy()

    view = view.rename(
        columns=labels
    )

    return view.to_html(
        index=False,
        border=0,
        classes="data-table",
        float_format=lambda value: (
            f"{value:,.4f}"
        ),
    )


def build_exp004_quick_report(
    *,
    report_directory: Path,
    optimization: pd.DataFrame,
    best_parameters: dict[str, Any],
    fixed_result: OrbBacktestResult,
    mcpt_results: pd.DataFrame,
    mcpt_p_value: float,
    evaluation: Exp004QuickEvaluation,
    data_audit: dict[str, Any],
    run_metadata: dict[str, Any],
) -> Path:
    report_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    equity_chart = (
        report_directory
        / "fixed_in_sample_equity.png"
    )

    parameter_chart = (
        report_directory
        / "parameter_profit_factor.png"
    )

    mcpt_chart = (
        report_directory
        / "mcpt_distribution.png"
    )

    plt.figure(figsize=(11, 4.8))
    equity = fixed_result.equity_curve
    plt.plot(
        pd.to_datetime(
            equity["session_date"]
        ),
        equity["equity"],
        linewidth=1.7,
    )
    plt.title(
        "Fixed Parameters — In-Sample Equity"
    )
    plt.xlabel("Session")
    plt.ylabel("Equity")
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(
        equity_chart,
        dpi=150,
    )
    plt.close()

    plot_frame = optimization.copy()
    plot_frame["label"] = (
        plot_frame[
            "opening_range_minutes"
        ].astype(str)
        + "m · "
        + plot_frame[
            "direction_mode"
        ].astype(str)
    )

    profit_factors = pd.to_numeric(
        plot_frame[
            "trade_profit_factor"
        ],
        errors="coerce",
    )

    finite_profit_factors = (
        profit_factors[
            np.isfinite(
                profit_factors
            )
        ]
    )

    visual_cap = (
        max(
            2.0,
            float(
                finite_profit_factors.max()
            )
            * 1.10,
        )
        if not finite_profit_factors.empty
        else 2.0
    )

    plot_values = (
        profit_factors.replace(
            [np.inf, -np.inf],
            visual_cap,
        )
        .fillna(0.0)
    )

    plt.figure(figsize=(11, 5.2))
    plt.bar(
        plot_frame["label"],
        plot_values,
    )
    plt.axhline(
        1.0,
        linewidth=1.2,
    )
    plt.title(
        "In-Sample Profit Factor by Locked Parameter Combination"
    )
    plt.xlabel("Opening range and direction")
    plt.ylabel("Trade Profit Factor")
    plt.xticks(
        rotation=35,
        ha="right",
    )
    plt.tight_layout()
    plt.savefig(
        parameter_chart,
        dpi=150,
    )
    plt.close()

    mcpt_plot_values = pd.to_numeric(
        mcpt_results[
            "best_trade_profit_factor"
        ],
        errors="coerce",
    ).replace(
        [np.inf, -np.inf],
        visual_cap,
    ).dropna()

    plt.figure(figsize=(10.5, 4.8))
    plt.hist(
        mcpt_plot_values,
        bins=min(
            12,
            max(
                5,
                len(mcpt_results),
            ),
        ),
    )
    real_best_for_plot = float(
        optimization[
            "trade_profit_factor"
        ].max()
    )

    if not np.isfinite(
        real_best_for_plot
    ):
        real_best_for_plot = (
            visual_cap
        )

    plt.axvline(
        real_best_for_plot,
        linewidth=1.7,
    )
    plt.title(
        "Session-Aware MCPT Best Profit Factors"
    )
    plt.xlabel(
        "Best optimized Profit Factor "
        "per permutation"
    )
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(
        mcpt_chart,
        dpi=150,
    )
    plt.close()

    gate_rows = []

    for gate_name, gate in (
        evaluation.gates.items()
    ):
        gate_rows.append(
            {
                "Gate": gate_name.replace(
                    "_",
                    " ",
                ).title(),
                "Status": (
                    "PASS"
                    if gate["passed"]
                    else "FAIL"
                ),
                "Actual": _format_value(
                    gate["actual"]
                ),
                "Rule": (
                    f"{gate['operator']} "
                    f"{_format_value(gate['threshold'])}"
                ),
            }
        )

    gates_html = pd.DataFrame(
        gate_rows
    ).to_html(
        index=False,
        border=0,
        classes="data-table",
    )

    optimization_html = _table_html(
        optimization.sort_values(
            [
                "trade_profit_factor",
                "total_return_percent",
            ],
            ascending=[
                False,
                False,
            ],
        ),
        columns=[
            "opening_range_minutes",
            "direction_mode",
            "trade_profit_factor",
            "total_return_percent",
            "max_drawdown_percent",
            "completed_trades",
            "long_trades",
            "short_trades",
            "win_rate_percent",
            "average_trade_percent",
            "valid",
        ],
        labels={
            "opening_range_minutes": (
                "Opening Range (min)"
            ),
            "direction_mode": (
                "Direction"
            ),
            "trade_profit_factor": (
                "Trade PF"
            ),
            "total_return_percent": (
                "Return %"
            ),
            "max_drawdown_percent": (
                "Max DD %"
            ),
            "completed_trades": (
                "Trades"
            ),
            "long_trades": (
                "Long"
            ),
            "short_trades": (
                "Short"
            ),
            "win_rate_percent": (
                "Win Rate %"
            ),
            "average_trade_percent": (
                "Avg Trade %"
            ),
            "valid": "Valid",
        },
    )

    recent_trades = (
        fixed_result.trades.tail(30)
    )

    if recent_trades.empty:
        trades_html = (
            "<p>No fixed-parameter trades "
            "were produced.</p>"
        )
    else:
        trade_columns = [
            "session_date",
            "direction",
            "entry_time",
            "exit_time",
            "entry_price",
            "exit_price",
            "net_return_percent",
            "exit_reason",
            "pnl_cash",
        ]

        trades_html = (
            recent_trades[
                trade_columns
            ].to_html(
                index=False,
                border=0,
                classes="data-table",
                float_format=lambda value: (
                    f"{value:,.4f}"
                ),
            )
        )

    fixed = fixed_result.summary

    document = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>EXP-004 Quick Screen</title>
<style>
:root {{
  color-scheme: light;
  --background: #f4f6f8;
  --panel: #ffffff;
  --text: #20252b;
  --muted: #66717d;
  --border: #dfe4e8;
  --accent: #1f5b8f;
  --success: #1f7a43;
  --danger: #a63535;
}}
* {{ box-sizing: border-box; }}
html, body {{
  margin: 0;
  max-width: 100%;
  overflow-x: hidden;
}}
body {{
  font-family: Arial, sans-serif;
  background: var(--background);
  color: var(--text);
}}
main {{
  width: min(1240px, calc(100% - 28px));
  margin: 24px auto 56px;
}}
.hero {{
  background: linear-gradient(135deg, #173b5d, #245f8d);
  color: white;
  padding: 28px;
  border-radius: 14px;
}}
.hero h1 {{
  margin: 0 0 8px;
  font-size: clamp(26px, 4vw, 42px);
}}
.hero p {{
  margin: 5px 0;
  opacity: .94;
}}
.lock-banner {{
  margin-top: 16px;
  padding: 12px 14px;
  background: rgba(255,255,255,.16);
  border: 1px solid rgba(255,255,255,.28);
  border-radius: 9px;
  font-weight: 700;
}}
.cards {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 13px;
  margin-top: 16px;
}}
.card, .panel {{
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,.04);
}}
.card {{
  padding: 16px;
}}
.card .label {{
  color: var(--muted);
  font-size: 13px;
}}
.card .value {{
  font-size: 25px;
  font-weight: 700;
  margin-top: 7px;
  overflow-wrap: anywhere;
}}
.panel {{
  margin-top: 16px;
  padding: 20px;
  min-width: 0;
}}
.panel h2 {{
  margin: 0 0 14px;
}}
.two-column {{
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}}
.chart {{
  width: 100%;
  display: block;
  border-radius: 8px;
}}
.table-scroll {{
  width: 100%;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}}
.data-table {{
  width: 100%;
  min-width: 760px;
  border-collapse: collapse;
  font-size: 13px;
}}
.data-table th,
.data-table td {{
  padding: 9px 10px;
  border-bottom: 1px solid var(--border);
  text-align: right;
  white-space: nowrap;
}}
.data-table th:first-child,
.data-table td:first-child {{
  text-align: left;
}}
.parameter-list {{
  margin: 0;
  padding-left: 20px;
}}
.parameter-list li {{
  margin: 7px 0;
}}
.decision {{
  color: {
      'var(--success)'
      if evaluation.passed
      else 'var(--danger)'
  };
}}
details {{
  margin-top: 16px;
}}
summary {{
  cursor: pointer;
  font-weight: 700;
}}
code, pre {{
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}}
@media (max-width: 850px) {{
  .two-column {{
    grid-template-columns: 1fr;
  }}
  main {{
    width: min(100% - 18px, 1240px);
  }}
  .panel {{
    padding: 15px;
  }}
}}
</style>
</head>
<body>
<main>
<section class="hero">
  <h1>EXP-004 Quick Screen</h1>
  <p>QQQ 5-Minute Opening Range Breakout</p>
  <p>In-sample period: 2019-01-02 through 2022-12-30</p>
  <div class="lock-banner">
    OUT-OF-SAMPLE DATA REMAINED LOCKED. This report contains in-sample evidence only.
  </div>
</section>

<section class="cards">
  <div class="card">
    <div class="label">Decision</div>
    <div class="value decision">{html.escape(evaluation.decision)}</div>
  </div>
  <div class="card">
    <div class="label">Best IS Trade PF</div>
    <div class="value">{optimization['trade_profit_factor'].max():.3f}</div>
  </div>
  <div class="card">
    <div class="label">Fixed IS Trade PF</div>
    <div class="value">{fixed['trade_profit_factor']:.3f}</div>
  </div>
  <div class="card">
    <div class="label">Quick MCPT p-value</div>
    <div class="value">{mcpt_p_value:.4f}</div>
  </div>
  <div class="card">
    <div class="label">Fixed Trades</div>
    <div class="value">{fixed['completed_trades']}</div>
  </div>
  <div class="card">
    <div class="label">Included Sessions</div>
    <div class="value">{data_audit['included_sessions']}</div>
  </div>
</section>

<section class="two-column">
  <div class="panel">
    <h2>Best In-Sample Parameters</h2>
    {_parameter_list(best_parameters)}
  </div>
  <div class="panel">
    <h2>Fixed Preregistered Parameters</h2>
    {_parameter_list(fixed_result.parameters)}
  </div>
</section>

<section class="panel">
  <h2>Quick-Screen Gates</h2>
  <div class="table-scroll">{gates_html}</div>
</section>

<section class="two-column">
  <div class="panel">
    <img class="chart" src="fixed_in_sample_equity.png" alt="Fixed in-sample equity">
  </div>
  <div class="panel">
    <img class="chart" src="mcpt_distribution.png" alt="MCPT distribution">
  </div>
</section>

<section class="panel">
  <img class="chart" src="parameter_profit_factor.png" alt="Parameter Profit Factors">
</section>

<section class="panel">
  <h2>All Locked Parameter Combinations</h2>
  <div class="table-scroll">{optimization_html}</div>
</section>

<details class="panel">
  <summary>Recent Fixed-Parameter Trades</summary>
  <div class="table-scroll">{trades_html}</div>
</details>

<details class="panel">
  <summary>Data Audit and Run Metadata</summary>
  <pre>{html.escape(json.dumps({
      "data_audit": data_audit,
      "run_metadata": run_metadata,
  }, indent=2, default=str))}</pre>
</details>
</main>
</body>
</html>
"""

    report_file = (
        report_directory
        / "report.html"
    )

    report_file.write_text(
        document,
        encoding="utf-8",
    )

    return report_file
