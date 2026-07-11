from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from exp003_preregistration import (
    get_exp003_preregistration,
)
from experiment_config import ResearchConfig


@dataclass(frozen=True)
class QuickScreenEvaluation:
    decision: str
    passed: bool
    gates: dict[str, dict[str, Any]]
    failed_gates: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "passed": self.passed,
            "gates": self.gates,
            "failed_gates": list(
                self.failed_gates
            ),
        }


def validate_exp003_config_matches_preregistration(
    config: ResearchConfig,
) -> None:
    preregistration = (
        get_exp003_preregistration()
    )

    expected = {
        "experiment_id": preregistration[
            "experiment_id"
        ],
        "strategy_name": (
            "volatility_compression_breakout_long"
        ),
        "fixed_parameters": preregistration[
            "fixed_parameters"
        ],
        "optimization_grid": preregistration[
            "optimized_parameters"
        ],
        "in_sample_start": pd.Timestamp(
            preregistration[
                "research_split"
            ]["in_sample_start"]
        ),
        "in_sample_end": (
            pd.Timestamp(
                preregistration[
                    "research_split"
                ]["in_sample_end"]
            )
            + pd.Timedelta(hours=1)
        ),
        "out_of_sample_start": pd.Timestamp(
            preregistration[
                "research_split"
            ]["out_of_sample_start"]
        ),
        "out_of_sample_end": (
            pd.Timestamp(
                preregistration[
                    "research_split"
                ]["out_of_sample_end"]
            )
            + pd.Timedelta(hours=1)
        ),
        "walkforward_training_bars": (
            preregistration[
                "research_split"
            ]["walkforward_training_bars"]
        ),
        "walkforward_retrain_bars": (
            preregistration[
                "research_split"
            ]["walkforward_retrain_bars"]
        ),
        "starting_capital": preregistration[
            "cost_and_execution_model"
        ]["starting_capital"],
        "commission_bps_per_side": (
            preregistration[
                "cost_and_execution_model"
            ]["commission_bps_per_side"]
        ),
        "slippage_bps_per_side": (
            preregistration[
                "cost_and_execution_model"
            ]["slippage_bps_per_side"]
        ),
        "execution_lag_bars": (
            preregistration[
                "cost_and_execution_model"
            ]["execution_lag_bars"]
        ),
        "mcpt_permutations": preregistration[
            "statistical_plan"
        ]["full_mcpt_permutations"],
        "random_seed": preregistration[
            "statistical_plan"
        ]["random_seed"],
    }

    mismatches: list[str] = []

    date_fields = {
        "in_sample_start",
        "in_sample_end",
        "out_of_sample_start",
        "out_of_sample_end",
    }

    for field_name, expected_value in (
        expected.items()
    ):
        actual_value = getattr(
            config,
            field_name,
        )

        if field_name in date_fields:
            matches = (
                pd.Timestamp(actual_value)
                == pd.Timestamp(expected_value)
            )
        else:
            matches = actual_value == expected_value

        if not matches:
            mismatches.append(
                f"{field_name}: expected "
                f"{expected_value!r}, got "
                f"{actual_value!r}"
            )

    if mismatches:
        raise ValueError(
            "EXP-003 configuration does not match the locked "
            "preregistration:\n- "
            + "\n- ".join(mismatches)
        )


def evaluate_exp003_quick_screen(
    *,
    best_in_sample_bar_pf: float,
    break_even_combination_count: int,
    neighbor_retention_ratio: float,
    quick_mcpt_p_value: float,
    fixed_in_sample_completed_trades: int,
) -> QuickScreenEvaluation:
    preregistration = (
        get_exp003_preregistration()
    )

    thresholds = preregistration[
        "quick_screen"
    ]["gates"]

    gate_values = {
        "best_in_sample_bar_pf": (
            float(best_in_sample_bar_pf)
        ),
        "parameter_combinations_pf_ge_1": (
            int(break_even_combination_count)
        ),
        "neighbor_median_ratio_to_best": (
            float(neighbor_retention_ratio)
        ),
        "quick_mcpt_p_value": (
            float(quick_mcpt_p_value)
        ),
        "fixed_in_sample_completed_trades": (
            int(fixed_in_sample_completed_trades)
        ),
    }

    gates: dict[str, dict[str, Any]] = {}

    gates["best_in_sample_bar_pf"] = {
        "actual": gate_values[
            "best_in_sample_bar_pf"
        ],
        "operator": ">",
        "threshold": thresholds[
            "best_in_sample_bar_pf_strictly_above"
        ],
        "passed": (
            gate_values[
                "best_in_sample_bar_pf"
            ]
            > thresholds[
                "best_in_sample_bar_pf_strictly_above"
            ]
        ),
    }

    gates[
        "parameter_combinations_pf_ge_1"
    ] = {
        "actual": gate_values[
            "parameter_combinations_pf_ge_1"
        ],
        "operator": ">=",
        "threshold": thresholds[
            "minimum_parameter_combinations_pf_ge_1"
        ],
        "passed": (
            gate_values[
                "parameter_combinations_pf_ge_1"
            ]
            >= thresholds[
                "minimum_parameter_combinations_pf_ge_1"
            ]
        ),
    }

    neighbor_value = gate_values[
        "neighbor_median_ratio_to_best"
    ]

    gates[
        "neighbor_median_ratio_to_best"
    ] = {
        "actual": neighbor_value,
        "operator": ">=",
        "threshold": thresholds[
            "minimum_neighbour_median_ratio_to_best"
        ],
        "passed": (
            np.isfinite(neighbor_value)
            and neighbor_value
            >= thresholds[
                "minimum_neighbour_median_ratio_to_best"
            ]
        ),
    }

    gates["quick_mcpt_p_value"] = {
        "actual": gate_values[
            "quick_mcpt_p_value"
        ],
        "operator": "<=",
        "threshold": thresholds[
            "maximum_quick_mcpt_p_value"
        ],
        "passed": (
            gate_values[
                "quick_mcpt_p_value"
            ]
            <= thresholds[
                "maximum_quick_mcpt_p_value"
            ]
        ),
    }

    gates[
        "fixed_in_sample_completed_trades"
    ] = {
        "actual": gate_values[
            "fixed_in_sample_completed_trades"
        ],
        "operator": ">=",
        "threshold": thresholds[
            "minimum_in_sample_completed_trades_fixed"
        ],
        "passed": (
            gate_values[
                "fixed_in_sample_completed_trades"
            ]
            >= thresholds[
                "minimum_in_sample_completed_trades_fixed"
            ]
        ),
    }

    failed_gates = tuple(
        gate_name
        for gate_name, gate in gates.items()
        if not gate["passed"]
    )

    passed = not failed_gates

    return QuickScreenEvaluation(
        decision=(
            "PASS_TO_FULL_VALIDATION"
            if passed
            else "REJECT"
        ),
        passed=passed,
        gates=gates,
        failed_gates=failed_gates,
    )
