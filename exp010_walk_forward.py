from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from exp009_engine import Exp009Arrays, run_exp009_candidate
from exp010_preregistration import get_exp010_preregistration
from exp010_selection import (
    evaluate_opening_drive_grid,
    select_opening_drive_candidate,
    selected_candidate_row,
)


@dataclass(frozen=True)
class Exp010WalkForwardResult:
    folds: pd.DataFrame
    profitable_test_folds: int
    combined_test_net_profit_usd: float


def subset_exp009_arrays(
    arrays: Exp009Arrays,
    mask: np.ndarray,
) -> Exp009Arrays:
    local = np.asarray(mask, dtype=bool)
    if local.ndim != 1 or len(local) != arrays.session_count:
        raise ValueError("EXP-010 subset mask does not match sessions.")
    return Exp009Arrays(
        session_dates=arrays.session_dates[local].copy(),
        years=arrays.years[local].copy(),
        open=arrays.open[local].copy(),
        high=arrays.high[local].copy(),
        low=arrays.low[local].copy(),
        close=arrays.close[local].copy(),
        volume=arrays.volume[local].copy(),
        open_5m=arrays.open_5m[local].copy(),
        high_5m=arrays.high_5m[local].copy(),
        low_5m=arrays.low_5m[local].copy(),
        close_5m=arrays.close_5m[local].copy(),
        volume_5m=arrays.volume_5m[local].copy(),
        vwap_5m=arrays.vwap_5m[local].copy(),
        vwap_std_5m=arrays.vwap_std_5m[local].copy(),
    )


def run_exp010_anchored_walk_forward(
    nq_arrays: Exp009Arrays,
) -> Exp010WalkForwardResult:
    folds = get_exp010_preregistration()["anchored_walk_forward"][
        "folds"
    ]
    if len(folds) != 5:
        raise ValueError("EXP-010 requires exactly five anchored folds.")

    rows: list[dict[str, Any]] = []
    dates = pd.to_datetime(nq_arrays.session_dates)
    for number, fold in enumerate(folds, start=1):
        test_year = int(fold["test_year"])
        train_mask = np.asarray(dates.year < test_year, dtype=bool)
        test_mask = np.asarray(dates.year == test_year, dtype=bool)
        if not train_mask.any() or not test_mask.any():
            raise ValueError(
                f"EXP-010 fold {number} lacks training or test sessions."
            )
        if dates[train_mask].max() >= dates[test_mask].min():
            raise ValueError(
                "EXP-010 training must end before test sessions."
            )

        train_arrays = subset_exp009_arrays(nq_arrays, train_mask)
        test_arrays = subset_exp009_arrays(nq_arrays, test_mask)
        grid = evaluate_opening_drive_grid(train_arrays)
        selection = select_opening_drive_candidate(grid)
        training_row = selected_candidate_row(selection)

        if selection.selected_candidate is None or training_row is None:
            rows.append(
                {
                    "fold": number,
                    "training_start": str(dates[train_mask].min().date()),
                    "training_end": str(dates[train_mask].max().date()),
                    "test_start": str(dates[test_mask].min().date()),
                    "test_end": str(dates[test_mask].max().date()),
                    "test_year": test_year,
                    "training_sessions": int(train_arrays.session_count),
                    "test_sessions": int(test_arrays.session_count),
                    "training_eligible_candidates": selection.eligible_count,
                    "selected_candidate_id": "",
                    "training_selected_profit_factor": 0.0,
                    "training_selected_net_profit_usd": 0.0,
                    "test_completed_trades": 0,
                    "test_trade_profit_factor": 0.0,
                    "test_net_profit_usd": 0.0,
                    "test_average_trade_usd": 0.0,
                    "test_profitable": False,
                }
            )
            continue

        result = run_exp009_candidate(
            test_arrays,
            selection.selected_candidate,
            symbol="NQ",
            slippage_ticks_per_side=1.0,
        )
        summary = result.summary
        rows.append(
            {
                "fold": number,
                "training_start": str(dates[train_mask].min().date()),
                "training_end": str(dates[train_mask].max().date()),
                "test_start": str(dates[test_mask].min().date()),
                "test_end": str(dates[test_mask].max().date()),
                "test_year": test_year,
                "training_sessions": int(train_arrays.session_count),
                "test_sessions": int(test_arrays.session_count),
                "training_eligible_candidates": selection.eligible_count,
                "selected_candidate_id": (
                    selection.selected_candidate.candidate_id
                ),
                "training_selected_profit_factor": float(
                    training_row["trade_profit_factor"]
                ),
                "training_selected_net_profit_usd": float(
                    training_row["net_profit_usd"]
                ),
                "test_completed_trades": int(summary["completed_trades"]),
                "test_trade_profit_factor": float(
                    summary["trade_profit_factor"]
                ),
                "test_net_profit_usd": float(summary["net_profit_usd"]),
                "test_average_trade_usd": float(
                    summary["average_trade_usd"]
                ),
                "test_profitable": bool(summary["net_profit_usd"] > 0),
            }
        )

    frame = pd.DataFrame.from_records(rows)
    return Exp010WalkForwardResult(
        folds=frame,
        profitable_test_folds=int(frame["test_profitable"].sum()),
        combined_test_net_profit_usd=float(
            frame["test_net_profit_usd"].sum()
        ),
    )
