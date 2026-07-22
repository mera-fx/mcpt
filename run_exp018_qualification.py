from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import numpy as np
import pandas as pd

from exp017_closure import validate_exp017_closure
from exp018_implementation import (
    DATABENTO_ENVIRONMENT_VARIABLE,
    DATABENTO_VENV,
    EXPECTED_DATABENTO_CLIENT_VERSION,
    EXPECTED_PREREGISTRATION_COMMIT,
    EXTRACT_ROOT,
    INITIAL_LOCK_ROOT,
    INITIAL_MANIFEST,
    INITIAL_RAW_ROOT,
    MISSING_RUNS_CSV,
    REPEATABILITY_CSV,
    REPEATABILITY_WINDOW_IDS,
    REPEAT_LOCK_ROOT,
    REPEAT_MANIFEST,
    REPEAT_RAW_ROOT,
    RESULT_JSON,
    RESULT_ROOT,
    SESSION_CSV,
    WINDOW_CSV,
    WORKER_FILE,
    validate_exp018_implementation,
)
from exp018_measurements import (
    audit_arrays,
    classify,
    load_npz,
    sha256_file,
)
from exp018_preregistration import WINDOWS, validate_exp018_preregistration
from experiment_lifecycle import get_experiment_lifecycle


PROJECT_DIR = Path(__file__).resolve().parent
WINDOW_BY_ID = {item[0]: item for item in WINDOWS}


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
    temporary.write_bytes(
        (json.dumps(value, indent=2, allow_nan=False) + "\n").encode("utf-8")
    )
    temporary.replace(path)


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"Expected a JSON object: {path}")
    return value


def _isolated_python() -> Path:
    if os.name == "nt":
        return DATABENTO_VENV / "Scripts" / "python.exe"
    return DATABENTO_VENV / "bin" / "python"


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
        raise RuntimeError(f"Protected output path is not ignored by Git: {relative}")


def _verify_client(python: Path) -> None:
    completed = subprocess.run(
        [
            str(python),
            "-c",
            (
                "import databento as db; "
                "print(db.__version__); "
                "print(bool(__import__('os').environ.get('DATABENTO_API_KEY')))"
            ),
        ],
        cwd=PROJECT_DIR,
        text=True,
        capture_output=True,
        check=True,
    )
    lines = completed.stdout.strip().splitlines()
    if not lines or lines[0].strip() != EXPECTED_DATABENTO_CLIENT_VERSION:
        raise RuntimeError("The isolated Databento client version changed.")


def protected_preflight() -> dict[str, Any]:
    validate_exp017_closure()
    validate_exp018_preregistration()
    validate_exp018_implementation()

    if get_experiment_lifecycle("EXP-017").stage != "REVIEW":
        raise RuntimeError("EXP-017 must remain in REVIEW.")
    if get_experiment_lifecycle("EXP-018").stage != "PRE_REGISTERED":
        raise RuntimeError("EXP-018 must remain PRE_REGISTERED.")

    ancestry = _run_git(
        "merge-base",
        "--is-ancestor",
        EXPECTED_PREREGISTRATION_COMMIT,
        "HEAD",
        check=False,
    )
    if ancestry.returncode != 0:
        raise RuntimeError("The committed EXP-018 preregistration is not an ancestor of HEAD.")

    git = _git_provenance()
    if not git["working_tree_clean"]:
        raise RuntimeError("Commit the EXP-018 implementation before any data access.")

    python = _isolated_python()
    if not python.is_file():
        raise RuntimeError("The isolated Databento environment is missing.")
    _verify_client(python)

    _assert_ignored(PROJECT_DIR / "data" / "EXP-018")
    _assert_ignored(RESULT_ROOT)

    print()
    print("EXP-018 IMPLEMENTATION PREFLIGHT")
    print("================================")
    print("Lifecycle:                 PRE_REGISTERED")
    print("Implementation:            IMPLEMENTED_NOT_RUN")
    print("Databento client:          0.81.0")
    print("Dataset/schema:            GLBX.MDP3 / ohlcv-1m")
    print("Locked initial requests:   6")
    print("Locked delayed repeats:    2")
    print("Maximum successful bars:   8")
    print("Minimum repeat delay:      24 hours")
    print("Cost cap:                  $1.00")
    print("Automatic retry:           False")
    print("Full history:              False")
    print("Strategy execution:        False")
    print(f"Git commit:                 {git['short_commit']}")
    print("Git clean:                  True")
    print("================================")
    return git


def _worker(
    python: Path,
    args: list[str],
    *,
    require_key: bool,
) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if require_key and not env.get(DATABENTO_ENVIRONMENT_VARIABLE):
        raise RuntimeError(
            "DATABENTO_API_KEY is not set. Do not place the key in a file."
        )
    completed = subprocess.run(
        [str(python), str(WORKER_FILE), *args],
        cwd=PROJECT_DIR,
        env=env,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip()[:1000] or "Worker failed.")
    value = json.loads(completed.stdout)
    if not isinstance(value, dict):
        raise RuntimeError("Worker returned a non-object response.")
    return value


def _lock_path(phase: str, window_id: str) -> Path:
    root = INITIAL_LOCK_ROOT if phase == "initial" else REPEAT_LOCK_ROOT
    return root / f"{window_id}.json"


def _raw_path(phase: str, window_id: str) -> Path:
    root = INITIAL_RAW_ROOT if phase == "initial" else REPEAT_RAW_ROOT
    return root / f"{window_id}.ohlcv-1m.dbn.zst"


def _completed_locks(root: Path) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    if not root.exists():
        return records
    for path in root.glob("*.json"):
        value = _load_json(path)
        records[str(value.get("window_id"))] = value
    return records


def _all_estimated_cost() -> float:
    total = 0.0
    for root in (INITIAL_LOCK_ROOT, REPEAT_LOCK_ROOT):
        for value in _completed_locks(root).values():
            if value.get("status") == "COMPLETE":
                total += float(value.get("estimated_cost_usd", 0.0))
    return total


def _request_one(
    *,
    phase: str,
    window: tuple[Any, ...],
    git: dict[str, Any],
    python: Path,
) -> dict[str, Any]:
    window_id, canonical, raw_symbol, instrument_id, start, end = window
    lock = _lock_path(phase, window_id)
    destination = _raw_path(phase, window_id)
    lock.parent.mkdir(parents=True, exist_ok=True)
    destination.parent.mkdir(parents=True, exist_ok=True)

    if lock.exists():
        prior = _load_json(lock)
        if prior.get("status") == "COMPLETE":
            return prior
        raise RuntimeError(
            f"{phase}/{window_id} already has a non-complete request lock. "
            "No retry is allowed without a reviewed amendment."
        )
    if destination.exists():
        raise RuntimeError(f"Unmanifested raw destination already exists: {destination}")

    started = {
        "schema_version": 1,
        "experiment_id": "EXP-018",
        "phase": phase,
        "window_id": window_id,
        "canonical_contract": canonical,
        "raw_symbol": raw_symbol,
        "expected_instrument_id": int(instrument_id),
        "start": start,
        "end_exclusive": end,
        "status": "REQUEST_STARTED",
        "request_attempt": 1,
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "git": git,
    }
    _atomic_json(started, lock)

    try:
        cost_result = _worker(
            python,
            [
                "estimate-cost",
                "--raw-symbol",
                raw_symbol,
                "--start",
                start,
                "--end",
                end,
            ],
            require_key=True,
        )
        estimated_cost = float(cost_result["estimated_cost_usd"])
        cumulative = _all_estimated_cost() + estimated_cost
        if cumulative > 1.0:
            raise RuntimeError(
                f"The locked $1.00 cost cap would be exceeded: ${cumulative:.9f}."
            )

        worker = _worker(
            python,
            [
                "download",
                "--raw-symbol",
                raw_symbol,
                "--instrument-id",
                str(instrument_id),
                "--start",
                start,
                "--end",
                end,
                "--destination",
                str(destination),
            ],
            require_key=True,
        )
    except Exception as exc:
        failed = {
            **started,
            "status": "FAILED",
            "failed_at_utc": datetime.now(timezone.utc).isoformat(),
            "safe_error": str(exc)[:1000],
        }
        _atomic_json(failed, lock)
        raise RuntimeError(
            f"{phase}/{window_id} failed. The one-attempt lock is preserved."
        ) from None

    record = {
        **started,
        "status": "COMPLETE",
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "estimated_cost_usd": estimated_cost,
        "local_path": destination.relative_to(PROJECT_DIR).as_posix(),
        "size_bytes": int(destination.stat().st_size),
        "sha256": sha256_file(destination),
        "remote_method": worker["remote_method"],
        "batch_called": False,
        "continuous_symbol_used": False,
        "strategy_called": False,
        "api_key_written": False,
    }
    _atomic_json(record, lock)
    return record


def run_initial_downloads() -> dict[str, Any]:
    git = protected_preflight()
    if INITIAL_MANIFEST.exists():
        raise RuntimeError("The initial manifest already exists. Do not rerun.")
    python = _isolated_python()

    records = [
        _request_one(phase="initial", window=window, git=git, python=python)
        for window in WINDOWS
    ]
    if len(records) != 6 or any(item.get("status") != "COMPLETE" for item in records):
        raise RuntimeError("Not all six initial requests completed.")

    manifest = {
        "schema_version": 1,
        "experiment_id": "EXP-018",
        "phase": "INITIAL_SIX_WINDOWS_COMPLETE",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "git": git,
        "requests": records,
        "successful_bar_requests": 6,
        "total_estimated_cost_usd": float(
            sum(float(item["estimated_cost_usd"]) for item in records)
        ),
        "automatic_retries": 0,
        "full_history": False,
        "strategy_run": False,
    }
    _atomic_json(manifest, INITIAL_MANIFEST)

    print()
    print("EXP-018 INITIAL DOWNLOADS")
    print("=========================")
    print("Completed windows:       6")
    print("Successful bar requests: 6")
    print(f"Estimated cost:          ${manifest['total_estimated_cost_usd']:.6f}")
    print("Automatic retries:       0")
    print("Full history:            False")
    print("Strategy run:            False")
    print("=========================")
    return manifest


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise RuntimeError("Expected timezone-aware UTC timestamp.")
    return parsed.astimezone(timezone.utc)


def run_repeat_downloads() -> dict[str, Any]:
    git = protected_preflight()
    if not INITIAL_MANIFEST.is_file():
        raise RuntimeError("The initial six-window manifest is missing.")
    if REPEAT_MANIFEST.exists():
        raise RuntimeError("The repeat manifest already exists. Do not rerun.")

    initial = _load_json(INITIAL_MANIFEST)
    initial_by_id = {item["window_id"]: item for item in initial["requests"]}
    now = datetime.now(timezone.utc)
    for window_id in REPEATABILITY_WINDOW_IDS:
        completed = _parse_utc(initial_by_id[window_id]["completed_at_utc"])
        elapsed_hours = (now - completed).total_seconds() / 3600.0
        if elapsed_hours < 24.0:
            raise RuntimeError(
                f"{window_id} repeat is too early: {elapsed_hours:.3f} hours."
            )

    python = _isolated_python()
    records = [
        _request_one(
            phase="repeat",
            window=WINDOW_BY_ID[window_id],
            git=git,
            python=python,
        )
        for window_id in REPEATABILITY_WINDOW_IDS
    ]
    if len(records) != 2 or any(item.get("status") != "COMPLETE" for item in records):
        raise RuntimeError("Both repeat requests must complete.")

    manifest = {
        "schema_version": 1,
        "experiment_id": "EXP-018",
        "phase": "TWO_DELAYED_REPEATS_COMPLETE",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "git": git,
        "requests": records,
        "successful_bar_requests": 2,
        "total_estimated_cost_usd": float(
            sum(float(item["estimated_cost_usd"]) for item in records)
        ),
        "minimum_delay_hours": 24,
        "automatic_retries": 0,
        "full_history": False,
        "strategy_run": False,
    }
    _atomic_json(manifest, REPEAT_MANIFEST)

    print()
    print("EXP-018 DELAYED REPEATS")
    print("=======================")
    print("Completed repeat windows: 2")
    print("Minimum delay met:         True")
    print(f"Estimated repeat cost:     ${manifest['total_estimated_cost_usd']:.6f}")
    print("Automatic retries:         0")
    print("=======================")
    return manifest


def _extract_one(
    python: Path,
    *,
    phase: str,
    record: dict[str, Any],
) -> Path:
    source = PROJECT_DIR / record["local_path"]
    destination = EXTRACT_ROOT / phase / f"{record['window_id']}.npz"
    _worker(
        python,
        [
            "extract",
            "--source",
            str(source),
            "--destination",
            str(destination),
        ],
        require_key=False,
    )
    return destination


def _repeatability_table(
    initial_records: dict[str, dict[str, Any]],
    repeat_records: dict[str, dict[str, Any]],
    initial_hashes: dict[str, str],
    repeat_hashes: dict[str, str],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for window_id in REPEATABILITY_WINDOW_IDS:
        initial_record = initial_records[window_id]
        repeat_record = repeat_records[window_id]
        initial_completed = _parse_utc(initial_record["completed_at_utc"])
        repeat_started = _parse_utc(repeat_record["started_at_utc"])
        delay_hours = (repeat_started - initial_completed).total_seconds() / 3600.0

        initial_npz = EXTRACT_ROOT / "initial" / f"{window_id}.npz"
        repeat_npz = EXTRACT_ROOT / "repeat" / f"{window_id}.npz"
        initial_arrays = load_npz(initial_npz)
        repeat_arrays = load_npz(repeat_npz)
        timestamp_match = np.array_equal(
            np.sort(initial_arrays.ts_event),
            np.sort(repeat_arrays.ts_event),
        )

        rows.append(
            {
                "window_id": window_id,
                "delay_hours": delay_hours,
                "minimum_delay_met": delay_hours >= 24.0,
                "initial_raw_sha256": initial_record["sha256"],
                "repeat_raw_sha256": repeat_record["sha256"],
                "raw_hash_match": initial_record["sha256"] == repeat_record["sha256"],
                "initial_canonical_sha256": initial_hashes[window_id],
                "repeat_canonical_sha256": repeat_hashes[window_id],
                "canonical_hash_match": initial_hashes[window_id]
                == repeat_hashes[window_id],
                "initial_rows": initial_arrays.row_count,
                "repeat_rows": repeat_arrays.row_count,
                "row_count_match": initial_arrays.row_count
                == repeat_arrays.row_count,
                "timestamp_set_match": bool(timestamp_match),
            }
        )
    return pd.DataFrame(rows)


def run_audit_local() -> dict[str, Any]:
    git = protected_preflight()
    if not INITIAL_MANIFEST.is_file():
        raise RuntimeError("The initial manifest is required before local audit.")

    initial_manifest = _load_json(INITIAL_MANIFEST)
    initial_records = {
        item["window_id"]: item for item in initial_manifest["requests"]
    }
    if set(initial_records) != {item[0] for item in WINDOWS}:
        raise RuntimeError("Initial manifest does not contain the six locked windows.")

    python = _isolated_python()
    window_rows: list[dict[str, Any]] = []
    session_frames: list[pd.DataFrame] = []
    missing_frames: list[pd.DataFrame] = []
    initial_hashes: dict[str, str] = {}

    for window in WINDOWS:
        window_id, canonical, raw_symbol, instrument_id, start, end = window
        record = initial_records[window_id]
        raw_path = PROJECT_DIR / record["local_path"]
        if sha256_file(raw_path) != record["sha256"]:
            raise RuntimeError(f"Raw hash changed for {window_id}.")
        npz_path = _extract_one(python, phase="initial", record=record)
        result = audit_arrays(
            load_npz(npz_path),
            window_id=window_id,
            canonical_contract=canonical,
            raw_symbol=raw_symbol,
            expected_instrument_id=int(instrument_id),
            start=start,
            end_exclusive=end,
            raw_sha256=record["sha256"],
            size_bytes=int(record["size_bytes"]),
        )
        window_rows.append(result.window)
        session_frames.append(result.sessions)
        missing_frames.append(result.missing_runs)
        initial_hashes[window_id] = result.canonical_hash

    windows = pd.DataFrame(window_rows)
    sessions = pd.concat(session_frames, ignore_index=True)
    missing = pd.concat(missing_frames, ignore_index=True)

    repeatability = pd.DataFrame()
    repeat_hashes: dict[str, str] = {}
    repeat_records: dict[str, dict[str, Any]] = {}
    if REPEAT_MANIFEST.is_file():
        repeat_manifest = _load_json(REPEAT_MANIFEST)
        repeat_records = {
            item["window_id"]: item for item in repeat_manifest["requests"]
        }
        for window_id in REPEATABILITY_WINDOW_IDS:
            record = repeat_records[window_id]
            raw_path = PROJECT_DIR / record["local_path"]
            if sha256_file(raw_path) != record["sha256"]:
                raise RuntimeError(f"Repeat raw hash changed for {window_id}.")
            npz_path = _extract_one(python, phase="repeat", record=record)
            window = WINDOW_BY_ID[window_id]
            result = audit_arrays(
                load_npz(npz_path),
                window_id=window_id,
                canonical_contract=window[1],
                raw_symbol=window[2],
                expected_instrument_id=int(window[3]),
                start=window[4],
                end_exclusive=window[5],
                raw_sha256=record["sha256"],
                size_bytes=int(record["size_bytes"]),
            )
            repeat_hashes[window_id] = result.canonical_hash
        repeatability = _repeatability_table(
            initial_records,
            repeat_records,
            initial_hashes,
            repeat_hashes,
        )

    total_cost = _all_estimated_cost()
    classification = classify(
        windows,
        repeatability,
        total_estimated_cost_usd=total_cost,
    )

    RESULT_ROOT.mkdir(parents=True, exist_ok=True)
    windows.to_csv(WINDOW_CSV, index=False)
    sessions.to_csv(SESSION_CSV, index=False)
    missing.to_csv(MISSING_RUNS_CSV, index=False)
    repeatability.to_csv(REPEATABILITY_CSV, index=False)

    result = {
        "schema_version": 1,
        "experiment_id": "EXP-018",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "git": git,
        "classification": classification,
        "initial_windows_measured": int(len(windows)),
        "repeatability_windows_measured": int(len(repeatability)),
        "total_estimated_cost_usd": total_cost,
        "gates": {
            "minimum_regular_trade_minute_coverage": 0.999,
            "minimum_extended_trade_minute_coverage": 0.995,
            "maximum_total_cost_usd": 1.0,
            "repeat_canonical_hash_exact": True,
        },
        "observed": {
            "minimum_regular_trade_minute_coverage": float(
                windows["regular_trade_minute_coverage"].min()
            ),
            "minimum_extended_trade_minute_coverage": float(
                windows["extended_trade_minute_coverage"].min()
            ),
            "identity_mismatch_rows": int(windows["identity_mismatch_rows"].sum()),
            "duplicate_timestamp_rows": int(
                windows["duplicate_timestamp_rows"].sum()
            ),
            "duplicate_full_rows": int(windows["duplicate_full_rows"].sum()),
            "invalid_ohlc_rows": int(windows["invalid_ohlc_rows"].sum()),
            "negative_volume_rows": int(windows["negative_volume_rows"].sum()),
            "nonfinite_ohlcv_rows": int(windows["nonfinite_ohlcv_rows"].sum()),
            "off_tick_ohlc_values": int(windows["off_tick_ohlc_values"].sum()),
        },
        "boundaries": {
            "exchange_accuracy_claim": False,
            "best_vendor_claim": False,
            "full_history_download": False,
            "continuous_series_construction": False,
            "strategy_run": False,
            "paper_trading_authorized": False,
            "live_trading_authorized": False,
        },
    }
    _atomic_json(result, RESULT_JSON)

    print()
    print("EXP-018 LOCAL AUDIT")
    print("===================")
    print(f"Classification:            {classification}")
    print(f"Initial windows measured:  {len(windows)}")
    print(f"Repeat windows measured:   {len(repeatability)}")
    print(
        "Minimum regular coverage: "
        f"{windows['regular_trade_minute_coverage'].min():.6%}"
    )
    print(
        "Minimum extended coverage: "
        f"{windows['extended_trade_minute_coverage'].min():.6%}"
    )
    print(f"Estimated total cost:      ${total_cost:.6f}")
    print("Exchange accuracy claim:   False")
    print("Strategy run:              False")
    print("===================")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--preflight", action="store_true")
    modes.add_argument("--initial-downloads", action="store_true")
    modes.add_argument("--repeat-downloads", action="store_true")
    modes.add_argument("--audit-local", action="store_true")
    args = parser.parse_args()

    if args.preflight:
        protected_preflight()
    elif args.initial_downloads:
        run_initial_downloads()
    elif args.repeat_downloads:
        run_repeat_downloads()
    else:
        run_audit_local()


if __name__ == "__main__":
    main()
