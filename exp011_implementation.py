from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from exp011_preregistration import validate_exp011_preregistration


EXP011_IMPLEMENTATION: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-011",
    "implementation_status": "IMPLEMENTED_NOT_RUN",
    "results_viewed": "NONE",
    "signal_candidate_ids": [
        "opening_drive_0p5_time",
        "opening_drive_0p5_1p5r",
    ],
    "sizing_ids": [
        "fixed_one_nq",
        "fractional_nq_equal_risk",
        "integer_mnq_equal_risk",
    ],
    "measurement_row_count": 6,
    "calibration": {
        "market": "NQ",
        "signal_candidate_id": "opening_drive_0p5_time",
        "start": "2019-05-06",
        "end": "2020-12-31",
        "statistic": "MEDIAN_ONE_CONTRACT_INITIAL_RISK",
        "includes_locked_round_trip_cost": True,
        "evaluation_data_excluded": True,
    },
    "evaluation": {
        "start": "2021-01-04",
        "end": "2025-12-31",
        "reference_capital_usd": 100000.0,
        "automatic_winner": False,
        "composite_score": False,
        "pass_fail_gate": False,
    },
    "sizing": {
        "fixed_one_nq_contracts": 1,
        "fractional_nq_cap": 2.0,
        "integer_mnq_rounding": "FLOOR",
        "integer_mnq_min": 0,
        "integer_mnq_cap": 20,
        "zero_contract_action": "SKIP_AND_RECORD",
        "compounding": False,
    },
    "bootstrap": {
        "resamples": 10000,
        "seed": 5111,
        "paired_by_evaluation_session": True,
        "mnq_scale_to_nq": 10.0,
        "decision_gate": False,
    },
    "files": [
        "exp011_sizing.py",
        "exp011_measurements.py",
        "exp011_bootstrap.py",
        "exp011_report.py",
        "exp011_implementation.py",
        "run_exp011_sizing_study.py",
    ],
    "protections": {
        "exp005_changed": False,
        "exp006_changed": False,
        "exp007_changed": False,
        "exp008_changed": False,
        "exp009_changed": False,
        "exp010_changed": False,
        "signal_rules_changed": False,
        "result_calculated_during_implementation": False,
        "new_mcpt": False,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
    },
}


def get_exp011_implementation() -> dict[str, Any]:
    return deepcopy(EXP011_IMPLEMENTATION)


def validate_exp011_implementation(
    record: dict[str, Any] | None = None,
    *,
    require_files: bool = True,
) -> None:
    validate_exp011_preregistration()
    current = EXP011_IMPLEMENTATION if record is None else record
    if (
        current.get("schema_version") != 1
        or current.get("experiment_id") != "EXP-011"
        or current.get("implementation_status") != "IMPLEMENTED_NOT_RUN"
        or current.get("results_viewed") != "NONE"
        or current.get("signal_candidate_ids")
        != [
            "opening_drive_0p5_time",
            "opening_drive_0p5_1p5r",
        ]
        or current.get("sizing_ids")
        != [
            "fixed_one_nq",
            "fractional_nq_equal_risk",
            "integer_mnq_equal_risk",
        ]
        or current.get("measurement_row_count") != 6
    ):
        raise ValueError("EXP-011 implementation identity changed.")

    calibration = current["calibration"]
    if (
        calibration["market"] != "NQ"
        or calibration["signal_candidate_id"]
        != "opening_drive_0p5_time"
        or calibration["start"] != "2019-05-06"
        or calibration["end"] != "2020-12-31"
        or calibration["statistic"]
        != "MEDIAN_ONE_CONTRACT_INITIAL_RISK"
        or calibration["includes_locked_round_trip_cost"] is not True
        or calibration["evaluation_data_excluded"] is not True
    ):
        raise ValueError("EXP-011 calibration implementation changed.")

    evaluation = current["evaluation"]
    if (
        evaluation["start"] != "2021-01-04"
        or evaluation["end"] != "2025-12-31"
        or evaluation["reference_capital_usd"] != 100000.0
        or evaluation["automatic_winner"] is not False
        or evaluation["composite_score"] is not False
        or evaluation["pass_fail_gate"] is not False
    ):
        raise ValueError("EXP-011 evaluation implementation changed.")

    sizing = current["sizing"]
    if (
        sizing["fixed_one_nq_contracts"] != 1
        or sizing["fractional_nq_cap"] != 2.0
        or sizing["integer_mnq_rounding"] != "FLOOR"
        or sizing["integer_mnq_min"] != 0
        or sizing["integer_mnq_cap"] != 20
        or sizing["zero_contract_action"] != "SKIP_AND_RECORD"
        or sizing["compounding"] is not False
    ):
        raise ValueError("EXP-011 sizing implementation changed.")

    bootstrap = current["bootstrap"]
    if (
        bootstrap["resamples"] != 10000
        or bootstrap["seed"] != 5111
        or bootstrap["paired_by_evaluation_session"] is not True
        or bootstrap["mnq_scale_to_nq"] != 10.0
        or bootstrap["decision_gate"] is not False
    ):
        raise ValueError("EXP-011 bootstrap implementation changed.")

    protections = current["protections"]
    if any(
        protections[key]
        for key in (
            "exp005_changed",
            "exp006_changed",
            "exp007_changed",
            "exp008_changed",
            "exp009_changed",
            "exp010_changed",
            "signal_rules_changed",
            "result_calculated_during_implementation",
            "new_mcpt",
            "paper_trading_authorized",
            "live_trading_authorized",
        )
    ):
        raise ValueError("EXP-011 protection boundary changed.")

    if require_files:
        project_dir = Path(__file__).resolve().parent
        missing = [
            filename
            for filename in current["files"]
            if not (project_dir / filename).is_file()
        ]
        if missing:
            raise FileNotFoundError(
                "Missing EXP-011 implementation files: "
                + ", ".join(missing)
            )


if __name__ == "__main__":
    validate_exp011_implementation()
    print("EXP-011 implementation is valid and contains no result.")
