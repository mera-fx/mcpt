from __future__ import annotations

from exp013_validation_result import verify_local_exp013_validation_result
from exp014_preregistration import (
    get_exp014_preregistration,
    validate_exp014_preregistration,
)
from experiment_lifecycle import get_experiment_lifecycle


def main() -> None:
    validate_exp014_preregistration()
    verify_local_exp013_validation_result()
    record = get_exp014_preregistration()
    if get_experiment_lifecycle("EXP-013").stage != "REVIEW":
        raise RuntimeError("EXP-013 must remain frozen in REVIEW.")
    if get_experiment_lifecycle("EXP-014").stage != "PRE_REGISTERED":
        raise RuntimeError("EXP-014 must be PRE_REGISTERED.")

    print()
    print("EXP-014 RESULT-FREE PREFLIGHT")
    print("============================")
    print("EXP-013 lifecycle: REVIEW")
    print("EXP-014 lifecycle: PRE_REGISTERED")
    print("Finalists:         3 unchanged")
    print(
        "Sleeve pairs:      "
        f"{record['sleeve_pair_comparison']['pair_count']} fixed pairs"
    )
    print("Focus year:        2025")
    print("Regimes:           entry-known trend and volatility")
    print("Parameter search:  disabled")
    print("Weight search:     disabled")
    print("MCPT rerun:        disabled")
    print("Bootstrap rerun:   disabled")
    print("Automatic winner:  False")
    print("Trading authorized: False")
    print("Results calculated: False")
    print("============================")
    print(
        "Preflight passed. No EXP-014 trade reconstruction, behaviour, "
        "overlap, regime or sleeve-pair result was calculated."
    )


if __name__ == "__main__":
    main()
