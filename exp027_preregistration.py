from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any


EXP027_PREREGISTRATION: dict[str, Any] = {'schema_version': 1,
 'experiment_id': 'EXP-027',
 'title': 'Protected 2026 Databento NQ Multi-Strategy Measurement',
 'locked_date': '2026-07-28',
 'research_status': 'PRE_REGISTERED',
 'implementation_status': 'NOT_IMPLEMENTED',
 'execution_status': 'NOT_RUN',
 'purpose': 'Measure the unchanged EXP-026 strategy population on the untouched 2026 '
            'Databento-derived NQ period, preserve all candidates as separate evidence rows, and '
            'publish canonical trade and equity evidence without optimization, reselection, winner '
            'declaration or trading authorization.',
 'research_question': 'How do the 22 fixed EXP-026 strategy variants and two fixed controls behave '
                      'on the protected 2026 NQ period, and how do the three predeclared EXP-026 '
                      'finalists compare with their frozen historical evidence when no candidate, '
                      'parameter, cost rule or interpretation gate may be changed after viewing '
                      '2026?',
 'prior_result_disclosure': {'exp026_phase_a_results_viewed': True,
                             'exp026_phase_b_results_viewed': True,
                             'exp026_phase_c_results_viewed': True,
                             'exp026_closure_viewed': True,
                             'all_22_candidate_identities_known': True,
                             'phase_a_survivors_known': True,
                             'phase_b_finalists_known': True,
                             'candidate_population_frozen_before_2026_access': True,
                             'protected_2026_market_values_viewed': False,
                             'protected_2026_strategy_results_viewed': False,
                             'cannot_claim_blind_strategy_discovery': True,
                             'protected_temporal_measurement_claim_requires_authorized_execution': True},
 'frozen_inputs': {'exp026_closure_commit': '7fc1994e396bfb237fd5f05f5a4298e6c5b5e307',
                   'exp026_closure_record_sha256': '8ec79810a26b58f2d445d47d3f496539f121d6f3e139eae4a9fd38ef029a386f',
                   'exp026_classification': 'COMPLETED_MEASUREMENT_REVIEW',
                   'exp026_preregistration_sha256': 'bbd2e6d8bb50c135d0c6ca04873eed2876c4e7db6a2714b91a934dcf554331a0',
                   'exp026_locked_implementation_commit': '13ee0683dfcbbb5d763f7254f3b245ecc8e6d9cd',
                   'exp026_phase_a_completion_commit': '28bd4209711f0c9b98a7650ab91f6408c2bdf4b7',
                   'exp026_phase_a_output_manifest_sha256': '6406c73e0944fdde3a4087f9fde98740210c4ec4bbebd97a888aaeb1ccad962b',
                   'exp026_phase_b_completion_commit': 'da8456d254dc710336806ad5940afcec649be016',
                   'exp026_phase_b_output_manifest_sha256': 'c26b20ceadfec332e9dd72870bc25b37554e184216515a8b8f868c24c0e621a9',
                   'exp026_phase_c_completion_commit': 'a400a373b87b780c21dc2d15048b1e1a5ad1050a',
                   'exp026_phase_c_output_manifest_sha256': 'c1a66777fa04fb69306ffe737cb15a1190051d0c1f9c34aa2a0b8542049a25c5',
                   'exp026_phase_a_survivors': ('gap_fade_0p75_1r',
                                                'gap_fade_0p25_1r',
                                                'opening_drive_0p75_1p5r',
                                                'opening_drive_0p75_time',
                                                'premarket_continuation_0p875_1p5r',
                                                'premarket_continuation_0p625_1p5r'),
                   'exp026_phase_b_finalists': ('gap_fade_0p75_1r',
                                                'opening_drive_0p75_time',
                                                'premarket_continuation_0p875_1p5r'),
                   'exp022_closure_commit': '9d157c8e7a6ba584a96cb5d37086672ad5b64ea1',
                   'exp022_closure_record_sha256': '1cc01baddeeae3acf81b0785923b581fad6aac0b6e36071d07d0d83d35bf588d',
                   'exp022_classification': 'QUALIFIED_AS_SELECTED_VOLUME_ROLL_CONTINUOUS_SERIES',
                   'selected_roll_method': 'VOL_GT_OUT_2S_E3',
                   'series_row_count': 5457606,
                   'series_first_timestamp_utc': '2010-06-06T22:00:00+00:00',
                   'series_last_timestamp_utc': '2026-07-23T23:59:00+00:00',
                   'series': ({'representation_id': 'BACKWARD_ADJUSTED',
                               'role': 'PRIMARY_PROTECTED_MEASUREMENT_SERIES',
                               'path': 'results/EXP-022/selected_continuous_series/selected_roll_backward_adjusted.parquet',
                               'size_bytes': 71964074,
                               'sha256': '61ccb3621b53fa313147a866948ec1f2c7a6b36956d2ba26090162b518c30c84',
                               'semantic_sha256': '3c6fa83821183ca54bc547c555834ceb16a126be50f90d8c6db5684220929951'},
                              {'representation_id': 'UNADJUSTED',
                               'role': 'REPRESENTATION_SENSITIVITY_ONLY',
                               'path': 'results/EXP-022/selected_continuous_series/selected_roll_unadjusted.parquet',
                               'size_bytes': 73760121,
                               'sha256': '606a69bbba4f4a5db3e0356d7b2849f9481e4555dc24cae4c6b9d1d12f673ab1',
                               'semantic_sha256': '29daf3f20b022fb69967349095eb9663bd04276cbc5743a65b1ecabc33113640'}),
                   'historical_data_policy_path': 'research/HISTORICAL_DATA_POLICY.md',
                   'historical_data_policy_sha256': '638cd9da878590bd0cb08302a7fcde81d0fa3380d0d2262af4491c9da63a19b9',
                   'all_source_inputs_read_only': True,
                   'databento_api_calls': 0,
                   'credentials_required': False},
 'objective': {'protected_2026_measurement': True,
               'all_fixed_candidates_reported': True,
               'primary_finalist_confirmation_context': True,
               'secondary_candidate_measurement_context': True,
               'fixed_controls_reported': True,
               'candidate_selection': False,
               'parameter_optimization': False,
               'position_sizing_optimization': False,
               'portfolio_weight_optimization': False,
               'single_winner_selection': False,
               'formal_accept_reject_gates': False,
               'paper_trading': False,
               'live_trading': False},
 'research_period': {'session_start': '2026-01-01',
                     'session_end': '2026-07-23',
                     'purpose': 'One protected temporal measurement of the unchanged EXP-026 '
                                'population.',
                     'results_viewed_before_lock': False,
                     'partial_year_disclosed': True,
                     'later_2026_data_outside_frozen_source': True},
 'candidate_population': {'family_count': 3,
                          'strategy_candidate_count': 22,
                          'control_candidate_count': 2,
                          'total_reported_count': 24,
                          'all_candidate_ids': ('gap_fade_0p25_prior_close',
                                                'gap_fade_0p25_1r',
                                                'gap_fade_0p50_prior_close',
                                                'gap_fade_0p50_1r',
                                                'gap_fade_0p75_prior_close',
                                                'gap_fade_0p75_1r',
                                                'premarket_continuation_0p50_time',
                                                'premarket_continuation_0p50_1p5r',
                                                'premarket_continuation_0p625_time',
                                                'premarket_continuation_0p625_1p5r',
                                                'premarket_continuation_0p75_time',
                                                'premarket_continuation_0p75_1p5r',
                                                'premarket_continuation_0p875_time',
                                                'premarket_continuation_0p875_1p5r',
                                                'opening_drive_0p25_time',
                                                'opening_drive_0p25_1p5r',
                                                'opening_drive_0p50_time',
                                                'opening_drive_0p50_1p5r',
                                                'opening_drive_0p75_time',
                                                'opening_drive_0p75_1p5r',
                                                'opening_drive_1p00_time',
                                                'opening_drive_1p00_1p5r'),
                          'control_ids': ('orb_control_exp005_15m_both_time',
                                          'orb_control_exp007_30m_long_1r'),
                          'all_reported_ids': ('gap_fade_0p25_prior_close',
                                               'gap_fade_0p25_1r',
                                               'gap_fade_0p50_prior_close',
                                               'gap_fade_0p50_1r',
                                               'gap_fade_0p75_prior_close',
                                               'gap_fade_0p75_1r',
                                               'premarket_continuation_0p50_time',
                                               'premarket_continuation_0p50_1p5r',
                                               'premarket_continuation_0p625_time',
                                               'premarket_continuation_0p625_1p5r',
                                               'premarket_continuation_0p75_time',
                                               'premarket_continuation_0p75_1p5r',
                                               'premarket_continuation_0p875_time',
                                               'premarket_continuation_0p875_1p5r',
                                               'opening_drive_0p25_time',
                                               'opening_drive_0p25_1p5r',
                                               'opening_drive_0p50_time',
                                               'opening_drive_0p50_1p5r',
                                               'opening_drive_0p75_time',
                                               'opening_drive_0p75_1p5r',
                                               'opening_drive_1p00_time',
                                               'opening_drive_1p00_1p5r',
                                               'orb_control_exp005_15m_both_time',
                                               'orb_control_exp007_30m_long_1r'),
                          'primary_confirmation_cohort': ('gap_fade_0p75_1r',
                                                          'opening_drive_0p75_time',
                                                          'premarket_continuation_0p875_1p5r'),
                          'secondary_candidate_ids': ('gap_fade_0p25_prior_close',
                                                      'gap_fade_0p25_1r',
                                                      'gap_fade_0p50_prior_close',
                                                      'gap_fade_0p50_1r',
                                                      'gap_fade_0p75_prior_close',
                                                      'premarket_continuation_0p50_time',
                                                      'premarket_continuation_0p50_1p5r',
                                                      'premarket_continuation_0p625_time',
                                                      'premarket_continuation_0p625_1p5r',
                                                      'premarket_continuation_0p75_time',
                                                      'premarket_continuation_0p75_1p5r',
                                                      'premarket_continuation_0p875_time',
                                                      'opening_drive_0p25_time',
                                                      'opening_drive_0p25_1p5r',
                                                      'opening_drive_0p50_time',
                                                      'opening_drive_0p50_1p5r',
                                                      'opening_drive_0p75_1p5r',
                                                      'opening_drive_1p00_time',
                                                      'opening_drive_1p00_1p5r'),
                          'phase_a_survivor_labels': ('gap_fade_0p75_1r',
                                                      'gap_fade_0p25_1r',
                                                      'opening_drive_0p75_1p5r',
                                                      'opening_drive_0p75_time',
                                                      'premarket_continuation_0p875_1p5r',
                                                      'premarket_continuation_0p625_1p5r'),
                          'selection_in_exp027': False,
                          'candidate_additions_prohibited': True,
                          'candidate_removals_prohibited': True,
                          'parameter_changes_prohibited': True,
                          'secondary_promotion_to_primary_prohibited': True,
                          'all_candidates_remain_visible': True,
                          'strategy_definition_source': 'exp026_preregistration.py',
                          'strategy_definition_source_sha256': 'bbd2e6d8bb50c135d0c6ca04873eed2876c4e7db6a2714b91a934dcf554331a0'},
 'data_access_boundary': {'allowed_strategy_session_start': '2026-01-01',
                          'allowed_strategy_session_end': '2026-07-23',
                          'research_timezone': 'America/New_York',
                          'source_timestamp_timezone': 'UTC',
                          'session_start_local': '18:00',
                          'session_date_filter_before_materialization_required': True,
                          'parquet_filter_pushdown_required': True,
                          'historical_2010_2025_market_row_deserialization_prohibited': True,
                          'frozen_exp026_aggregate_outputs_read_permitted': True,
                          'full_file_byte_hash_verification_permitted': True,
                          'parquet_metadata_inspection_permitted': True,
                          'no_network_access': True,
                          'no_databento_api_request': True,
                          'new_databento_download': False,
                          'missing_minutes_filled': False,
                          'synthetic_bars_created': False,
                          'source_ohlcv_modified': False},
 'strategy_and_execution_rules': {'strategy_rules_source': 'exp026_preregistration.py',
                                  'execution_engine_source': 'exp026_core.py',
                                  'execution_engine_locked_commit': '13ee0683dfcbbb5d763f7254f3b245ecc8e6d9cd',
                                  'source_resolution': '1 minute',
                                  'signal_resolution': '5 minutes',
                                  'completed_signal_bars_only': True,
                                  'five_minute_bars_use_observed_minutes_only': True,
                                  'maximum_trades_per_candidate_per_session': 1,
                                  'same_day_reentry': False,
                                  'overnight_positions': False,
                                  'entry_uses_actual_open': True,
                                  'entry_minute_can_exit': True,
                                  'evaluate_exit_minutes_chronologically': True,
                                  'same_minute_stop_target_rule': 'STOP_FIRST_CONSERVATIVE',
                                  'invalid_nonpositive_risk_trade': 'DO_NOT_ENTER',
                                  'candidate_native_eligibility_is_primary': True,
                                  'all_rules_unchanged_from_exp026': True},
 'position_and_cost_model': {'market': 'NQ',
                             'position_size': 'FIXED_ONE_CONTRACT',
                             'multiplier_usd_per_point': 20.0,
                             'tick_size_points': 0.25,
                             'tick_value_usd': 5.0,
                             'fees_usd_per_side': 2.5,
                             'base_slippage_ticks_per_side': 1.0,
                             'base_round_trip_cost_usd': 15.0,
                             'reference_capital_usd': 100000.0,
                             'cost_sensitivity_ticks_per_side': (0, 1, 2, 3),
                             'position_sizing_optimization': False},
 'measurement_plan': {'metric_columns': ('ALL_TRADES', 'LONG_TRADES', 'SHORT_TRADES'),
                      'performance_metrics': ('net_profit_usd',
                                              'gross_profit_usd',
                                              'gross_loss_usd',
                                              'trade_profit_factor',
                                              'completed_trades',
                                              'win_rate',
                                              'average_trade_usd',
                                              'median_trade_usd',
                                              'average_winner_usd',
                                              'average_loser_usd',
                                              'payoff_ratio'),
                      'risk_metrics': ('maximum_drawdown_usd',
                                       'maximum_drawdown_percent',
                                       'net_profit_to_drawdown',
                                       'drawdown_duration',
                                       'recovery_duration',
                                       'maximum_consecutive_losses'),
                      'consistency_metrics': ('profitable_month_fraction',
                                              'rolling_trade_profit_factor',
                                              'top_1_trade_profit_share',
                                              'top_5_trade_profit_share',
                                              'top_10_trade_profit_share'),
                      'practical_metrics': ('trades_per_month',
                                            'session_participation_rate',
                                            'average_holding_minutes',
                                            'median_holding_minutes',
                                            'average_trade_to_round_trip_cost',
                                            'entry_time_distribution',
                                            'exit_reason_distribution'),
                      'descriptive_sample_bands': {'ZERO': (0, 0),
                                                   'VERY_SMALL': (1, 9),
                                                   'SMALL': (10, 29),
                                                   'MODERATE_OR_LARGER': (30, None)},
                      'sample_bands_are_not_decision_gates': True,
                      'no_composite_score': True,
                      'no_formal_accept_reject_gate': True,
                      'no_automatic_confirmation_label': True,
                      'no_automatic_trading_winner': True},
 'historical_context_plan': {'read_frozen_exp026_outputs_only': True,
                             'historical_strategy_rerun': False,
                             'candidate_context_availability_must_be_disclosed': True,
                             'primary_finalists_have_phase_a_b_c_context': True,
                             'nonfinalist_context_is_phase_dependent': True,
                             'controls_remain_context_only': True,
                             '2026_results_cannot_rewrite_exp026_selection': True,
                             '2026_results_cannot_promote_a_secondary_candidate': True},
 'representation_plan': {'primary': 'BACKWARD_ADJUSTED',
                         'secondary': 'UNADJUSTED',
                         'unadjusted_runs_after_primary_rebuild': True,
                         'unadjusted_is_sensitivity_only': True,
                         'representation_cannot_change_candidate_status': True},
 'reporting_requirements': {'vertical_full_width_layout': True,
                            'plain_english_strategy_rules': True,
                            'all_24_rows_visible': True,
                            'primary_cohort_visually_labelled_not_ranked': True,
                            'all_long_short_metrics_table': True,
                            'full_width_equity_curves': True,
                            'full_width_drawdown_curves': True,
                            'monthly_results': True,
                            'trade_distributions': True,
                            'cost_sensitivity': True,
                            'representation_sensitivity': True,
                            'historical_context_coverage': True,
                            'canonical_trade_ledgers': True,
                            'canonical_equity_series': True,
                            'positive_numbers_use_neutral_text': True,
                            'adverse_numbers_use_red_text': True,
                            'green_reserved_for_status_words': True,
                            'charts_use_opaque_white_canvas': True},
 'required_outputs': {'root': ('candidate_registry.csv',
                               'protected_measurement_summary.json',
                               'protected_measurement_metrics.csv',
                               'monthly_results.csv',
                               'cost_sensitivity.csv',
                               'representation_sensitivity.csv',
                               'trade_distribution.csv',
                               'drawdown_episodes.csv',
                               'historical_context.csv',
                               'output_hashes.json',
                               'report.md',
                               'report.html',
                               'EXP027_COMPLETE.json'),
                      'assets': ('assets/equity_curves.png', 'assets/drawdown_curves.png'),
                      'per_series_pattern': ('series/<candidate_id>/trades.csv',
                                             'series/<candidate_id>/equity.csv',
                                             'series/<candidate_id>/comparison_timeseries.csv',
                                             'series/<candidate_id>/metrics.csv'),
                      'per_series_count': 24,
                      'header_only_trade_ledger_allowed_for_zero_trade_series': True,
                      'flat_equity_series_required_for_zero_trade_series': True},
 'execution_boundary': {'result_free_implementation_commit_required': True,
                        'implementation_preflight_required': True,
                        'separate_execution_authorization_commit_required': True,
                        'one_authorized_run': True,
                        'independent_rebuild_required': True,
                        'serial_parallel_parity_required': True,
                        'rerun_after_completion': False,
                        'results_before_authorization_prohibited': True,
                        'new_databento_download': False,
                        'databento_api_calls': 0,
                        'network_access': False,
                        'order_api_access': False},
 'prohibited_actions': {'modify_exp022_outputs': True,
                        'modify_exp026_preregistration_or_outputs': True,
                        'change_strategy_rules': True,
                        'change_candidate_parameters': True,
                        'change_candidate_population': True,
                        'change_cost_model': True,
                        'optimize_or_select_candidates': True,
                        'rank_for_single_winner': True,
                        'promote_secondary_candidate_from_2026': True,
                        'deserialize_2010_2025_market_rows': True,
                        'download_market_data': True,
                        'call_databento_api': True,
                        'fill_or_repair_missing_bars': True,
                        'paper_trading': True,
                        'live_trading': True,
                        'order_access': True,
                        'capital_deployment': True},
 'hard_checks': ('exp026_closure_commit_and_hash_match',
                 'exp026_preregistration_hash_matches',
                 'exp026_phase_output_manifests_match',
                 'exp022_closure_commit_and_hash_match',
                 'exp022_series_byte_hashes_match',
                 'exp022_series_semantic_hashes_match',
                 'historical_data_policy_hash_matches',
                 'candidate_count_is_twenty_two',
                 'control_count_is_two',
                 'primary_finalists_are_exactly_three',
                 'all_reported_ids_are_unique',
                 'candidate_population_matches_exp026',
                 'strategy_rules_match_exp026',
                 'cost_model_matches_exp026',
                 'only_2026_session_dates_are_deserialized',
                 'session_filter_applied_before_materialization',
                 'historical_market_rows_are_not_deserialized',
                 'no_databento_api_or_network_access',
                 'no_new_download',
                 'missing_minutes_are_not_filled',
                 'synthetic_bars_are_not_created',
                 'source_ohlcv_is_not_modified',
                 'primary_representation_is_backward_adjusted',
                 'unadjusted_representation_is_sensitivity_only',
                 'no_candidate_selection_or_optimization',
                 'no_secondary_candidate_promotion',
                 'all_candidates_remain_visible',
                 'all_long_short_total_metrics_are_reported',
                 'cost_sensitivity_is_reported',
                 'monthly_results_are_reported',
                 'canonical_trade_ledgers_are_written',
                 'canonical_equity_series_are_written',
                 'independent_rebuild_matches',
                 'serial_parallel_results_match',
                 'required_outputs_and_hashes_are_complete',
                 'no_paper_or_live_trading'),
 'hard_check_count': 36,
 'interpretation': {'measurement_first': True,
                    'protected_temporal_measurement': True,
                    'primary_finalists_are_predeclared': True,
                    'secondary_candidates_are_context_not_replacements': True,
                    'all_24_results_are_evidence_rows': True,
                    'no_single_best_strategy_claim': True,
                    'no_automatic_edge_validation': True,
                    'no_strategy_failure_established_automatically': True,
                    'no_strategy_accepted_for_trading': True,
                    'paper_trading_authorized': False,
                    'live_trading_authorized': False}}

EXPECTED_EXP027_PREREGISTRATION_SHA256 = (
    "3177e5bb81bbf330b8a020c3bfee56b584cd284da3546fcdad4b90df5ffd76bd"
)


def canonical_record_hash(
    record: dict[str, Any],
) -> str:
    encoded = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def get_exp027_preregistration() -> dict[str, Any]:
    return deepcopy(EXP027_PREREGISTRATION)


def validate_exp027_preregistration(
    candidate: dict[str, Any] | None = None,
) -> None:
    record = EXP027_PREREGISTRATION if candidate is None else candidate

    if (
        record.get("experiment_id") != "EXP-027"
        or record.get("locked_date") != "2026-07-28"
        or record.get("research_status") != "PRE_REGISTERED"
        or record.get("implementation_status") != "NOT_IMPLEMENTED"
        or record.get("execution_status") != "NOT_RUN"
    ):
        raise ValueError("EXP-027 preregistration identity changed.")

    frozen = record["frozen_inputs"]
    if (
        frozen["exp026_closure_commit"]
        != "7fc1994e396bfb237fd5f05f5a4298e6c5b5e307"
        or frozen["exp026_closure_record_sha256"]
        != "8ec79810a26b58f2d445d47d3f496539f121d6f3e139eae4a9fd38ef029a386f"
        or frozen["exp026_classification"]
        != "COMPLETED_MEASUREMENT_REVIEW"
        or frozen["exp026_preregistration_sha256"]
        != "bbd2e6d8bb50c135d0c6ca04873eed2876c4e7db6a2714b91a934dcf554331a0"
        or frozen["exp022_closure_commit"]
        != "9d157c8e7a6ba584a96cb5d37086672ad5b64ea1"
        or frozen["exp022_closure_record_sha256"]
        != "1cc01baddeeae3acf81b0785923b581fad6aac0b6e36071d07d0d83d35bf588d"
        or frozen["series_row_count"] != 5_457_606
    ):
        raise ValueError("EXP-027 frozen evidence chain changed.")

    period = record["research_period"]
    boundary = record["data_access_boundary"]
    if (
        period["session_start"] != "2026-01-01"
        or period["session_end"] != "2026-07-23"
        or period["results_viewed_before_lock"] is not False
        or boundary["allowed_strategy_session_start"] != "2026-01-01"
        or boundary["allowed_strategy_session_end"] != "2026-07-23"
        or boundary[
            "historical_2010_2025_market_row_deserialization_prohibited"
        ] is not True
        or boundary["no_databento_api_request"] is not True
    ):
        raise ValueError("EXP-027 protected-period boundary changed.")

    population = record["candidate_population"]
    candidate_ids = tuple(population["all_candidate_ids"])
    control_ids = tuple(population["control_ids"])
    reported_ids = tuple(population["all_reported_ids"])
    primary = tuple(population["primary_confirmation_cohort"])
    secondary = tuple(population["secondary_candidate_ids"])

    if (
        population["strategy_candidate_count"] != 22
        or population["control_candidate_count"] != 2
        or population["total_reported_count"] != 24
        or len(candidate_ids) != 22
        or len(control_ids) != 2
        or len(reported_ids) != 24
        or len(reported_ids) != len(set(reported_ids))
        or set(primary) != {
            "gap_fade_0p75_1r",
            "opening_drive_0p75_time",
            "premarket_continuation_0p875_1p5r",
        }
        or len(primary) != 3
        or set(primary) & set(secondary)
        or set(primary) | set(secondary) != set(candidate_ids)
        or tuple(candidate_ids + control_ids) != reported_ids
        or population["selection_in_exp027"] is not False
        or population[
            "secondary_promotion_to_primary_prohibited"
        ] is not True
    ):
        raise ValueError("EXP-027 candidate population changed.")

    objective = record["objective"]
    measurement = record["measurement_plan"]
    if (
        objective["candidate_selection"] is not False
        or objective["parameter_optimization"] is not False
        or objective["single_winner_selection"] is not False
        or objective["formal_accept_reject_gates"] is not False
        or measurement["no_composite_score"] is not True
        or measurement["no_automatic_trading_winner"] is not True
    ):
        raise ValueError("EXP-027 measurement-only design changed.")

    rules = record["strategy_and_execution_rules"]
    costs = record["position_and_cost_model"]
    if (
        rules["all_rules_unchanged_from_exp026"] is not True
        or rules["same_minute_stop_target_rule"] != "STOP_FIRST_CONSERVATIVE"
        or costs["position_size"] != "FIXED_ONE_CONTRACT"
        or costs["base_round_trip_cost_usd"] != 15.0
        or costs["cost_sensitivity_ticks_per_side"] != (0, 1, 2, 3)
    ):
        raise ValueError("EXP-027 strategy or cost rules changed.")

    required = record["required_outputs"]
    if (
        required["per_series_count"] != 24
        or len(required["per_series_pattern"]) != 4
        or "report.html" not in required["root"]
        or "EXP027_COMPLETE.json" not in required["root"]
        or record["reporting_requirements"]["canonical_trade_ledgers"] is not True
        or record["reporting_requirements"]["canonical_equity_series"] is not True
    ):
        raise ValueError("EXP-027 canonical output contract changed.")

    execution = record["execution_boundary"]
    prohibited = record["prohibited_actions"]
    if (
        execution["result_free_implementation_commit_required"] is not True
        or execution["separate_execution_authorization_commit_required"] is not True
        or execution["one_authorized_run"] is not True
        or execution["databento_api_calls"] != 0
        or prohibited["download_market_data"] is not True
        or prohibited["paper_trading"] is not True
        or prohibited["live_trading"] is not True
    ):
        raise ValueError("EXP-027 execution boundary changed.")

    if len(record["hard_checks"]) != record["hard_check_count"]:
        raise ValueError("EXP-027 hard-check count changed.")

    if canonical_record_hash(record) != EXPECTED_EXP027_PREREGISTRATION_SHA256:
        raise ValueError("EXP-027 preregistration record changed.")
