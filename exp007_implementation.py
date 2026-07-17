from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from exp007_preregistration import validate_exp007_preregistration


EXP007_IMPLEMENTATION: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-007",
    "implementation_status": "IMPLEMENTED_NOT_RUN",
    "results_viewed": "NONE",
    "strategy_key": "or30_long_1r_flat1400",
    "optimization_enabled": False,
    "parameter_combinations": 1,
    "signal_engine": {
        "opening_range_minutes": 30,
        "direction": "long_only",
        "signal_timeframe_minutes": 5,
        "entry": "next_five_minute_open",
        "stop": "opening_range_low",
        "target_r_multiple": 1.0,
        "forced_flat_time_new_york": "14:00",
    },
    "execution_engine": {
        "resolution_minutes": 1,
        "entry_minute_can_exit": True,
        "same_minute_stop_and_target": "STOP_FIRST_CONSERVATIVE",
        "target_gap_price_improvement": False,
        "stop_gap_uses_open": True,
    },
    "analysis": {
        "annual_blocks": [2021, 2022, 2023, 2024, 2025],
        "cost_sensitivity_ticks_per_side": [0, 1, 2],
        "bootstrap_resamples": 10000,
        "bootstrap_seed": 4701,
        "mcpt_permutations": 1000,
        "mcpt_seed": 47,
        "optimization_inside_mcpt": False,
    },
    "files": [
        "exp007_orb.py",
        "exp007_bootstrap.py",
        "exp007_evaluation.py",
        "exp007_mcpt.py",
        "exp007_report.py",
        "run_exp007_replication.py",
    ],
    "protections": {
        "exp005_changed": False,
        "exp006_changed": False,
        "new_data_cleaning_decisions": 0,
        "live_trading_authorized": False,
        "result_calculated_during_implementation": False,
    },
}


def get_exp007_implementation() -> dict[str, Any]:
    return deepcopy(EXP007_IMPLEMENTATION)


def validate_exp007_implementation(
    record: dict[str, Any] | None = None,
    *,
    require_files: bool = True,
) -> None:
    validate_exp007_preregistration()
    current = EXP007_IMPLEMENTATION if record is None else record

    if (
        current.get("schema_version") != 1
        or current.get("experiment_id") != "EXP-007"
        or current.get("implementation_status") != "IMPLEMENTED_NOT_RUN"
        or current.get("results_viewed") != "NONE"
        or current.get("strategy_key") != "or30_long_1r_flat1400"
        or current.get("optimization_enabled") is not False
        or current.get("parameter_combinations") != 1
    ):
        raise ValueError("EXP-007 implementation identity changed.")

    signal = current["signal_engine"]
    if (
        signal["opening_range_minutes"] != 30
        or signal["direction"] != "long_only"
        or signal["entry"] != "next_five_minute_open"
        or signal["target_r_multiple"] != 1.0
        or signal["forced_flat_time_new_york"] != "14:00"
    ):
        raise ValueError("EXP-007 implementation signal changed.")

    execution = current["execution_engine"]
    if (
        execution["resolution_minutes"] != 1
        or execution["entry_minute_can_exit"] is not True
        or execution["same_minute_stop_and_target"]
        != "STOP_FIRST_CONSERVATIVE"
        or execution["target_gap_price_improvement"] is not False
        or execution["stop_gap_uses_open"] is not True
    ):
        raise ValueError("EXP-007 implementation execution changed.")

    analysis = current["analysis"]
    if (
        analysis["annual_blocks"] != [2021, 2022, 2023, 2024, 2025]
        or analysis["cost_sensitivity_ticks_per_side"] != [0, 1, 2]
        or analysis["bootstrap_resamples"] != 10000
        or analysis["bootstrap_seed"] != 4701
        or analysis["mcpt_permutations"] != 1000
        or analysis["mcpt_seed"] != 47
        or analysis["optimization_inside_mcpt"] is not False
    ):
        raise ValueError("EXP-007 implementation analysis changed.")

    protections = current["protections"]
    if any(
        [
            protections["exp005_changed"],
            protections["exp006_changed"],
            protections["live_trading_authorized"],
            protections["result_calculated_during_implementation"],
        ]
    ) or protections["new_data_cleaning_decisions"] != 0:
        raise ValueError("EXP-007 implementation protections changed.")

    if require_files:
        root = Path(__file__).resolve().parent
        missing = [name for name in current["files"] if not (root / name).exists()]
        if missing:
            raise FileNotFoundError(
                f"EXP-007 implementation files are missing: {missing}"
            )


if __name__ == "__main__":
    validate_exp007_implementation()
    print("EXP-007 implementation is valid and contains no result.")
