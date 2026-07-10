from __future__ import annotations

import argparse
import html
import json
import os
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from experiment_config import list_experiments
from experiment_decisions import get_experiment_decision


PROJECT_DIR = Path(__file__).resolve().parent


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a visual dashboard covering all configured "
            "research experiments."
        )
    )

    parser.add_argument(
        "--open",
        action="store_true",
        help=(
            "Open the dashboard after building it. "
            "Supported on Windows through os.startfile."
        ),
    )

    return parser.parse_args()


def resolve(path: Path) -> Path:
    if path.is_absolute():
        return path

    return PROJECT_DIR / path


def read_csv_optional(
    path: Path,
    *,
    index_col: int | None = None,
) -> pd.DataFrame | None:
    if not path.exists():
        return None

    return pd.read_csv(
        path,
        index_col=index_col,
    )


def read_json_optional(
    path: Path,
) -> dict[str, Any]:
    if not path.exists():
        return {}

    return json.loads(
        path.read_text(encoding="utf-8")
    )


def get_row(
    table: pd.DataFrame | None,
    row_name: str,
) -> pd.Series | None:
    if table is None or table.empty:
        return None

    if row_name not in table.index:
        return None

    return table.loc[row_name]


def value_from_row(
    row: pd.Series | None,
    column: str,
) -> float:
    if row is None or column not in row:
        return float("nan")

    try:
        return float(row[column])
    except (TypeError, ValueError):
        return float("nan")


def format_number(
    value: Any,
    decimals: int = 3,
) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "N/A"

    if np.isnan(number):
        return "N/A"

    if np.isposinf(number):
        return "∞"

    if np.isneginf(number):
        return "-∞"

    return f"{number:,.{decimals}f}"


def format_percent(
    value: Any,
    decimals: int = 2,
) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "N/A"

    if np.isnan(number):
        return "N/A"

    return f"{number:,.{decimals}f}%"


def status_class(status: str) -> str:
    return status.lower().replace(" ", "-")


def relative_link(
    source_directory: Path,
    target: Path,
) -> str:
    return Path(
        os.path.relpath(
            target,
            source_directory,
        )
    ).as_posix()


def build_experiment_record(
    config,
) -> dict[str, Any]:
    results_directory = (
        resolve(config.results_folder)
        / config.experiment_id
    )

    report_file = (
        resolve(config.reports_folder)
        / f"{config.experiment_id}-research-lab"
        / "report.html"
    )

    summary = read_csv_optional(
        results_directory / "summary.csv",
        index_col=0,
    )

    diagnostics = read_csv_optional(
        results_directory
        / "trade_diagnostics_summary.csv",
        index_col=0,
    )

    metadata = read_json_optional(
        results_directory / "run_metadata.json"
    )

    fixed = get_row(
        summary,
        "Fixed parameters",
    )

    walkforward = get_row(
        summary,
        "Walk-forward",
    )

    fixed_diagnostics = get_row(
        diagnostics,
        "Fixed parameters",
    )

    decision = get_experiment_decision(
        config.experiment_id
    )

    has_results = fixed is not None

    return {
        "experiment_id": config.experiment_id,
        "experiment_name": config.experiment_name,
        "hypothesis": config.hypothesis,
        "market_name": config.market_name,
        "timeframe": config.timeframe,
        "strategy_name": config.strategy_name,
        "status": decision["status"],
        "decision_reason": decision["reason"],
        "has_results": has_results,
        "report_exists": report_file.exists(),
        "report_file": report_file,
        "fixed_return_percent": value_from_row(
            fixed,
            "total_return_percent",
        ),
        "fixed_max_drawdown_percent": value_from_row(
            fixed,
            "max_drawdown_percent",
        ),
        "fixed_trade_profit_factor": value_from_row(
            fixed,
            "trade_profit_factor",
        ),
        "fixed_trades": value_from_row(
            fixed,
            "total_trades",
        ),
        "walkforward_return_percent": value_from_row(
            walkforward,
            "total_return_percent",
        ),
        "walkforward_max_drawdown_percent": value_from_row(
            walkforward,
            "max_drawdown_percent",
        ),
        "walkforward_trade_profit_factor": value_from_row(
            walkforward,
            "trade_profit_factor",
        ),
        "walkforward_trades": value_from_row(
            walkforward,
            "total_trades",
        ),
        "mcpt_p_value": metadata.get(
            "mcpt_p_value",
            np.nan,
        ),
        "best_in_sample_bar_profit_factor": metadata.get(
            "best_in_sample_bar_profit_factor",
            np.nan,
        ),
        "best_in_sample_parameters": metadata.get(
            "best_in_sample_parameters",
            {},
        ),
        "average_winner_percent": value_from_row(
            fixed_diagnostics,
            "average_winner_percent",
        ),
        "average_loser_percent": value_from_row(
            fixed_diagnostics,
            "average_loser_percent",
        ),
        "payoff_ratio": value_from_row(
            fixed_diagnostics,
            "payoff_ratio",
        ),
        "largest_loss_percent": value_from_row(
            fixed_diagnostics,
            "largest_loss_percent",
        ),
    }


def build_charts(
    records: list[dict[str, Any]],
    dashboard_directory: Path,
) -> None:
    completed = [
        record
        for record in records
        if record["has_results"]
    ]

    if not completed:
        return

    labels = [
        record["experiment_id"]
        for record in completed
    ]

    positions = np.arange(len(completed))
    width = 0.36

    # Fixed and walk-forward return comparison.
    fixed_returns = [
        record["fixed_return_percent"]
        for record in completed
    ]

    walkforward_returns = [
        record["walkforward_return_percent"]
        for record in completed
    ]

    plt.figure(figsize=(13, 7))

    plt.bar(
        positions - width / 2,
        fixed_returns,
        width=width,
        label="Fixed parameters",
    )

    plt.bar(
        positions + width / 2,
        walkforward_returns,
        width=width,
        label="Walk-forward",
    )

    plt.axhline(0, linewidth=1)
    plt.xticks(positions, labels)
    plt.title("Out-of-Sample Total Return by Experiment")
    plt.xlabel("Experiment")
    plt.ylabel("Total Return (%)")
    plt.grid(axis="y", alpha=0.2)
    plt.legend()
    plt.tight_layout()
    plt.savefig(
        dashboard_directory / "01_oos_returns.png",
        dpi=140,
        bbox_inches="tight",
    )
    plt.close()

    # Fixed and walk-forward trade Profit Factor.
    fixed_pf = [
        record["fixed_trade_profit_factor"]
        for record in completed
    ]

    walkforward_pf = [
        record["walkforward_trade_profit_factor"]
        for record in completed
    ]

    plt.figure(figsize=(13, 7))

    plt.bar(
        positions - width / 2,
        fixed_pf,
        width=width,
        label="Fixed parameters",
    )

    plt.bar(
        positions + width / 2,
        walkforward_pf,
        width=width,
        label="Walk-forward",
    )

    plt.axhline(
        1.0,
        linewidth=1,
        linestyle="--",
        label="PF = 1.0",
    )

    plt.xticks(positions, labels)
    plt.title("Completed-Trade Profit Factor by Experiment")
    plt.xlabel("Experiment")
    plt.ylabel("Trade Profit Factor")
    plt.grid(axis="y", alpha=0.2)
    plt.legend()
    plt.tight_layout()
    plt.savefig(
        dashboard_directory / "02_trade_profit_factor.png",
        dpi=140,
        bbox_inches="tight",
    )
    plt.close()

    # Fixed and walk-forward drawdown.
    fixed_drawdown = [
        record["fixed_max_drawdown_percent"]
        for record in completed
    ]

    walkforward_drawdown = [
        record["walkforward_max_drawdown_percent"]
        for record in completed
    ]

    plt.figure(figsize=(13, 7))

    plt.bar(
        positions - width / 2,
        fixed_drawdown,
        width=width,
        label="Fixed parameters",
    )

    plt.bar(
        positions + width / 2,
        walkforward_drawdown,
        width=width,
        label="Walk-forward",
    )

    plt.axhline(0, linewidth=1)
    plt.xticks(positions, labels)
    plt.title("Maximum Drawdown by Experiment")
    plt.xlabel("Experiment")
    plt.ylabel("Maximum Drawdown (%)")
    plt.grid(axis="y", alpha=0.2)
    plt.legend()
    plt.tight_layout()
    plt.savefig(
        dashboard_directory / "03_max_drawdown.png",
        dpi=140,
        bbox_inches="tight",
    )
    plt.close()


def build_dashboard_html(
    records: list[dict[str, Any]],
    dashboard_directory: Path,
) -> str:
    completed_count = sum(
        bool(record["has_results"])
        for record in records
    )

    rejected_count = sum(
        record["status"] == "REJECTED"
        for record in records
    )

    accepted_count = sum(
        record["status"] == "ACCEPTED"
        for record in records
    )

    review_count = sum(
        record["status"] == "REVIEW"
        for record in records
    )

    cards_html = ""

    for record in records:
        status = record["status"]

        report_link = ""

        if record["report_exists"]:
            href = relative_link(
                dashboard_directory,
                record["report_file"],
            )

            report_link = (
                f'<a class="report-link" '
                f'href="{html.escape(href)}">'
                f'Open full report</a>'
            )
        else:
            report_link = (
                '<span class="report-missing">'
                'Full report not generated</span>'
            )

        parameters_text = json.dumps(
            record["best_in_sample_parameters"],
            sort_keys=True,
        )

        cards_html += f"""
<section class="experiment-card">
    <div class="experiment-heading">
        <div>
            <div class="experiment-id">
                {html.escape(record["experiment_id"])}
            </div>
            <h2>
                {html.escape(record["experiment_name"])}
            </h2>
        </div>

        <span class="status {status_class(status)}">
            {html.escape(status)}
        </span>
    </div>

    <p class="hypothesis">
        {html.escape(record["hypothesis"])}
    </p>

    <div class="meta">
        {html.escape(record["market_name"])} ·
        {html.escape(record["timeframe"])} ·
        {html.escape(record["strategy_name"])}
    </div>

    <div class="metrics-grid">
        <div class="metric">
            <span>Best IS Bar PF</span>
            <strong>
                {format_number(
                    record["best_in_sample_bar_profit_factor"],
                    4,
                )}
            </strong>
        </div>

        <div class="metric">
            <span>MCPT p-value</span>
            <strong>
                {format_number(
                    record["mcpt_p_value"],
                    4,
                )}
            </strong>
        </div>

        <div class="metric">
            <span>Fixed OOS Return</span>
            <strong>
                {format_percent(
                    record["fixed_return_percent"]
                )}
            </strong>
        </div>

        <div class="metric">
            <span>Fixed Trade PF</span>
            <strong>
                {format_number(
                    record["fixed_trade_profit_factor"]
                )}
            </strong>
        </div>

        <div class="metric">
            <span>Walk-Forward Return</span>
            <strong>
                {format_percent(
                    record["walkforward_return_percent"]
                )}
            </strong>
        </div>

        <div class="metric">
            <span>Walk-Forward PF</span>
            <strong>
                {format_number(
                    record["walkforward_trade_profit_factor"]
                )}
            </strong>
        </div>

        <div class="metric">
            <span>Payoff Ratio</span>
            <strong>
                {format_number(
                    record["payoff_ratio"]
                )}
            </strong>
        </div>

        <div class="metric">
            <span>Largest Fixed Loss</span>
            <strong>
                {format_percent(
                    record["largest_loss_percent"]
                )}
            </strong>
        </div>
    </div>

    <div class="parameters">
        <strong>Best in-sample parameters:</strong>
        <code>{html.escape(parameters_text)}</code>
    </div>

    <div class="decision-reason">
        <strong>Decision rationale:</strong>
        {html.escape(record["decision_reason"])}
    </div>

    <div class="card-footer">
        {report_link}
    </div>
</section>
"""

    rows_html = ""

    for record in records:
        rows_html += f"""
<tr>
    <td>{html.escape(record["experiment_id"])}</td>
    <td>{html.escape(record["experiment_name"])}</td>
    <td>
        <span class="status small {status_class(record["status"])}">
            {html.escape(record["status"])}
        </span>
    </td>
    <td>{format_number(record["mcpt_p_value"], 4)}</td>
    <td>{format_percent(record["fixed_return_percent"])}</td>
    <td>{format_number(record["fixed_trade_profit_factor"])}</td>
    <td>{format_percent(record["fixed_max_drawdown_percent"])}</td>
    <td>{format_percent(record["walkforward_return_percent"])}</td>
    <td>{format_number(record["walkforward_trade_profit_factor"])}</td>
    <td>{format_number(record["payoff_ratio"])}</td>
    <td>{format_percent(record["largest_loss_percent"])}</td>
</tr>
"""

    chart_section = ""

    if completed_count > 0:
        chart_section = """
<h2 class="section-title">Cross-Experiment Comparisons</h2>

<img class="chart"
     src="01_oos_returns.png"
     alt="Out-of-sample returns">

<img class="chart"
     src="02_trade_profit_factor.png"
     alt="Trade Profit Factor">

<img class="chart"
     src="03_max_drawdown.png"
     alt="Maximum drawdown">
"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Research Dashboard</title>

<style>
:root {{
    color-scheme: dark;
}}

body {{
    margin: 0;
    background: #090909;
    color: #eeeeee;
    font-family: Arial, Helvetica, sans-serif;
}}

.page {{
    max-width: 1500px;
    margin: auto;
    padding: 35px;
}}

h1 {{
    font-size: 42px;
    margin-bottom: 5px;
}}

.subtitle {{
    color: #aaaaaa;
    margin-bottom: 30px;
}}

.summary-grid {{
    display: grid;
    grid-template-columns:
        repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px;
    margin: 25px 0 35px;
}}

.summary-card {{
    background: #151515;
    border: 1px solid #303030;
    border-radius: 10px;
    padding: 20px;
}}

.summary-card span {{
    color: #aaaaaa;
    font-size: 14px;
}}

.summary-card strong {{
    display: block;
    font-size: 30px;
    margin-top: 8px;
}}

.section-title {{
    margin-top: 45px;
    border-bottom: 1px solid #333333;
    padding-bottom: 8px;
}}

.experiment-grid {{
    display: grid;
    grid-template-columns:
        repeat(auto-fit, minmax(460px, 1fr));
    gap: 22px;
}}

.experiment-card {{
    background: #141414;
    border: 1px solid #333333;
    border-radius: 12px;
    padding: 24px;
}}

.experiment-heading {{
    display: flex;
    justify-content: space-between;
    gap: 20px;
    align-items: flex-start;
}}

.experiment-id {{
    color: #aaaaaa;
    font-size: 14px;
    letter-spacing: 1px;
}}

.experiment-card h2 {{
    margin: 5px 0 10px;
    font-size: 24px;
}}

.hypothesis {{
    line-height: 1.55;
}}

.meta {{
    color: #aaaaaa;
    margin-bottom: 18px;
}}

.metrics-grid {{
    display: grid;
    grid-template-columns:
        repeat(2, minmax(0, 1fr));
    gap: 10px;
}}

.metric {{
    background: #1c1c1c;
    border: 1px solid #303030;
    border-radius: 8px;
    padding: 13px;
}}

.metric span {{
    color: #aaaaaa;
    display: block;
    font-size: 13px;
}}

.metric strong {{
    display: block;
    margin-top: 5px;
    font-size: 19px;
}}

.status {{
    border-radius: 999px;
    font-weight: bold;
    padding: 8px 12px;
    white-space: nowrap;
}}

.status.small {{
    display: inline-block;
    padding: 5px 9px;
    font-size: 12px;
}}

.status.rejected {{
    background: #3a1515;
    color: #ff8d8d;
}}

.status.accepted {{
    background: #12351f;
    color: #8ee2aa;
}}

.status.review {{
    background: #40330f;
    color: #ffd36e;
}}

.status.planned,
.status.running {{
    background: #142c40;
    color: #8ecbff;
}}

.parameters,
.decision-reason {{
    margin-top: 18px;
    line-height: 1.5;
}}

code {{
    background: #222222;
    border-radius: 4px;
    padding: 3px 6px;
}}

.card-footer {{
    margin-top: 22px;
}}

.report-link {{
    display: inline-block;
    background: #eeeeee;
    color: #111111;
    text-decoration: none;
    font-weight: bold;
    border-radius: 7px;
    padding: 10px 14px;
}}

.report-missing {{
    color: #888888;
}}

.chart {{
    width: 100%;
    background: #ffffff;
    border: 1px solid #333333;
    border-radius: 10px;
    margin: 15px 0 30px;
}}

.table-wrap {{
    overflow-x: auto;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    background: #151515;
}}

th,
td {{
    border: 1px solid #333333;
    padding: 10px;
    text-align: center;
    white-space: nowrap;
}}

th {{
    background: #222222;
}}
</style>
</head>

<body>
<div class="page">

<h1>Quantitative Research Dashboard</h1>

<div class="subtitle">
All configured experiments, decisions and validation results
in one place.
</div>

<div class="summary-grid">
    <div class="summary-card">
        <span>Configured experiments</span>
        <strong>{len(records)}</strong>
    </div>

    <div class="summary-card">
        <span>Experiments with results</span>
        <strong>{completed_count}</strong>
    </div>

    <div class="summary-card">
        <span>Accepted</span>
        <strong>{accepted_count}</strong>
    </div>

    <div class="summary-card">
        <span>Rejected</span>
        <strong>{rejected_count}</strong>
    </div>

    <div class="summary-card">
        <span>Awaiting review</span>
        <strong>{review_count}</strong>
    </div>
</div>

<h2 class="section-title">Experiment Cards</h2>

<div class="experiment-grid">
{cards_html}
</div>

<h2 class="section-title">Comparison Table</h2>

<div class="table-wrap">
<table>
<thead>
<tr>
    <th>ID</th>
    <th>Experiment</th>
    <th>Status</th>
    <th>MCPT p</th>
    <th>Fixed Return</th>
    <th>Fixed PF</th>
    <th>Fixed DD</th>
    <th>WF Return</th>
    <th>WF PF</th>
    <th>Payoff</th>
    <th>Largest Loss</th>
</tr>
</thead>
<tbody>
{rows_html}
</tbody>
</table>
</div>

{chart_section}

</div>
</body>
</html>
"""


def main() -> None:
    arguments = parse_arguments()

    configs = list_experiments()

    if not configs:
        raise RuntimeError(
            "No experiment configuration files were found."
        )

    records = [
        build_experiment_record(config)
        for config in configs
    ]

    reports_root = resolve(
        configs[0].reports_folder
    )

    results_root = resolve(
        configs[0].results_folder
    )

    dashboard_directory = (
        reports_root / "research_dashboard"
    )

    dashboard_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    results_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    build_charts(
        records,
        dashboard_directory,
    )

    dashboard_html = build_dashboard_html(
        records,
        dashboard_directory,
    )

    dashboard_file = (
        dashboard_directory / "index.html"
    )

    dashboard_file.write_text(
        dashboard_html,
        encoding="utf-8",
    )

    export_columns = [
        "experiment_id",
        "experiment_name",
        "status",
        "strategy_name",
        "mcpt_p_value",
        "best_in_sample_bar_profit_factor",
        "fixed_return_percent",
        "fixed_max_drawdown_percent",
        "fixed_trade_profit_factor",
        "fixed_trades",
        "walkforward_return_percent",
        "walkforward_max_drawdown_percent",
        "walkforward_trade_profit_factor",
        "walkforward_trades",
        "average_winner_percent",
        "average_loser_percent",
        "payoff_ratio",
        "largest_loss_percent",
        "decision_reason",
    ]

    pd.DataFrame(records)[
        export_columns
    ].to_csv(
        results_root / "research_dashboard.csv",
        index=False,
    )

    print()
    print("Research dashboard created.")
    print()
    print(f"Experiments: {len(records)}")
    print(
        "With results: "
        f"{sum(record['has_results'] for record in records)}"
    )
    print(
        "Rejected: "
        f"{sum(record['status'] == 'REJECTED' for record in records)}"
    )
    print(
        "Accepted: "
        f"{sum(record['status'] == 'ACCEPTED' for record in records)}"
    )
    print()
    print(f"Dashboard: {dashboard_file}")
    print(
        "Dashboard CSV: "
        f"{results_root / 'research_dashboard.csv'}"
    )

    if arguments.open:
        if hasattr(os, "startfile"):
            os.startfile(dashboard_file)
        else:
            print(
                "--open is only automatically supported "
                "on Windows."
            )


if __name__ == "__main__":
    main()
