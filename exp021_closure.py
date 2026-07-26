from __future__ import annotations

from copy import deepcopy
import hashlib
import json


EXP021_CLOSURE = {'schema_version': 1,
 'experiment_id': 'EXP-021',
 'closed_date': '2026-07-26',
 'research_status': 'REVIEW',
 'classification': 'DIAGNOSTIC_METHOD_SELECTED_FOR_SEPARATE_CONSTRUCTION',
 'repository': {'preregistration_commit': '27a960ad68f2059e5ac9d60e42e41a9171fbda41',
                'implementation_commit': '9d365613619e21b9fe4eb9625bba907efd60ecfa',
                'authorization_commit': '790918d8a484b08cff2bfff17edc907141547079',
                'execution_head': '790918d8a484b08cff2bfff17edc907141547079'},
 'source': {'exp019_archive_sha256': '225a64dc06cb6bb303fd83d186f2e7d81e2a8a8bec44382380c8ccc1b0b6baa3',
            'exp020_closure_commit': '44758ef08152b661f32c152866f5e71743d81acf',
            'exp020_closure_record_sha256': 'd23232285776135e623f35c10db57918274fc475111d70926a241d357f4e106f',
            'contract_count': 66,
            'record_count': 6276486,
            'archive_or_prior_output_modified': False},
 'diagnostic': {'started_at_utc': '2026-07-26T13:15:45.232671+00:00',
                'completed_at_utc': '2026-07-26T13:16:15.466092+00:00',
                'candidate_count': 8,
                'transition_count_per_candidate': 65,
                'hard_checks': 16,
                'hard_failure_count': 0,
                'independent_rebuild': True,
                'databento_api_calls': 0,
                'continuous_construction': False,
                'strategy_run': False,
                'diagnostic_complete': True,
                'diagnostic_rerun_authorized': False},
 'selected_method': {'candidate_id': 'VOL_GT_OUT_2S_E3',
                     'selection_rank': 4,
                     'required_consecutive_sessions': 2,
                     'maximum_effective_common_sessions_after_calendar': 3,
                     'selected_by_fixed_preregistered_order': True,
                     'clean_transition_count': 42,
                     'clean_volume_trigger_count': 40,
                     'warning_calendar_fallback_count': 23,
                     'clean_calendar_fallback_count': 2,
                     'total_calendar_fallback_count': 25,
                     'noncalendar_roll_date_count': 40,
                     'construction_authorized': False,
                     'strategy_use_authorized': False},
 'passing_candidates': ({'selection_rank': 4,
                         'candidate_id': 'VOL_GT_OUT_2S_E3',
                         'clean_triggers': 40,
                         'calendar_fallbacks': 25,
                         'noncalendar_roll_dates': 40},
                        {'selection_rank': 7,
                         'candidate_id': 'VOL_GT_OUT_1S_E2',
                         'clean_triggers': 40,
                         'calendar_fallbacks': 25,
                         'noncalendar_roll_dates': 40},
                        {'selection_rank': 8,
                         'candidate_id': 'VOL_GT_OUT_1S_E3',
                         'clean_triggers': 42,
                         'calendar_fallbacks': 23,
                         'noncalendar_roll_dates': 42}),
 'clean_fallbacks': ({'transition_sequence': 59,
                      'outgoing_contract': 'NQZ24',
                      'incoming_contract': 'NQH25',
                      'expiration': '2024-12-20',
                      'calendar_roll_date': '2024-12-13',
                      'diagnostic_window_start': '2024-11-29',
                      'diagnostic_window_end': '2024-12-18',
                      'trigger_type': 'CALENDAR_FALLBACK_NO_TRIGGER'},
                     {'transition_sequence': 60,
                      'outgoing_contract': 'NQH25',
                      'incoming_contract': 'NQM25',
                      'expiration': '2025-03-21',
                      'calendar_roll_date': '2025-03-14',
                      'diagnostic_window_start': '2025-02-28',
                      'diagnostic_window_end': '2025-03-19',
                      'trigger_type': 'CALENDAR_FALLBACK_NO_TRIGGER'}),
 'pairwise_roll_date_differences': ({'left': 'VOL_GT_OUT_2S_E3',
                                     'right': 'VOL_GT_OUT_1S_E2',
                                     'different_roll_dates': 40,
                                     'transition_count': 65},
                                    {'left': 'VOL_GT_OUT_2S_E3',
                                     'right': 'VOL_GT_OUT_1S_E3',
                                     'different_roll_dates': 42,
                                     'transition_count': 65},
                                    {'left': 'VOL_GT_OUT_1S_E2',
                                     'right': 'VOL_GT_OUT_1S_E3',
                                     'different_roll_dates': 2,
                                     'transition_count': 65}),
 'semantic_hashes': {'candidate_summary_semantic_sha256': '53e53be40e5da4ee97f9a341089a349bc47f1fe1b236305fa0ea0f5bed1c4d6e',
                     'candidate_transition_semantic_sha256': '4fd9e261e3b6afe31509f4ec2bf20e58930a8a2dc1e2d30a58215535d439b435',
                     'daily_volume_semantic_sha256': 'e0760762ab38a4b339d055c6b1299db57f67b4ec01396641727ac7b4ceee363c',
                     'selected_method_semantic_sha256': '0944c520d280340b80445515558656ea00cc86fc0cf5d4c8694fc2cf77e236be'},
 'output_files': {'candidate_method_summary.csv': {'size_bytes': 1466,
                                                   'sha256': 'f2680cd31c5f9ede27b1931655ff1f59cbf54e0a014e22d8ee9a506077a78206'},
                  'candidate_transition_diagnostics.csv': {'size_bytes': 81792,
                                                           'sha256': '942e7f47fcfc19adfffafd33f04168904a4512967fe0af2d71fd0935c8f2e573'},
                  'daily_volume_diagnostics.csv': {'size_bytes': 67400,
                                                   'sha256': 'f18e037f3d0cfc3c1d1619f12dc5b620b45dc85378f07cd34c5cd7a7acd493cf'},
                  'DIAGNOSTIC_COMPLETE.json': {'size_bytes': 2622,
                                               'sha256': '1b90a4aec2923e38117bfa6cacd3ac538192672afdc86f19e8ce3402a6e6f3a7'},
                  'output_hashes.json': {'size_bytes': 1039,
                                         'sha256': '2bc90acf41fd2cf0ac376cf2c2847402090a3016d481ae74b26dd142238750d2'},
                  'report.md': {'size_bytes': 832,
                                'sha256': 'd7775490c57c43877e2cd4c6abb8b51eeaf2c96c583dbf20203f810109acb5d5'},
                  'selected_method.json': {'size_bytes': 232,
                                           'sha256': '294bfe080d8d6deb272099ba9764f25a4e1d940c12047802d683218cbbf7886f'}},
 'interpretation': {'operational_roll_rule_selected': True,
                    'selection_based_on_strategy_performance': False,
                    'passing_candidates_are_equivalent': False,
                    'aggregate_counts_hide_schedule_differences': True,
                    'continuous_series_constructed': False,
                    'strategy_edge_tested': False,
                    'strategy_use_authorized': False,
                    'exchange_accuracy_verified': False,
                    'best_vendor_selected': False,
                    'paper_trading_authorized': False,
                    'live_trading_authorized': False},
 'next_research_boundary': {'exp021_frozen': True,
                            'rerun_exp021_prohibited': True,
                            'new_experiment_id_required': True,
                            'exp022_preregistration_required': True,
                            'exp022_construction_only': True,
                            'strategy_research_not_authorized': True}}

EXPECTED_EXP021_CLOSURE_SHA256 = "f4e1aa2966852c74a966a318dbe427f590c591122bebf02a15bc267338fd21a4"


def canonical_record_hash(record):
    encoded = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def get_exp021_closure():
    return deepcopy(EXP021_CLOSURE)


def validate_exp021_closure(record=None):
    candidate = EXP021_CLOSURE if record is None else record
    if (
        candidate["experiment_id"] != "EXP-021"
        or candidate["closed_date"] != "2026-07-26"
        or candidate["research_status"] != "REVIEW"
        or candidate["classification"]
        != "DIAGNOSTIC_METHOD_SELECTED_FOR_SEPARATE_CONSTRUCTION"
    ):
        raise ValueError("EXP-021 closure identity changed.")
    if canonical_record_hash(candidate) != EXPECTED_EXP021_CLOSURE_SHA256:
        raise ValueError("EXP-021 closure record changed.")
