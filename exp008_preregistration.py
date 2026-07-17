from __future__ import annotations

from copy import deepcopy
from itertools import product
from typing import Any


OPENING_RANGE_MINUTES = (15, 30, 45)
REWARD_TO_RISK_VALUES = (0.5, 1.0, 1.5)
FORCED_FLAT_TIMES = ("12:00", "14:00", "15:55")


def _decimal_key(value: float) -> str:
    return str(value).replace(".", "p")


def parameter_key(
    opening_range_minutes: int,
    reward_to_risk: float,
    forced_flat_time_new_york: str,
) -> str:
    return (
        f"or{opening_range_minutes}_"
        f"target{_decimal_key(reward_to_risk)}_"
        f"flat{forced_flat_time_new_york.replace(':', '')}"
    )


def build_exp008_grid() -> list[dict[str, Any]]:
    combinations: list[dict[str, Any]] = []

    for (
        opening_range_minutes,
        reward_to_risk,
        forced_flat_time,
    ) in product(
        OPENING_RANGE_MINUTES,
        REWARD_TO_RISK_VALUES,
        FORCED_FLAT_TIMES,
    ):
        opening_range_end = {
            15: "09:45",
            30: "10:00",
            45: "10:15",
        }[opening_range_minutes]
        final_signal_close = {
            "12:00": "11:55",
            "14:00": "13:55",
            "15:55": "15:50",
        }[forced_flat_time]

        combinations.append(
            {
                "parameter_key": parameter_key(
                    opening_range_minutes,
                    reward_to_risk,
                    forced_flat_time,
                ),
                "opening_range_minutes": (
                    opening_range_minutes
                ),
                "opening_range_end_new_york": (
                    opening_range_end
                ),
                "opening_range_five_minute_bars": (
                    opening_range_minutes // 5
                ),
                "reward_to_risk": reward_to_risk,
                "forced_flat_time_new_york": (
                    forced_flat_time
                ),
                "final_signal_close_time_new_york": (
                    final_signal_close
                ),
                "latest_entry_time_new_york": (
                    final_signal_close
                ),
            }
        )

    return combinations


EXP008_GRID = build_exp008_grid()


EXP008_PREREGISTRATION: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-008",
    "title": (
        "NQ/MNQ Structured Long-Only ORB "
        "Exit-Geometry Optimization"
    ),
    "locked_date": "2026-07-17",
    "research_status": "PRE_REGISTERED",
    "implementation_status": "NOT_RUN",
    "results_viewed": "NONE",
    "experiment_relationships": {
        "exp005": {
            "relationship": (
                "ACCEPTED_FROZEN_PAPER_CONTROL"
            ),
            "required_stage": (
                "ACCEPTED_FOR_PAPER_TESTING"
            ),
            "must_remain_unchanged": True,
        },
        "exp006": {
            "relationship": (
                "COMPLETED_REJECTED_ORB_OPTIMIZATION"
            ),
            "required_stage": "REJECTED",
            "must_remain_unchanged": True,
        },
        "exp007": {
            "relationship": (
                "COMPLETED_REJECTED_FIXED_BASELINE"
            ),
            "required_stage": "REJECTED",
            "must_remain_unchanged": True,
            "baseline_parameter_key": (
                "or30_target1p0_flat1400"
            ),
            "baseline_nq_trade_profit_factor": (
                1.1168167521220216
            ),
            "baseline_nq_net_profit_usd": 67780.0,
            "baseline_nq_completed_trades": 988,
            "baseline_nq_mcpt_p_value": (
                0.055944055944055944
            ),
            "baseline_failed_gate": (
                "nq_session_aware_mcpt_p_value"
            ),
        },
    },
    "hypothesis": (
        "A small, structured search over opening-range "
        "length, profit-target distance and forced-flat "
        "time may identify a stable long-only NQ/MNQ "
        "opening-range breakout geometry with stronger "
        "post-cost evidence than the fixed EXP-007 "
        "baseline."
    ),
    "null_hypothesis": (
        "After accounting for all 27 choices inside "
        "selection-aware permutation testing, no stable "
        "exit geometry provides a positive and temporally "
        "robust post-cost edge stronger than EXP-007."
    ),
    "interpretation": {
        "historical_status": (
            "EXPLORATORY_BECAUSE_2019_2025_WAS_ALREADY_VIEWED"
        ),
        "historical_result_cannot_authorize_live_trading": (
            True
        ),
        "best_possible_historical_decision": (
            "LOCK_EXP008_CANDIDATE_FOR_NEW_FORWARD_"
            "PAPER_COMPARISON"
        ),
        "final_confirmation_source": "NEW_FORWARD_DATA_ONLY",
        "selection_bias_must_be_included_in_mcpt": True,
        "exp007_rejection_cannot_be_reinterpreted": True,
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
        "signal_timeframe": "5 minutes",
        "source_timezone": "UTC",
        "research_timezone": "America/New_York",
        "cash_session": "09:30-16:00",
        "expected_included_sessions": 1639,
        "expected_one_minute_bars_per_full_session": 390,
        "expected_five_minute_bars_per_full_session": 78,
        "reuse_only_frozen_exp005_clean_sessions": True,
        "new_data_cleaning_decisions_prohibited": True,
        "missing_bar_fill_prohibited": True,
        "raw_source_editing_prohibited": True,
    },
    "fixed_rules_shared_by_all_candidates": {
        "optimization_enabled": True,
        "optimization_scope": (
            "ONLY_THE_27_LOCKED_GRID_COMBINATIONS"
        ),
        "parameter_combinations": 27,
        "direction_mode": "long_only",
        "opening_range_start_new_york": "09:30",
        "opening_range_high": (
            "Maximum high of the complete five-minute "
            "bars inside the candidate opening range."
        ),
        "opening_range_low": (
            "Minimum low of the complete five-minute "
            "bars inside the candidate opening range."
        ),
        "breakout_signal": (
            "First completed five-minute candle closing "
            "strictly above the candidate opening-range "
            "high."
        ),
        "signal_requires_completed_bar": True,
        "signal_price_comparison": (
            "five-minute close > opening-range high"
        ),
        "entry": (
            "Next five-minute bar open after the "
            "completed breakout signal."
        ),
        "entry_uses_actual_open_price": True,
        "entry_gap_filter": "NONE",
        "protective_stop": "Candidate opening-range low.",
        "risk_points": (
            "Actual entry price minus candidate "
            "opening-range low."
        ),
        "invalid_nonpositive_risk_trade": "DO_NOT_ENTER",
        "profit_target": (
            "Actual entry price plus candidate "
            "reward_to_risk times risk_points."
        ),
        "forced_flat_price": (
            "Candidate forced-flat one-minute bar open."
        ),
        "maximum_trades_per_session": 1,
        "same_day_reentry": False,
        "short_entries": False,
        "delta_confirmation": "DISABLED",
        "other_filters": "NONE",
        "overnight_positions": False,
    },
    "parameter_grid": {
        "dimensions": {
            "opening_range_minutes": [15, 30, 45],
            "reward_to_risk": [0.5, 1.0, 1.5],
            "forced_flat_time_new_york": [
                "12:00",
                "14:00",
                "15:55",
            ],
        },
        "combination_count": 27,
        "combinations": EXP008_GRID,
        "exp007_baseline_parameter_key": (
            "or30_target1p0_flat1400"
        ),
        "exp007_baseline_included_exactly_once": True,
        "post_result_grid_changes_prohibited": True,
    },
    "intrabar_execution": {
        "execution_resolution": "1 minute",
        "entry_minute_can_exit": True,
        "evaluate_minutes_in_chronological_order": True,
        "stop_gap_rule": (
            "If a one-minute bar opens at or below "
            "the stop, fill at that opening price."
        ),
        "stop_touch_rule": (
            "Otherwise fill at the stop boundary "
            "when the minute low touches it."
        ),
        "target_gap_rule": (
            "A target gap receives no favourable "
            "price improvement; fill at the target."
        ),
        "target_touch_rule": "Fill at the target boundary.",
        "same_minute_stop_and_target_rule": (
            "STOP_FIRST_CONSERVATIVE"
        ),
        "time_exit_precedence": (
            "A position still open is closed at the "
            "candidate forced-flat one-minute opening "
            "price."
        ),
    },
    "position_sizing": {
        "method": "FIXED_ONE_CONTRACT",
        "NQ_contracts": 1,
        "MNQ_contracts": 1,
        "volatility_targeting_enabled": False,
        "reason": (
            "EXP-008 isolates signal and exit geometry. "
            "Sizing remains a separate future experiment."
        ),
    },
    "contract_and_cost_model": {
        "NQ": {
            "multiplier_usd_per_point": 20.0,
            "tick_size_points": 0.25,
            "fees_usd_per_side": 2.50,
            "base_slippage_ticks_per_side": 1.0,
            "base_round_trip_cost_usd": 15.0,
            "analytical_reference_capital_usd": 100000.0,
        },
        "MNQ": {
            "multiplier_usd_per_point": 2.0,
            "tick_size_points": 0.25,
            "fees_usd_per_side": 1.00,
            "base_slippage_ticks_per_side": 1.0,
            "base_round_trip_cost_usd": 3.0,
            "analytical_reference_capital_usd": 10000.0,
        },
        "cost_sensitivity_ticks_per_side": [0, 1, 2],
        "decision_cost_stress_ticks_per_side": 2,
    },
    "candidate_selection": {
        "selection_market": "NQ",
        "selection_cost_model": (
            "BASE_ONE_TICK_SLIPPAGE_PER_SIDE"
        ),
        "eligibility_all_required": True,
        "minimum_trade_profit_factor_strict": 1.0,
        "minimum_net_profit_usd_strict": 0.0,
        "minimum_completed_trades": 100,
        "neighbor_definition": (
            "Immediate ordered-grid neighbors differ by "
            "one adjacent step in exactly one dimension "
            "and match the other two dimensions."
        ),
        "minimum_profitable_neighbor_fraction": 0.5,
        "minimum_neighbor_median_profit_factor_strict": 1.0,
        "neighbor_profitability_definition": (
            "Neighbor Profit Factor > 1.0 and "
            "neighbor net profit > 0."
        ),
        "primary_rank": (
            "trade_profit_factor descending"
        ),
        "tie_break_1": (
            "net_profit_to_drawdown descending"
        ),
        "tie_break_2": "net_profit_usd descending",
        "tie_break_3": "completed_trades descending",
        "tie_break_4": "parameter_key ascending",
        "no_eligible_candidate_statistic": 0.0,
        "same_procedure_used_in_every_training_fold": True,
        "same_procedure_used_inside_every_permutation": True,
    },
    "anchored_walk_forward": {
        "enabled": True,
        "selection_repeated_in_each_training_window": True,
        "folds": [
            {
                "fold": 1,
                "train_start": "2019-05-06",
                "train_end": "2020-12-31",
                "test_start": "2021-01-01",
                "test_end": "2021-12-31",
            },
            {
                "fold": 2,
                "train_start": "2019-05-06",
                "train_end": "2021-12-31",
                "test_start": "2022-01-01",
                "test_end": "2022-12-31",
            },
            {
                "fold": 3,
                "train_start": "2019-05-06",
                "train_end": "2022-12-31",
                "test_start": "2023-01-01",
                "test_end": "2023-12-31",
            },
            {
                "fold": 4,
                "train_start": "2019-05-06",
                "train_end": "2023-12-31",
                "test_start": "2024-01-01",
                "test_end": "2024-12-31",
            },
            {
                "fold": 5,
                "train_start": "2019-05-06",
                "train_end": "2024-12-31",
                "test_start": "2025-01-01",
                "test_end": "2025-12-31",
            },
        ],
        "fold_count": 5,
        "minimum_profitable_test_folds": 3,
        "combined_test_fold_nq_net_profit_must_be_positive": True,
        "training_end_must_precede_test_start": True,
        "not_claimed_as_untouched_out_of_sample": True,
    },
    "final_selected_candidate_temporal_check": {
        "years": [2021, 2022, 2023, 2024, 2025],
        "minimum_profitable_nq_years": 3,
        "combined_2021_2025_nq_net_profit_must_be_positive": True,
    },
    "selection_aware_mcpt": {
        "enabled": True,
        "primary_market": "NQ",
        "permutations": 1000,
        "random_seed": 48,
        "engine_family": (
            "EXP-005 session-aware one-minute permutation"
        ),
        "all_27_candidates_run_inside_each_permutation": True,
        "candidate_selection_repeated_inside_each_permutation": (
            True
        ),
        "test_statistic": (
            "selected_candidate_trade_profit_factor"
        ),
        "p_value_formula": (
            "(1 + permutation selected PF >= real "
            "selected PF) / (1 + permutations)"
        ),
        "maximum_p_value": 0.05,
        "exact_serial_parallel_parity_required": True,
    },
    "bootstrap_diagnostics": {
        "enabled": True,
        "resamples": 10000,
        "random_seed": 4801,
        "sampling_unit": (
            "completed trade from the final selected NQ "
            "candidate"
        ),
        "reported_intervals": [
            "95% percentile interval for average trade USD",
            "95% percentile interval for trade Profit Factor",
        ],
        "decision_gate": False,
    },
    "historical_decision_gates": {
        "all_required": True,
        "selected_candidate_must_be_neighbor_stable": True,
        "minimum_selected_nq_trade_profit_factor_strict": (
            1.1168167521220216
        ),
        "profit_factor_comparison_baseline": (
            "FROZEN_EXP007_NQ_TRADE_PROFIT_FACTOR"
        ),
        "minimum_selected_nq_net_profit_usd_strict": 0.0,
        "minimum_selected_nq_average_trade_usd_strict": 0.0,
        "minimum_selected_nq_completed_trades": 500,
        "minimum_profitable_final_candidate_nq_years": 3,
        "minimum_combined_2021_2025_final_candidate_nq_net_profit_usd_strict": (
            0.0
        ),
        "minimum_profitable_anchored_test_folds": 3,
        "minimum_combined_anchored_test_fold_nq_net_profit_usd_strict": (
            0.0
        ),
        "maximum_selection_aware_nq_mcpt_p_value": 0.05,
        "minimum_selected_nq_two_tick_stress_net_profit_usd_strict": (
            0.0
        ),
        "minimum_selected_mnq_trade_profit_factor_strict": 1.0,
        "minimum_selected_mnq_net_profit_usd_strict": 0.0,
        "failure_action": (
            "REJECT_EXP008_PRESERVE_AS_NEGATIVE_RESULT"
        ),
        "pass_action": (
            "LOCK_EXP008_EXIT_GEOMETRY_CANDIDATE_FOR_"
            "NEW_FORWARD_PAPER_COMPARISON"
        ),
        "live_trading_authorized": False,
    },
    "reporting_requirements": {
        "vertical_single_column_layout": True,
        "full_width_metric_tables": True,
        "full_width_charts": True,
        "complete_27_candidate_grid_table": True,
        "selected_candidate_equity_curve": True,
        "selected_candidate_drawdown_curve": True,
        "parameter_slice_heatmaps": True,
        "neighbor_stability_table": True,
        "anchored_walk_forward_table": True,
        "annual_results_table": True,
        "cost_sensitivity_table": True,
        "mcpt_distribution_chart": True,
        "bootstrap_interval_table": True,
        "exp007_baseline_comparison": True,
    },
    "future_experiment_boundaries": {
        "volatility_targeted_position_sizing": (
            "SEPARATE_FUTURE_EXPERIMENT_ONLY"
        ),
        "short_side_research": (
            "SEPARATE_FUTURE_EXPERIMENT_ONLY"
        ),
        "delta_confirmation": (
            "NOT_AVAILABLE_IN_FROZEN_OHLCV_DATA"
        ),
    },
    "prohibited_actions": [
        "Changing EXP-005.",
        "Reopening or changing EXP-006.",
        "Reopening or changing EXP-007.",
        "Adding a parameter outside the locked 27-combination grid.",
        "Removing a parameter after seeing any EXP-008 result.",
        "Adding short trades.",
        "Adding delta confirmation.",
        "Adding indicators or discretionary filters.",
        "Applying volatility targeting inside EXP-008.",
        "Selecting a candidate without the locked neighbor checks.",
        "Selecting a candidate using test-year data inside a fold.",
        "Running MCPT without all 27 candidates and selection inside every permutation.",
        "Running fewer than 1,000 NQ permutations.",
        "Changing the random seed after results are viewed.",
        "Changing the historical decision gates after results are viewed.",
        "Claiming 2019-2025 is untouched confirmation data.",
        "Authorizing live trading from historical EXP-008 results.",
    ],
}


def get_exp008_preregistration() -> dict[str, Any]:
    return deepcopy(EXP008_PREREGISTRATION)


def validate_exp008_preregistration(
    record: dict[str, Any] | None = None,
) -> None:
    current = (
        EXP008_PREREGISTRATION
        if record is None
        else record
    )

    if (
        current.get("schema_version") != 1
        or current.get("experiment_id") != "EXP-008"
        or current.get("research_status")
        != "PRE_REGISTERED"
        or current.get("implementation_status")
        != "NOT_RUN"
        or current.get("results_viewed") != "NONE"
    ):
        raise ValueError(
            "EXP-008 preregistration identity or "
            "pre-result state changed."
        )

    relationships = current[
        "experiment_relationships"
    ]
    if (
        relationships["exp005"]["required_stage"]
        != "ACCEPTED_FOR_PAPER_TESTING"
        or relationships["exp005"][
            "must_remain_unchanged"
        ] is not True
        or relationships["exp006"]["required_stage"]
        != "REJECTED"
        or relationships["exp006"][
            "must_remain_unchanged"
        ] is not True
        or relationships["exp007"]["required_stage"]
        != "REJECTED"
        or relationships["exp007"][
            "must_remain_unchanged"
        ] is not True
        or relationships["exp007"][
            "baseline_parameter_key"
        ] != "or30_target1p0_flat1400"
        or relationships["exp007"][
            "baseline_nq_trade_profit_factor"
        ] != 1.1168167521220216
    ):
        raise ValueError(
            "EXP-008 prior-experiment boundary changed."
        )

    interpretation = current["interpretation"]
    if (
        interpretation["historical_status"]
        != "EXPLORATORY_BECAUSE_2019_2025_WAS_ALREADY_VIEWED"
        or interpretation[
            "historical_result_cannot_authorize_live_trading"
        ] is not True
        or interpretation[
            "selection_bias_must_be_included_in_mcpt"
        ] is not True
        or interpretation[
            "exp007_rejection_cannot_be_reinterpreted"
        ] is not True
    ):
        raise ValueError(
            "EXP-008 interpretation boundary changed."
        )

    data = current["market_and_data"]
    if (
        data["primary_evidence_market"] != "NQ"
        or data["secondary_implementation_market"] != "MNQ"
        or data["expected_included_sessions"] != 1639
        or data[
            "reuse_only_frozen_exp005_clean_sessions"
        ] is not True
        or data[
            "new_data_cleaning_decisions_prohibited"
        ] is not True
    ):
        raise ValueError(
            "EXP-008 market/data lock changed."
        )

    shared = current[
        "fixed_rules_shared_by_all_candidates"
    ]
    if (
        shared["optimization_enabled"] is not True
        or shared["parameter_combinations"] != 27
        or shared["direction_mode"] != "long_only"
        or shared["maximum_trades_per_session"] != 1
        or shared["short_entries"] is not False
        or shared["delta_confirmation"] != "DISABLED"
    ):
        raise ValueError(
            "EXP-008 shared strategy rules changed."
        )

    grid = current["parameter_grid"]
    expected_grid = build_exp008_grid()
    if (
        grid["dimensions"]["opening_range_minutes"]
        != [15, 30, 45]
        or grid["dimensions"]["reward_to_risk"]
        != [0.5, 1.0, 1.5]
        or grid["dimensions"][
            "forced_flat_time_new_york"
        ] != ["12:00", "14:00", "15:55"]
        or grid["combination_count"] != 27
        or grid["combinations"] != expected_grid
        or len(
            {
                item["parameter_key"]
                for item in grid["combinations"]
            }
        ) != 27
        or sum(
            item["parameter_key"]
            == "or30_target1p0_flat1400"
            for item in grid["combinations"]
        ) != 1
        or grid[
            "post_result_grid_changes_prohibited"
        ] is not True
    ):
        raise ValueError(
            "EXP-008 parameter grid changed."
        )

    intrabar = current["intrabar_execution"]
    if (
        intrabar["execution_resolution"] != "1 minute"
        or intrabar[
            "evaluate_minutes_in_chronological_order"
        ] is not True
        or intrabar[
            "same_minute_stop_and_target_rule"
        ] != "STOP_FIRST_CONSERVATIVE"
    ):
        raise ValueError(
            "EXP-008 intrabar execution changed."
        )

    sizing = current["position_sizing"]
    if (
        sizing["method"] != "FIXED_ONE_CONTRACT"
        or sizing["NQ_contracts"] != 1
        or sizing["MNQ_contracts"] != 1
        or sizing[
            "volatility_targeting_enabled"
        ] is not False
    ):
        raise ValueError(
            "EXP-008 sizing isolation changed."
        )

    selection = current["candidate_selection"]
    if (
        selection["selection_market"] != "NQ"
        or selection["eligibility_all_required"] is not True
        or selection[
            "minimum_trade_profit_factor_strict"
        ] != 1.0
        or selection["minimum_completed_trades"] != 100
        or selection[
            "minimum_profitable_neighbor_fraction"
        ] != 0.5
        or selection[
            "minimum_neighbor_median_profit_factor_strict"
        ] != 1.0
        or selection["primary_rank"]
        != "trade_profit_factor descending"
        or selection[
            "same_procedure_used_inside_every_permutation"
        ] is not True
    ):
        raise ValueError(
            "EXP-008 candidate-selection procedure changed."
        )

    walk_forward = current["anchored_walk_forward"]
    if (
        walk_forward["enabled"] is not True
        or walk_forward[
            "selection_repeated_in_each_training_window"
        ] is not True
        or walk_forward["fold_count"] != 5
        or len(walk_forward["folds"]) != 5
        or walk_forward[
            "minimum_profitable_test_folds"
        ] != 3
        or walk_forward[
            "training_end_must_precede_test_start"
        ] is not True
        or walk_forward[
            "not_claimed_as_untouched_out_of_sample"
        ] is not True
    ):
        raise ValueError(
            "EXP-008 anchored walk-forward plan changed."
        )

    temporal = current[
        "final_selected_candidate_temporal_check"
    ]
    if (
        temporal["years"]
        != [2021, 2022, 2023, 2024, 2025]
        or temporal[
            "minimum_profitable_nq_years"
        ] != 3
    ):
        raise ValueError(
            "EXP-008 selected-candidate temporal "
            "check changed."
        )

    mcpt = current["selection_aware_mcpt"]
    if (
        mcpt["enabled"] is not True
        or mcpt["primary_market"] != "NQ"
        or mcpt["permutations"] != 1000
        or mcpt["random_seed"] != 48
        or mcpt[
            "all_27_candidates_run_inside_each_permutation"
        ] is not True
        or mcpt[
            "candidate_selection_repeated_inside_each_permutation"
        ] is not True
        or mcpt["test_statistic"]
        != "selected_candidate_trade_profit_factor"
        or mcpt["maximum_p_value"] != 0.05
        or mcpt[
            "exact_serial_parallel_parity_required"
        ] is not True
    ):
        raise ValueError(
            "EXP-008 selection-aware MCPT plan changed."
        )

    bootstrap = current["bootstrap_diagnostics"]
    if (
        bootstrap["enabled"] is not True
        or bootstrap["resamples"] != 10000
        or bootstrap["random_seed"] != 4801
        or bootstrap["decision_gate"] is not False
    ):
        raise ValueError(
            "EXP-008 bootstrap diagnostic changed."
        )

    gates = current["historical_decision_gates"]
    if (
        gates["all_required"] is not True
        or gates[
            "selected_candidate_must_be_neighbor_stable"
        ] is not True
        or gates[
            "minimum_selected_nq_trade_profit_factor_strict"
        ] != 1.1168167521220216
        or gates[
            "minimum_selected_nq_completed_trades"
        ] != 500
        or gates[
            "minimum_profitable_final_candidate_nq_years"
        ] != 3
        or gates[
            "minimum_profitable_anchored_test_folds"
        ] != 3
        or gates[
            "maximum_selection_aware_nq_mcpt_p_value"
        ] != 0.05
        or gates[
            "minimum_selected_mnq_trade_profit_factor_strict"
        ] != 1.0
        or gates["failure_action"]
        != "REJECT_EXP008_PRESERVE_AS_NEGATIVE_RESULT"
        or gates["pass_action"]
        != (
            "LOCK_EXP008_EXIT_GEOMETRY_CANDIDATE_FOR_"
            "NEW_FORWARD_PAPER_COMPARISON"
        )
        or gates["live_trading_authorized"] is not False
    ):
        raise ValueError(
            "EXP-008 historical decision gates changed."
        )

    prohibited = " ".join(
        current["prohibited_actions"]
    ).lower()
    for phrase in (
        "changing exp-005",
        "changing exp-006",
        "changing exp-007",
        "locked 27-combination grid",
        "adding short",
        "delta confirmation",
        "volatility targeting",
        "selection inside every permutation",
        "1,000 nq permutations",
        "decision gates",
        "untouched confirmation",
        "live trading",
    ):
        if phrase not in prohibited:
            raise ValueError(
                "EXP-008 prohibition missing: "
                f"{phrase}."
            )
