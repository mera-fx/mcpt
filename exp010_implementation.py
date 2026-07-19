from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from exp010_preregistration import validate_exp010_preregistration
from exp010_selection import (
    OPENING_DRIVE_IDS,
    locked_opening_drive_candidates,
)


EXP010_IMPLEMENTATION: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-010",
    "implementation_status": "IMPLEMENTED_NOT_RUN",
    "results_viewed": "NONE",
    "family_id": "opening_drive_continuation",
    "candidate_ids": list(OPENING_DRIVE_IDS),
    "candidate_count": 4,
    "user_reference_candidate": "opening_drive_0p5_1p5r",
    "execution": {
        "signal_timeframe_minutes": 5,
        "resolution_minutes": 1,
        "entry_time_new_york": "10:00",
        "forced_flat_time_new_york": "15:55",
        "same_minute_stop_and_target": "STOP_FIRST_CONSERVATIVE",
        "fixed_contracts": {"NQ": 1, "MNQ": 1},
        "nq_cost_sensitivity_ticks_per_side": [0, 1, 2],
    },
    "selection": {
        "minimum_completed_trades": 100,
        "minimum_profit_factor_strict": 1.0,
        "minimum_net_profit_usd_strict": 0.0,
        "rank_order": [
            "trade_profit_factor_descending",
            "net_profit_to_drawdown_descending",
            "net_profit_usd_descending",
            "completed_trades_descending",
            "candidate_id_ascending",
        ],
        "automatic_trading_winner": False,
    },
    "analysis": {
        "anchored_walk_forward_folds": 5,
        "bootstrap_resamples": 10000,
        "bootstrap_seed": 5001,
        "mcpt_permutations": 1000,
        "mcpt_seed": 50,
        "all_four_candidates_inside_mcpt": True,
        "selection_inside_mcpt": True,
        "fixed_reference_mcpt_diagnostic": True,
        "prior_six_family_selection_corrected": False,
    },
    "files": [
        "exp010_selection.py",
        "exp010_walk_forward.py",
        "exp010_bootstrap.py",
        "exp010_evaluation.py",
        "exp010_selection_mcpt.py",
        "exp010_report.py",
        "exp010_implementation.py",
        "run_exp010_validation.py",
    ],
    "protections": {
        "exp005_changed": False,
        "exp006_changed": False,
        "exp007_changed": False,
        "exp008_changed": False,
        "exp009_changed": False,
        "new_data_cleaning_decisions": 0,
        "result_calculated_during_implementation": False,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
    },
}


def get_exp010_implementation() -> dict[str, Any]:
    return deepcopy(EXP010_IMPLEMENTATION)


def validate_exp010_implementation(
    record: dict[str, Any] | None = None,
    *,
    require_files: bool = True,
) -> None:
    validate_exp010_preregistration()
    current = EXP010_IMPLEMENTATION if record is None else record
    if (
        current.get("schema_version") != 1
        or current.get("experiment_id") != "EXP-010"
        or current.get("implementation_status") != "IMPLEMENTED_NOT_RUN"
        or current.get("results_viewed") != "NONE"
        or current.get("family_id") != "opening_drive_continuation"
        or current.get("candidate_count") != 4
        or current.get("candidate_ids") != list(OPENING_DRIVE_IDS)
        or current.get("user_reference_candidate")
        != "opening_drive_0p5_1p5r"
    ):
        raise ValueError("EXP-010 implementation identity changed.")
    if len(locked_opening_drive_candidates()) != 4:
        raise ValueError("EXP-010 candidate engine coverage changed.")

    execution = current["execution"]
    if (
        execution["signal_timeframe_minutes"] != 5
        or execution["resolution_minutes"] != 1
        or execution["entry_time_new_york"] != "10:00"
        or execution["forced_flat_time_new_york"] != "15:55"
        or execution["same_minute_stop_and_target"]
        != "STOP_FIRST_CONSERVATIVE"
        or execution["fixed_contracts"] != {"NQ": 1, "MNQ": 1}
        or execution["nq_cost_sensitivity_ticks_per_side"] != [0, 1, 2]
    ):
        raise ValueError("EXP-010 execution implementation changed.")

    selection = current["selection"]
    if (
        selection["minimum_completed_trades"] != 100
        or selection["minimum_profit_factor_strict"] != 1.0
        or selection["minimum_net_profit_usd_strict"] != 0.0
        or len(selection["rank_order"]) != 5
        or selection["automatic_trading_winner"] is not False
    ):
        raise ValueError("EXP-010 selection implementation changed.")

    analysis = current["analysis"]
    if (
        analysis["anchored_walk_forward_folds"] != 5
        or analysis["bootstrap_resamples"] != 10000
        or analysis["bootstrap_seed"] != 5001
        or analysis["mcpt_permutations"] != 1000
        or analysis["mcpt_seed"] != 50
        or analysis["all_four_candidates_inside_mcpt"] is not True
        or analysis["selection_inside_mcpt"] is not True
        or analysis["fixed_reference_mcpt_diagnostic"] is not True
        or analysis["prior_six_family_selection_corrected"] is not False
    ):
        raise ValueError("EXP-010 analysis implementation changed.")

    protections = current["protections"]
    if (
        protections["exp005_changed"]
        or protections["exp006_changed"]
        or protections["exp007_changed"]
        or protections["exp008_changed"]
        or protections["exp009_changed"]
        or protections["new_data_cleaning_decisions"] != 0
        or protections["result_calculated_during_implementation"]
        or protections["paper_trading_authorized"]
        or protections["live_trading_authorized"]
    ):
        raise ValueError("EXP-010 protection boundary changed.")

    if require_files:
        project_dir = Path(__file__).resolve().parent
        missing = [
            filename
            for filename in current["files"]
            if not (project_dir / filename).is_file()
        ]
        if missing:
            raise FileNotFoundError(
                "Missing EXP-010 implementation files: "
                + ", ".join(missing)
            )


if __name__ == "__main__":
    validate_exp010_implementation()
    print("EXP-010 implementation is valid and contains no result.")
