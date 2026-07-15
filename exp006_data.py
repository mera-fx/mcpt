from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from exp005_quantower_import import dataframe_sha256
from run_exp005_full_validation import (
    load_frozen_confirmation_data,
)
from run_exp005_quick_transfer import (
    load_frozen_data as load_frozen_quick_data,
)

EXPECTED_QUICK_SESSIONS = 906
EXPECTED_CONFIRMATION_SESSIONS = 733
EXPECTED_TOTAL_SESSIONS = 1639
EXPECTED_ONE_MINUTE_ROWS = (
    EXPECTED_TOTAL_SESSIONS * 390
)
EXPECTED_FIVE_MINUTE_ROWS = (
    EXPECTED_TOTAL_SESSIONS * 78
)


@dataclass(frozen=True)
class Exp006FrozenData:
    audit: dict[str, Any]
    nq_1m: pd.DataFrame
    mnq_1m: pd.DataFrame
    nq_5m: pd.DataFrame
    mnq_5m: pd.DataFrame



def _normalized(frame: pd.DataFrame) -> pd.DataFrame:
    local = frame.copy()
    local.index = pd.to_datetime(
        local.index,
        utc=True,
    )
    local["session_date"] = local[
        "session_date"
    ].astype(str)
    return local.sort_index()



def _combine(
    quick: pd.DataFrame,
    confirmation: pd.DataFrame,
) -> pd.DataFrame:
    quick_local = _normalized(quick)
    confirmation_local = _normalized(
        confirmation
    )
    overlap = set(
        quick_local["session_date"].unique()
    ).intersection(
        set(
            confirmation_local[
                "session_date"
            ].unique()
        )
    )
    if overlap:
        raise RuntimeError(
            "EXP-006 frozen quick and confirmation "
            "sessions overlap: "
            f"{sorted(overlap)[:3]}."
        )
    combined = pd.concat(
        [quick_local, confirmation_local],
        axis=0,
    ).sort_index()
    if combined.index.has_duplicates:
        raise RuntimeError(
            "EXP-006 combined timestamps are duplicated."
        )
    return combined



def load_exp006_frozen_data() -> Exp006FrozenData:
    (
        quick_audit,
        quick_nq_1m,
        quick_mnq_1m,
        quick_nq_5m,
        quick_mnq_5m,
    ) = load_frozen_quick_data()
    (
        confirmation_audit,
        confirmation_nq_1m,
        confirmation_mnq_1m,
        confirmation_nq_5m,
        confirmation_mnq_5m,
    ) = load_frozen_confirmation_data()

    if int(
        quick_audit["included_sessions"]
    ) != EXPECTED_QUICK_SESSIONS:
        raise RuntimeError(
            "EXP-005 quick-session count changed."
        )
    if int(
        confirmation_audit[
            "included_sessions"
        ]
    ) != EXPECTED_CONFIRMATION_SESSIONS:
        raise RuntimeError(
            "EXP-005 confirmation-session count changed."
        )

    nq_1m = _combine(
        quick_nq_1m,
        confirmation_nq_1m,
    )
    mnq_1m = _combine(
        quick_mnq_1m,
        confirmation_mnq_1m,
    )
    nq_5m = _combine(
        quick_nq_5m,
        confirmation_nq_5m,
    )
    mnq_5m = _combine(
        quick_mnq_5m,
        confirmation_mnq_5m,
    )

    if not nq_1m.index.equals(mnq_1m.index):
        raise RuntimeError(
            "EXP-006 NQ/MNQ one-minute timestamps differ."
        )
    if not nq_5m.index.equals(mnq_5m.index):
        raise RuntimeError(
            "EXP-006 NQ/MNQ five-minute timestamps differ."
        )

    for name, frame, expected_rows in (
        ("NQ_1m", nq_1m, EXPECTED_ONE_MINUTE_ROWS),
        ("MNQ_1m", mnq_1m, EXPECTED_ONE_MINUTE_ROWS),
        ("NQ_5m", nq_5m, EXPECTED_FIVE_MINUTE_ROWS),
        ("MNQ_5m", mnq_5m, EXPECTED_FIVE_MINUTE_ROWS),
    ):
        sessions = int(
            frame["session_date"].nunique()
        )
        if sessions != EXPECTED_TOTAL_SESSIONS:
            raise RuntimeError(
                f"EXP-006 {name} session count changed: "
                f"{sessions}."
            )
        if len(frame) != expected_rows:
            raise RuntimeError(
                f"EXP-006 {name} row count changed: "
                f"{len(frame)}."
            )

    audit = {
        "source_experiment": "EXP-005",
        "quick_sessions": EXPECTED_QUICK_SESSIONS,
        "confirmation_sessions": (
            EXPECTED_CONFIRMATION_SESSIONS
        ),
        "included_sessions": EXPECTED_TOTAL_SESSIONS,
        "one_minute_rows_per_symbol": (
            EXPECTED_ONE_MINUTE_ROWS
        ),
        "five_minute_rows_per_symbol": (
            EXPECTED_FIVE_MINUTE_ROWS
        ),
        "quick_audit": quick_audit,
        "confirmation_audit": confirmation_audit,
        "fingerprints": {
            "NQ_1m": dataframe_sha256(nq_1m),
            "MNQ_1m": dataframe_sha256(mnq_1m),
            "NQ_5m": dataframe_sha256(nq_5m),
            "MNQ_5m": dataframe_sha256(mnq_5m),
        },
        "exp005_control_changed": False,
        "new_data_cleaning_decisions": 0,
    }
    return Exp006FrozenData(
        audit=audit,
        nq_1m=nq_1m,
        mnq_1m=mnq_1m,
        nq_5m=nq_5m,
        mnq_5m=mnq_5m,
    )
