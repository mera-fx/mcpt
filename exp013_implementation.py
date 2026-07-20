from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from exp012_engine import locked_exp012_candidates
from exp013_preregistration import validate_exp013_preregistration
from exp013_selection import FINALIST_IDS, locked_exp013_candidates
from exp013_selection_mcpt import (
    ENGINE_VERSION,
    LOCKED_BASE_SEED,
    LOCKED_PERMUTATIONS,
)


EXP013_IMPLEMENTATION: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-013",
    "implementation_status": "IMPLEMENTED_NOT_RUN",
    "results_viewed": "NONE",
    "finalist_ids": list(FINALIST_IDS),
    "source_candidate_count_inside_primary_mcpt": 24,
    "anchored_walk_forward_test_years": [2022, 2023, 2024, 2025],
    "bootstrap_resamples": 10000,
    "bootstrap_seed": 5301,
    "mcpt_permutations": LOCKED_PERMUTATIONS,
    "mcpt_seed": LOCKED_BASE_SEED,
    "mcpt_engine_version": ENGINE_VERSION,
    "mcpt_exact_extended_slots": 1320,
    "files": [
        "exp013_selection.py",
        "exp013_walk_forward.py",
        "exp013_bootstrap.py",
        "exp013_evaluation.py",
        "exp013_selection_mcpt.py",
        "exp013_report.py",
        "exp013_implementation.py",
        "run_exp013_validation.py",
        "research/EXP-013_implementation.md",
    ],
    "protections": {
        "exp012_result_changed": False,
        "candidate_rules_changed": False,
        "new_data_cleaning_decisions": 0,
        "result_calculated_during_implementation": False,
        "automatic_trading_winner": False,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
    },
}


def get_exp013_implementation() -> dict[str, Any]:
    return deepcopy(EXP013_IMPLEMENTATION)


def validate_exp013_implementation(
    record: dict[str, Any] | None = None,
    *,
    require_files: bool = True,
) -> None:
    validate_exp013_preregistration()
    current = EXP013_IMPLEMENTATION if record is None else record
    if (
        current.get("schema_version") != 1
        or current.get("experiment_id") != "EXP-013"
        or current.get("implementation_status") != "IMPLEMENTED_NOT_RUN"
        or current.get("results_viewed") != "NONE"
        or current.get("finalist_ids") != list(FINALIST_IDS)
        or current.get("source_candidate_count_inside_primary_mcpt") != 24
    ):
        raise ValueError("EXP-013 implementation identity changed.")
    if (
        len(locked_exp013_candidates()) != 3
        or len(locked_exp012_candidates()) != 24
        or current["anchored_walk_forward_test_years"]
        != [2022, 2023, 2024, 2025]
        or current["bootstrap_resamples"] != 10000
        or current["bootstrap_seed"] != 5301
        or current["mcpt_permutations"] != 1000
        or current["mcpt_seed"] != 53
        or current["mcpt_exact_extended_slots"] != 1320
    ):
        raise ValueError("EXP-013 protected analysis lock changed.")
    if any(
        (
            current["protections"]["exp012_result_changed"],
            current["protections"]["candidate_rules_changed"],
            current["protections"]["result_calculated_during_implementation"],
            current["protections"]["automatic_trading_winner"],
            current["protections"]["paper_trading_authorized"],
            current["protections"]["live_trading_authorized"],
        )
    ) or current["protections"]["new_data_cleaning_decisions"] != 0:
        raise ValueError("EXP-013 protection boundary changed.")
    if require_files:
        root = Path(__file__).resolve().parent
        missing = [
            value for value in current["files"] if not (root / value).is_file()
        ]
        if missing:
            raise FileNotFoundError(
                "Missing EXP-013 implementation files: "
                + ", ".join(missing)
            )
