from __future__ import annotations

from copy import deepcopy
from typing import Any


SIGNAL_VARIANTS: tuple[dict[str, Any], ...] = (
    {
        "candidate_id": "opening_drive_0p5_time",
        "role": "PRIMARY_MEASUREMENT_LEADER",
    },
    {
        "candidate_id": "opening_drive_0p5_1p5r",
        "role": "USER_REFERENCE",
    },
)

SIZING_METHODS: tuple[dict[str, Any], ...] = (
    {
        "sizing_id": "fixed_one_nq",
        "instrument": "NQ",
        "contract_rule": "Always one NQ contract.",
        "implementation_status": "IMPLEMENTABLE",
    },
    {
        "sizing_id": "fractional_nq_equal_risk",
        "instrument": "NQ",
        "contract_rule": (
            "Target risk divided by current one-NQ initial risk, capped "
            "at 2.0 NQ contracts."
        ),
        "implementation_status": "THEORETICAL_FRACTIONAL_ONLY",
    },
    {
        "sizing_id": "integer_mnq_equal_risk",
        "instrument": "MNQ",
        "contract_rule": (
            "Floor target risk divided by current one-MNQ initial risk; "
            "allow zero and cap at 20 MNQ contracts."
        ),
        "implementation_status": "IMPLEMENTABLE",
    },
)


EXP011_PREREGISTRATION: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-011",
    "title": "NQ/MNQ Opening-Drive Position-Sizing Study",
    "locked_date": "2026-07-20",
    "research_status": "PRE_REGISTERED",
    "implementation_status": "NOT_RUN",
    "results_viewed": "NONE",
    "purpose": (
        "Measure whether equal-dollar-risk sizing makes the frozen EXP-010 "
        "opening-drive strategies' trade risk and drawdown more consistent "
        "without changing their entry, stop or exit rules."
    ),
    "research_question": (
        "Compared with fixed one-contract NQ exposure, how do theoretical "
        "fractional NQ and implementable integer MNQ equal-risk sizing change "
        "profitability, drawdown, risk dispersion and practical trade behaviour?"
    ),
    "relationship_to_exp010": {
        "required_exp010_stage": "REVIEW",
        "exp010_result_must_match_frozen_hashes": True,
        "required_exp010_classification": "STRONG_HISTORICAL_EVIDENCE",
        "primary_signal_candidate": "opening_drive_0p5_time",
        "user_reference_candidate": "opening_drive_0p5_1p5r",
        "both_signal_variants_remain_visible": True,
        "signal_selection_prohibited": True,
        "entry_stop_and_exit_rule_changes_prohibited": True,
        "position_sizing_cannot_establish_signal_edge": True,
        "historical_status": (
            "EXPLORATORY_SIZING_STUDY_ON_PREVIOUSLY_VIEWED_2019_2025_DATA"
        ),
        "cannot_claim_independent_confirmation": True,
    },
    "signal_lock": {
        "variant_count": 2,
        "variants": SIGNAL_VARIANTS,
        "minimum_drive_fraction": 0.5,
        "measurement_window": "09:30-10:00 New York",
        "direction": "Sign of first-30-minute close minus open.",
        "entry": "10:00 five-minute bar open.",
        "stop": "Opposite side of first 30-minute opening range.",
        "primary_exit": "Stop or 15:55 one-minute bar open.",
        "reference_exit": "Stop, 1.5R target or 15:55 one-minute bar open.",
        "maximum_trades_per_session": 1,
        "new_signal_parameters_prohibited": True,
    },
    "market_and_data": {
        "primary_fixed_baseline_market": "NQ",
        "practical_sizing_market": "MNQ",
        "source": (
            "Frozen EXP-005 Quantower/Lucid-Rithmic NQ and MNQ datasets"
        ),
        "historical_start": "2019-05-06",
        "historical_end": "2025-12-31",
        "expected_included_sessions": 1639,
        "calibration_period": "2019-05-06 through 2020-12-31",
        "evaluation_period": "2021-01-04 through 2025-12-31",
        "calibration_sessions_are_not_in_evaluation_metrics": True,
        "source_timeframe": "1 minute",
        "signal_timeframe": "5 minutes",
        "research_timezone": "America/New_York",
        "reuse_only_frozen_exp005_clean_sessions": True,
        "new_data_cleaning_decisions_prohibited": True,
        "raw_source_editing_prohibited": True,
        "data_previously_viewed": True,
    },
    "risk_target_calibration": {
        "enabled": True,
        "calibration_signal": "opening_drive_0p5_time",
        "calibration_market": "NQ",
        "calibration_period": "2019-05-06 through 2020-12-31",
        "per_contract_initial_risk_definition": (
            "Absolute actual entry minus stop distance times NQ point "
            "value, plus locked base round-trip cost."
        ),
        "target_dollar_risk_rule": (
            "Median valid one-NQ initial risk across calibration trades."
        ),
        "target_risk_is_calculated_once_then_frozen": True,
        "same_target_used_for_both_signal_variants": True,
        "target_risk_optimization_prohibited": True,
        "account_risk_percentage_optimization_prohibited": True,
        "evaluation_data_cannot_set_target": True,
    },
    "sizing_lock": {
        "method_count": 3,
        "methods": SIZING_METHODS,
        "fractional_nq_max_contracts": 2.0,
        "integer_mnq_rounding": "FLOOR",
        "integer_mnq_min_contracts": 0,
        "integer_mnq_max_contracts": 20,
        "zero_contract_action": "SKIP_TRADE_AND_RECORD_REASON",
        "contract_count_known_at_entry": True,
        "future_price_information_prohibited": True,
        "equity_compounding_enabled": False,
        "risk_target_remains_constant_dollars": True,
        "costs_scale_with_contract_count": True,
        "margin_model_enabled": False,
        "fixed_one_nq_is_baseline_not_selection_candidate": True,
        "automatic_sizing_winner": False,
    },
    "execution_and_costs": {
        "reuse_exp010_signal_and_one_minute_execution": True,
        "evaluate_exit_minutes_chronologically": True,
        "entry_minute_can_exit": True,
        "same_minute_stop_and_target_rule": "STOP_FIRST_CONSERVATIVE",
        "base_slippage_ticks_per_side": 1,
        "nq_round_trip_cost_usd": 15.0,
        "mnq_round_trip_cost_usd": 3.0,
        "costs_applied_per_contract": True,
        "no_new_fill_assumptions": True,
    },
    "measurement_plan": {
        "signal_variants": 2,
        "sizing_methods": 3,
        "total_measurement_rows": 6,
        "all_rows_reported": True,
        "primary_comparison": (
            "Within each signal variant, compare sizing methods; do not "
            "select a signal variant from EXP-011."
        ),
        "performance_metrics": [
            "net_profit_usd",
            "trade_profit_factor",
            "average_trade_usd",
            "win_rate",
            "completed_trades",
            "skipped_zero_size_trades",
        ],
        "risk_metrics": [
            "maximum_drawdown_usd",
            "net_profit_to_maximum_drawdown",
            "average_initial_risk_usd",
            "initial_risk_standard_deviation_usd",
            "initial_risk_coefficient_of_variation",
            "95th_percentile_initial_risk_usd",
            "maximum_initial_risk_usd",
            "maximum_consecutive_losses",
            "worst_20_trade_result_usd",
            "worst_50_trade_result_usd",
        ],
        "practical_metrics": [
            "average_contracts",
            "median_contracts",
            "maximum_contracts",
            "zero_contract_skip_rate",
            "average_holding_minutes",
            "annual_net_profit",
            "monthly_net_profit",
            "cost_total_usd",
        ],
        "normalized_reference_capital_usd": 100000.0,
        "strategy_vs_normalized_nq_benchmark": True,
        "no_single_composite_score": True,
        "pareto_context_only": True,
        "no_pass_fail_gate": True,
    },
    "paired_bootstrap_diagnostics": {
        "enabled": True,
        "resamples": 10000,
        "random_seed": 5111,
        "sampling_unit": "evaluation_session",
        "paired_by_session": True,
        "comparisons": [
            "fractional_nq_equal_risk minus fixed_one_nq",
            "integer_mnq_equal_risk normalized to NQ dollars minus fixed_one_nq",
        ],
        "reported_intervals": [
            "mean_session_pnl_difference_95_percentile_interval",
            "mean_absolute_risk_difference_95_percentile_interval",
        ],
        "decision_gate": False,
        "does_not_confirm_signal_edge": True,
    },
    "statistical_scope": {
        "new_mcpt_enabled": False,
        "reason_no_new_mcpt": (
            "EXP-011 does not test a new entry signal and must not reuse "
            "position sizing to make a new alpha-significance claim."
        ),
        "exp010_mcpt_reported_as_signal_context_only": True,
        "selection_adjustment_not_applicable_because_no_sizing_winner": True,
        "independent_confirmation": False,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
    },
    "reporting_requirements": {
        "plain_english_strategy_and_sizing_explanation": True,
        "worked_contract_sizing_example": True,
        "primary_and_reference_signal_variants_visible": True,
        "all_six_measurement_rows_visible": True,
        "fixed_vs_fractional_vs_integer_equity": True,
        "drawdown_comparison": True,
        "initial_risk_distribution": True,
        "contract_count_distribution": True,
        "annual_and_monthly_comparison": True,
        "paired_bootstrap_intervals": True,
        "cost_and_skipped_trade_context": True,
        "positive_numbers_use_neutral_text": True,
        "adverse_numbers_use_red_text": True,
        "green_reserved_for_status_words": True,
    },
    "prohibited_actions": [
        "Changing either frozen EXP-010 signal variant.",
        "Adding a signal filter, entry, stop, target or time-exit parameter.",
        "Optimizing the target dollar risk or account risk percentage.",
        "Using 2021-2025 evaluation data to calibrate target risk.",
        "Compounding position size from historical profits.",
        "Changing the fixed costs, slippage or stop-first execution rule.",
        "Hiding zero-size skipped trades or unfavorable sizing measurements.",
        "Selecting one signal variant as a result of EXP-011.",
        "Declaring a sizing winner with a composite score.",
        "Claiming position sizing proves the opening-drive signal edge.",
        "Calling EXP-011 independent confirmation.",
        "Authorizing paper or live trading from EXP-011.",
    ],
}


def get_exp011_preregistration() -> dict[str, Any]:
    return deepcopy(EXP011_PREREGISTRATION)


def validate_exp011_preregistration(
    record: dict[str, Any] | None = None,
) -> None:
    current = EXP011_PREREGISTRATION if record is None else record

    if (
        current.get("schema_version") != 1
        or current.get("experiment_id") != "EXP-011"
        or current.get("research_status") != "PRE_REGISTERED"
        or current.get("implementation_status") != "NOT_RUN"
        or current.get("results_viewed") != "NONE"
    ):
        raise ValueError("EXP-011 identity or pre-result state changed.")

    relationship = current["relationship_to_exp010"]
    if (
        relationship["required_exp010_stage"] != "REVIEW"
        or relationship["exp010_result_must_match_frozen_hashes"] is not True
        or relationship["required_exp010_classification"]
        != "STRONG_HISTORICAL_EVIDENCE"
        or relationship["primary_signal_candidate"]
        != "opening_drive_0p5_time"
        or relationship["user_reference_candidate"]
        != "opening_drive_0p5_1p5r"
        or relationship["both_signal_variants_remain_visible"] is not True
        or relationship["signal_selection_prohibited"] is not True
        or relationship["position_sizing_cannot_establish_signal_edge"]
        is not True
        or relationship["cannot_claim_independent_confirmation"] is not True
    ):
        raise ValueError("EXP-011 relationship to EXP-010 changed.")

    signal = current["signal_lock"]
    if (
        signal["variant_count"] != 2
        or tuple(signal["variants"]) != SIGNAL_VARIANTS
        or signal["minimum_drive_fraction"] != 0.5
        or signal["entry"] != "10:00 five-minute bar open."
        or signal["maximum_trades_per_session"] != 1
        or signal["new_signal_parameters_prohibited"] is not True
    ):
        raise ValueError("EXP-011 signal lock changed.")

    data = current["market_and_data"]
    if (
        data["expected_included_sessions"] != 1639
        or data["calibration_period"]
        != "2019-05-06 through 2020-12-31"
        or data["evaluation_period"]
        != "2021-01-04 through 2025-12-31"
        or data["calibration_sessions_are_not_in_evaluation_metrics"]
        is not True
        or data["reuse_only_frozen_exp005_clean_sessions"] is not True
        or data["new_data_cleaning_decisions_prohibited"] is not True
        or data["data_previously_viewed"] is not True
    ):
        raise ValueError("EXP-011 market/data split changed.")

    calibration = current["risk_target_calibration"]
    if (
        calibration["enabled"] is not True
        or calibration["calibration_signal"]
        != "opening_drive_0p5_time"
        or calibration["calibration_market"] != "NQ"
        or calibration["target_dollar_risk_rule"]
        != "Median valid one-NQ initial risk across calibration trades."
        or calibration["target_risk_is_calculated_once_then_frozen"]
        is not True
        or calibration["same_target_used_for_both_signal_variants"] is not True
        or calibration["target_risk_optimization_prohibited"] is not True
        or calibration["account_risk_percentage_optimization_prohibited"]
        is not True
        or calibration["evaluation_data_cannot_set_target"] is not True
    ):
        raise ValueError("EXP-011 risk-target calibration changed.")

    sizing = current["sizing_lock"]
    if (
        sizing["method_count"] != 3
        or tuple(sizing["methods"]) != SIZING_METHODS
        or sizing["fractional_nq_max_contracts"] != 2.0
        or sizing["integer_mnq_rounding"] != "FLOOR"
        or sizing["integer_mnq_min_contracts"] != 0
        or sizing["integer_mnq_max_contracts"] != 20
        or sizing["zero_contract_action"] != "SKIP_TRADE_AND_RECORD_REASON"
        or sizing["contract_count_known_at_entry"] is not True
        or sizing["future_price_information_prohibited"] is not True
        or sizing["equity_compounding_enabled"] is not False
        or sizing["costs_scale_with_contract_count"] is not True
        or sizing["automatic_sizing_winner"] is not False
    ):
        raise ValueError("EXP-011 sizing lock changed.")

    execution = current["execution_and_costs"]
    if (
        execution["reuse_exp010_signal_and_one_minute_execution"] is not True
        or execution["same_minute_stop_and_target_rule"]
        != "STOP_FIRST_CONSERVATIVE"
        or execution["base_slippage_ticks_per_side"] != 1
        or execution["nq_round_trip_cost_usd"] != 15.0
        or execution["mnq_round_trip_cost_usd"] != 3.0
        or execution["costs_applied_per_contract"] is not True
    ):
        raise ValueError("EXP-011 execution/cost lock changed.")

    measurement = current["measurement_plan"]
    if (
        measurement["signal_variants"] != 2
        or measurement["sizing_methods"] != 3
        or measurement["total_measurement_rows"] != 6
        or measurement["all_rows_reported"] is not True
        or measurement["no_single_composite_score"] is not True
        or measurement["pareto_context_only"] is not True
        or measurement["no_pass_fail_gate"] is not True
    ):
        raise ValueError("EXP-011 measurement plan changed.")

    bootstrap = current["paired_bootstrap_diagnostics"]
    if (
        bootstrap["enabled"] is not True
        or bootstrap["resamples"] != 10000
        or bootstrap["random_seed"] != 5111
        or bootstrap["sampling_unit"] != "evaluation_session"
        or bootstrap["paired_by_session"] is not True
        or bootstrap["decision_gate"] is not False
        or bootstrap["does_not_confirm_signal_edge"] is not True
    ):
        raise ValueError("EXP-011 paired bootstrap plan changed.")

    scope = current["statistical_scope"]
    if (
        scope["new_mcpt_enabled"] is not False
        or scope["exp010_mcpt_reported_as_signal_context_only"] is not True
        or scope["independent_confirmation"] is not False
        or scope["paper_trading_authorized"] is not False
        or scope["live_trading_authorized"] is not False
    ):
        raise ValueError("EXP-011 statistical scope changed.")

    reporting = current["reporting_requirements"]
    if (
        reporting["plain_english_strategy_and_sizing_explanation"] is not True
        or reporting["all_six_measurement_rows_visible"] is not True
        or reporting["positive_numbers_use_neutral_text"] is not True
        or reporting["adverse_numbers_use_red_text"] is not True
        or reporting["green_reserved_for_status_words"] is not True
    ):
        raise ValueError("EXP-011 reporting standard changed.")

    prohibited = " ".join(current["prohibited_actions"]).lower()
    for phrase in (
        "changing either frozen exp-010",
        "optimizing the target dollar risk",
        "evaluation data to calibrate",
        "compounding position size",
        "hiding zero-size",
        "selecting one signal variant",
        "composite score",
        "proves the opening-drive signal edge",
        "independent confirmation",
        "paper or live trading",
    ):
        if phrase not in prohibited:
            raise ValueError(f"EXP-011 prohibition missing: {phrase}.")


if __name__ == "__main__":
    validate_exp011_preregistration()
    print("EXP-011 preregistration is valid.")
