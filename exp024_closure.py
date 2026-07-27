from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any


EXP024_CLOSURE: dict[str, Any] = {'schema_version': 1,
 'experiment_id': 'EXP-024',
 'closed_date': '2026-07-27',
 'research_status': 'REVIEW',
 'classification': 'ATTRIBUTION_DIAGNOSTIC_NOT_QUALIFIED',
 'repository': {'preregistration_commit': '37a6d007b103bb5baddfdbbe471a8b6626b8a35c',
                'original_implementation_commit': '1113202f3664d8114f9a7abf4184c6db53f487cd',
                'lifecycle_guard_correction_commit': '34f7d4c83dee025108229d5247e9cb4f87398a59',
                'original_authorization_commit': '55ae174f5517bdb5afc48f5a36f5268fbc1eb42a',
                'attempt_001_record_and_replacement_commit': 'fb5b8f02ac54cccf29c5d23452db6d8e9ac4589e',
                'replacement_authorization_commit': 'da7bbe843361fd9d08cf64cc1e772c9eabf82fb5',
                'attempt_002_failure_commit': '7acf180c9640079c560c992a00c4fd413f3b13b7',
                'evidence_recovery_implementation_commit': 'a57ebcbc237e2e8e8696e9d6b3b13f584102beee',
                'evidence_recovery_authorization_commit': 'b885c3fd8342d9d656c175c4c66f837954eb9452',
                'evidence_recovery_execution_head': 'b885c3fd8342d9d656c175c4c66f837954eb9452'},
 'locked_records': {'preregistration_sha256': '6bc6b7b493aa5eb4a58699fd8cd2c0af15d6c8cfe5323edf9cb3bba1193e3871',
                    'attempt_002_failure_sha256': 'd58e747db36ae3c5e80a034e3b6de127d9771184805470a16f0d3adbbab77359',
                    'evidence_recovery_authorization_sha256': '8d5b319b8550dcf12ebb616905a15793209eb996ee49663191ab8607671c3c7c',
                    'closure_evidence_zip_sha256': '7555c9a124c8f95174154cfd9d27bea4f58f81427ca92cf6d80a3ad7b9d7592d'},
 'execution': {'attempt_001_authorized': True,
               'attempt_001_attribution_calculated': False,
               'attempt_002_authorized': True,
               'attempt_002_attribution_calculated': True,
               'independent_attribution_rebuild_completed': True,
               'independent_attribution_rebuild_hashes_match': True,
               'publication_recovery_count': 1,
               'publication_mode': 'EVIDENCE_ONLY_RECOVERY',
               'completed_at_utc': '2026-07-27T14:29:24.519236+00:00',
               'final_output_file_count': 14,
               'preserved_artifact_count': 9,
               'generated_publication_file_count': 5,
               'partial_output_directory_absent': True,
               'final_output_directory_present': True,
               'original_locked_hard_check_count': 26,
               'reported_diagnostic_hard_check_count': 8,
               'diagnostic_hard_failure_count': 1,
               'recovery_hard_check_count': 18,
               'recovery_hard_failure_count': 0,
               'protected_history_accessed': False,
               'out_of_overlap_values_accessed': False,
               'current_post_entry_values_accessed': False,
               'volume_materialized': False,
               'publication_recovery_market_parquet_accessed': False,
               'publication_recovery_attribution_recalculated': False,
               'publication_recovery_charts_rebuilt': False,
               'databento_api_calls': 0,
               'network_access': False,
               'strategy_replay': False,
               'exit_evaluation': False,
               'performance_evaluation': False,
               'optimization': False,
               'mcpt': False,
               'bootstrap': False,
               'walk_forward': False,
               'paper_trading_authorized': False,
               'live_trading_authorized': False,
               'publication_complete': True,
               'diagnostic_qualified': False,
               'rerun_authorized': False},
 'diagnostic_result': {'candidate_session_row_count': 51,
                       'feature_row_count': 153,
                       'raw_component_difference_row_count': 1530,
                       'roll_context_row_count': 51,
                       'aggregation_check_row_count': 4709,
                       'aggregation_all_ohlc_match': True,
                       'reference_rebuild_match_rows': 8,
                       'reference_rebuild_failure_rows': 43,
                       'reference_failures_all_gap_fade': True,
                       'transfer_rebuild_match_rows': 51,
                       'unresolved_rows': 43,
                       'failed_hard_check': 'reference_decision_rebuild_matches_frozen_alignment',
                       'category_counts': {'CONTEXT_DIRECTION_DIFFERENCE': 0,
                                           'ELIGIBILITY_DIFFERENCE': 1,
                                           'ENTRY_RISK_VALIDITY_DIFFERENCE': 0,
                                           'FIRST_CASH_BAR_CONFIRMATION_DIFFERENCE': 0,
                                           'MULTIPLE_DECISION_COMPONENT_DIFFERENCES': 2,
                                           'NORMALIZED_CONTEXT_THRESHOLD_CROSSING': 5,
                                           'UNRESOLVED_WITH_LOCKED_FEATURES': 43}},
 'output_manifest_sha256': '93803c61ef670193556b2c7f1acb43a3cef9d4d6a692ead3afcf22baa1601cad',
 'completion_marker_sha256': 'b594f9177bafb3b5081ffdc37708b74c6da9294ec212885d0d3f99530ff63601',
 'output_files': {'aggregation_check.csv': {'size_bytes': 641094,
                                            'sha256': 'c2c693c142a076db404739047f8e683cb63e1c218f057e1c3d46b9c20f63a7fa'},
                  'ATTRIBUTION_DIAGNOSTIC_COMPLETE.json': {'size_bytes': 841,
                                                           'sha256': 'b594f9177bafb3b5081ffdc37708b74c6da9294ec212885d0d3f99530ff63601'},
                  'attribution_summary.json': {'size_bytes': 5210,
                                               'sha256': '86cf29b0b15488ec534b69adb67529833b1031333c298030862bbcc6301eac3e'},
                  'feature_comparison.csv': {'size_bytes': 38064,
                                             'sha256': 'd10a5ffb4e01ee0b7ab65d65f721ab5beca0a4b9cfac6eca4fdacc82c9bd595c'},
                  'mismatch_attribution.csv': {'size_bytes': 6797,
                                               'sha256': '1f762b2cbb2d53c0cd979171a584a42fb3e8742040b2c3bb9494155e7d55dbae'},
                  'output_hashes.json': {'size_bytes': 1818,
                                         'sha256': '93803c61ef670193556b2c7f1acb43a3cef9d4d6a692ead3afcf22baa1601cad'},
                  'raw_component_differences.csv': {'size_bytes': 163741,
                                                    'sha256': 'de13b28fb809ce5b267816b126b71ecbe3ae4d2d396b7cab9bbf9860e417c457'},
                  'report.html': {'size_bytes': 10850,
                                  'sha256': '39f8d6f7f4db241a0d9da03575a78432cd58d3cdc54a589ed997d3ba33bfd9fb'},
                  'report.md': {'size_bytes': 7363,
                                'sha256': 'd5e796c6fc17375ca6d735e0c932d49ec0197ea6d3d5bb5dba35e0b4307b4571'},
                  'roll_context.csv': {'size_bytes': 8791,
                                       'sha256': '35ec1eba30a6eeea59ab369b89a575b0cad44cf23b6b3ca89d494a8ef6428ffc'},
                  'assets/attribution_categories.png': {'size_bytes': 74003,
                                                        'sha256': '9c88dc6b2c68fd36eb471b0c8298e8e3d455de80fbef0a29d511ba4e8d4d5f85'},
                  'assets/raw_component_differences.png': {'size_bytes': 79515,
                                                           'sha256': '8e81cf3d629653841c90abac421e37b7f994ced81490eb1420ee7fb3e58f3214'},
                  'assets/roll_context.png': {'size_bytes': 57825,
                                              'sha256': 'f8b9fd976c18ce3e227dacb5317adf96f73ee4c769548e5ca892a5ccaf13e0bf'},
                  'assets/threshold_margins.png': {'size_bytes': 89786,
                                                   'sha256': 'f7489bb363b51e9a6250a53ca262d545c3dbf6cac93fa09b31132cd056dde7a6'}},
 'interpretation': {'known_overlap_attribution_diagnostic_only': True,
                    'diagnostic_hard_failure_requires_stop': True,
                    'source_equivalence_established': False,
                    'source_winner_selected': False,
                    'candidate_winner_selected': False,
                    'quantower_assumed_ground_truth': False,
                    'databento_assumed_ground_truth': False,
                    'strategy_edge_validated': False,
                    'independent_edge_confirmation': False,
                    'protected_history_unlocked': False,
                    'data_or_engine_qualification_required_before_strategy_validation': True,
                    'paper_trading_authorized': False,
                    'live_trading_authorized': False},
 'next_research_boundary': {'exp024_frozen': True,
                            'rerun_any_exp024_mode_prohibited': True,
                            'rerun_preflight_prohibited': True,
                            'rerun_original_attribution_prohibited': True,
                            'rerun_replacement_attribution_prohibited': True,
                            'rerun_evidence_recovery_prohibited': True,
                            'modify_exp024_outputs_prohibited': True,
                            'candidate_or_source_rescue_prohibited': True,
                            'protected_history_remains_locked': True,
                            'new_experiment_id_required': True,
                            'exp025_or_later_preregistration_required': True,
                            'separate_implementation_and_authorization_required': True,
                            'paper_or_live_trading_not_authorized': True}}

EXPECTED_EXP024_CLOSURE_SHA256 = (
    "f11d3dc899d6ffcb1e24be6113715240da7ab7af109b1ab45daac64f5aadf183"
)


def canonical_record_hash(record: dict[str, Any]) -> str:
    encoded = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def get_exp024_closure() -> dict[str, Any]:
    return deepcopy(EXP024_CLOSURE)


def validate_exp024_closure(
    candidate: dict[str, Any] | None = None,
) -> None:
    record = EXP024_CLOSURE if candidate is None else candidate
    if (
        record["experiment_id"] != "EXP-024"
        or record["closed_date"] != "2026-07-27"
        or record["research_status"] != "REVIEW"
        or record["classification"]
        != "ATTRIBUTION_DIAGNOSTIC_NOT_QUALIFIED"
    ):
        raise ValueError("EXP-024 closure identity changed.")

    execution = record["execution"]
    result = record["diagnostic_result"]
    if (
        execution["publication_recovery_count"] != 1
        or execution["publication_complete"] is not True
        or execution["diagnostic_qualified"] is not False
        or execution["diagnostic_hard_failure_count"] != 1
        or execution["rerun_authorized"] is not False
        or result["candidate_session_row_count"] != 51
        or result["reference_rebuild_match_rows"] != 8
        or result["reference_rebuild_failure_rows"] != 43
        or result["transfer_rebuild_match_rows"] != 51
        or result["unresolved_rows"] != 43
    ):
        raise ValueError("EXP-024 closure result boundary changed.")

    if len(record["output_files"]) != 14:
        raise ValueError("EXP-024 closure output set changed.")

    if (
        canonical_record_hash(record)
        != EXPECTED_EXP024_CLOSURE_SHA256
    ):
        raise ValueError("EXP-024 closure record changed.")
