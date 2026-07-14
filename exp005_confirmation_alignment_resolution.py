from __future__ import annotations

from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import exp005_quantower_import as base


PROJECT_DIR = Path(__file__).resolve().parent
RECORD_FILE = (
    PROJECT_DIR
    / "research"
    / "EXP-005_confirmation_alignment_resolution.json"
)
EXPECTED_FILE_SHA256 = "b92fd6f772d639ca2bade38535f3517721e68ab35c20aebb9f0d221c9c1d53ed"


def _sha256_file(
    path: Path,
) -> str:
    digest = hashlib.sha256()

    with Path(path).open("rb") as handle:
        for block in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def _load_record() -> dict[str, Any]:
    if not RECORD_FILE.exists():
        raise FileNotFoundError(
            "Tracked EXP-005 confirmation alignment "
            f"record is missing: {RECORD_FILE}"
        )

    if _sha256_file(RECORD_FILE) != EXPECTED_FILE_SHA256:
        raise ValueError(
            "Tracked EXP-005 confirmation alignment "
            "record hash changed."
        )

    return json.loads(
        RECORD_FILE.read_text(
            encoding="utf-8"
        )
    )


EXP005_CONFIRMATION_ALIGNMENT_RESOLUTION = (
    _load_record()
)


def get_exp005_confirmation_alignment_resolution(
) -> dict[str, Any]:
    return deepcopy(
        EXP005_CONFIRMATION_ALIGNMENT_RESOLUTION
    )


def locked_confirmation_alignment_excluded_dates(
) -> tuple[date, ...]:
    return tuple(
        date.fromisoformat(item)
        for item in sorted(
            EXP005_CONFIRMATION_ALIGNMENT_RESOLUTION[
                "excluded_sessions"
            ]
        )
    )


def validate_exp005_confirmation_alignment_resolution(
    record: dict[str, Any] | None = None,
) -> None:
    current = (
        EXP005_CONFIRMATION_ALIGNMENT_RESOLUTION
        if record is None
        else record
    )

    if (
        current.get("experiment_id") != "EXP-005"
        or current.get("record_id") != "EXP-005-DQ5"
    ):
        raise ValueError(
            "Invalid EXP-005 confirmation alignment "
            "record identity."
        )

    if current.get(
        "status"
    ) != "LOCKED_BEFORE_FULL_VALIDATION_RESULTS":
        raise ValueError(
            "Confirmation alignment resolution must "
            "precede full-validation results."
        )

    source = current["source_audit"]

    if (
        source["details_sha256"]
        != "deb9d23a2407c9fef4c98e5e28ba5ea1b08c618a4caffe37baa13c3be80b3cf9"
        or source["summary_sha256"]
        != "5d525a21634a1f3d4014587d99f576ca326924271ddd5de6488c6f3d50decc91"
    ):
        raise ValueError(
            "Confirmation alignment source-audit "
            "fingerprints changed."
        )

    protections = current["protections"]

    if (
        protections["quick_transfer_result_frozen"]
        is not True
        or protections[
            "confirmation_strategy_results_calculated"
        ]
        is not False
        or protections[
            "full_validation_results_calculated"
        ]
        is not False
        or protections["quick_transfer_rerun"]
        is not False
        or protections["source_files_modified"]
        is not False
        or protections["bars_synthesized"] != 0
    ):
        raise ValueError(
            "Confirmation alignment protection fields "
            "changed."
        )

    policy = current["alignment_policy"]

    if (
        policy["paired_session_exclusion"] is not True
        or policy[
            "maximum_allowed_median_close_difference_points"
        ]
        != 5.0
        or policy[
            "maximum_allowed_single_close_difference_points"
        ]
        != 20.0
        or policy["unrecorded_alignment_exclusion"]
        != "STOP"
        or policy["changed_alignment_metric"]
        != "STOP"
        or policy["repair_isolated_price_bar"]
        is not False
    ):
        raise ValueError(
            "Confirmation alignment policy changed."
        )

    expected_dates = {
        "2023-03-14",
        "2023-12-12",
        "2024-03-12",
        "2025-03-24",
        "2025-04-01",
        "2025-04-09",
        "2025-05-19",
        "2025-07-01",
        "2025-10-24",
    }

    if set(
        current["excluded_sessions"]
    ) != expected_dates:
        raise ValueError(
            "Locked confirmation alignment date set "
            "changed."
        )

    persistent = [
        item
        for item in current[
            "excluded_sessions"
        ].values()
        if item["category"]
        == "PERSISTENT_CROSS_SYMBOL_DIVERGENCE"
    ]
    isolated = [
        item
        for item in current[
            "excluded_sessions"
        ].values()
        if item["category"]
        == "ISOLATED_CROSS_SYMBOL_PRICE_DIVERGENCE"
    ]

    if (
        len(persistent) != 3
        or len(isolated) != 6
    ):
        raise ValueError(
            "Confirmation alignment category counts "
            "changed."
        )

    result = current["result"]

    expected_result = {
        "calendar_full_sessions": 744,
        "provider_unavailable_sessions_excluded": 2,
        "complete_retry_sessions_restored": 1,
        "common_complete_sessions_before_alignment": 742,
        "persistent_cross_symbol_divergence_sessions_excluded": 3,
        "isolated_cross_symbol_divergence_sessions_excluded": 6,
        "alignment_sessions_excluded": 9,
        "expected_included_sessions": 733,
        "expected_one_minute_rows_per_symbol": 285870,
        "expected_five_minute_rows_per_symbol": 57174,
        "included_invalid_sessions": 0,
        "included_alignment_mismatch_sessions": 0,
        "bars_synthesized": 0,
    }

    if result != expected_result:
        raise ValueError(
            "Confirmation alignment result changed."
        )


def validate_locked_confirmation_alignment_exclusions(
    *,
    exclusions: pd.DataFrame,
) -> pd.DataFrame:
    validate_exp005_confirmation_alignment_resolution()

    required = {
        "symbol",
        "session_date",
        "reason",
        "median_close_difference",
        "maximum_close_difference",
    }
    missing = required.difference(
        exclusions.columns
    )

    if missing:
        raise base.AlignmentError(
            "Confirmation alignment exclusions are "
            f"missing columns: {sorted(missing)}"
        )

    observed = exclusions.copy()
    observed["session_date"] = (
        observed["session_date"]
        .astype(str)
    )

    if (
        len(observed) != 9
        or observed[
            "session_date"
        ].duplicated().any()
    ):
        raise base.AlignmentError(
            "Confirmation alignment exclusion count "
            "or uniqueness changed."
        )

    specifications = (
        EXP005_CONFIRMATION_ALIGNMENT_RESOLUTION[
            "excluded_sessions"
        ]
    )

    if set(
        observed["session_date"]
    ) != set(specifications):
        raise base.AlignmentError(
            "Observed confirmation alignment dates do "
            "not exactly match locked record EXP-005-DQ5."
        )

    output_rows: list[dict[str, Any]] = []

    for row in observed.to_dict(
        orient="records"
    ):
        session_text = str(
            row["session_date"]
        )
        expected = specifications[
            session_text
        ]

        if (
            str(row["symbol"]) != "BOTH"
            or str(row["reason"])
            != "potential_front_month_mismatch"
        ):
            raise base.AlignmentError(
                "Confirmation alignment identity "
                f"changed for {session_text}."
            )

        for field in (
            "median_close_difference",
            "maximum_close_difference",
        ):
            if not np.isclose(
                float(row[field]),
                float(expected[field]),
                atol=1e-12,
                rtol=0.0,
            ):
                raise base.AlignmentError(
                    "Confirmation alignment metric "
                    f"changed for {session_text}: "
                    f"{field}."
                )

        output_rows.append(
            {
                **row,
                "reason": (
                    "locked_confirmation_cross_symbol_"
                    "alignment_exclusion"
                ),
                "alignment_category": (
                    expected["category"]
                ),
                "resolution_record": "EXP-005-DQ5",
                "bars_synthesized": 0,
                "detail": (
                    "Both NQ and MNQ were excluded "
                    "together by the unchanged locked "
                    "alignment thresholds."
                ),
            }
        )

    result = pd.DataFrame(
        output_rows
    ).sort_values(
        "session_date"
    ).reset_index(
        drop=True
    )

    return result


if __name__ == "__main__":
    validate_exp005_confirmation_alignment_resolution()
    print(
        "EXP-005 confirmation alignment resolution "
        "is valid."
    )
