from __future__ import annotations

from copy import deepcopy
import hashlib
import json

EXP020_CLOSURE_COMMIT = "44758ef08152b661f32c152866f5e71743d81acf"
EXPECTED_EXP020_CLOSURE_SHA256 = "d23232285776135e623f35c10db57918274fc475111d70926a241d357f4e106f"
EXP021_PREREGISTRATION = {'schema_version': 1,
 'experiment_id': 'EXP-021',
 'title': 'NQ Volume-Roll Trigger Diagnostic and Rule Selection',
 'locked_date': '2026-07-26',
 'research_status': 'PRE_REGISTERED',
 'implementation_status': 'NOT_IMPLEMENTED',
 'execution_status': 'NOT_RUN',
 'objective': {'diagnose_exp020_inactive_volume_trigger': True,
               'compare_prespecified_volume_rules': True,
               'select_rule_using_market_data_quality_only': True,
               'construct_continuous_series': False,
               'inspect_strategy_performance': False,
               'market_data_download': False},
 'prior_result_disclosure': {'exp020_results_viewed_before_lock': True,
                             'candidate_diagnostic_results_viewed_before_lock': False,
                             'known_exp020_result': {'volume_crossovers_selected': 0,
                                                     'calendar_fallbacks': 65,
                                                     'provider_warning_transitions': 23,
                                                     'fallbacks_without_provider_warnings': 42,
                                                     'identical_roll_dates': 65,
                                                     'unadjusted_market_data_identical': True,
                                                     'adjusted_market_data_identical': True},
                             'candidate_rules_fixed_after_exp020_review': True,
                             'candidate_rules_fixed_before_exp021_execution': True},
 'frozen_inputs': {'exp020_closure_commit': '44758ef08152b661f32c152866f5e71743d81acf',
                   'exp020_closure_record_sha256': 'd23232285776135e623f35c10db57918274fc475111d70926a241d357f4e106f',
                   'exp020_classification': 'QUALIFIED_WITH_DISCLOSED_CALENDAR_FALLBACKS',
                   'exp019_archive_sha256': '225a64dc06cb6bb303fd83d186f2e7d81e2a8a8bec44382380c8ccc1b0b6baa3',
                   'contract_count': 66,
                   'record_count': 6276486,
                   'adjacent_transition_count': 65,
                   'known_provider_warning_windows': 16,
                   'source_archive_read_only': True,
                   'exp020_outputs_read_only': True,
                   'databento_api_calls': 0},
 'session_definition': {'timezone': 'America/New_York',
                        'session_start_local': '18:00:00',
                        'session_end_local_exclusive': '18:00:00 next calendar day',
                        'trading_date_rule': 'Timestamps at or after 18:00 New York '
                                             'belong to the following trading date; '
                                             'earlier timestamps belong to the local '
                                             'date.',
                        'daylight_saving_time_aware': True,
                        'missing_minutes_not_filled': True,
                        'synthetic_bars_prohibited': True},
 'calendar_control': {'method_id': 'CALENDAR_THURSDAY_8_DAYS_BEFORE_EXPIRY',
                      'effective_boundary': 'First common trading session beginning '
                                            'after the Thursday eight calendar days '
                                            'before expiry.',
                      'exp020_roll_ledger_sha256': '6935bc97353cf68344795302ed15f6276af1492900ea333f3fb03ca34ff56214'},
 'diagnostic_window': {'start_common_sessions_before_calendar': 10,
                       'maximum_common_sessions_after_calendar': 3,
                       'trigger_sessions_must_be_consecutive_common_sessions': True,
                       'both_contracts_must_have_observed_volume': True,
                       'strictly_greater_comparison': True,
                       'zero_volume_is_observed_not_missing': True,
                       'no_post_expiry_effective_boundary': True,
                       'intraday_roll_prohibited': True},
 'provider_warning_policy': {'warning_transition_definition': 'Either contract belongs '
                                                              'to the frozen set of 16 '
                                                              'provider-warning '
                                                              'contracts.',
                             'warning_transition_count_expected': 23,
                             'warning_transitions_forced_to_calendar_fallback': True,
                             'warning_volume_may_be_reported_descriptively': True,
                             'warning_volume_may_select_candidate_boundary': False,
                             'warning_conditions_must_remain_disclosed': True},
 'candidate_methods': ({'method_id': 'VOL_GT_OUT_2S_E0',
                        'required_consecutive_sessions': 2,
                        'maximum_effective_common_sessions_after_calendar': 0,
                        'comparison': 'incoming_daily_volume > outgoing_daily_volume',
                        'effective_boundary': 'Next common trading session after the '
                                              'final qualifying trigger session.',
                        'calendar_fallback': True,
                        'control_method': True},
                       {'method_id': 'VOL_GT_OUT_2S_E1',
                        'required_consecutive_sessions': 2,
                        'maximum_effective_common_sessions_after_calendar': 1,
                        'comparison': 'incoming_daily_volume > outgoing_daily_volume',
                        'effective_boundary': 'Next common trading session after the '
                                              'final qualifying trigger session.',
                        'calendar_fallback': True,
                        'control_method': False},
                       {'method_id': 'VOL_GT_OUT_2S_E2',
                        'required_consecutive_sessions': 2,
                        'maximum_effective_common_sessions_after_calendar': 2,
                        'comparison': 'incoming_daily_volume > outgoing_daily_volume',
                        'effective_boundary': 'Next common trading session after the '
                                              'final qualifying trigger session.',
                        'calendar_fallback': True,
                        'control_method': False},
                       {'method_id': 'VOL_GT_OUT_2S_E3',
                        'required_consecutive_sessions': 2,
                        'maximum_effective_common_sessions_after_calendar': 3,
                        'comparison': 'incoming_daily_volume > outgoing_daily_volume',
                        'effective_boundary': 'Next common trading session after the '
                                              'final qualifying trigger session.',
                        'calendar_fallback': True,
                        'control_method': False},
                       {'method_id': 'VOL_GT_OUT_1S_E0',
                        'required_consecutive_sessions': 1,
                        'maximum_effective_common_sessions_after_calendar': 0,
                        'comparison': 'incoming_daily_volume > outgoing_daily_volume',
                        'effective_boundary': 'Next common trading session after the '
                                              'final qualifying trigger session.',
                        'calendar_fallback': True,
                        'control_method': False},
                       {'method_id': 'VOL_GT_OUT_1S_E1',
                        'required_consecutive_sessions': 1,
                        'maximum_effective_common_sessions_after_calendar': 1,
                        'comparison': 'incoming_daily_volume > outgoing_daily_volume',
                        'effective_boundary': 'Next common trading session after the '
                                              'final qualifying trigger session.',
                        'calendar_fallback': True,
                        'control_method': False},
                       {'method_id': 'VOL_GT_OUT_1S_E2',
                        'required_consecutive_sessions': 1,
                        'maximum_effective_common_sessions_after_calendar': 2,
                        'comparison': 'incoming_daily_volume > outgoing_daily_volume',
                        'effective_boundary': 'Next common trading session after the '
                                              'final qualifying trigger session.',
                        'calendar_fallback': True,
                        'control_method': False},
                       {'method_id': 'VOL_GT_OUT_1S_E3',
                        'required_consecutive_sessions': 1,
                        'maximum_effective_common_sessions_after_calendar': 3,
                        'comparison': 'incoming_daily_volume > outgoing_daily_volume',
                        'effective_boundary': 'Next common trading session after the '
                                              'final qualifying trigger session.',
                        'calendar_fallback': True,
                        'control_method': False}),
 'candidate_count': 8,
 'diagnostic_metrics': ('volume_trigger_count_all_transitions',
                        'volume_trigger_count_clean_transitions',
                        'calendar_fallback_count',
                        'noncalendar_roll_date_count',
                        'median_roll_offset_common_sessions',
                        'minimum_roll_offset_common_sessions',
                        'maximum_roll_offset_common_sessions',
                        'warning_transition_count',
                        'clean_transition_count',
                        'first_trigger_session_distribution',
                        'second_trigger_session_distribution'),
 'selection_gates': {'all_hard_checks_must_pass': True,
                     'clean_transition_count': 42,
                     'minimum_clean_volume_trigger_count': 34,
                     'minimum_noncalendar_roll_date_count': 20,
                     'maximum_effective_sessions_after_calendar': 3,
                     'post_expiry_boundary_count': 0,
                     'warning_volume_selected_boundary_count': 0,
                     'all_65_transitions_resolved_with_fallback': True,
                     'selection_uses_strategy_returns': False},
 'fixed_selection_order': ('VOL_GT_OUT_2S_E0',
                           'VOL_GT_OUT_2S_E1',
                           'VOL_GT_OUT_2S_E2',
                           'VOL_GT_OUT_2S_E3',
                           'VOL_GT_OUT_1S_E0',
                           'VOL_GT_OUT_1S_E1',
                           'VOL_GT_OUT_1S_E2',
                           'VOL_GT_OUT_1S_E3'),
 'selection_rule': 'Select the first candidate in fixed_selection_order that passes '
                   'every locked selection gate. Report all candidate results even '
                   'when no candidate is selected.',
 'required_outputs': ('daily_volume_diagnostics.csv',
                      'candidate_transition_diagnostics.csv',
                      'candidate_method_summary.csv',
                      'selected_method.json',
                      'output_hashes.json',
                      'report.md',
                      'DIAGNOSTIC_COMPLETE.json'),
 'hard_checks': ('frozen_exp020_closure_hash_matches',
                 'frozen_exp019_archive_hash_matches',
                 'exactly_66_source_contract_files',
                 'source_and_exp020_outputs_remain_read_only',
                 'all_65_adjacent_transitions_present',
                 'daily_volume_aggregation_is_deterministic',
                 'candidate_matrix_is_exactly_8_methods',
                 'control_reproduces_exp020_zero_crossovers',
                 'warning_transition_count_is_23',
                 'warning_transitions_never_select_volume_boundary',
                 'all_candidates_resolve_65_transitions_with_fallback',
                 'all_boundaries_are_inside_locked_overlap',
                 'no_effective_boundary_is_after_expiry',
                 'no_strategy_or_return_metric_is_computed',
                 'independent_rebuild_hashes_match',
                 'required_outputs_are_complete'),
 'classification': {'selected_result': 'DIAGNOSTIC_METHOD_SELECTED_FOR_SEPARATE_CONSTRUCTION',
                    'no_selection_result': 'DIAGNOSTIC_COMPLETE_NO_METHOD_SELECTED',
                    'hard_failure_result': 'DIAGNOSTIC_NOT_QUALIFIED',
                    'selected_method_authorizes_construction': False,
                    'selected_method_authorizes_strategy_use': False},
 'execution_boundary': {'separate_implementation_commit_required': True,
                        'separate_execution_authorization_required': True,
                        'protected_preflight_required': True,
                        'one_authorized_diagnostic_run': True,
                        'databento_api_calls': 0,
                        'credentials_required': False,
                        'source_archive_modifications': False,
                        'exp020_output_modifications': False,
                        'independent_rebuild_required': True,
                        'diagnostic_rerun_after_completion': False},
 'prohibited_actions': {'rerun_exp019': True,
                        'rerun_exp020': True,
                        'databento_api_request': True,
                        'new_market_data_download': True,
                        'modify_exp019_archive': True,
                        'modify_exp020_outputs': True,
                        'construct_continuous_series': True,
                        'strategy_replay': True,
                        'strategy_optimization': True,
                        'mcpt': True,
                        'bootstrap': True,
                        'walk_forward': True,
                        'paper_trading': True,
                        'live_trading': True},
 'interpretation': {'data_engineering_diagnostic_only': True,
                    'all_candidate_results_must_be_reported': True,
                    'no_pass_fail_result_may_delete_candidate_data': True,
                    'strategy_edge_not_tested': True,
                    'exchange_accuracy_not_claimed': True,
                    'best_vendor_not_claimed': True,
                    'separate_construction_experiment_required': True,
                    'separate_strategy_experiment_required': True}}
EXPECTED_EXP021_PREREGISTRATION_SHA256 = "00218e65ba5722bf0a4f1ba0571e6bea18d34022f32e3d7a689ae5e83d7c93e5"

def canonical_record_hash(record):
    encoded = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

def get_exp021_preregistration():
    return deepcopy(EXP021_PREREGISTRATION)

def validate_exp021_preregistration(candidate=None):
    record = EXP021_PREREGISTRATION if candidate is None else candidate
    if (
        record["experiment_id"] != "EXP-021"
        or record["locked_date"] != "2026-07-26"
        or record["research_status"] != "PRE_REGISTERED"
        or record["implementation_status"] != "NOT_IMPLEMENTED"
        or record["execution_status"] != "NOT_RUN"
    ):
        raise ValueError("EXP-021 preregistration identity changed.")
    if (
        record["frozen_inputs"]["exp020_closure_commit"] != EXP020_CLOSURE_COMMIT
        or record["frozen_inputs"]["exp020_closure_record_sha256"]
        != EXPECTED_EXP020_CLOSURE_SHA256
    ):
        raise ValueError("EXP-021 frozen EXP-020 boundary changed.")
    if canonical_record_hash(record) != EXPECTED_EXP021_PREREGISTRATION_SHA256:
        raise ValueError("EXP-021 preregistration record changed.")
