from __future__ import annotations

from copy import deepcopy
from typing import Any

from exp005_preregistration import (
    get_exp005_preregistration,
)


EXP005_FULL_VALIDATION_IMPLEMENTATION: dict[
    str,
    Any,
] = {
    "schema_version": 1,
    "experiment_id": "EXP-005",
    "record_id": "EXP-005-I3",
    "implemented_date": "2026-07-14",
    "status": "IMPLEMENTED_BEFORE_FULL_RESULTS",
    "full_validation_results_viewed": False,
    "quick_transfer_rerun": False,
    "runner": "run_exp005_full_validation.py",
    "strategy_engine": "exp005_futures_orb.py",
    "mcpt_engine": "exp005_full_session_mcpt.py",
    "evaluation": "exp005_full_validation.py",
    "document": (
        "research/"
        "EXP-005_full_validation_implementation.md"
    ),
    "confirmation_import": {
        "audit": (
            "results/EXP-005/confirmation_data/"
            "quantower_confirmation_import_audit.json"
        ),
        "import_commit": (
            "53a740aedb63e2a7508e3e010f5370be49cf816a"
        ),
        "included_sessions": 733,
        "NQ_1m_rows": 285_870,
        "MNQ_1m_rows": 285_870,
        "NQ_5m_rows": 57_174,
        "MNQ_5m_rows": 57_174,
        "included_invalid_sessions": 0,
        "included_roll_switch_sessions": 0,
    },
    "locked_strategy": {
        "opening_range_minutes": 15,
        "direction_mode": "both",
        "parameter_combinations": 1,
        "optimization": False,
        "entry": "next_five_minute_open",
        "final_signal_bar": (
            "11:55 America/New_York"
        ),
        "final_entry": "12:00 America/New_York",
        "same_entry_bar_stop": True,
        "maximum_trades_per_session": 1,
        "same_day_reversal": False,
        "forced_flat": (
            "15:55 America/New_York open"
        ),
        "overnight_positions": False,
    },
    "cost_model": {
        "decision_slippage_ticks_per_side": 1.0,
        "sensitivity_ticks_per_side": [
            0.0,
            1.0,
            2.0,
        ],
        "NQ_round_trip_usd": 15.0,
        "MNQ_round_trip_usd": 3.0,
    },
    "mcpt": {
        "market": "NQ",
        "input_timeframe": "one_minute",
        "permutations": 1000,
        "random_seed": 45,
        "optimization_inside_permutation": False,
        "parallel_deterministic": True,
        "checkpoint_resume": True,
        "p_value_formula": (
            "(1 + permutations_at_least_real) / "
            "(1 + 1000)"
        ),
    },
    "full_gates": {
        "minimum_nq_trade_profit_factor_strict": 1.05,
        "minimum_mnq_trade_profit_factor_strict": 1.00,
        "minimum_nq_net_profit_usd_strict": 0.0,
        "minimum_mnq_net_profit_usd_strict": 0.0,
        "maximum_nq_mcpt_p_value": 0.05,
        "minimum_nq_completed_trades": 500,
        "minimum_profitable_nq_calendar_years": 2,
        "maximum_included_invalid_sessions": 0,
        "maximum_included_roll_switch_sessions": 0,
    },
    "outputs": {
        "decision": (
            "results/EXP-005/full_validation/"
            "full_validation_decision.json"
        ),
        "report": (
            "reports/EXP-005-full-validation/"
            "report.html"
        ),
        "pass_action": "PASS_TO_REVIEW",
        "failure_action": "REJECT",
    },
    "safety": {
        "requires_clean_git": True,
        "verifies_frozen_quick_result": True,
        "verifies_confirmation_import_hashes": True,
        "refuses_existing_decision": True,
        "no_parameter_optimization": True,
        "no_automatic_lifecycle_source_edit": True,
        "does_not_rerun_quick_transfer": True,
    },
}


def get_exp005_full_validation_implementation(
) -> dict[str, Any]:
    return deepcopy(
        EXP005_FULL_VALIDATION_IMPLEMENTATION
    )


def validate_exp005_full_validation_implementation(
    record: dict[str, Any] | None = None,
) -> None:
    current = (
        EXP005_FULL_VALIDATION_IMPLEMENTATION
        if record is None
        else record
    )

    if (
        current.get("experiment_id") != "EXP-005"
        or current.get("record_id") != "EXP-005-I3"
    ):
        raise ValueError(
            "Invalid EXP-005 full-validation "
            "implementation identity."
        )

    if current.get("status") != (
        "IMPLEMENTED_BEFORE_FULL_RESULTS"
    ):
        raise ValueError(
            "EXP-005 full validation must be "
            "implemented before results."
        )

    if (
        current.get(
            "full_validation_results_viewed"
        )
        is not False
        or current.get("quick_transfer_rerun")
        is not False
    ):
        raise ValueError(
            "Full-validation implementation record "
            "cannot contain research results."
        )

    prereg = get_exp005_preregistration()
    strategy = current["locked_strategy"]

    if (
        prereg["optimization"]["enabled"]
        is not False
        or strategy["opening_range_minutes"] != 15
        or strategy["direction_mode"] != "both"
        or strategy["parameter_combinations"] != 1
        or strategy["optimization"] is not False
        or strategy["maximum_trades_per_session"] != 1
        or strategy["overnight_positions"] is not False
    ):
        raise ValueError(
            "EXP-005 full strategy implementation changed."
        )

    statistical = prereg["statistical_plan"]
    mcpt = current["mcpt"]

    if (
        mcpt["permutations"]
        != statistical["full_mcpt_permutations"]
        or mcpt["random_seed"]
        != statistical["random_seed"]
        or mcpt["input_timeframe"] != "one_minute"
        or mcpt["optimization_inside_permutation"]
        is not False
    ):
        raise ValueError(
            "EXP-005 full MCPT implementation changed."
        )

    if current["full_gates"] != (
        prereg["full_validation"]["gates"]
    ):
        raise ValueError(
            "EXP-005 full-validation gates changed."
        )

    import_record = current[
        "confirmation_import"
    ]

    if import_record != {
        "audit": (
            "results/EXP-005/confirmation_data/"
            "quantower_confirmation_import_audit.json"
        ),
        "import_commit": (
            "53a740aedb63e2a7508e3e010f5370be49cf816a"
        ),
        "included_sessions": 733,
        "NQ_1m_rows": 285_870,
        "MNQ_1m_rows": 285_870,
        "NQ_5m_rows": 57_174,
        "MNQ_5m_rows": 57_174,
        "included_invalid_sessions": 0,
        "included_roll_switch_sessions": 0,
    }:
        raise ValueError(
            "EXP-005 confirmation import lock changed."
        )

    costs = current["cost_model"]
    contracts = prereg[
        "contract_and_cost_model"
    ]

    if (
        costs[
            "decision_slippage_ticks_per_side"
        ]
        != 1.0
        or costs[
            "sensitivity_ticks_per_side"
        ]
        != [0.0, 1.0, 2.0]
        or costs["NQ_round_trip_usd"]
        != contracts["NQ"]["round_trip_cost_usd"]
        or costs["MNQ_round_trip_usd"]
        != contracts["MNQ"]["round_trip_cost_usd"]
    ):
        raise ValueError(
            "EXP-005 full-validation cost model changed."
        )

    if not all(current["safety"].values()):
        raise ValueError(
            "Every EXP-005 full-validation safety "
            "control is required."
        )


if __name__ == "__main__":
    validate_exp005_full_validation_implementation()
    print(
        "EXP-005 full-validation implementation is "
        "valid and contains no full results."
    )
