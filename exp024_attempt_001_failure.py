from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any


EXP024_ATTEMPT_001_FAILURE: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-024",
    "attempt_id": "EXP-024-ATTEMPT-001",
    "failed_date": "2026-07-26",
    "execution_head": (
        "55ae174f5517bdb5afc48f5a36f5268fbc1eb42a"
    ),
    "implementation_commit": (
        "34f7d4c83dee025108229d5247e9cb4f87398a59"
    ),
    "authorization_commit": (
        "55ae174f5517bdb5afc48f5a36f5268fbc1eb42a"
    ),
    "authorization_id": "EXP-024-ATTRIBUTION-AUTH-001",
    "command": (
        ".venv/Scripts/python.exe exp024_attribution.py --run"
    ),
    "failure_stage": (
        "FIRST_QUANTOWER_CURRENT_WINDOW_AFTER_ARROW_TO_PANDAS"
    ),
    "exception_type": "KeyError",
    "exception_message": "'timestamp'",
    "root_cause": (
        "The frozen Quantower Parquet projects timestamp as an Arrow field "
        "but its pandas metadata identifies timestamp as the index. "
        "Table.to_pandas restored that field as the DataFrame index while "
        "the protected scanner expected a regular timestamp column."
    ),
    "market_value_access": {
        "quantower_current_mismatch_window_materialized": True,
        "quantower_current_window_new_york": (
            "08:00:00 through 09:34:59"
        ),
        "quantower_current_fields": (
            "open",
            "high",
            "low",
            "close",
        ),
        "quantower_entry_open_materialized": False,
        "quantower_previous_gap_cash_materialized": False,
        "quantower_five_minute_materialized": False,
        "databento_values_materialized": False,
        "non_mismatch_values_materialized": False,
        "current_post_entry_values_materialized": False,
        "out_of_overlap_values_materialized": False,
        "volume_materialized": False,
    },
    "databento_values_materialized": False,
    "feature_reconstruction_started": False,
    "attribution_calculated": False,
    "independent_rebuild_completed": False,
    "report_generated": False,
    "final_output_created": False,
    "partial_output_created": False,
    "frozen_input_modified": False,
    "network_access": False,
    "databento_api_calls": 0,
    "strategy_replay": False,
    "performance_metric_calculated": False,
    "paper_or_live_action": False,
    "original_authorization_consumed": True,
    "retry_under_original_authorization": False,
    "replacement_requirements": (
        "Preserve this failed-attempt record, commit a narrowly scoped "
        "timestamp-index loader correction, pass a result-free replacement "
        "preflight, and commit a distinct one-time replacement "
        "authorization before another execution attempt."
    ),
}

EXPECTED_EXP024_ATTEMPT_001_FAILURE_SHA256 = (
    "556854e35ac217f62677cf15d3e6c03abf38414bd65585d9decd441154f7be17"
)


def canonical_record_hash(record: dict[str, Any]) -> str:
    encoded = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def get_exp024_attempt_001_failure() -> dict[str, Any]:
    return deepcopy(EXP024_ATTEMPT_001_FAILURE)


def validate_exp024_attempt_001_failure(
    candidate: dict[str, Any] | None = None,
) -> None:
    record = (
        EXP024_ATTEMPT_001_FAILURE
        if candidate is None
        else candidate
    )
    access = record["market_value_access"]
    if (
        record["experiment_id"] != "EXP-024"
        or record["attempt_id"] != "EXP-024-ATTEMPT-001"
        or record["execution_head"]
        != "55ae174f5517bdb5afc48f5a36f5268fbc1eb42a"
        or record["implementation_commit"]
        != "34f7d4c83dee025108229d5247e9cb4f87398a59"
        or record["authorization_id"]
        != "EXP-024-ATTRIBUTION-AUTH-001"
        or record["failure_stage"]
        != "FIRST_QUANTOWER_CURRENT_WINDOW_AFTER_ARROW_TO_PANDAS"
        or record["exception_type"] != "KeyError"
        or record["exception_message"] != "'timestamp'"
    ):
        raise ValueError("EXP-024 attempt-001 identity changed.")
    if (
        access[
            "quantower_current_mismatch_window_materialized"
        ]
        is not True
        or access["databento_values_materialized"] is not False
        or access["non_mismatch_values_materialized"] is not False
        or access["current_post_entry_values_materialized"] is not False
        or access["out_of_overlap_values_materialized"] is not False
        or access["volume_materialized"] is not False
        or record["attribution_calculated"] is not False
        or record["final_output_created"] is not False
        or record["partial_output_created"] is not False
        or record["frozen_input_modified"] is not False
        or record["network_access"] is not False
        or record["databento_api_calls"] != 0
        or record["original_authorization_consumed"] is not True
        or record["retry_under_original_authorization"] is not False
    ):
        raise ValueError("EXP-024 attempt-001 boundary changed.")
    if (
        canonical_record_hash(record)
        != EXPECTED_EXP024_ATTEMPT_001_FAILURE_SHA256
    ):
        raise ValueError("EXP-024 attempt-001 record changed.")
