from __future__ import annotations

from exp006_preregistration import (
    build_locked_parameter_grid,
    validate_exp006_preregistration,
)
from experiment_lifecycle import (
    get_experiment_lifecycle,
)


def main() -> None:
    validate_exp006_preregistration()

    lifecycle = get_experiment_lifecycle(
        "EXP-006"
    )
    grid = build_locked_parameter_grid()

    if lifecycle.stage != "PRE_REGISTERED":
        raise RuntimeError(
            "EXP-006 must be PRE_REGISTERED."
        )

    print()
    print("EXP-006 PROTECTED PREFLIGHT")
    print("===========================")
    print(
        f"Lifecycle: {lifecycle.stage}"
    )
    print(
        f"Parameter combinations: {len(grid)}"
    )
    print(
        "Opening ranges: 5, 15, 30 minutes"
    )
    print(
        "Final entries: 10:30, 11:15, 12:00 ET"
    )
    print(
        "Directions: long, short, both"
    )
    print(
        "Walk-forward folds: 5 anchored annual"
    )
    print(
        "Selection-aware MCPT: 1,000 permutations"
    )
    print(
        "EXP-005 control changed: False"
    )
    print(
        "EXP-006 results calculated: False"
    )
    print("===========================")


if __name__ == "__main__":
    main()
