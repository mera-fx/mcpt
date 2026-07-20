from __future__ import annotations

from pathlib import Path

from exp012_preregistration import (
    get_exp012_preregistration,
    validate_exp012_preregistration,
)
from experiment_lifecycle import get_experiment_lifecycle
from extended_session_data_result import (
    EXPECTED_YEAR_COUNTS,
    verify_extended_session_data_result,
)


PROJECT_DIR = Path(__file__).resolve().parent
RESULT_ROOT = PROJECT_DIR / "results" / "EXP-012"


def main() -> None:
    validate_exp012_preregistration()
    data_result = verify_extended_session_data_result()

    expected_stages = {
        "EXP-005": "ACCEPTED_FOR_PAPER_TESTING",
        "EXP-006": "REJECTED",
        "EXP-007": "REJECTED",
        "EXP-008": "REJECTED",
        "EXP-009": "REVIEW",
        "EXP-010": "REVIEW",
        "EXP-011": "REVIEW",
        "EXP-012": "PRE_REGISTERED",
    }
    for experiment_id, expected_stage in expected_stages.items():
        actual = get_experiment_lifecycle(experiment_id).stage
        if actual != expected_stage:
            raise RuntimeError(
                f"{experiment_id} must be {expected_stage}; found {actual}."
            )

    if RESULT_ROOT.exists() and any(
        path.is_file() for path in RESULT_ROOT.rglob("*")
    ):
        raise RuntimeError("EXP-012 result files already exist.")

    record = get_exp012_preregistration()
    data = record["market_and_data"]
    budget = record["candidate_budget"]
    included_sessions = sum(
        EXPECTED_YEAR_COUNTS[year]["complete_aligned"]
        for year in data["included_years"]
    )
    if included_sessions != data["expected_complete_aligned_sessions"]:
        raise RuntimeError("EXP-012 included-session count changed.")

    print()
    print("EXP-012 EXTENDED-HOURS CONTEXT PREFLIGHT")
    print("========================================")
    print("Lifecycle: PRE_REGISTERED")
    print("Purpose: measurement-first discovery")
    print(
        "Frozen extended-session foundation: "
        f"{data_result['complete_aligned_sessions']:,} aligned sessions"
    )
    print(
        "EXP-012 sample: "
        f"{included_sessions:,} aligned 2020-2025 sessions"
    )
    print(f"Strategy families: {budget['family_count']}")
    print(f"Locked candidates: {budget['total_candidates']}")
    print("Extended context: overnight, premarket and opening gap")
    print("Entries: cash session only")
    print("Position sizing: fixed one contract")
    print("Automatic winner: False")
    print("Formal pass/fail gates: False")
    print("MCPT/bootstrap/walk-forward: deferred")
    print("Paper trading authorized: False")
    print("Live trading authorized: False")
    print("EXP-012 results calculated: False")
    print("========================================")
    print("Preflight passed. No EXP-012 strategy result was calculated.")


if __name__ == "__main__":
    main()
