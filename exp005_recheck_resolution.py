from __future__ import annotations

from copy import deepcopy
from typing import Any


EXP005_RECHECK_RESOLUTION: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-005",
    "record_id": "EXP-005-DQ1",
    "locked_date": "2026-07-13",
    "status": "LOCKED_BEFORE_STRATEGY_RESULTS",
    "purpose": (
        "Resolve four provider front-month OHLC conflicts using "
        "dedicated one-day re-exports, while preserving all "
        "strategy rules, periods, costs and gates."
    ),
    "strategy_results_viewed": False,
    "confirmation_period_accessed": False,
    "normalization_rules": {
        "exact_ohlcv_duplicate": (
            "Keep one identical copy."
        ),
        "volume_only_conflict": (
            "When OHLC is identical and only volume differs, "
            "keep the maximum volume. EXP-005 does not use "
            "volume in any signal, entry, exit or gate."
        ),
        "ohlc_conflict": (
            "Replace only when a locked dedicated one-day "
            "re-export exists, matches one of the original "
            "conflicting rows exactly, and its file hash and "
            "bar values match this record."
        ),
        "unresolved_ohlc_conflict": "STOP",
        "raw_files_edited": False,
    },
    "recheck_files": {
        "NQ": {
            "2020-06-11": {
                "sha256": (
                    "089eeb4202ccca58ba9cccf259edc6862"
                    "a82fa8eabed99dd261f3f4e2f8cfabc"
                ),
                "timestamp_utc": "2020-06-11T17:40:00+00:00",
                "bar": {
                    "open": 9737.75,
                    "high": 9741.50,
                    "low": 9732.00,
                    "close": 9739.75,
                    "volume": 953.0,
                },
                "raw_rows": 1365,
                "duplicate_timestamps": 0,
            },
            "2020-10-21": {
                "sha256": (
                    "9819d55df092da47922ef41cac21b9fa"
                    "c4f66da7801cfb62f3d29a4d5e2c92d5"
                ),
                "timestamp_utc": "2020-10-21T16:20:00+00:00",
                "bar": {
                    "open": 11653.75,
                    "high": 11701.00,
                    "low": 11651.00,
                    "close": 11700.00,
                    "volume": 3082.0,
                },
                "raw_rows": 1365,
                "duplicate_timestamps": 0,
            },
        },
        "MNQ": {
            "2020-06-11": {
                "sha256": (
                    "48aca4807f724b12af93537ef866f6754"
                    "9e9ab106c8ea2aae172f4c2f9250330"
                ),
                "timestamp_utc": "2020-06-11T17:40:00+00:00",
                "bar": {
                    "open": 9738.00,
                    "high": 9741.75,
                    "low": 9732.00,
                    "close": 9739.50,
                    "volume": 1034.0,
                },
                "raw_rows": 1365,
                "duplicate_timestamps": 0,
            },
            "2020-10-21": {
                "sha256": (
                    "53374d9f82023217623a80260dcf6081"
                    "6e6f7fd08c288be1933036bf43fd04b8"
                ),
                "timestamp_utc": "2020-10-21T16:20:00+00:00",
                "bar": {
                    "open": 11653.75,
                    "high": 11700.00,
                    "low": 11651.00,
                    "close": 11700.00,
                    "volume": 4284.0,
                },
                "raw_rows": 1365,
                "duplicate_timestamps": 0,
            },
        },
    },
    "evidence": {
        "full_export_duplicate_timestamps": 222,
        "inside_research_session": 66,
        "inside_exact_ohlcv_duplicates": 0,
        "inside_volume_only_conflicts": 62,
        "inside_ohlc_conflicts": 4,
        "unique_ohlc_conflict_timestamps": 2,
        "dedicated_reexports_have_duplicates": False,
        "dedicated_reexports_match_original_candidate": True,
    },
    "interpretation": (
        "The two one-day re-exports returned one stable bar for "
        "each affected symbol and timestamp. Each stable bar "
        "matches the lower-volume candidate in the original "
        "full export. This record does not claim why Quantower "
        "created the additional conflicting rows."
    ),
    "document": (
        "research/EXP-005_quantower_recheck_resolution.md"
    ),
}


def get_exp005_recheck_resolution(
) -> dict[str, Any]:
    return deepcopy(
        EXP005_RECHECK_RESOLUTION
    )


def validate_exp005_recheck_resolution(
    record: dict[str, Any] | None = None,
) -> None:
    current = (
        EXP005_RECHECK_RESOLUTION
        if record is None
        else record
    )

    if (
        current.get("experiment_id") != "EXP-005"
        or current.get("record_id") != "EXP-005-DQ1"
    ):
        raise ValueError(
            "Invalid EXP-005 recheck record identity."
        )

    if current.get(
        "status"
    ) != "LOCKED_BEFORE_STRATEGY_RESULTS":
        raise ValueError(
            "Recheck resolution must precede results."
        )

    if current.get(
        "strategy_results_viewed"
    ) is not False:
        raise ValueError(
            "Recheck record cannot contain strategy results."
        )

    if current.get(
        "confirmation_period_accessed"
    ) is not False:
        raise ValueError(
            "Confirmation period must remain blocked."
        )

    rules = current[
        "normalization_rules"
    ]

    if (
        "maximum volume"
        not in rules["volume_only_conflict"]
        or rules["unresolved_ohlc_conflict"] != "STOP"
        or rules["raw_files_edited"] is not False
    ):
        raise ValueError(
            "EXP-005 duplicate rules changed."
        )

    files = current[
        "recheck_files"
    ]

    if set(files) != {"NQ", "MNQ"}:
        raise ValueError(
            "Recheck symbols changed."
        )

    expected_dates = {
        "2020-06-11",
        "2020-10-21",
    }

    for symbol in ("NQ", "MNQ"):
        if set(files[symbol]) != expected_dates:
            raise ValueError(
                f"{symbol} recheck dates changed."
            )

        for item in files[symbol].values():
            if len(item["sha256"]) != 64:
                raise ValueError(
                    "Recheck SHA-256 must be complete."
                )

            if item["raw_rows"] != 1365:
                raise ValueError(
                    "Recheck raw-row count changed."
                )

            if item["duplicate_timestamps"] != 0:
                raise ValueError(
                    "Recheck file cannot contain duplicates."
                )

    evidence = current[
        "evidence"
    ]

    if (
        evidence["inside_volume_only_conflicts"] != 62
        or evidence["inside_ohlc_conflicts"] != 4
        or evidence["unique_ohlc_conflict_timestamps"] != 2
    ):
        raise ValueError(
            "Duplicate audit evidence changed."
        )


if __name__ == "__main__":
    validate_exp005_recheck_resolution()

    print(
        "EXP-005 Quantower recheck resolution is valid."
    )
