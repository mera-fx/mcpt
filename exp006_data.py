from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from exp005_full_validation_result import (
    verify_local_full_validation_decision,
)
from exp005_quantower_import import (
    dataframe_sha256,
)
from import_exp005_quantower_confirmation_data import (
    AUDIT_FILE as CONFIRMATION_AUDIT_FILE,
    OUTPUT_FILES as CONFIRMATION_OUTPUT_FILES,
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

EXPECTED_CONFIRMATION_IMPORT_FIELDS = {
    "included_sessions": 733,
    "included_nq_one_minute_rows": 285_870,
    "included_mnq_one_minute_rows": 285_870,
    "included_nq_five_minute_rows": 57_174,
    "included_mnq_five_minute_rows": 57_174,
    "provider_unavailable_sessions_excluded": 2,
    "provider_complete_sessions_restored": 1,
    "potential_front_month_mismatch_sessions_excluded": 9,
    "included_invalid_sessions": 0,
    "included_front_month_mismatch_sessions": 0,
    "strategy_results_calculated": False,
    "full_validation_results_calculated": False,
    "quick_transfer_rerun": False,
}


@dataclass(frozen=True)
class Exp006FrozenData:
    audit: dict[str, Any]
    nq_1m: pd.DataFrame
    mnq_1m: pd.DataFrame
    nq_5m: pd.DataFrame
    mnq_5m: pd.DataFrame


def _normalized(
    frame: pd.DataFrame,
) -> pd.DataFrame:
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


def _read_confirmation_audit(
    path: Path = CONFIRMATION_AUDIT_FILE,
) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            "Frozen EXP-005 confirmation audit is "
            f"missing: {path}"
        )

    value = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(value, dict):
        raise RuntimeError(
            "Frozen EXP-005 confirmation audit "
            "must be a JSON object."
        )

    return value


def verify_confirmation_audit_for_exp006(
    *,
    audit: dict[str, Any],
    full_validation_result: dict[str, Any],
) -> None:
    for field, expected in (
        EXPECTED_CONFIRMATION_IMPORT_FIELDS.items()
    ):
        actual = audit.get(field)

        if actual != expected:
            raise RuntimeError(
                "Frozen confirmation audit field "
                f"{field} changed: expected "
                f"{expected!r}, got {actual!r}."
            )

    frozen_data = full_validation_result[
        "data"
    ]
    audit_git = audit.get("git", {})

    if (
        audit_git.get("commit")
        != frozen_data[
            "confirmation_import_commit"
        ]
    ):
        raise RuntimeError(
            "Frozen confirmation import commit "
            "does not match the tracked EXP-005 "
            "full-validation result."
        )

    expected_fingerprints = frozen_data[
        "fingerprints"
    ]

    if (
        audit.get("fingerprints")
        != expected_fingerprints
    ):
        raise RuntimeError(
            "Frozen confirmation audit "
            "fingerprints do not match the tracked "
            "EXP-005 full-validation result."
        )


def _load_verified_confirmation_frames(
    *,
    audit: dict[str, Any],
    output_files: Mapping[str, Path],
) -> dict[str, pd.DataFrame]:
    required_names = {
        "NQ_1m",
        "MNQ_1m",
        "NQ_5m",
        "MNQ_5m",
    }

    if set(output_files) != required_names:
        raise RuntimeError(
            "Frozen confirmation output-file set "
            "changed."
        )

    frames: dict[str, pd.DataFrame] = {}

    for name in sorted(required_names):
        path = Path(output_files[name])

        if not path.exists():
            raise FileNotFoundError(
                "Frozen confirmation output is "
                f"missing: {path}"
            )

        frame = pd.read_parquet(path)
        frame.index = pd.to_datetime(
            frame.index,
            utc=True,
        )
        frame = frame.sort_index()

        actual_fingerprint = (
            dataframe_sha256(frame)
        )
        expected_fingerprint = audit[
            "fingerprints"
        ][name]

        if (
            actual_fingerprint
            != expected_fingerprint
        ):
            raise RuntimeError(
                f"{name} frozen confirmation "
                "fingerprint changed."
            )

        frames[name] = frame

    if not frames["NQ_1m"].index.equals(
        frames["MNQ_1m"].index
    ):
        raise RuntimeError(
            "Frozen confirmation NQ/MNQ "
            "one-minute timestamps are not aligned."
        )

    if not frames["NQ_5m"].index.equals(
        frames["MNQ_5m"].index
    ):
        raise RuntimeError(
            "Frozen confirmation NQ/MNQ "
            "five-minute timestamps are not aligned."
        )

    for name, frame in frames.items():
        sessions = pd.to_datetime(
            frame["session_date"]
        )

        if (
            sessions.min()
            < pd.Timestamp("2023-01-03")
            or sessions.max()
            > pd.Timestamp("2025-12-31")
            or sessions.nunique()
            != EXPECTED_CONFIRMATION_SESSIONS
        ):
            raise RuntimeError(
                f"{name} frozen confirmation "
                "period or session count changed."
            )

    return frames


def load_frozen_confirmation_data_for_exp006(
) -> tuple[
    dict[str, Any],
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    # The original EXP-005 importer is intentionally
    # stage-gated to FULL_VALIDATION so it cannot be
    # reopened later. EXP-006 therefore verifies the
    # already-frozen files against the independently
    # tracked EXP-005 full-validation result instead
    # of calling that historical importer again.
    full_validation_result = (
        verify_local_full_validation_decision()
    )
    audit = _read_confirmation_audit()

    verify_confirmation_audit_for_exp006(
        audit=audit,
        full_validation_result=(
            full_validation_result
        ),
    )
    frames = (
        _load_verified_confirmation_frames(
            audit=audit,
            output_files=(
                CONFIRMATION_OUTPUT_FILES
            ),
        )
    )

    print(
        "EXP-005 frozen confirmation data "
        "passed independent hash verification."
    )
    print(
        "Sessions: "
        f"{audit['included_sessions']:,}"
    )
    print(
        "EXP-005 lifecycle reopened: False"
    )

    return (
        audit,
        frames["NQ_1m"],
        frames["MNQ_1m"],
        frames["NQ_5m"],
        frames["MNQ_5m"],
    )


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
    ) = (
        load_frozen_confirmation_data_for_exp006()
    )

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
            "EXP-005 confirmation-session count "
            "changed."
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

    if not nq_1m.index.equals(
        mnq_1m.index
    ):
        raise RuntimeError(
            "EXP-006 NQ/MNQ one-minute "
            "timestamps differ."
        )

    if not nq_5m.index.equals(
        mnq_5m.index
    ):
        raise RuntimeError(
            "EXP-006 NQ/MNQ five-minute "
            "timestamps differ."
        )

    for name, frame, expected_rows in (
        (
            "NQ_1m",
            nq_1m,
            EXPECTED_ONE_MINUTE_ROWS,
        ),
        (
            "MNQ_1m",
            mnq_1m,
            EXPECTED_ONE_MINUTE_ROWS,
        ),
        (
            "NQ_5m",
            nq_5m,
            EXPECTED_FIVE_MINUTE_ROWS,
        ),
        (
            "MNQ_5m",
            mnq_5m,
            EXPECTED_FIVE_MINUTE_ROWS,
        ),
    ):
        sessions = int(
            frame[
                "session_date"
            ].nunique()
        )

        if sessions != EXPECTED_TOTAL_SESSIONS:
            raise RuntimeError(
                f"EXP-006 {name} session count "
                f"changed: {sessions}."
            )

        if len(frame) != expected_rows:
            raise RuntimeError(
                f"EXP-006 {name} row count "
                f"changed: {len(frame)}."
            )

    audit = {
        "source_experiment": "EXP-005",
        "quick_sessions": (
            EXPECTED_QUICK_SESSIONS
        ),
        "confirmation_sessions": (
            EXPECTED_CONFIRMATION_SESSIONS
        ),
        "included_sessions": (
            EXPECTED_TOTAL_SESSIONS
        ),
        "one_minute_rows_per_symbol": (
            EXPECTED_ONE_MINUTE_ROWS
        ),
        "five_minute_rows_per_symbol": (
            EXPECTED_FIVE_MINUTE_ROWS
        ),
        "quick_audit": quick_audit,
        "confirmation_audit": (
            confirmation_audit
        ),
        "fingerprints": {
            "NQ_1m": dataframe_sha256(
                nq_1m
            ),
            "MNQ_1m": dataframe_sha256(
                mnq_1m
            ),
            "NQ_5m": dataframe_sha256(
                nq_5m
            ),
            "MNQ_5m": dataframe_sha256(
                mnq_5m
            ),
        },
        "exp005_control_changed": False,
        "exp005_lifecycle_reopened": False,
        "new_data_cleaning_decisions": 0,
    }

    return Exp006FrozenData(
        audit=audit,
        nq_1m=nq_1m,
        mnq_1m=mnq_1m,
        nq_5m=nq_5m,
        mnq_5m=mnq_5m,
    )
