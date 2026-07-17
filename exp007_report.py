from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


REPORT_VERSION = "exp007_vertical_report_v1"


def _money(value: Any) -> str:
    if value is None or not np.isfinite(float(value)):
        return "—"
    number = float(value)
    sign = "−" if number < 0 else ""
    return f"{sign}${abs(number):,.2f}"


def _number(value: Any, digits: int = 3) -> str:
    if value is None or not np.isfinite(float(value)):
        return "—"
    return f"{float(value):,.{digits}f}"


def _percent(value: Any, digits: int = 2) -> str:
    if value is None or not np.isfinite(float(value)):
        return "—"
    return f"{float(value):,.{digits}f}%"


def _save_equity_chart(
    frame: pd.DataFrame,
    *,
    title: str,
    output: Path,
) -> None:
    dates = pd.to_datetime(frame["session_date"])
    figure, axis = plt.subplots(figsize=(12, 5.2))
    axis.plot(dates, frame["cumulative_net_pnl_usd"])
    axis.axhline(0.0, linewidth=0.8)
    axis.set_title(title)
    axis.set_xlabel("Session")
    axis.set_ylabel("Cumulative net PnL (USD)")
    axis.grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(output, dpi=150)
    plt.close(figure)


def _save_drawdown_chart(
    frame: pd.DataFrame,
    *,
    title: str,
    reference_capital: float,
    output: Path,
) -> None:
    dates = pd.to_datetime(frame["session_date"])
    drawdown_percent = (
        frame["drawdown_usd"].to_numpy(dtype=float)
        / float(reference_capital)
        * 100.0
    )
    figure, axis = plt.subplots(figsize=(12, 4.8))
    axis.fill_between(dates, drawdown_percent, 0.0, alpha=0.35)
    axis.plot(dates, drawdown_percent)
    axis.axhline(0.0, linewidth=0.8)
    axis.set_title(title)
    axis.set_xlabel("Session")
    axis.set_ylabel("Drawdown (% of reference capital)")
    axis.grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(output, dpi=150)
    plt.close(figure)


def _save_annual_chart(frame: pd.DataFrame, output: Path) -> None:
    pivot = frame.pivot(
        index="year",
        columns="symbol",
        values="net_profit_usd",
    ).sort_index()
    figure, axis = plt.subplots(figsize=(12, 5.0))
    pivot.plot(kind="bar", ax=axis)
    axis.axhline(0.0, linewidth=0.8)
    axis.set_title("Annual net profit")
    axis.set_xlabel("Year")
    axis.set_ylabel("Net PnL (USD)")
    axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    figure.savefig(output, dpi=150)
    plt.close(figure)


def _save_cost_chart(frame: pd.DataFrame, output: Path) -> None:
    pivot = frame.pivot(
        index="slippage_ticks_per_side",
        columns="symbol",
        values="net_profit_usd",
    ).sort_index()
    figure, axis = plt.subplots(figsize=(12, 5.0))
    pivot.plot(marker="o", ax=axis)
    axis.axhline(0.0, linewidth=0.8)
    axis.set_title("Cost sensitivity")
    axis.set_xlabel("Slippage ticks per side")
    axis.set_ylabel("Net PnL (USD)")
    axis.grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(output, dpi=150)
    plt.close(figure)


def _save_mcpt_chart(
    frame: pd.DataFrame,
    *,
    real_pf: float,
    output: Path,
) -> None:
    values = frame["trade_profit_factor"].replace(
        [np.inf, -np.inf], np.nan
    ).dropna()
    figure, axis = plt.subplots(figsize=(12, 5.0))
    axis.hist(values, bins=40, alpha=0.75)
    axis.axvline(real_pf, linewidth=2.0, label="Real PF")
    axis.set_title("Session-aware MCPT Profit Factor distribution")
    axis.set_xlabel("Permuted trade Profit Factor")
    axis.set_ylabel("Frequency")
    axis.legend()
    axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    figure.savefig(output, dpi=150)
    plt.close(figure)


def build_exp007_report(
    *,
    decision: dict[str, Any],
    nq_equity: pd.DataFrame,
    mnq_equity: pd.DataFrame,
    yearly: pd.DataFrame,
    cost_sensitivity: pd.DataFrame,
    mcpt: pd.DataFrame,
    output_dir: Path,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    assets = output_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)

    _save_equity_chart(
        nq_equity,
        title="NQ total equity",
        output=assets / "nq_total_equity.png",
    )
    _save_drawdown_chart(
        nq_equity,
        title="NQ drawdown",
        reference_capital=100_000.0,
        output=assets / "nq_drawdown_percent.png",
    )
    _save_equity_chart(
        mnq_equity,
        title="MNQ total equity",
        output=assets / "mnq_total_equity.png",
    )
    _save_drawdown_chart(
        mnq_equity,
        title="MNQ drawdown",
        reference_capital=10_000.0,
        output=assets / "mnq_drawdown_percent.png",
    )
    _save_annual_chart(yearly, assets / "annual_net_profit.png")
    _save_cost_chart(cost_sensitivity, assets / "cost_sensitivity.png")
    nq = decision["results"]["NQ"]
    mnq = decision["results"]["MNQ"]
    _save_mcpt_chart(
        mcpt,
        real_pf=float(nq["trade_profit_factor"]),
        output=assets / "mcpt_profit_factor.png",
    )

    evaluation = decision["evaluation"]
    bootstrap = decision["bootstrap"]
    decision_label = evaluation["decision"].replace("_", " ").title()
    failed = evaluation["failed_gates"]
    failed_text = "None" if not failed else ", ".join(failed)

    metric_rows = [
        ("Completed trades", nq["completed_trades"], nq["long_trades"], 0),
        ("Net profit", _money(nq["net_profit_usd"]), _money(nq["net_profit_usd"]), _money(0)),
        ("Profit Factor", _number(nq["trade_profit_factor"]), _number(nq["trade_profit_factor"]), "—"),
        ("Win rate", _percent(nq["win_rate_percent"]), _percent(nq["win_rate_percent"]), "—"),
        ("Average trade", _money(nq["average_trade_usd"]), _money(nq["average_trade_usd"]), "—"),
        ("Maximum drawdown", _money(nq["maximum_drawdown_usd"]), _money(nq["maximum_drawdown_usd"]), "—"),
        ("Maximum drawdown %", _percent(nq["maximum_drawdown_percent"]), _percent(nq["maximum_drawdown_percent"]), "—"),
    ]
    metrics_html = "".join(
        "<tr>"
        f"<th>{html.escape(str(name))}</th>"
        f"<td>{html.escape(str(all_value))}</td>"
        f"<td>{html.escape(str(long_value))}</td>"
        f"<td>{html.escape(str(short_value))}</td>"
        "</tr>"
        for name, all_value, long_value, short_value in metric_rows
    )

    gate_rows = "".join(
        "<tr>"
        f"<th>{html.escape(name.replace('_', ' ').title())}</th>"
        f"<td>{html.escape(str(gate['actual']))}</td>"
        f"<td>{html.escape(str(gate['operator']))}</td>"
        f"<td>{html.escape(str(gate['threshold']))}</td>"
        f"<td>{'Pass' if gate['passed'] else 'Fail'}</td>"
        "</tr>"
        for name, gate in evaluation["gates"].items()
    )

    annual_html = yearly.sort_values(["year", "symbol"]).to_html(
        index=False,
        border=0,
        classes="data-table",
        float_format=lambda value: f"{value:,.4f}",
    )
    cost_html = cost_sensitivity.sort_values(
        ["symbol", "slippage_ticks_per_side"]
    ).to_html(
        index=False,
        border=0,
        classes="data-table",
        float_format=lambda value: f"{value:,.4f}",
    )

    document = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>EXP-007 Fixed ORB Replication</title>
<style>
:root {{ color-scheme: light dark; --panel:#151922; --line:#343b49; --muted:#9da7b8; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:Segoe UI,Arial,sans-serif; line-height:1.5; background:#0d1016; color:#edf1f7; }}
nav {{ position:fixed; inset:0 auto 0 0; width:250px; padding:28px 20px; background:#11151d; border-right:1px solid var(--line); overflow:auto; }}
nav h1 {{ font-size:18px; margin:0 0 22px; }}
nav a {{ display:block; color:#cbd4e2; text-decoration:none; padding:8px 0; }}
main {{ margin-left:250px; max-width:1250px; padding:36px 42px 80px; }}
section {{ width:100%; margin:0 0 34px; padding:26px; background:var(--panel); border:1px solid var(--line); border-radius:12px; }}
h1,h2,h3 {{ line-height:1.2; }}
.hero {{ padding:34px; }}
.kicker {{ color:var(--muted); text-transform:uppercase; letter-spacing:.12em; font-size:12px; }}
.status {{ font-size:24px; font-weight:700; margin:10px 0; }}
.summary {{ display:grid; grid-template-columns:1fr; gap:12px; }}
.summary div {{ padding:12px 0; border-bottom:1px solid var(--line); }}
table {{ width:100%; border-collapse:collapse; }}
th,td {{ text-align:right; padding:10px 12px; border-bottom:1px solid var(--line); vertical-align:top; }}
th:first-child,td:first-child {{ text-align:left; }}
img {{ width:100%; height:auto; display:block; background:white; border-radius:8px; }}
.note {{ color:var(--muted); }}
.pass {{ color:#7ee2a8; }} .fail {{ color:#ff9b9b; }}
@media (max-width:900px) {{ nav {{ position:static; width:auto; }} main {{ margin:0; padding:20px; }} }}
</style>
</head>
<body>
<nav>
<h1>EXP-007</h1>
<a href="#decision">Decision</a>
<a href="#rules">Fixed rules</a>
<a href="#performance">Performance</a>
<a href="#equity">Equity and drawdown</a>
<a href="#annual">Annual blocks</a>
<a href="#costs">Cost sensitivity</a>
<a href="#mcpt">MCPT</a>
<a href="#bootstrap">Bootstrap</a>
<a href="#gates">Decision gates</a>
</nav>
<main>
<section class="hero" id="decision">
<div class="kicker">Fixed historical replication · {REPORT_VERSION}</div>
<h1>30-Minute Long-Only 1R Opening Range Breakout</h1>
<div class="status {'pass' if evaluation['passed'] else 'fail'}">{html.escape(decision_label)}</div>
<p>Failed gates: {html.escape(failed_text)}</p>
<p class="note">Historical 2019–2025 evidence is exploratory because the period had already been viewed. Passing can only lock a candidate for new forward paper comparison. No live trading is authorized.</p>
</section>
<section id="rules"><h2>Fixed rules</h2>
<div class="summary">
<div><strong>Opening range:</strong> 09:30–10:00 New York</div>
<div><strong>Direction:</strong> Long only</div>
<div><strong>Signal and entry:</strong> First completed 5-minute close above the range high; next 5-minute open</div>
<div><strong>Exit:</strong> Range-low stop, 1R target, or 14:00 time exit</div>
<div><strong>Execution:</strong> One-minute sequencing; same-minute stop and target resolves stop first</div>
<div><strong>Position size:</strong> One fixed contract</div>
</div></section>
<section id="performance"><h2>NQ performance summary</h2>
<table><thead><tr><th>Metric</th><th>All trades</th><th>Long trades</th><th>Short trades</th></tr></thead><tbody>{metrics_html}</tbody></table>
<h3>MNQ implementation check</h3>
<table><tbody>
<tr><th>Completed trades</th><td>{mnq['completed_trades']}</td></tr>
<tr><th>Net profit</th><td>{_money(mnq['net_profit_usd'])}</td></tr>
<tr><th>Profit Factor</th><td>{_number(mnq['trade_profit_factor'])}</td></tr>
<tr><th>Maximum drawdown</th><td>{_money(mnq['maximum_drawdown_usd'])}</td></tr>
</tbody></table></section>
<section id="equity"><h2>NQ total equity</h2><img src="assets/nq_total_equity.png" alt="NQ total equity"><h3>NQ drawdown</h3><img src="assets/nq_drawdown_percent.png" alt="NQ drawdown"><h2>MNQ total equity</h2><img src="assets/mnq_total_equity.png" alt="MNQ total equity"><h3>MNQ drawdown</h3><img src="assets/mnq_drawdown_percent.png" alt="MNQ drawdown"></section>
<section id="annual"><h2>Annual evaluation blocks</h2><img src="assets/annual_net_profit.png" alt="Annual net profit">{annual_html}</section>
<section id="costs"><h2>Cost sensitivity</h2><img src="assets/cost_sensitivity.png" alt="Cost sensitivity">{cost_html}</section>
<section id="mcpt"><h2>Session-aware MCPT</h2><p><strong>Permutations:</strong> {decision['mcpt']['permutations']:,}</p><p><strong>p-value:</strong> {_number(decision['mcpt']['p_value'], 6)}</p><p><strong>Permutations at least real:</strong> {decision['mcpt']['permutations_at_least_real']}</p><img src="assets/mcpt_profit_factor.png" alt="MCPT distribution"></section>
<section id="bootstrap"><h2>Bootstrap diagnostics</h2><p>Average trade 95% interval: {_money(bootstrap['average_trade_usd_95_percentile_interval'][0])} to {_money(bootstrap['average_trade_usd_95_percentile_interval'][1])}</p><p>Profit Factor 95% interval: {_number(bootstrap['trade_profit_factor_95_percentile_interval'][0])} to {_number(bootstrap['trade_profit_factor_95_percentile_interval'][1])}</p><p class="note">Diagnostic only; not a decision gate.</p></section>
<section id="gates"><h2>Locked decision gates</h2><table><thead><tr><th>Gate</th><th>Actual</th><th>Operator</th><th>Threshold</th><th>Result</th></tr></thead><tbody>{gate_rows}</tbody></table></section>
</main>
</body>
</html>"""

    report_file = output_dir / "report.html"
    report_file.write_text(document, encoding="utf-8")

    metadata = {
        "schema_version": 1,
        "experiment_id": "EXP-007",
        "report_version": REPORT_VERSION,
        "report_type": "fixed_orb_replication_saved_results",
        "primary_metrics": {
            "primary_symbol": "NQ",
            "profit_factor": nq["trade_profit_factor"],
            "net_profit_usd": nq["net_profit_usd"],
            "total_return_percent": nq["return_percent"],
            "win_rate_percent": nq["win_rate_percent"],
            "max_drawdown_usd": nq["maximum_drawdown_usd"],
            "max_drawdown_percent": nq["maximum_drawdown_percent"],
            "total_trades": nq["completed_trades"],
            "mcpt_p_value": decision["mcpt"]["p_value"],
            "result_decision": evaluation["decision"],
            "drawdown_percent_note": (
                "Uses the locked $100,000 analytical NQ reference capital; "
                "it is not a margin or account recommendation."
            ),
        },
        "failed_gates": failed,
        "optimization_enabled": False,
        "live_trading_authorized": False,
    }
    (output_dir / "report_metadata.json").write_text(
        json.dumps(metadata, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    return report_file
