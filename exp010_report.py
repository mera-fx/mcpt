from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, Mapping

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from exp009_engine import Exp009Arrays, Exp009Result


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
        if "rate" in column or "fraction" in column or "probability" in column:
            return f"{float(value):.2%}"
        if "usd" in column:
            return f"${float(value):,.2f}"
        if "p_value" in column:
            return f"{float(value):.6f}"
        return f"{float(value):,.4f}"
    return str(value)


def _cell_class(column: str, value: Any) -> str:
    text = str(value).upper()
    if text in {
        "PASS",
        "ACCEPTED",
        "LOCKED",
        "STRONG_HISTORICAL_EVIDENCE",
    }:
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
    local = table if columns is None else table[columns]
    header = "".join(
        f"<th>{html.escape(column.replace('_', ' ').title())}</th>"
        for column in local.columns
    )
    rows: list[str] = []
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
        + header
        + "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></div>"
    )


def _session_equity(
    result: Exp009Result,
    session_dates: np.ndarray,
) -> np.ndarray:
    session_pnl = (
        result.trades.groupby("session_date")["net_pnl_usd"].sum()
        if not result.trades.empty
        else pd.Series(dtype=float)
    )
    pnl = (
        pd.Series(session_dates)
        .map(session_pnl)
        .fillna(0.0)
        .to_numpy(dtype=float)
    )
    return 100_000.0 + np.cumsum(pnl)


def _save_equity_chart(
    results: Mapping[str, Exp009Result],
    arrays: Exp009Arrays,
    output_dir: Path,
) -> Path:
    dates = pd.to_datetime(arrays.session_dates)
    benchmark = 100_000.0 * arrays.close[:, -1] / arrays.close[0, -1]
    figure, axis = plt.subplots(figsize=(13, 7))
    axis.plot(
        dates,
        benchmark,
        color="#94a3b8",
        linewidth=2.2,
        label="NQ normalized price benchmark",
    )
    for candidate_id, result in results.items():
        axis.plot(
            dates,
            _session_equity(result, arrays.session_dates),
            linewidth=1.5,
            label=candidate_id,
        )
    axis.axhline(100_000.0, color="#64748b", linestyle="--", linewidth=1)
    axis.set_title("All four opening-drive equity paths versus NQ")
    axis.set_ylabel("Normalized starting value ($100,000)")
    axis.grid(alpha=0.18)
    axis.legend(frameon=False, fontsize=8, ncol=2)
    figure.tight_layout()
    path = output_dir / "equity_vs_nq_benchmark.png"
    figure.savefig(path, dpi=160, facecolor="#0b1220")
    plt.close(figure)
    return path


def _save_drawdown_chart(
    results: Mapping[str, Exp009Result],
    output_dir: Path,
    *,
    selected_id: str,
    reference_id: str,
) -> Path:
    figure, axis = plt.subplots(figsize=(13, 5.5))
    for candidate_id in dict.fromkeys((selected_id, reference_id)):
        result = results[candidate_id]
        axis.plot(
            pd.to_datetime(result.equity_curve["session_date"]),
            result.equity_curve["drawdown_usd"],
            linewidth=1.6,
            label=candidate_id,
        )
    axis.axhline(0.0, color="#64748b", linewidth=1)
    axis.set_title("Measurement leader and user-reference drawdowns")
    axis.set_ylabel("Drawdown ($)")
    axis.grid(alpha=0.18)
    axis.legend(frameon=False)
    figure.tight_layout()
    path = output_dir / "selected_reference_drawdown.png"
    figure.savefig(path, dpi=155, facecolor="#0b1220")
    plt.close(figure)
    return path


def _save_annual_chart(
    results: Mapping[str, Exp009Result],
    output_dir: Path,
) -> Path:
    records = []
    for candidate_id, result in results.items():
        for row in result.yearly_results.itertuples():
            records.append(
                {
                    "candidate_id": candidate_id,
                    "year": int(row.year),
                    "net_profit_usd": float(row.net_profit_usd),
                }
            )
    frame = pd.DataFrame.from_records(records)
    pivot = frame.pivot(
        index="year", columns="candidate_id", values="net_profit_usd"
    ).fillna(0.0)
    axis = pivot.plot(kind="bar", figsize=(13, 6.5), width=0.82)
    axis.axhline(0.0, color="#f87171", linewidth=1)
    axis.set_title("Annual NQ net profit by candidate")
    axis.set_ylabel("Net profit ($)")
    axis.grid(axis="y", alpha=0.18)
    axis.legend(frameon=False, fontsize=8)
    figure = axis.get_figure()
    figure.tight_layout()
    path = output_dir / "annual_candidate_comparison.png"
    figure.savefig(path, dpi=155, facecolor="#0b1220")
    plt.close(figure)
    return path


def _save_walk_forward_chart(
    walk_forward: pd.DataFrame,
    output_dir: Path,
) -> Path:
    figure, axis = plt.subplots(figsize=(11, 5.5))
    colors = np.where(
        walk_forward["test_net_profit_usd"].astype(float) < 0,
        "#f87171",
        "#60a5fa",
    )
    axis.bar(
        walk_forward["test_year"].astype(str),
        walk_forward["test_net_profit_usd"],
        color=colors,
    )
    axis.axhline(0.0, color="#94a3b8", linewidth=1)
    axis.set_title("Anchored walk-forward test net profit")
    axis.set_ylabel("Net profit ($)")
    axis.grid(axis="y", alpha=0.18)
    figure.tight_layout()
    path = output_dir / "walk_forward_net_profit.png"
    figure.savefig(path, dpi=155, facecolor="#0b1220")
    plt.close(figure)
    return path


def _save_cost_chart(
    cost_sensitivity: pd.DataFrame,
    output_dir: Path,
) -> Path:
    local = cost_sensitivity.loc[cost_sensitivity["symbol"].eq("NQ")]
    figure, axis = plt.subplots(figsize=(11, 5.5))
    for candidate_id, group in local.groupby("candidate_id", sort=False):
        axis.plot(
            group["slippage_ticks_per_side"],
            group["net_profit_usd"],
            marker="o",
            label=candidate_id,
        )
    axis.axhline(0.0, color="#f87171", linewidth=1)
    axis.set_xticks([0, 1, 2])
    axis.set_title("NQ cost sensitivity")
    axis.set_xlabel("Slippage ticks per side")
    axis.set_ylabel("Net profit ($)")
    axis.grid(alpha=0.18)
    axis.legend(frameon=False, fontsize=8, ncol=2)
    figure.tight_layout()
    path = output_dir / "cost_sensitivity.png"
    figure.savefig(path, dpi=155, facecolor="#0b1220")
    plt.close(figure)
    return path


def _save_mcpt_chart(
    mcpt: pd.DataFrame,
    output_dir: Path,
    *,
    real_selected_pf: float,
    real_reference_pf: float,
) -> Path:
    figure, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    axes[0].hist(
        mcpt["selected_trade_profit_factor"],
        bins=35,
        color="#2563eb",
        alpha=0.8,
    )
    axes[0].axvline(real_selected_pf, color="#f87171", linewidth=2)
    axes[0].set_title("Four-candidate selection-aware MCPT")
    axes[1].hist(
        mcpt["fixed_reference_trade_profit_factor"],
        bins=35,
        color="#64748b",
        alpha=0.8,
    )
    axes[1].axvline(real_reference_pf, color="#f87171", linewidth=2)
    axes[1].set_title("Fixed user-reference diagnostic")
    for axis in axes:
        axis.set_xlabel("Profit Factor")
        axis.grid(alpha=0.16)
    figure.tight_layout()
    path = output_dir / "mcpt_distributions.png"
    figure.savefig(path, dpi=155, facecolor="#0b1220")
    plt.close(figure)
    return path


def _save_trade_distribution(
    results: Mapping[str, Exp009Result],
    output_dir: Path,
    *,
    selected_id: str,
    reference_id: str,
) -> Path:
    figure, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    for axis, candidate_id in zip(
        axes, (selected_id, reference_id), strict=True
    ):
        axis.hist(
            results[candidate_id].trades["net_pnl_usd"],
            bins=35,
            color="#60a5fa",
            alpha=0.82,
        )
        axis.axvline(0.0, color="#f87171", linewidth=1)
        axis.set_title(candidate_id)
        axis.set_xlabel("Trade net P&L ($)")
        axis.grid(alpha=0.16)
    figure.tight_layout()
    path = output_dir / "selected_reference_trade_distribution.png"
    figure.savefig(path, dpi=155, facecolor="#0b1220")
    plt.close(figure)
    return path


def build_exp010_report(
    *,
    decision: Mapping[str, Any],
    candidate_table: pd.DataFrame,
    nq_results: Mapping[str, Exp009Result],
    nq_arrays: Exp009Arrays,
    walk_forward: pd.DataFrame,
    cost_sensitivity: pd.DataFrame,
    mcpt: pd.DataFrame,
    bootstrap: list[dict[str, Any]],
    output_dir: Path,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    selected_id = str(decision["selection"]["selected_candidate_id"])
    reference_id = str(decision["selection"]["user_reference_candidate_id"])
    _save_equity_chart(nq_results, nq_arrays, output_dir)
    _save_drawdown_chart(
        nq_results,
        output_dir,
        selected_id=selected_id,
        reference_id=reference_id,
    )
    _save_annual_chart(nq_results, output_dir)
    _save_walk_forward_chart(walk_forward, output_dir)
    _save_cost_chart(cost_sensitivity, output_dir)
    _save_mcpt_chart(
        mcpt,
        output_dir,
        real_selected_pf=float(
            decision["mcpt"]["real_selected_trade_profit_factor"]
        ),
        real_reference_pf=float(
            decision["mcpt"]["real_fixed_reference_trade_profit_factor"]
        ),
    )
    _save_trade_distribution(
        nq_results,
        output_dir,
        selected_id=selected_id,
        reference_id=reference_id,
    )

    evaluation = decision["evaluation"]
    classification = str(evaluation["classification"])
    classification_css = (
        "status-good"
        if classification == "STRONG_HISTORICAL_EVIDENCE"
        else "adverse"
        if classification == "WEAK_OR_INCONCLUSIVE_HISTORICAL_EVIDENCE"
        else ""
    )
    selected = candidate_table.loc[
        candidate_table["candidate_id"].eq(selected_id)
    ].iloc[0]
    reference = candidate_table.loc[
        candidate_table["candidate_id"].eq(reference_id)
    ].iloc[0]
    candidate_columns = [
        "candidate_id",
        "minimum_drive_fraction",
        "exit_mode",
        "completed_trades",
        "trade_profit_factor",
        "win_rate",
        "net_profit_usd",
        "maximum_drawdown_usd",
        "net_profit_to_drawdown",
        "average_trade_usd",
        "mnq_profit_factor",
        "two_tick_net_profit_usd",
        "profitable_years",
    ]
    bootstrap_table = pd.DataFrame.from_records(bootstrap)
    bootstrap_columns = [
        "candidate_id",
        "completed_trades",
        "observed_average_trade_usd",
        "observed_trade_profit_factor",
        "average_trade_probability_above_zero",
        "profit_factor_probability_above_one",
    ]
    metadata = html.escape(
        json.dumps(dict(decision), indent=2, default=str)
    )
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>EXP-010 Opening-Drive Deep Validation</title>
<style>
:root {{ color-scheme:dark; --bg:#07101d; --panel:#0f1b2d;
  --panel2:#132238; --text:#e5edf7; --muted:#94a3b8;
  --line:#263850; --accent:#60a5fa; --adverse:#f87171;
  --status:#4ade80; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--text);
  font:14px/1.55 Inter,Segoe UI,Arial,sans-serif; }}
main {{ max-width:1500px; margin:auto; padding:30px; }}
section {{ background:var(--panel); border:1px solid var(--line);
  border-radius:14px; padding:22px; margin-bottom:22px; }}
h1 {{ font-size:34px; margin:0 0 8px; }}
h2 {{ color:var(--accent); margin-top:0; }}
p,li {{ max-width:1080px; }}
.muted {{ color:var(--muted); }}
.status-good {{ color:var(--status); font-weight:inherit; }}
.adverse {{ color:var(--adverse); font-weight:inherit; }}
.grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr));
  gap:18px; }}
.chart {{ width:100%; border-radius:10px; background:#0b1220; }}
.table-scroll {{ overflow:auto; }}
table {{ border-collapse:collapse; width:100%; min-width:980px; }}
th,td {{ border-bottom:1px solid var(--line); padding:9px 10px;
  text-align:right; white-space:nowrap; font-weight:400; }}
th {{ color:#bfdbfe; background:var(--panel2); }}
th:first-child,td:first-child {{ text-align:left; }}
pre {{ background:#081321; border:1px solid var(--line);
  border-radius:8px; padding:15px; overflow:auto; color:var(--muted); }}
@media(max-width:900px) {{ .grid {{ grid-template-columns:1fr; }}
  main {{ padding:14px; }} }}
</style></head><body><main>
<section>
  <h1>EXP-010 — Opening-Drive Deep Validation</h1>
  <p class="muted">Four locked candidates · NQ primary · MNQ comparison ·
  five anchored folds · 1,000 selection-aware permutations</p>
  <p><span class="{classification_css}">{html.escape(classification.replace('_', ' ').title())}</span>
  is a secondary historical evidence label. The measurements below come
  first. No paper or live trading is authorized.</p>
</section>
<section>
  <h2>What we tested and how</h2>
  <p>EXP-010 retained all four opening-drive candidates discovered in
  EXP-009. Every candidate uses the 09:30–10:00 move, enters at 10:00 in
  the direction of that move, uses the opposite opening-range boundary as
  its stop, and is flat by 15:55. The candidates differ only in the minimum
  drive fraction and whether they use a 1.5R target.</p>
  <p>The primary MCPT repeated selection among all four candidates inside
  every randomized market. It corrects this four-candidate comparison, but
  it does not correct the earlier human choice of this family after viewing
  six families and 24 candidates in EXP-009.</p>
</section>
<section>
  <h2>What happened</h2>
  <p>The full-sample measurement leader was
  <code>{html.escape(selected_id)}</code>: {int(selected['completed_trades']):,}
  trades, Profit Factor {float(selected['trade_profit_factor']):.4f},
  win rate {float(selected['win_rate']):.2%}, net profit
  ${float(selected['net_profit_usd']):,.2f}, and maximum drawdown
  ${float(selected['maximum_drawdown_usd']):,.2f}.</p>
  <p>Your preferred reference remained
  <code>{html.escape(reference_id)}</code>: Profit Factor
  {float(reference['trade_profit_factor']):.4f}, win rate
  {float(reference['win_rate']):.2%}, and net profit
  ${float(reference['net_profit_usd']):,.2f}. The selection-aware p-value was
  {float(decision['mcpt']['selection_aware_p_value']):.6f}; the fixed-reference
  diagnostic p-value was
  {float(decision['mcpt']['fixed_reference_p_value']):.6f}.</p>
</section>
<section><h2>All four candidates</h2>
  {_table_html(candidate_table, columns=candidate_columns)}
</section>
<section><h2>Strategy versus the market</h2>
  <p>The benchmark is a normalized NQ session-close price path, not literal
  one-contract futures buy-and-hold P&amp;L.</p>
  <img class="chart" src="equity_vs_nq_benchmark.png"
       alt="Opening-drive equity versus NQ benchmark">
</section>
<section><h2>Risk, annual consistency and trade distribution</h2>
  <div class="grid">
    <img class="chart" src="selected_reference_drawdown.png"
         alt="Selected and reference drawdowns">
    <img class="chart" src="annual_candidate_comparison.png"
         alt="Annual candidate comparison">
    <img class="chart" src="selected_reference_trade_distribution.png"
         alt="Trade distributions">
    <img class="chart" src="cost_sensitivity.png"
         alt="Cost sensitivity">
  </div>
</section>
<section><h2>Anchored walk-forward measurement</h2>
  <img class="chart" src="walk_forward_net_profit.png"
       alt="Walk-forward test profit">
  {_table_html(walk_forward)}
</section>
<section><h2>Statistical uncertainty</h2>
  <p>The left MCPT distribution includes four-candidate reselection. The
  right side is the fixed preferred-reference diagnostic. Bootstrap
  intervals resample completed trades and do not independently confirm an
  edge.</p>
  <img class="chart" src="mcpt_distributions.png"
       alt="MCPT distributions">
  {_table_html(bootstrap_table, columns=bootstrap_columns)}
</section>
<section><h2>How to interpret this</h2>
  <p>The evidence label is
  <strong>{html.escape(evaluation['classification'].replace('_', ' ').title())}</strong>.
  It summarizes locked context checks but does not erase any strategy
  measurement or create an accept/reject lifecycle decision.</p>
  <p class="adverse">EXP-010 uses previously viewed historical data, does
  not correct the earlier six-family choice, and authorizes neither paper
  nor live trading.</p>
</section>
<section><h2>Protected result metadata</h2><pre>{metadata}</pre></section>
</main></body></html>"""
    path = output_dir / "report.html"
    path.write_text(document, encoding="utf-8")
    return path
