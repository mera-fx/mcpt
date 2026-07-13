from __future__ import annotations

from copy import deepcopy
from typing import Any

from exp005_preregistration import (
    get_exp005_preregistration,
    validate_exp005_preregistration,
)


EXP005_SOURCE_AMENDMENT: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-005",
    "amendment_id": "EXP-005-A1",
    "amended_date": "2026-07-13",
    "status": "LOCKED_BEFORE_FULL_DATA_EXPORT",
    "reason": (
        "Replace the originally named paid data source with "
        "an existing zero-additional-cost Lucid Trading / "
        "Rithmic connection accessed through Quantower."
    ),
    "results_viewed": "NONE",
    "source_validation_only": True,
    "old_source": {
        "provider": "Databento",
        "dataset": "GLBX.MDP3",
        "symbols": {
            "NQ": "NQ.v.0",
            "MNQ": "MNQ.v.0",
        },
        "roll_claim": "volume-ranked front contract",
        "price_adjustment_claim": "none",
    },
    "new_source": {
        "provider": (
            "Lucid Trading / Rithmic via Quantower "
            "History Exporter"
        ),
        "additional_data_cost": 0.0,
        "symbols": {
            "NQ": "NQ",
            "MNQ": "MNQ",
        },
        "symbol_type": "provider_front_month",
        "roll_statement": (
            "Provider-defined front month. The exact rollover "
            "trigger is not exposed by the CSV export."
        ),
        "price_adjustment_statement": (
            "Unknown/provider-defined. No adjusted or "
            "unadjusted claim is made."
        ),
        "input": "Quantower Time-Time one-minute CSV",
        "timestamps": "UTC",
    },
    "sample_evidence": {
        "date": "2019-08-09",
        "strategy_metrics_calculated": False,
        "NQ": {
            "raw_rows": 1305,
            "cash_session_rows": 390,
            "five_minute_bars": 78,
            "missing_cash_minutes": 0,
            "duplicate_timestamps": 0,
            "invalid_ohlc_rows": 0,
            "tick_nonconforming_values": 0,
            "sha256": (
                "9fd2ac2ab4e9185ce937d969cc0184c6"
                "f7757a108c4eb8dd58d13d27840678c9"
            ),
        },
        "MNQ": {
            "raw_rows": 1300,
            "cash_session_rows": 390,
            "five_minute_bars": 78,
            "missing_cash_minutes": 0,
            "duplicate_timestamps": 0,
            "invalid_ohlc_rows": 0,
            "tick_nonconforming_values": 0,
            "sha256": (
                "e330ee53d485975772de33bc60d97006"
                "bc7d9f24c10345579a9f01225a6bb369"
            ),
        },
    },
    "roll_risk_controls": {
        "same_session_strategy_only": True,
        "previous_close_used": False,
        "overnight_gap_used": False,
        "overnight_position_allowed": False,
        "identical_nq_mnq_cash_timestamps_required": True,
        "maximum_median_close_difference_points": 5.0,
        "maximum_single_close_difference_points": 20.0,
        "failure_action": (
            "Exclude the session from both symbols as a "
            "potential front-month mismatch or data anomaly."
        ),
        "included_mismatch_sessions_allowed": 0,
    },
    "unchanged_research_components": [
        "Hypothesis and null hypothesis",
        "15-minute both-direction ORB",
        "Next-bar-open execution",
        "Opposite-range protective stop",
        "One trade per session",
        "15:55 ET forced exit",
        "No optimization",
        "2019-05-06 through 2022-12-30 quick period",
        "2023-01-03 through 2025-12-31 confirmation lock",
        "NQ and MNQ multipliers and modeled costs",
        "Session-aware MCPT",
        "Every quick-transfer and full-validation threshold",
    ],
    "prohibited": [
        "Downloading or exporting 2023–2025 before quick pass",
        "Changing signal, cost or gate values",
        "Claiming a known provider roll rule",
        "Claiming a known adjustment method",
        "Treating the one-day source samples as research results",
    ],
    "document": "research/EXP-005_source_amendment.md",
}


def get_exp005_source_amendment(
) -> dict[str, Any]:
    return deepcopy(
        EXP005_SOURCE_AMENDMENT
    )


def validate_exp005_source_amendment(
    record: dict[str, Any] | None = None,
) -> None:
    validate_exp005_preregistration()

    current = (
        EXP005_SOURCE_AMENDMENT
        if record is None
        else record
    )

    if (
        current.get("experiment_id") != "EXP-005"
        or current.get("amendment_id") != "EXP-005-A1"
    ):
        raise ValueError(
            "Invalid EXP-005 amendment identity."
        )

    if current.get(
        "status"
    ) != "LOCKED_BEFORE_FULL_DATA_EXPORT":
        raise ValueError(
            "EXP-005 amendment must precede full export."
        )

    if current.get(
        "results_viewed"
    ) != "NONE":
        raise ValueError(
            "EXP-005 amendment cannot contain results."
        )

    if current.get(
        "source_validation_only"
    ) is not True:
        raise ValueError(
            "EXP-005 samples must remain source validation."
        )

    new_source = current[
        "new_source"
    ]

    if (
        new_source["additional_data_cost"] != 0.0
        or new_source["symbols"]
        != {
            "NQ": "NQ",
            "MNQ": "MNQ",
        }
        or new_source["symbol_type"]
        != "provider_front_month"
    ):
        raise ValueError(
            "EXP-005 free source identity changed."
        )

    evidence = current[
        "sample_evidence"
    ]

    if evidence[
        "strategy_metrics_calculated"
    ] is not False:
        raise ValueError(
            "Sample evidence cannot contain strategy metrics."
        )

    for symbol, expected_rows, expected_hash in (
        (
            "NQ",
            1305,
            (
                "9fd2ac2ab4e9185ce937d969cc0184c6"
                "f7757a108c4eb8dd58d13d27840678c9"
            ),
        ),
        (
            "MNQ",
            1300,
            (
                "e330ee53d485975772de33bc60d97006"
                "bc7d9f24c10345579a9f01225a6bb369"
            ),
        ),
    ):
        sample = evidence[symbol]

        if (
            sample["raw_rows"] != expected_rows
            or sample["cash_session_rows"] != 390
            or sample["five_minute_bars"] != 78
            or sample["missing_cash_minutes"] != 0
            or sample["duplicate_timestamps"] != 0
            or sample["invalid_ohlc_rows"] != 0
            or sample["tick_nonconforming_values"] != 0
            or sample["sha256"] != expected_hash
        ):
            raise ValueError(
                f"{symbol} source sample evidence changed."
            )

    controls = current[
        "roll_risk_controls"
    ]

    if (
        controls[
            "maximum_median_close_difference_points"
        ] != 5.0
        or controls[
            "maximum_single_close_difference_points"
        ] != 20.0
        or controls[
            "included_mismatch_sessions_allowed"
        ] != 0
    ):
        raise ValueError(
            "EXP-005 roll-risk controls changed."
        )

    preregistration = get_exp005_preregistration()

    if (
        preregistration["source_amendment"][
            "amendment_id"
        ]
        != current["amendment_id"]
    ):
        raise ValueError(
            "EXP-005 preregistration and amendment disagree."
        )


if __name__ == "__main__":
    validate_exp005_source_amendment()

    print(
        "EXP-005 free Lucid/Rithmic source amendment "
        "is valid."
    )
