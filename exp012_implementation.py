from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from exp012_engine import SIGNAL_BUILDERS, locked_exp012_candidates
from exp012_preregistration import validate_exp012_preregistration


EXP012_IMPLEMENTATION: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-012",
    "implementation_status": "IMPLEMENTED_NOT_RUN",
    "results_viewed": "NONE",
    "strategy_family_count": 6,
    "candidate_count": 24,
    "sample_years": [2020, 2021, 2022, 2023, 2024, 2025],
    "expected_sessions": 1331,
    "context_windows": {
        "overnight": "18:00-09:30",
        "premarket": "08:00-09:30",
        "cash": "09:30-16:00",
    },
    "entries_during_cash_session_only": True,
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
        "walk_forward": True,
        "family_optimization": True,
    },
    "files": [
        "exp012_engine.py",
        "exp012_measurements.py",
        "exp012_report.py",
        "exp012_implementation.py",
        "run_exp012_tournament.py",
    ],
    "protections": {
        "frozen_extended_session_data_changed": False,
        "prior_experiments_changed": False,
        "overnight_execution_claimed": False,
        "result_calculated_during_implementation": False,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
    },
}


def get_exp012_implementation() -> dict[str, Any]:
    return deepcopy(EXP012_IMPLEMENTATION)


def validate_exp012_implementation(
    record: dict[str, Any] | None = None,
    *,
    require_files: bool = True,
) -> None:
    validate_exp012_preregistration()
    current = EXP012_IMPLEMENTATION if record is None else record
    if (
        current.get("schema_version") != 1
        or current.get("experiment_id") != "EXP-012"
        or current.get("implementation_status") != "IMPLEMENTED_NOT_RUN"
        or current.get("results_viewed") != "NONE"
        or current.get("strategy_family_count") != 6
        or current.get("candidate_count") != 24
        or current.get("expected_sessions") != 1331
    ):
        raise ValueError("EXP-012 implementation identity changed.")

    if (
        current["sample_years"] != [2020, 2021, 2022, 2023, 2024, 2025]
        or current["entries_during_cash_session_only"] is not True
        or current["signal_timeframe_minutes"] != 5
        or current["execution_resolution_minutes"] != 1
        or current["forced_flat_time_new_york"] != "15:55"
        or current["same_minute_stop_and_target"]
        != "STOP_FIRST_CONSERVATIVE"
        or current["fixed_contracts"] != {"NQ": 1, "MNQ": 1}
        or current["nq_cost_sensitivity_ticks_per_side"] != [0, 1, 2]
    ):
        raise ValueError("EXP-012 execution implementation changed.")

    candidates = locked_exp012_candidates()
    if (
        len(candidates) != 24
        or len({candidate.candidate_id for candidate in candidates}) != 24
        or len({candidate.family_id for candidate in candidates}) != 6
        or set(SIGNAL_BUILDERS)
        != {candidate.family_id for candidate in candidates}
    ):
        raise ValueError("EXP-012 candidate engine coverage changed.")

    comparison = current["comparison"]
    if (
        comparison["automatic_winner"] is not False
        or comparison["formal_accept_reject_gates"] is not False
        or comparison["single_composite_score"] is not False
        or comparison["pareto_context"] is not True
        or comparison["maximum_later_finalists"] != 3
    ):
        raise ValueError("EXP-012 review boundary changed.")

    if not all(current["deferred"].values()):
        raise ValueError("EXP-012 expensive-test boundary changed.")

    protections = current["protections"]
    if (
        protections["frozen_extended_session_data_changed"] is not False
        or protections["prior_experiments_changed"] is not False
        or protections["overnight_execution_claimed"] is not False
        or protections["result_calculated_during_implementation"] is not False
        or protections["paper_trading_authorized"] is not False
        or protections["live_trading_authorized"] is not False
    ):
        raise ValueError("EXP-012 protection boundary changed.")

    if require_files:
        project_dir = Path(__file__).resolve().parent
        missing = [
            filename
            for filename in current["files"]
            if not (project_dir / filename).is_file()
        ]
        if missing:
            raise FileNotFoundError(
                "Missing EXP-012 implementation files: "
                + ", ".join(missing)
            )
