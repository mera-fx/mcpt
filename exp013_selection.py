from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from exp012_engine import (
    Exp012Arrays,
    get_exp012_candidate,
    run_exp012_candidate,
)
from exp013_preregistration import FINALIST_CANDIDATES


FINALIST_IDS = tuple(
    str(record["candidate_id"]) for record in FINALIST_CANDIDATES
)


@dataclass(frozen=True)
class Exp013Selection:
    selected_candidate_id: str | None
    scored_candidates: pd.DataFrame
    eligible_count: int


def locked_exp013_candidates() -> tuple[Any, ...]:
    candidates = tuple(get_exp012_candidate(value) for value in FINALIST_IDS)
    if (
        len(candidates) != 3
        or len({candidate.candidate_id for candidate in candidates}) != 3
        or {candidate.family_id for candidate in candidates}
        != {"gap_fade", "premarket_momentum_continuation"}
    ):
        raise RuntimeError("EXP-013 finalist lock changed.")
    return candidates


def evaluate_exp013_finalists(
    arrays: Exp012Arrays,
    *,
    symbol: str = "NQ",
    slippage_ticks_per_side: float = 1.0,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for candidate in locked_exp013_candidates():
        result = run_exp012_candidate(
            arrays,
            candidate,
            symbol=symbol,
            slippage_ticks_per_side=slippage_ticks_per_side,
        )
        summary = result.summary
        rows.append(
            {
                "candidate_id": candidate.candidate_id,
                "family_id": candidate.family_id,
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
                "average_trade_usd": float(
                    summary["average_trade_usd"]
                ),
            }
        )
    return pd.DataFrame.from_records(rows)


def select_exp013_measurement_leader(
    table: pd.DataFrame,
) -> Exp013Selection:
    required = {
        "candidate_id",
        "completed_trades",
        "trade_profit_factor",
        "net_profit_usd",
        "net_profit_to_drawdown",
    }
    missing = sorted(required.difference(table.columns))
    if missing:
        raise ValueError(
            "EXP-013 finalist table is missing: " + ", ".join(missing)
        )
    if (
        len(table) != 3
        or table["candidate_id"].nunique() != 3
        or set(table["candidate_id"]) != set(FINALIST_IDS)
    ):
        raise ValueError("EXP-013 selection requires all three finalists.")

    scored = table.copy().reset_index(drop=True)
    scored["eligible"] = (
        scored["completed_trades"].astype(int).ge(20)
        & scored["trade_profit_factor"].astype(float).gt(1.0)
        & scored["net_profit_usd"].astype(float).gt(0.0)
        & np.isfinite(scored["trade_profit_factor"].astype(float))
    )
    scored["measurement_leader"] = False
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
    selected_id = None if eligible.empty else str(
        eligible.iloc[0]["candidate_id"]
    )
    if selected_id is not None:
        scored.loc[
            scored["candidate_id"].eq(selected_id),
            "measurement_leader",
        ] = True
    return Exp013Selection(
        selected_candidate_id=selected_id,
        scored_candidates=scored,
        eligible_count=int(scored["eligible"].sum()),
    )


def selected_exp013_row(
    selection: Exp013Selection,
) -> pd.Series | None:
    rows = selection.scored_candidates.loc[
        selection.scored_candidates["measurement_leader"]
    ]
    if selection.selected_candidate_id is None:
        if not rows.empty:
            raise RuntimeError("EXP-013 no-selection state is inconsistent.")
        return None
    if len(rows) != 1:
        raise RuntimeError("EXP-013 measurement leader is not unique.")
    return rows.iloc[0]
