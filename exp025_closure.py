from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any


EXP025_CLOSURE: dict[str, Any] = {'schema_version': 1,
 'experiment_id': 'EXP-025',
 'closed_date': '2026-07-27',
 'research_status': 'REVIEW',
 'classification': 'BLOCKED_DATA_UNAVAILABLE',
 'repository': {'preregistration_commit': '1d736705a41d0208e353fb17710c8a16cc937710',
                'corrected_implementation_commit': '2011745145b9799a4a42b556d57780002d30e317',
                'quantower_export_authorization_commit': '6a76dba1702f87f7610b0d7346958478c6685ed4',
                'closure_base_head': '6a76dba1702f87f7610b0d7346958478c6685ed4'},
 'locked_records': {'preregistration_sha256': '7534f8ba59a57e79ec98067b3fda3606e5b327a2320c82805cf8001f8c6dd5aa',
                    'quantower_export_plan_sha256': 'd716978b28b98f01798760e8298bf7217585a9f5397da068d1893dd28781e6de',
                    'quantower_export_authorization_sha256': 'bfc06527f421002e54adaed83c1a2d5136c877dd6ef86906aefb6c081ba2b607',
                    'session_quality_sha256': '6b55077783ad2c1cd8ef99f10d50ed7d691aad7cafcdb7e8fa37639d90724712',
                    'historical_data_policy_path': 'research/HISTORICAL_DATA_POLICY.md',
                    'historical_data_policy_sha256': '638cd9da878590bd0cb08302a7fcde81d0fa3380d0d2262af4491c9da63a19b9'},
 'preflight_history': {'implementation_preflight_passed': True,
                       'implementation_preflight_head': '2011745145b9799a4a42b556d57780002d30e317',
                       'quantower_export_preflight_passed': True,
                       'quantower_export_preflight_head': '6a76dba1702f87f7610b0d7346958478c6685ed4',
                       'frozen_unresolved_session_count': 43,
                       'unique_exact_contract_count': 22,
                       'authorized_window_export_count': 86,
                       'authorized_final_evidence_file_count': 43},
 'provider_access_evidence': {'required_canonical_contract': 'NQH20',
                              'quantower_symbols_searched': ['NQH20',
                                                             'NQH0',
                                                             'NQH0.CME'],
                              'quantower_expired_contract_found': False,
                              'rtrader_symbols_searched': ['NQH0.CME'],
                              'rtrader_expired_contract_found': False,
                              'generic_nq_history_available': True,
                              'generic_nq_construction_confirmed': False,
                              'generic_nq_roll_trigger_confirmed': False,
                              'generic_nq_adjustment_method_confirmed': False,
                              'lucid_ai_documentation_confirmed_access': False,
                              'human_provider_confirmation_obtained': False},
 'evidence': {'accepted_exact_contract_file_count': 0,
              'accepted_exact_contract_manifest_created': False,
              'rejected_generic_nq_file_count': 2,
              'rejected_generic_nq_files': {'data/EXP-025/quantower_export_staging/rejected_generic_nq/01_2020-01-22_GENERIC_NQ_previous.csv': {'size_bytes': 44529,
                                                                                                                                                'sha256': '622945e4ef717c3b4d3fd32e1c30e0d84d4f39367a9fa3839c2dd9b71e1ca809',
                                                                                                                                                'data_rows': 389,
                                                                                                                                                'first_timestamp': '2020-01-21 '
                                                                                                                                                                   '09:30:00.000',
                                                                                                                                                'last_timestamp': '2020-01-21 '
                                                                                                                                                                  '15:58:00.000',
                                                                                                                                                'delimiter': ';',
                                                                                                                                                'accepted_as_exact_contract_evidence': False},
                                            'data/EXP-025/quantower_export_staging/rejected_generic_nq/01_2020-01-22_GENERIC_NQ_current.csv': {'size_bytes': 656,
                                                                                                                                               'sha256': '3b12528811de9fbefdd7037e6b355647d8f542da400f3f2f46ba7528ba5d43fe',
                                                                                                                                               'data_rows': 5,
                                                                                                                                               'first_timestamp': '2020-01-22 '
                                                                                                                                                                  '09:30:00.000',
                                                                                                                                               'last_timestamp': '2020-01-22 '
                                                                                                                                                                 '09:34:00.000',
                                                                                                                                               'delimiter': ';',
                                                                                                                                               'accepted_as_exact_contract_evidence': False}},
              'generic_csv_explicit_contract_column_present': False,
              'renamed_filename_proves_contract_identity': False,
              'generic_nq_files_accepted_for_diagnostic': False},
 'execution': {'format_verification_attempted': True,
               'quantower_export_phase_completed': False,
               'execution_authorization_created': False,
               'diagnostic_executed': False,
               'decision_engine_comparison_executed': False,
               'strategy_replay_executed': False,
               'exit_evaluation_executed': False,
               'performance_evaluation_executed': False,
               'optimization_executed': False,
               'mcpt_executed': False,
               'bootstrap_executed': False,
               'walk_forward_executed': False,
               'databento_api_calls': 0,
               'new_databento_download_performed': False,
               'network_access_by_python': False,
               'order_api_accessed': False,
               'paper_trading_authorized': False,
               'live_trading_authorized': False},
 'interpretation': {'exact_contract_comparison_completed': False,
                    'decision_engine_qualified': False,
                    'source_equivalence_established': False,
                    'quantower_selected_as_ground_truth': False,
                    'databento_selected_as_ground_truth_by_exp025': False,
                    'strategy_edge_validated': False,
                    'strategy_failure_established': False,
                    'candidate_selected_or_rejected': False,
                    'no_strategy_conclusion_permitted': True,
                    'closure_is_data_availability_outcome_only': True},
 'next_research_boundary': {'exp025_frozen': True,
                            'rerun_exp025_preflight_prohibited': True,
                            'rerun_exp025_export_phase_prohibited': True,
                            'rerun_exp025_diagnostic_prohibited': True,
                            'generic_nq_rescue_prohibited': True,
                            'modify_exp025_preregistration_prohibited': True,
                            'modify_exp025_authorization_prohibited': True,
                            'databento_primary_for_future_historical_testing': True,
                            'existing_frozen_databento_archives_may_be_reused': True,
                            'new_databento_download_authorized_by_closure': False,
                            'new_experiment_required_for_cross_provider_comparison': True,
                            'paper_or_live_trading_not_authorized': True}}

EXPECTED_EXP025_CLOSURE_SHA256 = (
    "b386a0c45a81e40a3f9459f802882b8c749b6038e1d447b75d14d59acfea660c"
)


def canonical_record_hash(record: dict[str, Any]) -> str:
    encoded = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def get_exp025_closure() -> dict[str, Any]:
    return deepcopy(EXP025_CLOSURE)


def validate_exp025_closure(
    candidate: dict[str, Any] | None = None,
) -> None:
    record = EXP025_CLOSURE if candidate is None else candidate

    if (
        record.get("experiment_id") != "EXP-025"
        or record.get("closed_date") != "2026-07-27"
        or record.get("research_status") != "REVIEW"
        or record.get("classification")
        != "BLOCKED_DATA_UNAVAILABLE"
    ):
        raise ValueError("EXP-025 closure identity changed.")

    repository = record["repository"]
    if (
        repository.get("preregistration_commit")
        != "1d736705a41d0208e353fb17710c8a16cc937710"
        or repository.get("corrected_implementation_commit")
        != "2011745145b9799a4a42b556d57780002d30e317"
        or repository.get("quantower_export_authorization_commit")
        != "6a76dba1702f87f7610b0d7346958478c6685ed4"
    ):
        raise ValueError(
            "EXP-025 closure repository chain changed."
        )

    evidence = record["evidence"]
    execution = record["execution"]
    interpretation = record["interpretation"]
    boundary = record["next_research_boundary"]

    if (
        evidence.get("accepted_exact_contract_file_count") != 0
        or evidence.get("rejected_generic_nq_file_count") != 2
        or evidence.get(
            "generic_csv_explicit_contract_column_present"
        ) is not False
        or evidence.get(
            "generic_nq_files_accepted_for_diagnostic"
        ) is not False
        or execution.get("diagnostic_executed") is not False
        or execution.get("performance_evaluation_executed")
        is not False
        or execution.get("databento_api_calls") != 0
        or interpretation.get(
            "no_strategy_conclusion_permitted"
        ) is not True
        or interpretation.get(
            "closure_is_data_availability_outcome_only"
        ) is not True
    ):
        raise ValueError(
            "EXP-025 closure evidence boundary changed."
        )

    if (
        boundary.get("exp025_frozen") is not True
        or boundary.get(
            "databento_primary_for_future_historical_testing"
        ) is not True
        or boundary.get(
            "new_databento_download_authorized_by_closure"
        ) is not False
        or boundary.get(
            "paper_or_live_trading_not_authorized"
        ) is not True
    ):
        raise ValueError(
            "EXP-025 closure next-research boundary changed."
        )

    if (
        canonical_record_hash(record)
        != EXPECTED_EXP025_CLOSURE_SHA256
    ):
        raise ValueError("EXP-025 closure record changed.")
