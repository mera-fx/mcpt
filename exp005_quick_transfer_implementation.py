from __future__ import annotations

from copy import deepcopy
from typing import Any

from exp005_preregistration import (
    get_exp005_preregistration,
)


EXP005_QUICK_TRANSFER_IMPLEMENTATION: dict[
    str,
    Any,
] = {
    "schema_version": 1,
    "experiment_id": "EXP-005",
    "record_id": "EXP-005-I2",
    "implemented_date": "2026-07-13",
    "status": "IMPLEMENTED_BEFORE_RESULTS",
    "results_viewed": False,
    "confirmation_period_accessed": False,
    "runner": (
        "run_exp005_quick_transfer.py"
    ),
    "engine": "exp005_futures_orb.py",
    "mcpt_engine": "exp005_session_mcpt.py",
    "evaluation": (
        "exp005_quick_transfer.py"
    ),
    "document": (
        "research/"
        "EXP-005_quick_transfer_implementation.md"
    ),
    "data_inputs": {
        "NQ_1m": (
            "data/EXP-005/processed/"
            "NQ_1m_quick.parquet"
        ),
        "MNQ_1m": (
            "data/EXP-005/processed/"
            "MNQ_1m_quick.parquet"
        ),
        "NQ_5m": (
            "data/EXP-005/processed/"
            "NQ_5m_quick.parquet"
        ),
        "MNQ_5m": (
            "data/EXP-005/processed/"
            "MNQ_5m_quick.parquet"
        ),
        "import_audit": (
            "results/EXP-005/data/"
            "quantower_import_audit.json"
        ),
    },
    "locked_strategy": {
        "opening_range_minutes": 15,
        "direction_mode": "both",
        "entry": "next_five_minute_open",
        "final_signal_bar": "11:55 America/New_York",
        "final_entry": "12:00 America/New_York",
        "long_stop": "opening_range_low",
        "short_stop": "opening_range_high",
        "same_entry_bar_stop": True,
        "maximum_trades_per_session": 1,
        "same_day_reversal": False,
        "forced_flat": "15:55 America/New_York open",
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
        "permutations": 25,
        "random_seed": 45,
        "optimization_inside_permutation": False,
        "parallel_deterministic": True,
        "checkpoint_resume": True,
        "p_value_formula": (
            "(1 + permutations_at_least_real) / "
            "(1 + 25)"
        ),
    },
    "outputs": {
        "decision": (
            "results/EXP-005/quick_transfer/"
            "quick_transfer_decision.json"
        ),
        "report": (
            "reports/EXP-005-quick-transfer/"
            "report.html"
        ),
    },
    "safety": {
        "requires_clean_git": True,
        "verifies_frozen_import_hashes": True,
        "refuses_existing_decision": True,
        "confirmation_period_blocked": True,
        "no_parameter_optimization": True,
        "no_automatic_lifecycle_source_edit": True,
    },
}


def get_exp005_quick_transfer_implementation(
) -> dict[str, Any]:
    return deepcopy(
        EXP005_QUICK_TRANSFER_IMPLEMENTATION
    )


def validate_exp005_quick_transfer_implementation(
    record: dict[str, Any] | None = None,
) -> None:
    current = (
        EXP005_QUICK_TRANSFER_IMPLEMENTATION
        if record is None
        else record
    )

    if (
        current.get("experiment_id")
        != "EXP-005"
        or current.get("record_id")
        != "EXP-005-I2"
    ):
        raise ValueError(
            "Invalid EXP-005 quick-transfer "
            "implementation identity."
        )

    if current.get(
        "status"
    ) != "IMPLEMENTED_BEFORE_RESULTS":
        raise ValueError(
            "EXP-005 quick transfer must be "
            "implemented before results."
        )

    if (
        current.get("results_viewed")
        is not False
        or current.get(
            "confirmation_period_accessed"
        )
        is not False
    ):
        raise ValueError(
            "Implementation record cannot "
            "contain research results."
        )

    prereg = (
        get_exp005_preregistration()
    )
    fixed = prereg[
        "optimization"
    ]["fixed_parameters"]

    if fixed != {
        "opening_range_minutes": 15,
        "direction_mode": "both",
    }:
        raise ValueError(
            "EXP-005 fixed parameters changed."
        )

    strategy = current[
        "locked_strategy"
    ]

    if (
        strategy["opening_range_minutes"]
        != 15
        or strategy["direction_mode"]
        != "both"
        or strategy[
            "maximum_trades_per_session"
        ]
        != 1
        or strategy[
            "overnight_positions"
        ]
        is not False
    ):
        raise ValueError(
            "EXP-005 implementation strategy changed."
        )

    statistical = prereg[
        "statistical_plan"
    ]
    mcpt = current["mcpt"]

    if (
        mcpt["permutations"]
        != statistical[
            "quick_mcpt_permutations"
        ]
        or mcpt["random_seed"]
        != statistical["random_seed"]
        or mcpt[
            "optimization_inside_permutation"
        ]
        is not False
        or mcpt["input_timeframe"]
        != "one_minute"
    ):
        raise ValueError(
            "EXP-005 quick MCPT implementation changed."
        )

    costs = current["cost_model"]

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
        != prereg[
            "contract_and_cost_model"
        ]["NQ"]["round_trip_cost_usd"]
        or costs["MNQ_round_trip_usd"]
        != prereg[
            "contract_and_cost_model"
        ]["MNQ"]["round_trip_cost_usd"]
    ):
        raise ValueError(
            "EXP-005 cost implementation changed."
        )

    safety = current["safety"]

    if not all(
        safety.values()
    ):
        raise ValueError(
            "Every EXP-005 quick-transfer "
            "safety control is required."
        )


if __name__ == "__main__":
    validate_exp005_quick_transfer_implementation()

    print(
        "EXP-005 quick-transfer implementation "
        "is valid and contains no results."
    )
