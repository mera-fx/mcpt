from __future__ import annotations

from pathlib import Path
from typing import Any
import html
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


COMPARISON_VERSION = "strategy_measurement_comparison_v1"


def _safe(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return number if math.isfinite(number) else float("nan")


def _number(value: Any, digits: int = 3) -> str:
    number = _safe(value)
    return "—" if not math.isfinite(number) else f"{number:,.{digits}f}"


def _percent(value: Any, digits: int = 2) -> str:
    number = _safe(value)
    return "—" if not math.isfinite(number) else f"{number:,.{digits}f}%"


def _money(value: Any) -> str:
    number = _safe(value)
    if not math.isfinite(number):
        return "—"
    sign = "−" if number < 0 else ""
    return f"{sign}${abs(number):,.2f}"


def _integer(value: Any) -> str:
    number = _safe(value)
    return "—" if not math.isfinite(number) else f"{int(round(number)):,}"


def _save(figure: plt.Figure, path: Path) -> None:
    figure.tight_layout()
    figure.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(figure)


def _write_comparison_charts(
    project_dir: Path,
    dashboard_directory: Path,
    summary: pd.DataFrame,
) -> list[str]:
    assets = dashboard_directory / "strategy_comparison_assets"
    assets.mkdir(parents=True, exist_ok=True)
    written: list[str] = []

    figure, axis = plt.subplots(figsize=(14, 6.0))
    benchmark_drawn = False
    for experiment_id in summary["experiment_id"].astype(str):
        path = (
            project_dir
            / "results"
            / "strategy_measurements"
            / experiment_id
            / "comparison_timeseries.csv"
        )
        if not path.exists():
            continue
        frame = pd.read_csv(path)
        dates = pd.to_datetime(frame["session_date"])
        strategy = pd.to_numeric(frame["strategy_equity"], errors="coerce")
        normalized = strategy / float(strategy.iloc[0]) * 100.0
        axis.plot(dates, normalized, label=experiment_id)
        if not benchmark_drawn:
            benchmark = pd.to_numeric(frame["benchmark_equity"], errors="coerce")
            benchmark_normalized = benchmark / float(benchmark.iloc[0]) * 100.0
            axis.plot(dates, benchmark_normalized, linestyle="--", label="NQ benchmark")
            benchmark_drawn = True
    axis.axhline(100.0, linewidth=0.8)
    axis.set_title("Normalized strategy equity comparison")
    axis.set_ylabel("Starting value = 100")
    axis.legend()
    axis.grid(alpha=0.25)
    path = assets / "normalized_equity_comparison.png"
    _save(figure, path); written.append(path.name)

    figure, axis = plt.subplots(figsize=(14, 5.2))
    for experiment_id in summary["experiment_id"].astype(str):
        path = (
            project_dir
            / "results"
            / "strategy_measurements"
            / experiment_id
            / "comparison_timeseries.csv"
        )
        if not path.exists():
            continue
        frame = pd.read_csv(path)
        axis.plot(
            pd.to_datetime(frame["session_date"]),
            pd.to_numeric(frame["strategy_drawdown_percent"], errors="coerce"),
            label=experiment_id,
        )
    axis.axhline(0.0, linewidth=0.8)
    axis.set_title("Strategy drawdown comparison")
    axis.set_ylabel("Drawdown (%)")
    axis.legend()
    axis.grid(alpha=0.25)
    path = assets / "drawdown_comparison.png"
    _save(figure, path); written.append(path.name)

    for column, title, ylabel, file_name in (
        ("profit_factor", "Profit Factor comparison", "Profit Factor", "profit_factor_comparison.png"),
        ("win_rate_percent", "Win-rate comparison", "Win rate (%)", "win_rate_comparison.png"),
        ("net_profit_to_drawdown", "Net profit to drawdown comparison", "Net profit / max drawdown", "net_drawdown_comparison.png"),
        ("average_trade_to_cost", "Average trade relative to costs", "Average trade / average cost", "trade_cost_comparison.png"),
    ):
        if column not in summary:
            continue
        figure, axis = plt.subplots(figsize=(12, 4.8))
        axis.bar(summary["experiment_id"].astype(str), pd.to_numeric(summary[column], errors="coerce"))
        axis.set_title(title)
        axis.set_ylabel(ylabel)
        axis.grid(axis="y", alpha=0.25)
        path = assets / file_name
        _save(figure, path); written.append(path.name)

    return written


def _comparison_table(summary: pd.DataFrame) -> str:
    local = summary.set_index("experiment_id")
    rows = [
        ("Formal decision", "formal_decision", str),
        ("Parameters", "parameters", str),
        ("Test period", None, None),
        ("Completed trades", "completed_trades", _integer),
        ("Profit Factor", "profit_factor", lambda value: _number(value, 3)),
        ("Win rate", "win_rate_percent", _percent),
        ("Average trade", "average_trade_usd", _money),
        ("Net profit", "net_profit_usd", _money),
        ("Maximum drawdown", "maximum_drawdown_usd", _money),
        ("Maximum drawdown %", "maximum_drawdown_percent", _percent),
        ("Net profit / drawdown", "net_profit_to_drawdown", lambda value: _number(value, 3)),
        ("Average trade / costs", "average_trade_to_cost", lambda value: _number(value, 3)),
        ("Maximum consecutive losses", "max_consecutive_losses", _integer),
        ("Median holding time", "median_holding_minutes", lambda value: f"{_number(value, 1)} min"),
        ("Profitable months", "profitable_months_percent", _percent),
        ("Longest drawdown", "longest_drawdown_sessions", lambda value: f"{_integer(value)} sessions"),
        ("Session participation", "session_participation_percent", _percent),
        ("Approximate trades/year", "trades_per_year", lambda value: _number(value, 1)),
        ("Strategy return", "strategy_return_percent", _percent),
        ("NQ benchmark return", "benchmark_return_percent", _percent),
        ("Excess return", "excess_return_percent", _percent),
        ("Two-tick NQ net profit", "two_tick_nq_net_profit_usd", _money),
        ("Walk-forward profitable folds", None, None),
        ("Walk-forward net profit", "walk_forward_net_profit_usd", _money),
        ("MCPT p-value", "mcpt_p_value", lambda value: _number(value, 4)),
        ("MCPT percentile", "mcpt_percentile", _percent),
        ("Failed gates", "failed_gates", lambda value: str(value).replace("|", ", ") or "None"),
    ]
    html_rows: list[str] = []
    for label, field, formatter in rows:
        values = []
        for experiment_id in local.index:
            record = local.loc[experiment_id]
            if label == "Test period":
                value = f"{record.get('start_date', '—')} to {record.get('end_date', '—')}"
            elif label == "Walk-forward profitable folds":
                good = _safe(record.get("walk_forward_profitable_folds"))
                total = _safe(record.get("walk_forward_fold_count"))
                value = "—" if not math.isfinite(good) else f"{int(good)}/{int(total)}"
            else:
                raw = record.get(field) if field else None
                value = formatter(raw) if formatter else str(raw)
            values.append(f"<td>{html.escape(str(value))}</td>")
        html_rows.append(
            "<tr><th>" + html.escape(label) + "</th>" + "".join(values) + "</tr>"
        )
    headers = "".join(f"<th>{html.escape(str(value))}</th>" for value in local.index)
    return (
        '<table class="strategy-comparison-table"><thead><tr><th>Measurement</th>'
        + headers
        + "</tr></thead><tbody>"
        + "".join(html_rows)
        + "</tbody></table>"
    )


def build_strategy_comparison_section(
    project_dir: Path,
    dashboard_directory: Path,
) -> str:
    project_dir = Path(project_dir)
    dashboard_directory = Path(dashboard_directory)
    summary_file = project_dir / "results" / "strategy_measurements" / "strategy_comparison.csv"
    if not summary_file.exists():
        return """
<section class="strategy-comparison" id="strategy-comparison">
  <h2>Strategy measurement comparison</h2>
  <p class="footer-note">Run rebuild_strategy_measurement_reports.py to create the explanatory reports and comparison measurements.</p>
</section>
"""
    summary = pd.read_csv(summary_file).sort_values("experiment_id")
    if summary.empty:
        return ""
    charts = _write_comparison_charts(project_dir, dashboard_directory, summary)
    chart_html = "".join(
        f'<img class="comparison-chart" src="strategy_comparison_assets/{html.escape(name)}" alt="Strategy comparison chart">'
        for name in charts
    )
    report_links = " · ".join(
        f'<a href="../{html.escape(experiment_id)}-research-lab/report.html">Open {html.escape(experiment_id)} report</a>'
        for experiment_id in summary["experiment_id"].astype(str)
    )
    return f"""
<section class="strategy-comparison" id="strategy-comparison">
  <div class="comparison-kicker">Measured strategy characteristics · {COMPARISON_VERSION}</div>
  <h2>Strategy comparison</h2>
  <p>
    This section compares what each strategy measured: performance, risk,
    consistency, robustness and practical behaviour. Lifecycle status remains
    visible, but it does not replace the underlying data.
  </p>
  <p>{report_links}</p>
  {chart_html}
  <div class="comparison-table-wrap">{_comparison_table(summary)}</div>
  <p class="footer-note">
    The NQ benchmark is a descriptive normalized session-close price path.
    It is not a tradable one-contract continuous-futures backtest.
  </p>
</section>
"""
