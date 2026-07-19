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


COMPARISON_VERSION = "strategy_measurement_comparison_v2"


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
        strategy = pd.to_numeric(
            frame["strategy_equity"],
            errors="coerce",
        )
        normalized = strategy / float(strategy.iloc[0]) * 100.0
        axis.plot(dates, normalized, label=experiment_id)
        if not benchmark_drawn:
            benchmark = pd.to_numeric(
                frame["benchmark_equity"],
                errors="coerce",
            )
            benchmark_normalized = (
                benchmark / float(benchmark.iloc[0]) * 100.0
            )
            axis.plot(
                dates,
                benchmark_normalized,
                linestyle="--",
                label="NQ benchmark",
            )
            benchmark_drawn = True
    axis.axhline(100.0, linewidth=0.8)
    axis.set_title("Normalized strategy equity comparison")
    axis.set_ylabel("Starting value = 100")
    axis.legend()
    axis.grid(alpha=0.25)
    path = assets / "normalized_equity_comparison.png"
    _save(figure, path)
    written.append(path.name)

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
            pd.to_numeric(
                frame["strategy_drawdown_percent"],
                errors="coerce",
            ),
            label=experiment_id,
        )
    axis.axhline(0.0, linewidth=0.8)
    axis.set_title("Strategy drawdown comparison")
    axis.set_ylabel("Drawdown (%)")
    axis.legend()
    axis.grid(alpha=0.25)
    path = assets / "drawdown_comparison.png"
    _save(figure, path)
    written.append(path.name)

    for column, title, ylabel, file_name in (
        (
            "profit_factor",
            "Profit Factor comparison",
            "Profit Factor",
            "profit_factor_comparison.png",
        ),
        (
            "win_rate_percent",
            "Win-rate comparison",
            "Win rate (%)",
            "win_rate_comparison.png",
        ),
        (
            "net_profit_to_drawdown",
            "Net profit to drawdown comparison",
            "Net profit / max drawdown",
            "net_drawdown_comparison.png",
        ),
        (
            "average_trade_to_cost",
            "Average trade relative to costs",
            "Average trade / average cost",
            "trade_cost_comparison.png",
        ),
    ):
        if column not in summary:
            continue
        figure, axis = plt.subplots(figsize=(12, 4.8))
        axis.bar(
            summary["experiment_id"].astype(str),
            pd.to_numeric(summary[column], errors="coerce"),
        )
        axis.set_title(title)
        axis.set_ylabel(ylabel)
        axis.grid(axis="y", alpha=0.25)
        path = assets / file_name
        _save(figure, path)
        written.append(path.name)

    return written


def _tone_for_value(
    label: str,
    raw: Any,
) -> str:
    normalized = label.strip().lower()
    text = str(raw).strip().lower()

    if normalized == "formal decision":
        if "accept" in text or "pass" in text or "lock" in text:
            return "value-positive"
        if "reject" in text or "fail" in text:
            return "value-negative"
        return ""

    if normalized == "failed gates":
        if not text or text in {"none", "nan", "—"}:
            return "value-positive"
        return "value-negative"

    number = _safe(raw)
    if not math.isfinite(number):
        return ""

    if normalized == "mcpt p-value":
        return "value-positive" if number <= 0.05 else "value-negative"

    if normalized in {
        "profit factor",
        "net profit",
        "average trade",
        "net profit / drawdown",
        "average trade / costs",
        "strategy return",
        "nq benchmark return",
        "excess return",
        "two-tick nq net profit",
        "walk-forward net profit",
    }:
        if normalized == "profit factor":
            return "value-positive" if number > 1.0 else "value-negative"
        if number > 0:
            return "value-positive"
        if number < 0:
            return "value-negative"

    if normalized in {
        "maximum drawdown",
        "maximum drawdown %",
    } and number < 0:
        return "value-negative"

    if normalized == "win rate" and number >= 50.0:
        return "value-positive"

    if normalized == "mcpt percentile" and number >= 95.0:
        return "value-positive"

    return ""


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
        (
            "Net profit / drawdown",
            "net_profit_to_drawdown",
            lambda value: _number(value, 3),
        ),
        (
            "Average trade / costs",
            "average_trade_to_cost",
            lambda value: _number(value, 3),
        ),
        ("Maximum consecutive losses", "max_consecutive_losses", _integer),
        (
            "Median holding time",
            "median_holding_minutes",
            lambda value: f"{_number(value, 1)} min",
        ),
        ("Profitable months", "profitable_months_percent", _percent),
        (
            "Longest drawdown",
            "longest_drawdown_sessions",
            lambda value: f"{_integer(value)} sessions",
        ),
        ("Session participation", "session_participation_percent", _percent),
        (
            "Approximate trades/year",
            "trades_per_year",
            lambda value: _number(value, 1),
        ),
        ("Strategy return", "strategy_return_percent", _percent),
        ("NQ benchmark return", "benchmark_return_percent", _percent),
        ("Excess return", "excess_return_percent", _percent),
        ("Two-tick NQ net profit", "two_tick_nq_net_profit_usd", _money),
        ("Walk-forward profitable folds", None, None),
        ("Walk-forward net profit", "walk_forward_net_profit_usd", _money),
        ("MCPT p-value", "mcpt_p_value", lambda value: _number(value, 4)),
        ("MCPT percentile", "mcpt_percentile", _percent),
        (
            "Failed gates",
            "failed_gates",
            lambda value: str(value).replace("|", ", ") or "None",
        ),
    ]
    html_rows: list[str] = []
    for label, field, formatter in rows:
        values = []
        for experiment_id in local.index:
            record = local.loc[experiment_id]
            if label == "Test period":
                raw = ""
                value = (
                    f"{record.get('start_date', '—')} to "
                    f"{record.get('end_date', '—')}"
                )
            elif label == "Walk-forward profitable folds":
                good = _safe(record.get("walk_forward_profitable_folds"))
                total = _safe(record.get("walk_forward_fold_count"))
                raw = good
                value = (
                    "—"
                    if not math.isfinite(good)
                    else f"{int(good)}/{int(total)}"
                )
            else:
                raw = record.get(field) if field else None
                value = formatter(raw) if formatter else str(raw)
            tone = _tone_for_value(label, raw)
            class_attribute = f' class="{tone}"' if tone else ""
            values.append(
                f"<td{class_attribute}>{html.escape(str(value))}</td>"
            )
        html_rows.append(
            "<tr><th>"
            + html.escape(label)
            + "</th>"
            + "".join(values)
            + "</tr>"
        )
    headers = "".join(
        f"<th>{html.escape(str(value))}</th>"
        for value in local.index
    )
    return (
        '<table class="strategy-comparison-table">'
        '<thead><tr><th>Measurement</th>'
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
    summary_file = (
        project_dir
        / "results"
        / "strategy_measurements"
        / "strategy_comparison.csv"
    )
    if not summary_file.exists():
        return """
<section class="strategy-comparison" id="strategy-comparison">
  <h2>Strategy measurement comparison</h2>
  <p class="footer-note">
    Run rebuild_strategy_measurement_reports.py to create the explanatory
    reports and comparison measurements.
  </p>
</section>
"""
    summary = pd.read_csv(summary_file).sort_values("experiment_id")
    if summary.empty:
        return ""
    charts = _write_comparison_charts(
        project_dir,
        dashboard_directory,
        summary,
    )
    chart_html = "".join(
        (
            '<img class="comparison-chart" '
            f'src="strategy_comparison_assets/{html.escape(name)}" '
            'alt="Strategy comparison chart">'
        )
        for name in charts
    )
    report_links = " · ".join(
        (
            f'<a href="../{html.escape(experiment_id)}-research-lab/'
            f'report.html">Open {html.escape(experiment_id)} report</a>'
        )
        for experiment_id in summary["experiment_id"].astype(str)
    )
    return f"""
<section class="strategy-comparison" id="strategy-comparison">
  <div class="comparison-kicker">
    Measured strategy characteristics · {COMPARISON_VERSION}
  </div>
  <h1>Strategy comparison</h1>
  <p class="lead">
    Compare performance, risk, consistency, robustness and practical
    behaviour without reducing a strategy to its lifecycle label.
  </p>
  <p class="report-links">{report_links}</p>
  {chart_html}
  <div class="comparison-table-wrap">{_comparison_table(summary)}</div>
  <p class="footer-note">
    Green highlights favourable measurements. Red highlights losses,
    drawdowns, failed evidence thresholds and rejected decisions. The NQ
    benchmark is a descriptive normalized session-close price path, not a
    tradable one-contract continuous-futures backtest.
  </p>
</section>
"""


def build_strategy_comparison_page(
    project_dir: Path,
    dashboard_directory: Path,
) -> str:
    content = build_strategy_comparison_section(
        project_dir,
        dashboard_directory,
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Strategy Comparison</title>
<style>
:root {{
  color-scheme: dark;
  --bg:#081120;
  --panel:#101b2e;
  --panel-2:#15243b;
  --text:#e8eef8;
  --muted:#9cacbf;
  --line:#2a3b56;
  --accent:#38bdf8;
  --positive:#4ade80;
  --negative:#fb7185;
  --warning:#facc15;
}}
* {{ box-sizing:border-box; }}
body {{
  margin:0;
  background:radial-gradient(circle at top right,#123155 0,transparent 28%),var(--bg);
  color:var(--text);
  font-family:Inter,Segoe UI,Arial,sans-serif;
  line-height:1.5;
}}
a {{ color:var(--accent); text-decoration:none; }}
a:hover {{ text-decoration:underline; }}
header {{
  position:sticky;
  top:0;
  z-index:10;
  background:rgba(8,17,32,.94);
  border-bottom:1px solid var(--line);
  backdrop-filter:blur(14px);
}}
.header-inner {{
  width:min(1550px,calc(100% - 32px));
  margin:0 auto;
  padding:12px 0;
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:18px;
}}
.brand {{ font-weight:800; }}
.tabs {{ display:flex; gap:8px; flex-wrap:wrap; }}
.tab {{
  display:inline-block;
  padding:9px 13px;
  border:1px solid var(--line);
  border-radius:10px;
  color:var(--muted);
  font-weight:700;
}}
.tab:hover {{ color:var(--text); text-decoration:none; border-color:var(--accent); }}
.tab.active {{ color:#06233a; background:var(--accent); border-color:var(--accent); }}
main {{ width:min(1550px,calc(100% - 32px)); margin:30px auto 70px; }}
.strategy-comparison {{
  background:var(--panel);
  border:1px solid var(--line);
  border-radius:18px;
  padding:24px;
  overflow:auto;
}}
.comparison-kicker {{
  color:var(--accent);
  font-size:.76rem;
  font-weight:800;
  letter-spacing:.08em;
  text-transform:uppercase;
}}
h1 {{ margin:.3rem 0 .5rem; font-size:clamp(2rem,5vw,3.6rem); }}
.lead {{ color:var(--muted); max-width:1000px; font-size:1.05rem; }}
.report-links {{ padding:12px 0; }}
.comparison-chart {{
  display:block;
  width:100%;
  height:auto;
  margin:18px 0;
  border:1px solid var(--line);
  border-radius:12px;
  background:#fff;
}}
.comparison-table-wrap {{ overflow:auto; margin-top:22px; }}
.strategy-comparison-table {{
  width:100%;
  min-width:1050px;
  border-collapse:collapse;
  background:var(--panel-2);
}}
th,td {{
  border-bottom:1px solid var(--line);
  padding:10px 12px;
  text-align:right;
  vertical-align:top;
  white-space:nowrap;
}}
th {{
  background:#1d3557;
  color:#dbeafe;
  font-weight:800;
}}
th:first-child,td:first-child {{ text-align:left; }}
tbody tr:nth-child(even) {{ background:rgba(255,255,255,.025); }}
tbody tr:hover {{ background:rgba(56,189,248,.08); }}
.value-positive {{ color:var(--positive); font-weight:800; }}
.value-negative {{ color:var(--negative); font-weight:800; }}
.footer-note {{ color:var(--muted); margin-top:24px; }}
@media(max-width:760px) {{
  .header-inner {{ align-items:flex-start; flex-direction:column; }}
  main {{ width:calc(100% - 20px); }}
  .strategy-comparison {{ padding:15px; }}
}}
</style>
</head>
<body>
<header>
  <div class="header-inner">
    <div class="brand">Quantitative Research Hub</div>
    <nav class="tabs" aria-label="Research dashboard tabs">
      <a class="tab" href="index.html">Research hub</a>
      <a class="tab active" href="strategy_comparison.html">Strategy comparison</a>
    </nav>
  </div>
</header>
<main>{content}</main>
</body>
</html>
"""


def write_strategy_comparison_page(
    project_dir: Path,
    dashboard_directory: Path,
) -> Path:
    dashboard_directory = Path(dashboard_directory)
    dashboard_directory.mkdir(parents=True, exist_ok=True)
    output = dashboard_directory / "strategy_comparison.html"
    output.write_text(
        build_strategy_comparison_page(
            Path(project_dir),
            dashboard_directory,
        ),
        encoding="utf-8",
    )
    return output
