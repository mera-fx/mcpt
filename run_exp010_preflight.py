from __future__ import annotations

from pathlib import Path

from exp009_tournament_result import verify_local_exp009_tournament_result
from exp010_preregistration import (
    get_exp010_preregistration,
    validate_exp010_preregistration,
)
from experiment_lifecycle import get_experiment_lifecycle


PROJECT_DIR = Path(__file__).resolve().parent
RESULT_ROOT = PROJECT_DIR / "results" / "EXP-010"


def main() -> None:
    validate_exp010_preregistration()
    exp009 = verify_local_exp009_tournament_result()

    expected_stages = {
        "EXP-005": "ACCEPTED_FOR_PAPER_TESTING",
        "EXP-006": "REJECTED",
        "EXP-007": "REJECTED",
        "EXP-008": "REJECTED",
        "EXP-009": "REVIEW",
        "EXP-010": "PRE_REGISTERED",
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
        raise RuntimeError("EXP-010 result files already exist.")

    record = get_exp010_preregistration()
    mcpt = record["selection_aware_mcpt"]
    walk_forward = record["anchored_walk_forward"]
    relationship = record["relationship_to_exp009"]

    print()
    print("EXP-010 DEEP-VALIDATION PREFLIGHT")
    print("=================================")
    print("Lifecycle: PRE_REGISTERED")
    print("Family: opening-drive continuation")
    print("Locked candidates: 4")
    print(
        "User reference: "
        f"{relationship['user_preferred_reference_candidate']}"
    )
    print("User reference treated as independently selected: False")
    print("EXP-009 candidate measurements hash-verified: True")
    print(
        "EXP-009 candidates preserved: "
        f"{len(exp009['candidates'])}"
    )
    print(f"Sessions: {record['market_and_data']['expected_included_sessions']}")
    print(f"Anchored walk-forward folds: {walk_forward['fold_count']}")
    print(f"Selection-aware NQ MCPT: {mcpt['permutations']} permutations")
    print("All 4 candidates selected inside every permutation: True")
    print("Prior 6-family selection corrected by this MCPT: False")
    print(
        "Bootstrap diagnostics: "
        f"{record['bootstrap_diagnostics']['resamples']:,} resamples"
    )
    print("Automatic trading winner: False")
    print("Paper trading authorized: False")
    print("Live trading authorized: False")
    print("EXP-010 results calculated: False")
    print("=================================")
    print("Preflight passed. No EXP-010 result was calculated.")


if __name__ == "__main__":
    main()
