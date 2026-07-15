from __future__ import annotations

from copy import deepcopy
from itertools import product
from typing import Any


OPENING_RANGE_MINUTES = (5, 15, 30)
FINAL_ENTRY_TIMES_NEW_YORK = (
    "10:30",
    "11:15",
    "12:00",
)
DIRECTION_MODES = (
    "long",
    "short",
    "both",
)

FINAL_SIGNAL_BY_ENTRY = {
    "10:30": "10:25",
    "11:15": "11:10",
    "12:00": "11:55",
}

BASELINE_PARAMETERS = {
    "opening_range_minutes": 15,
    "final_entry_time_new_york": "12:00",
    "direction_mode": "both",
}


def build_locked_parameter_grid(
) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "opening_range_minutes": opening_range,
            "final_entry_time_new_york": final_entry,
            "final_signal_time_new_york": (
                FINAL_SIGNAL_BY_ENTRY[
                    final_entry
                ]
            ),
            "direction_mode": direction,
        }
        for (
            opening_range,
            final_entry,
            direction,
        ) in product(
            OPENING_RANGE_MINUTES,
            FINAL_ENTRY_TIMES_NEW_YORK,
            DIRECTION_MODES,
        )
    )


EXP006_PREREGISTRATION: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-006",
    "title": (
        "NQ/MNQ Structured ORB Optimization"
    ),
    "locked_date": "2026-07-15",
    "research_status": "PRE_REGISTERED",
    "implementation_status": "NOT_RUN",
    "results_viewed": "NONE",
    "source_experiment": {
        "experiment_id": "EXP-005",
        "relationship": (
            "SEPARATE_STRUCTURED_OPTIMIZATION"
        ),
        "source_status": (
            "ACCEPTED_FOR_PAPER_TESTING"
        ),
        "source_is_control": True,
        "source_must_remain_frozen": True,
    },
    "hypothesis": (
        "A small, structured set of opening-range "
        "length, final-entry time and direction "
        "choices may improve risk-adjusted NQ/MNQ "
        "ORB performance without relying on a large "
        "parameter search."
    ),
    "null_hypothesis": (
        "No candidate in the locked 27-combination "
        "grid provides stable improvement over the "
        "frozen EXP-005 control after costs, "
        "walk-forward testing and selection-aware "
        "permutation testing."
    ),
    "interpretation": {
        "historical_status": (
            "EXPLORATORY_BECAUSE_2019_2025_WAS_ALREADY_VIEWED"
        ),
        "historical_result_cannot_authorize_live_trading": True,
        "best_possible_historical_decision": (
            "CANDIDATE_FOR_FORWARD_PAPER_COMPARISON"
        ),
        "final_confirmation_source": (
            "NEW_FORWARD_DATA_ONLY"
        ),
    },
    "market_and_data": {
        "primary_evidence_market": "NQ",
        "secondary_implementation_market": "MNQ",
        "secondary_is_independent_evidence": False,
        "data_source": (
            "Frozen EXP-005 Quantower/Lucid-Rithmic "
            "NQ and MNQ datasets"
        ),
        "historical_start": "2019-05-06",
        "historical_end": "2025-12-31",
        "source_timeframe": "1 minute",
        "strategy_timeframe": "5 minutes",
        "source_timezone": "UTC",
        "research_timezone": (
            "America/New_York"
        ),
        "cash_session": "09:30-16:00",
        "expected_one_minute_bars_per_full_session": 390,
        "expected_five_minute_bars_per_full_session": 78,
        "reuse_only_frozen_exp005_clean_sessions": True,
        "new_data_cleaning_decisions_prohibited": True,
        "missing_bar_fill_prohibited": True,
        "raw_source_editing_prohibited": True,
    },
    "locked_parameter_grid": {
        "opening_range_minutes": list(
            OPENING_RANGE_MINUTES
        ),
        "final_entry_times_new_york": list(
            FINAL_ENTRY_TIMES_NEW_YORK
        ),
        "direction_modes": list(
            DIRECTION_MODES
        ),
        "parameter_combinations": 27,
        "baseline_parameters": (
            BASELINE_PARAMETERS
        ),
        "baseline_is_in_grid": True,
        "grid": list(
            build_locked_parameter_grid()
        ),
    },
    "unchanged_execution_rules": {
        "signal_requires_completed_bar": True,
        "breakout_is_strict_close_outside_range": True,
        "entry": "next 5-minute bar open",
        "entry_gap_filter": "NONE",
        "protective_stop": (
            "opposite opening-range boundary"
        ),
        "gap_through_stop": (
            "fill at bar open; otherwise boundary"
        ),
        "entry_bar_can_stop": True,
        "maximum_trades_per_session": 1,
        "same_day_reversal": False,
        "forced_flat_time_new_york": "15:55",
        "forced_flat_price": (
            "15:55 five-minute bar open"
        ),
        "overnight_positions": False,
    },
    "contract_and_cost_model": {
        "NQ": {
            "multiplier_usd_per_point": 20.0,
            "tick_size_points": 0.25,
            "fees_usd_per_side": 2.50,
            "slippage_ticks_per_side": 1.0,
            "round_trip_cost_usd": 15.0,
            "analytical_reference_capital_usd": 100000.0,
        },
        "MNQ": {
            "multiplier_usd_per_point": 2.0,
            "tick_size_points": 0.25,
            "fees_usd_per_side": 1.00,
            "slippage_ticks_per_side": 1.0,
            "round_trip_cost_usd": 3.0,
            "analytical_reference_capital_usd": 10000.0,
        },
        "cost_sensitivity_ticks_per_side": [
            0,
            1,
            2,
        ],
    },
    "walk_forward": {
        "method": (
            "ANCHORED_ANNUAL_SELECTION"
        ),
        "folds": [
            {
                "train_start": "2019-05-06",
                "train_end": "2020-12-31",
                "test_start": "2021-01-01",
                "test_end": "2021-12-31",
            },
            {
                "train_start": "2019-05-06",
                "train_end": "2021-12-31",
                "test_start": "2022-01-01",
                "test_end": "2022-12-31",
            },
            {
                "train_start": "2019-05-06",
                "train_end": "2022-12-31",
                "test_start": "2023-01-01",
                "test_end": "2023-12-31",
            },
            {
                "train_start": "2019-05-06",
                "train_end": "2023-12-31",
                "test_start": "2024-01-01",
                "test_end": "2024-12-31",
            },
            {
                "train_start": "2019-05-06",
                "train_end": "2024-12-31",
                "test_start": "2025-01-01",
                "test_end": "2025-12-31",
            },
        ],
        "parameter_selection_uses_training_only": True,
        "test_fold_parameter_reselection_prohibited": True,
    },
    "candidate_scoring": {
        "eligible_only_if": {
            "minimum_nq_trade_profit_factor_strict": 1.0,
            "minimum_mnq_trade_profit_factor_strict": 1.0,
            "minimum_nq_net_profit_usd_strict": 0.0,
            "minimum_mnq_net_profit_usd_strict": 0.0,
            "minimum_nq_completed_trades": 1000,
            "minimum_profitable_nq_calendar_years": 5,
        },
        "ranking_method": (
            "MEDIAN_RANK_ACROSS_LOCKED_COMPONENTS"
        ),
        "ranking_components": [
            "NQ trade Profit Factor descending",
            "NQ net-profit-to-maximum-drawdown descending",
            "NQ average trade divided by round-trip cost descending",
            "MNQ trade Profit Factor descending",
            "profitable NQ calendar years descending",
            "anchored walk-forward NQ net profit descending",
        ],
        "tie_breakers_in_order": [
            "Lower NQ maximum drawdown percentage",
            "Higher NQ completed-trade count",
            "Smaller distance from EXP-005 baseline",
            "Lexicographic parameter order",
        ],
        "isolated_peak_prohibited": True,
        "neighbor_definition": (
            "One grid step away in exactly one "
            "parameter while the other two match."
        ),
        "minimum_profitable_neighbor_share": 0.50,
        "maximum_selected_candidate_count": 1,
    },
    "selection_aware_mcpt": {
        "enabled": True,
        "primary_market": "NQ",
        "permutations": 1000,
        "random_seed": 46,
        "method": (
            "Use the locked EXP-005 session-aware "
            "one-minute permutation engine. Evaluate "
            "all 27 candidates inside every "
            "permutation and record the best eligible "
            "composite score so selection bias is "
            "included in the null distribution."
        ),
        "optimization_inside_each_permutation": True,
        "maximum_p_value": 0.05,
        "exact_serial_parallel_parity_required": True,
    },
    "historical_decision_gates": {
        "all_required": True,
        "selected_candidate_must_differ_from_baseline": True,
        "selected_candidate_must_pass_eligibility": True,
        "minimum_profitable_neighbor_share": 0.50,
        "minimum_profitable_walk_forward_test_folds": 3,
        "minimum_total_walk_forward_nq_net_profit_usd_strict": 0.0,
        "minimum_total_walk_forward_mnq_net_profit_usd_strict": 0.0,
        "maximum_selection_aware_mcpt_p_value": 0.05,
        "maximum_nq_drawdown_increase_vs_baseline_fraction": 0.20,
        "minimum_nq_profit_factor_improvement_vs_baseline": 0.02,
        "minimum_mnq_profit_factor_strict": 1.0,
        "failure_action": (
            "REJECT_EXP006_KEEP_EXP005_CONTROL"
        ),
        "pass_action": (
            "LOCK_ONE_CANDIDATE_FOR_FORWARD_PAPER_COMPARISON"
        ),
    },
    "prohibited_actions": [
        "Changing EXP-005.",
        "Adding parameters after results are viewed.",
        "Testing stops, targets, filters or sizing not listed here.",
        "Selecting a candidate by net profit alone.",
        "Treating MNQ as independent evidence.",
        "Claiming 2019-2025 is untouched confirmation data.",
        "Running fewer than all 27 candidates.",
        "Changing ranking components after results are viewed.",
        "Optimizing only the real market during MCPT.",
        "Authorizing live trading from historical EXP-006 results.",
    ],
}


def get_exp006_preregistration(
) -> dict[str, Any]:
    return deepcopy(
        EXP006_PREREGISTRATION
    )


def validate_exp006_preregistration(
    record: dict[str, Any] | None = None,
) -> None:
    current = (
        EXP006_PREREGISTRATION
        if record is None
        else record
    )

    if (
        current.get("schema_version") != 1
        or current.get("experiment_id")
        != "EXP-006"
        or current.get("research_status")
        != "PRE_REGISTERED"
        or current.get("implementation_status")
        != "NOT_RUN"
        or current.get("results_viewed")
        != "NONE"
    ):
        raise ValueError(
            "EXP-006 preregistration identity "
            "or pre-result state changed."
        )

    source = current["source_experiment"]

    if (
        source["experiment_id"] != "EXP-005"
        or source["source_status"]
        != "ACCEPTED_FOR_PAPER_TESTING"
        or source["source_is_control"]
        is not True
        or source["source_must_remain_frozen"]
        is not True
    ):
        raise ValueError(
            "EXP-006 source/control relationship changed."
        )

    interpretation = current["interpretation"]

    if (
        interpretation["historical_status"]
        != "EXPLORATORY_BECAUSE_2019_2025_WAS_ALREADY_VIEWED"
        or interpretation[
            "historical_result_cannot_authorize_live_trading"
        ]
        is not True
        or interpretation[
            "best_possible_historical_decision"
        ]
        != "CANDIDATE_FOR_FORWARD_PAPER_COMPARISON"
        or interpretation[
            "final_confirmation_source"
        ]
        != "NEW_FORWARD_DATA_ONLY"
    ):
        raise ValueError(
            "EXP-006 interpretation boundary changed."
        )

    grid = current["locked_parameter_grid"]
    expected_grid = list(
        build_locked_parameter_grid()
    )

    if (
        grid["opening_range_minutes"]
        != [5, 15, 30]
        or grid["final_entry_times_new_york"]
        != ["10:30", "11:15", "12:00"]
        or grid["direction_modes"]
        != ["long", "short", "both"]
        or grid["parameter_combinations"] != 27
        or grid["baseline_parameters"]
        != BASELINE_PARAMETERS
        or grid["baseline_is_in_grid"]
        is not True
        or grid["grid"] != expected_grid
        or len(expected_grid) != 27
    ):
        raise ValueError(
            "EXP-006 locked 27-combination grid changed."
        )

    if (
        sum(
            item["opening_range_minutes"] == 15
            and item[
                "final_entry_time_new_york"
            ]
            == "12:00"
            and item["direction_mode"]
            == "both"
            for item in expected_grid
        )
        != 1
    ):
        raise ValueError(
            "EXP-005 baseline must appear exactly "
            "once in EXP-006."
        )

    walk_forward = current["walk_forward"]

    if (
        walk_forward["method"]
        != "ANCHORED_ANNUAL_SELECTION"
        or len(walk_forward["folds"]) != 5
        or walk_forward[
            "parameter_selection_uses_training_only"
        ]
        is not True
        or walk_forward[
            "test_fold_parameter_reselection_prohibited"
        ]
        is not True
    ):
        raise ValueError(
            "EXP-006 walk-forward plan changed."
        )

    scoring = current["candidate_scoring"]

    if (
        scoring["ranking_method"]
        != "MEDIAN_RANK_ACROSS_LOCKED_COMPONENTS"
        or len(scoring["ranking_components"])
        != 6
        or scoring["isolated_peak_prohibited"]
        is not True
        or scoring[
            "minimum_profitable_neighbor_share"
        ]
        != 0.50
        or scoring[
            "maximum_selected_candidate_count"
        ]
        != 1
    ):
        raise ValueError(
            "EXP-006 candidate-scoring plan changed."
        )

    mcpt = current["selection_aware_mcpt"]

    if (
        mcpt["enabled"] is not True
        or mcpt["primary_market"] != "NQ"
        or mcpt["permutations"] != 1000
        or mcpt["random_seed"] != 46
        or mcpt[
            "optimization_inside_each_permutation"
        ]
        is not True
        or mcpt["maximum_p_value"] != 0.05
        or mcpt[
            "exact_serial_parallel_parity_required"
        ]
        is not True
    ):
        raise ValueError(
            "EXP-006 selection-aware MCPT changed."
        )

    gates = current[
        "historical_decision_gates"
    ]

    if (
        gates["all_required"] is not True
        or gates[
            "selected_candidate_must_differ_from_baseline"
        ]
        is not True
        or gates[
            "minimum_profitable_walk_forward_test_folds"
        ]
        != 3
        or gates[
            "maximum_selection_aware_mcpt_p_value"
        ]
        != 0.05
        or gates["failure_action"]
        != "REJECT_EXP006_KEEP_EXP005_CONTROL"
        or gates["pass_action"]
        != "LOCK_ONE_CANDIDATE_FOR_FORWARD_PAPER_COMPARISON"
    ):
        raise ValueError(
            "EXP-006 historical decision gates changed."
        )

    prohibited = " ".join(
        current["prohibited_actions"]
    ).lower()

    for phrase in (
        "changing exp-005",
        "adding parameters",
        "net profit alone",
        "untouched confirmation",
        "all 27",
        "during mcpt",
        "live trading",
    ):
        if phrase not in prohibited:
            raise ValueError(
                "EXP-006 prohibition missing: "
                f"{phrase}."
            )


if __name__ == "__main__":
    validate_exp006_preregistration()
    print(
        "EXP-006 structured ORB preregistration "
        "is valid and contains no results."
    )
