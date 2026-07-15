from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from exp006_orb import (
    OrbArrays,
    OrbParameters,
    locked_parameters,
    run_candidate_summary,
)

BASELINE = OrbParameters(
    opening_range_minutes=15,
    final_entry_time_new_york="12:00",
    direction_mode="both",
)
OPENING_ORDER = (5, 15, 30)
ENTRY_ORDER = ("10:30", "11:15", "12:00")
DIRECTION_ORDER = ("long", "short", "both")


@dataclass(frozen=True)
class CandidateSelection:
    selected_parameters: OrbParameters | None
    scored_grid: pd.DataFrame
    eligible_count: int
    stable_eligible_count: int


def parameter_distance_from_baseline(
    parameters: OrbParameters,
) -> int:
    return (
        abs(
            OPENING_ORDER.index(
                parameters.opening_range_minutes
            )
            - OPENING_ORDER.index(
                BASELINE.opening_range_minutes
            )
        )
        + abs(
            ENTRY_ORDER.index(
                parameters.final_entry_time_new_york
            )
            - ENTRY_ORDER.index(
                BASELINE.final_entry_time_new_york
            )
        )
        + abs(
            DIRECTION_ORDER.index(
                parameters.direction_mode
            )
            - DIRECTION_ORDER.index(
                BASELINE.direction_mode
            )
        )
    )


def parameter_neighbors(
    parameters: OrbParameters,
) -> tuple[OrbParameters, ...]:
    output: list[OrbParameters] = []
    axes = (
        (
            "opening_range_minutes",
            OPENING_ORDER,
        ),
        (
            "final_entry_time_new_york",
            ENTRY_ORDER,
        ),
        (
            "direction_mode",
            DIRECTION_ORDER,
        ),
    )
    values = parameters.to_dict()

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
            candidate = {
                "opening_range_minutes": (
                    parameters.opening_range_minutes
                ),
                "final_entry_time_new_york": (
                    parameters.final_entry_time_new_york
                ),
                "direction_mode": (
                    parameters.direction_mode
                ),
            }
            candidate[field] = ordered[
                neighbor_position
            ]
            output.append(
                OrbParameters(**candidate)
            )

    return tuple(output)


def evaluate_candidate_grid(
    nq_arrays: OrbArrays,
    mnq_arrays: OrbArrays,
) -> pd.DataFrame:
    if not np.array_equal(
        nq_arrays.session_dates,
        mnq_arrays.session_dates,
    ):
        raise ValueError(
            "EXP-006 NQ and MNQ sessions must align."
        )

    rows: list[dict[str, Any]] = []
    for parameters in locked_parameters():
        nq = run_candidate_summary(
            nq_arrays,
            parameters=parameters,
            symbol="NQ",
        )
        mnq = run_candidate_summary(
            mnq_arrays,
            parameters=parameters,
            symbol="MNQ",
        )
        oos_mask = nq_arrays.years >= 2021
        nq_oos = run_candidate_summary(
            nq_arrays.subset(oos_mask),
            parameters=parameters,
            symbol="NQ",
        )
        rows.append(
            {
                **parameters.to_dict(),
                "nq_trade_profit_factor": nq[
                    "trade_profit_factor"
                ],
                "nq_net_profit_usd": nq[
                    "net_profit_usd"
                ],
                "nq_maximum_drawdown_usd": nq[
                    "maximum_drawdown_usd"
                ],
                "nq_maximum_drawdown_percent": nq[
                    "maximum_drawdown_percent"
                ],
                "nq_net_profit_to_drawdown": nq[
                    "net_profit_to_drawdown"
                ],
                "nq_average_trade_to_cost": nq[
                    "average_trade_to_cost"
                ],
                "nq_completed_trades": nq[
                    "completed_trades"
                ],
                "nq_profitable_calendar_years": nq[
                    "profitable_calendar_years"
                ],
                "nq_win_rate_percent": nq[
                    "win_rate_percent"
                ],
                "mnq_trade_profit_factor": mnq[
                    "trade_profit_factor"
                ],
                "mnq_net_profit_usd": mnq[
                    "net_profit_usd"
                ],
                "mnq_maximum_drawdown_usd": mnq[
                    "maximum_drawdown_usd"
                ],
                "mnq_completed_trades": mnq[
                    "completed_trades"
                ],
                "fixed_candidate_2021_2025_nq_net_profit_usd": (
                    nq_oos["net_profit_usd"]
                ),
                "distance_from_exp005_baseline": (
                    parameter_distance_from_baseline(
                        parameters
                    )
                ),
            }
        )

    return pd.DataFrame(rows)


def _rank_descending(
    frame: pd.DataFrame,
    column: str,
) -> pd.Series:
    values = pd.to_numeric(
        frame[column],
        errors="coerce",
    ).replace(
        [np.inf, -np.inf],
        np.nan,
    )
    return values.rank(
        method="min",
        ascending=False,
        na_option="bottom",
    )


def add_eligibility_and_scores(
    grid: pd.DataFrame,
    *,
    include_walk_forward_component: bool = True,
    global_eligibility: bool = True,
) -> pd.DataFrame:
    frame = grid.copy()
    required = {
        "parameter_key",
        "nq_trade_profit_factor",
        "nq_net_profit_usd",
        "nq_completed_trades",
        "nq_profitable_calendar_years",
        "nq_net_profit_to_drawdown",
        "nq_average_trade_to_cost",
        "mnq_trade_profit_factor",
        "mnq_net_profit_usd",
        "nq_maximum_drawdown_percent",
        "distance_from_exp005_baseline",
    }
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(
            "EXP-006 candidate table is missing: "
            f"{sorted(missing)}"
        )

    if global_eligibility:
        eligible = (
            frame["nq_trade_profit_factor"]
            .astype(float)
            .gt(1.0)
            & frame["mnq_trade_profit_factor"]
            .astype(float)
            .gt(1.0)
            & frame["nq_net_profit_usd"]
            .astype(float)
            .gt(0.0)
            & frame["mnq_net_profit_usd"]
            .astype(float)
            .gt(0.0)
            & frame["nq_completed_trades"]
            .astype(int)
            .ge(1000)
            & frame["nq_profitable_calendar_years"]
            .astype(int)
            .ge(5)
        )
    else:
        eligible = (
            frame["nq_trade_profit_factor"]
            .astype(float)
            .gt(1.0)
            & frame["mnq_trade_profit_factor"]
            .astype(float)
            .gt(1.0)
            & frame["nq_net_profit_usd"]
            .astype(float)
            .gt(0.0)
            & frame["mnq_net_profit_usd"]
            .astype(float)
            .gt(0.0)
        )

    frame["eligible"] = eligible
    components = [
        "nq_trade_profit_factor",
        "nq_net_profit_to_drawdown",
        "nq_average_trade_to_cost",
        "mnq_trade_profit_factor",
        "nq_profitable_calendar_years",
    ]
    if include_walk_forward_component:
        components.append(
            "fixed_candidate_2021_2025_nq_net_profit_usd"
        )

    rank_columns: list[str] = []
    for component in components:
        if component not in frame:
            raise ValueError(
                "EXP-006 ranking component is missing: "
                f"{component}."
            )
        name = f"rank_{component}"
        frame[name] = _rank_descending(
            frame,
            component,
        )
        rank_columns.append(name)

    frame["median_component_rank"] = frame[
        rank_columns
    ].median(axis=1)
    return frame


def add_neighbor_stability(
    scored_grid: pd.DataFrame,
) -> pd.DataFrame:
    frame = scored_grid.copy()
    lookup = frame.set_index("parameter_key")
    shares: list[float] = []
    profitable_counts: list[int] = []
    total_counts: list[int] = []

    for row in frame.itertuples(index=False):
        parameters = OrbParameters(
            opening_range_minutes=int(
                row.opening_range_minutes
            ),
            final_entry_time_new_york=str(
                row.final_entry_time_new_york
            ),
            direction_mode=str(
                row.direction_mode
            ),
        )
        neighbors = parameter_neighbors(parameters)
        profitable = 0
        observed = 0
        for neighbor in neighbors:
            if neighbor.key() not in lookup.index:
                continue
            neighbor_row = lookup.loc[neighbor.key()]
            observed += 1
            profitable += int(
                float(
                    neighbor_row[
                        "nq_trade_profit_factor"
                    ]
                )
                > 1.0
                and float(
                    neighbor_row[
                        "mnq_trade_profit_factor"
                    ]
                )
                > 1.0
                and float(
                    neighbor_row[
                        "nq_net_profit_usd"
                    ]
                )
                > 0.0
                and float(
                    neighbor_row[
                        "mnq_net_profit_usd"
                    ]
                )
                > 0.0
            )
        share = (
            profitable / observed
            if observed
            else 0.0
        )
        shares.append(float(share))
        profitable_counts.append(profitable)
        total_counts.append(observed)

    frame["profitable_neighbor_count"] = (
        profitable_counts
    )
    frame["neighbor_count"] = total_counts
    frame["profitable_neighbor_share"] = shares
    frame["neighbor_stable"] = frame[
        "profitable_neighbor_share"
    ].ge(0.50)
    return frame


def select_candidate(
    grid: pd.DataFrame,
    *,
    include_walk_forward_component: bool = True,
    global_eligibility: bool = True,
) -> CandidateSelection:
    scored = add_eligibility_and_scores(
        grid,
        include_walk_forward_component=(
            include_walk_forward_component
        ),
        global_eligibility=global_eligibility,
    )
    scored = add_neighbor_stability(scored)
    candidates = scored.loc[
        scored["eligible"]
        & scored["neighbor_stable"]
    ].copy()
    candidates = candidates.sort_values(
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
    )

    selected: OrbParameters | None = None
    if not candidates.empty:
        row = candidates.iloc[0]
        selected = OrbParameters(
            opening_range_minutes=int(
                row["opening_range_minutes"]
            ),
            final_entry_time_new_york=str(
                row[
                    "final_entry_time_new_york"
                ]
            ),
            direction_mode=str(
                row["direction_mode"]
            ),
        )

    selected_key = (
        selected.key()
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
