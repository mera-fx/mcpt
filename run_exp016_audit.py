from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

import pandas as pd

from exp015_catalog_result import verify_local_exp015_catalog_result
from exp015_implementation import (
    EXPECTED_CLIENT_VERSION,
    EXPECTED_CLIENT_WHEEL_SHA256,
    PROBE_MANIFEST,
    PROBE_VENV,
)
from exp016_implementation import (
    CROSS_SOURCE_CSV,
    DATA_ROOT,
    DISCREPANCIES_CSV,
    DOWNLOAD_MANIFEST,
    EXPECTED_PREREGISTRATION_COMMIT,
    EXPECTED_REFERENCE_NQ_SHA256,
    RAW_ROOT,
    REQUEST_LOCK_ROOT,
    RESULT_JSON,
    RESULT_ROOT,
    STRUCTURAL_CSV,
    validate_exp016_implementation,
)
from exp016_measurements import (
    canonicalize_vendor_frame,
    classify_audit,
    compare_with_reference,
    sha256_file,
)
from exp016_rate_limit_amendment import (
    COMPLETED_BEFORE_RATE_LIMIT,
    EXPECTED_IMPLEMENTATION_COMMIT,
    MINIMUM_RETRY_WAIT_SECONDS,
    OBSERVED_RATE_LIMIT_FAILURE,
    RETRY_LOCK_RELATIVE_PATH,
    RETRY_RAW_RELATIVE_PATH,
    validate_exp016_rate_limit_amendment,
)
from exp016_preregistration import (
    FIXED_SAMPLE_WINDOWS,
    validate_exp016_preregistration,
)
from experiment_lifecycle import get_experiment_lifecycle
from extended_session_data import OUTPUT_FILES
from extended_session_data_result import verify_extended_session_data_result


PROJECT_DIR = Path(__file__).resolve().parent
WORKER_FILE = PROJECT_DIR / "exp016_lse_history_worker.py"


def _run_git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=PROJECT_DIR,
        text=True,
        capture_output=True,
        check=check,
    )


def _git_provenance() -> dict[str, Any]:
    commit = _run_git("rev-parse", "HEAD").stdout.strip()
    clean = not bool(_run_git("status", "--porcelain").stdout.strip())
    return {
        "commit": commit,
        "short_commit": commit[:7],
        "working_tree_clean": clean,
    }


def _atomic_json(value: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    temporary.replace(path)


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"Expected JSON object: {path}")
    return value


def _verify_lifecycle() -> None:
    expected = {
        "EXP-005": "ACCEPTED_FOR_PAPER_TESTING",
        "EXP-006": "REJECTED",
        "EXP-007": "REJECTED",
        "EXP-008": "REJECTED",
        "EXP-009": "REVIEW",
        "EXP-010": "REVIEW",
        "EXP-011": "REVIEW",
        "EXP-012": "REVIEW",
        "EXP-013": "REVIEW",
        "EXP-014": "REVIEW",
        "EXP-015": "REVIEW",
        "EXP-016": "PRE_REGISTERED",
    }
    for experiment_id, stage in expected.items():
        actual = get_experiment_lifecycle(experiment_id).stage
        if actual != stage:
            raise RuntimeError(
                f"{experiment_id} must remain {stage}; found {actual}."
            )


def _verify_probe() -> dict[str, Any]:
    if not PROBE_MANIFEST.is_file():
        raise RuntimeError("The frozen EXP-015 isolated probe is missing.")
    probe = _load_json(PROBE_MANIFEST)
    if (
        probe.get("status") != "PASS"
        or probe.get("distribution") != "lse-data"
        or probe.get("version") != EXPECTED_CLIENT_VERSION
        or probe.get("wheel_sha256") != EXPECTED_CLIENT_WHEEL_SHA256
        or probe.get("real_api_key_used") is not False
        or probe.get("network_market_data_call") is not False
        or probe.get("main_project_environment_modified") is not False
    ):
        raise RuntimeError("The frozen EXP-015 isolated probe is invalid.")
    return probe


def _isolated_python() -> Path:
    if os.name == "nt":
        return PROBE_VENV / "Scripts" / "python.exe"
    return PROBE_VENV / "bin" / "python"


def _assert_ignored(path: Path) -> None:
    relative = path.relative_to(PROJECT_DIR)
    completed = _run_git(
        "check-ignore",
        "-q",
        "--",
        str(relative),
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"Protected output path is not ignored by Git: {relative}"
        )


def protected_preflight() -> dict[str, Any]:
    validate_exp016_preregistration()
    validate_exp016_implementation()
    _verify_lifecycle()
    verify_local_exp015_catalog_result()
    verify_extended_session_data_result()
    _verify_probe()

    ancestry = _run_git(
        "merge-base",
        "--is-ancestor",
        EXPECTED_PREREGISTRATION_COMMIT,
        "HEAD",
        check=False,
    )
    if ancestry.returncode != 0:
        raise RuntimeError(
            "The committed EXP-016 preregistration is not an ancestor of HEAD."
        )

    git = _git_provenance()
    if not git["working_tree_clean"]:
        raise RuntimeError(
            "Commit the EXP-016 implementation before external access."
        )

    reference = OUTPUT_FILES["NQ_1m"]
    if sha256_file(reference) != EXPECTED_REFERENCE_NQ_SHA256:
        raise RuntimeError("Frozen Quantower NQ reference hash changed.")

    _assert_ignored(DATA_ROOT)
    _assert_ignored(RESULT_ROOT)

    print()
    print("EXP-016 IMPLEMENTATION PREFLIGHT")
    print("================================")
    print("Lifecycle:                 PRE_REGISTERED")
    print("Implementation:            IMPLEMENTED_PARTIALLY_ACCESSED")
    print("Rate-limit amendment:      AVAILABLE")
    print("EXP-015 result verified:   True")
    print("Quantower reference valid: True")
    print("Vendor symbol:             NQ.F")
    print("Locked windows:            6")
    print("Original request limit:    6")
    print("Amended retry allowance:   1 failed window only")
    print("Catalog rerun:             False")
    print("Full-history download:     False")
    print("Strategy execution:        False")
    print("Primary-source claim:      False")
    print(f"Git commit:                 {git['short_commit']}")
    print("Git clean:                  True")
    print("================================")
    return git


def _request_lock(window_id: str) -> Path:
    return REQUEST_LOCK_ROOT / f"{window_id}.json"


def _window_raw_dir(window_id: str) -> Path:
    return RAW_ROOT / window_id


def _load_completed_records() -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    if not REQUEST_LOCK_ROOT.exists():
        return records
    for path in REQUEST_LOCK_ROOT.glob("*.json"):
        value = _load_json(path)
        records[str(value.get("window_id"))] = value
    return records


def run_download_samples() -> dict[str, Any]:
    git = protected_preflight()
    key = os.environ.get("LSE_API_KEY")
    if not key:
        raise RuntimeError(
            "LSE_API_KEY is not set. Do not place the key in a file."
        )

    python = _isolated_python()
    if not python.is_file():
        raise RuntimeError("The frozen isolated lse-data environment is missing.")
    if DOWNLOAD_MANIFEST.exists():
        raise RuntimeError(
            "The six-window download manifest already exists. Do not rerun."
        )

    REQUEST_LOCK_ROOT.mkdir(parents=True, exist_ok=True)
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    records = _load_completed_records()

    completed_count = 0
    for index, window in enumerate(FIXED_SAMPLE_WINDOWS):
        window_id = window["window_id"]
        existing = records.get(window_id)
        if existing:
            if existing.get("status") == "COMPLETE":
                completed_count += 1
                continue
            raise RuntimeError(
                f"{window_id} already has a non-complete request lock. "
                "Do not retry without a reviewed amendment."
            )

        lock = _request_lock(window_id)
        started = {
            "schema_version": 1,
            "experiment_id": "EXP-016",
            "window_id": window_id,
            "start": window["start"],
            "end": window["end"],
            "status": "REQUEST_STARTED",
            "started_at_utc": datetime.now(timezone.utc).isoformat(),
            "git": git,
            "request_attempt": 1,
        }
        _atomic_json(started, lock)

        destination = _window_raw_dir(window_id)
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        completed = subprocess.run(
            [
                str(python),
                str(WORKER_FILE),
                "--window-id",
                window_id,
                "--start",
                window["start"],
                "--end",
                window["end"],
                "--destination",
                str(destination),
            ],
            cwd=PROJECT_DIR,
            env=env,
            text=True,
            capture_output=True,
        )
        if completed.returncode != 0:
            failed = {
                **started,
                "status": "FAILED",
                "failed_at_utc": datetime.now(timezone.utc).isoformat(),
                "safe_error": completed.stderr.strip()[:1000],
            }
            _atomic_json(failed, lock)
            raise RuntimeError(
                f"{window_id} failed. The one-attempt lock is preserved."
            )

        worker = json.loads(completed.stdout)
        output = Path(worker["path"])
        record = {
            **started,
            "status": "COMPLETE",
            "completed_at_utc": datetime.now(timezone.utc).isoformat(),
            "symbol": "NQ.F",
            "dataset": "futures",
            "timeframe": "1m",
            "local_path": str(output.relative_to(PROJECT_DIR)),
            "size_bytes": int(output.stat().st_size),
            "sha256": sha256_file(output),
            "catalog_called": False,
            "strategy_called": False,
        }
        _atomic_json(record, lock)
        completed_count += 1

        if index < len(FIXED_SAMPLE_WINDOWS) - 1:
            time.sleep(10)

    final_records = _load_completed_records()
    ordered = [final_records[item["window_id"]] for item in FIXED_SAMPLE_WINDOWS]
    if len(ordered) != 6 or any(item["status"] != "COMPLETE" for item in ordered):
        raise RuntimeError("Not all six locked samples completed.")

    manifest = {
        "schema_version": 1,
        "experiment_id": "EXP-016",
        "result_phase": "SIX_FIXED_SAMPLES_DOWNLOADED",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "git": git,
        "client": {
            "distribution": "lse-data",
            "version": EXPECTED_CLIENT_VERSION,
            "isolated_environment": True,
        },
        "requests": ordered,
        "request_count": 6,
        "catalog_rerun": False,
        "full_history_download": False,
        "strategy_run": False,
        "api_key_written": False,
    }
    _atomic_json(manifest, DOWNLOAD_MANIFEST)

    print()
    print("EXP-016 SIX-WINDOW DOWNLOAD")
    print("===========================")
    print("Completed windows:       6")
    print("Remote history requests: 6")
    print("Vendor symbol:           NQ.F")
    print("Timeframe:               1m")
    print("Catalog rerun:           False")
    print("Full history:            False")
    print("Strategy run:            False")
    print("===========================")
    return manifest



def _verify_rate_limit_amendment_state() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    validate_exp016_rate_limit_amendment()

    ancestry = _run_git(
        "merge-base",
        "--is-ancestor",
        EXPECTED_IMPLEMENTATION_COMMIT,
        "HEAD",
        check=False,
    )
    if ancestry.returncode != 0:
        raise RuntimeError(
            "The frozen EXP-016 implementation commit is not an ancestor of HEAD."
        )

    if DOWNLOAD_MANIFEST.exists():
        raise RuntimeError(
            "The six-window download manifest already exists. No retry is allowed."
        )

    records = _load_completed_records()
    expected_ids = {
        item["window_id"] for item in COMPLETED_BEFORE_RATE_LIMIT
    } | {OBSERVED_RATE_LIMIT_FAILURE["window_id"]}
    if set(records) != expected_ids:
        raise RuntimeError(
            "The original request-lock set does not match the frozen amendment evidence."
        )

    successful: list[dict[str, Any]] = []
    for expected in COMPLETED_BEFORE_RATE_LIMIT:
        record = records[expected["window_id"]]
        if (
            record.get("status") != "COMPLETE"
            or record.get("request_attempt") != 1
            or record.get("start") != expected["start"]
            or record.get("end") != expected["end"]
            or record.get("size_bytes") != expected["size_bytes"]
            or record.get("sha256") != expected["sha256"]
            or record.get("local_path") != expected["local_path"]
        ):
            raise RuntimeError(
                f"Frozen successful request changed: {expected['window_id']}"
            )
        path = PROJECT_DIR / record["local_path"]
        if (
            not path.is_file()
            or path.stat().st_size != expected["size_bytes"]
            or sha256_file(path) != expected["sha256"]
        ):
            raise RuntimeError(
                f"Frozen successful sample changed: {expected['window_id']}"
            )
        successful.append(record)

    failed = records[OBSERVED_RATE_LIMIT_FAILURE["window_id"]]
    safe_error = str(failed.get("safe_error", ""))
    if (
        failed.get("status") != "FAILED"
        or failed.get("request_attempt") != 1
        or failed.get("start") != OBSERVED_RATE_LIMIT_FAILURE["start"]
        or failed.get("end") != OBSERVED_RATE_LIMIT_FAILURE["end"]
        or safe_error != OBSERVED_RATE_LIMIT_FAILURE["safe_error"]
        or failed.get("local_path")
        or failed.get("size_bytes")
        or failed.get("sha256")
    ):
        raise RuntimeError("The frozen 429 failure evidence changed.")

    failed_at_text = failed.get("failed_at_utc")
    if not isinstance(failed_at_text, str):
        raise RuntimeError("The original failed request has no failure timestamp.")
    failed_at = datetime.fromisoformat(failed_at_text)
    if failed_at.tzinfo is None:
        raise RuntimeError("The original failure timestamp is not timezone-aware.")
    elapsed = (datetime.now(timezone.utc) - failed_at.astimezone(timezone.utc)).total_seconds()
    if elapsed < MINIMUM_RETRY_WAIT_SECONDS:
        remaining = int(MINIMUM_RETRY_WAIT_SECONDS - elapsed + 59) // 60
        raise RuntimeError(
            f"The amended retry cooldown has not elapsed. Wait at least {remaining} more minute(s)."
        )

    return failed, successful


def run_retry_rate_limited_window() -> dict[str, Any]:
    git = protected_preflight()
    failed, successful = _verify_rate_limit_amendment_state()

    key = os.environ.get("LSE_API_KEY")
    if not key:
        raise RuntimeError(
            "LSE_API_KEY is not set. Do not place the key in a file."
        )

    python = _isolated_python()
    if not python.is_file():
        raise RuntimeError("The frozen isolated lse-data environment is missing.")

    retry_lock = PROJECT_DIR / RETRY_LOCK_RELATIVE_PATH
    retry_destination = PROJECT_DIR / RETRY_RAW_RELATIVE_PATH
    if retry_lock.exists():
        raise RuntimeError(
            "The one amended retry already has a lock. No further retry is allowed."
        )
    if retry_destination.exists():
        raise RuntimeError(
            "The amended retry destination already exists. Stop for review."
        )

    retry_lock.parent.mkdir(parents=True, exist_ok=True)
    started = {
        "schema_version": 1,
        "experiment_id": "EXP-016",
        "amendment_id": "EXP-016-A1",
        "window_id": OBSERVED_RATE_LIMIT_FAILURE["window_id"],
        "start": OBSERVED_RATE_LIMIT_FAILURE["start"],
        "end": OBSERVED_RATE_LIMIT_FAILURE["end"],
        "status": "RETRY_REQUEST_STARTED",
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "git": git,
        "original_request_attempt": 1,
        "amended_retry_attempt": 1,
        "total_window_request_attempt": 2,
        "original_failure_preserved": True,
        "original_safe_error": OBSERVED_RATE_LIMIT_FAILURE["safe_error"],
    }
    _atomic_json(started, retry_lock)

    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [
            str(python),
            str(WORKER_FILE),
            "--window-id",
            OBSERVED_RATE_LIMIT_FAILURE["window_id"],
            "--start",
            OBSERVED_RATE_LIMIT_FAILURE["start"],
            "--end",
            OBSERVED_RATE_LIMIT_FAILURE["end"],
            "--destination",
            str(retry_destination),
        ],
        cwd=PROJECT_DIR,
        env=env,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        retry_failed = {
            **started,
            "status": "RETRY_FAILED",
            "failed_at_utc": datetime.now(timezone.utc).isoformat(),
            "safe_error": completed.stderr.strip()[:1000],
            "additional_retry_authorized": False,
        }
        _atomic_json(retry_failed, retry_lock)
        raise RuntimeError(
            "The one amended retry failed. No additional request is authorized."
        )

    worker = json.loads(completed.stdout)
    output = Path(worker["path"])
    retry_record = {
        **started,
        "status": "COMPLETE",
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "symbol": "NQ.F",
        "dataset": "futures",
        "timeframe": "1m",
        "local_path": str(output.relative_to(PROJECT_DIR)),
        "size_bytes": int(output.stat().st_size),
        "sha256": sha256_file(output),
        "catalog_called": False,
        "strategy_called": False,
        "additional_retry_authorized": False,
    }
    _atomic_json(retry_record, retry_lock)

    requests = [*successful, retry_record]
    by_id = {item["window_id"]: item for item in requests}
    ordered = [by_id[item["window_id"]] for item in FIXED_SAMPLE_WINDOWS]
    manifest = {
        "schema_version": 1,
        "experiment_id": "EXP-016",
        "result_phase": "SIX_FIXED_SAMPLES_DOWNLOADED_WITH_RATE_LIMIT_AMENDMENT",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "git": git,
        "client": {
            "distribution": "lse-data",
            "version": EXPECTED_CLIENT_VERSION,
            "isolated_environment": True,
        },
        "requests": ordered,
        "successful_sample_count": 6,
        "original_request_attempt_count": 6,
        "amended_retry_attempt_count": 1,
        "total_remote_history_request_attempts": 7,
        "original_rate_limit_failure": failed,
        "rate_limit_amendment": {
            "amendment_id": "EXP-016-A1",
            "retry_window_id": OBSERVED_RATE_LIMIT_FAILURE["window_id"],
            "original_failure_preserved": True,
            "only_one_additional_attempt": True,
            "minimum_wait_seconds": MINIMUM_RETRY_WAIT_SECONDS,
        },
        "catalog_rerun": False,
        "full_history_download": False,
        "strategy_run": False,
        "api_key_written": False,
    }
    _atomic_json(manifest, DOWNLOAD_MANIFEST)

    print()
    print("EXP-016 RATE-LIMITED WINDOW RETRY")
    print("=================================")
    print("Retry window:             2025_march_dst_roll")
    print("Original completed:       5")
    print("Amended retry completed:  1")
    print("Successful samples:       6")
    print("Total request attempts:   7")
    print("Original failure kept:    True")
    print("Further retry allowed:    False")
    print("Catalog rerun:            False")
    print("Full history:             False")
    print("Strategy run:             False")
    print("=================================")
    return manifest

def run_local_audit() -> dict[str, Any]:
    git = protected_preflight()
    if not DOWNLOAD_MANIFEST.is_file():
        raise RuntimeError("Run the six fixed sample download first.")
    if RESULT_JSON.exists():
        raise RuntimeError("EXP-016 local audit result already exists.")

    manifest = _load_json(DOWNLOAD_MANIFEST)
    requests = manifest.get("requests")
    if not isinstance(requests, list) or len(requests) != 6:
        raise RuntimeError("The download manifest is incomplete.")

    reference = pd.read_parquet(OUTPUT_FILES["NQ_1m"])
    structural_rows: list[dict[str, Any]] = []
    cross_rows: list[dict[str, Any]] = []
    discrepancies: list[pd.DataFrame] = []

    by_window = {item["window_id"]: item for item in requests}
    for window in FIXED_SAMPLE_WINDOWS:
        record = by_window[window["window_id"]]
        path = PROJECT_DIR / record["local_path"]
        if sha256_file(path) != record["sha256"]:
            raise RuntimeError(
                f"Vendor sample hash changed: {window['window_id']}"
            )
        raw = pd.read_parquet(path)
        canonical = canonicalize_vendor_frame(raw)
        structural_rows.append(
            {
                "window_id": window["window_id"],
                "start": window["start"],
                "end": window["end"],
                "raw_rows": int(len(raw)),
                "timestamp_source": canonical.timestamp_source,
                "timestamp_timezone_aware": (
                    canonical.timestamp_timezone_aware
                ),
                "duplicate_timestamp_count": (
                    canonical.duplicate_timestamp_count
                ),
                "invalid_ohlc_rows": canonical.invalid_ohlc_rows,
                "negative_volume_rows": canonical.negative_volume_rows,
                "nonfinite_ohlcv_rows": canonical.nonfinite_ohlcv_rows,
                "raw_sha256": record["sha256"],
            }
        )
        cross, detail = compare_with_reference(
            vendor=canonical,
            reference=reference,
            start=window["start"],
            end=window["end"],
            window_id=window["window_id"],
        )
        cross_rows.append(cross)
        if not detail.empty:
            discrepancies.append(detail)

    structural = pd.DataFrame(structural_rows)
    cross_source = pd.DataFrame(cross_rows)
    classification = classify_audit(structural, cross_source)

    RESULT_ROOT.mkdir(parents=True, exist_ok=True)
    structural.to_csv(STRUCTURAL_CSV, index=False, lineterminator="\n")
    cross_source.to_csv(CROSS_SOURCE_CSV, index=False, lineterminator="\n")
    if discrepancies:
        pd.concat(discrepancies, ignore_index=True).to_csv(
            DISCREPANCIES_CSV,
            index=False,
            lineterminator="\n",
        )
    else:
        pd.DataFrame().to_csv(DISCREPANCIES_CSV, index=False)

    result = {
        "schema_version": 1,
        "experiment_id": "EXP-016",
        "result_phase": "LOCAL_SAMPLE_AUDIT",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "git": git,
        "classification": classification,
        "classification_scope": "SUPPLEMENTARY_NQ_SOURCE_ONLY",
        "sample_windows": 6,
        "methodology": {
            "contract_type": "UNRESOLVED",
            "continuous_series_method": "UNRESOLVED",
            "roll_method": "UNRESOLVED",
            "price_adjustment": "UNRESOLVED",
            "volume_semantics": "UNRESOLVED",
        },
        "outputs": {
            "structural_csv": str(STRUCTURAL_CSV.relative_to(PROJECT_DIR)),
            "cross_source_csv": str(CROSS_SOURCE_CSV.relative_to(PROJECT_DIR)),
            "discrepancies_csv": str(
                DISCREPANCIES_CSV.relative_to(PROJECT_DIR)
            ),
        },
        "research_boundary": {
            "primary_source_qualified": False,
            "mnq_qualified": False,
            "other_assets_qualified": False,
            "quantower_replaced": False,
            "strategy_run": False,
            "optimization_run": False,
            "paper_trading_authorized": False,
            "live_trading_authorized": False,
        },
    }
    _atomic_json(result, RESULT_JSON)

    print()
    print("EXP-016 LOCAL SAMPLE AUDIT")
    print("==========================")
    print(f"Classification:       {classification}")
    print("Sample windows:       6")
    print("Primary source claim: False")
    print("Quantower replaced:   False")
    print("Strategy run:         False")
    print("Paper/live authority: False")
    print("==========================")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--preflight", action="store_true")
    group.add_argument("--download-samples", action="store_true")
    group.add_argument("--retry-rate-limited-window", action="store_true")
    group.add_argument("--audit-local", action="store_true")
    args = parser.parse_args()

    if args.preflight:
        protected_preflight()
    elif args.download_samples:
        run_download_samples()
    elif args.retry_rate_limited_window:
        run_retry_rate_limited_window()
    else:
        run_local_audit()


if __name__ == "__main__":
    main()
