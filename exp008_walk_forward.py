from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from exp008_candidate_scoring import (
    CandidateSelection,
    evaluate_nq_grid,
    select_candidate,
)
from exp008_orb import (
    Exp008Arrays,
    run_candidate_summary,
)
from exp008_preregistration import (
    get_exp008_preregistration,
)


@dataclass(frozen=True)
class Exp008WalkForwardResult:
    folds: pd.DataFrame
    profitable_test_folds: int
    combined_test_net_profit_usd: float


def _session_timestamp(
    session_dates: np.ndarray,
) -> pd.DatetimeIndex:
    return pd.to_datetime(
        np.asarray(
            session_dates,
            dtype=object,
        )
    )


def _fold_mask(
    arrays: Exp008Arrays,
    *,
    start: str,
    end: str,
) -> np.ndarray:
    dates = _session_timestamp(
        arrays.session_dates
    )
    return np.asarray(
        (
            (dates >= pd.Timestamp(start))
            & (dates <= pd.Timestamp(end))
        ),
        dtype=bool,
    )


def run_exp008_anchored_walk_forward(
    nq_arrays: Exp008Arrays,
) -> Exp008WalkForwardResult:
    prereg = get_exp008_preregistration()
    folds = prereg[
        "anchored_walk_forward"
    ]["folds"]

    if len(folds) != 5:
        raise ValueError(
            "EXP-008 requires exactly five anchored folds."
        )

    rows: list[dict[str, Any]] = []

    for fold in folds:
        train_end = pd.Timestamp(
            fold["train_end"]
        )
        test_start = pd.Timestamp(
            fold["test_start"]
        )
        if not train_end < test_start:
            raise ValueError(
                "EXP-008 training must end before "
                "its test block starts."
            )

        train_mask = _fold_mask(
            nq_arrays,
            start=fold["train_start"],
            end=fold["train_end"],
        )
        test_mask = _fold_mask(
            nq_arrays,
            start=fold["test_start"],
            end=fold["test_end"],
        )

        if not train_mask.any():
            raise ValueError(
                f"EXP-008 fold {fold['fold']} "
                "has no training sessions."
            )
        if not test_mask.any():
            raise ValueError(
                f"EXP-008 fold {fold['fold']} "
                "has no test sessions."
            )

        train_arrays = nq_arrays.subset(
            train_mask
        )
        test_arrays = nq_arrays.subset(
            test_mask
        )

        training_grid = evaluate_nq_grid(
            train_arrays
        )
        selection = select_candidate(
            training_grid
        )

        if (
            selection.selected_parameters
            is None
        ):
            rows.append(
                {
                    "fold": int(fold["fold"]),
                    "train_start": fold[
                        "train_start"
                    ],
                    "train_end": fold[
                        "train_end"
                    ],
                    "test_start": fold[
                        "test_start"
                    ],
                    "test_end": fold[
                        "test_end"
                    ],
                    "training_sessions": int(
                        train_arrays.session_count
                    ),
                    "test_sessions": int(
                        test_arrays.session_count
                    ),
                    "selected_parameter_key": "",
                    "selected_opening_range_minutes": None,
                    "selected_reward_to_risk": None,
                    "selected_forced_flat_time_new_york": None,
                    "training_eligible_candidates": (
                        selection.eligible_count
                    ),
                    "training_stable_eligible_candidates": (
                        selection.stable_eligible_count
                    ),
                    "training_selected_trade_profit_factor": 0.0,
                    "training_selected_net_profit_usd": 0.0,
                    "test_completed_trades": 0,
                    "test_trade_profit_factor": 0.0,
                    "test_net_profit_usd": 0.0,
                    "test_average_trade_usd": 0.0,
                    "test_profitable": False,
                }
            )
            continue

        parameters = (
            selection.selected_parameters
        )
        training_rows = (
            selection.scored_grid.loc[
                selection.scored_grid[
                    "selected"
                ]
            ]
        )
        if len(training_rows) != 1:
            raise RuntimeError(
                "EXP-008 fold selection row is "
                "not unique."
            )
        training_row = training_rows.iloc[0]

        test_summary = run_candidate_summary(
            test_arrays,
            parameters=parameters,
            symbol="NQ",
        )

        rows.append(
            {
                "fold": int(fold["fold"]),
                "train_start": fold[
                    "train_start"
                ],
                "train_end": fold["train_end"],
                "test_start": fold[
                    "test_start"
                ],
                "test_end": fold["test_end"],
                "training_sessions": int(
                    train_arrays.session_count
                ),
                "test_sessions": int(
                    test_arrays.session_count
                ),
                "selected_parameter_key": (
                    parameters.key
                ),
                "selected_opening_range_minutes": (
                    parameters.opening_range_minutes
                ),
                "selected_reward_to_risk": float(
                    parameters.reward_to_risk
                ),
                "selected_forced_flat_time_new_york": (
                    parameters.forced_flat_time_new_york
                ),
                "training_eligible_candidates": (
                    selection.eligible_count
                ),
                "training_stable_eligible_candidates": (
                    selection.stable_eligible_count
                ),
                "training_selected_trade_profit_factor": (
                    float(
                        training_row[
                            "nq_trade_profit_factor"
                        ]
                    )
                ),
                "training_selected_net_profit_usd": (
                    float(
                        training_row[
                            "nq_net_profit_usd"
                        ]
                    )
                ),
                "test_completed_trades": int(
                    test_summary[
                        "completed_trades"
                    ]
                ),
                "test_trade_profit_factor": (
                    float(
                        test_summary[
                            "trade_profit_factor"
                        ]
                    )
                ),
                "test_net_profit_usd": float(
                    test_summary[
                        "net_profit_usd"
                    ]
                ),
                "test_average_trade_usd": float(
                    test_summary[
                        "average_trade_usd"
                    ]
                ),
                "test_profitable": bool(
                    float(
                        test_summary[
                            "net_profit_usd"
                        ]
                    )
                    > 0.0
                ),
            }
        )

    frame = pd.DataFrame(rows)
    profitable = int(
        frame["test_profitable"].sum()
    )
    combined = float(
        frame["test_net_profit_usd"].sum()
    )

    return Exp008WalkForwardResult(
        folds=frame,
        profitable_test_folds=profitable,
        combined_test_net_profit_usd=(
            combined
        ),
    )
