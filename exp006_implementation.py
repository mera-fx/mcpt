from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from exp006_candidate_scoring import BASELINE
from exp006_orb import (
    FINAL_ENTRY_SLOT,
    FINAL_SIGNAL_SLOT,
    locked_parameters,
)
from exp006_selection_mcpt import (
    ENGINE_VERSION,
    FORMAL_BASE_SEED,
    FORMAL_MINIMUM_TRADES,
    FORMAL_PERMUTATIONS,
)

PROJECT_DIR = Path(__file__).resolve().parent

EXP006_IMPLEMENTATION: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-006",
    "stage": "IMPLEMENTATION",
    "locked_date": "2026-07-15",
    "status": "LOCKED_BEFORE_RESULTS",
    "results_calculated": False,
    "source_commit": "799a758bdf1672db8e8f350df82f66a6a2b5a73a",
    "engine": {
        "parameterized_orb": "exp006_orb_v1",
        "candidate_scoring": "exp006_candidate_scoring_v1",
        "walk_forward": "exp006_anchored_walk_forward_v1",
        "selection_mcpt": ENGINE_VERSION,
        "report": "exp006_vertical_report_v1",
    },
    "parameter_grid": {
        "count": 27,
        "opening_range_minutes": [5, 15, 30],
        "final_entry_times_new_york": [
            "10:30",
            "11:15",
            "12:00",
        ],
        "direction_modes": [
            "long",
            "short",
            "both",
        ],
        "final_entry_slots": FINAL_ENTRY_SLOT,
        "final_signal_slots": FINAL_SIGNAL_SLOT,
        "baseline": BASELINE.to_dict(),
    },
    "selection": {
        "global_components": [
            "NQ trade Profit Factor",
            "NQ net-profit-to-drawdown",
            "NQ average-trade-to-cost",
            "MNQ trade Profit Factor",
            "profitable NQ calendar years",
            "fixed-candidate 2021-2025 NQ net profit",
        ],
        "ranking": "median component rank",
        "minimum_profitable_neighbor_share": 0.50,
        "maximum_selected_candidates": 1,
    },
    "walk_forward": {
        "folds": 5,
        "method": "anchored annual",
        "training_selection_components": 5,
        "test_data_used_for_selection": False,
    },
    "selection_aware_mcpt": {
        "permutations": FORMAL_PERMUTATIONS,
        "base_seed": FORMAL_BASE_SEED,
        "minimum_completed_trades": (
            FORMAL_MINIMUM_TRADES
        ),
        "all_27_candidates_inside_each_permutation": True,
        "statistic_components": [
            "bounded Profit Factor excess",
            "bounded net-profit-to-drawdown",
            "bounded average-trade-to-cost",
            "profitable-year fraction",
        ],
        "checkpoint_frequency": 5,
        "exact_serial_parallel_parity_required": True,
    },
    "protections": {
        "exp005_control_changed": False,
        "new_data_cleaning_decisions": 0,
        "parameter_addition_after_results": False,
        "live_trading_authorized": False,
        "automatic_lifecycle_edit": False,
        "result_file_may_be_overwritten": False,
    },
}


def get_exp006_implementation() -> dict[str, Any]:
    return deepcopy(EXP006_IMPLEMENTATION)


def validate_exp006_implementation(
    record: dict[str, Any] | None = None,
) -> None:
    current = (
        EXP006_IMPLEMENTATION
        if record is None
        else record
    )
    if (
        current.get("schema_version") != 1
        or current.get("experiment_id")
        != "EXP-006"
        or current.get("status")
        != "LOCKED_BEFORE_RESULTS"
        or current.get("results_calculated")
        is not False
    ):
        raise ValueError(
            "EXP-006 implementation identity or pre-result state changed."
        )
    grid = current["parameter_grid"]
    if (
        grid["count"] != 27
        or len(locked_parameters()) != 27
        or grid["baseline"] != BASELINE.to_dict()
        or grid["final_entry_slots"]
        != {
            "10:30": 12,
            "11:15": 21,
            "12:00": 30,
        }
        or grid["final_signal_slots"]
        != {
            "10:30": 11,
            "11:15": 20,
            "12:00": 29,
        }
    ):
        raise ValueError(
            "EXP-006 implementation grid changed."
        )
    mcpt = current["selection_aware_mcpt"]
    if (
        mcpt["permutations"] != 1000
        or mcpt["base_seed"] != 46
        or mcpt["minimum_completed_trades"]
        != 1000
        or mcpt[
            "all_27_candidates_inside_each_permutation"
        ]
        is not True
        or mcpt[
            "exact_serial_parallel_parity_required"
        ]
        is not True
    ):
        raise ValueError(
            "EXP-006 implementation MCPT changed."
        )
    protections = current["protections"]
    if (
        protections["exp005_control_changed"]
        is not False
        or protections[
            "new_data_cleaning_decisions"
        ]
        != 0
        or protections[
            "live_trading_authorized"
        ]
        is not False
        or protections[
            "result_file_may_be_overwritten"
        ]
        is not False
    ):
        raise ValueError(
            "EXP-006 implementation protections changed."
        )


if __name__ == "__main__":
    validate_exp006_implementation()
    print(
        "EXP-006 implementation is locked and contains no results."
    )
