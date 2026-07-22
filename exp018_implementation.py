from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from exp018_preregistration import (
    REPEATABILITY_WINDOW_IDS,
    WINDOWS,
    validate_exp018_preregistration,
)


PROJECT_DIR = Path(__file__).resolve().parent
EXPECTED_PREREGISTRATION_COMMIT = (
    "fd0844dacab65f25d160e0b32a2273504528551f"
)
EXPECTED_DATABENTO_CLIENT_VERSION = "0.81.0"
DATABENTO_VENV = PROJECT_DIR / ".venv-exp017-databento"
DATABENTO_ENVIRONMENT_VARIABLE = "DATABENTO_API_KEY"

DATA_ROOT = PROJECT_DIR / "data" / "EXP-018" / "databento_exact_contract"
RAW_ROOT = DATA_ROOT / "raw"
INITIAL_RAW_ROOT = RAW_ROOT / "initial"
REPEAT_RAW_ROOT = RAW_ROOT / "repeat"
EXTRACT_ROOT = DATA_ROOT / "extracted"
LOCK_ROOT = DATA_ROOT / "request_locks"
INITIAL_LOCK_ROOT = LOCK_ROOT / "initial"
REPEAT_LOCK_ROOT = LOCK_ROOT / "repeat"
INITIAL_MANIFEST = DATA_ROOT / "initial_manifest.json"
REPEAT_MANIFEST = DATA_ROOT / "repeat_manifest.json"

RESULT_ROOT = PROJECT_DIR / "results" / "EXP-018" / "source_qualification"
RESULT_JSON = RESULT_ROOT / "audit_result.json"
WINDOW_CSV = RESULT_ROOT / "window_measurements.csv"
SESSION_CSV = RESULT_ROOT / "session_measurements.csv"
MISSING_RUNS_CSV = RESULT_ROOT / "missing_minute_runs.csv"
REPEATABILITY_CSV = RESULT_ROOT / "repeatability_measurements.csv"

WORKER_FILE = PROJECT_DIR / "exp018_databento_worker.py"

EXP018_IMPLEMENTATION: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-018",
    "implementation_status": "IMPLEMENTED_NOT_RUN",
    "expected_preregistration_commit": EXPECTED_PREREGISTRATION_COMMIT,
    "source": {
        "provider": "Databento",
        "client_version": EXPECTED_DATABENTO_CLIENT_VERSION,
        "dataset": "GLBX.MDP3",
        "schema": "ohlcv-1m",
        "stype_in": "raw_symbol",
        "stype_out": "instrument_id",
        "isolated_environment": str(DATABENTO_VENV.relative_to(PROJECT_DIR)),
    },
    "runner_modes": {
        "preflight": True,
        "initial_downloads": True,
        "repeat_downloads": True,
        "audit_local": True,
        "modes_mutually_exclusive": True,
        "full_history": False,
        "continuous_series": False,
        "strategy_replay": False,
        "strategy_optimization": False,
    },
    "request_boundary": {
        "windows": WINDOWS,
        "repeatability_window_ids": REPEATABILITY_WINDOW_IDS,
        "initial_bar_requests": 6,
        "repeat_bar_requests": 2,
        "maximum_successful_bar_requests": 8,
        "minimum_repeat_delay_hours": 24,
        "automatic_retry": False,
        "failure_requires_review": True,
        "cost_check_before_each_bar_request": True,
        "maximum_total_estimated_cost_usd": 1.0,
        "api_key_environment_variable": DATABENTO_ENVIRONMENT_VARIABLE,
        "api_key_never_printed_or_written": True,
        "raw_vendor_files_local_and_gitignored": True,
    },
    "remote_method": {
        "client": "databento.Historical",
        "method": "timeseries.get_range",
        "path_streaming": True,
        "dataset": "GLBX.MDP3",
        "schema": "ohlcv-1m",
        "stype_in": "raw_symbol",
        "stype_out": "instrument_id",
        "batch_calls": False,
        "continuous_symbols": False,
        "parent_symbols": False,
        "unlocked_symbols": False,
        "unlocked_dates": False,
    },
    "local_audit_boundary": {
        "raw_format": "DBN_ZSTD",
        "extraction_format": "NPZ_RAW_INTEGER_FIELDS",
        "timestamp_field": "ts_event",
        "price_scale": 1_000_000_000,
        "tick_raw_units": 250_000_000,
        "timestamp_shift": False,
        "price_rounding": False,
        "bar_fill": False,
        "bar_delete": False,
        "price_repair": False,
        "duplicate_rows_silently_removed": False,
        "expected_session_timezone": "America/New_York",
        "regular_session": "09:30-16:00 ET",
        "extended_session_definition": "Globex minutes outside regular session",
        "holiday_exceptions_locked": True,
    },
    "result_boundary": {
        "highest_possible_classification": (
            "QUALIFIED_AS_ACCESSIBLE_EXACT_CONTRACT_SOURCE"
        ),
        "exchange_accuracy_claim": False,
        "best_vendor_claim": False,
        "full_history_migration": False,
        "continuous_roll_construction": False,
        "strategy_results": False,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
    },
}


def get_exp018_implementation() -> dict[str, Any]:
    return deepcopy(EXP018_IMPLEMENTATION)


def validate_exp018_implementation(
    record: dict[str, Any] | None = None,
) -> None:
    validate_exp018_preregistration()
    current = EXP018_IMPLEMENTATION if record is None else record

    if (
        current.get("schema_version") != 1
        or current.get("experiment_id") != "EXP-018"
        or current.get("implementation_status") != "IMPLEMENTED_NOT_RUN"
        or current.get("expected_preregistration_commit")
        != EXPECTED_PREREGISTRATION_COMMIT
    ):
        raise ValueError("EXP-018 implementation identity changed.")

    source = current["source"]
    if (
        source["provider"] != "Databento"
        or source["client_version"] != EXPECTED_DATABENTO_CLIENT_VERSION
        or source["dataset"] != "GLBX.MDP3"
        or source["schema"] != "ohlcv-1m"
        or source["stype_in"] != "raw_symbol"
        or source["stype_out"] != "instrument_id"
    ):
        raise ValueError("EXP-018 source lock changed.")

    modes = current["runner_modes"]
    if (
        modes["preflight"] is not True
        or modes["initial_downloads"] is not True
        or modes["repeat_downloads"] is not True
        or modes["audit_local"] is not True
        or modes["modes_mutually_exclusive"] is not True
        or modes["full_history"] is not False
        or modes["continuous_series"] is not False
        or modes["strategy_replay"] is not False
        or modes["strategy_optimization"] is not False
    ):
        raise ValueError("EXP-018 runner modes changed.")

    request = current["request_boundary"]
    if (
        tuple(request["windows"]) != WINDOWS
        or tuple(request["repeatability_window_ids"])
        != REPEATABILITY_WINDOW_IDS
        or request["initial_bar_requests"] != 6
        or request["repeat_bar_requests"] != 2
        or request["maximum_successful_bar_requests"] != 8
        or request["minimum_repeat_delay_hours"] != 24
        or request["automatic_retry"] is not False
        or request["failure_requires_review"] is not True
        or request["cost_check_before_each_bar_request"] is not True
        or request["maximum_total_estimated_cost_usd"] != 1.0
        or request["api_key_environment_variable"]
        != DATABENTO_ENVIRONMENT_VARIABLE
    ):
        raise ValueError("EXP-018 request boundary changed.")

    remote = current["remote_method"]
    if (
        remote["method"] != "timeseries.get_range"
        or remote["dataset"] != "GLBX.MDP3"
        or remote["schema"] != "ohlcv-1m"
        or remote["stype_in"] != "raw_symbol"
        or remote["stype_out"] != "instrument_id"
        or remote["batch_calls"] is not False
        or remote["continuous_symbols"] is not False
        or remote["parent_symbols"] is not False
        or remote["unlocked_symbols"] is not False
        or remote["unlocked_dates"] is not False
    ):
        raise ValueError("EXP-018 remote method changed.")

    audit = current["local_audit_boundary"]
    if (
        audit["timestamp_field"] != "ts_event"
        or audit["price_scale"] != 1_000_000_000
        or audit["tick_raw_units"] != 250_000_000
        or audit["timestamp_shift"] is not False
        or audit["price_rounding"] is not False
        or audit["bar_fill"] is not False
        or audit["bar_delete"] is not False
        or audit["price_repair"] is not False
        or audit["duplicate_rows_silently_removed"] is not False
        or audit["expected_session_timezone"] != "America/New_York"
    ):
        raise ValueError("EXP-018 local audit boundary changed.")

    result = current["result_boundary"]
    if (
        result["highest_possible_classification"]
        != "QUALIFIED_AS_ACCESSIBLE_EXACT_CONTRACT_SOURCE"
        or result["exchange_accuracy_claim"] is not False
        or result["best_vendor_claim"] is not False
        or result["full_history_migration"] is not False
        or result["continuous_roll_construction"] is not False
        or result["strategy_results"] is not False
        or result["paper_trading_authorized"] is not False
        or result["live_trading_authorized"] is not False
    ):
        raise ValueError("EXP-018 result boundary changed.")
