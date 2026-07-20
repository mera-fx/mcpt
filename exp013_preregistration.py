from __future__ import annotations

from copy import deepcopy
from typing import Any


FINALIST_CANDIDATES: tuple[dict[str, Any], ...] = (
    {
        "candidate_id": "gap_fade_0p50_1r",
        "family_id": "gap_fade",
        "minimum_gap_fraction": 0.50,
        "exit_mode": "1r_or_time",
        "review_reason": (
            "Best fit for the user's stated preference for higher win "
            "rate and lower drawdown."
        ),
        "known_limitation": (
            "Selected after viewing all 24 EXP-012 measurements."
        ),
    },
    {
        "candidate_id": "premarket_continuation_0p50_time",
        "family_id": "premarket_momentum_continuation",
        "minimum_drive_fraction": 0.50,
        "exit_mode": "time",
        "review_reason": (
            "Strongest broader-sample performance among the measured "
            "extended-context candidates."
        ),
        "known_limitation": (
            "Selected after viewing all 24 EXP-012 measurements."
        ),
    },
    {
        "candidate_id": "premarket_continuation_0p75_time",
        "family_id": "premarket_momentum_continuation",
        "minimum_drive_fraction": 0.75,
        "exit_mode": "time",
        "review_reason": (
            "Strongest raw Profit Factor and net-profit-to-drawdown "
            "measurement in EXP-012."
        ),
        "known_limitation": (
            "Only 88 NQ trades in EXP-012 and selected after viewing all "
            "24 measurements."
        ),
    },
)


EXP013_PREREGISTRATION: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-013",
    "title": "Extended-Context Three-Finalist Deep Validation",
    "locked_date": "2026-07-20",
    "research_status": "PRE_REGISTERED",
    "implementation_status": "NOT_RUN",
    "results_viewed": "NONE",
    "purpose": (
        "Deeply measure three explicitly justified EXP-012 review "
        "candidates with anchored walk-forward selection, bootstrap "
        "uncertainty, cost and market checks, and discovery-wide MCPT."
    ),
    "research_question": (
        "Do the gap-fade and premarket-continuation review candidates "
        "retain attractive performance, risk and consistency after "
        "temporal testing and a permutation test that repeats the full "
        "24-candidate Profit-Factor search?"
    ),
    "relationship_to_exp012": {
        "required_exp012_stage": "REVIEW",
        "exp012_result_must_match_frozen_hashes": True,
        "source_candidate_count": 24,
        "review_candidate_count": 3,
        "review_candidates_selected_after_results": True,
        "selection_reasons_are_post_result_judgments": True,
        "preference_is_not_independent_preselection": True,
        "discovery_wide_mcpt_repeats_all_24_candidates": True,
        "discovery_wide_mcpt_statistic": (
            "maximum_trade_profit_factor_across_all_24_candidates"
        ),
        "mcpt_cannot_erase_post_result_rule_design": True,
        "historical_status": (
            "EXPLORATORY_DEEP_VALIDATION_BECAUSE_EXP012_RESULTS_AND_"
            "FINALIST_SELECTION_WERE_ALREADY_VIEWED"
        ),
        "cannot_claim_independent_confirmation": True,
    },
    "candidate_lock": {
        "candidate_count": 3,
        "candidates": FINALIST_CANDIDATES,
        "families": (
            "gap_fade",
            "premarket_momentum_continuation",
        ),
        "new_parameters_prohibited": True,
        "candidate_additions_prohibited": True,
        "candidate_removals_prohibited": True,
        "selection_reasons_must_remain_visible": True,
        "low_sample_warning_must_remain_visible": True,
    },
    "market_and_data": {
        "primary_market": "NQ",
        "secondary_implementation_market": "MNQ",
        "secondary_is_independent_confirmation": False,
        "source": (
            "Frozen extended-session NQ and MNQ datasets used by EXP-012"
        ),
        "historical_start": "2020-01-03",
        "historical_end": "2025-12-31",
        "expected_included_sessions": 1331,
        "source_timeframe": "1 minute",
        "signal_timeframe": "5 minutes",
        "research_timezone": "America/New_York",
        "cash_session": "09:30-16:00",
        "extended_context_only": True,
        "cash_session_entries_only": True,
        "reuse_only_frozen_exp012_sessions": True,
        "new_data_cleaning_decisions_prohibited": True,
        "raw_source_editing_prohibited": True,
    },
    "strategy_rules": {
        "gap_fade_0p50_1r": {
            "context": (
                "Opening gap from the immediately preceding complete cash "
                "session close, divided by that prior cash-session range."
            ),
            "setup": "Absolute gap fraction is at least 0.50.",
            "signal": (
                "The completed 09:30-09:35 bar moves opposite the gap."
            ),
            "entry": "09:35 five-minute bar open toward prior cash close.",
            "stop": "Outer extreme of the completed first cash bar.",
            "target": "1R from actual entry, otherwise 15:55 time exit.",
        },
        "premarket_continuation_time": {
            "context": (
                "Final 90-minute premarket close-minus-open divided by "
                "the premarket high-low range."
            ),
            "setups": (
                "Absolute premarket drive fraction is at least 0.50 or "
                "0.75 according to the locked candidate."
            ),
            "signal": (
                "The completed 09:30-09:35 bar moves in the premarket "
                "direction."
            ),
            "entry": "09:35 five-minute bar open.",
            "stop": "Opposite extreme of the completed first cash bar.",
            "target": "No price target; 15:55 time exit.",
        },
        "maximum_trades_per_session": 1,
        "overnight_positions": False,
    },
    "execution_and_costs": {
        "completed_signal_data_only": True,
        "execution_resolution": "1 minute",
        "evaluate_exit_minutes_chronologically": True,
        "entry_minute_can_exit": True,
        "same_minute_stop_and_target_rule": "STOP_FIRST_CONSERVATIVE",
        "position_size": "FIXED_ONE_CONTRACT",
        "nq_contracts": 1,
        "mnq_contracts": 1,
        "reuse_exp012_commissions": True,
        "base_slippage_ticks_per_side": 1,
        "nq_cost_sensitivity_ticks_per_side": [0, 1, 2],
        "volatility_targeting_enabled": False,
    },
    "full_sample_comparison": {
        "show_all_three_candidates": True,
        "measurement_leader_rank": [
            "trade_profit_factor descending",
            "net_profit_to_maximum_drawdown descending",
            "net_profit_usd descending",
            "completed_trades descending",
            "candidate_id ascending",
        ],
        "automatic_trading_winner": False,
        "user_preference_candidate_reported_separately": True,
        "low_sample_candidate_reported_separately": True,
        "no_arbitrary_profit_factor_improvement_hurdle": True,
    },
    "anchored_walk_forward": {
        "enabled": True,
        "selection_repeated_among_three_in_each_training_window": True,
        "folds": [
            {
                "training": "2020-01-03 through 2021-12-31",
                "test_year": 2022,
            },
            {
                "training": "2020-01-03 through 2022-12-31",
                "test_year": 2023,
            },
            {
                "training": "2020-01-03 through 2023-12-31",
                "test_year": 2024,
            },
            {
                "training": "2020-01-03 through 2024-12-31",
                "test_year": 2025,
            },
        ],
        "fold_count": 4,
        "training_eligibility": {
            "minimum_completed_trades": 20,
            "trade_profit_factor_strictly_above": 1.0,
            "net_profit_usd_strictly_above": 0.0,
        },
        "selection_rank": [
            "trade_profit_factor descending",
            "net_profit_to_maximum_drawdown descending",
            "net_profit_usd descending",
            "completed_trades descending",
            "candidate_id ascending",
        ],
        "no_eligible_candidate_action": (
            "Record the fold as unselected with zero test trades and "
            "preserve that outcome."
        ),
        "training_end_must_precede_test_start": True,
        "not_claimed_as_untouched_out_of_sample": True,
    },
    "discovery_wide_selection_aware_mcpt": {
        "enabled": True,
        "primary_market": "NQ",
        "permutations": 1000,
        "random_seed": 53,
        "permutation_engine": {
            "source_resolution": "1 minute",
            "source_session_shape": (
                "1,320 active minutes from 18:00 through 15:59 New York"
            ),
            "component_definition": (
                "log open gap from prior minute close; log close move "
                "from minute open; high excursion above max(open, close); "
                "low excursion below min(open, close); volume"
            ),
            "shuffle_axis": (
                "independently across complete sessions within each exact "
                "extended-session minute slot"
            ),
            "first_session_open_anchor": True,
            "reconstruct_prices_chronologically": True,
            "preserves_time_of_day_component_distributions": True,
            "destroys_cross_slot_and_cross_session_predictive_alignment": True,
            "nq_only_primary_null": True,
        },
        "all_24_exp012_candidates_run_inside_each_permutation": True,
        "same_candidate_rules_and_costs_inside_every_permutation": True,
        "primary_test_statistic": (
            "maximum_trade_profit_factor_across_all_24_candidates"
        ),
        "real_statistic_uses_all_24_exp012_candidates": True,
        "plus_one_p_value": True,
        "each_finalist_fixed_candidate_mcpt_is_secondary": True,
        "corrects_maximum_pf_search_across_24": True,
        "does_not_make_post_result_selection_independent": True,
        "exact_serial_parallel_parity_required": True,
    },
    "bootstrap_diagnostics": {
        "enabled": True,
        "resamples": 10000,
        "random_seed": 5301,
        "confidence_level": 0.95,
        "report_all_three_candidates": True,
        "decision_gate": False,
    },
    "evidence_context": {
        "measurement_first": True,
        "classification_is_secondary": True,
        "strong_historical_evidence": {
            "maximum_discovery_wide_mcpt_p_value": 0.05,
            "minimum_profitable_walk_forward_folds": 3,
            "combined_walk_forward_net_profit_strictly_above": 0.0,
            "selected_nq_profit_factor_strictly_above": 1.0,
            "selected_mnq_profit_factor_strictly_above": 1.0,
            "two_tick_nq_net_profit_strictly_above": 0.0,
        },
        "promising_but_uncertain": {
            "maximum_discovery_wide_mcpt_p_value": 0.10,
            "minimum_profitable_walk_forward_folds": 2,
            "combined_walk_forward_net_profit_strictly_above": 0.0,
            "selected_nq_profit_factor_strictly_above": 1.0,
            "two_tick_nq_net_profit_strictly_above": 0.0,
        },
        "otherwise": "WEAK_OR_INCONCLUSIVE_HISTORICAL_EVIDENCE",
        "no_accept_reject_lifecycle_from_one_threshold": True,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
    },
    "reporting_requirements": {
        "plain_english_what_how_happened_why": True,
        "all_three_candidates_visible": True,
        "selection_reasons_and_limitations_visible": True,
        "strategy_vs_normalized_nq_benchmark": True,
        "equity_and_drawdown_visuals": True,
        "annual_monthly_and_rolling_measurements": True,
        "trade_distribution_and_profit_concentration": True,
        "cost_sensitivity": True,
        "nq_mnq_comparison": True,
        "walk_forward_fold_table": True,
        "discovery_wide_mcpt_distribution_and_percentile": True,
        "fixed_candidate_mcpt_diagnostics": True,
        "bootstrap_intervals": True,
        "positive_numbers_use_neutral_text": True,
        "adverse_numbers_use_red_text": True,
        "green_reserved_for_status_words": True,
        "charts_use_solid_opaque_white_canvas": True,
    },
    "prohibited_actions": [
        "Changing EXP-012 candidates, measurements or lifecycle record.",
        "Adding, removing or changing an EXP-013 finalist.",
        "Hiding the 0.75 premarket candidate's low-sample warning.",
        "Calling the finalists independently preselected.",
        "Running only three candidates inside the primary MCPT.",
        "Claiming the MCPT erases post-result human rule design.",
        "Changing seeds, permutations, costs or execution after results.",
        "Using variable sizing or volatility targeting.",
        "Hiding weak candidate, fold, bootstrap or MCPT measurements.",
        "Calling EXP-013 untouched out-of-sample confirmation.",
        "Authorizing paper or live trading from EXP-013.",
    ],
}


def get_exp013_preregistration() -> dict[str, Any]:
    return deepcopy(EXP013_PREREGISTRATION)


def validate_exp013_preregistration(
    record: dict[str, Any] | None = None,
) -> None:
    current = EXP013_PREREGISTRATION if record is None else record

    if (
        current.get("schema_version") != 1
        or current.get("experiment_id") != "EXP-013"
        or current.get("research_status") != "PRE_REGISTERED"
        or current.get("implementation_status") != "NOT_RUN"
        or current.get("results_viewed") != "NONE"
    ):
        raise ValueError("EXP-013 identity or pre-result state changed.")

    relationship = current["relationship_to_exp012"]
    if (
        relationship["required_exp012_stage"] != "REVIEW"
        or relationship["exp012_result_must_match_frozen_hashes"] is not True
        or relationship["source_candidate_count"] != 24
        or relationship["review_candidate_count"] != 3
        or relationship["review_candidates_selected_after_results"]
        is not True
        or relationship["selection_reasons_are_post_result_judgments"]
        is not True
        or relationship["preference_is_not_independent_preselection"]
        is not True
        or relationship["discovery_wide_mcpt_repeats_all_24_candidates"]
        is not True
        or relationship["mcpt_cannot_erase_post_result_rule_design"]
        is not True
        or relationship["cannot_claim_independent_confirmation"] is not True
    ):
        raise ValueError("EXP-013 relationship to EXP-012 changed.")

    lock = current["candidate_lock"]
    candidates = tuple(lock["candidates"])
    expected_ids = {
        "gap_fade_0p50_1r",
        "premarket_continuation_0p50_time",
        "premarket_continuation_0p75_time",
    }
    if (
        lock["candidate_count"] != 3
        or candidates != FINALIST_CANDIDATES
        or {item["candidate_id"] for item in candidates} != expected_ids
        or lock["new_parameters_prohibited"] is not True
        or lock["candidate_additions_prohibited"] is not True
        or lock["candidate_removals_prohibited"] is not True
        or lock["low_sample_warning_must_remain_visible"] is not True
    ):
        raise ValueError("EXP-013 three-candidate lock changed.")

    data = current["market_and_data"]
    if (
        data["historical_start"] != "2020-01-03"
        or data["historical_end"] != "2025-12-31"
        or data["expected_included_sessions"] != 1331
        or data["cash_session_entries_only"] is not True
        or data["reuse_only_frozen_exp012_sessions"] is not True
        or data["new_data_cleaning_decisions_prohibited"] is not True
    ):
        raise ValueError("EXP-013 frozen data scope changed.")

    costs = current["execution_and_costs"]
    if (
        costs["position_size"] != "FIXED_ONE_CONTRACT"
        or costs["base_slippage_ticks_per_side"] != 1
        or costs["nq_cost_sensitivity_ticks_per_side"] != [0, 1, 2]
        or costs["same_minute_stop_and_target_rule"]
        != "STOP_FIRST_CONSERVATIVE"
        or costs["volatility_targeting_enabled"] is not False
    ):
        raise ValueError("EXP-013 execution or cost standard changed.")

    walk_forward = current["anchored_walk_forward"]
    if (
        walk_forward["enabled"] is not True
        or walk_forward["fold_count"] != 4
        or [fold["test_year"] for fold in walk_forward["folds"]]
        != [2022, 2023, 2024, 2025]
        or walk_forward[
            "selection_repeated_among_three_in_each_training_window"
        ]
        is not True
        or walk_forward["training_eligibility"][
            "minimum_completed_trades"
        ]
        != 20
        or walk_forward["not_claimed_as_untouched_out_of_sample"]
        is not True
    ):
        raise ValueError("EXP-013 walk-forward plan changed.")

    mcpt = current["discovery_wide_selection_aware_mcpt"]
    permutation_engine = mcpt["permutation_engine"]
    if (
        mcpt["enabled"] is not True
        or mcpt["permutations"] != 1000
        or mcpt["random_seed"] != 53
        or mcpt["all_24_exp012_candidates_run_inside_each_permutation"]
        is not True
        or mcpt["primary_test_statistic"]
        != "maximum_trade_profit_factor_across_all_24_candidates"
        or mcpt["real_statistic_uses_all_24_exp012_candidates"] is not True
        or mcpt["does_not_make_post_result_selection_independent"]
        is not True
        or mcpt["exact_serial_parallel_parity_required"] is not True
        or permutation_engine["source_resolution"] != "1 minute"
        or "1,320 active minutes"
        not in permutation_engine["source_session_shape"]
        or "within each exact" not in permutation_engine["shuffle_axis"]
        or permutation_engine["first_session_open_anchor"] is not True
        or permutation_engine["reconstruct_prices_chronologically"]
        is not True
        or permutation_engine[
            "preserves_time_of_day_component_distributions"
        ]
        is not True
        or permutation_engine[
            "destroys_cross_slot_and_cross_session_predictive_alignment"
        ]
        is not True
    ):
        raise ValueError("EXP-013 discovery-wide MCPT plan changed.")

    bootstrap = current["bootstrap_diagnostics"]
    if (
        bootstrap["enabled"] is not True
        or bootstrap["resamples"] != 10000
        or bootstrap["random_seed"] != 5301
        or bootstrap["report_all_three_candidates"] is not True
        or bootstrap["decision_gate"] is not False
    ):
        raise ValueError("EXP-013 bootstrap plan changed.")

    evidence = current["evidence_context"]
    if (
        evidence["measurement_first"] is not True
        or evidence["classification_is_secondary"] is not True
        or evidence["no_accept_reject_lifecycle_from_one_threshold"]
        is not True
        or evidence["paper_trading_authorized"] is not False
        or evidence["live_trading_authorized"] is not False
    ):
        raise ValueError("EXP-013 interpretation boundary changed.")

    reporting = current["reporting_requirements"]
    if (
        reporting["all_three_candidates_visible"] is not True
        or reporting["selection_reasons_and_limitations_visible"] is not True
        or reporting["discovery_wide_mcpt_distribution_and_percentile"]
        is not True
        or reporting["positive_numbers_use_neutral_text"] is not True
        or reporting["adverse_numbers_use_red_text"] is not True
        or reporting["green_reserved_for_status_words"] is not True
        or reporting["charts_use_solid_opaque_white_canvas"] is not True
    ):
        raise ValueError("EXP-013 reporting standard changed.")

    if current["full_sample_comparison"]["automatic_trading_winner"]:
        raise ValueError("EXP-013 cannot select an automatic winner.")


if __name__ == "__main__":
    validate_exp013_preregistration()
    print("EXP-013 preregistration is valid and result-free.")
