from __future__ import annotations

from pathlib import Path

from exp006_optimization_result import (
    verify_local_exp006_optimization_decision,
)
from exp007_replication_result import (
    verify_local_exp007_replication_decision,
)
from exp008_preregistration import (
    get_exp008_preregistration,
    validate_exp008_preregistration,
)
from experiment_lifecycle import (
    get_experiment_lifecycle,
)


PROJECT_DIR = Path(__file__).resolve().parent
RESULT_ROOT = (
    PROJECT_DIR / "results" / "EXP-008"
)


def main() -> None:
    validate_exp008_preregistration()

    exp005 = get_experiment_lifecycle(
        "EXP-005"
    )
    exp006 = get_experiment_lifecycle(
        "EXP-006"
    )
    exp007 = get_experiment_lifecycle(
        "EXP-007"
    )
    exp008 = get_experiment_lifecycle(
        "EXP-008"
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
            "EXP-006 stage changed."
        )

    if exp007.stage != "REJECTED":
        raise RuntimeError(
            "EXP-007 stage changed."
        )

    verify_local_exp006_optimization_decision()
    verify_local_exp007_replication_decision()

    if exp008.stage != "PRE_REGISTERED":
        raise RuntimeError(
            "EXP-008 must be PRE_REGISTERED."
        )

    if RESULT_ROOT.exists():
        result_files = [
            path
            for path in RESULT_ROOT.rglob("*")
            if path.is_file()
        ]
        if result_files:
            raise RuntimeError(
                "EXP-008 result files already exist."
            )

    prereg = get_exp008_preregistration()
    grid = prereg["parameter_grid"]
    selection = prereg["candidate_selection"]
    mcpt = prereg["selection_aware_mcpt"]
    gates = prereg["historical_decision_gates"]

    print()
    print("EXP-008 PROTECTED PREFLIGHT")
    print("===========================")
    print(
        f"Lifecycle: {exp008.stage}"
    )
    print(
        "Strategy: structured long-only ORB "
        "exit geometry"
    )
    print(
        "Opening ranges: 15, 30, 45 minutes"
    )
    print(
        "Targets: 0.5R, 1.0R, 1.5R"
    )
    print(
        "Forced flats: 12:00, 14:00, "
        "15:55 New York"
    )
    print(
        "Parameter combinations: "
        f"{grid['combination_count']}"
    )
    print(
        "EXP-007 baseline included once: "
        f"{grid['exp007_baseline_included_exactly_once']}"
    )
    print(
        "Neighbor stability required: True"
    )
    print(
        "Anchored annual folds: 5"
    )
    print(
        "Selection-aware NQ MCPT: "
        f"{mcpt['permutations']:,} permutations"
    )
    print(
        "All candidates selected inside "
        "each permutation: "
        f"{mcpt['candidate_selection_repeated_inside_each_permutation']}"
    )
    print(
        "Selected PF must exceed frozen "
        "EXP-007 PF: "
        f"{gates['minimum_selected_nq_trade_profit_factor_strict']:.6f}"
    )
    print(
        "Position size: fixed one contract"
    )
    print(
        "Volatility targeting enabled: False"
    )
    print(
        "Historical status: exploratory"
    )
    print(
        "EXP-005/006/007 changed: False"
    )
    print(
        "EXP-008 results calculated: False"
    )
    print("===========================")


if __name__ == "__main__":
    main()
