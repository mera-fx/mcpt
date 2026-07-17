from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from exp008_preregistration import (
    validate_exp008_preregistration,
)


EXP008_IMPLEMENTATION: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-008",
    "implementation_status": (
        "IMPLEMENTED_NOT_RUN"
    ),
    "results_viewed": "NONE",
    "optimization_enabled": True,
    "parameter_combinations": 27,
    "grid": {
        "opening_range_minutes": [
            15,
            30,
            45,
        ],
        "reward_to_risk": [
            0.5,
            1.0,
            1.5,
        ],
        "forced_flat_time_new_york": [
            "12:00",
            "14:00",
            "15:55",
        ],
        "direction": "long_only",
        "position_size": (
            "fixed_one_contract"
        ),
        "exp007_baseline_parameter_key": (
            "or30_target1p0_flat1400"
        ),
    },
    "execution_engine": {
        "signal_timeframe_minutes": 5,
        "resolution_minutes": 1,
        "entry": (
            "next_five_minute_open"
        ),
        "stop": "opening_range_low",
        "entry_minute_can_exit": True,
        "same_minute_stop_and_target": (
            "STOP_FIRST_CONSERVATIVE"
        ),
        "target_gap_price_improvement": (
            False
        ),
        "stop_gap_uses_open": True,
        "maximum_trades_per_session": 1,
        "short_entries": False,
    },
    "selection_engine": {
        "market": "NQ",
        "minimum_profit_factor_strict": (
            1.0
        ),
        "minimum_net_profit_usd_strict": (
            0.0
        ),
        "minimum_completed_trades": 100,
        "minimum_profitable_neighbor_fraction": (
            0.5
        ),
        "minimum_neighbor_median_profit_factor_strict": (
            1.0
        ),
        "rank_order": [
            "trade_profit_factor_descending",
            "net_profit_to_drawdown_descending",
            "net_profit_usd_descending",
            "completed_trades_descending",
            "parameter_key_ascending",
        ],
    },
    "analysis": {
        "anchored_walk_forward_folds": 5,
        "final_candidate_years": [
            2021,
            2022,
            2023,
            2024,
            2025,
        ],
        "cost_sensitivity_ticks_per_side": [
            0,
            1,
            2,
        ],
        "bootstrap_resamples": 10000,
        "bootstrap_seed": 4801,
        "mcpt_permutations": 1000,
        "mcpt_seed": 48,
        "all_27_candidates_inside_mcpt": (
            True
        ),
        "selection_inside_mcpt": True,
    },
    "files": [
        "exp008_orb.py",
        "exp008_candidate_scoring.py",
        "exp008_walk_forward.py",
        "exp008_bootstrap.py",
        "exp008_evaluation.py",
        "exp008_selection_mcpt.py",
        "exp008_report.py",
        "run_exp008_optimization.py",
    ],
    "protections": {
        "exp005_changed": False,
        "exp006_changed": False,
        "exp007_changed": False,
        "new_data_cleaning_decisions": 0,
        "live_trading_authorized": False,
        "result_calculated_during_implementation": (
            False
        ),
    },
}


def get_exp008_implementation(
) -> dict[str, Any]:
    return deepcopy(
        EXP008_IMPLEMENTATION
    )


def validate_exp008_implementation(
    record: dict[str, Any] | None = None,
    *,
    require_files: bool = True,
) -> None:
    validate_exp008_preregistration()
    current = (
        EXP008_IMPLEMENTATION
        if record is None
        else record
    )

    if (
        current.get("schema_version")
        != 1
        or current.get("experiment_id")
        != "EXP-008"
        or current.get(
            "implementation_status"
        )
        != "IMPLEMENTED_NOT_RUN"
        or current.get("results_viewed")
        != "NONE"
        or current.get(
            "optimization_enabled"
        )
        is not True
        or current.get(
            "parameter_combinations"
        )
        != 27
    ):
        raise ValueError(
            "EXP-008 implementation "
            "identity changed."
        )

    grid = current["grid"]
    if (
        grid[
            "opening_range_minutes"
        ]
        != [15, 30, 45]
        or grid["reward_to_risk"]
        != [0.5, 1.0, 1.5]
        or grid[
            "forced_flat_time_new_york"
        ]
        != [
            "12:00",
            "14:00",
            "15:55",
        ]
        or grid["direction"]
        != "long_only"
        or grid["position_size"]
        != "fixed_one_contract"
        or grid[
            "exp007_baseline_parameter_key"
        ]
        != "or30_target1p0_flat1400"
    ):
        raise ValueError(
            "EXP-008 implementation grid "
            "changed."
        )

    execution = current[
        "execution_engine"
    ]
    if (
        execution[
            "signal_timeframe_minutes"
        ]
        != 5
        or execution[
            "resolution_minutes"
        ]
        != 1
        or execution["entry"]
        != "next_five_minute_open"
        or execution["stop"]
        != "opening_range_low"
        or execution[
            "entry_minute_can_exit"
        ]
        is not True
        or execution[
            "same_minute_stop_and_target"
        ]
        != "STOP_FIRST_CONSERVATIVE"
        or execution[
            "target_gap_price_improvement"
        ]
        is not False
        or execution[
            "stop_gap_uses_open"
        ]
        is not True
        or execution[
            "maximum_trades_per_session"
        ]
        != 1
        or execution["short_entries"]
        is not False
    ):
        raise ValueError(
            "EXP-008 implementation "
            "execution changed."
        )

    selection = current[
        "selection_engine"
    ]
    if (
        selection["market"] != "NQ"
        or selection[
            "minimum_profit_factor_strict"
        ]
        != 1.0
        or selection[
            "minimum_net_profit_usd_strict"
        ]
        != 0.0
        or selection[
            "minimum_completed_trades"
        ]
        != 100
        or selection[
            "minimum_profitable_neighbor_fraction"
        ]
        != 0.5
        or selection[
            "minimum_neighbor_median_profit_factor_strict"
        ]
        != 1.0
        or selection["rank_order"]
        != [
            "trade_profit_factor_descending",
            "net_profit_to_drawdown_descending",
            "net_profit_usd_descending",
            "completed_trades_descending",
            "parameter_key_ascending",
        ]
    ):
        raise ValueError(
            "EXP-008 implementation "
            "selection changed."
        )

    analysis = current["analysis"]
    if (
        analysis[
            "anchored_walk_forward_folds"
        ]
        != 5
        or analysis[
            "final_candidate_years"
        ]
        != [
            2021,
            2022,
            2023,
            2024,
            2025,
        ]
        or analysis[
            "cost_sensitivity_ticks_per_side"
        ]
        != [0, 1, 2]
        or analysis[
            "bootstrap_resamples"
        ]
        != 10000
        or analysis["bootstrap_seed"]
        != 4801
        or analysis[
            "mcpt_permutations"
        ]
        != 1000
        or analysis["mcpt_seed"]
        != 48
        or analysis[
            "all_27_candidates_inside_mcpt"
        ]
        is not True
        or analysis[
            "selection_inside_mcpt"
        ]
        is not True
    ):
        raise ValueError(
            "EXP-008 implementation "
            "analysis changed."
        )

    protections = current[
        "protections"
    ]
    if (
        protections["exp005_changed"]
        or protections["exp006_changed"]
        or protections["exp007_changed"]
        or protections[
            "live_trading_authorized"
        ]
        or protections[
            "result_calculated_during_implementation"
        ]
        or protections[
            "new_data_cleaning_decisions"
        ]
        != 0
    ):
        raise ValueError(
            "EXP-008 implementation "
            "protections changed."
        )

    if require_files:
        project_root = (
            Path(__file__).resolve().parent
        )
        missing = [
            name
            for name in current["files"]
            if not (
                project_root / name
            ).exists()
        ]
        if missing:
            raise FileNotFoundError(
                "EXP-008 implementation "
                "files are missing: "
                f"{missing}"
            )


if __name__ == "__main__":
    validate_exp008_implementation()
    print(
        "EXP-008 implementation is "
        "valid and contains no result."
    )
