from __future__ import annotations

from copy import deepcopy
from typing import Any


EXP005_MISSING_SESSION_RESOLUTION: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-005",
    "record_id": "EXP-005-DQ2",
    "locked_date": "2026-07-13",
    "status": "LOCKED_BEFORE_STRATEGY_RESULTS",
    "strategy_results_viewed": False,
    "confirmation_period_accessed": False,
    "purpose": (
        "Document three provider-history sessions that remained "
        "incomplete after dedicated one-day re-export attempts "
        "and exclude both NQ and MNQ for those dates without "
        "filling or inventing bars."
    ),
    "policy": {
        "paired_exclusion": True,
        "fill_missing_bars": False,
        "edit_raw_files": False,
        "change_strategy_rules": False,
        "change_costs": False,
        "change_gates": False,
        "unrecorded_incomplete_session": "STOP",
    },
    "required_source_hashes": {
        "NQ": {
            "full_export": (
                "0e4834ab140f87ea6f406ac3e4173163"
                "0278585ef75fcb3b10bad9bc96a0bf77"
            ),
            "2020-07-21_retry": (
                "cc8c828f1010d38e08f72aad4a6acf9"
                "036ff6a0fe0ee0efcc77b6824a337c3f6"
            ),
        },
        "MNQ": {
            "full_export": (
                "fede2377a13c5647bec9302ff8b1d3f1"
                "c161b46c382f7501d576e3f76b503bff"
            ),
            "2019-05-06_retry": (
                "6566a664553358cc3936fc1bfcdc846f"
                "9e26b3fc07bfa34f91610e0363d5d66b"
            ),
            "2019-06-17_retry": (
                "ee06bca746cb1881b2d484746e69d664"
                "9d0fb067bd655db8c2ad5cdaa1dd7597"
            ),
            "2020-07-21_retry": (
                "c1a6aecb1d6ed91180b5d8e8843e8fa"
                "7dc11b80f9af55fdf255890fe4d68659a"
            ),
        },
    },
    "sessions": {
        "2019-05-06": {
            "reason": (
                "MNQ provider history begins at 10:47 ET in both "
                "the full export and the dedicated retry."
            ),
            "symbols": {
                "NQ": {
                    "actual_bars": 390,
                    "missing_mode": "none",
                },
                "MNQ": {
                    "actual_bars": 313,
                    "missing_mode": "leading_range",
                    "missing_start": "09:30",
                    "missing_end": "10:46",
                },
            },
        },
        "2019-06-17": {
            "reason": (
                "MNQ has the same 12 absent cash-session minutes "
                "in both the full export and the dedicated retry."
            ),
            "symbols": {
                "NQ": {
                    "actual_bars": 390,
                    "missing_mode": "none",
                },
                "MNQ": {
                    "actual_bars": 378,
                    "missing_mode": "explicit",
                    "missing_times": [
                        "12:24",
                        "13:12",
                        "13:25",
                        "13:29",
                        "13:31",
                        "13:32",
                        "13:33",
                        "13:53",
                        "14:33",
                        "14:39",
                        "14:43",
                        "14:44",
                    ],
                },
            },
        },
        "2020-07-21": {
            "reason": (
                "No NQ or MNQ bars were returned for the session "
                "by either the full exports or dedicated retries."
            ),
            "symbols": {
                "NQ": {
                    "actual_bars": 0,
                    "missing_mode": "full_session",
                },
                "MNQ": {
                    "actual_bars": 0,
                    "missing_mode": "full_session",
                },
            },
        },
    },
    "expected_missing_session_rows": {
        "2019-05-06": ["MNQ"],
        "2019-06-17": ["MNQ"],
        "2020-07-21": ["NQ", "MNQ"],
    },
    "result": {
        "paired_sessions_excluded": 3,
        "included_invalid_sessions": 0,
        "bars_synthesized": 0,
    },
    "document": (
        "research/EXP-005_missing_session_resolution.md"
    ),
}


def get_exp005_missing_session_resolution(
) -> dict[str, Any]:
    return deepcopy(
        EXP005_MISSING_SESSION_RESOLUTION
    )


def validate_exp005_missing_session_resolution(
    record: dict[str, Any] | None = None,
) -> None:
    current = (
        EXP005_MISSING_SESSION_RESOLUTION
        if record is None
        else record
    )

    if (
        current.get("experiment_id") != "EXP-005"
        or current.get("record_id") != "EXP-005-DQ2"
    ):
        raise ValueError(
            "Invalid EXP-005 missing-session record identity."
        )

    if current.get(
        "status"
    ) != "LOCKED_BEFORE_STRATEGY_RESULTS":
        raise ValueError(
            "Missing-session record must precede results."
        )

    if current.get(
        "strategy_results_viewed"
    ) is not False:
        raise ValueError(
            "Missing-session record cannot contain results."
        )

    if current.get(
        "confirmation_period_accessed"
    ) is not False:
        raise ValueError(
            "Confirmation period must remain blocked."
        )

    policy = current["policy"]

    if (
        policy["paired_exclusion"] is not True
        or policy["fill_missing_bars"] is not False
        or policy["edit_raw_files"] is not False
        or policy["unrecorded_incomplete_session"] != "STOP"
    ):
        raise ValueError(
            "EXP-005 missing-session policy changed."
        )

    if set(current["sessions"]) != {
        "2019-05-06",
        "2019-06-17",
        "2020-07-21",
    }:
        raise ValueError(
            "Locked provider-unavailable dates changed."
        )

    for symbol, items in current[
        "required_source_hashes"
    ].items():
        if symbol not in {"NQ", "MNQ"}:
            raise ValueError(
                "Unexpected symbol in source hashes."
            )

        for digest in items.values():
            if len(digest) != 64:
                raise ValueError(
                    "Every locked source hash must be SHA-256."
                )

    expected = current[
        "expected_missing_session_rows"
    ]

    if expected != {
        "2019-05-06": ["MNQ"],
        "2019-06-17": ["MNQ"],
        "2020-07-21": ["NQ", "MNQ"],
    }:
        raise ValueError(
            "Expected incomplete-symbol profile changed."
        )

    result = current["result"]

    if (
        result["paired_sessions_excluded"] != 3
        or result["included_invalid_sessions"] != 0
        or result["bars_synthesized"] != 0
    ):
        raise ValueError(
            "Locked resolution result changed."
        )


if __name__ == "__main__":
    validate_exp005_missing_session_resolution()

    print(
        "EXP-005 missing-session resolution is valid."
    )
