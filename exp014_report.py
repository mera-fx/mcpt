from __future__ import annotations

import html
from pathlib import Path
from typing import Any, Mapping

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from exp012_engine import Exp012Arrays
from exp014_preregistration import FINALIST_IDS, PAIR_DEFINITIONS
from report_chart_style import save_report_figure


DISPLAY_NAMES = {
    "gap_fade_0p50_1r": "Gap fade · 0.50 fraction · 1R",
    "premarket_continuation_0p50_time": (
        "Premarket continuation · 0.50 fraction · time exit"
    ),
    "premarket_continuation_0p75_time": (
        "Premarket continuation · 0.75 fraction · time exit"
    ),
    "gap_fade_plus_premarket_0p50": (
        "Gap fade + premarket continuation 0.50"
    ),
    "gap_fade_plus_premarket_0p75": (
        "Gap fade + premarket continuation 0.75"
    ),
}


def _display_identifier(value: Any) -> str:
    text = str(value)
    return DISPLAY_NAMES.get(text, text)


def _save_figure(figure: Any, path: Path) -> None:
    figure.patch.set_facecolor("white")
    for axis in figure.axes:
        axis.set_facecolor("white")
        axis.tick_params(colors="#172033")
        axis.xaxis.label.set_color("#172033")
        axis.yaxis.label.set_color("#172033")
        axis.title.set_color("#172033")
    save_report_figure(figure, path, dpi=155, bbox_inches="tight")
    plt.close(figure)


def _drawdown(equity: np.ndarray) -> np.ndarray:
    values = np.asarray(equity, dtype=float)
    return values - np.maximum.accumulate(values)


def _chart_assets(
    *,
    output_dir: Path,
    arrays: Exp012Arrays,
    session_pnl: pd.DataFrame,
    pair_session_pnl: pd.DataFrame,
    behaviour: pd.DataFrame,
    periods: pd.DataFrame,
    monthly: pd.DataFrame,
    rolling: pd.DataFrame,
    concentration: pd.DataFrame,
    overlap: pd.DataFrame,
    ledgers: Mapping[str, pd.DataFrame],
) -> None:
    dates = pd.to_datetime(session_pnl["session_date"])
    benchmark = (
        100_000.0
        * arrays.cash.close[:, -1]
        / arrays.cash.close[0, -1]
    )

    fig, axis = plt.subplots(figsize=(14, 6.5))
    axis.plot(dates, benchmark, color="#667085", lw=2, label="NQ benchmark")
    for candidate_id in FINALIST_IDS:
        equity = 100_000.0 + session_pnl[candidate_id].cumsum()
        axis.plot(dates, equity, lw=1.7, label=DISPLAY_NAMES[candidate_id])
    axis.axhline(100_000, color="#64748b", ls="--", lw=1)
    axis.set_title("Standalone strategy equity versus NQ price benchmark")
    axis.set_ylabel("Normalized value ($)")
    axis.grid(alpha=0.2)
    axis.legend(fontsize=8, ncol=2)
    _save_figure(fig, output_dir / "standalone_equity_vs_benchmark.png")

    fig, axis = plt.subplots(figsize=(14, 5.4))
    for candidate_id in FINALIST_IDS:
        equity = 100_000.0 + session_pnl[candidate_id].cumsum().to_numpy()
        axis.plot(
            dates,
            _drawdown(equity),
            lw=1.6,
            label=DISPLAY_NAMES[candidate_id],
        )
    axis.axhline(0, color="#64748b", lw=1)
    axis.set_title("Standalone drawdown through time")
    axis.set_ylabel("Drawdown ($)")
    axis.grid(alpha=0.2)
    axis.legend(fontsize=8)
    _save_figure(fig, output_dir / "standalone_drawdown.png")

    fig, axis = plt.subplots(figsize=(14, 6.2))
    axis.plot(dates, benchmark, color="#667085", lw=2, label="NQ benchmark")
    for pair in PAIR_DEFINITIONS:
        pair_id = str(pair["pair_id"])
        equity = 100_000.0 + pair_session_pnl[pair_id].cumsum()
        axis.plot(dates, equity, lw=1.8, label=DISPLAY_NAMES[pair_id])
    axis.axhline(100_000, color="#64748b", ls="--", lw=1)
    axis.set_title("Arithmetic research-sleeve equity paths")
    axis.set_ylabel("Normalized value ($)")
    axis.grid(alpha=0.2)
    axis.legend(fontsize=8)
    _save_figure(fig, output_dir / "sleeve_pair_equity.png")

    fig, axis = plt.subplots(figsize=(14, 5.2))
    for pair in PAIR_DEFINITIONS:
        pair_id = str(pair["pair_id"])
        equity = 100_000.0 + pair_session_pnl[pair_id].cumsum().to_numpy()
        axis.plot(dates, _drawdown(equity), lw=1.7, label=DISPLAY_NAMES[pair_id])
    axis.axhline(0, color="#64748b", lw=1)
    axis.set_title("Arithmetic research-sleeve drawdown")
    axis.set_ylabel("Drawdown ($)")
    axis.grid(alpha=0.2)
    axis.legend(fontsize=8)
    _save_figure(fig, output_dir / "sleeve_pair_drawdown.png")

    correlation = session_pnl[list(FINALIST_IDS)].corr().fillna(0.0)
    fig, axis = plt.subplots(figsize=(8, 6.5))
    image = axis.imshow(correlation.to_numpy(), vmin=-1, vmax=1, cmap="RdBu_r")
    labels = [DISPLAY_NAMES[value] for value in FINALIST_IDS]
    axis.set_xticks(range(3), labels=labels, rotation=25, ha="right")
    axis.set_yticks(range(3), labels=labels)
    for row in range(3):
        for column in range(3):
            axis.text(
                column,
                row,
                f"{correlation.iloc[row, column]:.3f}",
                ha="center",
                va="center",
                color="#172033",
            )
    axis.set_title("Session P&L correlation (zero on no-trade sessions)")
    fig.colorbar(image, ax=axis, label="Pearson correlation")
    _save_figure(fig, output_dir / "pnl_correlation.png")

    active_counts = {
        candidate_id: int(
            ledgers[candidate_id]["session_date"].astype(str).nunique()
        )
        for candidate_id in FINALIST_IDS
    }
    overlap_matrix = np.zeros((3, 3), dtype=int)
    for index, candidate_id in enumerate(FINALIST_IDS):
        overlap_matrix[index, index] = active_counts[candidate_id]
    for row in overlap.itertuples():
        left = FINALIST_IDS.index(str(row.left_candidate_id))
        right = FINALIST_IDS.index(str(row.right_candidate_id))
        overlap_matrix[left, right] = int(row.overlap_sessions)
        overlap_matrix[right, left] = int(row.overlap_sessions)
    fig, axis = plt.subplots(figsize=(8.5, 6.5))
    image = axis.imshow(overlap_matrix, cmap="Blues")
    axis.set_xticks(range(3), labels=labels, rotation=25, ha="right")
    axis.set_yticks(range(3), labels=labels)
    for row in range(3):
        for column in range(3):
            axis.text(
                column,
                row,
                f"{overlap_matrix[row, column]:,}",
                ha="center",
                va="center",
                color="#172033",
            )
    axis.set_title("Active-session and pairwise overlap matrix")
    fig.colorbar(image, ax=axis, label="Sessions")
    _save_figure(fig, output_dir / "overlap_matrix.png")

    overlap_labels = [
        f"{DISPLAY_NAMES[str(row.left_candidate_id)]}\nvs\n"
        f"{DISPLAY_NAMES[str(row.right_candidate_id)]}"
        for row in overlap.itertuples()
    ]
    x = np.arange(len(overlap))
    fig, axis = plt.subplots(figsize=(13, 5.5))
    axis.bar(
        x - 0.2,
        overlap["same_direction_overlap"],
        width=0.4,
        label="Same direction",
    )
    axis.bar(
        x + 0.2,
        overlap["opposite_direction_overlap"],
        width=0.4,
        label="Opposite direction",
    )
    axis.set_xticks(x, overlap_labels, fontsize=7)
    axis.set_ylabel("Overlapping sessions")
    axis.set_title("How often finalist signals overlap")
    axis.grid(axis="y", alpha=0.2)
    axis.legend()
    _save_figure(fig, output_dir / "overlap_detail.png")

    focus = periods.loc[periods["period"].isin(["2022-2024", "2025"])].copy()
    fig, axes = plt.subplots(3, 1, figsize=(14, 13))
    metrics = [
        ("net_profit_usd", "Net profit ($)"),
        ("profit_factor", "Profit Factor"),
        ("win_rate", "Win rate"),
    ]
    for axis, (metric, title) in zip(axes, metrics):
        pivot = focus.pivot(index="candidate_id", columns="period", values=metric)
        pivot = pivot.reindex(FINALIST_IDS)
        pivot.plot(kind="bar", ax=axis)
        axis.set_title(f"2025 versus 2022–2024: {title}")
        axis.set_xlabel("")
        axis.set_xticklabels(
            [DISPLAY_NAMES[value] for value in pivot.index],
            rotation=12,
            ha="right",
            fontsize=8,
        )
        axis.grid(axis="y", alpha=0.2)
    _save_figure(fig, output_dir / "period_comparison.png")

    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    for axis, dimension in zip(axes, ["trend_regime", "volatility_regime"]):
        local = behaviour.loc[
            behaviour["dimension"].eq(dimension)
            & ~behaviour["value"].eq("UNAVAILABLE")
        ]
        pivot = local.pivot(
            index="candidate_id", columns="value", values="net_profit_usd"
        ).reindex(FINALIST_IDS).fillna(0.0)
        max_abs = max(float(np.abs(pivot.to_numpy()).max()), 1.0)
        image = axis.imshow(
            pivot.to_numpy(),
            aspect="auto",
            cmap="RdBu_r",
            vmin=-max_abs,
            vmax=max_abs,
        )
        axis.set_xticks(range(len(pivot.columns)), labels=pivot.columns)
        axis.set_yticks(
            range(3),
            labels=[DISPLAY_NAMES[value] for value in FINALIST_IDS],
            fontsize=8,
        )
        axis.set_title(dimension.replace("_", " ").title())
        for row in range(pivot.shape[0]):
            for column in range(pivot.shape[1]):
                axis.text(
                    column,
                    row,
                    f"${pivot.iloc[row, column]:,.0f}",
                    ha="center",
                    va="center",
                    fontsize=8,
                )
        fig.colorbar(image, ax=axis, label="Net profit ($)")
    _save_figure(fig, output_dir / "regime_heatmaps.png")

    local = behaviour.loc[
        behaviour["dimension"].eq("context_strength")
        & ~behaviour["value"].eq("UNAVAILABLE")
    ]
    pivot = local.pivot(
        index="value", columns="candidate_id", values="net_profit_usd"
    ).reindex(columns=FINALIST_IDS).fillna(0.0)
    fig, axis = plt.subplots(figsize=(14, 6))
    pivot.plot(kind="bar", ax=axis)
    axis.axhline(0, color="#64748b", lw=1)
    axis.set_title("Net profit by locked context-strength band")
    axis.set_xlabel("Context fraction band")
    axis.set_ylabel("Net profit ($)")
    axis.grid(axis="y", alpha=0.2)
    axis.legend([DISPLAY_NAMES[value] for value in FINALIST_IDS], fontsize=8)
    _save_figure(fig, output_dir / "context_strength.png")

    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    for axis, dimension in zip(axes, ["direction", "exit_reason"]):
        local = behaviour.loc[behaviour["dimension"].eq(dimension)]
        pivot = local.pivot(
            index="candidate_id", columns="value", values="net_profit_usd"
        ).reindex(FINALIST_IDS).fillna(0.0)
        pivot.plot(kind="bar", ax=axis)
        axis.set_title(f"Net profit by {dimension.replace('_', ' ')}")
        axis.set_xlabel("")
        axis.set_xticklabels(
            [DISPLAY_NAMES[value] for value in pivot.index],
            rotation=12,
            ha="right",
            fontsize=8,
        )
        axis.grid(axis="y", alpha=0.2)
        axis.legend(fontsize=8)
    _save_figure(fig, output_dir / "direction_exit.png")

    local = behaviour.loc[behaviour["dimension"].eq("holding_time")]
    pivot = local.pivot(
        index="value", columns="candidate_id", values="net_profit_usd"
    ).reindex(columns=FINALIST_IDS).fillna(0.0)
    order = [
        "0-14 minutes",
        "15-59 minutes",
        "60-179 minutes",
        "180+ minutes",
    ]
    pivot = pivot.reindex(order).fillna(0.0)
    fig, axis = plt.subplots(figsize=(14, 6))
    pivot.plot(kind="bar", ax=axis)
    axis.axhline(0, color="#64748b", lw=1)
    axis.set_title("Net profit by holding-time band")
    axis.set_xlabel("Holding time")
    axis.set_ylabel("Net profit ($)")
    axis.grid(axis="y", alpha=0.2)
    axis.legend([DISPLAY_NAMES[value] for value in FINALIST_IDS], fontsize=8)
    _save_figure(fig, output_dir / "holding_time.png")

    fig, axes = plt.subplots(2, 1, figsize=(14, 9))
    for axis, dimension in zip(axes, ["entry_time", "exit_time"]):
        local = behaviour.loc[behaviour["dimension"].eq(dimension)]
        pivot = local.pivot(
            index="value",
            columns="candidate_id",
            values="completed_trades",
        ).reindex(columns=FINALIST_IDS).fillna(0.0)
        pivot.plot(kind="bar", ax=axis)
        axis.set_title(f"Trade count by {dimension.replace('_', ' ')}")
        axis.set_xlabel("")
        axis.set_ylabel("Trades")
        axis.grid(axis="y", alpha=0.2)
        axis.legend([DISPLAY_NAMES[value] for value in FINALIST_IDS], fontsize=8)
    _save_figure(fig, output_dir / "entry_exit_time.png")

    fig, axes = plt.subplots(3, 1, figsize=(14, 14))
    for axis, candidate_id in zip(axes, FINALIST_IDS):
        trades = ledgers[candidate_id]
        colors = np.where(trades["net_pnl_usd"] < 0, "#dc2626", "#5b8def")
        axis.scatter(
            trades["pre_exit_mae_usd"],
            trades["pre_exit_mfe_usd"],
            c=colors,
            s=18,
            alpha=0.65,
        )
        axis.axvline(0, color="#64748b", lw=1)
        axis.axhline(0, color="#64748b", lw=1)
        axis.set_title(DISPLAY_NAMES[candidate_id], fontsize=9)
        axis.set_xlabel("Pre-exit MAE ($)")
        axis.set_ylabel("Pre-exit MFE ($)")
        axis.grid(alpha=0.15)
    _save_figure(fig, output_dir / "mfe_mae.png")

    removal_columns = [
        "net_profit_usd",
        "net_after_removing_best_1_usd",
        "net_after_removing_best_5_usd",
        "net_after_removing_best_10_usd",
    ]
    fig, axis = plt.subplots(figsize=(14, 5.5))
    concentration.set_index("candidate_id")[removal_columns].reindex(
        FINALIST_IDS
    ).plot(kind="bar", ax=axis)
    axis.axhline(0, color="#64748b", lw=1)
    axis.set_xticklabels(
        [DISPLAY_NAMES[value] for value in FINALIST_IDS],
        rotation=12,
        ha="right",
    )
    axis.set_title("Profit concentration: removing the best trades")
    axis.set_ylabel("Remaining net profit ($)")
    axis.set_xlabel("")
    axis.grid(axis="y", alpha=0.2)
    axis.legend(fontsize=8)
    _save_figure(fig, output_dir / "profit_concentration.png")

    annual = behaviour.loc[behaviour["dimension"].eq("year")].copy()
    pivot = annual.pivot(
        index="value", columns="candidate_id", values="net_profit_usd"
    ).reindex(columns=FINALIST_IDS).fillna(0.0)
    fig, axis = plt.subplots(figsize=(14, 5.5))
    pivot.plot(kind="bar", ax=axis)
    axis.axhline(0, color="#64748b", lw=1)
    axis.set_title("Annual NQ net profit by finalist")
    axis.set_xlabel("Year")
    axis.set_ylabel("Net profit ($)")
    axis.grid(axis="y", alpha=0.2)
    axis.legend([DISPLAY_NAMES[value] for value in FINALIST_IDS], fontsize=8)
    _save_figure(fig, output_dir / "annual_comparison.png")

    fig, axes = plt.subplots(3, 1, figsize=(14, 15))
    for axis, candidate_id in zip(axes, FINALIST_IDS):
        local = monthly.loc[monthly["candidate_id"].eq(candidate_id)]
        pivot = local.pivot(
            index="year", columns="month_number", values="net_profit_usd"
        ).reindex(columns=range(1, 13)).fillna(0.0)
        max_abs = max(float(np.abs(pivot.to_numpy()).max()), 1.0)
        image = axis.imshow(
            pivot.to_numpy(),
            aspect="auto",
            cmap="RdBu_r",
            vmin=-max_abs,
            vmax=max_abs,
        )
        axis.set_xticks(
            range(12),
            labels=["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        )
        axis.set_yticks(range(len(pivot.index)), labels=pivot.index)
        axis.set_title(DISPLAY_NAMES[candidate_id])
        for row in range(pivot.shape[0]):
            for column in range(pivot.shape[1]):
                value = float(pivot.iloc[row, column])
                axis.text(
                    column,
                    row,
                    f"{value / 1000:.1f}k",
                    ha="center",
                    va="center",
                    fontsize=7,
                )
        fig.colorbar(image, ax=axis, label="Net profit ($)")
    _save_figure(fig, output_dir / "monthly_heatmaps.png")

    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    for candidate_id in FINALIST_IDS:
        local = rolling.loc[
            rolling["candidate_id"].eq(candidate_id)
            & rolling["window_trades"].eq(20)
        ]
        axes[0].plot(
            local["window_end_trade_number"],
            local["profit_factor"],
            label=DISPLAY_NAMES[candidate_id],
        )
        axes[1].plot(
            local["window_end_trade_number"],
            local["average_trade_usd"],
            label=DISPLAY_NAMES[candidate_id],
        )
    axes[0].axhline(1.0, color="#64748b", ls="--", lw=1)
    axes[0].set_title("Rolling 20-trade Profit Factor")
    axes[0].set_ylabel("Profit Factor")
    axes[1].axhline(0.0, color="#64748b", ls="--", lw=1)
    axes[1].set_title("Rolling 20-trade average trade")
    axes[1].set_xlabel("Candidate trade number")
    axes[1].set_ylabel("Average trade ($)")
    for axis in axes:
        axis.grid(alpha=0.2)
        axis.legend(fontsize=8)
    _save_figure(fig, output_dir / "rolling_trade_behaviour.png")


def _format_value(column: str, value: Any) -> str:
    if pd.isna(value):
        return "—"
    if column in {
        "candidate_id",
        "pair_id",
        "series_id",
        "left_candidate_id",
        "right_candidate_id",
        "first_candidate_id",
        "second_candidate_id",
    }:
        return html.escape(_display_identifier(value))
    if isinstance(value, (bool, np.bool_)):
        return "Yes" if bool(value) else "No"
    if "win_rate" in column or "share" in column:
        return f"{100 * float(value):.2f}%"
    if "correlation" in column:
        return f"{float(value):.4f}"
    if any(
        token in column
        for token in (
            "profit_usd",
            "drawdown_usd",
            "trade_usd",
            "mfe_usd",
            "mae_usd",
            "year_usd",
            "month_usd",
        )
    ):
        return f"${float(value):,.2f}"
    if "profit_factor" in column or "ratio" in column:
        return f"{float(value):,.4f}"
    if isinstance(value, (float, np.floating)):
        return f"{float(value):,.4f}"
    return html.escape(str(value))


def _table(frame: pd.DataFrame, columns: list[str]) -> str:
    labels = {
        "candidate_id": "Strategy",
        "pair_id": "Research sleeve pair",
        "series_id": "Strategy / pair",
        "series_type": "Type",
        "period": "Period",
        "completed_trades": "Trades",
        "component_trades": "Component trades",
        "active_sessions": "Active sessions",
        "trade_profit_factor": "Trade PF",
        "profit_factor": "Profit Factor",
        "session_profit_factor": "Session PF",
        "win_rate": "Win rate",
        "session_win_rate": "Session win rate",
        "net_profit_usd": "Net profit",
        "maximum_drawdown_usd": "Max drawdown",
        "net_profit_to_drawdown": "Net / drawdown",
        "average_trade_usd": "Average trade",
        "payoff_ratio": "Payoff ratio",
        "worst_year_usd": "Worst year",
        "worst_month_usd": "Worst month",
        "overlap_sessions": "Overlap sessions",
        "same_direction_overlap": "Same direction",
        "opposite_direction_overlap": "Opposite direction",
        "all_session_pnl_correlation": "All-session P&L correlation",
        "drawdown_correlation": "Drawdown correlation",
        "simultaneous_underwater_share": "Both underwater",
        "profitable_years": "Profitable years",
        "decline_duration_sessions": "Peak-to-trough sessions",
        "recovery_duration_sessions": "Trough-to-recovery sessions",
        "maximum_drawdown_recovered": "Recovered",
        "longest_underwater_sessions": "Longest underwater",
        "ending_underwater": "Ends underwater",
    }
    header = "".join(
        f"<th>{html.escape(labels.get(column, column))}</th>"
        for column in columns
    )
    rows: list[str] = []
    for record in frame[columns].to_dict(orient="records"):
        cells: list[str] = []
        for column in columns:
            value = record[column]
            negative = (
                isinstance(value, (int, float, np.integer, np.floating))
                and not isinstance(value, (bool, np.bool_))
                and not pd.isna(value)
                and float(value) < 0
            )
            css = ' class="negative"' if negative else ""
            cells.append(f"<td{css}>{_format_value(column, value)}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return (
        '<div class="table-wrap"><table><thead><tr>'
        + header
        + "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></div>"
    )


def _exp013_context_table(decision: Mapping[str, Any]) -> pd.DataFrame:
    context = decision["exp013_context"]
    return pd.DataFrame(
        [
            {
                "classification": context["classification"],
                "walk_forward_profitable_folds": (
                    context["walk_forward_profitable_folds"]
                ),
                "walk_forward_total_folds": context["walk_forward_total_folds"],
                "walk_forward_net_profit_usd": (
                    context["walk_forward_net_profit_usd"]
                ),
                "discovery_wide_mcpt_p_value": (
                    context["discovery_wide_mcpt_p_value"]
                ),
                "mcpt_candidate_count": context["mcpt_candidate_count"],
                "bootstrap_resamples_per_finalist": (
                    context["bootstrap_resamples_per_finalist"]
                ),
            }
        ]
    )


def build_exp014_report(
    *,
    decision: Mapping[str, Any],
    candidate_table: pd.DataFrame,
    arrays: Exp012Arrays,
    ledgers: Mapping[str, pd.DataFrame],
    behaviour: pd.DataFrame,
    periods: pd.DataFrame,
    monthly: pd.DataFrame,
    rolling: pd.DataFrame,
    drawdown_diagnostics: pd.DataFrame,
    concentration: pd.DataFrame,
    overlap: pd.DataFrame,
    pair_measurements: pd.DataFrame,
    session_pnl: pd.DataFrame,
    pair_session_pnl: pd.DataFrame,
    output_dir: Path,
) -> Path:
    if set(ledgers) != set(FINALIST_IDS):
        raise ValueError("EXP-014 report requires all three finalists.")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    _chart_assets(
        output_dir=output_dir,
        arrays=arrays,
        session_pnl=session_pnl,
        pair_session_pnl=pair_session_pnl,
        behaviour=behaviour,
        periods=periods,
        monthly=monthly,
        rolling=rolling,
        concentration=concentration,
        overlap=overlap,
        ledgers=ledgers,
    )

    focus = periods.loc[periods["period"].isin(["2022-2024", "2025"])]
    standalone_columns = [
        "candidate_id",
        "completed_trades",
        "trade_profit_factor",
        "win_rate",
        "average_trade_usd",
        "net_profit_usd",
        "maximum_drawdown_usd",
        "net_profit_to_drawdown",
    ]
    pair_columns = [
        "pair_id",
        "component_trades",
        "active_sessions",
        "overlap_sessions",
        "opposite_direction_overlap",
        "net_profit_usd",
        "maximum_drawdown_usd",
        "net_profit_to_drawdown",
        "session_profit_factor",
        "session_win_rate",
        "profitable_years",
        "worst_year_usd",
    ]
    overlap_columns = [
        "left_candidate_id",
        "right_candidate_id",
        "overlap_sessions",
        "same_direction_overlap",
        "opposite_direction_overlap",
        "both_win_overlap",
        "both_lose_overlap",
        "offsetting_outcome_overlap",
        "all_session_pnl_correlation",
        "drawdown_correlation",
        "simultaneous_underwater_share",
    ]
    focus_columns = [
        "candidate_id",
        "period",
        "completed_trades",
        "net_profit_usd",
        "profit_factor",
        "win_rate",
        "average_trade_usd",
        "payoff_ratio",
        "maximum_drawdown_usd",
        "stop_exit_share",
        "target_exit_share",
        "time_exit_share",
        "average_holding_minutes",
    ]
    concentration_columns = [
        "candidate_id",
        "net_profit_usd",
        "net_after_removing_best_1_usd",
        "net_after_removing_best_5_usd",
        "net_after_removing_best_10_usd",
        "top_5_percent_profit_share",
        "maximum_losing_streak",
        "worst_20_trade_result_usd",
        "worst_50_trade_result_usd",
        "worst_100_trade_result_usd",
    ]
    drawdown_columns = [
        "series_id",
        "series_type",
        "maximum_drawdown_usd",
        "decline_duration_sessions",
        "recovery_duration_sessions",
        "maximum_drawdown_recovered",
        "longest_underwater_sessions",
        "underwater_session_share",
        "ending_underwater",
    ]
    context_table = _exp013_context_table(decision)
    context_columns = list(context_table.columns)

    volatility_boundary = float(
        decision["regime_context"]["volatility_boundary"]
    )
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>EXP-014 Finalist Behaviour and Complementarity</title>
<style>
:root{{--bg:#07111f;--panel:#101d31;--line:#29415f;--text:#edf3fb;
--muted:#a9b6c8;--blue:#68a5ff;--red:#ff6b75;--green:#4fca8a}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);
font:15px/1.58 Inter,Segoe UI,Arial,sans-serif}}main{{max-width:1480px;
margin:auto;padding:28px}}section{{background:var(--panel);border:1px solid var(--line);
border-radius:16px;padding:22px;margin:18px 0}}h1{{font-size:30px;margin:0 0 8px}}
h2{{color:var(--blue);margin-top:0}}h3{{margin:22px 0 8px}}.muted{{color:var(--muted)}}
.status{{color:var(--green)}}.negative{{color:var(--red)}}.callout{{border-left:4px solid
var(--blue);padding:12px 16px;background:#0b1729;border-radius:8px}}
.strategy{{padding:14px 16px;background:#0b1729;border:1px solid #223753;
border-radius:10px;margin:12px 0}}img{{display:block;width:100%;height:auto;
background:#fff;border-radius:10px;margin:18px 0}}.table-wrap{{overflow:auto}}
table{{border-collapse:collapse;width:100%;background:#0b1729}}th,td{{padding:9px 11px;
border-bottom:1px solid #223753;text-align:right;white-space:nowrap}}
th:first-child,td:first-child{{text-align:left}}th{{color:#9cc2ff}}
code{{color:#d7e8ff}}
</style></head><body><main>
<header><div class="status">MEASURED BEHAVIOUR REVIEW</div>
<h1>EXP-014 · Finalist behaviour and complementarity</h1>
<p class="muted">Three unchanged strategies. Two fixed arithmetic research-sleeve pairs. No optimization, winner or trading authorization.</p></header>

<section><h2>What we tested</h2>
<p>EXP-014 reconstructs the exact three EXP-013 strategies and checks their
core results before examining individual trades. It does not change an entry,
stop, target, time exit, cost or position size. The purpose is explanation:
why the strategies differ, what weakened in 2025, and whether gap fade and
premarket continuation tend to experience profits and drawdowns at different times.</p>
<div class="callout"><strong>Evidence boundary:</strong> this report reuses
EXP-013's frozen walk-forward, bootstrap and 24-candidate MCPT evidence. It
does not rerun those tests or turn a descriptive regime into a new trading rule.</div>
<h3>Frozen EXP-013 evidence retained</h3>
{_table(context_table, context_columns)}</section>

<section><h2>How the strategies work</h2>
<div class="strategy"><h3>Gap fade · 0.50 fraction · 1R</h3>
<p>If the previous cash-session range was 200 points, a 0.50 gap fraction means
today's opening gap is at least 100 points. When the completed first five-minute
bar moves back against that gap, the strategy enters toward the previous close.
It uses the first-bar outer extreme as its stop and a target equal to the initial
risk.</p></div>
<div class="strategy"><h3>Premarket continuation · 0.50 fraction · time exit</h3>
<p>If the final 90-minute premarket range is 100 points, 0.50 requires at least
50 points of directional open-to-close movement. After the completed first cash
bar confirms that direction, the strategy enters at 09:35, uses the opposite
first-bar extreme as its stop and otherwise exits at 15:55.</p></div>
<div class="strategy"><h3>Premarket continuation · 0.75 fraction · time exit</h3>
<p>The rules are identical to the 0.50 version except that the premarket
open-to-close movement must cover at least 75 points of a 100-point range.
It is therefore more selective. The fraction describes a share of the
premarket range—not a percentage change in NQ.</p></div></section>

<section><h2>What happened overall</h2>
<p>{html.escape(str(decision['plain_english_summary']))}</p>
{_table(candidate_table, standalone_columns)}
<img src="standalone_equity_vs_benchmark.png" alt="Standalone equity versus benchmark">
<img src="standalone_drawdown.png" alt="Standalone drawdown"></section>

<section><h2>What changed in 2025?</h2>
<p>The table separates the recent 2025 results from the 2022–2024 walk-forward
years. It shows whether deterioration came from fewer trades, lower win rate,
smaller winners, larger losers or a different exit mix.</p>
{_table(focus, focus_columns)}
<img src="period_comparison.png" alt="2025 period comparison">
<img src="annual_comparison.png" alt="Annual strategy comparison">
<img src="monthly_heatmaps.png" alt="Monthly strategy heatmaps">
<img src="rolling_trade_behaviour.png" alt="Rolling trade behaviour"></section>

<section><h2>Entry-known market context</h2>
<p>Trend and volatility labels use only the prior 20 completed sessions. The
volatility boundary was calibrated from 2020–2021 and then frozen at
<code>{volatility_boundary:.8f}</code>. These rows describe behaviour; they
are not permission to filter future trades.</p>
<img src="regime_heatmaps.png" alt="Entry-known regime heatmaps">
<img src="context_strength.png" alt="Context strength breakdown"></section>

<section><h2>Direction, exits and holding behaviour</h2>
<img src="direction_exit.png" alt="Direction and exit breakdown">
<img src="holding_time.png" alt="Holding time breakdown">
<img src="entry_exit_time.png" alt="Entry and exit time distributions"></section>

<section><h2>Do the strategies overlap?</h2>
<p>P&L correlation uses every one of the 1,331 sessions and inserts zero when a
strategy did not trade. Opposite-direction overlaps are especially important:
the arithmetic sleeve view may not be directly executable in one netting account.</p>
{_table(overlap, overlap_columns)}
<img src="pnl_correlation.png" alt="Session P&amp;L correlation">
<img src="overlap_matrix.png" alt="Overlap matrix">
<img src="overlap_detail.png" alt="Signal overlap detail"></section>

<section><h2>Two fixed arithmetic research-sleeve pairs</h2>
<p>Each active component contributes one contract. No weights or pair membership
were optimized. The nested 0.50 and 0.75 premarket strategies are never combined.
These are complementarity measurements, not executable portfolio instructions.</p>
{_table(pair_measurements, pair_columns)}
<img src="sleeve_pair_equity.png" alt="Research-sleeve equity">
<img src="sleeve_pair_drawdown.png" alt="Research-sleeve drawdown">
<h3>Drawdown duration and recovery</h3>
{_table(drawdown_diagnostics, drawdown_columns)}</section>

<section><h2>Tail behaviour and profit concentration</h2>
<p>MFE and MAE use only completed one-minute bars before the exit minute plus the
actual exit price, avoiding price extremes that may have occurred after exit.</p>
{_table(concentration, concentration_columns)}
<img src="mfe_mae.png" alt="MFE and MAE">
<img src="profit_concentration.png" alt="Profit concentration"></section>

<section><h2>How to use this evidence</h2>
<p>EXP-014 has no pass/fail threshold and does not select a winner. It provides
the behavioural map needed to decide whether later research should refine gap
fade, refine premarket continuation, investigate a clearly defined combination,
or move to a different strategy family. It is historical explanatory research,
not independent confirmation. No paper or live trading is authorized.</p></section>
</main></body></html>"""
    path = output_dir / "report.html"
    path.write_text(page, encoding="utf-8")
    return path
