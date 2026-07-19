from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from exp009_engine import (
    Exp009Arrays,
    Exp009Candidate,
    get_exp009_candidate,
    run_exp009_candidate,
)
from exp010_preregistration import OPENING_DRIVE_CANDIDATES


OPENING_DRIVE_IDS = tuple(
    str(record["candidate_id"]) for record in OPENING_DRIVE_CANDIDATES
)


@dataclass(frozen=True)
class Exp010Selection:
    selected_candidate: Exp009Candidate | None
    scored_candidates: pd.DataFrame
    eligible_count: int


def locked_opening_drive_candidates() -> tuple[Exp009Candidate, ...]:
    candidates = tuple(
        get_exp009_candidate(candidate_id)
        for candidate_id in OPENING_DRIVE_IDS
    )
    if (
        len(candidates) != 4
        or len({item.candidate_id for item in candidates}) != 4
        or {item.family_id for item in candidates}
        != {"opening_drive_continuation"}
    ):
        raise RuntimeError("EXP-010 opening-drive candidate lock changed.")
    return candidates


def evaluate_opening_drive_grid(
    arrays: Exp009Arrays,
    *,
    symbol: str = "NQ",
    slippage_ticks_per_side: float = 1.0,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for candidate in locked_opening_drive_candidates():
        result = run_exp009_candidate(
            arrays,
            candidate,
            symbol=symbol,
            slippage_ticks_per_side=slippage_ticks_per_side,
        )
        summary = result.summary
        rows.append(
            {
                "candidate_id": candidate.candidate_id,
                "minimum_drive_fraction": float(
                    candidate.parameters["minimum_drive_fraction"]
                ),
                "exit_mode": str(candidate.parameters["exit_mode"]),
                "completed_trades": int(summary["completed_trades"]),
                "trade_profit_factor": float(
                    summary["trade_profit_factor"]
                ),
                "win_rate": float(summary["win_rate"]),
                "net_profit_usd": float(summary["net_profit_usd"]),
                "maximum_drawdown_usd": float(
                    summary["maximum_drawdown_usd"]
                ),
                "net_profit_to_drawdown": float(
                    summary["net_profit_to_drawdown"]
                ),
                "average_trade_usd": float(summary["average_trade_usd"]),
            }
        )
    return pd.DataFrame.from_records(rows)


def select_opening_drive_candidate(
    grid: pd.DataFrame,
) -> Exp010Selection:
    required = {
        "candidate_id",
        "completed_trades",
        "trade_profit_factor",
        "net_profit_usd",
        "net_profit_to_drawdown",
    }
    missing = sorted(required.difference(grid.columns))
    if missing:
        raise ValueError(
            "EXP-010 selection grid is missing: " + ", ".join(missing)
        )
    if (
        len(grid) != 4
        or grid["candidate_id"].nunique() != 4
        or set(grid["candidate_id"]) != set(OPENING_DRIVE_IDS)
    ):
        raise ValueError("EXP-010 selection requires all four candidates.")

    scored = grid.copy().reset_index(drop=True)
    scored["eligible"] = (
        scored["completed_trades"].astype(int).ge(100)
        & scored["trade_profit_factor"].astype(float).gt(1.0)
        & scored["net_profit_usd"].astype(float).gt(0.0)
        & np.isfinite(scored["trade_profit_factor"].astype(float))
    )
    scored["selected"] = False
    eligible = scored.loc[scored["eligible"]].sort_values(
        [
            "trade_profit_factor",
            "net_profit_to_drawdown",
            "net_profit_usd",
            "completed_trades",
            "candidate_id",
        ],
        ascending=[False, False, False, False, True],
        kind="stable",
    )
    if eligible.empty:
        selected = None
    else:
        selected_id = str(eligible.iloc[0]["candidate_id"])
        scored.loc[
            scored["candidate_id"].eq(selected_id), "selected"
        ] = True
        selected = get_exp009_candidate(selected_id)

    return Exp010Selection(
        selected_candidate=selected,
        scored_candidates=scored,
        eligible_count=int(scored["eligible"].sum()),
    )


def selected_candidate_row(selection: Exp010Selection) -> pd.Series | None:
    rows = selection.scored_candidates.loc[
        selection.scored_candidates["selected"]
    ]
    if selection.selected_candidate is None:
        if not rows.empty:
            raise RuntimeError("EXP-010 no-selection state is inconsistent.")
        return None
    if len(rows) != 1:
        raise RuntimeError("EXP-010 selected candidate row is not unique.")
    return rows.iloc[0]
