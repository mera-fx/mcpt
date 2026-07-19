from __future__ import annotations

from pathlib import Path

from exp006_optimization_result import (
    verify_local_exp006_optimization_decision,
)
from exp007_replication_result import (
    verify_local_exp007_replication_decision,
)
from exp008_optimization_result import (
    verify_local_exp008_optimization_decision,
)
from exp009_preregistration import (
    get_exp009_preregistration,
    validate_exp009_preregistration,
)
from experiment_lifecycle import get_experiment_lifecycle


PROJECT_DIR = Path(__file__).resolve().parent
RESULT_ROOT = PROJECT_DIR / "results" / "EXP-009"


def main() -> None:
    validate_exp009_preregistration()

    expected_stages = {
        "EXP-005": "ACCEPTED_FOR_PAPER_TESTING",
        "EXP-006": "REJECTED",
        "EXP-007": "REJECTED",
        "EXP-008": "REJECTED",
        "EXP-009": "PRE_REGISTERED",
    }
    for experiment_id, expected_stage in expected_stages.items():
        actual = get_experiment_lifecycle(experiment_id).stage
        if actual != expected_stage:
            raise RuntimeError(
                f"{experiment_id} must be {expected_stage}; found {actual}."
            )

    verify_local_exp006_optimization_decision()
    verify_local_exp007_replication_decision()
    verify_local_exp008_optimization_decision()

    if RESULT_ROOT.exists():
        result_files = [
            path
            for path in RESULT_ROOT.rglob("*")
            if path.is_file()
        ]
        if result_files:
            raise RuntimeError("EXP-009 result files already exist.")

    prereg = get_exp009_preregistration()
    budget = prereg["candidate_budget"]
    review = prereg["comparison_and_review"]
    deferred = prereg["deferred_expensive_tests"]

    print()
    print("EXP-009 DISCOVERY PREFLIGHT")
    print("===========================")
    print("Lifecycle: PRE_REGISTERED")
    print("Purpose: measurement and comparison, not pass/fail")
    print(f"Strategy families: {budget['family_count']}")
    print(f"Candidates per family: {budget['candidates_per_family']}")
    print(f"Total candidates: {budget['total_candidates']}")
    print("Overnight gap families included: False")
    print("Primary market: NQ")
    print("Secondary implementation market: MNQ")
    print("Position size: fixed one contract")
    print("One-minute chronological execution: True")
    print("NQ cost sensitivity: 0, 1 and 2 ticks per side")
    print(f"Automatic winner: {review['automatic_strategy_winner']}")
    print(f"Formal pass/fail gates: {review['formal_accept_reject_gates']}")
    print(f"Maximum later finalists: {review['finalist_count_maximum']}")
    print(f"MCPT run in EXP-009: {deferred['mcpt_run_in_exp009']}")
    print(f"Bootstrap run in EXP-009: {deferred['bootstrap_run_in_exp009']}")
    print("EXP-005/006/007/008 changed: False")
    print("EXP-009 results calculated: False")
    print("===========================")
    print("Preflight passed. No strategy result was calculated.")


if __name__ == "__main__":
    main()

