from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any


EXP024_ATTEMPT_002_FAILURE: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-024",
    "attempt_id": "EXP-024-ATTEMPT-002",
    "failed_date": "2026-07-26",
    "execution_head": (
        "da7bbe843361fd9d08cf64cc1e772c9eabf82fb5"
    ),
    "replacement_implementation_commit": (
        "fb5b8f02ac54cccf29c5d23452db6d8e9ac4589e"
    ),
    "replacement_authorization_commit": (
        "da7bbe843361fd9d08cf64cc1e772c9eabf82fb5"
    ),
    "authorization_id": "EXP-024-ATTRIBUTION-AUTH-002",
    "failure_stage": "MARKDOWN_REPORT_FORMATTING_AFTER_CHARTS",
    "exception_type": "TypeError",
    "exception_message": (
        "cannot use 'dict' as a set element (unhashable type: 'dict')"
    ),
    "root_cause": (
        "The Markdown hard-check table expression wrapped each dictionary "
        "in an additional pair of braces inside an f-string, creating a set "
        "literal containing an unhashable dictionary. The exception occurred "
        "after both deterministic attribution rebuilds matched and after the "
        "five CSV outputs and four chart assets were written."
    ),
    "execution_boundary": {
        "all_permitted_source_windows_materialized": True,
        "non_mismatch_values_materialized": False,
        "current_post_entry_values_materialized": False,
        "out_of_overlap_values_materialized": False,
        "volume_materialized": False,
        "databento_api_calls": 0,
        "network_access": False,
        "strategy_replay": False,
        "performance_metric_calculated": False,
    },
    "attribution_calculated": True,
    "independent_rebuild_completed": True,
    "independent_rebuild_hashes_matched": True,
    "aggregation_check_rows": 4_709,
    "aggregation_all_ohlc_match": True,
    "candidate_session_rows": 51,
    "feature_rows": 153,
    "raw_component_difference_rows": 1_530,
    "roll_context_rows": 51,
    "reference_rebuild_match_rows": 8,
    "reference_rebuild_failure_rows": 43,
    "transfer_rebuild_match_rows": 51,
    "unresolved_rows": 43,
    "category_counts": {
        "ELIGIBILITY_DIFFERENCE": 1,
        "NORMALIZED_CONTEXT_THRESHOLD_CROSSING": 5,
        "CONTEXT_DIRECTION_DIFFERENCE": 0,
        "FIRST_CASH_BAR_CONFIRMATION_DIFFERENCE": 0,
        "ENTRY_RISK_VALIDITY_DIFFERENCE": 0,
        "MULTIPLE_DECISION_COMPONENT_DIFFERENCES": 2,
        "UNRESOLVED_WITH_LOCKED_FEATURES": 43,
    },
    "reconstructed_classification": (
        "ATTRIBUTION_DIAGNOSTIC_NOT_QUALIFIED"
    ),
    "classification_reason": (
        "The locked reference-decision reconstruction hard check fails on "
        "43 gap-fade mismatch rows. The transfer reconstruction and "
        "Quantower one-to-five-minute aggregation checks pass."
    ),
    "partial_output_directory": (
        "results/EXP-024/source_disagreement_attribution.partial"
    ),
    "partial_artifacts": {
        "aggregation_check.csv": {
            "size_bytes": 641_094,
            "sha256": (
                "c2c693c142a076db404739047f8e683cb"
                "63e1c218f057e1c3d46b9c20f63a7fa"
            ),
        },
        "assets/attribution_categories.png": {
            "size_bytes": 74_003,
            "sha256": (
                "9c88dc6b2c68fd36eb471b0c8298e8e3"
                "d455de80fbef0a29d511ba4e8d4d5f85"
            ),
        },
        "assets/raw_component_differences.png": {
            "size_bytes": 79_515,
            "sha256": (
                "8e81cf3d629653841c90abac421e37b7"
                "f994ced81490eb1420ee7fb3e58f3214"
            ),
        },
        "assets/roll_context.png": {
            "size_bytes": 57_825,
            "sha256": (
                "f8b9fd976c18ce3e227dacb5317adf96"
                "f73ee4c769548e5ca892a5ccaf13e0bf"
            ),
        },
        "assets/threshold_margins.png": {
            "size_bytes": 89_786,
            "sha256": (
                "f7489bb363b51e9a6250a53ca262d545"
                "c3dbf6cac93fa09b31132cd056dde7a6"
            ),
        },
        "feature_comparison.csv": {
            "size_bytes": 38_064,
            "sha256": (
                "d10a5ffb4e01ee0b7ab65d65f721ab5"
                "beca0a4b9cfac6eca4fdacc82c9bd595c"
            ),
        },
        "mismatch_attribution.csv": {
            "size_bytes": 6_797,
            "sha256": (
                "1f762b2cbb2d53c0cd979171a584a42f"
                "b3e8742040b2c3bb9494155e7d55dbae"
            ),
        },
        "raw_component_differences.csv": {
            "size_bytes": 163_741,
            "sha256": (
                "de13b28fb809ce5b267816b126b71ecb"
                "e3ae4d2d396b7cab9bbf9860e417c457"
            ),
        },
        "roll_context.csv": {
            "size_bytes": 8_791,
            "sha256": (
                "35ec1eba30a6eeea59ab369b89a575b0"
                "cad44cf23b6b3ca89d494a8ef6428ffc"
            ),
        },
    },
    "partial_artifact_count": 9,
    "final_output_created": False,
    "partial_output_created": True,
    "frozen_input_modified": False,
    "replacement_authorization_consumed": True,
    "market_data_rerun_authorized": False,
    "evidence_only_recovery_authorized": True,
    "recovery_boundary": (
        "Recovery may read only the nine hash-locked partial artifacts, "
        "generate the missing summary, Markdown report, HTML report, output "
        "manifest and completion marker, verify the original nine hashes "
        "remain unchanged, and atomically rename the partial directory. It "
        "may not read market Parquet values, reconstruct features, recalculate "
        "attribution, rebuild charts or alter any existing partial artifact."
    ),
}

EXPECTED_EXP024_ATTEMPT_002_FAILURE_SHA256 = (
    "d58e747db36ae3c5e80a034e3b6de127d9771184805470a16f0d3adbbab77359"
)


def canonical_record_hash(record: dict[str, Any]) -> str:
    encoded = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def get_exp024_attempt_002_failure() -> dict[str, Any]:
    return deepcopy(EXP024_ATTEMPT_002_FAILURE)


def validate_exp024_attempt_002_failure(
    candidate: dict[str, Any] | None = None,
) -> None:
    record = (
        EXP024_ATTEMPT_002_FAILURE
        if candidate is None
        else candidate
    )
    if (
        record["experiment_id"] != "EXP-024"
        or record["attempt_id"] != "EXP-024-ATTEMPT-002"
        or record["execution_head"]
        != "da7bbe843361fd9d08cf64cc1e772c9eabf82fb5"
        or record["authorization_id"]
        != "EXP-024-ATTRIBUTION-AUTH-002"
        or record["failure_stage"]
        != "MARKDOWN_REPORT_FORMATTING_AFTER_CHARTS"
        or record["exception_type"] != "TypeError"
        or record["partial_artifact_count"] != 9
    ):
        raise ValueError("EXP-024 attempt-002 identity changed.")
    boundary = record["execution_boundary"]
    if (
        record["attribution_calculated"] is not True
        or record["independent_rebuild_completed"] is not True
        or record["independent_rebuild_hashes_matched"] is not True
        or record["aggregation_all_ohlc_match"] is not True
        or record["reference_rebuild_failure_rows"] != 43
        or record["transfer_rebuild_match_rows"] != 51
        or record["unresolved_rows"] != 43
        or record["reconstructed_classification"]
        != "ATTRIBUTION_DIAGNOSTIC_NOT_QUALIFIED"
        or record["final_output_created"] is not False
        or record["partial_output_created"] is not True
        or record["frozen_input_modified"] is not False
        or record["replacement_authorization_consumed"] is not True
        or record["market_data_rerun_authorized"] is not False
        or record["evidence_only_recovery_authorized"] is not True
        or boundary["non_mismatch_values_materialized"] is not False
        or boundary["current_post_entry_values_materialized"] is not False
        or boundary["out_of_overlap_values_materialized"] is not False
        or boundary["volume_materialized"] is not False
        or boundary["databento_api_calls"] != 0
        or boundary["network_access"] is not False
    ):
        raise ValueError("EXP-024 attempt-002 boundary changed.")
    if set(record["partial_artifacts"]) != {
        "aggregation_check.csv",
        "assets/attribution_categories.png",
        "assets/raw_component_differences.png",
        "assets/roll_context.png",
        "assets/threshold_margins.png",
        "feature_comparison.csv",
        "mismatch_attribution.csv",
        "raw_component_differences.csv",
        "roll_context.csv",
    }:
        raise ValueError("EXP-024 attempt-002 artifact set changed.")
    if (
        canonical_record_hash(record)
        != EXPECTED_EXP024_ATTEMPT_002_FAILURE_SHA256
    ):
        raise ValueError("EXP-024 attempt-002 record changed.")
