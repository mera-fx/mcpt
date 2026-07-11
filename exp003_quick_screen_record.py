from __future__ import annotations

from copy import deepcopy
from typing import Any

from exp003_preregistration import (
    get_exp003_preregistration,
)


EXP003_QUICK_SCREEN_RECORD: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-003",
    "decision": "PASS_TO_FULL_VALIDATION",
    "passed": True,
    "source_git_commit_short": "0e4e67a",
    "source_decision_file": (
        "results/EXP-003/quick_screen/"
        "quick_screen_decision.json"
    ),
    "source_report_file": (
        "reports/EXP-003-quick-screen/report.html"
    ),
    "gates": {
        "best_in_sample_bar_pf": {
            "actual": 1.1149662652395165,
            "operator": ">",
            "threshold": 1.0,
            "passed": True,
        },
        "parameter_combinations_pf_ge_1": {
            "actual": 27,
            "operator": ">=",
            "threshold": 6,
            "passed": True,
        },
        "neighbor_median_ratio_to_best": {
            "actual": 0.9917160295704314,
            "operator": ">=",
            "threshold": 0.95,
            "passed": True,
        },
        "quick_mcpt_p_value": {
            "actual": 0.07692307692307693,
            "operator": "<=",
            "threshold": 0.20,
            "passed": True,
        },
        "fixed_in_sample_completed_trades": {
            "actual": 105,
            "operator": ">=",
            "threshold": 50,
            "passed": True,
        },
    },
    "failed_gates": [],
}


def get_exp003_quick_screen_record() -> dict[str, Any]:
    return deepcopy(EXP003_QUICK_SCREEN_RECORD)


def validate_exp003_quick_screen_record(
    record: dict[str, Any] | None = None,
) -> None:
    candidate = (
        EXP003_QUICK_SCREEN_RECORD
        if record is None
        else record
    )

    if candidate.get("experiment_id") != "EXP-003":
        raise ValueError(
            "Quick-screen record must belong to EXP-003."
        )

    if candidate.get("decision") != "PASS_TO_FULL_VALIDATION":
        raise ValueError(
            "Tracked quick-screen decision must be "
            "PASS_TO_FULL_VALIDATION."
        )

    if candidate.get("passed") is not True:
        raise ValueError(
            "Tracked quick-screen record must have passed=True."
        )

    if candidate.get("failed_gates") != []:
        raise ValueError(
            "Tracked quick-screen record cannot contain failed gates."
        )

    expected = {
        "best_in_sample_bar_pf": (
            ">",
            get_exp003_preregistration()[
                "quick_screen"
            ]["gates"][
                "best_in_sample_bar_pf_strictly_above"
            ],
        ),
        "parameter_combinations_pf_ge_1": (
            ">=",
            get_exp003_preregistration()[
                "quick_screen"
            ]["gates"][
                "minimum_parameter_combinations_pf_ge_1"
            ],
        ),
        "neighbor_median_ratio_to_best": (
            ">=",
            get_exp003_preregistration()[
                "quick_screen"
            ]["gates"][
                "minimum_neighbour_median_ratio_to_best"
            ],
        ),
        "quick_mcpt_p_value": (
            "<=",
            get_exp003_preregistration()[
                "quick_screen"
            ]["gates"][
                "maximum_quick_mcpt_p_value"
            ],
        ),
        "fixed_in_sample_completed_trades": (
            ">=",
            get_exp003_preregistration()[
                "quick_screen"
            ]["gates"][
                "minimum_in_sample_completed_trades_fixed"
            ],
        ),
    }

    gates = candidate.get("gates", {})

    if set(gates) != set(expected):
        raise ValueError(
            "Tracked quick-screen gate names do not match "
            "the preregistration."
        )

    for gate_name, (
        expected_operator,
        expected_threshold,
    ) in expected.items():
        gate = gates[gate_name]

        if gate.get("operator") != expected_operator:
            raise ValueError(
                f"Operator mismatch for {gate_name}."
            )

        if gate.get("threshold") != expected_threshold:
            raise ValueError(
                f"Threshold mismatch for {gate_name}."
            )

        if gate.get("passed") is not True:
            raise ValueError(
                f"Tracked gate {gate_name} did not pass."
            )


if __name__ == "__main__":
    validate_exp003_quick_screen_record()
    print(
        "EXP-003 quick-screen record is valid: "
        "PASS_TO_FULL_VALIDATION"
    )
