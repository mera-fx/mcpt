from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any


EXP022_CLOSURE_COMMIT = (
    "9d157c8e7a6ba584a96cb5d37086672ad5b64ea1"
)

EXPECTED_EXP022_CLOSURE_SHA256 = (
    "1cc01baddeeae3acf81b0785923b581fad6aac0b6e36071d07d0d83d35bf588d"
)

EXP014_FREEZE_COMMIT = (
    "5ac5e8ebe2dd251f394d8cdac8d4bad654a2fd0c"
)

EXPECTED_SESSION_QUALITY_SHA256 = (
    "6b55077783ad2c1cd8ef99f10d50ed7d691aad7cafcdb7e8fa37639d90724712"
)

FINALIST_IDS = (
    "gap_fade_0p50_1r",
    "premarket_continuation_0p50_time",
    "premarket_continuation_0p75_time",
)

EXP023_PREREGISTRATION: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-023",
    "title": (
        "NQ Frozen-Finalist Continuous-Series Transfer Qualification"
    ),
    "locked_date": "2026-07-26",
    "research_status": "PRE_REGISTERED",
    "implementation_status": "NOT_IMPLEMENTED",
    "execution_status": "NOT_RUN",
    "purpose": (
        "Measure whether the three unchanged EXP-014 finalists replay "
        "consistently on the frozen EXP-022 selected-roll NQ series during "
        "the already-known 2020-2025 overlap, before any new historical "
        "strategy evidence is viewed."
    ),
    "research_question": (
        "Does the backward-adjusted EXP-022 series preserve enough session "
        "coverage, fixed-rule signal decisions and trade-level P&L behaviour "
        "to support a separately preregistered later validation on dates "
        "outside the known overlap?"
    ),
    "prior_result_disclosure": {
        "exp014_strategy_results_viewed_before_lock": True,
        "exp022_construction_results_viewed_before_lock": True,
        "exp023_transfer_results_viewed_before_lock": False,
        "exp022_strategy_results_viewed_before_lock": False,
        "out_of_overlap_exp022_strategy_results_viewed": False,
        "finalists_were_selected_after_exp012_results": True,
        "cannot_claim_independent_confirmation": True,
    },
    "objective": {
        "fixed_strategy_replay": True,
        "cross_source_transfer_diagnostic": True,
        "data_and_rule_sensitivity_measurement": True,
        "new_strategy_discovery": False,
        "candidate_selection": False,
        "parameter_search": False,
        "roll_rule_selection": False,
        "optimization": False,
        "mcpt": False,
        "bootstrap": False,
        "walk_forward": False,
        "untouched_history_validation": False,
        "paper_or_live_trading": False,
    },
    "frozen_inputs": {
        "exp022_closure_commit": EXP022_CLOSURE_COMMIT,
        "exp022_closure_record_sha256": (
            EXPECTED_EXP022_CLOSURE_SHA256
        ),
        "exp022_classification": (
            "QUALIFIED_AS_SELECTED_VOLUME_ROLL_CONTINUOUS_SERIES"
        ),
        "selected_roll_method": "VOL_GT_OUT_2S_E3",
        "series_row_count": 5_457_606,
        "series_first_timestamp_utc": (
            "2010-06-06T22:00:00+00:00"
        ),
        "series_last_timestamp_utc": (
            "2026-07-23T23:59:00+00:00"
        ),
        "series": (
            {
                "representation_id": "BACKWARD_ADJUSTED",
                "role": "PRIMARY_TRANSFER_SERIES",
                "path": (
                    "results/EXP-022/selected_continuous_series/"
                    "selected_roll_backward_adjusted.parquet"
                ),
                "size_bytes": 71_964_074,
                "sha256": (
                    "61ccb3621b53fa313147a866948ec1f2c7a6b36956d2ba260"
                    "90162b518c30c84"
                ),
                "semantic_sha256": (
                    "3c6fa83821183ca54bc547c555834ceb16a126be50f90d8c6"
                    "db5684220929951"
                ),
            },
            {
                "representation_id": "UNADJUSTED",
                "role": "SECONDARY_ROLL_SENSITIVITY_SERIES",
                "path": (
                    "results/EXP-022/selected_continuous_series/"
                    "selected_roll_unadjusted.parquet"
                ),
                "size_bytes": 73_760_121,
                "sha256": (
                    "606a69bbba4f4a5db3e0356d7b2849f9481e4555dc24cae4"
                    "c6b9d1d12f673ab1"
                ),
                "semantic_sha256": (
                    "29daf3f20b022fb69967349095eb9663bd04276cbc5743a65b"
                    "1ecabc33113640"
                ),
            },
        ),
        "exp014_freeze_commit": EXP014_FREEZE_COMMIT,
        "exp014_reference_period_start": "2020-01-03",
        "exp014_reference_period_end": "2025-12-31",
        "exp014_reference_session_count": 1_331,
        "session_quality_path": (
            "results/extended_session_data/session_quality.csv"
        ),
        "session_quality_sha256": (
            EXPECTED_SESSION_QUALITY_SHA256
        ),
        "exp022_outputs_read_only": True,
        "exp014_outputs_read_only": True,
        "session_quality_read_only": True,
        "databento_api_calls": 0,
        "credentials_required": False,
    },
    "frozen_finalists": (
        {
            "candidate_id": "gap_fade_0p50_1r",
            "family_id": "gap_fade",
            "reference_ledger_path": (
                "results/EXP-014/finalist_behaviour/candidates/"
                "gap_fade_0p50_1r/nq_enriched_trades.csv"
            ),
            "reference_ledger_canonical_sha256": (
                "67cc5efc71c07cf90dab86ae66ae56cf1d3217d960d7f5532"
                "b6946055beb8a1a"
            ),
            "reference_trade_count": 186,
            "reference_profit_factor": 1.530923511019599,
            "reference_net_profit_usd": 34_810.0,
            "reference_maximum_drawdown_usd": -5_080.0,
        },
        {
            "candidate_id": "premarket_continuation_0p50_time",
            "family_id": "premarket_momentum_continuation",
            "reference_ledger_path": (
                "results/EXP-014/finalist_behaviour/candidates/"
                "premarket_continuation_0p50_time/"
                "nq_enriched_trades.csv"
            ),
            "reference_ledger_canonical_sha256": (
                "b6a02559f66545181880b0c54aef00ed608b907f566bd87d"
                "b06aa2e6dc8fe474"
            ),
            "reference_trade_count": 291,
            "reference_profit_factor": 1.7363738499377523,
            "reference_net_profit_usd": 121_255.0,
            "reference_maximum_drawdown_usd": -20_695.0,
        },
        {
            "candidate_id": "premarket_continuation_0p75_time",
            "family_id": "premarket_momentum_continuation",
            "reference_ledger_path": (
                "results/EXP-014/finalist_behaviour/candidates/"
                "premarket_continuation_0p75_time/"
                "nq_enriched_trades.csv"
            ),
            "reference_ledger_canonical_sha256": (
                "f20565e12e7c914f37239a21649ceb40c03f6e22672dcfa4"
                "60ed41d8f55155ac"
            ),
            "reference_trade_count": 88,
            "reference_profit_factor": 2.0237378415933303,
            "reference_net_profit_usd": 44_205.0,
            "reference_maximum_drawdown_usd": -5_540.0,
        },
    ),
    "strategy_lock": {
        "candidate_ids": FINALIST_IDS,
        "candidate_count": 3,
        "rules_are_exactly_exp013_and_exp014": True,
        "maximum_trades_per_candidate_per_session": 1,
        "cash_session_entries_only": True,
        "overnight_positions": False,
        "entry_time_new_york": "09:35",
        "forced_flat_time_new_york": "15:55",
        "same_minute_stop_and_target_rule": (
            "STOP_FIRST_CONSERVATIVE"
        ),
        "position_size": "FIXED_ONE_NQ_CONTRACT",
        "nq_multiplier_usd_per_point": 20.0,
        "nq_tick_size_points": 0.25,
        "fees_usd_per_side": 2.50,
        "slippage_ticks_per_side": 1.0,
        "round_trip_cost_usd": 15.0,
        "candidate_additions_prohibited": True,
        "candidate_removals_prohibited": True,
        "rule_or_parameter_changes_prohibited": True,
        "cost_or_execution_changes_prohibited": True,
    },
    "data_access_boundary": {
        "allowed_session_date_start": "2020-01-03",
        "allowed_session_date_end": "2025-12-31",
        "allowed_utc_read_start_inclusive": (
            "2020-01-02T23:00:00+00:00"
        ),
        "allowed_utc_read_end_exclusive": (
            "2025-12-31T21:00:00+00:00"
        ),
        "research_timezone": "America/New_York",
        "session_start_local": "18:00",
        "strategy_context_end_local": "15:59",
        "full_file_byte_hash_verification_permitted": True,
        "parquet_metadata_inspection_permitted": True,
        "out_of_window_ohlcv_deserialization_prohibited": True,
        "out_of_window_strategy_calculation_prohibited": True,
        "preserved_for_later_experiments": (
            "2010-06-06 through 2019-12-31",
            "2026-01-01 through 2026-07-23",
        ),
        "preserved_periods_are_not_exp023_results": True,
        "no_new_market_data_download": True,
        "no_network_access": True,
    },
    "bar_and_session_normalization": {
        "source_resolution": "1 minute",
        "signal_resolution": "5 minutes",
        "timestamps_are_utc_minute_starts": True,
        "session_dates_use_america_new_york": True,
        "missing_source_minutes_filled": False,
        "synthetic_bars_created": False,
        "source_ohlcv_modified": False,
        "five_minute_ohlcv_uses_observed_source_minutes_only": True,
        "five_minute_bin_requires_at_least_one_observation": True,
        "cash_entry_minute_0935_must_exist": True,
        "forced_flat_minute_1555_must_exist": True,
        "gap_fade_requires_immediately_prior_reference_cash_session": True,
        "gap_fade_requires_all_prior_cash_five_minute_bins": True,
        "premarket_candidates_require_all_18_premarket_five_minute_bins": (
            True
        ),
        "all_candidates_require_all_78_cash_five_minute_bins": True,
        "ineligible_sessions_are_logged_not_repaired": True,
        "reference_axis_is_1331_frozen_exp014_sessions": True,
        "every_reference_session_must_be_accounted_for": True,
    },
    "comparison_plan": {
        "primary_representation": "BACKWARD_ADJUSTED",
        "secondary_representation": "UNADJUSTED",
        "primary_qualification_applies_only_to_backward_adjusted": True,
        "unadjusted_is_roll_sensitivity_diagnostic_only": True,
        "compare_session_eligibility": True,
        "compare_trade_indicator": True,
        "compare_direction": True,
        "compare_entry_and_exit_timestamps": True,
        "compare_exit_reason": True,
        "compare_gross_and_net_trade_pnl": True,
        "compare_profit_factor_net_profit_and_drawdown": True,
        "compare_annual_and_monthly_results": True,
        "report_differences_by_distance_from_roll_boundary": True,
        "roll_distance_bands_sessions": (0, 1, 3, "OTHER"),
        "reference_results_are_known_not_holdout_evidence": True,
        "profitability_is_measured_but_not_a_transfer_gate": True,
        "no_strategy_ranking_or_winner_selection": True,
    },
    "qualification_gates": {
        "apply_to_each_of_three_primary_replays": True,
        "reference_session_denominator": 1_331,
        "eligibility_share_formula": (
            "eligible_primary_sessions / 1331"
        ),
        "trade_indicator_and_direction_agreement_formula": (
            "eligible sessions with identical (trade_flag, direction) / "
            "eligible_primary_sessions"
        ),
        "trade_count_relative_difference_formula": (
            "abs(primary_trade_count - reference_trade_count) / "
            "reference_trade_count"
        ),
        "common_trade_key": (
            "session_date",
            "direction",
        ),
        "common_trade_match_share_formula": (
            "intersection of primary and reference trade keys / union of "
            "primary and reference trade keys"
        ),
        "entry_timestamp_agreement_formula": (
            "common trades with identical entry timestamp / common trades"
        ),
        "gross_pnl_correlation_method": (
            "Pearson correlation on common trades keyed by session_date "
            "and direction"
        ),
        "gross_pnl_sign_agreement_formula": (
            "common trades with identical sign(gross_pnl_usd) / "
            "common trades"
        ),
        "insufficient_or_zero_variance_correlation_action": "FAIL",
        "minimum_required_session_eligibility_share": 0.99,
        "minimum_trade_indicator_and_direction_agreement": 0.99,
        "maximum_trade_count_relative_difference": 0.01,
        "minimum_common_trade_match_share": 0.98,
        "minimum_matching_entry_timestamp_agreement": 1.0,
        "minimum_common_trade_gross_pnl_correlation": 0.98,
        "minimum_common_trade_gross_pnl_sign_agreement": 0.95,
        "profit_factor_threshold": None,
        "net_profit_threshold_usd": None,
        "all_gates_must_pass_for_qualified_classification": True,
        "threshold_changes_after_results_prohibited": True,
    },
    "classification": {
        "qualified": (
            "QUALIFIED_FOR_SEPARATE_FIXED_RULE_HISTORY_VALIDATION"
        ),
        "divergent": (
            "TRANSFER_DIAGNOSTIC_COMPLETE_WITH_MATERIAL_DIFFERENCES"
        ),
        "hard_failure": "TRANSFER_DIAGNOSTIC_NOT_QUALIFIED",
        "qualified_does_not_validate_strategy_edge": True,
        "qualified_does_not_authorize_out_of_overlap_access": True,
        "qualified_does_not_authorize_paper_or_live_trading": True,
        "divergent_requires_separate_resolution_before_history_use": True,
    },
    "required_outputs": (
        "transfer_summary.json",
        "candidate_transfer_metrics.csv",
        "session_alignment.csv",
        "trade_alignment.csv",
        "representation_sensitivity.csv",
        "ineligible_sessions.csv",
        "output_hashes.json",
        "report.md",
        "TRANSFER_DIAGNOSTIC_COMPLETE.json",
    ),
    "reporting_requirements": {
        "vertical_single_column_html_report": True,
        "plain_english_strategy_rules": True,
        "known_reference_results_disclosed": True,
        "session_coverage_chart": True,
        "trade_agreement_chart": True,
        "common_trade_pnl_scatter": True,
        "reference_vs_transfer_equity_chart": True,
        "annual_comparison_chart": True,
        "roll_proximity_difference_chart": True,
        "representation_sensitivity_chart": True,
        "all_adverse_results_visible": True,
        "positive_numbers_use_neutral_text": True,
        "adverse_numbers_use_red_text": True,
        "green_reserved_for_status_words": True,
        "charts_use_opaque_white_canvas": True,
    },
    "hard_checks": (
        "exp022_closure_hash_matches",
        "exp022_series_byte_and_semantic_hashes_match",
        "exp014_freeze_commit_and_ledger_hashes_match",
        "frozen_session_quality_hash_matches",
        "source_and_reference_evidence_remain_read_only",
        "no_databento_api_or_network_access",
        "utc_and_new_york_session_semantics_are_exact",
        "only_locked_overlap_ohlcv_values_are_deserialized",
        "out_of_overlap_strategy_values_are_not_calculated",
        "exactly_three_frozen_finalists_are_replayed",
        "strategy_rules_costs_and_execution_are_unchanged",
        "missing_minutes_are_not_filled_or_repaired",
        "candidate_session_eligibility_is_deterministic",
        "all_1331_reference_sessions_are_accounted_for",
        "primary_and_secondary_representation_roles_are_fixed",
        "trade_alignment_keys_are_unique",
        "qualification_thresholds_are_applied_unchanged",
        "required_outputs_and_hashes_are_complete",
        "independent_rebuild_matches",
        "no_search_robustness_or_trading_action_occurs",
    ),
    "hard_check_count": 20,
    "execution_boundary": {
        "separate_implementation_commit_required": True,
        "separate_execution_authorization_required": True,
        "protected_preflight_required": True,
        "one_authorized_transfer_run": True,
        "independent_rebuild_required": True,
        "rerun_after_completion": False,
        "databento_api_calls": 0,
        "credentials_required": False,
        "external_network_access": False,
        "strategy_results_calculated_by_preregistration": False,
        "out_of_overlap_values_accessed_by_preregistration": False,
    },
    "prohibited_actions": {
        "rerun_exp022": True,
        "modify_exp022_outputs": True,
        "modify_exp014_outputs": True,
        "read_out_of_overlap_ohlcv_values": True,
        "calculate_out_of_overlap_strategy_results": True,
        "databento_api_request": True,
        "new_market_data_download": True,
        "reselect_roll_rule": True,
        "add_remove_or_change_finalist": True,
        "change_costs_or_execution": True,
        "strategy_optimization": True,
        "mcpt": True,
        "bootstrap": True,
        "walk_forward": True,
        "strategy_ranking": True,
        "paper_trading": True,
        "live_trading": True,
    },
    "interpretation": {
        "known_overlap_transfer_test_only": True,
        "not_new_edge_evidence": True,
        "not_independent_confirmation": True,
        "backward_adjusted_series_selected_before_replay": True,
        "unadjusted_series_is_not_a_competing_strategy": True,
        "no_strategy_winner_selected": True,
        "earlier_and_2026_strategy_evidence_preserved": True,
        "separate_future_experiment_required": True,
        "paper_or_live_trading_authorized": False,
    },
}

EXPECTED_EXP023_PREREGISTRATION_SHA256 = (
    "20c7295123adead63b5e9c398419a3129aa93c4fcd3e597e6e92c295dc2841be"
)


def canonical_record_hash(record: dict[str, Any]) -> str:
    encoded = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def get_exp023_preregistration() -> dict[str, Any]:
    return deepcopy(EXP023_PREREGISTRATION)


def validate_exp023_preregistration(
    candidate: dict[str, Any] | None = None,
) -> None:
    record = (
        EXP023_PREREGISTRATION
        if candidate is None
        else candidate
    )

    if (
        record["experiment_id"] != "EXP-023"
        or record["locked_date"] != "2026-07-26"
        or record["research_status"] != "PRE_REGISTERED"
        or record["implementation_status"] != "NOT_IMPLEMENTED"
        or record["execution_status"] != "NOT_RUN"
    ):
        raise ValueError(
            "EXP-023 preregistration identity changed."
        )

    frozen = record["frozen_inputs"]
    if (
        frozen["exp022_closure_commit"]
        != EXP022_CLOSURE_COMMIT
        or frozen["exp022_closure_record_sha256"]
        != EXPECTED_EXP022_CLOSURE_SHA256
        or frozen["exp014_freeze_commit"]
        != EXP014_FREEZE_COMMIT
        or frozen["session_quality_sha256"]
        != EXPECTED_SESSION_QUALITY_SHA256
    ):
        raise ValueError(
            "EXP-023 frozen evidence boundary changed."
        )

    candidate_ids = tuple(
        item["candidate_id"]
        for item in record["frozen_finalists"]
    )
    if (
        candidate_ids != FINALIST_IDS
        or record["strategy_lock"]["candidate_ids"]
        != FINALIST_IDS
        or record["strategy_lock"]["round_trip_cost_usd"]
        != 15.0
    ):
        raise ValueError(
            "EXP-023 frozen strategy set changed."
        )

    access = record["data_access_boundary"]
    if (
        access["allowed_session_date_start"]
        != "2020-01-03"
        or access["allowed_session_date_end"]
        != "2025-12-31"
        or access[
            "out_of_window_ohlcv_deserialization_prohibited"
        ]
        is not True
        or access[
            "out_of_window_strategy_calculation_prohibited"
        ]
        is not True
    ):
        raise ValueError(
            "EXP-023 protected data window changed."
        )

    gates = record["qualification_gates"]
    if (
        gates["reference_session_denominator"]
        != 1_331
        or gates["common_trade_key"]
        != (
            "session_date",
            "direction",
        )
        or gates[
            "insufficient_or_zero_variance_correlation_action"
        ]
        != "FAIL"
        or gates["minimum_required_session_eligibility_share"]
        != 0.99
        or gates[
            "minimum_trade_indicator_and_direction_agreement"
        ]
        != 0.99
        or gates["maximum_trade_count_relative_difference"]
        != 0.01
        or gates["minimum_common_trade_match_share"]
        != 0.98
        or gates[
            "minimum_matching_entry_timestamp_agreement"
        ]
        != 1.0
        or gates[
            "minimum_common_trade_gross_pnl_correlation"
        ]
        != 0.98
        or gates[
            "minimum_common_trade_gross_pnl_sign_agreement"
        ]
        != 0.95
    ):
        raise ValueError(
            "EXP-023 qualification gates changed."
        )

    if (
        record["hard_check_count"] != 20
        or len(record["hard_checks"]) != 20
        or len(set(record["hard_checks"])) != 20
    ):
        raise ValueError(
            "EXP-023 hard-check set changed."
        )

    if (
        canonical_record_hash(record)
        != EXPECTED_EXP023_PREREGISTRATION_SHA256
    ):
        raise ValueError(
            "EXP-023 preregistration record changed."
        )
