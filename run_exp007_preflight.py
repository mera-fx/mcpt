from __future__ import annotations

from pathlib import Path

from exp006_optimization_result import (
    verify_local_exp006_optimization_decision,
)
from exp007_preregistration import (
    get_exp007_preregistration,
    validate_exp007_preregistration,
)
from experiment_lifecycle import (
    get_experiment_lifecycle,
)


PROJECT_DIR = Path(__file__).resolve().parent
RESULT_ROOT = (
    PROJECT_DIR / "results" / "EXP-007"
)


def main() -> None:
    validate_exp007_preregistration()

    exp005 = get_experiment_lifecycle(
        "EXP-005"
    )
    exp006 = get_experiment_lifecycle(
        "EXP-006"
    )
    exp007 = get_experiment_lifecycle(
        "EXP-007"
    )

    if (
        exp005.stage
        != "ACCEPTED_FOR_PAPER_TESTING"
    ):
        raise RuntimeError(
            "EXP-005 control stage changed."
        )

    if exp006.stage != "REJECTED":
        raise RuntimeError(
            "EXP-006 is not formally rejected."
        )

    decision = (
        verify_local_exp006_optimization_decision()
    )
    if (
        decision["evaluation"]["decision"]
        != "REJECT_EXP006_KEEP_EXP005_CONTROL"
    ):
        raise RuntimeError(
            "Frozen EXP-006 rejection changed."
        )

    if exp007.stage != "PRE_REGISTERED":
        raise RuntimeError(
            "EXP-007 must be PRE_REGISTERED."
        )

    if RESULT_ROOT.exists():
        result_files = [
            path
            for path in RESULT_ROOT.rglob("*")
            if path.is_file()
        ]
        if result_files:
            raise RuntimeError(
                "EXP-007 result files already exist."
            )

    prereg = get_exp007_preregistration()
    rules = prereg["fixed_strategy_rules"]
    gates = prereg[
        "historical_decision_gates"
    ]

    print()
    print("EXP-007 PROTECTED PREFLIGHT")
    print("===========================")
    print(
        f"Lifecycle: {exp007.stage}"
    )
    print(
        "Strategy: fixed 30-minute ORB, "
        "long only"
    )
    print(
        "Entry: first completed 5-minute "
        "close above range; next bar open"
    )
    print(
        "Stop: opening-range low"
    )
    print(
        "Target: 1R"
    )
    print(
        "Forced flat: 14:00 New York"
    )
    print(
        "Position size: one fixed contract"
    )
    print(
        "Optimization enabled: "
        f"{rules['optimization_enabled']}"
    )
    print(
        "Parameter combinations: "
        f"{rules['parameter_combinations']}"
    )
    print(
        "Annual evaluation blocks: 5"
    )
    print(
        "Session-aware NQ MCPT: "
        "1,000 permutations"
    )
    print(
        "PF improvement over EXP-005 "
        "required: "
        f"{gates['profit_factor_improvement_vs_exp005_required']}"
    )
    print(
        "EXP-005 control changed: False"
    )
    print(
        "EXP-006 result changed: False"
    )
    print(
        "EXP-007 results calculated: False"
    )
    print("===========================")


if __name__ == "__main__":
    main()
