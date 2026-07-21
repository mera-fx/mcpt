from __future__ import annotations

from copy import deepcopy
from typing import Any


EXPECTED_IMPLEMENTATION_COMMIT = (
    "a0f1c8c40d80b5a13f38604b2608c21528ad7bcd"
)
MINIMUM_RETRY_WAIT_SECONDS = 3900
RETRY_LOCK_RELATIVE_PATH = (
    "data/EXP-016/nq_f_samples/retry_locks/"
    "2025_march_dst_roll_retry1.json"
)
RETRY_RAW_RELATIVE_PATH = (
    "data/EXP-016/nq_f_samples/retry_raw/"
    "2025_march_dst_roll_retry1"
)

COMPLETED_BEFORE_RATE_LIMIT: tuple[dict[str, Any], ...] = (
    {
        "window_id": "2020_march_dst_roll_volatility",
        "start": "2020-03-06",
        "end": "2020-03-20",
        "request_attempt": 1,
        "status": "COMPLETE",
        "local_path": (
            "data/EXP-016/nq_f_samples/raw/"
            "2020_march_dst_roll_volatility/futures_NQ.F_1m.parquet"
        ),
        "size_bytes": 246673,
        "sha256": "1f307ae35720423829e682d050a18f7e1fee87a2864ebc3f305e85209bcdc3a1",
    },
    {
        "window_id": "2021_thanksgiving",
        "start": "2021-11-19",
        "end": "2021-12-03",
        "request_attempt": 1,
        "status": "COMPLETE",
        "local_path": (
            "data/EXP-016/nq_f_samples/raw/"
            "2021_thanksgiving/futures_NQ.F_1m.parquet"
        ),
        "size_bytes": 247606,
        "sha256": "f87a247852a1d3811d1f584d6a6c1081c93092006c80562289b9930fdd938b0a",
    },
    {
        "window_id": "2022_june_roll",
        "start": "2022-06-03",
        "end": "2022-06-17",
        "request_attempt": 1,
        "status": "COMPLETE",
        "local_path": (
            "data/EXP-016/nq_f_samples/raw/"
            "2022_june_roll/futures_NQ.F_1m.parquet"
        ),
        "size_bytes": 275752,
        "sha256": "3d710efcd0cc81d7e640f0d824e8dfb213df5ec376effea138218785c4944d13",
    },
    {
        "window_id": "2023_march_dst_roll",
        "start": "2023-03-03",
        "end": "2023-03-17",
        "request_attempt": 1,
        "status": "COMPLETE",
        "local_path": (
            "data/EXP-016/nq_f_samples/raw/"
            "2023_march_dst_roll/futures_NQ.F_1m.parquet"
        ),
        "size_bytes": 247120,
        "sha256": "28caec68d023772a360252181fbe481978c2f11d2dc2de73d7ba0ac0c4836464",
    },
    {
        "window_id": "2024_thanksgiving",
        "start": "2024-11-22",
        "end": "2024-12-06",
        "request_attempt": 1,
        "status": "COMPLETE",
        "local_path": (
            "data/EXP-016/nq_f_samples/raw/"
            "2024_thanksgiving/futures_NQ.F_1m.parquet"
        ),
        "size_bytes": 234557,
        "sha256": "d66ad09496ea0c3012afcc8a25d12e3a6e13bf20f728eb65ed3e034c5535cab1",
    },
)

OBSERVED_RATE_LIMIT_FAILURE: dict[str, Any] = {
    "window_id": "2025_march_dst_roll",
    "start": "2025-03-07",
    "end": "2025-03-21",
    "request_attempt": 1,
    "status": "FAILED",
    "safe_error": (
        'LSEError: [429] {"detail":"too many export requests; '
        'try again shortly"}'
    ),
}

EXP016_RATE_LIMIT_AMENDMENT: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-016",
    "amendment_id": "EXP-016-A1",
    "amendment_type": "POST_ACCESS_OPERATIONAL_RATE_LIMIT_RETRY",
    "expected_implementation_commit": EXPECTED_IMPLEMENTATION_COMMIT,
    "observed_before_amendment": {
        "successful_fixed_windows": COMPLETED_BEFORE_RATE_LIMIT,
        "failed_fixed_window": OBSERVED_RATE_LIMIT_FAILURE,
        "download_manifest_exists": False,
        "api_key_persisted": False,
        "git_working_tree_changed": False,
        "sample_contents_audited": False,
        "strategy_run": False,
    },
    "amended_permission": {
        "retry_window_id": "2025_march_dst_roll",
        "maximum_additional_requests": 1,
        "minimum_wait_seconds_after_failure": MINIMUM_RETRY_WAIT_SECONDS,
        "original_failed_lock_must_remain_unchanged": True,
        "separate_retry_lock_required": True,
        "separate_retry_destination_required": True,
        "other_window_requests_prohibited": True,
        "catalog_rerun_prohibited": True,
        "full_history_download_prohibited": True,
        "api_key_environment_only": True,
        "additional_retry_after_failure_prohibited": True,
    },
    "research_boundary": {
        "sample_windows_changed": False,
        "symbol_changed": False,
        "timeframe_changed": False,
        "measurements_changed": False,
        "qualification_thresholds_changed": False,
        "quantower_replaced": False,
        "strategy_run_authorized": False,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
    },
    "request_accounting": {
        "original_attempts": 6,
        "original_successes": 5,
        "original_rate_limited_failures": 1,
        "maximum_amended_attempts": 1,
        "maximum_total_attempts": 7,
        "maximum_successful_samples": 6,
    },
    "failure_after_amended_retry": {
        "no_further_remote_attempt": True,
        "final_access_classification": "ACCESS_UNAVAILABLE",
        "local_six_window_audit_prohibited": True,
    },
}


def get_exp016_rate_limit_amendment() -> dict[str, Any]:
    return deepcopy(EXP016_RATE_LIMIT_AMENDMENT)


def validate_exp016_rate_limit_amendment(
    record: dict[str, Any] | None = None,
) -> None:
    current = EXP016_RATE_LIMIT_AMENDMENT if record is None else record
    if (
        current.get("schema_version") != 1
        or current.get("experiment_id") != "EXP-016"
        or current.get("amendment_id") != "EXP-016-A1"
        or current.get("expected_implementation_commit")
        != EXPECTED_IMPLEMENTATION_COMMIT
    ):
        raise ValueError("EXP-016 rate-limit amendment identity changed.")

    observed = current["observed_before_amendment"]
    if (
        tuple(observed["successful_fixed_windows"])
        != COMPLETED_BEFORE_RATE_LIMIT
        or observed["failed_fixed_window"] != OBSERVED_RATE_LIMIT_FAILURE
        or observed["download_manifest_exists"] is not False
        or observed["api_key_persisted"] is not False
        or observed["git_working_tree_changed"] is not False
        or observed["sample_contents_audited"] is not False
        or observed["strategy_run"] is not False
    ):
        raise ValueError("EXP-016 observed rate-limit evidence changed.")

    permission = current["amended_permission"]
    if (
        permission["retry_window_id"] != "2025_march_dst_roll"
        or permission["maximum_additional_requests"] != 1
        or permission["minimum_wait_seconds_after_failure"]
        != MINIMUM_RETRY_WAIT_SECONDS
        or permission["original_failed_lock_must_remain_unchanged"] is not True
        or permission["separate_retry_lock_required"] is not True
        or permission["separate_retry_destination_required"] is not True
        or permission["other_window_requests_prohibited"] is not True
        or permission["catalog_rerun_prohibited"] is not True
        or permission["full_history_download_prohibited"] is not True
        or permission["api_key_environment_only"] is not True
        or permission["additional_retry_after_failure_prohibited"] is not True
    ):
        raise ValueError("EXP-016 amended retry permission changed.")

    accounting = current["request_accounting"]
    if accounting != {
        "original_attempts": 6,
        "original_successes": 5,
        "original_rate_limited_failures": 1,
        "maximum_amended_attempts": 1,
        "maximum_total_attempts": 7,
        "maximum_successful_samples": 6,
    }:
        raise ValueError("EXP-016 request accounting changed.")

    boundary = current["research_boundary"]
    if any(boundary.values()):
        raise ValueError("EXP-016 research boundary changed.")

    failure = current["failure_after_amended_retry"]
    if (
        failure["no_further_remote_attempt"] is not True
        or failure["final_access_classification"] != "ACCESS_UNAVAILABLE"
        or failure["local_six_window_audit_prohibited"] is not True
    ):
        raise ValueError("EXP-016 retry-failure boundary changed.")
