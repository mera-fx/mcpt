from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any

import numpy as np
import pandas as pd

from exp009_engine import Exp009Arrays
from exp012_engine import Exp012Arrays, get_exp012_candidate, run_exp012_candidate
from exp013_preregistration import get_exp013_preregistration
from exp013_selection import (
    evaluate_exp013_finalists,
    select_exp013_measurement_leader,
    selected_exp013_row,
)


@dataclass(frozen=True)
class Exp013WalkForwardResult:
    folds: pd.DataFrame
    profitable_test_folds: int
    combined_test_net_profit_usd: float


def _subset_cash(arrays: Exp009Arrays, mask: np.ndarray) -> Exp009Arrays:
    return Exp009Arrays(
        **{
            field.name: getattr(arrays, field.name)[mask].copy()
            for field in fields(Exp009Arrays)
        }
    )


def subset_exp012_arrays(
    arrays: Exp012Arrays,
    mask: np.ndarray,
) -> Exp012Arrays:
    local = np.asarray(mask, dtype=bool)
    if local.ndim != 1 or len(local) != arrays.session_count:
        raise ValueError("EXP-013 subset mask does not match sessions.")
    return Exp012Arrays(
        cash=_subset_cash(arrays.cash, local),
        **{
            field.name: getattr(arrays, field.name)[local].copy()
            for field in fields(Exp012Arrays)
            if field.name != "cash"
        },
    )


def run_exp013_anchored_walk_forward(
    nq_arrays: Exp012Arrays,
) -> Exp013WalkForwardResult:
    folds = get_exp013_preregistration()["anchored_walk_forward"]["folds"]
    if len(folds) != 4:
        raise ValueError("EXP-013 requires four anchored folds.")

    dates = pd.to_datetime(nq_arrays.session_dates)
    rows: list[dict[str, Any]] = []
    for number, fold in enumerate(folds, start=1):
        test_year = int(fold["test_year"])
        train_mask = np.asarray(dates.year < test_year, dtype=bool)
        test_mask = np.asarray(dates.year == test_year, dtype=bool)
        if not train_mask.any() or not test_mask.any():
            raise ValueError(
                f"EXP-013 fold {number} lacks training or test sessions."
            )
        if dates[train_mask].max() >= dates[test_mask].min():
            raise ValueError(
                "EXP-013 training must end before test sessions."
            )

        train = subset_exp012_arrays(nq_arrays, train_mask)
        test = subset_exp012_arrays(nq_arrays, test_mask)
        selection = select_exp013_measurement_leader(
            evaluate_exp013_finalists(train)
        )
        selected = selected_exp013_row(selection)
        common = {
            "fold": number,
            "training_start": str(dates[train_mask].min().date()),
            "training_end": str(dates[train_mask].max().date()),
            "test_start": str(dates[test_mask].min().date()),
            "test_end": str(dates[test_mask].max().date()),
            "test_year": test_year,
            "training_sessions": int(train.session_count),
            "test_sessions": int(test.session_count),
            "training_eligible_candidates": selection.eligible_count,
        }
        if selection.selected_candidate_id is None or selected is None:
            rows.append(
                {
                    **common,
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

        result = run_exp012_candidate(
            test,
            get_exp012_candidate(selection.selected_candidate_id),
            symbol="NQ",
            slippage_ticks_per_side=1.0,
        )
        summary = result.summary
        rows.append(
            {
                **common,
                "selected_candidate_id": selection.selected_candidate_id,
                "training_selected_profit_factor": float(
                    selected["trade_profit_factor"]
                ),
                "training_selected_net_profit_usd": float(
                    selected["net_profit_usd"]
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
    return Exp013WalkForwardResult(
        folds=frame,
        profitable_test_folds=int(frame["test_profitable"].sum()),
        combined_test_net_profit_usd=float(
            frame["test_net_profit_usd"].sum()
        ),
    )
