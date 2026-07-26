from __future__ import annotations

from copy import deepcopy
import hashlib
import json


EXP021_DIAGNOSTIC_AUTHORIZATION = {'schema_version': 1,
 'experiment_id': 'EXP-021',
 'authorization_date': '2026-07-26',
 'authorization_status': 'AUTHORIZED_FOR_ONE_TIME_DIAGNOSTIC',
 'locked_preregistration_commit': '27a960ad68f2059e5ac9d60e42e41a9171fbda41',
 'locked_preregistration_record_sha256': '00218e65ba5722bf0a4f1ba0571e6bea18d34022f32e3d7a689ae5e83d7c93e5',
 'locked_implementation_commit': '9d365613619e21b9fe4eb9625bba907efd60ecfa',
 'locked_implementation_paths': ('exp021_diagnostic.py',
                                 'exp021_diagnostic_core.py',
                                 'tests/test_exp021_diagnostic.py',
                                 'research/EXP-021_implementation_report.md'),
 'diagnostic_authorized': True,
 'one_time_diagnostic': True,
 'maximum_diagnostic_runs': 1,
 'protected_preflight_required': True,
 'diagnostic_confirmation_flag_required': True,
 'databento_api_calls': 0,
 'credentials_required': False,
 'source_boundary': {'exp019_archive_read_only': True,
                     'exp019_archive_sha256': '225a64dc06cb6bb303fd83d186f2e7d81e2a8a8bec44382380c8ccc1b0b6baa3',
                     'exp020_outputs_read_only': True,
                     'exp020_closure_commit': '44758ef08152b661f32c152866f5e71743d81acf',
                     'exp020_closure_record_sha256': 'd23232285776135e623f35c10db57918274fc475111d70926a241d357f4e106f',
                     'contract_count': 66,
                     'record_count': 6276486},
 'diagnostic_scope': {'candidate_method_count': 8,
                      'transition_count_per_candidate': 65,
                      'hard_check_count': 16,
                      'independent_rebuild_required': True,
                      'all_candidate_results_retained': True,
                      'selection_uses_strategy_returns': False,
                      'continuous_series_construction': False},
 'allowed_actions': {'protected_read_only_preflight': True,
                     'one_local_diagnostic_run': True,
                     'write_exp021_diagnostic_outputs': True},
 'prohibited_actions': {'rerun_exp019': True,
                        'rerun_exp020': True,
                        'databento_api_request': True,
                        'new_market_data_download': True,
                        'modify_exp019_archive': True,
                        'modify_exp020_outputs': True,
                        'continuous_series_construction': True,
                        'strategy_replay': True,
                        'strategy_optimization': True,
                        'mcpt': True,
                        'bootstrap': True,
                        'walk_forward': True,
                        'paper_trading': True,
                        'live_trading': True},
 'continuous_construction_authorized': False,
 'strategy_run_authorized': False,
 'strategy_use_authorized': False,
 'paper_trading_authorized': False,
 'live_trading_authorized': False,
 'diagnostic_rerun_after_completion': False,
 'interpretation': {'diagnostic_data_engineering_only': True,
                    'selected_method_requires_separate_construction_experiment': True,
                    'strategy_research_requires_separate_experiment': True,
                    'exchange_accuracy_not_claimed': True,
                    'best_vendor_not_claimed': True}}

EXPECTED_EXP021_DIAGNOSTIC_AUTHORIZATION_SHA256 = (
    "56eede13d2f630b6a52af97a2146263cb6493368d6303010e366a2f7267e0f6a"
)


def canonical_record_hash(record):
    encoded = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def get_exp021_diagnostic_authorization():
    return deepcopy(
        EXP021_DIAGNOSTIC_AUTHORIZATION
    )


def validate_exp021_diagnostic_authorization(
    candidate=None,
):
    record = (
        EXP021_DIAGNOSTIC_AUTHORIZATION
        if candidate is None
        else candidate
    )

    if (
        record["experiment_id"] != "EXP-021"
        or record["authorization_date"] != "2026-07-26"
        or record["authorization_status"]
        != "AUTHORIZED_FOR_ONE_TIME_DIAGNOSTIC"
        or record["locked_preregistration_commit"]
        != "27a960ad68f2059e5ac9d60e42e41a9171fbda41"
        or record["locked_implementation_commit"]
        != "9d365613619e21b9fe4eb9625bba907efd60ecfa"
    ):
        raise ValueError(
            "EXP-021 diagnostic authorization "
            "identity changed."
        )

    if (
        canonical_record_hash(record)
        != EXPECTED_EXP021_DIAGNOSTIC_AUTHORIZATION_SHA256
    ):
        raise ValueError(
            "EXP-021 diagnostic authorization "
            "record changed."
        )
