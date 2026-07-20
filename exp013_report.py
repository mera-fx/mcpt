from __future__ import annotations

import html
from pathlib import Path
from typing import Any, Mapping

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from exp009_engine import Exp009Result, profit_factor
from exp012_engine import Exp012Arrays
from exp013_preregistration import FINALIST_CANDIDATES
from report_chart_style import save_report_figure


DISPLAY_NAMES = {
    "gap_fade_0p50_1r": "Gap fade · 0.50 fraction · 1R",
    "premarket_continuation_0p50_time": (
        "Premarket continuation · 0.50 fraction · time exit"
    ),
    "premarket_continuation_0p75_time": (
        "Premarket continuation · 0.75 fraction · time exit"
    ),
}


def _save_figure(fig: Any, path: Path) -> None:
    fig.patch.set_facecolor("white")
    for axis in fig.axes:
        axis.set_facecolor("white")
        axis.tick_params(colors="#172033")
        axis.xaxis.label.set_color("#172033")
        axis.yaxis.label.set_color("#172033")
        axis.title.set_color("#172033")
    save_report_figure(
        fig,
        path,
        dpi=155,
        bbox_inches="tight",
    )
    plt.close(fig)


def _session_equity(
    arrays: Exp012Arrays,
    result: Exp009Result,
) -> np.ndarray:
    pnl = (
        result.trades.groupby("session_date")["net_pnl_usd"].sum()
        if not result.trades.empty
        else pd.Series(dtype=float)
    )
    return (
        100_000.0
        + pd.Series(arrays.session_dates).map(pnl).fillna(0.0).cumsum()
    ).to_numpy(dtype=float)


def _drawdown(values: np.ndarray) -> np.ndarray:
    peaks = np.maximum.accumulate(values)
    return values - peaks


def _strategy_charts(
    *,
    directory: Path,
    arrays: Exp012Arrays,
    nq_results: Mapping[str, Exp009Result],
    walk_forward: pd.DataFrame,
    cost_sensitivity: pd.DataFrame,
    mcpt: pd.DataFrame,
    real_maximum_pf: float,
) -> None:
    dates = pd.to_datetime(arrays.session_dates)
    benchmark = (
        100_000.0
        * arrays.cash.close[:, -1]
        / arrays.cash.close[0, -1]
    )
    fig, axis = plt.subplots(figsize=(14, 6.6))
    axis.plot(dates, benchmark, color="#667085", lw=2.0, label="NQ benchmark")
    for candidate_id, result in nq_results.items():
        axis.plot(
            dates,
            _session_equity(arrays, result),
            lw=1.7,
            label=DISPLAY_NAMES[candidate_id],
        )
    axis.axhline(100_000, color="#64748b", ls="--", lw=1)
    axis.set_title("Normalized strategy equity versus NQ price benchmark")
    axis.set_ylabel("Normalized value ($)")
    axis.grid(alpha=0.2)
    axis.legend(fontsize=8, ncol=2)
    _save_figure(fig, directory / "equity_vs_benchmark.png")

    fig, axis = plt.subplots(figsize=(14, 5.4))
    for candidate_id, result in nq_results.items():
        axis.plot(
            dates,
            _drawdown(_session_equity(arrays, result)),
            lw=1.6,
            label=DISPLAY_NAMES[candidate_id],
        )
    axis.axhline(0, color="#64748b", lw=1)
    axis.set_title("Strategy drawdown through time")
    axis.set_ylabel("Drawdown ($)")
    axis.grid(alpha=0.2)
    axis.legend(fontsize=8)
    _save_figure(fig, directory / "drawdown_comparison.png")

    annual = []
    for candidate_id, result in nq_results.items():
        local = result.yearly_results[["year", "net_profit_usd"]].copy()
        local["candidate_id"] = candidate_id
        annual.append(local)
    annual_frame = pd.concat(annual, ignore_index=True)
    pivot = annual_frame.pivot(
        index="year", columns="candidate_id", values="net_profit_usd"
    ).fillna(0)
    fig, axis = plt.subplots(figsize=(14, 5.4))
    pivot.plot(kind="bar", ax=axis)
    axis.set_title("Annual NQ net profit by finalist")
    axis.set_ylabel("Net profit ($)")
    axis.grid(axis="y", alpha=0.2)
    axis.legend(
        [DISPLAY_NAMES.get(value, value) for value in pivot.columns],
        fontsize=8,
    )
    _save_figure(fig, directory / "annual_comparison.png")

    monthly_rows = []
    for candidate_id, result in nq_results.items():
        local = result.trades.copy()
        local["month"] = pd.to_datetime(local["session_date"]).dt.to_period(
            "M"
        ).astype(str)
        grouped = local.groupby("month")["net_pnl_usd"].sum()
        monthly_rows.append(grouped.rename(candidate_id))
    monthly = pd.concat(monthly_rows, axis=1).fillna(0).T
    fig, axis = plt.subplots(figsize=(16, 3.8))
    image = axis.imshow(monthly.to_numpy(), aspect="auto", cmap="RdBu_r")
    axis.set_yticks(range(len(monthly.index)))
    axis.set_yticklabels(
        [DISPLAY_NAMES[value] for value in monthly.index], fontsize=8
    )
    step = max(1, len(monthly.columns) // 12)
    ticks = np.arange(0, len(monthly.columns), step)
    axis.set_xticks(ticks)
    axis.set_xticklabels(
        [monthly.columns[index] for index in ticks],
        rotation=45,
        ha="right",
        fontsize=7,
    )
    axis.set_title("Monthly NQ net-profit heatmap")
    fig.colorbar(image, ax=axis, label="Net profit ($)")
    _save_figure(fig, directory / "monthly_heatmap.png")

    fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=False)
    for candidate_id, result in nq_results.items():
        pnl = result.trades["net_pnl_usd"].to_numpy(dtype=float)
        if len(pnl) >= 50:
            rolling_pf = pd.Series(
                [
                    profit_factor(pnl[index - 49:index + 1])
                    for index in range(49, len(pnl))
                ]
            )
            axes[0].plot(
                np.arange(50, len(pnl) + 1),
                rolling_pf,
                label=DISPLAY_NAMES[candidate_id],
            )
            axes[1].plot(
                np.arange(50, len(pnl) + 1),
                pd.Series(pnl).rolling(50).mean().dropna(),
                label=DISPLAY_NAMES[candidate_id],
            )
    axes[0].axhline(1, color="#64748b", ls="--")
    axes[0].set_title("Rolling 50-trade Profit Factor")
    axes[1].axhline(0, color="#64748b", ls="--")
    axes[1].set_title("Rolling 50-trade average")
    axes[1].set_xlabel("Completed trade number")
    axes[1].set_ylabel("Average trade ($)")
    for axis in axes:
        axis.grid(alpha=0.2)
        axis.legend(fontsize=8)
    _save_figure(fig, directory / "rolling_measurements.png")

    fig, axis = plt.subplots(figsize=(12, 4.8))
    colors = np.where(
        walk_forward["test_net_profit_usd"].astype(float) < 0,
        "#dc2626",
        "#5b8def",
    )
    axis.bar(
        walk_forward["test_year"].astype(str),
        walk_forward["test_net_profit_usd"].astype(float),
        color=colors,
    )
    axis.axhline(0, color="#64748b", lw=1)
    axis.set_title("Anchored walk-forward test profit")
    axis.set_ylabel("Net profit ($)")
    axis.grid(axis="y", alpha=0.2)
    _save_figure(fig, directory / "walk_forward.png")

    fig, axis = plt.subplots(figsize=(12, 5))
    for candidate_id, group in cost_sensitivity.groupby("candidate_id"):
        axis.plot(
            group["slippage_ticks_per_side"],
            group["net_profit_usd"],
            marker="o",
            label=DISPLAY_NAMES[candidate_id],
        )
    axis.axhline(0, color="#64748b", lw=1)
    axis.set_title("NQ cost sensitivity")
    axis.set_xlabel("Slippage ticks per side")
    axis.set_ylabel("Net profit ($)")
    axis.grid(alpha=0.2)
    axis.legend(fontsize=8)
    _save_figure(fig, directory / "cost_sensitivity.png")

    fig, axis = plt.subplots(figsize=(12, 5))
    axis.hist(
        mcpt["maximum_trade_profit_factor"].astype(float),
        bins=35,
        color="#94a3b8",
        edgecolor="white",
    )
    axis.axvline(
        real_maximum_pf,
        color="#dc2626",
        lw=2,
        label=f"Real 24-candidate maximum PF: {real_maximum_pf:.4f}",
    )
    axis.set_title(
        "Discovery-wide MCPT: maximum PF after repeating all 24 candidates"
    )
    axis.set_xlabel("Maximum Profit Factor in each randomized search")
    axis.set_ylabel("Permutations")
    axis.legend()
    _save_figure(fig, directory / "discovery_wide_mcpt.png")

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    for axis, (candidate_id, result) in zip(axes, nq_results.items()):
        axis.hist(
            result.trades["net_pnl_usd"].astype(float),
            bins=28,
            color="#5b8def",
            edgecolor="white",
        )
        axis.axvline(0, color="#dc2626", lw=1)
        axis.set_title(DISPLAY_NAMES[candidate_id], fontsize=9)
        axis.set_xlabel("Trade P&L ($)")
    axes[0].set_ylabel("Trades")
    _save_figure(fig, directory / "trade_distributions.png")


def _format_value(column: str, value: Any) -> str:
    if pd.isna(value):
        return "—"
    if isinstance(value, (bool, np.bool_)):
        return "Yes" if bool(value) else "No"
    if column in {"win_rate"} or "probability" in column:
        return f"{100 * float(value):.2f}%"
    if any(
        token in column
        for token in (
            "profit_usd",
            "drawdown_usd",
            "trade_usd",
        )
    ):
        return f"${float(value):,.2f}"
    if "profit_factor" in column or "ratio" in column:
        return f"{float(value):.4f}"
    if isinstance(value, (float, np.floating)):
        return f"{float(value):,.4f}"
    return html.escape(str(value))


def _table(frame: pd.DataFrame, columns: list[str]) -> str:
    labels = {
        "candidate_id": "Candidate",
        "completed_trades": "Trades",
        "trade_profit_factor": "Profit Factor",
        "win_rate": "Win rate",
        "net_profit_usd": "Net profit",
        "maximum_drawdown_usd": "Max drawdown",
        "net_profit_to_drawdown": "Net / drawdown",
        "average_trade_usd": "Average trade",
        "mnq_profit_factor": "MNQ PF",
        "two_tick_net_profit_usd": "Two-tick net",
        "test_year": "Test year",
        "selected_candidate_id": "Selected from training",
        "test_completed_trades": "Test trades",
        "test_trade_profit_factor": "Test PF",
        "test_net_profit_usd": "Test net",
        "slippage_ticks_per_side": "Ticks / side",
    }
    header = "".join(f"<th>{labels.get(c, c)}</th>" for c in columns)
    rows = []
    for record in frame[columns].to_dict(orient="records"):
        cells = []
        for column in columns:
            value = record[column]
            css = ""
            if (
                isinstance(value, (int, float, np.integer, np.floating))
                and float(value) < 0
            ):
                css = ' class="negative"'
            cells.append(
                f"<td{css}>{_format_value(column, value)}</td>"
            )
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return (
        '<div class="table-wrap"><table><thead><tr>'
        + header
        + "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></div>"
    )


def build_exp013_report(
    *,
    decision: Mapping[str, Any],
    candidate_table: pd.DataFrame,
    nq_results: Mapping[str, Exp009Result],
    nq_arrays: Exp012Arrays,
    walk_forward: pd.DataFrame,
    cost_sensitivity: pd.DataFrame,
    mcpt: pd.DataFrame,
    bootstrap: list[dict[str, Any]],
    output_dir: Path,
) -> Path:
    if set(nq_results) != set(DISPLAY_NAMES):
        raise ValueError("EXP-013 report requires all three finalists.")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    real_maximum = float(
        decision["mcpt"]["real_maximum_trade_profit_factor"]
    )
    _strategy_charts(
        directory=output_dir,
        arrays=nq_arrays,
        nq_results=nq_results,
        walk_forward=walk_forward,
        cost_sensitivity=cost_sensitivity,
        mcpt=mcpt,
        real_maximum_pf=real_maximum,
    )

    reasons = []
    for record in FINALIST_CANDIDATES:
        reasons.append(
            "<li><strong>"
            + html.escape(DISPLAY_NAMES[record["candidate_id"]])
            + "</strong> — "
            + html.escape(record["review_reason"])
            + " <span class=\"muted\">Limitation: "
            + html.escape(record["known_limitation"])
            + "</span></li>"
        )
    bootstrap_frame = pd.DataFrame.from_records(bootstrap)
    fixed_p = decision["mcpt"]["fixed_candidate_p_values"]
    bootstrap_frame["fixed_candidate_mcpt_p_value"] = (
        bootstrap_frame["candidate_id"].map(fixed_p)
    )
    evidence = decision["evaluation"]
    classification = html.escape(str(evidence["classification"]))
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>EXP-013 Extended-Context Validation</title>
<style>
:root{{--bg:#07111f;--panel:#101d31;--line:#29415f;--text:#edf3fb;
--muted:#a9b6c8;--blue:#68a5ff;--red:#ff6b75;--green:#4fca8a}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--text);
font:15px/1.58 Inter,Segoe UI,Arial,sans-serif}}
main{{max-width:1480px;margin:auto;padding:28px}} section{{background:var(--panel);
border:1px solid var(--line);border-radius:16px;padding:22px;margin:18px 0}}
h1{{font-size:30px;margin:0 0 8px}} h2{{color:var(--blue);margin-top:0}}
h3{{margin-bottom:8px}} .muted{{color:var(--muted)}} .status{{color:var(--green)}}
.negative{{color:var(--red)}} .callout{{border-left:4px solid var(--blue);
padding:12px 16px;background:#0b1729;border-radius:8px}}
img{{display:block;width:100%;height:auto;background:#fff;border-radius:10px;
margin:14px 0}} .grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));
gap:18px}} .table-wrap{{overflow:auto}} table{{border-collapse:collapse;width:100%;
background:#0b1729}} th,td{{padding:9px 11px;border-bottom:1px solid #223753;
text-align:right;white-space:nowrap}} th:first-child,td:first-child{{text-align:left}}
th{{color:#9cc2ff}} code{{color:#d7e8ff}} @media(max-width:900px){{.grid{{grid-template-columns:1fr}}}}
</style></head><body><main>
<header><div class="status">MEASURED HISTORICAL VALIDATION</div>
<h1>EXP-013 · Three-finalist extended-context validation</h1>
<p class="muted">Measurement first. Classification is secondary. No paper or live trading is authorized.</p></header>

<section><h2>What we tested and why</h2>
<p>EXP-013 revisits three review candidates chosen after the 24-candidate
EXP-012 tournament. It measures the same frozen 2020–2025 NQ/MNQ sessions,
the same fixed one-contract costs, and the same one-minute execution rules.
No strategy rule or threshold was changed.</p>
<ul>{''.join(reasons)}</ul>
<div class="callout"><strong>Important:</strong> the three candidates were
chosen after their EXP-012 results were visible. The discovery-wide MCPT
corrects the maximum Profit Factor search across all 24 candidates, but it
cannot turn the later human shortlist into an independently preselected test.</div>
</section>

<section><h2>How the strategies work</h2>
<div class="grid"><div><h3>Gap fade</h3>
<p>The strategy compares the opening gap with the previous complete cash
session’s high–low range. A fraction of <strong>0.50</strong> means the gap
is half as large as that prior range—not a 50% move in NQ. Example: if the
prior range was 200 points and today opens 100 points away, the fraction is
100 ÷ 200 = 0.50. If the first five-minute bar moves back against the gap,
the strategy enters at 09:35 toward the prior close. The first-bar outer
extreme is the stop; the target is 1R, with a 15:55 fallback exit.</p></div>
<div><h3>Premarket continuation</h3>
<p>The strategy measures the final 90-minute premarket move relative to its
own high–low range. A 0.75 fraction means a 75-point directional move inside
a 100-point premarket range—not a 75% price change. If the first cash bar
continues in that direction, it enters at 09:35, uses the opposite first-bar
extreme as the stop, and otherwise holds until 15:55. The 0.75 version is
stricter and therefore trades much less often.</p></div></div>
</section>

<section><h2>What happened</h2>
<p>{html.escape(str(decision["plain_english_summary"]))}</p>
{_table(candidate_table, ["candidate_id","completed_trades",
"trade_profit_factor","win_rate","net_profit_usd","maximum_drawdown_usd",
"net_profit_to_drawdown","average_trade_usd","mnq_profit_factor",
"two_tick_net_profit_usd"])}
<img src="equity_vs_benchmark.png" alt="Equity versus benchmark">
<img src="drawdown_comparison.png" alt="Drawdown comparison"></section>

<section><h2>Consistency and trade behaviour</h2>
<img src="annual_comparison.png" alt="Annual comparison">
<img src="monthly_heatmap.png" alt="Monthly heatmap">
<img src="rolling_measurements.png" alt="Rolling measurements">
<img src="trade_distributions.png" alt="Trade distributions"></section>

<section><h2>Anchored walk-forward selection</h2>
<p>For each test year, only earlier years selected among the three finalists.
These folds are temporal diagnostics, not untouched out-of-sample evidence,
because the families and shortlist were already influenced by the full
historical discovery process.</p>
{_table(walk_forward, ["test_year","selected_candidate_id",
"test_completed_trades","test_trade_profit_factor","test_net_profit_usd"])}
<img src="walk_forward.png" alt="Walk-forward results"></section>

<section><h2>Costs, bootstrap uncertainty and market comparison</h2>
<img src="cost_sensitivity.png" alt="Cost sensitivity">
{_table(bootstrap_frame, ["candidate_id","completed_trades",
"observed_trade_profit_factor","observed_average_trade_usd",
"profit_factor_probability_above_one",
"average_trade_probability_above_zero","fixed_candidate_mcpt_p_value"])}
</section>

<section><h2>Discovery-wide Monte Carlo permutation test</h2>
<p>Every randomized market repeated all 24 EXP-012 strategies. The primary
statistic is the best Profit Factor found in each full randomized search.
This is deliberately harder than testing only the three finalists.</p>
<p>Primary p-value: <strong>{float(decision["mcpt"]["discovery_wide_p_value"]):.6f}</strong>.
Randomized searches at least as strong as the real maximum:
<strong>{int(decision["mcpt"]["permutations_at_least_real"])}</strong> of
{int(decision["mcpt"]["permutations"])}.</p>
<img src="discovery_wide_mcpt.png" alt="Discovery-wide MCPT distribution"></section>

<section><h2>How to interpret the evidence</h2>
<p>Secondary classification: <strong>{classification}</strong>.</p>
<p>The classification limits what can be claimed; it does not erase the
measured return, drawdown, win rate, trade count, stability or practical
differences between the strategies. EXP-013 does not make an automatic
trading winner and does not authorize paper or live trading.</p></section>
</main></body></html>"""
    path = output_dir / "report.html"
    path.write_text(page, encoding="utf-8")
    return path
