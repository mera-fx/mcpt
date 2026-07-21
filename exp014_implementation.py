from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from exp014_preregistration import validate_exp014_preregistration


EXP014_IMPLEMENTATION: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-014",
    "implementation_status": "IMPLEMENTED_NOT_RUN",
    "results_viewed": "NONE",
    "files": [
        "exp014_measurements.py",
        "exp014_report.py",
        "exp014_implementation.py",
        "run_exp014_study.py",
        "research/EXP-014_implementation.md",
        "tests/exp014_test_data.py",
        "tests/test_exp014_implementation.py",
        "tests/test_exp014_measurements.py",
        "tests/test_exp014_report.py",
        "tests/test_exp014_runner_boundary.py",
    ],
    "outputs": [
        "study_result.json",
        "standalone_measurements.csv",
        "behaviour_breakdowns.csv",
        "period_comparison.csv",
        "monthly_measurements.csv",
        "rolling_measurements.csv",
        "drawdown_diagnostics.csv",
        "concentration_measurements.csv",
        "overlap_measurements.csv",
        "sleeve_pair_measurements.csv",
        "session_pnl.csv",
        "pair_session_pnl.csv",
        "regime_context.csv",
    ],
    "diagnostic_definitions": {
        "rolling_trade_windows": [20, 50],
        "monthly_axis_includes_zero_trade_months": True,
        "drawdown_axis": "all_1331_included_sessions",
        "mfe_mae_uses_pre_exit_minutes_plus_actual_exit_fill": True,
        "correlation_uses_zero_on_no_trade_sessions": True,
    },
    "protections": {
        "exp013_result_changed": False,
        "strategy_rules_changed": False,
        "parameter_search_enabled": False,
        "weight_search_enabled": False,
        "regime_filter_enabled": False,
        "mcpt_rerun_enabled": False,
        "bootstrap_rerun_enabled": False,
        "walk_forward_rerun_enabled": False,
        "automatic_winner": False,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
    },
}


def get_exp014_implementation() -> dict[str, Any]:
    return deepcopy(EXP014_IMPLEMENTATION)


def validate_exp014_implementation(
    record: dict[str, Any] | None = None,
    *,
    require_files: bool = True,
) -> None:
    validate_exp014_preregistration()
    current = EXP014_IMPLEMENTATION if record is None else record
    if (
        current.get("schema_version") != 1
        or current.get("experiment_id") != "EXP-014"
        or current.get("implementation_status") != "IMPLEMENTED_NOT_RUN"
        or current.get("results_viewed") != "NONE"
        or len(current.get("outputs", [])) != 13
    ):
        raise ValueError("EXP-014 implementation identity changed.")

    diagnostics = current["diagnostic_definitions"]
    if (
        diagnostics["rolling_trade_windows"] != [20, 50]
        or diagnostics["monthly_axis_includes_zero_trade_months"] is not True
        or diagnostics["drawdown_axis"] != "all_1331_included_sessions"
        or diagnostics[
            "mfe_mae_uses_pre_exit_minutes_plus_actual_exit_fill"
        ]
        is not True
        or diagnostics["correlation_uses_zero_on_no_trade_sessions"]
        is not True
    ):
        raise ValueError("EXP-014 diagnostic definitions changed.")

    protections = current["protections"]
    if any(protections.values()):
        raise ValueError("EXP-014 protection boundary changed.")

    if require_files:
        root = Path(__file__).resolve().parent
        missing = [
            value for value in current["files"] if not (root / value).is_file()
        ]
        if missing:
            raise FileNotFoundError(
                "Missing EXP-014 implementation files: "
                + ", ".join(missing)
            )


if __name__ == "__main__":
    validate_exp014_implementation()
    print("EXP-014 implementation is valid and result-free.")
