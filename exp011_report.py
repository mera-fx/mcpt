from __future__ import annotations

import html
from pathlib import Path
from typing import Any, Mapping

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from exp009_engine import Exp009Arrays
from exp011_measurements import SIGNAL_IDS
from exp011_sizing import Exp011Calibration, Exp011SizedResult, SIZING_IDS
from report_chart_style import save_report_figure
from strategy_explanations import (
    STRATEGY_EXPLANATION_CSS,
    strategy_explanation_html,
)


SIZING_LABELS = {
    "fixed_one_nq": "Fixed 1 NQ",
    "fractional_nq_equal_risk": "Fractional NQ equal risk",
    "integer_mnq_equal_risk": "Integer MNQ equal risk",
}
SIGNAL_LABELS = {
    "opening_drive_0p5_time": "Primary: time exit",
    "opening_drive_0p5_1p5r": "User reference: 1.5R or time",
}
COLORS = {
    "fixed_one_nq": "#94a3b8",
    "fractional_nq_equal_risk": "#60a5fa",
    "integer_mnq_equal_risk": "#a78bfa",
}


def _format_value(column: str, value: Any) -> str:
    if value is None or (
        isinstance(value, (float, np.floating)) and np.isnan(value)
    ):
        return "—"
    if isinstance(value, (bool, np.bool_)):
        return "Yes" if bool(value) else "No"
    if isinstance(value, (int, np.integer)):
        return f"{int(value):,}"
    if isinstance(value, (float, np.floating)):
        number = float(value)
        if "rate" in column or "probability" in column:
            return f"{number:.2%}"
        if "usd" in column:
            return f"${number:,.2f}"
        if "profit_factor" in column or "coefficient" in column:
            return f"{number:.4f}"
        return f"{number:,.3f}"
    return str(value)


def _cell_class(column: str, value: Any) -> str:
    text = str(value).upper()
    if text in {"PASS", "ACCEPTED", "LOCKED"}:
        return "status-good"
    if text in {"FAIL", "FAILED", "REJECTED"}:
        return "adverse"
    if isinstance(value, (int, float, np.number)) and float(value) < 0:
        return "adverse"
    if column.endswith("_check") and value is False:
        return "adverse"
    return ""


def _table_html(
    table: pd.DataFrame,
    *,
    columns: list[str] | None = None,
) -> str:
    local = table if columns is None else table.loc[:, columns]
    headers = "".join(
        f"<th>{html.escape(column.replace('_', ' ').title())}</th>"
        for column in local.columns
    )
    rows = []
    for _, row in local.iterrows():
        cells = []
        for column in local.columns:
            value = row[column]
            cells.append(
                f'<td class="{_cell_class(column, value)}">'
                f"{html.escape(_format_value(column, value))}</td>"
            )
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return (
        '<div class="table-scroll"><table><thead><tr>'
        + headers
        + "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></div>"
    )


def _evaluation_benchmark(
    arrays: Exp009Arrays,
) -> tuple[pd.DatetimeIndex, np.ndarray]:
    mask = arrays.years >= 2021
    dates = pd.to_datetime(arrays.session_dates[mask])
    closes = arrays.close[mask, -1]
    benchmark = 100_000.0 * closes / closes[0]
    return dates, benchmark


def _save_equity_chart(
    results: Mapping[tuple[str, str], Exp011SizedResult],
    arrays: Exp009Arrays,
    output_dir: Path,
) -> Path:
    benchmark_dates, benchmark = _evaluation_benchmark(arrays)
    figure, axes = plt.subplots(2, 1, figsize=(13, 10), sharex=True)
    for axis, signal_id in zip(axes, SIGNAL_IDS, strict=True):
        axis.plot(
            benchmark_dates,
            benchmark,
            color="#475569",
            linewidth=1.8,
            alpha=0.9,
            label="NQ normalized price benchmark",
        )
        for sizing_id in SIZING_IDS:
            result = results[(signal_id, sizing_id)]
            axis.plot(
                pd.to_datetime(result.equity_curve["session_date"]),
                result.equity_curve["equity_usd"],
                color=COLORS[sizing_id],
                linewidth=1.5,
                label=SIZING_LABELS[sizing_id],
            )
        axis.axhline(
            100_000.0, color="#64748b", linewidth=1, linestyle="--"
        )
        axis.set_title(SIGNAL_LABELS[signal_id])
        axis.set_ylabel("Normalized value ($)")
        axis.grid(alpha=0.16)
        axis.legend(frameon=False, fontsize=8, ncol=2)
    figure.suptitle(
        "2021–2025 sizing equity paths versus NQ price benchmark",
        fontsize=14,
    )
    figure.tight_layout()
    path = output_dir / "sizing_equity_vs_nq.png"
    save_report_figure(figure, path, dpi=160)
    plt.close(figure)
    return path


def _save_drawdown_chart(
    results: Mapping[tuple[str, str], Exp011SizedResult],
    output_dir: Path,
) -> Path:
    figure, axes = plt.subplots(2, 1, figsize=(13, 9), sharex=True)
    for axis, signal_id in zip(axes, SIGNAL_IDS, strict=True):
        for sizing_id in SIZING_IDS:
            result = results[(signal_id, sizing_id)]
            axis.plot(
                pd.to_datetime(result.equity_curve["session_date"]),
                result.equity_curve["drawdown_usd"],
                color=COLORS[sizing_id],
                linewidth=1.5,
                label=SIZING_LABELS[sizing_id],
            )
        axis.axhline(0.0, color="#64748b", linewidth=1)
        axis.set_title(SIGNAL_LABELS[signal_id])
        axis.set_ylabel("Drawdown ($)")
        axis.grid(alpha=0.16)
        axis.legend(frameon=False, fontsize=8)
    figure.suptitle("Sizing-method drawdown comparison", fontsize=14)
    figure.tight_layout()
    path = output_dir / "sizing_drawdowns.png"
    save_report_figure(figure, path, dpi=160)
    plt.close(figure)
    return path


def _save_risk_chart(
    results: Mapping[tuple[str, str], Exp011SizedResult],
    output_dir: Path,
) -> Path:
    figure, axes = plt.subplots(1, 2, figsize=(13, 6))
    for axis, signal_id in zip(axes, SIGNAL_IDS, strict=True):
        samples = [
            results[(signal_id, sizing_id)]
            .trades["initial_risk_usd"]
            .to_numpy(dtype=float)
            for sizing_id in SIZING_IDS
        ]
        axis.boxplot(
            samples,
            tick_labels=[SIZING_LABELS[item] for item in SIZING_IDS],
            showfliers=False,
        )
        axis.set_title(SIGNAL_LABELS[signal_id])
        axis.set_ylabel("Initial dollar risk")
        axis.tick_params(axis="x", labelrotation=20)
        axis.grid(axis="y", alpha=0.16)
    figure.suptitle("Initial-risk distribution after sizing", fontsize=14)
    figure.tight_layout()
    path = output_dir / "initial_risk_distribution.png"
    save_report_figure(figure, path, dpi=160)
    plt.close(figure)
    return path


def _save_contract_chart(
    results: Mapping[tuple[str, str], Exp011SizedResult],
    output_dir: Path,
) -> Path:
    figure, axes = plt.subplots(2, 2, figsize=(13, 9))
    for row, signal_id in enumerate(SIGNAL_IDS):
        for column, sizing_id in enumerate(
            ("fractional_nq_equal_risk", "integer_mnq_equal_risk")
        ):
            axis = axes[row, column]
            values = results[(signal_id, sizing_id)].signals[
                "contracts"
            ].to_numpy(dtype=float)
            bins = (
                np.arange(-0.5, 20.6, 1.0)
                if sizing_id == "integer_mnq_equal_risk"
                else np.linspace(0, 2.0, 31)
            )
            axis.hist(values, bins=bins, color=COLORS[sizing_id], alpha=0.85)
            axis.set_title(
                f"{SIGNAL_LABELS[signal_id]} — {SIZING_LABELS[sizing_id]}"
            )
            axis.set_xlabel("Contracts")
            axis.set_ylabel("Signals")
            axis.grid(alpha=0.14)
    figure.suptitle("Calculated contract quantities", fontsize=14)
    figure.tight_layout()
    path = output_dir / "contract_count_distribution.png"
    save_report_figure(figure, path, dpi=160)
    plt.close(figure)
    return path


def _save_annual_chart(
    results: Mapping[tuple[str, str], Exp011SizedResult],
    output_dir: Path,
) -> Path:
    figure, axes = plt.subplots(2, 1, figsize=(13, 10))
    for axis, signal_id in zip(axes, SIGNAL_IDS, strict=True):
        records = []
        for sizing_id in SIZING_IDS:
            for row in results[
                (signal_id, sizing_id)
            ].yearly_results.to_dict(orient="records"):
                records.append({"sizing_id": sizing_id, **row})
        frame = pd.DataFrame.from_records(records)
        pivot = frame.pivot(
            index="year", columns="sizing_id", values="net_profit_usd"
        ).reindex(columns=list(SIZING_IDS))
        pivot.columns = [SIZING_LABELS[item] for item in pivot.columns]
        pivot.plot(kind="bar", ax=axis, width=0.8)
        axis.axhline(0.0, color="#f87171", linewidth=1)
        axis.set_title(SIGNAL_LABELS[signal_id])
        axis.set_ylabel("Net profit ($)")
        axis.grid(axis="y", alpha=0.16)
        axis.legend(frameon=False, fontsize=8)
    figure.suptitle("Annual net profit by sizing method", fontsize=14)
    figure.tight_layout()
    path = output_dir / "annual_sizing_comparison.png"
    save_report_figure(figure, path, dpi=160)
    plt.close(figure)
    return path


def _save_monthly_heatmap(
    results: Mapping[tuple[str, str], Exp011SizedResult],
    output_dir: Path,
) -> Path:
    records = []
    for signal_id in SIGNAL_IDS:
        for sizing_id in SIZING_IDS:
            label = (
                SIGNAL_LABELS[signal_id].split(":")[0]
                + " / "
                + SIZING_LABELS[sizing_id]
            )
            series = results[(signal_id, sizing_id)].monthly_results.set_index(
                "month"
            )["net_profit_usd"]
            records.append(series.rename(label))
    frame = pd.concat(records, axis=1).fillna(0.0).T
    maximum = float(np.abs(frame.to_numpy()).max()) or 1.0
    figure, axis = plt.subplots(figsize=(16, 5.5))
    image = axis.imshow(
        frame.to_numpy(),
        aspect="auto",
        cmap="RdBu",
        vmin=-maximum,
        vmax=maximum,
    )
    axis.set_yticks(np.arange(len(frame.index)))
    axis.set_yticklabels(frame.index, fontsize=8)
    step = max(1, len(frame.columns) // 12)
    ticks = np.arange(0, len(frame.columns), step)
    axis.set_xticks(ticks)
    axis.set_xticklabels(frame.columns[ticks], rotation=45, ha="right")
    axis.set_title("Monthly net-profit heatmap")
    figure.colorbar(image, ax=axis, label="Net profit ($)")
    figure.tight_layout()
    path = output_dir / "monthly_sizing_heatmap.png"
    save_report_figure(figure, path, dpi=160)
    plt.close(figure)
    return path


def _bootstrap_table(bootstrap: list[dict[str, Any]]) -> pd.DataFrame:
    records = []
    for item in bootstrap:
        pnl_interval = item[
            "mean_session_pnl_difference_95_percentile_interval"
        ]
        risk_interval = item[
            "mean_absolute_risk_difference_95_percentile_interval"
        ]
        records.append(
            {
                "signal_candidate_id": item["signal_candidate_id"],
                "comparison_sizing_id": item["comparison_sizing_id"],
                "comparison_scale_to_nq": item[
                    "comparison_scale_to_nq"
                ],
                "observed_mean_session_pnl_difference_usd": item[
                    "observed_mean_session_pnl_difference_usd"
                ],
                "pnl_difference_95_interval": (
                    f"${pnl_interval[0]:,.2f} to "
                    f"${pnl_interval[1]:,.2f}"
                ),
                "probability_mean_session_pnl_difference_above_zero": item[
                    "probability_mean_session_pnl_difference_above_zero"
                ],
                "observed_mean_initial_risk_difference_usd": item[
                    "observed_mean_initial_risk_difference_usd"
                ],
                "risk_difference_95_interval": (
                    f"${risk_interval[0]:,.2f} to "
                    f"${risk_interval[1]:,.2f}"
                ),
                "decision_gate": "No",
            }
        )
    return pd.DataFrame.from_records(records)


def build_exp011_report(
    *,
    decision: Mapping[str, Any],
    calibration: Exp011Calibration,
    results: Mapping[tuple[str, str], Exp011SizedResult],
    measurement_table: pd.DataFrame,
    bootstrap: list[dict[str, Any]],
    nq_arrays: Exp009Arrays,
    output_dir: Path,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    _save_equity_chart(results, nq_arrays, output_dir)
    _save_drawdown_chart(results, output_dir)
    _save_risk_chart(results, output_dir)
    _save_contract_chart(results, output_dir)
    _save_annual_chart(results, output_dir)
    _save_monthly_heatmap(results, output_dir)

    display_columns = [
        "signal_candidate_id",
        "sizing_id",
        "symbol",
        "implementation_status",
        "completed_trades",
        "skipped_zero_size_trades",
        "net_profit_usd",
        "trade_profit_factor",
        "win_rate",
        "average_trade_usd",
        "maximum_drawdown_usd",
        "net_profit_to_maximum_drawdown",
        "average_initial_risk_usd",
        "initial_risk_standard_deviation_usd",
        "initial_risk_coefficient_of_variation",
        "95th_percentile_initial_risk_usd",
        "maximum_initial_risk_usd",
        "average_contracts",
        "maximum_contracts",
        "cost_total_usd",
    ]
    practical_columns = [
        "signal_candidate_id",
        "sizing_id",
        "signal_count",
        "completed_trades",
        "skipped_zero_size_trades",
        "zero_contract_skip_rate",
        "average_contracts",
        "median_contracts",
        "maximum_contracts",
        "average_holding_minutes",
        "maximum_consecutive_losses",
        "worst_20_trade_result_usd",
        "worst_50_trade_result_usd",
    ]
    primary = measurement_table.loc[
        measurement_table["signal_candidate_id"].eq(
            "opening_drive_0p5_time"
        )
    ].set_index("sizing_id")
    fixed = primary.loc["fixed_one_nq"]
    fractional = primary.loc["fractional_nq_equal_risk"]
    integer = primary.loc["integer_mnq_equal_risk"]
    target = calibration.target_dollar_risk_usd
    worked_nq_risk = target * 4 / 3
    worked_mnq_risk = target / 7.25
    bootstrap_frame = _bootstrap_table(bootstrap)

    css = f"""
    :root {{
      --bg:#07111f; --panel:#0d1a2b; --line:#25364d;
      --text:#dbe7f5; --muted:#8ea2b9; --accent:#60a5fa;
      --good:#4ade80; --bad:#f87171;
    }}
    * {{ box-sizing:border-box; }}
    body {{
      margin:0; background:var(--bg); color:var(--text);
      font-family:Inter,Segoe UI,Arial,sans-serif; line-height:1.55;
    }}
    main {{ max-width:1500px; margin:0 auto; padding:28px; }}
    nav {{ display:flex; gap:16px; margin-bottom:24px; }}
    nav a {{ color:var(--accent); text-decoration:none; }}
    h1 {{ font-size:2.1rem; margin:.2rem 0; }}
    h2 {{ margin-top:2.4rem; border-bottom:1px solid var(--line);
          padding-bottom:.55rem; }}
    h3 {{ color:#bfdbfe; }}
    .lead {{ color:var(--muted); max-width:1000px; font-size:1.05rem; }}
    .panel {{
      background:var(--panel); border:1px solid var(--line);
      border-radius:12px; padding:20px; margin:18px 0;
    }}
    .grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr));
             gap:14px; }}
    .stat {{ background:#0a1626; border:1px solid var(--line);
             border-radius:10px; padding:15px; }}
    .stat span {{ display:block; color:var(--muted); font-size:.82rem; }}
    .stat strong {{ font-size:1.25rem; font-weight:600; }}
    .table-scroll {{ overflow-x:auto; }}
    table {{ width:100%; border-collapse:collapse; font-size:.88rem; }}
    th,td {{ padding:10px; border-bottom:1px solid var(--line);
             text-align:right; white-space:nowrap; font-weight:400; }}
    th {{ color:#bfdbfe; text-align:right; }}
    th:first-child,td:first-child {{ text-align:left; }}
    .status-good {{ color:var(--good); font-weight:400; }}
    .adverse {{ color:var(--bad); font-weight:400; }}
    img {{ width:100%; border-radius:10px; border:1px solid var(--line); }}
    .note {{ color:var(--muted); border-left:3px solid var(--accent);
             padding-left:14px; }}
    code {{ color:#bfdbfe; }}
    {STRATEGY_EXPLANATION_CSS}
    @media(max-width:900px) {{ .grid {{ grid-template-columns:1fr; }} }}
    """

    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>EXP-011 position-sizing study</title><style>{css}</style></head>
<body><main>
<nav><a href="../research_dashboard/index.html">Research dashboard</a>
<a href="../research_dashboard/strategy_comparison.html">Strategy comparison</a>
<a href="../EXP-010-research-lab/report.html">EXP-010 signal report</a></nav>
<p class="lead">EXP-011 · measurement-only position-sizing study ·
2021–2025 evaluation</p>
<h1>Opening-drive position sizing</h1>
<p class="lead">The two frozen EXP-010 signals were not changed. This report
measures what happened when the same trades were expressed as fixed one-contract
NQ, theoretical fractional NQ equal risk, and practical whole-contract MNQ equal
risk. It does not declare a sizing winner or re-test the entry signal.</p>

<section class="grid">
<div class="stat"><span>Frozen target dollar risk</span>
<strong>${target:,.2f}</strong></div>
<div class="stat"><span>Calibration trades (2019–2020)</span>
<strong>{calibration.trade_count:,}</strong></div>
<div class="stat"><span>Displayed signal × sizing rows</span>
<strong>6 of 6</strong></div>
</section>

{strategy_explanation_html("EXP-011")}

<h2>What we tested and how</h2>
<div class="panel">
<p>The target was the median valid one-NQ entry-to-stop risk, including the
locked one-contract round-trip cost, from the primary signal's 2019–2020
calibration trades. That value was frozen before the 2021–2025 evaluation and
used unchanged for both signal variants. Contract quantity was known at entry;
profits were not compounded into later size.</p>
<p><strong>Worked sizing example.</strong> With the measured target of
${target:,.2f}, a trade whose one-NQ initial risk is ${worked_nq_risk:,.2f}
would use {target / worked_nq_risk:.2f} theoretical NQ contracts. If one MNQ
initially risked ${worked_mnq_risk:,.2f}, the implementable calculation would
be floor({target:,.2f} / {worked_mnq_risk:,.2f}) =
{int(np.floor(target / worked_mnq_risk))} MNQ contracts.</p>
<p class="note">A fraction such as 0.75 is a contract quantity. It does not
mean a 75% probability, a 75% account risk, or a 75% market move.</p>
</div>

<h2>What happened</h2>
<div class="panel">
<p>For the primary time-exit signal, fixed one NQ produced
${float(fixed['net_profit_usd']):,.2f} with a maximum drawdown of
${float(fixed['maximum_drawdown_usd']):,.2f}. Fractional equal-risk NQ produced
${float(fractional['net_profit_usd']):,.2f} with a maximum drawdown of
${float(fractional['maximum_drawdown_usd']):,.2f}. Integer equal-risk MNQ
produced ${float(integer['net_profit_usd']):,.2f} in native MNQ dollars and
skipped {int(integer['skipped_zero_size_trades']):,} signals whose target risk
could not fund one whole MNQ contract.</p>
<p>The tables and charts retain all methods and both exit variants. Differences
are measurements, not automatic recommendations. Fractional NQ remains
theoretical, while MNQ is implementable in whole contracts.</p>
</div>

<h2>All six measurements</h2>
{_table_html(measurement_table, columns=display_columns)}
<p class="note">Positive numbers use neutral text. Adverse values are red.
Green is reserved for explicit status words.</p>

<h2>Strategy equity versus NQ</h2>
<img src="sizing_equity_vs_nq.png" alt="Sizing equity and NQ benchmark">
<p class="note">The NQ line is a normalized session-close price benchmark
starting at $100,000. It is not literal one-contract futures buy-and-hold P&amp;L,
because leverage, rolls, financing and margin are not modeled.</p>

<h2>Drawdown comparison</h2>
<img src="sizing_drawdowns.png" alt="Sizing drawdowns">

<h2>Did sizing make initial risk more consistent?</h2>
<img src="initial_risk_distribution.png" alt="Initial risk distribution">
<p>The coefficient of variation in the six-row table is risk standard deviation
divided by average risk. A lower value means initial dollar risk varied less
from trade to trade.</p>

<h2>Contract quantities and skipped trades</h2>
<img src="contract_count_distribution.png" alt="Contract distribution">
{_table_html(measurement_table, columns=practical_columns)}

<h2>Consistency through time</h2>
<img src="annual_sizing_comparison.png" alt="Annual sizing comparison">
<img src="monthly_sizing_heatmap.png" alt="Monthly sizing heatmap">

<h2>Paired session bootstrap</h2>
{_table_html(bootstrap_frame)}
<p class="note">Each comparison resampled the same evaluation sessions on both
sides. Both NQ and the complete multi-contract MNQ position are already recorded
in actual US dollars, so no extra ten-times conversion is applied. This
report-only bootstrap does not confirm the signal edge or impose a pass/fail
gate.</p>

<h2>Research context and limits</h2>
<div class="panel">
<ul>
<li>EXP-010 signal context: <span class="status-good">LOCKED</span>;
selection-aware MCPT p={float(decision['signal_context']['exp010_selection_aware_mcpt_p_value']):.6f}.</li>
<li>EXP-011 uses previously viewed 2019–2025 data and is not independent
confirmation.</li>
<li>No target-risk optimization, account-risk optimization, compounding,
margin model, new MCPT, composite score, or automatic winner was used.</li>
<li>Paper trading authorized: No. Live trading authorized: No.</li>
</ul>
</div>
</main></body></html>"""
    path = output_dir / "report.html"
    path.write_text(page, encoding="utf-8")
    return path
