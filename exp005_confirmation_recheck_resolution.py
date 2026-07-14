from __future__ import annotations

from copy import deepcopy
from typing import Any


EXP005_CONFIRMATION_RECHECK_RESOLUTION: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-005",
    "record_id": "EXP-005-DQ3",
    "locked_date": "2026-07-14",
    "status": "LOCKED_BEFORE_CONFIRMATION_STRATEGY_RESULTS",
    "purpose": (
        "Resolve the two confirmation-period provider-front-month "
        "OHLC conflicts using dedicated one-day NQ and MNQ "
        "re-exports, without calculating strategy or "
        "full-validation results."
    ),
    "quick_transfer_result_frozen": True,
    "confirmation_source_accessed": True,
    "strategy_results_calculated": False,
    "full_validation_results_calculated": False,
    "raw_files_edited": False,
    "normalization_rules": {
        "exact_ohlcv_duplicate": (
            "Keep one identical copy."
        ),
        "volume_only_conflict": (
            "When OHLC is identical and only volume differs, "
            "keep the maximum volume inside the locked cash "
            "session. EXP-005 does not use volume in any signal, "
            "entry, exit or gate."
        ),
        "ohlc_conflict": (
            "Replace only when the SHA-256-locked dedicated "
            "one-day re-export matches one of the original "
            "conflicting rows exactly."
        ),
        "unresolved_ohlc_conflict": "STOP",
    },
    "duplicate_audit": {
        "summary_sha256": (
            "13d3815d799d3f26322b9961e7574c60"
            "822569e85d2b3eae2c07235b0abf20d9"
        ),
        "details_sha256": (
            "62d35c12b42dae795100e703ae4e0ada"
            "ed69fbb0df343b4fad803c80c5215994"
        ),
        "recheck_plan_sha256": (
            "93c2bb9d4ff9e0f2a75886978730e22"
            "df436e8f4a9b04930142eb06eafd8b333"
        ),
        "total_duplicate_timestamps": 200,
        "inside_confirmation_cash_session": 54,
        "outside_confirmation_cash_session": 146,
        "inside_volume_only_conflicts": 52,
        "inside_ohlc_conflicts": 2,
        "unique_ohlc_conflict_timestamps": 1,
        "nq_duplicate_timestamps": 100,
        "mnq_duplicate_timestamps": 100,
        "nq_inside_volume_only_conflicts": 26,
        "mnq_inside_volume_only_conflicts": 26,
        "nq_inside_ohlc_conflicts": 1,
        "mnq_inside_ohlc_conflicts": 1,
    },
    "recheck_files": {
        "NQ": {
            "2024-11-06": {
                "sha256": (
                    "82356fcec569434e317ea1ad60bf294a"
                    "76493fb65eae8a842438df98bcc93986"
                ),
                "raw_rows": 1380,
                "unique_timestamps": 1380,
                "duplicate_timestamps": 0,
                "first_timestamp_utc": (
                    "2024-11-06T00:00:00+00:00"
                ),
                "last_timestamp_utc": (
                    "2024-11-06T23:59:00+00:00"
                ),
                "expected_missing_start_utc": (
                    "2024-11-06T22:00:00+00:00"
                ),
                "expected_missing_end_utc": (
                    "2024-11-06T22:59:00+00:00"
                ),
                "expected_missing_minutes": 60,
                "timestamp_utc": (
                    "2024-11-06T14:40:00+00:00"
                ),
                "bar": {
                    "open": 20793.00,
                    "high": 20805.25,
                    "low": 20778.25,
                    "close": 20783.75,
                    "volume": 3845.0,
                },
            },
        },
        "MNQ": {
            "2024-11-06": {
                "sha256": (
                    "ed8704b7932a1077bd521cea5abc40e9"
                    "d735e9d032bb2014127ebbd4e4a2f0db"
                ),
                "raw_rows": 1380,
                "unique_timestamps": 1380,
                "duplicate_timestamps": 0,
                "first_timestamp_utc": (
                    "2024-11-06T00:00:00+00:00"
                ),
                "last_timestamp_utc": (
                    "2024-11-06T23:59:00+00:00"
                ),
                "expected_missing_start_utc": (
                    "2024-11-06T22:00:00+00:00"
                ),
                "expected_missing_end_utc": (
                    "2024-11-06T22:59:00+00:00"
                ),
                "expected_missing_minutes": 60,
                "timestamp_utc": (
                    "2024-11-06T14:40:00+00:00"
                ),
                "bar": {
                    "open": 20793.00,
                    "high": 20806.75,
                    "low": 20778.25,
                    "close": 20783.75,
                    "volume": 8851.0,
                },
            },
        },
    },
    "evidence": {
        "dedicated_reexports_have_duplicates": False,
        "dedicated_reexports_match_original_candidate": True,
        "selected_candidate": (
            "lower-volume candidate for both NQ and MNQ"
        ),
        "selected_close": 20783.75,
        "strategy_results_viewed_during_resolution": False,
    },
    "interpretation": (
        "Both independent one-day re-exports returned a single "
        "14:40 UTC bar with close 20783.75. Each bar exactly "
        "matches the lower-volume candidate in its original full "
        "export. This record does not claim why the duplicate "
        "provider rows occurred."
    ),
    "document": (
        "research/"
        "EXP-005_confirmation_recheck_resolution.md"
    ),
}


def get_exp005_confirmation_recheck_resolution(
) -> dict[str, Any]:
    return deepcopy(
        EXP005_CONFIRMATION_RECHECK_RESOLUTION
    )


def validate_exp005_confirmation_recheck_resolution(
    record: dict[str, Any] | None = None,
) -> None:
    current = (
        EXP005_CONFIRMATION_RECHECK_RESOLUTION
        if record is None
        else record
    )

    if (
        current.get("experiment_id") != "EXP-005"
        or current.get("record_id") != "EXP-005-DQ3"
    ):
        raise ValueError(
            "Invalid confirmation recheck record identity."
        )

    if current.get("status") != (
        "LOCKED_BEFORE_CONFIRMATION_STRATEGY_RESULTS"
    ):
        raise ValueError(
            "Confirmation recheck must be locked before results."
        )

    if (
        current.get("quick_transfer_result_frozen") is not True
        or current.get("confirmation_source_accessed") is not True
        or current.get("strategy_results_calculated") is not False
        or current.get("full_validation_results_calculated")
        is not False
        or current.get("raw_files_edited") is not False
    ):
        raise ValueError(
            "Confirmation recheck protection fields changed."
        )

    rules = current["normalization_rules"]

    if (
        "maximum volume"
        not in rules["volume_only_conflict"]
        or "matches one of the original"
        not in rules["ohlc_conflict"]
        or rules["unresolved_ohlc_conflict"] != "STOP"
    ):
        raise ValueError(
            "Confirmation duplicate normalization rules changed."
        )

    audit = current["duplicate_audit"]

    expected_audit = {
        "total_duplicate_timestamps": 200,
        "inside_confirmation_cash_session": 54,
        "outside_confirmation_cash_session": 146,
        "inside_volume_only_conflicts": 52,
        "inside_ohlc_conflicts": 2,
        "unique_ohlc_conflict_timestamps": 1,
        "nq_duplicate_timestamps": 100,
        "mnq_duplicate_timestamps": 100,
        "nq_inside_volume_only_conflicts": 26,
        "mnq_inside_volume_only_conflicts": 26,
        "nq_inside_ohlc_conflicts": 1,
        "mnq_inside_ohlc_conflicts": 1,
    }

    for key, expected in expected_audit.items():
        if audit.get(key) != expected:
            raise ValueError(
                f"Confirmation duplicate audit field changed: {key}."
            )

    for key in (
        "summary_sha256",
        "details_sha256",
        "recheck_plan_sha256",
    ):
        if len(str(audit.get(key, ""))) != 64:
            raise ValueError(
                f"Confirmation audit hash is invalid: {key}."
            )

    files = current["recheck_files"]

    if set(files) != {"NQ", "MNQ"}:
        raise ValueError(
            "Confirmation recheck symbols changed."
        )

    expected_hashes = {
        "NQ": (
            "82356fcec569434e317ea1ad60bf294a"
            "76493fb65eae8a842438df98bcc93986"
        ),
        "MNQ": (
            "ed8704b7932a1077bd521cea5abc40e9"
            "d735e9d032bb2014127ebbd4e4a2f0db"
        ),
    }

    expected_highs = {
        "NQ": 20805.25,
        "MNQ": 20806.75,
    }

    expected_volumes = {
        "NQ": 3845.0,
        "MNQ": 8851.0,
    }

    for symbol in ("NQ", "MNQ"):
        if set(files[symbol]) != {"2024-11-06"}:
            raise ValueError(
                f"{symbol} confirmation recheck date changed."
            )

        item = files[symbol]["2024-11-06"]

        if item["sha256"] != expected_hashes[symbol]:
            raise ValueError(
                f"{symbol} confirmation recheck hash changed."
            )

        if (
            item["raw_rows"] != 1380
            or item["unique_timestamps"] != 1380
            or item["duplicate_timestamps"] != 0
            or item["expected_missing_minutes"] != 60
        ):
            raise ValueError(
                f"{symbol} confirmation recheck structure changed."
            )

        bar = item["bar"]

        expected_bar = {
            "open": 20793.0,
            "high": expected_highs[symbol],
            "low": 20778.25,
            "close": 20783.75,
            "volume": expected_volumes[symbol],
        }

        if bar != expected_bar:
            raise ValueError(
                f"{symbol} confirmation recheck bar changed."
            )


if __name__ == "__main__":
    validate_exp005_confirmation_recheck_resolution()

    print(
        "EXP-005 confirmation recheck resolution is valid."
    )
