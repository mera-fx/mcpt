from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any


EXP024_EVIDENCE_RECOVERY_AUTHORIZATION: dict[str, Any] = {'schema_version': 1,
 'experiment_id': 'EXP-024',
 'authorization_id': 'EXP-024-EVIDENCE-RECOVERY-AUTH-001',
 'authorized_date': '2026-07-27',
 'evidence_recovery_authorized': True,
 'one_time_recovery': True,
 'maximum_recovery_runs': 1,
 'locked_recovery_implementation_commit': 'a57ebcbc237e2e8e8696e9d6b3b13f584102beee',
 'attempt_002_failure_commit': '7acf180c9640079c560c992a00c4fd413f3b13b7',
 'attempt_002_failure_record_sha256': 'd58e747db36ae3c5e80a034e3b6de127d9771184805470a16f0d3adbbab77359',
 'partial_artifact_count': 9,
 'preserved_artifacts': {'aggregation_check.csv': {'size_bytes': 641094,
                                                   'sha256': 'c2c693c142a076db404739047f8e683cb63e1c218f057e1c3d46b9c20f63a7fa'},
                         'assets/attribution_categories.png': {'size_bytes': 74003,
                                                               'sha256': '9c88dc6b2c68fd36eb471b0c8298e8e3d455de80fbef0a29d511ba4e8d4d5f85'},
                         'assets/raw_component_differences.png': {'size_bytes': 79515,
                                                                  'sha256': '8e81cf3d629653841c90abac421e37b7f994ced81490eb1420ee7fb3e58f3214'},
                         'assets/roll_context.png': {'size_bytes': 57825,
                                                     'sha256': 'f8b9fd976c18ce3e227dacb5317adf96f73ee4c769548e5ca892a5ccaf13e0bf'},
                         'assets/threshold_margins.png': {'size_bytes': 89786,
                                                          'sha256': 'f7489bb363b51e9a6250a53ca262d545c3dbf6cac93fa09b31132cd056dde7a6'},
                         'feature_comparison.csv': {'size_bytes': 38064,
                                                    'sha256': 'd10a5ffb4e01ee0b7ab65d65f721ab5beca0a4b9cfac6eca4fdacc82c9bd595c'},
                         'mismatch_attribution.csv': {'size_bytes': 6797,
                                                      'sha256': '1f762b2cbb2d53c0cd979171a584a42fb3e8742040b2c3bb9494155e7d55dbae'},
                         'raw_component_differences.csv': {'size_bytes': 163741,
                                                           'sha256': 'de13b28fb809ce5b267816b126b71ecbe3ae4d2d396b7cab9bbf9860e417c457'},
                         'roll_context.csv': {'size_bytes': 8791,
                                              'sha256': '35ec1eba30a6eeea59ab369b89a575b0cad44cf23b6b3ca89d494a8ef6428ffc'}},
 'expected_classification': 'ATTRIBUTION_DIAGNOSTIC_NOT_QUALIFIED',
 'expected_candidate_session_rows': 51,
 'expected_reference_rebuild_matches': 8,
 'expected_reference_rebuild_failures': 43,
 'expected_transfer_rebuild_matches': 51,
 'expected_unresolved_rows': 43,
 'permitted_operations': ('verify_attempt_002_failure_record',
                          'verify_nine_preserved_artifact_hashes',
                          'read_five_preserved_csv_files',
                          'write_attribution_summary_json',
                          'write_markdown_report',
                          'write_html_report',
                          'write_output_hashes_json',
                          'write_completion_marker_json',
                          'verify_original_nine_artifacts_unchanged',
                          'atomically_rename_partial_directory'),
 'required_preconditions': {'clean_synchronised_main': True,
                            'implementation_commit_locked': True,
                            'authorized_preflight_required': True,
                            'partial_directory_present': True,
                            'final_directory_absent': True,
                            'databento_api_key_absent': True},
 'market_parquet_access_authorized': False,
 'attribution_recalculation_authorized': False,
 'feature_reconstruction_authorized': False,
 'chart_rebuild_authorized': False,
 'network_access_authorized': False,
 'strategy_replay_authorized': False,
 'performance_evaluation_authorized': False,
 'optimization_authorized': False,
 'mcpt_authorized': False,
 'bootstrap_authorized': False,
 'walk_forward_authorized': False,
 'paper_trading_authorized': False,
 'live_trading_authorized': False,
 'source_winner_selection_authorized': False,
 'candidate_winner_selection_authorized': False,
 'market_data_rerun_authorized': False,
 'attribution_attempt_rerun_authorized': False,
 'recovery_rerun_authorized': False,
 'interpretation_boundary': 'This authorization permits one evidence-only publication '
                            'recovery. It does not qualify the attribution diagnostic, '
                            'prove either data source correct or superior, validate '
                            'strategy edge, or authorize paper or live trading.'}

EXPECTED_EXP024_EVIDENCE_RECOVERY_AUTHORIZATION_SHA256 = (
    "8d5b319b8550dcf12ebb616905a15793209eb996ee49663191ab8607671c3c7c"
)


def canonical_record_hash(record: dict[str, Any]) -> str:
    encoded = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def get_exp024_evidence_recovery_authorization() -> dict[str, Any]:
    return deepcopy(EXP024_EVIDENCE_RECOVERY_AUTHORIZATION)


def validate_exp024_evidence_recovery_authorization(
    candidate: dict[str, Any] | None = None,
) -> None:
    record = (
        EXP024_EVIDENCE_RECOVERY_AUTHORIZATION
        if candidate is None
        else candidate
    )
    if (
        record.get("experiment_id") != "EXP-024"
        or record.get("authorization_id")
        != "EXP-024-EVIDENCE-RECOVERY-AUTH-001"
        or record.get("evidence_recovery_authorized") is not True
        or record.get("one_time_recovery") is not True
        or record.get("maximum_recovery_runs") != 1
        or record.get("locked_recovery_implementation_commit")
        != "a57ebcbc237e2e8e8696e9d6b3b13f584102beee"
        or record.get("attempt_002_failure_commit")
        != "7acf180c9640079c560c992a00c4fd413f3b13b7"
        or record.get("attempt_002_failure_record_sha256")
        != "d58e747db36ae3c5e80a034e3b6de127d9771184805470a16f0d3adbbab77359"
        or record.get("partial_artifact_count") != 9
        or record.get("expected_classification")
        != "ATTRIBUTION_DIAGNOSTIC_NOT_QUALIFIED"
    ):
        raise ValueError("EXP-024 recovery authorization identity changed.")

    required_false = (
        "market_parquet_access_authorized",
        "attribution_recalculation_authorized",
        "feature_reconstruction_authorized",
        "chart_rebuild_authorized",
        "network_access_authorized",
        "strategy_replay_authorized",
        "performance_evaluation_authorized",
        "optimization_authorized",
        "mcpt_authorized",
        "bootstrap_authorized",
        "walk_forward_authorized",
        "paper_trading_authorized",
        "live_trading_authorized",
        "source_winner_selection_authorized",
        "candidate_winner_selection_authorized",
        "market_data_rerun_authorized",
        "attribution_attempt_rerun_authorized",
        "recovery_rerun_authorized",
    )
    if any(record.get(name) is not False for name in required_false):
        raise ValueError("EXP-024 recovery prohibition boundary changed.")

    if set(record.get("preserved_artifacts", {})) != {'mismatch_attribution.csv', 'roll_context.csv', 'raw_component_differences.csv', 'feature_comparison.csv', 'assets/raw_component_differences.png', 'assets/roll_context.png', 'aggregation_check.csv', 'assets/attribution_categories.png', 'assets/threshold_margins.png'}:
        raise ValueError("EXP-024 preserved-artifact set changed.")

    if (
        canonical_record_hash(record)
        != EXPECTED_EXP024_EVIDENCE_RECOVERY_AUTHORIZATION_SHA256
    ):
        raise ValueError("EXP-024 recovery authorization record changed.")
