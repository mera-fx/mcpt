from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class TradeDiagnostics:
    summary: dict[str, Any]
    by_side: pd.DataFrame
    streaks: pd.DataFrame


def _profit_factor(pnl: pd.Series) -> float:
    gains = float(pnl[pnl > 0].sum())
    losses = float(abs(pnl[pnl < 0].sum()))

    if losses == 0:
        return float("inf") if gains > 0 else np.nan

    return gains / losses


def _maximum_streak(
    outcomes: pd.Series,
    target: str,
) -> int:
    longest = 0
    current = 0

    for outcome in outcomes:
        if outcome == target:
            current += 1
            longest = max(longest, current)
        else:
            current = 0

    return longest


def build_streak_table(
    trades: pd.DataFrame,
) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame(
            columns=[
                "streak_number",
                "outcome",
                "length",
                "start_trade_id",
                "end_trade_id",
                "start_time",
                "end_time",
                "total_pnl_cash",
            ]
        )

    working = trades.copy().reset_index(drop=True)

    working["outcome"] = np.select(
        [
            working["pnl_cash"] > 0,
            working["pnl_cash"] < 0,
        ],
        [
            "Win",
            "Loss",
        ],
        default="Breakeven",
    )

    group_id = (
        working["outcome"]
        != working["outcome"].shift(1)
    ).cumsum()

    rows: list[dict[str, Any]] = []

    for streak_number, (_, group) in enumerate(
        working.groupby(group_id),
        start=1,
    ):
        rows.append(
            {
                "streak_number": streak_number,
                "outcome": group["outcome"].iloc[0],
                "length": int(len(group)),
                "start_trade_id": int(
                    group["trade_id"].iloc[0]
                ),
                "end_trade_id": int(
                    group["trade_id"].iloc[-1]
                ),
                "start_time": group["entry_time"].iloc[0],
                "end_time": group["exit_time"].iloc[-1],
                "total_pnl_cash": float(
                    group["pnl_cash"].sum()
                ),
            }
        )

    return pd.DataFrame(rows)


def _summarize_group(
    trades: pd.DataFrame,
) -> dict[str, Any]:
    if trades.empty:
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "breakeven_trades": 0,
            "win_rate_percent": np.nan,
            "trade_profit_factor": np.nan,
            "average_trade_percent": np.nan,
            "median_trade_percent": np.nan,
            "average_winner_percent": np.nan,
            "average_loser_percent": np.nan,
            "payoff_ratio": np.nan,
            "largest_win_percent": np.nan,
            "largest_loss_percent": np.nan,
            "fifth_percentile_trade_percent": np.nan,
            "average_holding_hours": np.nan,
            "average_winner_holding_hours": np.nan,
            "average_loser_holding_hours": np.nan,
            "gross_profit_cash": 0.0,
            "gross_loss_cash": 0.0,
            "net_profit_cash": 0.0,
            "largest_win_cash": np.nan,
            "largest_loss_cash": np.nan,
            "top_1_loss_share_percent": np.nan,
            "top_5_loss_share_percent": np.nan,
            "max_consecutive_wins": 0,
            "max_consecutive_losses": 0,
        }

    working = trades.copy()

    winners = working[working["pnl_cash"] > 0]
    losers = working[working["pnl_cash"] < 0]
    breakeven = working[working["pnl_cash"] == 0]

    average_winner = (
        float(winners["net_return_percent"].mean())
        if not winners.empty
        else np.nan
    )

    average_loser = (
        float(losers["net_return_percent"].mean())
        if not losers.empty
        else np.nan
    )

    if (
        pd.notna(average_winner)
        and pd.notna(average_loser)
        and average_loser != 0
    ):
        payoff_ratio = (
            average_winner / abs(average_loser)
        )
    else:
        payoff_ratio = np.nan

    gross_loss_cash = float(
        abs(losers["pnl_cash"].sum())
    )

    ordered_loss_sizes = (
        losers["pnl_cash"]
        .abs()
        .sort_values(ascending=False)
    )

    if gross_loss_cash > 0:
        top_1_loss_share = float(
            ordered_loss_sizes.head(1).sum()
            / gross_loss_cash
            * 100
        )

        top_5_loss_share = float(
            ordered_loss_sizes.head(5).sum()
            / gross_loss_cash
            * 100
        )
    else:
        top_1_loss_share = np.nan
        top_5_loss_share = np.nan

    outcomes = pd.Series(
        np.select(
            [
                working["pnl_cash"] > 0,
                working["pnl_cash"] < 0,
            ],
            [
                "Win",
                "Loss",
            ],
            default="Breakeven",
        )
    )

    return {
        "total_trades": int(len(working)),
        "winning_trades": int(len(winners)),
        "losing_trades": int(len(losers)),
        "breakeven_trades": int(len(breakeven)),
        "win_rate_percent": float(
            len(winners) / len(working) * 100
        ),
        "trade_profit_factor": _profit_factor(
            working["pnl_cash"]
        ),
        "average_trade_percent": float(
            working["net_return_percent"].mean()
        ),
        "median_trade_percent": float(
            working["net_return_percent"].median()
        ),
        "average_winner_percent": average_winner,
        "average_loser_percent": average_loser,
        "payoff_ratio": payoff_ratio,
        "largest_win_percent": float(
            working["net_return_percent"].max()
        ),
        "largest_loss_percent": float(
            working["net_return_percent"].min()
        ),
        "fifth_percentile_trade_percent": float(
            working["net_return_percent"].quantile(0.05)
        ),
        "average_holding_hours": float(
            working["hours_held"].mean()
        ),
        "average_winner_holding_hours": (
            float(winners["hours_held"].mean())
            if not winners.empty
            else np.nan
        ),
        "average_loser_holding_hours": (
            float(losers["hours_held"].mean())
            if not losers.empty
            else np.nan
        ),
        "gross_profit_cash": float(
            winners["pnl_cash"].sum()
        ),
        "gross_loss_cash": gross_loss_cash,
        "net_profit_cash": float(
            working["pnl_cash"].sum()
        ),
        "largest_win_cash": float(
            working["pnl_cash"].max()
        ),
        "largest_loss_cash": float(
            working["pnl_cash"].min()
        ),
        "top_1_loss_share_percent": top_1_loss_share,
        "top_5_loss_share_percent": top_5_loss_share,
        "max_consecutive_wins": _maximum_streak(
            outcomes,
            "Win",
        ),
        "max_consecutive_losses": _maximum_streak(
            outcomes,
            "Loss",
        ),
    }


def calculate_trade_diagnostics(
    trades: pd.DataFrame,
) -> TradeDiagnostics:
    required_columns = {
        "trade_id",
        "side",
        "entry_time",
        "exit_time",
        "hours_held",
        "net_return_percent",
        "pnl_cash",
    }

    missing = required_columns.difference(
        trades.columns
    )

    if missing:
        raise ValueError(
            "Trade ledger is missing required columns: "
            f"{sorted(missing)}"
        )

    working = trades.copy()

    working["entry_time"] = pd.to_datetime(
        working["entry_time"]
    )

    working["exit_time"] = pd.to_datetime(
        working["exit_time"]
    )

    working = working.sort_values(
        ["exit_time", "trade_id"]
    ).reset_index(drop=True)

    summary = _summarize_group(working)

    side_rows: list[dict[str, Any]] = []

    for side, group in working.groupby("side"):
        side_rows.append(
            {
                "side": side,
                **_summarize_group(group),
            }
        )

    by_side = pd.DataFrame(side_rows)
    streaks = build_streak_table(working)

    return TradeDiagnostics(
        summary=summary,
        by_side=by_side,
        streaks=streaks,
    )
