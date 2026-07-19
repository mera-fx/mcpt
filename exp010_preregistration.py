from __future__ import annotations

from copy import deepcopy
from typing import Any


OPENING_DRIVE_CANDIDATES: tuple[dict[str, Any], ...] = (
    {
        "candidate_id": "opening_drive_0p5_time",
        "minimum_drive_fraction": 0.5,
        "exit_mode": "time",
    },
    {
        "candidate_id": "opening_drive_0p5_1p5r",
        "minimum_drive_fraction": 0.5,
        "exit_mode": "1p5r_or_time",
    },
    {
        "candidate_id": "opening_drive_0p75_time",
        "minimum_drive_fraction": 0.75,
        "exit_mode": "time",
    },
    {
        "candidate_id": "opening_drive_0p75_1p5r",
        "minimum_drive_fraction": 0.75,
        "exit_mode": "1p5r_or_time",
    },
)


EXP010_PREREGISTRATION: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-010",
    "title": "NQ/MNQ Opening-Drive Deep Validation",
    "locked_date": "2026-07-19",
    "research_status": "PRE_REGISTERED",
    "implementation_status": "NOT_RUN",
    "results_viewed": "NONE",
    "purpose": (
        "Deeply measure the four opening-drive candidates identified in "
        "EXP-009 using selection-aware statistical tests, anchored "
        "walk-forward measurement and detailed risk reporting."
    ),
    "research_question": (
        "Does the opening-drive family retain attractive performance, "
        "risk, consistency and cost characteristics after accounting for "
        "selection among its four locked candidates?"
    ),
    "relationship_to_exp009": {
        "required_exp009_stage": "REVIEW",
        "exp009_result_must_match_frozen_hashes": True,
        "source_family": "opening_drive_continuation",
        "source_candidate_count": 4,
        "all_source_candidates_included": True,
        "user_preferred_reference_candidate": (
            "opening_drive_0p5_1p5r"
        ),
        "preference_is_not_independent_preselection": True,
        "prior_family_selection_across_24_candidates_is_not_corrected": True,
        "historical_status": (
            "EXPLORATORY_DEEP_VALIDATION_BECAUSE_THE_FAMILY_AND_"
            "2019_2025_RESULTS_WERE_ALREADY_VIEWED"
        ),
        "cannot_claim_independent_confirmation": True,
    },
    "candidate_lock": {
        "family_id": "opening_drive_continuation",
        "candidate_count": 4,
        "candidates": OPENING_DRIVE_CANDIDATES,
        "new_parameters_prohibited": True,
        "candidate_additions_prohibited": True,
        "candidate_removals_prohibited": True,
    },
    "market_and_data": {
        "primary_market": "NQ",
        "secondary_implementation_market": "MNQ",
        "secondary_is_independent_confirmation": False,
        "source": (
            "Frozen EXP-005 Quantower/Lucid-Rithmic NQ and MNQ datasets"
        ),
        "historical_start": "2019-05-06",
        "historical_end": "2025-12-31",
        "expected_included_sessions": 1639,
        "source_timeframe": "1 minute",
        "signal_timeframe": "5 minutes",
        "research_timezone": "America/New_York",
        "cash_session": "09:30-16:00",
        "reuse_only_frozen_exp005_clean_sessions": True,
        "new_data_cleaning_decisions_prohibited": True,
        "raw_source_editing_prohibited": True,
    },
    "strategy_rules": {
        "measurement_window": "09:30-10:00 New York",
        "drive_definition": (
            "Absolute first-30-minute close-minus-open divided by the "
            "first-30-minute high-low range."
        ),
        "direction": (
            "Trade in the sign of the first-30-minute return when the "
            "drive fraction meets the candidate threshold."
        ),
        "entry": "10:00 five-minute bar open.",
        "stop": "Opposite side of the first 30-minute opening range.",
        "target": (
            "No target for time candidates; 1.5R from actual entry for "
            "1p5r_or_time candidates."
        ),
        "forced_flat": "15:55 one-minute bar open.",
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
        "reuse_exp009_commissions": True,
        "base_slippage_ticks_per_side": 1,
        "nq_cost_sensitivity_ticks_per_side": [0, 1, 2],
        "volatility_targeting_enabled": False,
    },
    "full_sample_comparison": {
        "show_all_four_candidates": True,
        "measurement_leader_rank": [
            "trade_profit_factor descending",
            "net_profit_to_maximum_drawdown descending",
            "net_profit_usd descending",
            "completed_trades descending",
            "candidate_id ascending",
        ],
        "automatic_trading_winner": False,
        "user_reference_reported_separately": True,
        "no_arbitrary_profit_factor_improvement_hurdle": True,
    },
    "anchored_walk_forward": {
        "enabled": True,
        "selection_repeated_in_each_training_window": True,
        "folds": [
            {
                "training": "2019-05-06 through 2020-12-31",
                "test_year": 2021,
            },
            {
                "training": "2019-05-06 through 2021-12-31",
                "test_year": 2022,
            },
            {
                "training": "2019-05-06 through 2022-12-31",
                "test_year": 2023,
            },
            {
                "training": "2019-05-06 through 2023-12-31",
                "test_year": 2024,
            },
            {
                "training": "2019-05-06 through 2024-12-31",
                "test_year": 2025,
            },
        ],
        "fold_count": 5,
        "training_eligibility": {
            "minimum_completed_trades": 100,
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
    "selection_aware_mcpt": {
        "enabled": True,
        "primary_market": "NQ",
        "permutations": 1000,
        "random_seed": 50,
        "all_four_candidates_run_inside_each_permutation": True,
        "same_full_sample_rank_inside_every_permutation": True,
        "no_eligible_candidate_statistic": 0.0,
        "primary_test_statistic": (
            "selected_opening_drive_candidate_trade_profit_factor"
        ),
        "plus_one_p_value": True,
        "fixed_user_reference_mcpt_is_secondary_diagnostic": True,
        "fixed_reference_candidate": "opening_drive_0p5_1p5r",
        "does_not_correct_prior_six_family_selection": True,
        "exact_serial_parallel_parity_required": True,
    },
    "bootstrap_diagnostics": {
        "enabled": True,
        "resamples": 10000,
        "random_seed": 5001,
        "confidence_level": 0.95,
        "report_measurement_leader_and_user_reference": True,
        "decision_gate": False,
    },
    "evidence_context": {
        "measurement_first": True,
        "classification_is_secondary": True,
        "strong_historical_evidence": {
            "maximum_selection_aware_mcpt_p_value": 0.05,
            "minimum_profitable_walk_forward_folds": 4,
            "combined_walk_forward_net_profit_strictly_above": 0.0,
            "selected_nq_profit_factor_strictly_above": 1.0,
            "selected_mnq_profit_factor_strictly_above": 1.0,
            "two_tick_nq_net_profit_strictly_above": 0.0,
        },
        "promising_but_uncertain": {
            "maximum_selection_aware_mcpt_p_value": 0.10,
            "minimum_profitable_walk_forward_folds": 3,
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
        "all_four_candidates_visible": True,
        "measurement_leader_and_user_reference_visible": True,
        "strategy_vs_normalized_nq_benchmark": True,
        "equity_and_drawdown_visuals": True,
        "annual_monthly_and_rolling_measurements": True,
        "trade_distribution_and_profit_concentration": True,
        "cost_sensitivity": True,
        "nq_mnq_comparison": True,
        "walk_forward_fold_table": True,
        "mcpt_distribution_and_percentile": True,
        "bootstrap_intervals": True,
        "positive_numbers_use_neutral_text": True,
        "adverse_numbers_use_red_text": True,
        "green_reserved_for_status_words": True,
    },
    "prohibited_actions": [
        "Changing EXP-009 candidates, measurements or lifecycle record.",
        "Adding new opening-drive parameters or candidates to EXP-010.",
        "Removing any of the four opening-drive candidates.",
        "Treating the user reference as independently preselected.",
        "Claiming the four-candidate MCPT corrects the prior six-family selection.",
        "Changing the random seeds or permutation count after results.",
        "Changing the cost, execution or data-cleaning model.",
        "Using variable sizing or volatility targeting.",
        "Hiding weak candidate, fold, bootstrap or MCPT measurements.",
        "Calling EXP-010 an untouched out-of-sample confirmation.",
        "Authorizing paper or live trading from EXP-010.",
    ],
}


def get_exp010_preregistration() -> dict[str, Any]:
    return deepcopy(EXP010_PREREGISTRATION)


def validate_exp010_preregistration(
    record: dict[str, Any] | None = None,
) -> None:
    current = EXP010_PREREGISTRATION if record is None else record

    if (
        current.get("schema_version") != 1
        or current.get("experiment_id") != "EXP-010"
        or current.get("research_status") != "PRE_REGISTERED"
        or current.get("implementation_status") != "NOT_RUN"
        or current.get("results_viewed") != "NONE"
    ):
        raise ValueError("EXP-010 identity or pre-result state changed.")

    relationship = current["relationship_to_exp009"]
    if (
        relationship["required_exp009_stage"] != "REVIEW"
        or relationship["exp009_result_must_match_frozen_hashes"] is not True
        or relationship["source_family"] != "opening_drive_continuation"
        or relationship["source_candidate_count"] != 4
        or relationship["all_source_candidates_included"] is not True
        or relationship["user_preferred_reference_candidate"]
        != "opening_drive_0p5_1p5r"
        or relationship["preference_is_not_independent_preselection"]
        is not True
        or relationship[
            "prior_family_selection_across_24_candidates_is_not_corrected"
        ]
        is not True
        or relationship["cannot_claim_independent_confirmation"] is not True
    ):
        raise ValueError("EXP-010 relationship to EXP-009 changed.")

    lock = current["candidate_lock"]
    if (
        lock["family_id"] != "opening_drive_continuation"
        or lock["candidate_count"] != 4
        or tuple(lock["candidates"]) != OPENING_DRIVE_CANDIDATES
        or lock["new_parameters_prohibited"] is not True
        or lock["candidate_additions_prohibited"] is not True
        or lock["candidate_removals_prohibited"] is not True
    ):
        raise ValueError("EXP-010 four-candidate lock changed.")

    data = current["market_and_data"]
    if (
        data["primary_market"] != "NQ"
        or data["secondary_implementation_market"] != "MNQ"
        or data["expected_included_sessions"] != 1639
        or data["reuse_only_frozen_exp005_clean_sessions"] is not True
        or data["new_data_cleaning_decisions_prohibited"] is not True
    ):
        raise ValueError("EXP-010 market/data lock changed.")

    rules = current["strategy_rules"]
    if (
        rules["measurement_window"] != "09:30-10:00 New York"
        or rules["entry"] != "10:00 five-minute bar open."
        or rules["forced_flat"] != "15:55 one-minute bar open."
        or rules["maximum_trades_per_session"] != 1
        or rules["overnight_positions"] is not False
    ):
        raise ValueError("EXP-010 strategy rules changed.")

    execution = current["execution_and_costs"]
    if (
        execution["execution_resolution"] != "1 minute"
        or execution["same_minute_stop_and_target_rule"]
        != "STOP_FIRST_CONSERVATIVE"
        or execution["position_size"] != "FIXED_ONE_CONTRACT"
        or execution["nq_contracts"] != 1
        or execution["mnq_contracts"] != 1
        or execution["base_slippage_ticks_per_side"] != 1
        or execution["nq_cost_sensitivity_ticks_per_side"] != [0, 1, 2]
        or execution["volatility_targeting_enabled"] is not False
    ):
        raise ValueError("EXP-010 execution/cost lock changed.")

    comparison = current["full_sample_comparison"]
    if (
        comparison["show_all_four_candidates"] is not True
        or comparison["automatic_trading_winner"] is not False
        or comparison["user_reference_reported_separately"] is not True
        or comparison["no_arbitrary_profit_factor_improvement_hurdle"]
        is not True
        or len(comparison["measurement_leader_rank"]) != 5
    ):
        raise ValueError("EXP-010 full-sample comparison changed.")

    walk_forward = current["anchored_walk_forward"]
    eligibility = walk_forward["training_eligibility"]
    if (
        walk_forward["enabled"] is not True
        or walk_forward["selection_repeated_in_each_training_window"]
        is not True
        or walk_forward["fold_count"] != 5
        or len(walk_forward["folds"]) != 5
        or eligibility["minimum_completed_trades"] != 100
        or eligibility["trade_profit_factor_strictly_above"] != 1.0
        or eligibility["net_profit_usd_strictly_above"] != 0.0
        or walk_forward["training_end_must_precede_test_start"] is not True
        or walk_forward["not_claimed_as_untouched_out_of_sample"]
        is not True
    ):
        raise ValueError("EXP-010 anchored walk-forward plan changed.")

    mcpt = current["selection_aware_mcpt"]
    if (
        mcpt["enabled"] is not True
        or mcpt["primary_market"] != "NQ"
        or mcpt["permutations"] != 1000
        or mcpt["random_seed"] != 50
        or mcpt["all_four_candidates_run_inside_each_permutation"]
        is not True
        or mcpt["same_full_sample_rank_inside_every_permutation"]
        is not True
        or mcpt["plus_one_p_value"] is not True
        or mcpt["fixed_reference_candidate"]
        != "opening_drive_0p5_1p5r"
        or mcpt["does_not_correct_prior_six_family_selection"] is not True
        or mcpt["exact_serial_parallel_parity_required"] is not True
    ):
        raise ValueError("EXP-010 selection-aware MCPT plan changed.")

    bootstrap = current["bootstrap_diagnostics"]
    if (
        bootstrap["enabled"] is not True
        or bootstrap["resamples"] != 10000
        or bootstrap["random_seed"] != 5001
        or bootstrap["decision_gate"] is not False
    ):
        raise ValueError("EXP-010 bootstrap plan changed.")

    evidence = current["evidence_context"]
    if (
        evidence["measurement_first"] is not True
        or evidence["classification_is_secondary"] is not True
        or evidence["strong_historical_evidence"][
            "maximum_selection_aware_mcpt_p_value"
        ]
        != 0.05
        or evidence["promising_but_uncertain"][
            "maximum_selection_aware_mcpt_p_value"
        ]
        != 0.10
        or evidence["no_accept_reject_lifecycle_from_one_threshold"]
        is not True
        or evidence["paper_trading_authorized"] is not False
        or evidence["live_trading_authorized"] is not False
    ):
        raise ValueError("EXP-010 evidence context changed.")

    reporting = current["reporting_requirements"]
    if (
        reporting["all_four_candidates_visible"] is not True
        or reporting["strategy_vs_normalized_nq_benchmark"] is not True
        or reporting["positive_numbers_use_neutral_text"] is not True
        or reporting["adverse_numbers_use_red_text"] is not True
        or reporting["green_reserved_for_status_words"] is not True
    ):
        raise ValueError("EXP-010 reporting standard changed.")

    prohibited = " ".join(current["prohibited_actions"]).lower()
    for phrase in (
        "changing exp-009",
        "adding new opening-drive parameters",
        "removing any of the four",
        "independently preselected",
        "prior six-family selection",
        "random seeds or permutation count",
        "variable sizing",
        "untouched out-of-sample",
        "paper or live trading",
    ):
        if phrase not in prohibited:
            raise ValueError(f"EXP-010 prohibition missing: {phrase}.")


if __name__ == "__main__":
    validate_exp010_preregistration()
    print("EXP-010 preregistration is valid.")
