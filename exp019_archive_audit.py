from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
from typing import Any

import numpy as np
import pandas as pd

from exp019_archive_audit_preregistration import (
    get_exp019_archive_audit_preregistration,
    validate_exp019_archive_audit_preregistration,
)
from exp019_preregistration import (
    CONTRACT_PLAN,
    validate_exp019_preregistration,
)


PROJECT_DIR = Path(__file__).resolve().parent

LOCKED_AUDIT_PREREGISTRATION_COMMIT = (
    "0ffc71d048f1ccf82e8311794789a18a61519bd0"
)

LOCKED_PATHS = (
    "exp019_preregistration.py",
    "research/EXP-019_preregistration.md",
    "exp019_acquisition_authorization.py",
    "research/EXP-019_acquisition_authorization.md",
    "exp019_archive_audit_preregistration.py",
    "research/EXP-019_archive_audit_preregistration.md",
)

ARCHIVE_ROOT = (
    PROJECT_DIR
    / "data"
    / "EXP-019"
    / "exact_contract_archive"
)

RAW_DIR = ARCHIVE_ROOT / "raw"

MANIFEST_PATH = (
    ARCHIVE_ROOT
    / "acquisition_manifest.json"
)

COMPLETION_PATH = (
    ARCHIVE_ROOT
    / "ACQUISITION_COMPLETE.json"
)

OUTPUT_PARENT = (
    PROJECT_DIR
    / "results"
    / "EXP-019"
)

OUTPUT_DIR = (
    OUTPUT_PARENT
    / "archive_audit"
)

PARTIAL_OUTPUT_DIR = (
    OUTPUT_PARENT
    / "archive_audit.partial"
)

SUMMARY_PATH = (
    OUTPUT_DIR
    / "exp019_archive_audit_summary.json"
)

CONTRACTS_PATH = (
    OUTPUT_DIR
    / "exp019_archive_audit_contracts.csv"
)

OVERLAPS_PATH = (
    OUTPUT_DIR
    / "exp019_archive_audit_overlaps.csv"
)

REPORT_PATH = (
    OUTPUT_DIR
    / "report.md"
)

COMPLETION_OUTPUT_PATH = (
    OUTPUT_DIR
    / "AUDIT_COMPLETE.json"
)

EXPECTED_FILE_COUNT = 66
EXPECTED_TOTAL_BYTES = 104_491_346

EXPECTED_MANIFEST_SHA256 = (
    "f8fbac395bbe7f9cdafd0187a00c3d77"
    "ee8f6ded31d7ba6870d6ed3c8e3007b3"
)

EXPECTED_COMPLETION_SHA256 = (
    "ef8ad499e62284d872edfd480e7aa635"
    "a26340e85ba1d74d98a51ed80f71f935"
)

EXPECTED_ARCHIVE_SHA256 = (
    "225a64dc06cb6bb303fd83d186f2e7d8"
    "1e2a8a8bec44382380c8ccc1b0b6baa3"
)

KNOWN_PROVIDER_WARNING_WINDOWS = 16

REQUIRED_COLUMNS = (
    "instrument_id",
    "open",
    "high",
    "low",
    "close",
    "volume",
)

HARD_CHECK_NAMES = (
    "archive_file_count",
    "manifest_file_size",
    "manifest_file_sha256",
    "dbn_readability",
    "ohlcv_1m_schema",
    "nonempty_records",
    "required_columns",
    "single_instrument_id_per_file",
    "timestamps_inside_locked_window",
    "minute_timestamp_alignment",
    "monotonic_timestamp_order",
    "duplicate_timestamps",
    "duplicate_full_rows",
    "finite_ohlcv",
    "ohlc_invariants",
    "negative_volume",
    "nq_quarter_point_tick_alignment",
)


def utc_now() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def run_git(
    *args: str,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=PROJECT_DIR,
        text=True,
        capture_output=True,
        check=check,
    )


def sha256_file(
    path: Path,
) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for block in iter(
            lambda: handle.read(
                1024 * 1024
            ),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def archive_digest(
    completed: list[
        dict[str, Any]
    ],
) -> str:
    payload = [
        {
            "sequence": row["sequence"],
            "canonical_symbol": (
                row["canonical_symbol"]
            ),
            "sha256": row["sha256"],
            "size_bytes": row["size_bytes"],
        }
        for row in sorted(
            completed,
            key=lambda item: item[
                "sequence"
            ],
        )
    ]

    encoded = json.dumps(
        payload,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")

    return hashlib.sha256(
        encoded
    ).hexdigest()


def enum_text(
    value: Any,
) -> str:
    raw = getattr(
        value,
        "value",
        value,
    )

    return (
        str(raw)
        .strip()
        .lower()
        .replace("_", "-")
    )


def schema_is_ohlcv_1m(
    value: Any,
) -> bool:
    text = enum_text(value)

    return (
        "ohlcv-1m" in text
        or "ohlcv1m" in text
    )


def stype_matches(
    value: Any,
    expected: str,
) -> bool:
    text = enum_text(value)
    expected_text = (
        expected
        .lower()
        .replace("_", "-")
    )

    return (
        text == expected_text
        or text.endswith(
            "." + expected_text
        )
        or expected_text in text
    )


def extract_timestamps(
    frame: pd.DataFrame,
) -> pd.DatetimeIndex:
    if isinstance(
        frame.index,
        pd.DatetimeIndex,
    ):
        timestamps = pd.DatetimeIndex(
            frame.index
        )
    elif "ts_event" in frame.columns:
        timestamps = pd.DatetimeIndex(
            pd.to_datetime(
                frame["ts_event"],
                utc=True,
                errors="coerce",
            )
        )
    else:
        return pd.DatetimeIndex(
            []
        )

    if timestamps.tz is None:
        timestamps = (
            timestamps.tz_localize(
                "UTC"
            )
        )
    else:
        timestamps = (
            timestamps.tz_convert(
                "UTC"
            )
        )

    return timestamps


def timestamp_ns_values(
    timestamps: pd.DatetimeIndex,
) -> np.ndarray:
    """
    Return UTC timestamp values explicitly expressed
    as integer nanoseconds.

    DatetimeIndex.asi8 follows the index's current
    resolution in newer pandas versions, so it cannot
    be assumed to contain nanoseconds.
    """
    try:
        return (
            timestamps
            .as_unit("ns")
            .asi8
        )
    except (
        AttributeError,
        TypeError,
    ):
        return (
            timestamps
            .to_numpy(
                dtype="datetime64[ns]"
            )
            .astype(
                "int64",
                copy=False,
            )
        )


def minute_gap_diagnostics(
    timestamps: pd.DatetimeIndex,
) -> dict[str, Any]:
    if len(timestamps) < 2:
        return {
            "missing_minute_run_count": 0,
            "largest_missing_minute_run": 0,
            "session_or_weekend_gap_count": 0,
        }

    unique_sorted = (
        timestamps
        .drop_duplicates()
        .sort_values()
    )

    timestamp_values = (
        timestamp_ns_values(
            unique_sorted
        )
    )

    differences = (
        timestamp_values[1:]
        - timestamp_values[:-1]
    )

    minute_ns = 60_000_000_000

    missing_minutes = (
        differences // minute_ns
        - 1
    )

    positive = missing_minutes[
        missing_minutes > 0
    ]

    return {
        "missing_minute_run_count": int(
            len(positive)
        ),
        "largest_missing_minute_run": int(
            positive.max()
            if len(positive)
            else 0
        ),
        "session_or_weekend_gap_count": int(
            np.count_nonzero(
                differences
                >= 60 * minute_ns
            )
        ),
    }


def audit_dataframe(
    frame: pd.DataFrame,
    *,
    start: str,
    end_exclusive: str,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "nonempty_records": (
            len(frame) > 0
        ),
        "required_columns": all(
            column in frame.columns
            for column in REQUIRED_COLUMNS
        ),
        "single_instrument_id_per_file": False,
        "timestamps_inside_locked_window": False,
        "minute_timestamp_alignment": False,
        "monotonic_timestamp_order": False,
        "duplicate_timestamps": False,
        "duplicate_full_rows": False,
        "finite_ohlcv": False,
        "ohlc_invariants": False,
        "negative_volume": False,
        "nq_quarter_point_tick_alignment": False,
        "record_count": int(len(frame)),
        "first_observed_timestamp": None,
        "last_observed_timestamp": None,
        "instrument_id": None,
        "calendar_minute_density": 0.0,
        "duplicate_timestamp_count": 0,
        "duplicate_full_row_count": 0,
        "nonfinite_value_count": 0,
        "ohlc_invariant_failure_count": 0,
        "negative_volume_count": 0,
        "off_tick_value_count": 0,
        "missing_minute_run_count": 0,
        "largest_missing_minute_run": 0,
        "session_or_weekend_gap_count": 0,
    }

    if (
        not result["nonempty_records"]
        or not result["required_columns"]
    ):
        return result

    timestamps = extract_timestamps(
        frame
    )

    if len(timestamps) != len(frame):
        return result

    if timestamps.isna().any():
        return result

    start_timestamp = pd.Timestamp(
        start,
        tz="UTC",
    )

    end_timestamp = pd.Timestamp(
        end_exclusive,
        tz="UTC",
    )

    result[
        "first_observed_timestamp"
    ] = timestamps.min().isoformat()

    result[
        "last_observed_timestamp"
    ] = timestamps.max().isoformat()

    result[
        "timestamps_inside_locked_window"
    ] = bool(
        timestamps.min()
        >= start_timestamp
        and timestamps.max()
        < end_timestamp
    )

    minute_ns = 60_000_000_000

    timestamp_values = (
        timestamp_ns_values(
            timestamps
        )
    )

    result[
        "minute_timestamp_alignment"
    ] = bool(
        np.all(
            timestamp_values
            % minute_ns
            == 0
        )
    )

    result[
        "monotonic_timestamp_order"
    ] = bool(
        timestamps.is_monotonic_increasing
    )

    duplicate_timestamp_count = int(
        timestamps.duplicated().sum()
    )

    result[
        "duplicate_timestamp_count"
    ] = duplicate_timestamp_count

    result[
        "duplicate_timestamps"
    ] = (
        duplicate_timestamp_count == 0
    )

    duplicate_frame = frame.copy()

    duplicate_frame.insert(
        0,
        "__audit_ts_event",
        timestamps,
    )

    duplicate_full_row_count = int(
        duplicate_frame.duplicated().sum()
    )

    result[
        "duplicate_full_row_count"
    ] = duplicate_full_row_count

    result[
        "duplicate_full_rows"
    ] = (
        duplicate_full_row_count == 0
    )

    instrument_ids = (
        frame["instrument_id"]
        .dropna()
        .unique()
    )

    result[
        "single_instrument_id_per_file"
    ] = (
        len(instrument_ids) == 1
    )

    if len(instrument_ids) == 1:
        result["instrument_id"] = int(
            instrument_ids[0]
        )

    prices = frame[
        ["open", "high", "low", "close"]
    ].apply(
        pd.to_numeric,
        errors="coerce",
    )

    volume = pd.to_numeric(
        frame["volume"],
        errors="coerce",
    )

    price_values = prices.to_numpy(
        dtype=float
    )

    volume_values = volume.to_numpy(
        dtype=float
    )

    finite_mask = np.isfinite(
        price_values
    )

    finite_volume = np.isfinite(
        volume_values
    )

    nonfinite_count = int(
        np.size(finite_mask)
        - np.count_nonzero(
            finite_mask
        )
        + np.size(finite_volume)
        - np.count_nonzero(
            finite_volume
        )
    )

    result[
        "nonfinite_value_count"
    ] = nonfinite_count

    result[
        "finite_ohlcv"
    ] = (
        nonfinite_count == 0
    )

    high = prices["high"]
    low = prices["low"]
    open_price = prices["open"]
    close = prices["close"]

    invariant_failures = (
        (high < low)
        | (high < open_price)
        | (high < close)
        | (low > open_price)
        | (low > close)
    )

    invariant_failure_count = int(
        invariant_failures.fillna(
            True
        ).sum()
    )

    result[
        "ohlc_invariant_failure_count"
    ] = invariant_failure_count

    result[
        "ohlc_invariants"
    ] = (
        invariant_failure_count == 0
    )

    negative_volume_count = int(
        (volume < 0)
        .fillna(True)
        .sum()
    )

    result[
        "negative_volume_count"
    ] = negative_volume_count

    result[
        "negative_volume"
    ] = (
        negative_volume_count == 0
    )

    scaled_prices = (
        price_values * 4.0
    )

    tick_aligned = np.isclose(
        scaled_prices,
        np.rint(
            scaled_prices
        ),
        rtol=0.0,
        atol=1e-7,
        equal_nan=False,
    )

    off_tick_count = int(
        tick_aligned.size
        - np.count_nonzero(
            tick_aligned
        )
    )

    result[
        "off_tick_value_count"
    ] = off_tick_count

    result[
        "nq_quarter_point_tick_alignment"
    ] = (
        off_tick_count == 0
    )

    total_calendar_minutes = max(
        1,
        int(
            (
                end_timestamp
                - start_timestamp
            ).total_seconds()
            // 60
        ),
    )

    result[
        "calendar_minute_density"
    ] = (
        float(len(frame))
        / float(
            total_calendar_minutes
        )
    )

    result.update(
        minute_gap_diagnostics(
            timestamps
        )
    )

    return result


def load_store(
    path: Path,
) -> Any:
    import databento as db

    return db.DBNStore.from_file(
        path
    )


def repository_preflight() -> dict[str, Any]:
    validate_exp019_preregistration()
    validate_exp019_archive_audit_preregistration()

    if os.environ.get(
        "DATABENTO_API_KEY",
        "",
    ).strip():
        raise RuntimeError(
            "DATABENTO_API_KEY must not be set "
            "for the local archive audit."
        )

    status = run_git(
        "status",
        "--porcelain",
    ).stdout.strip()

    if status:
        raise RuntimeError(
            "Repository must be clean before "
            "running the EXP-019 archive audit."
        )

    branch = run_git(
        "branch",
        "--show-current",
    ).stdout.strip()

    if branch != "main":
        raise RuntimeError(
            "EXP-019 archive audit must run "
            f"on main, found {branch!r}."
        )

    head = run_git(
        "rev-parse",
        "HEAD",
    ).stdout.strip()

    origin_main = run_git(
        "rev-parse",
        "origin/main",
    ).stdout.strip()

    if head != origin_main:
        raise RuntimeError(
            "Local HEAD and origin/main are "
            "not aligned."
        )

    ancestor = run_git(
        "merge-base",
        "--is-ancestor",
        LOCKED_AUDIT_PREREGISTRATION_COMMIT,
        "HEAD",
        check=False,
    )

    if ancestor.returncode != 0:
        raise RuntimeError(
            "Locked EXP-019 audit preregistration "
            "commit is not an ancestor of HEAD."
        )

    protected_diff = run_git(
        "diff",
        "--quiet",
        LOCKED_AUDIT_PREREGISTRATION_COMMIT,
        "--",
        *LOCKED_PATHS,
        check=False,
    )

    if protected_diff.returncode != 0:
        raise RuntimeError(
            "Locked EXP-019 files changed after "
            "audit preregistration."
        )

    if (
        OUTPUT_DIR.exists()
        or PARTIAL_OUTPUT_DIR.exists()
    ):
        raise RuntimeError(
            "EXP-019 archive-audit output already "
            "exists. Refusing to rerun."
        )

    if not MANIFEST_PATH.is_file():
        raise RuntimeError(
            "Missing acquisition manifest."
        )

    if not COMPLETION_PATH.is_file():
        raise RuntimeError(
            "Missing acquisition completion marker."
        )

    if (
        sha256_file(
            MANIFEST_PATH
        )
        != EXPECTED_MANIFEST_SHA256
    ):
        raise RuntimeError(
            "Acquisition manifest hash changed."
        )

    if (
        sha256_file(
            COMPLETION_PATH
        )
        != EXPECTED_COMPLETION_SHA256
    ):
        raise RuntimeError(
            "Completion marker hash changed."
        )

    manifest = json.loads(
        MANIFEST_PATH.read_text(
            encoding="utf-8"
        )
    )

    completion = json.loads(
        COMPLETION_PATH.read_text(
            encoding="utf-8"
        )
    )

    if (
        manifest["experiment_id"]
        != "EXP-019"
        or manifest["status"]
        != "COMPLETE"
        or len(
            manifest["completed"]
        )
        != EXPECTED_FILE_COUNT
    ):
        raise RuntimeError(
            "Acquisition manifest completion "
            "state changed."
        )

    if (
        completion["classification"]
        != (
            "EXACT_CONTRACT_"
            "ACQUISITION_COMPLETE"
        )
        or completion[
            "archive_sha256"
        ]
        != EXPECTED_ARCHIVE_SHA256
        or completion[
            "archive_qualified"
        ]
        is not False
        or completion[
            "audit_required_before_use"
        ]
        is not True
    ):
        raise RuntimeError(
            "Acquisition completion boundary "
            "changed."
        )

    return {
        "branch": branch,
        "head": head,
        "origin_main": origin_main,
        "manifest": manifest,
        "completion": completion,
    }


def audit_contract(
    *,
    sequence: int,
    contract: tuple[
        str,
        str,
        str,
        str,
        str,
    ],
    manifest_entry: dict[str, Any],
) -> tuple[
    dict[str, Any],
    pd.DatetimeIndex,
]:
    (
        canonical_symbol,
        raw_symbol,
        start,
        end_exclusive,
        expiration,
    ) = contract

    file_path = (
        ARCHIVE_ROOT
        / manifest_entry[
            "relative_path"
        ]
    )

    row: dict[str, Any] = {
        "sequence": sequence,
        "canonical_symbol": (
            canonical_symbol
        ),
        "raw_symbol": raw_symbol,
        "start": start,
        "end_exclusive": (
            end_exclusive
        ),
        "expiration": expiration,
        "relative_path": (
            manifest_entry[
                "relative_path"
            ]
        ),
        "expected_size_bytes": int(
            manifest_entry[
                "size_bytes"
            ]
        ),
        "actual_size_bytes": (
            int(
                file_path.stat().st_size
            )
            if file_path.is_file()
            else 0
        ),
        "expected_sha256": (
            manifest_entry[
                "sha256"
            ]
        ),
        "actual_sha256": None,
        "archive_file_count": True,
        "manifest_file_size": False,
        "manifest_file_sha256": False,
        "dbn_readability": False,
        "ohlcv_1m_schema": False,
        "nonempty_records": False,
        "required_columns": False,
        "single_instrument_id_per_file": False,
        "timestamps_inside_locked_window": False,
        "minute_timestamp_alignment": False,
        "monotonic_timestamp_order": False,
        "duplicate_timestamps": False,
        "duplicate_full_rows": False,
        "finite_ohlcv": False,
        "ohlc_invariants": False,
        "negative_volume": False,
        "nq_quarter_point_tick_alignment": False,
        "dataset": None,
        "schema": None,
        "stype_in": None,
        "stype_out": None,
        "request_symbols": None,
        "error": None,
    }

    empty_timestamps = pd.DatetimeIndex(
        []
    )

    if not file_path.is_file():
        row["error"] = (
            "Raw DBN file is missing."
        )
        return row, empty_timestamps

    row["manifest_file_size"] = (
        file_path.stat().st_size
        == int(
            manifest_entry[
                "size_bytes"
            ]
        )
    )

    actual_hash = sha256_file(
        file_path
    )

    row["actual_sha256"] = (
        actual_hash
    )

    row["manifest_file_sha256"] = (
        actual_hash
        == manifest_entry["sha256"]
    )

    try:
        store = load_store(
            file_path
        )

        row["dbn_readability"] = True

        row["dataset"] = str(
            getattr(
                store,
                "dataset",
                "",
            )
        )

        row["schema"] = enum_text(
            getattr(
                store,
                "schema",
                "",
            )
        )

        row["stype_in"] = enum_text(
            getattr(
                store,
                "stype_in",
                "",
            )
        )

        row["stype_out"] = enum_text(
            getattr(
                store,
                "stype_out",
                "",
            )
        )

        symbols = getattr(
            store,
            "symbols",
            [],
        )

        row["request_symbols"] = (
            "|".join(
                str(symbol)
                for symbol in symbols
            )
        )

        row["ohlcv_1m_schema"] = bool(
            row["dataset"]
            == "GLBX.MDP3"
            and schema_is_ohlcv_1m(
                getattr(
                    store,
                    "schema",
                    "",
                )
            )
            and stype_matches(
                getattr(
                    store,
                    "stype_in",
                    "",
                ),
                "raw_symbol",
            )
            and stype_matches(
                getattr(
                    store,
                    "stype_out",
                    "",
                ),
                "instrument_id",
            )
        )

        frame = store.to_df()

        frame_result = audit_dataframe(
            frame,
            start=start,
            end_exclusive=(
                end_exclusive
            ),
        )

        row.update(
            frame_result
        )

        timestamps = extract_timestamps(
            frame
        )

        return row, timestamps

    except Exception as exc:
        row["error"] = (
            f"{type(exc).__name__}: "
            f"{str(exc)[:1000]}"
        )

        return row, empty_timestamps


def final_classification(
    hard_checks: dict[str, bool],
    *,
    warning_windows: int = (
        KNOWN_PROVIDER_WARNING_WINDOWS
    ),
) -> str:
    if not all(
        hard_checks.values()
    ):
        return "NOT_QUALIFIED"

    if warning_windows > 0:
        return (
            "QUALIFIED_WITH_KNOWN_"
            "PROVIDER_CONDITIONS"
        )

    return "QUALIFIED"


def write_csv(
    path: Path,
    rows: list[dict[str, Any]],
) -> None:
    if not rows:
        path.write_text(
            "",
            encoding="utf-8",
        )
        return

    fieldnames = list(
        rows[0]
    )

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )

        writer.writeheader()
        writer.writerows(
            rows
        )


def build_report(
    summary: dict[str, Any],
) -> str:
    lines = [
        "# EXP-019 Local Archive Audit",
        "",
        (
            f"**Classification:** "
            f"`{summary['classification']}`"
        ),
        "",
        "## Scope",
        "",
        "- Local files only",
        "- Databento API calls: 0",
        "- Credentials used: No",
        "- Archive files modified: No",
        "- Continuous series constructed: No",
        "- Strategy run: No",
        "",
        "## Archive totals",
        "",
        (
            f"- Contracts audited: "
            f"{summary['contract_count']}"
        ),
        (
            f"- Records audited: "
            f"{summary['total_record_count']:,}"
        ),
        (
            f"- Compressed bytes: "
            f"{summary['compressed_total_bytes']:,}"
        ),
        (
            f"- Known provider-warning windows: "
            f"{summary['known_provider_warning_windows']}"
        ),
        "",
        "## Hard checks",
        "",
        "| Check | Passed |",
        "|---|---:|",
    ]

    for name, passed in (
        summary["hard_checks"].items()
    ):
        lines.append(
            f"| {name} | {passed} |"
        )

    lines.extend(
        [
            "",
            "## Diagnostics",
            "",
            (
                f"- Missing-minute runs: "
                f"{summary['diagnostics']['missing_minute_run_count']:,}"
            ),
            (
                f"- Largest missing-minute run: "
                f"{summary['diagnostics']['largest_missing_minute_run']:,}"
            ),
            (
                f"- Adjacent contract pairs measured: "
                f"{summary['diagnostics']['adjacent_pairs_measured']}"
            ),
            (
                f"- Total overlapping timestamps: "
                f"{summary['diagnostics']['total_overlap_minutes']:,}"
            ),
            "",
            "## Interpretation",
            "",
            (
                "Known provider-condition warnings remain "
                "part of the evidence."
            ),
            (
                "Minute gaps are diagnostic because an OHLCV "
                "bar is absent when no trade occurs."
            ),
            (
                "This audit does not establish exchange accuracy, "
                "best-vendor status, a roll rule or permission "
                "to run strategies."
            ),
            "",
        ]
    )

    return "\n".join(
        lines
    )


def run_audit() -> dict[str, Any]:
    preflight = repository_preflight()

    manifest = preflight[
        "manifest"
    ]

    completed_by_symbol = {
        entry["canonical_symbol"]: entry
        for entry in manifest[
            "completed"
        ]
    }

    raw_files = sorted(
        RAW_DIR.glob(
            "*.dbn.zst"
        )
    )

    archive_count_pass = (
        len(raw_files)
        == EXPECTED_FILE_COUNT
        and len(
            completed_by_symbol
        )
        == EXPECTED_FILE_COUNT
    )

    actual_total_bytes = sum(
        path.stat().st_size
        for path in raw_files
    )

    manifest_archive_digest = (
        archive_digest(
            manifest[
                "completed"
            ]
        )
    )

    contract_rows: list[
        dict[str, Any]
    ] = []

    overlap_rows: list[
        dict[str, Any]
    ] = []

    previous_symbol: str | None = None
    previous_timestamps = (
        pd.DatetimeIndex([])
    )

    for sequence, contract in enumerate(
        CONTRACT_PLAN,
        start=1,
    ):
        canonical_symbol = contract[0]

        print(
            f"[{sequence:02d}/"
            f"{EXPECTED_FILE_COUNT}] "
            f"Auditing {canonical_symbol}"
        )

        manifest_entry = (
            completed_by_symbol.get(
                canonical_symbol
            )
        )

        if manifest_entry is None:
            missing_row = {
                "sequence": sequence,
                "canonical_symbol": (
                    canonical_symbol
                ),
                "raw_symbol": contract[1],
                "start": contract[2],
                "end_exclusive": contract[3],
                "expiration": contract[4],
                "archive_file_count": False,
                "manifest_file_size": False,
                "manifest_file_sha256": False,
                "dbn_readability": False,
                "ohlcv_1m_schema": False,
                "nonempty_records": False,
                "required_columns": False,
                "single_instrument_id_per_file": False,
                "timestamps_inside_locked_window": False,
                "minute_timestamp_alignment": False,
                "monotonic_timestamp_order": False,
                "duplicate_timestamps": False,
                "duplicate_full_rows": False,
                "finite_ohlcv": False,
                "ohlc_invariants": False,
                "negative_volume": False,
                "nq_quarter_point_tick_alignment": False,
                "record_count": 0,
                "error": (
                    "Missing manifest entry."
                ),
            }

            contract_rows.append(
                missing_row
            )
            previous_symbol = canonical_symbol
            previous_timestamps = (
                pd.DatetimeIndex([])
            )
            continue

        row, timestamps = audit_contract(
            sequence=sequence,
            contract=contract,
            manifest_entry=(
                manifest_entry
            ),
        )

        row["archive_file_count"] = (
            archive_count_pass
        )

        contract_rows.append(
            row
        )

        if previous_symbol is not None:
            overlap = (
                previous_timestamps
                .intersection(
                    timestamps
                )
            )

            overlap_rows.append(
                {
                    "previous_contract": (
                        previous_symbol
                    ),
                    "current_contract": (
                        canonical_symbol
                    ),
                    "overlap_minute_count": int(
                        len(overlap)
                    ),
                    "first_overlap_timestamp": (
                        overlap.min().isoformat()
                        if len(overlap)
                        else None
                    ),
                    "last_overlap_timestamp": (
                        overlap.max().isoformat()
                        if len(overlap)
                        else None
                    ),
                }
            )

        previous_symbol = (
            canonical_symbol
        )

        previous_timestamps = (
            timestamps
            .drop_duplicates()
            .sort_values()
        )

    hard_checks: dict[
        str,
        bool,
    ] = {}

    for check_name in HARD_CHECK_NAMES:
        hard_checks[check_name] = bool(
            contract_rows
            and all(
                bool(
                    row.get(
                        check_name,
                        False,
                    )
                )
                for row in contract_rows
            )
        )

    hard_checks[
        "archive_file_count"
    ] = bool(
        archive_count_pass
        and actual_total_bytes
        == EXPECTED_TOTAL_BYTES
        and manifest_archive_digest
        == EXPECTED_ARCHIVE_SHA256
    )

    classification = (
        final_classification(
            hard_checks
        )
    )

    total_record_count = sum(
        int(
            row.get(
                "record_count",
                0,
            )
        )
        for row in contract_rows
    )

    missing_run_count = sum(
        int(
            row.get(
                "missing_minute_run_count",
                0,
            )
        )
        for row in contract_rows
    )

    largest_missing_run = max(
        (
            int(
                row.get(
                    "largest_missing_minute_run",
                    0,
                )
            )
            for row in contract_rows
        ),
        default=0,
    )

    total_overlap_minutes = sum(
        int(
            row[
                "overlap_minute_count"
            ]
        )
        for row in overlap_rows
    )

    summary = {
        "schema_version": 1,
        "experiment_id": "EXP-019",
        "classification": classification,
        "generated_at_utc": utc_now(),
        "audit_preregistration_commit": (
            LOCKED_AUDIT_PREREGISTRATION_COMMIT
        ),
        "execution_commit": (
            preflight["head"]
        ),
        "contract_count": len(
            contract_rows
        ),
        "total_record_count": (
            total_record_count
        ),
        "compressed_total_bytes": (
            actual_total_bytes
        ),
        "manifest_sha256": (
            sha256_file(
                MANIFEST_PATH
            )
        ),
        "completion_marker_sha256": (
            sha256_file(
                COMPLETION_PATH
            )
        ),
        "archive_sha256": (
            manifest_archive_digest
        ),
        "known_provider_warning_windows": (
            KNOWN_PROVIDER_WARNING_WINDOWS
        ),
        "hard_checks": hard_checks,
        "hard_failure_count": sum(
            not passed
            for passed in hard_checks.values()
        ),
        "diagnostics": {
            "missing_minute_run_count": (
                missing_run_count
            ),
            "largest_missing_minute_run": (
                largest_missing_run
            ),
            "adjacent_pairs_measured": len(
                overlap_rows
            ),
            "total_overlap_minutes": (
                total_overlap_minutes
            ),
        },
        "boundaries": {
            "databento_api_calls": 0,
            "credentials_used": False,
            "archive_files_modified": False,
            "continuous_series_constructed": False,
            "strategy_run": False,
            "exchange_accuracy_claim": False,
            "best_vendor_claim": False,
            "strategy_use_authorized": False,
        },
        "outputs": {
            "contracts_csv": (
                CONTRACTS_PATH.name
            ),
            "overlaps_csv": (
                OVERLAPS_PATH.name
            ),
            "report": REPORT_PATH.name,
        },
    }

    PARTIAL_OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=False,
    )

    partial_contracts = (
        PARTIAL_OUTPUT_DIR
        / CONTRACTS_PATH.name
    )

    partial_overlaps = (
        PARTIAL_OUTPUT_DIR
        / OVERLAPS_PATH.name
    )

    partial_summary = (
        PARTIAL_OUTPUT_DIR
        / SUMMARY_PATH.name
    )

    partial_report = (
        PARTIAL_OUTPUT_DIR
        / REPORT_PATH.name
    )

    partial_completion = (
        PARTIAL_OUTPUT_DIR
        / COMPLETION_OUTPUT_PATH.name
    )

    write_csv(
        partial_contracts,
        contract_rows,
    )

    write_csv(
        partial_overlaps,
        overlap_rows,
    )

    partial_summary.write_text(
        json.dumps(
            summary,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    partial_report.write_text(
        build_report(
            summary
        ),
        encoding="utf-8",
        newline="\n",
    )

    completion_output = {
        "experiment_id": "EXP-019",
        "classification": (
            classification
        ),
        "completed_at_utc": utc_now(),
        "contract_count": len(
            contract_rows
        ),
        "hard_failure_count": (
            summary[
                "hard_failure_count"
            ]
        ),
        "known_provider_warning_windows": (
            KNOWN_PROVIDER_WARNING_WINDOWS
        ),
        "databento_api_calls": 0,
        "archive_files_modified": False,
        "continuous_series_constructed": False,
        "strategy_run": False,
        "strategy_use_authorized": False,
    }

    partial_completion.write_text(
        json.dumps(
            completion_output,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    os.replace(
        PARTIAL_OUTPUT_DIR,
        OUTPUT_DIR,
    )

    return summary


def print_preflight(
    preflight: dict[str, Any],
) -> None:
    print(
        "EXP-019 ARCHIVE AUDIT PREFLIGHT"
    )
    print(
        "==============================="
    )
    print(
        f"Branch:                 "
        f"{preflight['branch']}"
    )
    print(
        f"HEAD:                   "
        f"{preflight['head']}"
    )
    print(
        "Locked raw files:       66"
    )
    print(
        "Locked compressed bytes:"
        "104491346"
    )
    print(
        "Databento API calls:    0"
    )
    print(
        "Credentials required:   False"
    )
    print(
        "Archive modifications:  False"
    )
    print(
        "Continuous construction:False"
    )
    print(
        "Strategy run:           False"
    )
    print(
        "Existing audit output:  False"
    )
    print(
        "==============================="
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Protected read-only EXP-019 "
            "exact-contract archive audit."
        )
    )

    mode = (
        parser.add_mutually_exclusive_group(
            required=True
        )
    )

    mode.add_argument(
        "--preflight",
        action="store_true",
    )

    mode.add_argument(
        "--audit-local",
        action="store_true",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.preflight:
        print_preflight(
            repository_preflight()
        )
        return 0

    summary = run_audit()

    print()
    print(
        "EXP-019 LOCAL ARCHIVE AUDIT"
    )
    print(
        "==========================="
    )
    print(
        "Classification:          "
        f"{summary['classification']}"
    )
    print(
        "Contracts audited:       "
        f"{summary['contract_count']}"
    )
    print(
        "Records audited:         "
        f"{summary['total_record_count']:,}"
    )
    print(
        "Hard failures:           "
        f"{summary['hard_failure_count']}"
    )
    print(
        "Known warning windows:   "
        f"{summary['known_provider_warning_windows']}"
    )
    print(
        "Missing-minute runs:     "
        f"{summary['diagnostics']['missing_minute_run_count']:,}"
    )
    print(
        "Largest missing run:     "
        f"{summary['diagnostics']['largest_missing_minute_run']:,}"
    )
    print(
        "Adjacent pairs measured: "
        f"{summary['diagnostics']['adjacent_pairs_measured']}"
    )
    print(
        "Overlap minutes:         "
        f"{summary['diagnostics']['total_overlap_minutes']:,}"
    )
    print(
        "Databento API calls:     0"
    )
    print(
        "Continuous constructed:  False"
    )
    print(
        "Strategy run:            False"
    )
    print(
        f"Report:                  "
        f"{REPORT_PATH}"
    )
    print(
        f"Summary:                 "
        f"{SUMMARY_PATH}"
    )
    print(
        "==========================="
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
