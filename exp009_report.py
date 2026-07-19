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
from exp009_measurements import family_measurement_summary


FAMILY_LABELS = {
    "orb_pullback_continuation": "ORB pullback continuation",
    "failed_orb_reversal": "Failed ORB reversal",
    "vwap_mean_reversion": "VWAP mean reversion",
    "vwap_trend_pullback": "VWAP trend pullback",
    "intraday_compression_breakout": "Compression breakout",
    "opening_drive_continuation": "Opening drive continuation",
}


def _format_value(column: str, value: Any) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "—"
    if isinstance(value, (bool, np.bool_)):
        return "Yes" if value else "No"
    if isinstance(value, (int, np.integer)):
        return f"{int(value):,}"
    if isinstance(value, (float, np.floating)):
        if "rate" in column or "fraction" in column or "percent" in column:
            return f"{float(value):.2%}"
        if "usd" in column or "profit" in column or "drawdown" in column:
            return f"${float(value):,.2f}"
        return f"{float(value):,.4f}"
    return str(value)


def _cell_class(column: str, value: Any) -> str:
    text = str(value).upper()
    if text in {"MEASURED_NOT_VALIDATED", "PASS", "ACCEPTED", "LOCKED"}:
        return "status-good"
    if text in {"REJECTED", "FAIL", "FAILED"}:
        return "adverse"
    if isinstance(value, (int, float, np.number)) and float(value) < 0:
        return "adverse"
    if column in {
        "low_sample",
        "concentrated_activity",
        "cost_fragile",
        "mnq_divergence",
    } and bool(value):
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
    rows = []
    for _, row in local.iterrows():
        cells = []
        for column in local.columns:
            value = row[column]
            css = _cell_class(column, value)
            cells.append(
                f'<td class="{css}">'
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


def _save_pareto_charts(
    candidate_table: pd.DataFrame,
    report_dir: Path,
) -> list[Path]:
    paths: list[Path] = []
    colors = plt.cm.tab10(
        pd.Categorical(candidate_table["family_id"]).codes
        % 10
    )
    chart_specs = [
        (
            "trade_profit_factor",
            "maximum_drawdown_usd",
            "Profit Factor",
            "Maximum drawdown ($)",
            "pareto_profit_factor_drawdown.png",
        ),
        (
            "win_rate",
            "payoff_ratio",
            "Win rate",
            "Payoff ratio",
            "pareto_win_rate_payoff.png",
        ),
        (
            "average_trade_to_round_trip_cost",
            "completed_trades",
            "Average trade / round-trip cost",
            "Completed trades",
            "pareto_trade_quality_count.png",
        ),
        (
            "net_profit_to_drawdown",
            "longest_drawdown_duration_trades",
            "Net profit / maximum drawdown",
            "Longest drawdown (trades)",
            "pareto_efficiency_duration.png",
        ),
    ]
    for x, y, x_label, y_label, filename in chart_specs:
        figure, axis = plt.subplots(figsize=(11, 6.5))
        axis.scatter(
            candidate_table[x],
            candidate_table[y],
            c=colors,
            s=np.where(
                candidate_table["pareto_nondominated"], 90, 45
            ),
            alpha=0.85,
            edgecolors=np.where(
                candidate_table["pareto_nondominated"],
                "#f8fafc",
                "none",
            ),
        )
        for _, record in candidate_table.iterrows():
            axis.annotate(
                record["candidate_id"],
                (record[x], record[y]),
                fontsize=6,
                alpha=0.78,
                xytext=(3, 3),
                textcoords="offset points",
            )
        axis.set_xlabel(x_label)
        axis.set_ylabel(y_label)
        axis.grid(alpha=0.2)
        figure.tight_layout()
        path = report_dir / filename
        figure.savefig(path, dpi=150, facecolor="#0b1220")
        plt.close(figure)
        paths.append(path)
    return paths


def _save_equity_benchmark_chart(
    candidate_results: Mapping[str, Exp009Result],
    arrays: Exp009Arrays,
    report_dir: Path,
) -> Path:
    session_dates = pd.to_datetime(arrays.session_dates)
    benchmark = 100_000.0 * arrays.close[:, -1] / arrays.close[0, -1]
    figure, axis = plt.subplots(figsize=(13, 7))
    axis.plot(
        session_dates,
        benchmark,
        color="#94a3b8",
        linewidth=2.2,
        label="NQ normalized price benchmark",
    )
    for candidate_id, result in candidate_results.items():
        session_pnl = (
            result.trades.groupby("session_date")["net_pnl_usd"].sum()
            if not result.trades.empty
            else pd.Series(dtype=float)
        )
        pnl_path = pd.Series(
            arrays.session_dates, index=arrays.session_dates
        ).map(session_pnl).fillna(0.0)
        equity = 100_000.0 + pnl_path.cumsum().to_numpy(dtype=float)
        axis.plot(
            session_dates,
            equity,
            linewidth=0.85,
            alpha=0.46,
            label=candidate_id,
        )
    axis.axhline(100_000.0, color="#64748b", linestyle="--", linewidth=1)
    axis.set_title(
        "All 24 candidate equity paths versus normalized NQ benchmark"
    )
    axis.set_ylabel("Normalized starting value ($100,000)")
    axis.grid(alpha=0.18)
    axis.legend(
        fontsize=5,
        ncol=3,
        loc="upper left",
        frameon=False,
    )
    figure.tight_layout()
    path = report_dir / "candidate_equity_vs_nq_benchmark.png"
    figure.savefig(path, dpi=160, facecolor="#0b1220")
    plt.close(figure)
    return path


def _save_family_chart(
    family_table: pd.DataFrame,
    report_dir: Path,
) -> Path:
    local = family_table.copy()
    local["label"] = local["family_id"].map(FAMILY_LABELS)
    figure, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    axes[0].barh(local["label"], local["median_profit_factor"])
    axes[0].axvline(1.0, color="#ef4444", linewidth=1)
    axes[0].set_title("Median Profit Factor by family")
    axes[1].barh(local["label"], local["median_net_profit_usd"])
    axes[1].axvline(0.0, color="#ef4444", linewidth=1)
    axes[1].set_title("Median net profit by family")
    for axis in axes:
        axis.grid(axis="x", alpha=0.2)
    figure.tight_layout()
    path = report_dir / "family_measurement_comparison.png"
    figure.savefig(path, dpi=150, facecolor="#0b1220")
    plt.close(figure)
    return path


def _monthly_matrix(
    results: list[Exp009Result],
) -> tuple[np.ndarray, list[str], list[str]]:
    all_months: set[str] = set()
    monthly_by_candidate: dict[str, pd.Series] = {}
    for result in results:
        trades = result.trades
        if trades.empty:
            monthly = pd.Series(dtype=float)
        else:
            month = pd.to_datetime(
                trades["session_date"]
            ).dt.to_period("M").astype(str)
            monthly = trades.assign(month=month).groupby("month")[
                "net_pnl_usd"
            ].sum()
        monthly_by_candidate[result.candidate.candidate_id] = monthly
        all_months.update(monthly.index)
    months = sorted(all_months)
    matrix = np.array(
        [
            [
                float(monthly_by_candidate[candidate_id].get(month, 0.0))
                for month in months
            ]
            for candidate_id in monthly_by_candidate
        ],
        dtype=float,
    )
    return matrix, list(monthly_by_candidate), months


def _save_family_diagnostics(
    *,
    family_id: str,
    results: list[Exp009Result],
    arrays: Exp009Arrays,
    candidate_table: pd.DataFrame,
    report_dir: Path,
) -> dict[str, Path]:
    prefix = family_id
    paths: dict[str, Path] = {}

    # The four locked candidate equity curves are shown together. No curve is
    # labelled as the winner.
    session_dates = pd.to_datetime(arrays.session_dates)
    benchmark = 100_000.0 * arrays.close[:, -1] / arrays.close[0, -1]
    figure, axis = plt.subplots(figsize=(12, 6))
    axis.plot(
        session_dates,
        benchmark,
        color="#94a3b8",
        linewidth=2,
        label="NQ normalized price benchmark",
    )
    for result in results:
        session_pnl = (
            result.trades.groupby("session_date")["net_pnl_usd"].sum()
            if not result.trades.empty
            else pd.Series(dtype=float)
        )
        daily = pd.Series(arrays.session_dates).map(session_pnl).fillna(0.0)
        axis.plot(
            session_dates,
            100_000.0 + daily.cumsum(),
            linewidth=1.25,
            label=result.candidate.candidate_id,
        )
    axis.axhline(100_000.0, color="#64748b", linestyle="--", linewidth=1)
    axis.set_title(f"{FAMILY_LABELS[family_id]} equity comparison")
    axis.set_ylabel("Normalized starting value ($100,000)")
    axis.grid(alpha=0.2)
    axis.legend(fontsize=7, frameon=False)
    figure.tight_layout()
    path = report_dir / f"{prefix}_equity_benchmark.png"
    figure.savefig(path, dpi=150, facecolor="#0b1220")
    plt.close(figure)
    paths["equity"] = path

    matrix, candidate_ids, months = _monthly_matrix(results)
    figure, axis = plt.subplots(figsize=(14, 3.8))
    if matrix.size and months:
        maximum = float(np.nanmax(np.abs(matrix)))
        maximum = maximum if maximum > 0 else 1.0
        image = axis.imshow(
            matrix,
            aspect="auto",
            cmap="RdBu",
            vmin=-maximum,
            vmax=maximum,
        )
        figure.colorbar(image, ax=axis, label="Monthly net P&L ($)")
        tick_positions = np.arange(0, len(months), max(1, len(months) // 12))
        axis.set_xticks(tick_positions)
        axis.set_xticklabels(
            [months[index] for index in tick_positions],
            rotation=45,
            ha="right",
            fontsize=7,
        )
    axis.set_yticks(np.arange(len(candidate_ids)))
    axis.set_yticklabels(candidate_ids, fontsize=7)
    axis.set_title(f"{FAMILY_LABELS[family_id]} monthly P&L heatmap")
    figure.tight_layout()
    path = report_dir / f"{prefix}_monthly_heatmap.png"
    figure.savefig(path, dpi=150, facecolor="#0b1220")
    plt.close(figure)
    paths["monthly"] = path

    figure, axes = plt.subplots(1, 2, figsize=(13, 5))
    holding_values = [
        result.trades["holding_minutes"].to_numpy(dtype=float)
        if "holding_minutes" in result.trades
        else np.array([])
        for result in results
    ]
    if any(len(values) for values in holding_values):
        axes[0].boxplot(
            holding_values,
            tick_labels=[
                result.candidate.candidate_id for result in results
            ],
            showfliers=False,
        )
    axes[0].tick_params(axis="x", rotation=35, labelsize=7)
    axes[0].set_ylabel("Holding minutes")
    axes[0].set_title("Holding-time distribution")

    exit_labels = sorted(
        {
            str(reason)
            for result in results
            if "exit_reason" in result.trades
            for reason in result.trades["exit_reason"].dropna().unique()
        }
    )
    bottom = np.zeros(len(results))
    for reason in exit_labels:
        counts = np.array(
            [
                int((result.trades["exit_reason"] == reason).sum())
                if "exit_reason" in result.trades
                else 0
                for result in results
            ]
        )
        axes[1].bar(
            [result.candidate.candidate_id for result in results],
            counts,
            bottom=bottom,
            label=reason,
        )
        bottom += counts
    axes[1].tick_params(axis="x", rotation=35, labelsize=7)
    axes[1].set_ylabel("Completed trades")
    axes[1].set_title("Exit-reason distribution")
    if exit_labels:
        axes[1].legend(fontsize=7, frameon=False)
    figure.tight_layout()
    path = report_dir / f"{prefix}_trade_behaviour.png"
    figure.savefig(path, dpi=150, facecolor="#0b1220")
    plt.close(figure)
    paths["behaviour"] = path

    local = candidate_table.set_index("candidate_id").loc[
        [result.candidate.candidate_id for result in results]
    ]
    figure, axes = plt.subplots(1, 2, figsize=(13, 5))
    axes[0].bar(
        local.index,
        local["top_5_trade_profit_contribution"],
    )
    axes[0].set_title("Profit share from top five trades")
    axes[0].set_ylabel("Share of total net profit")
    axes[1].bar(
        local.index,
        local["best_year_profit_contribution"],
    )
    axes[1].set_title("Profit share from best year")
    axes[1].set_ylabel("Share of total net profit")
    for axis in axes:
        axis.tick_params(axis="x", rotation=35, labelsize=7)
        axis.axhline(0.0, color="#ef4444", linewidth=1)
        axis.grid(axis="y", alpha=0.2)
    figure.tight_layout()
    path = report_dir / f"{prefix}_profit_concentration.png"
    figure.savefig(path, dpi=150, facecolor="#0b1220")
    plt.close(figure)
    paths["concentration"] = path
    return paths


def build_exp009_report(
    *,
    candidate_table: pd.DataFrame,
    nq_results: Mapping[str, Exp009Result],
    arrays: Exp009Arrays,
    report_dir: Path,
    metadata: Mapping[str, Any],
) -> Path:
    if len(candidate_table) != 24:
        raise ValueError("EXP-009 report requires all 24 candidates.")
    if set(candidate_table["candidate_id"]) != set(nq_results):
        raise ValueError("EXP-009 report candidate results are incomplete.")

    report_dir.mkdir(parents=True, exist_ok=True)
    family_table = family_measurement_summary(candidate_table)
    _save_pareto_charts(candidate_table, report_dir)
    _save_equity_benchmark_chart(nq_results, arrays, report_dir)
    _save_family_chart(family_table, report_dir)
    family_assets: dict[str, dict[str, Path]] = {}
    for family_id in FAMILY_LABELS:
        family_assets[family_id] = _save_family_diagnostics(
            family_id=family_id,
            results=[
                nq_results[candidate_id]
                for candidate_id in candidate_table.loc[
                    candidate_table["family_id"] == family_id,
                    "candidate_id",
                ]
            ],
            arrays=arrays,
            candidate_table=candidate_table,
            report_dir=report_dir,
        )

    visible_columns = [
        "candidate_id",
        "family_id",
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

    family_sections = []
    for family_id in FAMILY_LABELS:
        subset = candidate_table.loc[
            candidate_table["family_id"] == family_id
        ]
        profitable = int((subset["net_profit_usd"] > 0).sum())
        cost_resilient = int(
            (subset["two_tick_net_profit_usd"] > 0).sum()
        )
        divergent = int(subset["mnq_divergence"].sum())
        family_sections.append(
            f"<section><h2>{html.escape(FAMILY_LABELS[family_id])}</h2>"
            "<p>Four locked variations were measured under the same "
            "NQ/MNQ data, costs, one-contract sizing and one-minute "
            "execution rules. These measurements describe the family; "
            "they do not validate an edge.</p>"
            f"<p><strong>What happened:</strong> {profitable} of 4 "
            f"candidates had positive base-cost NQ net profit, "
            f"{cost_resilient} of 4 remained positive at two ticks of "
            f"slippage per side, and {divergent} showed NQ/MNQ Profit "
            "Factors on opposite sides of 1.0.</p>"
            '<div class="grid">'
            f'<img class="chart" src="{family_id}_equity_benchmark.png" '
            'alt="Family equity and normalized NQ benchmark">'
            f'<img class="chart" src="{family_id}_monthly_heatmap.png" '
            'alt="Family monthly heatmap">'
            f'<img class="chart" src="{family_id}_trade_behaviour.png" '
            'alt="Family trade behaviour">'
            f'<img class="chart" src="{family_id}_profit_concentration.png" '
            'alt="Family profit concentration">'
            "</div>"
            + _table_html(subset, columns=visible_columns)
            + "</section>"
        )

    positive_candidates = int((candidate_table["net_profit_usd"] > 0).sum())
    cost_resilient_candidates = int(
        (candidate_table["two_tick_net_profit_usd"] > 0).sum()
    )
    nondominated_candidates = int(
        candidate_table["pareto_nondominated"].sum()
    )
    flagged_candidates = int(
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
<title>EXP-009 Strategy Discovery Tournament</title>
<style>
:root {{
  color-scheme: dark;
  --bg:#07101d; --panel:#0f1b2d; --panel2:#132238;
  --text:#e5edf7; --muted:#94a3b8; --line:#263850;
  --accent:#60a5fa; --adverse:#f87171; --status:#4ade80;
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
p,li {{ max-width:1050px; }}
.muted {{ color:var(--muted); }}
.status-good {{ color:var(--status); font-weight:inherit; }}
.adverse {{ color:var(--adverse); font-weight:inherit; }}
.grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr));
  gap:18px; }}
.chart {{ width:100%; border-radius:10px; background:#0b1220; }}
.table-scroll {{ overflow:auto; }}
table {{ border-collapse:collapse; width:100%; min-width:1050px; }}
th,td {{ border-bottom:1px solid var(--line); padding:9px 10px;
  text-align:right; white-space:nowrap; font-weight:400; }}
th {{ color:#bfdbfe; background:var(--panel2); position:sticky; top:0; }}
th:first-child,td:first-child,th:nth-child(2),td:nth-child(2) {{
  text-align:left;
}}
code,pre {{ background:#081321; border:1px solid var(--line);
  border-radius:8px; padding:2px 6px; }}
pre {{ padding:15px; overflow:auto; color:var(--muted); }}
@media(max-width:900px) {{ .grid {{ grid-template-columns:1fr; }}
  main {{ padding:14px; }} }}
</style>
</head>
<body><main>
<section>
  <h1>EXP-009 — Multi-Strategy Discovery Tournament</h1>
  <p class="muted">Six strategy families · 24 locked candidates · NQ primary
  measurement · MNQ implementation comparison · 2019–2025 frozen sessions</p>
  <p><span class="status-good">Measured, not validated.</span> EXP-009 is a
  broad discovery screen. It does not declare a winner, confirm an edge,
  authorize paper trading, or authorize live trading.</p>
</section>
<section>
  <h2>What we tested and how</h2>
  <p>We measured four locked versions of each of six structurally different
  cash-session strategies: ORB pullback continuation, failed ORB reversal,
  VWAP mean reversion, VWAP trend pullback, compression breakout and opening
  drive continuation. Each candidate used completed five-minute signals,
  entered at the next five-minute open, and was executed chronologically
  with one-minute bars.</p>
  <p>All candidates used one NQ contract and one MNQ contract, the same frozen
  1,639-session data, the same commissions, one tick of base slippage per side,
  a conservative stop-first rule when both levels touched within one minute,
  and a 15:55 New York forced exit. NQ was also measured at zero and two ticks
  of slippage per side.</p>
  <p>No MCPT, bootstrap, family optimization, automatic score or pass/fail
  gate was run. Those expensive tests are deferred until you review the
  measurements and choose no more than three personally attractive finalists.</p>
</section>
<section>
  <h2>How to read the results</h2>
  <p>Each point and table row describes a trade-off. A candidate can offer a
  higher win rate but a smaller payoff, or lower drawdown but lower net profit.
  Larger outlined points on the Pareto charts are not dominated across the
  locked comparison dimensions. That is context, not a recommendation.</p>
  <p>Positive numbers remain neutral. Losses, drawdowns and adverse flags are
  red. Green is reserved for status words.</p>
</section>
<section>
  <h2>What happened</h2>
  <p>{positive_candidates} of 24 candidates produced positive base-cost NQ
  net profit. {cost_resilient_candidates} remained positive with two ticks
  of slippage per side. {nondominated_candidates} appear on the
  multi-dimensional Pareto frontier, while {flagged_candidates} carry at
  least one reliability warning for sample size, activity concentration,
  cost fragility or NQ/MNQ divergence.</p>
  <p>This is a measurement summary, not a winner announcement. The family
  sections below show monthly behaviour, holding time, exits, profit
  concentration and equity versus the same NQ benchmark so you can judge
  what characteristics you actually prefer.</p>
</section>
<section>
  <h2>Strategy equity versus NQ</h2>
  <p>The NQ line is a normalized session-close price benchmark beginning at
  $100,000. It is not literal one-contract futures buy-and-hold P&amp;L because
  rolls, leverage, margin and financing are not modeled.</p>
  <img class="chart" src="candidate_equity_vs_nq_benchmark.png"
       alt="Candidate equity paths versus normalized NQ benchmark">
</section>
<section>
  <h2>Family-level measurements</h2>
  <img class="chart" src="family_measurement_comparison.png"
       alt="Family measurement comparison">
  {_table_html(family_table)}
</section>
<section>
  <h2>Pareto views</h2>
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
  {_table_html(candidate_table, columns=visible_columns)}
</section>
{''.join(family_sections)}
<section>
  <h2>What happens next</h2>
  <p>Review all candidates for profitability, win rate, payoff, drawdown,
  cost resilience, consistency and practical fit. You may choose up to three
  finalists. Each finalist then requires a new preregistered experiment for
  family-specific optimization and expensive statistical validation.</p>
  <p class="adverse">No paper or live trading is authorized by EXP-009.</p>
</section>
<section>
  <h2>Protected run metadata</h2>
  <pre>{metadata_text}</pre>
</section>
</main></body></html>"""
    path = report_dir / "report.html"
    path.write_text(document, encoding="utf-8")
    return path
