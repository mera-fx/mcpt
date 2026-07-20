from __future__ import annotations

from copy import deepcopy
from typing import Any


FINALIST_IDS: tuple[str, ...] = (
    "gap_fade_0p50_1r",
    "premarket_continuation_0p50_time",
    "premarket_continuation_0p75_time",
)

PAIR_DEFINITIONS: tuple[dict[str, Any], ...] = (
    {
        "pair_id": "gap_fade_plus_premarket_0p50",
        "first_candidate_id": "gap_fade_0p50_1r",
        "second_candidate_id": "premarket_continuation_0p50_time",
        "contracts_per_active_sleeve": 1,
    },
    {
        "pair_id": "gap_fade_plus_premarket_0p75",
        "first_candidate_id": "gap_fade_0p50_1r",
        "second_candidate_id": "premarket_continuation_0p75_time",
        "contracts_per_active_sleeve": 1,
    },
)


EXP014_PREREGISTRATION: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-014",
    "title": "Finalist Behaviour and Complementarity Study",
    "locked_date": "2026-07-20",
    "research_status": "PRE_REGISTERED",
    "implementation_status": "NOT_RUN",
    "results_viewed": "NONE",
    "purpose": (
        "Explain how the three frozen EXP-013 finalists behave, why "
        "their results differ, what weakened in 2025, and whether gap "
        "fade and premarket continuation provide complementary P&L."
    ),
    "research_question": (
        "Which measured behaviours, regimes, overlaps and tail outcomes "
        "explain the trade-offs among the three finalists, and do the two "
        "locked cross-family sleeve pairs improve consistency or drawdown?"
    ),
    "relationship_to_exp013": {
        "required_exp013_stage": "REVIEW",
        "exp013_result_must_match_frozen_hashes": True,
        "source_finalist_count": 3,
        "source_classification": "STRONG_HISTORICAL_EVIDENCE",
        "finalists_selected_after_exp012_results": True,
        "independent_confirmation": False,
        "new_alpha_claim": False,
        "existing_exp013_mcpt_reused_not_rerun": True,
        "existing_exp013_bootstrap_reused_not_rerun": True,
        "existing_exp013_walk_forward_reused_not_rerun": True,
    },
    "candidate_lock": {
        "candidate_ids": FINALIST_IDS,
        "candidate_count": 3,
        "strategy_rules_changed": False,
        "parameters_changed": False,
        "entries_changed": False,
        "stops_changed": False,
        "targets_changed": False,
        "time_exits_changed": False,
        "costs_changed": False,
        "position_sizing_changed": False,
        "new_filter_or_regime_rule_prohibited": True,
    },
    "market_and_data": {
        "primary_market": "NQ",
        "secondary_context_market": "MNQ",
        "source": "Frozen EXP-012 extended-session datasets",
        "historical_start": "2020-01-03",
        "historical_end": "2025-12-31",
        "included_sessions": 1331,
        "source_timeframe": "1 minute",
        "signal_timeframe": "5 minutes",
        "research_timezone": "America/New_York",
        "cash_session_entries_only": True,
        "new_data_cleaning_decisions": 0,
        "raw_source_editing_prohibited": True,
    },
    "trade_reconstruction": {
        "rerun_exact_locked_candidates_for_trade_ledgers": True,
        "same_exp012_engine": True,
        "same_one_minute_execution": True,
        "same_base_costs": True,
        "fixed_one_contract": True,
        "same_minute_stop_target_rule": "STOP_FIRST_CONSERVATIVE",
        "summary_must_match_exp013_candidate_measurements": True,
        "mismatch_action": "STOP_WITHOUT_WRITING_FINAL_RESULT",
    },
    "behaviour_measurements": {
        "standalone_candidate_table": True,
        "calendar_years": [2020, 2021, 2022, 2023, 2024, 2025],
        "focus_year": 2025,
        "focus_comparisons": ["2020-2024", "2022-2024"],
        "direction_breakdown": ["LONG", "SHORT"],
        "exit_reason_breakdown": True,
        "holding_time_bins_minutes": [0, 15, 60, 180, 391],
        "context_strength_breakdown": {
            "gap_fraction_edges": [0.50, 0.75, 1.00, "infinity"],
            "premarket_fraction_edges": [
                0.50,
                0.625,
                0.75,
                0.875,
                1.0000001,
            ],
        },
        "entry_known_trend_regime": {
            "measure": "prior_20_session_close_to_close_return",
            "labels": ["DOWN_OR_FLAT", "UP"],
            "boundary": 0.0,
            "current_session_excluded": True,
        },
        "entry_known_volatility_regime": {
            "measure": "prior_20_session_close_return_standard_deviation",
            "calibration_period": "2020-01-03 through 2021-12-31",
            "boundary": "calibration_period_median",
            "labels": ["LOW", "HIGH"],
            "current_session_excluded": True,
            "boundary_reported": True,
        },
        "monthly_and_rolling_measurements": True,
        "entry_and_exit_time_distributions": True,
        "maximum_favourable_and_adverse_excursion": True,
    },
    "failure_and_concentration": {
        "explain_2025_from_trade_components": True,
        "compare_trade_count_win_rate_payoff_and_exit_mix": True,
        "remove_best_trade_counts": [1, 5, 10],
        "top_profit_shares_percent": [1, 5, 10],
        "worst_consecutive_trade_windows": [20, 50, 100],
        "maximum_losing_streak": True,
        "drawdown_duration_and_recovery": True,
        "diagnostic_only": True,
    },
    "overlap_and_dependence": {
        "all_three_pairwise_comparisons": True,
        "calendar_axis": "all_1331_included_sessions_with_zero_on_no_trade",
        "session_pnl_pearson_correlation": True,
        "active_overlap_count": True,
        "same_direction_overlap_count": True,
        "opposite_direction_overlap_count": True,
        "both_win_both_lose_and_offset_counts": True,
        "simultaneous_underwater_share": True,
        "drawdown_correlation": True,
        "no_causality_claim": True,
    },
    "sleeve_pair_comparison": {
        "pairs": PAIR_DEFINITIONS,
        "pair_count": 2,
        "one_contract_per_active_sleeve": True,
        "maximum_gross_contracts": 2,
        "same_instrument_opposite_signals_may_offset": True,
        "arithmetic_research_sleeves_not_single_netting_account": True,
        "no_weights": True,
        "no_weight_optimization": True,
        "no_pair_selection": True,
        "nested_premarket_candidates_never_combined": True,
        "all_three_candidates_never_combined": True,
        "measurements": [
            "net_profit_usd",
            "maximum_drawdown_usd",
            "net_profit_to_drawdown",
            "profitable_years",
            "profitable_months",
            "worst_year_usd",
            "worst_month_usd",
            "session_profit_factor",
            "session_win_rate",
        ],
        "diagnostic_not_executable_portfolio": True,
    },
    "result_interpretation": {
        "measurement_first": True,
        "no_pass_fail_gates": True,
        "no_composite_score": True,
        "no_automatic_winner": True,
        "no_strategy_parameter_selection": True,
        "no_regime_filter_selection": True,
        "expected_lifecycle_after_measurement": "REVIEW",
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
    },
    "reporting_requirements": {
        "plain_english_strategy_rules_and_fraction_examples": True,
        "plain_english_what_how_happened_why": True,
        "all_three_candidates_visible": True,
        "two_sleeve_pairs_visible": True,
        "2025_failure_decomposition": True,
        "standalone_and_pair_equity_vs_normalized_nq": True,
        "standalone_and_pair_drawdown": True,
        "overlap_matrix": True,
        "pnl_correlation_heatmap": True,
        "regime_heatmaps": True,
        "annual_monthly_direction_exit_and_tail_visuals": True,
        "exp013_mcpt_bootstrap_and_walk_forward_context_retained": True,
        "positive_numbers_use_neutral_text": True,
        "adverse_numbers_use_red_text": True,
        "green_reserved_for_status_words": True,
        "charts_use_solid_opaque_white_canvas": True,
    },
    "prohibited_actions": [
        "Changing any EXP-013 strategy rule or parameter.",
        "Searching for or selecting a new context threshold.",
        "Turning a descriptive regime into a trading filter.",
        "Optimizing portfolio weights or pair membership.",
        "Combining the nested 0.50 and 0.75 premarket candidates.",
        "Treating arithmetic research sleeves as an executable account.",
        "Rerunning EXP-013 MCPT, bootstrap or walk-forward selection.",
        "Hiding the 2025 losing fold or the 88-trade warning.",
        "Claiming independent confirmation or trading authorization.",
    ],
}


def get_exp014_preregistration() -> dict[str, Any]:
    return deepcopy(EXP014_PREREGISTRATION)


def validate_exp014_preregistration(
    record: dict[str, Any] | None = None,
) -> None:
    current = EXP014_PREREGISTRATION if record is None else record
    if (
        current.get("schema_version") != 1
        or current.get("experiment_id") != "EXP-014"
        or current.get("research_status") != "PRE_REGISTERED"
        or current.get("implementation_status") != "NOT_RUN"
        or current.get("results_viewed") != "NONE"
    ):
        raise ValueError("EXP-014 identity or pre-result state changed.")

    relationship = current["relationship_to_exp013"]
    if (
        relationship["required_exp013_stage"] != "REVIEW"
        or relationship["exp013_result_must_match_frozen_hashes"] is not True
        or relationship["source_finalist_count"] != 3
        or relationship["source_classification"]
        != "STRONG_HISTORICAL_EVIDENCE"
        or relationship["finalists_selected_after_exp012_results"]
        is not True
        or relationship["independent_confirmation"] is not False
        or relationship["new_alpha_claim"] is not False
        or relationship["existing_exp013_mcpt_reused_not_rerun"]
        is not True
        or relationship["existing_exp013_bootstrap_reused_not_rerun"]
        is not True
        or relationship["existing_exp013_walk_forward_reused_not_rerun"]
        is not True
    ):
        raise ValueError("EXP-014 relationship to EXP-013 changed.")

    lock = current["candidate_lock"]
    if (
        tuple(lock["candidate_ids"]) != FINALIST_IDS
        or lock["candidate_count"] != 3
        or any(
            lock[field]
            for field in (
                "strategy_rules_changed",
                "parameters_changed",
                "entries_changed",
                "stops_changed",
                "targets_changed",
                "time_exits_changed",
                "costs_changed",
                "position_sizing_changed",
            )
        )
        or lock["new_filter_or_regime_rule_prohibited"] is not True
    ):
        raise ValueError("EXP-014 candidate lock changed.")

    data = current["market_and_data"]
    if (
        data["historical_start"] != "2020-01-03"
        or data["historical_end"] != "2025-12-31"
        or data["included_sessions"] != 1331
        or data["cash_session_entries_only"] is not True
        or data["new_data_cleaning_decisions"] != 0
    ):
        raise ValueError("EXP-014 frozen data scope changed.")

    reconstruction = current["trade_reconstruction"]
    if (
        reconstruction[
            "rerun_exact_locked_candidates_for_trade_ledgers"
        ]
        is not True
        or reconstruction["same_exp012_engine"] is not True
        or reconstruction["same_base_costs"] is not True
        or reconstruction["fixed_one_contract"] is not True
        or reconstruction["summary_must_match_exp013_candidate_measurements"]
        is not True
        or reconstruction["mismatch_action"]
        != "STOP_WITHOUT_WRITING_FINAL_RESULT"
    ):
        raise ValueError("EXP-014 reconstruction lock changed.")

    behaviour = current["behaviour_measurements"]
    if (
        behaviour["calendar_years"]
        != [2020, 2021, 2022, 2023, 2024, 2025]
        or behaviour["focus_year"] != 2025
        or behaviour["focus_comparisons"]
        != ["2020-2024", "2022-2024"]
        or behaviour["holding_time_bins_minutes"]
        != [0, 15, 60, 180, 391]
        or behaviour["entry_known_trend_regime"][
            "current_session_excluded"
        ]
        is not True
        or behaviour["entry_known_volatility_regime"][
            "calibration_period"
        ]
        != "2020-01-03 through 2021-12-31"
        or behaviour["entry_known_volatility_regime"][
            "current_session_excluded"
        ]
        is not True
    ):
        raise ValueError("EXP-014 behaviour analysis changed.")

    overlap = current["overlap_and_dependence"]
    if (
        overlap["all_three_pairwise_comparisons"] is not True
        or "1331" not in overlap["calendar_axis"]
        or overlap["session_pnl_pearson_correlation"] is not True
        or overlap["opposite_direction_overlap_count"] is not True
        or overlap["simultaneous_underwater_share"] is not True
        or overlap["no_causality_claim"] is not True
    ):
        raise ValueError("EXP-014 dependence analysis changed.")

    pairs = current["sleeve_pair_comparison"]
    if (
        tuple(pairs["pairs"]) != PAIR_DEFINITIONS
        or pairs["pair_count"] != 2
        or pairs["one_contract_per_active_sleeve"] is not True
        or pairs["maximum_gross_contracts"] != 2
        or pairs["arithmetic_research_sleeves_not_single_netting_account"]
        is not True
        or pairs["no_weights"] is not True
        or pairs["no_weight_optimization"] is not True
        or pairs["no_pair_selection"] is not True
        or pairs["nested_premarket_candidates_never_combined"] is not True
        or pairs["all_three_candidates_never_combined"] is not True
        or pairs["diagnostic_not_executable_portfolio"] is not True
    ):
        raise ValueError("EXP-014 sleeve-pair lock changed.")

    interpretation = current["result_interpretation"]
    if (
        interpretation["measurement_first"] is not True
        or interpretation["no_pass_fail_gates"] is not True
        or interpretation["no_composite_score"] is not True
        or interpretation["no_automatic_winner"] is not True
        or interpretation["no_strategy_parameter_selection"] is not True
        or interpretation["no_regime_filter_selection"] is not True
        or interpretation["expected_lifecycle_after_measurement"] != "REVIEW"
        or interpretation["paper_trading_authorized"] is not False
        or interpretation["live_trading_authorized"] is not False
    ):
        raise ValueError("EXP-014 interpretation boundary changed.")

    reporting = current["reporting_requirements"]
    if (
        reporting["plain_english_strategy_rules_and_fraction_examples"]
        is not True
        or reporting["2025_failure_decomposition"] is not True
        or reporting["overlap_matrix"] is not True
        or reporting["pnl_correlation_heatmap"] is not True
        or reporting["positive_numbers_use_neutral_text"] is not True
        or reporting["adverse_numbers_use_red_text"] is not True
        or reporting["green_reserved_for_status_words"] is not True
        or reporting["charts_use_solid_opaque_white_canvas"] is not True
    ):
        raise ValueError("EXP-014 reporting standard changed.")


if __name__ == "__main__":
    validate_exp014_preregistration()
    print("EXP-014 preregistration is valid and result-free.")
