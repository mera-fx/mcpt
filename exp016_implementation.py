from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from exp015_implementation import (
    EXPECTED_CLIENT_VERSION,
    EXPECTED_CLIENT_WHEEL_SHA256,
    PROBE_MANIFEST,
    PROBE_VENV,
)
from exp016_preregistration import (
    FIXED_SAMPLE_WINDOWS,
    validate_exp016_preregistration,
)


PROJECT_DIR = Path(__file__).resolve().parent

EXPECTED_PREREGISTRATION_COMMIT = (
    "55577ca589fbc2b899c93a088592d32398121e49"
)
EXPECTED_EXP015_FINAL_COMMIT = (
    "bd877443f637d8041c3de935c1c8c872f5abcf72"
)

DATA_ROOT = PROJECT_DIR / "data" / "EXP-016" / "nq_f_samples"
REQUEST_LOCK_ROOT = DATA_ROOT / "request_locks"
RAW_ROOT = DATA_ROOT / "raw"
DOWNLOAD_MANIFEST = DATA_ROOT / "download_manifest.json"

RESULT_ROOT = (
    PROJECT_DIR / "results" / "EXP-016" / "source_qualification"
)
RESULT_JSON = RESULT_ROOT / "audit_result.json"
STRUCTURAL_CSV = RESULT_ROOT / "structural_measurements.csv"
CROSS_SOURCE_CSV = RESULT_ROOT / "cross_source_measurements.csv"
DISCREPANCIES_CSV = RESULT_ROOT / "largest_discrepancies.csv"

REFERENCE_NQ_FILE = (
    PROJECT_DIR
    / "data"
    / "extended_session"
    / "processed"
    / "NQ_1m_extended.parquet"
)
EXPECTED_REFERENCE_NQ_SHA256 = (
    "b1679f833d03c2f2aedeaf4ec442a34a284edd307942e13918a0488c71a669cc"
)


EXP016_IMPLEMENTATION: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-016",
    "implementation_status": "IMPLEMENTED_NOT_RUN",
    "expected_preregistration_commit": EXPECTED_PREREGISTRATION_COMMIT,
    "exp015_dependency": {
        "final_commit": EXPECTED_EXP015_FINAL_COMMIT,
        "catalog_result_must_verify": True,
        "probe_manifest_must_verify": True,
        "client_version": EXPECTED_CLIENT_VERSION,
        "wheel_sha256": EXPECTED_CLIENT_WHEEL_SHA256,
        "reuse_isolated_venv": str(PROBE_VENV.relative_to(PROJECT_DIR)),
        "catalog_rerun": False,
    },
    "runner_modes": {
        "preflight": True,
        "download_samples": True,
        "audit_local": True,
        "catalog": False,
        "full_history": False,
        "strategy_replay": False,
        "optimization": False,
        "modes_mutually_exclusive": True,
    },
    "remote_boundary": {
        "official_method": (
            "history('NQ.F', dataset='futures', timeframe='1m', "
            "start=..., end=..., dataframe=False)"
        ),
        "fixed_windows": FIXED_SAMPLE_WINDOWS,
        "maximum_requests": 6,
        "one_request_attempt_per_window": True,
        "minimum_seconds_between_requests": 10,
        "api_key_environment_variable": "LSE_API_KEY",
        "api_key_never_printed_or_written": True,
        "raw_files_local_and_gitignored": True,
        "catalog_call_prohibited": True,
        "datasets_call_prohibited": True,
        "candles_call_prohibited": True,
        "stream_call_prohibited": True,
    },
    "local_audit_boundary": {
        "reference_file": str(REFERENCE_NQ_FILE.relative_to(PROJECT_DIR)),
        "reference_sha256": EXPECTED_REFERENCE_NQ_SHA256,
        "reference_read_only": True,
        "normalization_fills_bars": False,
        "normalization_deletes_bars": False,
        "normalization_resamples_bars": False,
        "automatic_timezone_assumption": False,
        "automatic_price_offset": False,
        "duplicate_rows_silently_removed": False,
        "match_key": "UTC minute",
        "nq_tick_size_points": 0.25,
        "largest_discrepancy_rows": 100,
    },
    "result_boundary": {
        "highest_possible_classification": (
            "QUALIFIED_AS_SUPPLEMENTARY_NQ_SOURCE"
        ),
        "primary_source_qualification_prohibited": True,
        "mnq_qualification_prohibited": True,
        "other_asset_qualification_prohibited": True,
        "prior_data_replacement": False,
        "strategy_results": False,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
    },
}


def get_exp016_implementation() -> dict[str, Any]:
    return deepcopy(EXP016_IMPLEMENTATION)


def validate_exp016_implementation(
    record: dict[str, Any] | None = None,
) -> None:
    validate_exp016_preregistration()
    current = EXP016_IMPLEMENTATION if record is None else record

    if (
        current.get("schema_version") != 1
        or current.get("experiment_id") != "EXP-016"
        or current.get("implementation_status") != "IMPLEMENTED_NOT_RUN"
        or current.get("expected_preregistration_commit")
        != EXPECTED_PREREGISTRATION_COMMIT
    ):
        raise ValueError("EXP-016 implementation identity changed.")

    dependency = current["exp015_dependency"]
    if (
        dependency["final_commit"] != EXPECTED_EXP015_FINAL_COMMIT
        or dependency["catalog_result_must_verify"] is not True
        or dependency["probe_manifest_must_verify"] is not True
        or dependency["client_version"] != EXPECTED_CLIENT_VERSION
        or dependency["wheel_sha256"] != EXPECTED_CLIENT_WHEEL_SHA256
        or dependency["catalog_rerun"] is not False
    ):
        raise ValueError("EXP-016 EXP-015 dependency changed.")

    expected_modes = {
        "preflight": True,
        "download_samples": True,
        "audit_local": True,
        "catalog": False,
        "full_history": False,
        "strategy_replay": False,
        "optimization": False,
        "modes_mutually_exclusive": True,
    }
    if current["runner_modes"] != expected_modes:
        raise ValueError("EXP-016 runner modes changed.")

    remote = current["remote_boundary"]
    if (
        tuple(remote["fixed_windows"]) != FIXED_SAMPLE_WINDOWS
        or remote["maximum_requests"] != 6
        or remote["one_request_attempt_per_window"] is not True
        or remote["minimum_seconds_between_requests"] != 10
        or remote["api_key_environment_variable"] != "LSE_API_KEY"
        or remote["api_key_never_printed_or_written"] is not True
        or remote["catalog_call_prohibited"] is not True
        or remote["datasets_call_prohibited"] is not True
        or remote["candles_call_prohibited"] is not True
        or remote["stream_call_prohibited"] is not True
    ):
        raise ValueError("EXP-016 remote boundary changed.")

    audit = current["local_audit_boundary"]
    if (
        audit["reference_sha256"] != EXPECTED_REFERENCE_NQ_SHA256
        or audit["reference_read_only"] is not True
        or audit["normalization_fills_bars"] is not False
        or audit["normalization_deletes_bars"] is not False
        or audit["normalization_resamples_bars"] is not False
        or audit["automatic_timezone_assumption"] is not False
        or audit["automatic_price_offset"] is not False
        or audit["duplicate_rows_silently_removed"] is not False
        or audit["match_key"] != "UTC minute"
        or audit["nq_tick_size_points"] != 0.25
        or audit["largest_discrepancy_rows"] != 100
    ):
        raise ValueError("EXP-016 local audit boundary changed.")

    result = current["result_boundary"]
    if (
        result["highest_possible_classification"]
        != "QUALIFIED_AS_SUPPLEMENTARY_NQ_SOURCE"
        or result["primary_source_qualification_prohibited"] is not True
        or result["mnq_qualification_prohibited"] is not True
        or result["prior_data_replacement"] is not False
        or result["strategy_results"] is not False
        or result["paper_trading_authorized"] is not False
        or result["live_trading_authorized"] is not False
    ):
        raise ValueError("EXP-016 result boundary changed.")
