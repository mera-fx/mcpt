from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from exp009_engine import SIGNAL_BUILDERS, locked_exp009_candidates
from exp009_preregistration import validate_exp009_preregistration


EXP009_IMPLEMENTATION: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-009",
    "implementation_status": "IMPLEMENTED_NOT_RUN",
    "results_viewed": "NONE",
    "strategy_family_count": 6,
    "candidate_count": 24,
    "signal_timeframe_minutes": 5,
    "execution_resolution_minutes": 1,
    "forced_flat_time_new_york": "15:55",
    "same_minute_stop_and_target": "STOP_FIRST_CONSERVATIVE",
    "fixed_contracts": {"NQ": 1, "MNQ": 1},
    "nq_cost_sensitivity_ticks_per_side": [0, 1, 2],
    "comparison": {
        "automatic_winner": False,
        "formal_accept_reject_gates": False,
        "single_composite_score": False,
        "pareto_context": True,
        "maximum_later_finalists": 3,
    },
    "deferred": {
        "mcpt": True,
        "bootstrap": True,
        "family_optimization": True,
    },
    "files": [
        "exp009_engine.py",
        "exp009_measurements.py",
        "exp009_report.py",
        "exp009_implementation.py",
        "run_exp009_tournament.py",
    ],
    "protections": {
        "exp005_changed": False,
        "exp006_changed": False,
        "exp007_changed": False,
        "exp008_changed": False,
        "new_data_cleaning_decisions": 0,
        "result_calculated_during_implementation": False,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
    },
}


def get_exp009_implementation() -> dict[str, Any]:
    return deepcopy(EXP009_IMPLEMENTATION)


def validate_exp009_implementation(
    record: dict[str, Any] | None = None,
    *,
    require_files: bool = True,
) -> None:
    validate_exp009_preregistration()
    current = EXP009_IMPLEMENTATION if record is None else record

    if (
        current.get("schema_version") != 1
        or current.get("experiment_id") != "EXP-009"
        or current.get("implementation_status") != "IMPLEMENTED_NOT_RUN"
        or current.get("results_viewed") != "NONE"
        or current.get("strategy_family_count") != 6
        or current.get("candidate_count") != 24
    ):
        raise ValueError("EXP-009 implementation identity changed.")

    if (
        current["signal_timeframe_minutes"] != 5
        or current["execution_resolution_minutes"] != 1
        or current["forced_flat_time_new_york"] != "15:55"
        or current["same_minute_stop_and_target"]
        != "STOP_FIRST_CONSERVATIVE"
        or current["fixed_contracts"] != {"NQ": 1, "MNQ": 1}
        or current["nq_cost_sensitivity_ticks_per_side"] != [0, 1, 2]
    ):
        raise ValueError("EXP-009 shared execution implementation changed.")

    candidates = locked_exp009_candidates()
    if (
        len(candidates) != 24
        or len({item.candidate_id for item in candidates}) != 24
        or len({item.family_id for item in candidates}) != 6
        or set(SIGNAL_BUILDERS)
        != {item.family_id for item in candidates}
    ):
        raise ValueError("EXP-009 candidate engine coverage changed.")

    comparison = current["comparison"]
    if (
        comparison["automatic_winner"] is not False
        or comparison["formal_accept_reject_gates"] is not False
        or comparison["single_composite_score"] is not False
        or comparison["pareto_context"] is not True
        or comparison["maximum_later_finalists"] != 3
    ):
        raise ValueError("EXP-009 review boundary changed.")

    deferred = current["deferred"]
    if (
        deferred["mcpt"] is not True
        or deferred["bootstrap"] is not True
        or deferred["family_optimization"] is not True
    ):
        raise ValueError("EXP-009 expensive-test boundary changed.")

    protections = current["protections"]
    if (
        protections["exp005_changed"] is not False
        or protections["exp006_changed"] is not False
        or protections["exp007_changed"] is not False
        or protections["exp008_changed"] is not False
        or protections["result_calculated_during_implementation"] is not False
        or protections["paper_trading_authorized"] is not False
        or protections["live_trading_authorized"] is not False
    ):
        raise ValueError("EXP-009 protection boundary changed.")

    if require_files:
        project_dir = Path(__file__).resolve().parent
        missing = [
            filename
            for filename in current["files"]
            if not (project_dir / filename).is_file()
        ]
        if missing:
            raise FileNotFoundError(
                "Missing EXP-009 implementation files: "
                + ", ".join(missing)
            )
