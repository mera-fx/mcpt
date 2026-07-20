from __future__ import annotations

from exp012_tournament_result import verify_local_exp012_tournament_result
from exp013_preregistration import (
    get_exp013_preregistration,
    validate_exp013_preregistration,
)
from experiment_lifecycle import get_experiment_lifecycle


def main() -> None:
    validate_exp013_preregistration()
    verify_local_exp012_tournament_result()
    record = get_exp013_preregistration()

    if get_experiment_lifecycle("EXP-012").stage != "REVIEW":
        raise RuntimeError("EXP-012 must remain frozen in REVIEW.")
    if get_experiment_lifecycle("EXP-013").stage != "PRE_REGISTERED":
        raise RuntimeError("EXP-013 must be PRE_REGISTERED.")

    lock = record["candidate_lock"]
    walk_forward = record["anchored_walk_forward"]
    mcpt = record["discovery_wide_selection_aware_mcpt"]
    bootstrap = record["bootstrap_diagnostics"]

    print()
    print("EXP-013 RESULT-FREE PREFLIGHT")
    print("============================")
    print("EXP-012 lifecycle: REVIEW")
    print("EXP-013 lifecycle: PRE_REGISTERED")
    print(f"Finalists:         {lock['candidate_count']}")
    print("Families:          gap fade / premarket continuation")
    print(f"Anchored folds:    {walk_forward['fold_count']}")
    print(
        "Primary MCPT:      "
        f"{mcpt['permutations']:,} permutations, all 24 candidates"
    )
    print(f"MCPT seed:         {mcpt['random_seed']}")
    print(f"Bootstrap:         {bootstrap['resamples']:,} per finalist")
    print(f"Bootstrap seed:    {bootstrap['random_seed']}")
    print("Automatic winner: False")
    print("Independent claim: False")
    print("Trading authorized: False")
    print("Results calculated: False")
    print("============================")
    print(
        "Preflight passed. No EXP-013 strategy, walk-forward, bootstrap "
        "or MCPT result was calculated."
    )


if __name__ == "__main__":
    main()
