from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from exp006_candidate_scoring import (
    CandidateSelection,
    evaluate_candidate_grid,
    select_candidate,
)
from exp006_orb import (
    OrbArrays,
    OrbParameters,
    run_candidate_summary,
)
from exp006_preregistration import (
    get_exp006_preregistration,
)


@dataclass(frozen=True)
class WalkForwardResult:
    folds: pd.DataFrame
    profitable_nq_test_folds: int
    total_nq_net_profit_usd: float
    total_mnq_net_profit_usd: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "profitable_nq_test_folds": (
                self.profitable_nq_test_folds
            ),
            "total_nq_net_profit_usd": (
                self.total_nq_net_profit_usd
            ),
            "total_mnq_net_profit_usd": (
                self.total_mnq_net_profit_usd
            ),
            "fold_count": int(len(self.folds)),
        }


def _date_mask(
    arrays: OrbArrays,
    start: str,
    end: str,
) -> np.ndarray:
    dates = pd.to_datetime(
        arrays.session_dates
    )
    return (
        (dates >= pd.Timestamp(start))
        & (dates <= pd.Timestamp(end))
    )


def _training_selection(
    nq_train: OrbArrays,
    mnq_train: OrbArrays,
) -> tuple[CandidateSelection, pd.DataFrame]:
    grid = evaluate_candidate_grid(
        nq_train,
        mnq_train,
    )
    # The global 1,000-trade and five-profitable-year
    # requirements cannot apply inside early training folds.
    # Fold selection therefore uses the same locked ranking
    # components, excluding the future OOS component, with
    # only positive NQ/MNQ edge eligibility.
    selection = select_candidate(
        grid,
        include_walk_forward_component=False,
        global_eligibility=False,
    )
    if selection.selected_parameters is None:
        # If no positive-and-stable candidate exists in a
        # training fold, select the top ranked candidate from
        # the complete grid without looking at test data.
        fallback = selection.scored_grid.sort_values(
            by=[
                "median_component_rank",
                "nq_maximum_drawdown_percent",
                "nq_completed_trades",
                "distance_from_exp005_baseline",
                "opening_range_minutes",
                "final_entry_time_new_york",
                "direction_mode",
            ],
            ascending=[
                True,
                False,
                False,
                True,
                True,
                True,
                True,
            ],
            kind="mergesort",
        ).iloc[0]
        selected = OrbParameters(
            opening_range_minutes=int(
                fallback["opening_range_minutes"]
            ),
            final_entry_time_new_york=str(
                fallback[
                    "final_entry_time_new_york"
                ]
            ),
            direction_mode=str(
                fallback["direction_mode"]
            ),
        )
        selection = CandidateSelection(
            selected_parameters=selected,
            scored_grid=(
                selection.scored_grid.assign(
                    selected=lambda frame: frame[
                        "parameter_key"
                    ].eq(selected.key())
                )
            ),
            eligible_count=(
                selection.eligible_count
            ),
            stable_eligible_count=(
                selection.stable_eligible_count
            ),
        )
    return selection, grid


def run_anchored_walk_forward(
    nq_arrays: OrbArrays,
    mnq_arrays: OrbArrays,
) -> WalkForwardResult:
    if not np.array_equal(
        nq_arrays.session_dates,
        mnq_arrays.session_dates,
    ):
        raise ValueError(
            "EXP-006 walk-forward NQ/MNQ sessions must align."
        )

    folds = get_exp006_preregistration()[
        "walk_forward"
    ]["folds"]
    rows: list[dict[str, Any]] = []

    for fold_number, fold in enumerate(
        folds,
        start=1,
    ):
        train_mask = _date_mask(
            nq_arrays,
            fold["train_start"],
            fold["train_end"],
        )
        test_mask = _date_mask(
            nq_arrays,
            fold["test_start"],
            fold["test_end"],
        )
        if not train_mask.any() or not test_mask.any():
            raise ValueError(
                "EXP-006 walk-forward fold has no sessions: "
                f"{fold}."
            )

        nq_train = nq_arrays.subset(train_mask)
        mnq_train = mnq_arrays.subset(train_mask)
        nq_test = nq_arrays.subset(test_mask)
        mnq_test = mnq_arrays.subset(test_mask)

        selection, _ = _training_selection(
            nq_train,
            mnq_train,
        )
        parameters = selection.selected_parameters
        if parameters is None:
            raise RuntimeError(
                "EXP-006 training selection did not produce parameters."
            )

        nq_result = run_candidate_summary(
            nq_test,
            parameters=parameters,
            symbol="NQ",
        )
        mnq_result = run_candidate_summary(
            mnq_test,
            parameters=parameters,
            symbol="MNQ",
        )
        rows.append(
            {
                "fold": fold_number,
                **fold,
                **parameters.to_dict(),
                "training_sessions": int(
                    nq_train.session_count
                ),
                "test_sessions": int(
                    nq_test.session_count
                ),
                "training_eligible_candidates": int(
                    selection.eligible_count
                ),
                "training_stable_eligible_candidates": int(
                    selection.stable_eligible_count
                ),
                "nq_test_net_profit_usd": float(
                    nq_result["net_profit_usd"]
                ),
                "nq_test_trade_profit_factor": float(
                    nq_result[
                        "trade_profit_factor"
                    ]
                ),
                "nq_test_completed_trades": int(
                    nq_result["completed_trades"]
                ),
                "mnq_test_net_profit_usd": float(
                    mnq_result["net_profit_usd"]
                ),
                "mnq_test_trade_profit_factor": float(
                    mnq_result[
                        "trade_profit_factor"
                    ]
                ),
                "mnq_test_completed_trades": int(
                    mnq_result["completed_trades"]
                ),
                "nq_test_profitable": bool(
                    nq_result["net_profit_usd"] > 0.0
                ),
                "mnq_test_profitable": bool(
                    mnq_result["net_profit_usd"] > 0.0
                ),
            }
        )

    frame = pd.DataFrame(rows)
    return WalkForwardResult(
        folds=frame,
        profitable_nq_test_folds=int(
            frame["nq_test_profitable"].sum()
        ),
        total_nq_net_profit_usd=float(
            frame["nq_test_net_profit_usd"].sum()
        ),
        total_mnq_net_profit_usd=float(
            frame["mnq_test_net_profit_usd"].sum()
        ),
    )
