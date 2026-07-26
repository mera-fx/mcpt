from __future__ import annotations

from copy import deepcopy
import hashlib
import json


EXP021_CLOSURE_COMMIT = (
    "253ef695bae819102ec75c3e0cadfa99c8f78d3f"
)

EXPECTED_EXP021_CLOSURE_SHA256 = (
    "f4e1aa2966852c74a966a318dbe427f590c591122bebf02a15bc267338fd21a4"
)

EXP022_PREREGISTRATION = {'schema_version': 1,
 'experiment_id': 'EXP-022',
 'title': 'NQ Selected Volume-Roll Continuous-Series Construction',
 'locked_date': '2026-07-26',
 'research_status': 'PRE_REGISTERED',
 'implementation_status': 'NOT_IMPLEMENTED',
 'execution_status': 'NOT_RUN',
 'objective': {'construct_selected_continuous_series': True,
               'selected_rule_research': False,
               'compare_candidate_rules': False,
               'inspect_strategy_performance': False,
               'market_data_download': False,
               'data_engineering_only': True},
 'prior_result_disclosure': {'exp021_results_viewed_before_lock': True,
                             'known_selected_method': 'VOL_GT_OUT_2S_E3',
                             'known_selection_rank': 4,
                             'known_clean_transition_count': 42,
                             'known_clean_volume_trigger_count': 40,
                             'known_warning_calendar_fallback_count': 23,
                             'known_clean_calendar_fallback_count': 2,
                             'known_total_calendar_fallback_count': 25,
                             'known_noncalendar_roll_date_count': 40,
                             'construction_results_viewed_before_lock': False},
 'frozen_inputs': {'exp021_closure_commit': '253ef695bae819102ec75c3e0cadfa99c8f78d3f',
                   'exp021_closure_record_sha256': 'f4e1aa2966852c74a966a318dbe427f590c591122bebf02a15bc267338fd21a4',
                   'exp021_classification': 'DIAGNOSTIC_METHOD_SELECTED_FOR_SEPARATE_CONSTRUCTION',
                   'exp021_selected_transition_evidence': {'path': 'results/EXP-021/volume_roll_diagnostic/candidate_transition_diagnostics.csv',
                                                           'sha256': '942e7f47fcfc19adfffafd33f04168904a4512967fe0af2d71fd0935c8f2e573',
                                                           'semantic_sha256': '4fd9e261e3b6afe31509f4ec2bf20e58930a8a2dc1e2d30a58215535d439b435',
                                                           'filter_candidate_id': 'VOL_GT_OUT_2S_E3'},
                   'exp019_archive_sha256': '225a64dc06cb6bb303fd83d186f2e7d81e2a8a8bec44382380c8ccc1b0b6baa3',
                   'contract_count': 66,
                   'record_count': 6276486,
                   'adjacent_transition_count': 65,
                   'source_archive_read_only': True,
                   'exp020_outputs_read_only': True,
                   'exp021_outputs_read_only': True,
                   'databento_api_calls': 0},
 'selected_roll_rule': {'candidate_id': 'VOL_GT_OUT_2S_E3',
                        'required_consecutive_sessions': 2,
                        'comparison': 'incoming_daily_volume > outgoing_daily_volume',
                        'maximum_effective_common_sessions_after_calendar': 3,
                        'effective_roll_dates_are_frozen_from_exp021': True,
                        'recalculate_roll_dates': False,
                        'warning_transition_policy': 'Use the frozen EXP-021 calendar '
                                                     'fallback.',
                        'clean_no_trigger_policy': 'Use the frozen EXP-021 calendar '
                                                   'fallback.',
                        'volume_driven_transition_count': 40,
                        'calendar_fallback_transition_count': 25,
                        'provider_warning_fallback_count': 23,
                        'clean_fallback_count': 2},
 'session_definition': {'timezone': 'America/New_York',
                        'session_start_local': '18:00:00',
                        'daylight_saving_time_aware': True,
                        'trading_date_assignment': 'Timestamps at or after 18:00 New '
                                                   'York belong to the following '
                                                   'trading date; earlier timestamps '
                                                   'belong to the local date.',
                        'missing_minutes_not_filled': True,
                        'synthetic_bars_prohibited': True},
 'stitching_rule': {'before_effective_roll_trading_date': 'Use the outgoing contract.',
                    'on_or_after_effective_roll_trading_date': 'Use the incoming '
                                                               'contract.',
                    'intraday_rolls': False,
                    'duplicate_timestamps_permitted': False,
                    'missing_source_minutes_filled': False,
                    'source_ohlcv_modified_in_unadjusted_series': False},
 'adjustment_rule': {'method': 'BACKWARD_DIFFERENCE',
                     'reference_timestamp': 'Latest timestamp present in both adjacent '
                                            'contracts strictly before the effective '
                                            'roll-session boundary.',
                     'roll_difference_points': 'incoming_reference_close - '
                                               'outgoing_reference_close',
                     'application': 'Apply the cumulative roll difference to all '
                                    'earlier open, high, low and close values only.',
                     'latest_segment_adjustment_points': 0.0,
                     'volume_adjusted': False,
                     'instrument_id_adjusted': False,
                     'source_contract_adjusted': False,
                     'trading_date_adjusted': False,
                     'roll_method_adjusted': False},
 'series_specification': {'series_count': 2,
                          'series': ({'series_id': 'SELECTED_ROLL_UNADJUSTED',
                                      'filename': 'selected_roll_unadjusted.parquet',
                                      'price_adjustment': 'NONE'},
                                     {'series_id': 'SELECTED_ROLL_BACKWARD_ADJUSTED',
                                      'filename': 'selected_roll_backward_adjusted.parquet',
                                      'price_adjustment': 'BACKWARD_DIFFERENCE'}),
                          'roll_method_column_value': 'VOL_GT_OUT_2S_E3',
                          'columns': ('ts_event',
                                      'open',
                                      'high',
                                      'low',
                                      'close',
                                      'volume',
                                      'instrument_id',
                                      'source_contract',
                                      'roll_method',
                                      'trading_date',
                                      'adjustment_points'),
                          'timestamp_timezone': 'UTC',
                          'parquet_engine': 'pyarrow',
                          'parquet_compression': 'zstd',
                          'parquet_use_dictionary': False,
                          'parquet_write_statistics': True,
                          'parquet_version': '2.6',
                          'parquet_data_page_version': '1.0',
                          'parquet_row_group_size': 250000,
                          'parquet_schema_metadata': 'exp022_schema=selected-continuous-series-v1'},
 'required_outputs': ('roll_ledger.csv',
                      'contract_contribution.csv',
                      'selected_roll_unadjusted.parquet',
                      'selected_roll_backward_adjusted.parquet',
                      'construction_summary.json',
                      'output_hashes.json',
                      'report.md',
                      'CONSTRUCTION_COMPLETE.json'),
 'hard_checks': ('frozen_exp021_closure_hash_matches',
                 'frozen_exp021_output_hashes_match',
                 'frozen_exp019_archive_hash_matches',
                 'exactly_66_source_contract_files',
                 'source_and_prior_outputs_remain_read_only',
                 'selected_method_is_vol_gt_out_2s_e3',
                 'exactly_65_ordered_transitions',
                 'selected_counts_match_40_25_23_2',
                 'selected_ledger_semantic_hash_matches',
                 'all_boundaries_are_inside_locked_overlap',
                 'no_effective_boundary_is_after_expiry',
                 'one_boundary_per_adjacent_pair',
                 'stitching_boundary_rule_is_exact',
                 'stitched_rows_reconcile_to_source',
                 'timestamps_are_unique_and_monotonic',
                 'adjustment_references_exist_and_are_finite',
                 'backward_adjustment_reconciles',
                 'adjusted_and_unadjusted_nonprice_fields_match',
                 'independent_rebuild_hashes_match',
                 'required_outputs_complete_and_no_strategy_or_api'),
 'hard_check_count': 20,
 'completion_classification': {'qualified': 'QUALIFIED_AS_SELECTED_VOLUME_ROLL_CONTINUOUS_SERIES',
                               'hard_failure': 'CONSTRUCTION_NOT_QUALIFIED',
                               'construction_qualifies_dataset_only': True,
                               'construction_authorizes_strategy_use': False},
 'execution_boundary': {'separate_implementation_commit_required': True,
                        'separate_execution_authorization_required': True,
                        'protected_preflight_required': True,
                        'one_authorized_construction_run': True,
                        'independent_rebuild_required': True,
                        'databento_api_calls': 0,
                        'credentials_required': False,
                        'source_archive_modifications': False,
                        'exp020_output_modifications': False,
                        'exp021_output_modifications': False,
                        'construction_rerun_after_completion': False},
 'prohibited_actions': {'rerun_exp019': True,
                        'rerun_exp020': True,
                        'rerun_exp021': True,
                        'reselect_roll_rule': True,
                        'recalculate_exp021_roll_dates': True,
                        'databento_api_request': True,
                        'new_market_data_download': True,
                        'modify_exp019_archive': True,
                        'modify_exp020_outputs': True,
                        'modify_exp021_outputs': True,
                        'strategy_replay': True,
                        'strategy_optimization': True,
                        'mcpt': True,
                        'bootstrap': True,
                        'walk_forward': True,
                        'paper_trading': True,
                        'live_trading': True},
 'interpretation': {'construction_only': True,
                    'selected_method_is_operational_not_performance_selected': True,
                    'strategy_edge_not_tested': True,
                    'strategy_use_not_authorized': True,
                    'exchange_accuracy_not_claimed': True,
                    'best_vendor_not_claimed': True,
                    'separate_strategy_experiment_required': True}}

EXPECTED_EXP022_PREREGISTRATION_SHA256 = (
    "527b7222fb56e8f070e404e0f49977730fd9709b254157cbb73710ccc6cee252"
)


def canonical_record_hash(record):
    encoded = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def get_exp022_preregistration():
    return deepcopy(EXP022_PREREGISTRATION)


def validate_exp022_preregistration(candidate=None):
    record = (
        EXP022_PREREGISTRATION
        if candidate is None
        else candidate
    )

    if (
        record["experiment_id"] != "EXP-022"
        or record["locked_date"] != "2026-07-26"
        or record["research_status"] != "PRE_REGISTERED"
        or record["implementation_status"] != "NOT_IMPLEMENTED"
        or record["execution_status"] != "NOT_RUN"
    ):
        raise ValueError(
            "EXP-022 preregistration identity changed."
        )

    if (
        record["frozen_inputs"][
            "exp021_closure_commit"
        ]
        != EXP021_CLOSURE_COMMIT
        or record["frozen_inputs"][
            "exp021_closure_record_sha256"
        ]
        != EXPECTED_EXP021_CLOSURE_SHA256
    ):
        raise ValueError(
            "EXP-022 frozen EXP-021 boundary changed."
        )

    if (
        canonical_record_hash(record)
        != EXPECTED_EXP022_PREREGISTRATION_SHA256
    ):
        raise ValueError(
            "EXP-022 preregistration record changed."
        )
