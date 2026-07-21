from __future__ import annotations

from dataclasses import replace
from typing import Any

import numpy as np
import pandas as pd

from exp009_engine import (
    Exp009Arrays,
    Exp009Candidate,
    Exp009Result,
    maximum_drawdown,
    profit_factor,
)
from exp012_engine import Exp012Arrays
from exp014_preregistration import FINALIST_IDS


def synthetic_exp014_arrays(session_count: int = 120) -> Exp012Arrays:
    dates = pd.bdate_range("2020-01-03", periods=session_count)
    minute = np.arange(390, dtype=float)
    base = 10_000.0 + 2.0 * np.arange(session_count, dtype=float)
    open_1m = base[:, None] + 0.02 * minute[None, :]
    close_1m = open_1m + 0.10 * np.sin(minute[None, :] / 15.0)
    high_1m = np.maximum(open_1m, close_1m) + 1.0
    low_1m = np.minimum(open_1m, close_1m) - 1.0
    volume_1m = np.full((session_count, 390), 100.0)
    five_shape = (session_count, 78, 5)
    cash = Exp009Arrays(
        session_dates=dates.strftime("%Y-%m-%d").to_numpy(),
        years=dates.year.to_numpy(dtype=int),
        open=open_1m,
        high=high_1m,
        low=low_1m,
        close=close_1m,
        volume=volume_1m,
        open_5m=open_1m.reshape(five_shape)[:, :, 0],
        high_5m=high_1m.reshape(five_shape).max(axis=2),
        low_5m=low_1m.reshape(five_shape).min(axis=2),
        close_5m=close_1m.reshape(five_shape)[:, :, -1],
        volume_5m=volume_1m.reshape(five_shape).sum(axis=2),
        vwap_5m=close_1m.reshape(five_shape)[:, :, -1],
        vwap_std_5m=np.full((session_count, 78), 1.0),
    )
    alternating = np.where(np.arange(session_count) % 2 == 0, 1, -1)
    fraction = 0.50 + 0.50 * (
        np.arange(session_count, dtype=float) % 5
    ) / 4.0
    return Exp012Arrays(
        cash=cash,
        overnight_open=base - 20,
        overnight_high=base + 10,
        overnight_low=base - 30,
        overnight_close=base,
        overnight_drive_fraction=fraction,
        overnight_direction=alternating.astype(np.int8),
        premarket_open=base - 10,
        premarket_high=base + 5,
        premarket_low=base - 15,
        premarket_close=base,
        premarket_drive_fraction=fraction,
        premarket_direction=alternating.astype(np.int8),
        previous_cash_available=np.ones(session_count, dtype=bool),
        previous_cash_close=base - 5,
        previous_cash_range=np.full(session_count, 20.0),
        gap_fraction=fraction,
        gap_direction=alternating.astype(np.int8),
    )


def _result_summary(
    candidate_id: str,
    family_id: str,
    trades: pd.DataFrame,
) -> dict[str, Any]:
    pnl = trades["net_pnl_usd"].to_numpy(dtype=float)
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    drawdown = maximum_drawdown(pnl)
    return {
        "candidate_id": candidate_id,
        "family_id": family_id,
        "symbol": "NQ",
        "completed_trades": int(len(trades)),
        "long_trades": int(trades["direction"].eq("long").sum()),
        "short_trades": int(trades["direction"].eq("short").sum()),
        "gross_profit_usd": float(wins.sum()),
        "gross_loss_usd": float(losses.sum()),
        "net_profit_usd": float(pnl.sum()),
        "trade_profit_factor": float(profit_factor(pnl)),
        "win_rate": float(np.mean(pnl > 0)),
        "average_trade_usd": float(pnl.mean()),
        "median_trade_usd": float(np.median(pnl)),
        "average_winner_usd": float(wins.mean()),
        "average_loser_usd": float(losses.mean()),
        "payoff_ratio": float(wins.mean() / abs(losses.mean())),
        "maximum_drawdown_usd": float(drawdown),
        "maximum_drawdown_percent": float(abs(drawdown) / 100_000.0),
        "net_profit_to_drawdown": float(pnl.sum() / abs(drawdown)),
        "round_trip_cost_usd": 15.0,
        "average_trade_to_round_trip_cost": float(pnl.mean() / 15.0),
        "context_value_name": (
            "gap_fraction"
            if candidate_id == "gap_fade_0p50_1r"
            else "premarket_drive_fraction"
        ),
        "feature_eligible_sessions": len(trades),
        "feature_eligible_rate": len(trades) / 120,
        "signal_confirmed_sessions": len(trades),
        "signal_confirmation_rate": 1.0,
        "context_value_mean": 0.75,
        "context_value_median": 0.75,
        "context_long_trades": int(trades["direction"].eq("long").sum()),
        "context_short_trades": int(trades["direction"].eq("short").sum()),
    }


def synthetic_exp014_results(
    arrays: Exp012Arrays,
) -> dict[str, Exp009Result]:
    starts = {
        "gap_fade_0p50_1r": 0,
        "premarket_continuation_0p50_time": 20,
        "premarket_continuation_0p75_time": 40,
    }
    families = {
        "gap_fade_0p50_1r": "gap_fade",
        "premarket_continuation_0p50_time": (
            "premarket_momentum_continuation"
        ),
        "premarket_continuation_0p75_time": (
            "premarket_momentum_continuation"
        ),
    }
    output: dict[str, Exp009Result] = {}
    for candidate_index, candidate_id in enumerate(FINALIST_IDS):
        start = starts[candidate_id]
        rows: list[dict[str, Any]] = []
        for local_index, session in enumerate(range(start, start + 80)):
            direction = 1 if local_index % 2 == 0 else -1
            net = (
                180.0 + 20.0 * candidate_index
                if local_index % 3 != 0
                else -120.0
            )
            gross = net + 15.0
            entry_minute = 5
            exit_minute = (
                10
                if candidate_id == "gap_fade_0p50_1r"
                else 385
            )
            entry = float(arrays.cash.open[session, entry_minute])
            exit_price = entry + direction * gross / 20.0
            context = float(
                arrays.gap_fraction[session]
                if candidate_id == "gap_fade_0p50_1r"
                else arrays.premarket_drive_fraction[session]
            )
            rows.append(
                {
                    "candidate_id": candidate_id,
                    "family_id": families[candidate_id],
                    "symbol": "NQ",
                    "session_date": str(arrays.session_dates[session]),
                    "year": int(arrays.years[session]),
                    "direction": "long" if direction == 1 else "short",
                    "signal_five_minute_slot": 0,
                    "entry_minute_slot": entry_minute,
                    "exit_minute_slot": exit_minute,
                    "holding_minutes": exit_minute - entry_minute,
                    "entry_price": entry,
                    "stop_price": entry - direction * 10.0,
                    "target_price": (
                        entry + direction * 10.0
                        if candidate_id == "gap_fade_0p50_1r"
                        else np.nan
                    ),
                    "exit_price": exit_price,
                    "risk_points": 10.0,
                    "gross_pnl_usd": gross,
                    "transaction_cost_usd": 15.0,
                    "net_pnl_usd": net,
                    "exit_reason": (
                        "profit_target"
                        if candidate_id == "gap_fade_0p50_1r" and net > 0
                        else "protective_stop"
                        if candidate_id == "gap_fade_0p50_1r"
                        else "forced_flat_1555"
                    ),
                    "context_value_name": (
                        "gap_fraction"
                        if candidate_id == "gap_fade_0p50_1r"
                        else "premarket_drive_fraction"
                    ),
                    "context_value": context,
                }
            )
        trades = pd.DataFrame.from_records(rows)
        summary = _result_summary(
            candidate_id, families[candidate_id], trades
        )
        equity = trades["net_pnl_usd"].cumsum()
        equity_curve = pd.DataFrame(
            {
                "session_date": trades["session_date"],
                "net_pnl_usd": trades["net_pnl_usd"],
                "cumulative_net_profit_usd": equity,
                "equity_usd": 100_000.0 + equity,
                "drawdown_usd": equity - equity.cummax().clip(lower=0.0),
            }
        )
        yearly = (
            trades.groupby("year", as_index=False)
            .agg(
                completed_trades=("net_pnl_usd", "size"),
                net_profit_usd=("net_pnl_usd", "sum"),
            )
        )
        candidate = Exp009Candidate(
            candidate_id=candidate_id,
            family_id=families[candidate_id],
            parameters={},
        )
        output[candidate_id] = Exp009Result(
            candidate=candidate,
            symbol="NQ",
            summary=summary,
            trades=trades,
            equity_curve=equity_curve,
            yearly_results=yearly,
        )
    return output
