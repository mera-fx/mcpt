from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from exp008_orb import (
    Exp008Arrays,
    Exp008Parameters,
    locked_exp008_parameters,
    run_candidate_summary,
)


OPENING_ORDER = (15, 30, 45)
TARGET_ORDER = (0.5, 1.0, 1.5)
FLAT_ORDER = ("12:00", "14:00", "15:55")
BASELINE = Exp008Parameters(
    opening_range_minutes=30,
    reward_to_risk=1.0,
    forced_flat_time_new_york="14:00",
)


@dataclass(frozen=True)
class CandidateSelection:
    selected_parameters: Exp008Parameters | None
    scored_grid: pd.DataFrame
    eligible_count: int
    stable_eligible_count: int

    @property
    def selected_key(self) -> str:
        if self.selected_parameters is None:
            return ""
        return self.selected_parameters.key


def parameter_neighbors(
    parameters: Exp008Parameters,
) -> tuple[Exp008Parameters, ...]:
    output: list[Exp008Parameters] = []
    axes: tuple[
        tuple[str, tuple[Any, ...]],
        ...,
    ] = (
        (
            "opening_range_minutes",
            OPENING_ORDER,
        ),
        (
            "reward_to_risk",
            TARGET_ORDER,
        ),
        (
            "forced_flat_time_new_york",
            FLAT_ORDER,
        ),
    )
    values: dict[str, Any] = {
        "opening_range_minutes": (
            parameters.opening_range_minutes
        ),
        "reward_to_risk": (
            parameters.reward_to_risk
        ),
        "forced_flat_time_new_york": (
            parameters.forced_flat_time_new_york
        ),
    }

    for field, ordered in axes:
        current = values[field]
        position = ordered.index(current)

        for neighbor_position in (
            position - 1,
            position + 1,
        ):
            if not 0 <= neighbor_position < len(
                ordered
            ):
                continue

            candidate = dict(values)
            candidate[field] = ordered[
                neighbor_position
            ]
            output.append(
                Exp008Parameters(
                    opening_range_minutes=int(
                        candidate[
                            "opening_range_minutes"
                        ]
                    ),
                    reward_to_risk=float(
                        candidate["reward_to_risk"]
                    ),
                    forced_flat_time_new_york=str(
                        candidate[
                            "forced_flat_time_new_york"
                        ]
                    ),
                )
            )

    return tuple(output)


def evaluate_nq_grid(
    nq_arrays: Exp008Arrays,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    for parameters in locked_exp008_parameters():
        summary = run_candidate_summary(
            nq_arrays,
            parameters=parameters,
            symbol="NQ",
        )
        rows.append(
            {
                **parameters.to_dict(),
                "nq_trade_profit_factor": (
                    summary[
                        "trade_profit_factor"
                    ]
                ),
                "nq_net_profit_usd": (
                    summary["net_profit_usd"]
                ),
                "nq_average_trade_usd": (
                    summary["average_trade_usd"]
                ),
                "nq_maximum_drawdown_usd": (
                    summary[
                        "maximum_drawdown_usd"
                    ]
                ),
                "nq_maximum_drawdown_percent": (
                    summary[
                        "maximum_drawdown_percent"
                    ]
                ),
                "nq_net_profit_to_drawdown": (
                    summary[
                        "net_profit_to_drawdown"
                    ]
                ),
                "nq_average_trade_to_cost": (
                    summary[
                        "average_trade_to_cost"
                    ]
                ),
                "nq_completed_trades": (
                    summary["completed_trades"]
                ),
                "nq_profitable_calendar_years": (
                    summary[
                        "profitable_calendar_years"
                    ]
                ),
                "nq_win_rate_percent": (
                    summary["win_rate_percent"]
                ),
            }
        )

    return pd.DataFrame(rows)


def add_mnq_grid_metrics(
    grid: pd.DataFrame,
    mnq_arrays: Exp008Arrays,
) -> pd.DataFrame:
    frame = grid.copy()
    rows: list[dict[str, Any]] = []

    for parameters in locked_exp008_parameters():
        summary = run_candidate_summary(
            mnq_arrays,
            parameters=parameters,
            symbol="MNQ",
        )
        rows.append(
            {
                "parameter_key": parameters.key,
                "mnq_trade_profit_factor": (
                    summary[
                        "trade_profit_factor"
                    ]
                ),
                "mnq_net_profit_usd": (
                    summary["net_profit_usd"]
                ),
                "mnq_average_trade_usd": (
                    summary["average_trade_usd"]
                ),
                "mnq_maximum_drawdown_usd": (
                    summary[
                        "maximum_drawdown_usd"
                    ]
                ),
                "mnq_completed_trades": (
                    summary["completed_trades"]
                ),
            }
        )

    mnq = pd.DataFrame(rows)
    return frame.merge(
        mnq,
        on="parameter_key",
        how="left",
        validate="one_to_one",
    )


def evaluate_candidate_grid(
    nq_arrays: Exp008Arrays,
    mnq_arrays: Exp008Arrays | None = None,
) -> pd.DataFrame:
    if (
        mnq_arrays is not None
        and not np.array_equal(
            nq_arrays.session_dates,
            mnq_arrays.session_dates,
        )
    ):
        raise ValueError(
            "EXP-008 NQ and MNQ sessions must align."
        )

    grid = evaluate_nq_grid(nq_arrays)
    if mnq_arrays is not None:
        grid = add_mnq_grid_metrics(
            grid,
            mnq_arrays,
        )
    return grid


def add_neighbor_stability(
    grid: pd.DataFrame,
) -> pd.DataFrame:
    frame = grid.copy()
    required = {
        "parameter_key",
        "opening_range_minutes",
        "reward_to_risk",
        "forced_flat_time_new_york",
        "nq_trade_profit_factor",
        "nq_net_profit_usd",
    }
    missing = required.difference(
        frame.columns
    )
    if missing:
        raise ValueError(
            "EXP-008 candidate table is missing: "
            f"{sorted(missing)}"
        )

    lookup = frame.set_index(
        "parameter_key"
    )
    profitable_counts: list[int] = []
    neighbor_counts: list[int] = []
    profitable_shares: list[float] = []
    median_profit_factors: list[float] = []
    neighbor_key_lists: list[str] = []

    for row in frame.itertuples(index=False):
        parameters = Exp008Parameters(
            opening_range_minutes=int(
                row.opening_range_minutes
            ),
            reward_to_risk=float(
                row.reward_to_risk
            ),
            forced_flat_time_new_york=str(
                row.forced_flat_time_new_york
            ),
        )
        neighbor_rows: list[pd.Series] = []
        neighbor_keys: list[str] = []

        for neighbor in parameter_neighbors(
            parameters
        ):
            if neighbor.key not in lookup.index:
                continue
            neighbor_rows.append(
                lookup.loc[neighbor.key]
            )
            neighbor_keys.append(neighbor.key)

        profitable = 0
        neighbor_pfs: list[float] = []

        for neighbor_row in neighbor_rows:
            pf = float(
                neighbor_row[
                    "nq_trade_profit_factor"
                ]
            )
            net = float(
                neighbor_row[
                    "nq_net_profit_usd"
                ]
            )
            neighbor_pfs.append(pf)
            profitable += int(
                pf > 1.0 and net > 0.0
            )

        count = len(neighbor_rows)
        share = (
            profitable / count
            if count
            else 0.0
        )
        finite_pfs = [
            value
            for value in neighbor_pfs
            if np.isfinite(value)
        ]
        median_pf = (
            float(np.median(finite_pfs))
            if finite_pfs
            else float("nan")
        )

        profitable_counts.append(
            profitable
        )
        neighbor_counts.append(count)
        profitable_shares.append(
            float(share)
        )
        median_profit_factors.append(
            median_pf
        )
        neighbor_key_lists.append(
            "|".join(neighbor_keys)
        )

    frame[
        "profitable_neighbor_count"
    ] = profitable_counts
    frame["neighbor_count"] = neighbor_counts
    frame[
        "profitable_neighbor_fraction"
    ] = profitable_shares
    frame[
        "neighbor_median_nq_trade_profit_factor"
    ] = median_profit_factors
    frame["neighbor_keys"] = (
        neighbor_key_lists
    )
    frame["neighbor_stable"] = (
        frame[
            "profitable_neighbor_fraction"
        ].ge(0.50)
        & frame[
            "neighbor_median_nq_trade_profit_factor"
        ].gt(1.0)
    )
    return frame


def add_eligibility(
    grid: pd.DataFrame,
) -> pd.DataFrame:
    frame = grid.copy()
    required = {
        "nq_trade_profit_factor",
        "nq_net_profit_usd",
        "nq_completed_trades",
    }
    missing = required.difference(
        frame.columns
    )
    if missing:
        raise ValueError(
            "EXP-008 candidate table is missing: "
            f"{sorted(missing)}"
        )

    frame["eligible"] = (
        frame[
            "nq_trade_profit_factor"
        ].astype(float).gt(1.0)
        & frame[
            "nq_net_profit_usd"
        ].astype(float).gt(0.0)
        & frame[
            "nq_completed_trades"
        ].astype(int).ge(100)
    )
    return frame


def select_candidate(
    grid: pd.DataFrame,
) -> CandidateSelection:
    scored = add_neighbor_stability(
        add_eligibility(grid)
    )

    candidates = scored.loc[
        scored["eligible"]
        & scored["neighbor_stable"]
    ].copy()

    candidates = candidates.sort_values(
        by=[
            "nq_trade_profit_factor",
            "nq_net_profit_to_drawdown",
            "nq_net_profit_usd",
            "nq_completed_trades",
            "parameter_key",
        ],
        ascending=[
            False,
            False,
            False,
            False,
            True,
        ],
        kind="mergesort",
    )

    selected: Exp008Parameters | None = None
    if not candidates.empty:
        row = candidates.iloc[0]
        selected = Exp008Parameters(
            opening_range_minutes=int(
                row["opening_range_minutes"]
            ),
            reward_to_risk=float(
                row["reward_to_risk"]
            ),
            forced_flat_time_new_york=str(
                row[
                    "forced_flat_time_new_york"
                ]
            ),
        )

    selected_key = (
        selected.key
        if selected is not None
        else ""
    )
    scored["selected"] = scored[
        "parameter_key"
    ].eq(selected_key)

    return CandidateSelection(
        selected_parameters=selected,
        scored_grid=scored,
        eligible_count=int(
            scored["eligible"].sum()
        ),
        stable_eligible_count=int(
            (
                scored["eligible"]
                & scored["neighbor_stable"]
            ).sum()
        ),
    )


def selected_row(
    selection: CandidateSelection,
) -> dict[str, Any] | None:
    if selection.selected_parameters is None:
        return None

    rows = selection.scored_grid.loc[
        selection.scored_grid[
            "parameter_key"
        ].eq(selection.selected_key)
    ]
    if len(rows) != 1:
        raise RuntimeError(
            "EXP-008 selected candidate row is not unique."
        )
    return rows.iloc[0].to_dict()
