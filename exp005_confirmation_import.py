from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict
from datetime import date
import hashlib
from pathlib import Path
from typing import Any, Iterable, Iterator

import pandas as pd

import exp005_quantower_import as base
from exp005_quick_transfer_result import (
    EXPECTED_FILE_SHA256 as QUICK_RESULT_SHA256,
    verify_local_quick_transfer_decision,
)


PROJECT_DIR = Path(__file__).resolve().parent
CONFIRMATION_START = date(2023, 1, 3)
CONFIRMATION_END = date(2025, 12, 31)
CONFIRMATION_ROOT = (
    PROJECT_DIR
    / "data"
    / "EXP-005"
    / "confirmation"
)
INCOMING_ROOT = CONFIRMATION_ROOT / "incoming"
RAW_ROOT = CONFIRMATION_ROOT / "raw"
PROCESSED_ROOT = CONFIRMATION_ROOT / "processed"
RESULTS_ROOT = (
    PROJECT_DIR
    / "results"
    / "EXP-005"
    / "confirmation_data"
)
CALENDAR_FILE = (
    PROJECT_DIR
    / "research"
    / "EXP-005_confirmation_full_sessions.csv"
)
CALENDAR_SHA256 = "3ca50dfd41e9e069c4a848ca63845ebc9a308a19245da85fe669808c831867b2"
EXPECTED_FULL_SESSIONS = 744
EXPECTED_ONE_MINUTE_ROWS_PER_SYMBOL = (
    EXPECTED_FULL_SESSIONS
    * base.EXPECTED_ONE_MINUTE_BARS
)
EXPECTED_FIVE_MINUTE_ROWS_PER_SYMBOL = (
    EXPECTED_FULL_SESSIONS
    * base.EXPECTED_FIVE_MINUTE_BARS
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with Path(path).open("rb") as handle:
        for block in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def load_confirmation_calendar(
    path: Path = CALENDAR_FILE,
) -> tuple[date, ...]:
    calendar_path = Path(path)

    if not calendar_path.exists():
        raise FileNotFoundError(
            f"Frozen confirmation calendar is missing: "
            f"{calendar_path}"
        )

    if sha256_file(calendar_path) != CALENDAR_SHA256:
        raise ValueError(
            "Frozen EXP-005 confirmation calendar hash changed."
        )

    frame = pd.read_csv(
        calendar_path
    )

    required = {
        "session_date",
        "market_open_utc",
        "market_close_utc",
        "expected_cash_minutes",
        "expected_five_minute_bars",
    }

    missing = required.difference(
        frame.columns
    )

    if missing:
        raise ValueError(
            "Confirmation calendar is missing columns: "
            f"{sorted(missing)}"
        )

    parsed = pd.to_datetime(
        frame["session_date"],
        errors="raise",
    ).dt.date

    if len(frame) != EXPECTED_FULL_SESSIONS:
        raise ValueError(
            "Confirmation calendar session count changed."
        )

    if parsed.duplicated().any():
        raise ValueError(
            "Confirmation calendar contains duplicate dates."
        )

    if not frame[
        "expected_cash_minutes"
    ].eq(
        base.EXPECTED_ONE_MINUTE_BARS
    ).all():
        raise ValueError(
            "Confirmation calendar contains a non-full session."
        )

    if not frame[
        "expected_five_minute_bars"
    ].eq(
        base.EXPECTED_FIVE_MINUTE_BARS
    ).all():
        raise ValueError(
            "Confirmation calendar five-minute counts changed."
        )

    sessions = tuple(
        sorted(parsed)
    )

    if (
        sessions[0] != CONFIRMATION_START
        or sessions[-1] != CONFIRMATION_END
    ):
        raise ValueError(
            "Confirmation calendar boundaries changed."
        )

    return sessions


def _confirmation_cash_only(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    local = frame.copy()
    local.index = local.index.tz_convert(
        base.NEW_YORK_TZ
    )

    times = local.index.time

    mask = (
        (times >= base.SESSION_START)
        & (times < base.SESSION_END)
    )

    cash = local.loc[mask].copy()
    cash["session_date"] = [
        item.date()
        for item in cash.index
    ]

    unauthorized = sorted(
        {
            item
            for item in cash["session_date"]
            if (
                item < CONFIRMATION_START
                or item > CONFIRMATION_END
            )
        }
    )

    if unauthorized:
        raise base.ProtectedPeriodError(
            "Quantower CSV contains cash-session rows outside "
            "the unlocked EXP-005 confirmation period. "
            f"First detected: {unauthorized[0]}."
        )

    return cash


@contextmanager
def confirmation_period_context(
) -> Iterator[None]:
    old_start = base.QUICK_START
    old_end = base.QUICK_END
    old_cash_only = base._cash_only

    base.QUICK_START = CONFIRMATION_START
    base.QUICK_END = CONFIRMATION_END
    base._cash_only = _confirmation_cash_only

    try:
        yield
    finally:
        base.QUICK_START = old_start
        base.QUICK_END = old_end
        base._cash_only = old_cash_only


def _combine_exclusions(
    frames: Iterable[pd.DataFrame],
) -> pd.DataFrame:
    populated = [
        frame
        for frame in frames
        if not frame.empty
    ]

    if not populated:
        return pd.DataFrame(
            columns=[
                "symbol",
                "session_date",
                "reason",
            ]
        )

    return pd.concat(
        populated,
        axis=0,
        ignore_index=True,
        sort=False,
    )


def build_confirmation_dataset(
    *,
    nq_paths: Iterable[Path],
    mnq_paths: Iterable[Path],
    archive_files: bool = True,
) -> base.ProcessedDataset:
    verify_local_quick_transfer_decision()
    expected_sessions = (
        load_confirmation_calendar()
    )

    with confirmation_period_context():
        nq_import = base.load_symbol_chunks(
            nq_paths,
            symbol="NQ",
        )
        mnq_import = base.load_symbol_chunks(
            mnq_paths,
            symbol="MNQ",
        )

        nq = base.extract_complete_sessions(
            nq_import,
            expected_sessions=expected_sessions,
        )
        mnq = base.extract_complete_sessions(
            mnq_import,
            expected_sessions=expected_sessions,
        )

        missing_expected = (
            base._strict_missing_session_rows(
                expected_sessions,
                nq,
                mnq,
            )
        )

        if not missing_expected.empty:
            preview = ", ".join(
                missing_expected[
                    "session_date"
                ].head(10)
            )

            raise base.IncompleteExportError(
                "The full EXP-005 confirmation export is "
                f"incomplete. {len(missing_expected)} expected "
                "full sessions are missing from NQ, MNQ or both. "
                f"First: {preview}.",
                missing_sessions=missing_expected,
            )

        aligned = base.align_nq_mnq(
            nq,
            mnq,
        )

        nq_5m = base.aggregate_to_five_minutes(
            aligned.nq_1m
        )
        mnq_5m = base.aggregate_to_five_minutes(
            aligned.mnq_1m
        )

        base.validate_processed_one_minute(
            aligned.nq_1m,
            symbol="NQ",
        )
        base.validate_processed_one_minute(
            aligned.mnq_1m,
            symbol="MNQ",
        )
        base.validate_processed_five_minute(
            nq_5m,
            symbol="NQ",
        )
        base.validate_processed_five_minute(
            mnq_5m,
            symbol="MNQ",
        )

    if not aligned.nq_1m.index.equals(
        aligned.mnq_1m.index
    ):
        raise base.AlignmentError(
            "Final confirmation NQ/MNQ one-minute "
            "timestamps differ."
        )

    if not nq_5m.index.equals(
        mnq_5m.index
    ):
        raise base.AlignmentError(
            "Final confirmation NQ/MNQ five-minute "
            "timestamps differ."
        )

    original_records = (
        *nq_import.files,
        *mnq_import.files,
    )

    manifest = (
        base.archive_raw_files(
            original_records,
            raw_root=RAW_ROOT,
        )
        if archive_files
        else tuple(original_records)
    )

    excluded = _combine_exclusions(
        (
            nq.incomplete_sessions,
            mnq.incomplete_sessions,
            nq.unexpected_sessions,
            mnq.unexpected_sessions,
            aligned.excluded_mismatch_sessions,
        )
    )

    included_sessions = int(
        aligned.nq_1m[
            "session_date"
        ].nunique()
    )

    mismatch_excluded = int(
        len(
            aligned.excluded_mismatch_sessions
        )
    )

    unexpected_dates = sorted(
        set(
            nq.unexpected_sessions.get(
                "session_date",
                pd.Series(dtype=str),
            ).astype(str)
        ).union(
            set(
                mnq.unexpected_sessions.get(
                    "session_date",
                    pd.Series(dtype=str),
                ).astype(str)
            )
        )
    )

    audit = {
        "experiment_id": "EXP-005",
        "research_stage": (
            "FULL_VALIDATION_CONFIRMATION_DATA"
        ),
        "source": (
            "Lucid Trading / Rithmic via Quantower "
            "History Exporter"
        ),
        "symbols": ["NQ", "MNQ"],
        "input_timeframe": "1 minute",
        "output_timeframe": "5 minutes",
        "source_timezone": base.SOURCE_TZ,
        "research_timezone": base.NEW_YORK_TZ,
        "confirmation_start": (
            CONFIRMATION_START.isoformat()
        ),
        "confirmation_end": (
            CONFIRMATION_END.isoformat()
        ),
        "confirmation_period_requested": True,
        "quick_transfer_result_sha256": (
            QUICK_RESULT_SHA256
        ),
        "expected_full_sessions": int(
            len(expected_sessions)
        ),
        "included_sessions": included_sessions,
        "included_nq_one_minute_rows": int(
            len(aligned.nq_1m)
        ),
        "included_mnq_one_minute_rows": int(
            len(aligned.mnq_1m)
        ),
        "included_nq_five_minute_rows": int(
            len(nq_5m)
        ),
        "included_mnq_five_minute_rows": int(
            len(mnq_5m)
        ),
        "nq_source_files": len(
            nq_import.files
        ),
        "mnq_source_files": len(
            mnq_import.files
        ),
        "nq_overlap_rows_deduplicated": int(
            nq_import.duplicate_overlap_rows_removed
        ),
        "mnq_overlap_rows_deduplicated": int(
            mnq_import.duplicate_overlap_rows_removed
        ),
        "nq_within_file_rows_deduplicated": int(
            sum(
                item.duplicate_rows_removed
                for item in nq_import.files
            )
        ),
        "mnq_within_file_rows_deduplicated": int(
            sum(
                item.duplicate_rows_removed
                for item in mnq_import.files
            )
        ),
        "nq_research_volume_only_conflicts_resolved": int(
            sum(
                item.research_volume_only_conflicts_resolved
                for item in nq_import.files
            )
        ),
        "mnq_research_volume_only_conflicts_resolved": int(
            sum(
                item.research_volume_only_conflicts_resolved
                for item in mnq_import.files
            )
        ),
        "potential_front_month_mismatch_sessions_excluded": (
            mismatch_excluded
        ),
        "unexpected_or_early_close_session_dates": (
            unexpected_dates
        ),
        "included_invalid_sessions": 0,
        "included_front_month_mismatch_sessions": 0,
        "bars_synthesized": 0,
        "strategy_results_calculated": False,
        "full_validation_results_calculated": False,
        "quick_transfer_rerun": False,
    }

    return base.ProcessedDataset(
        nq_1m=aligned.nq_1m,
        mnq_1m=aligned.mnq_1m,
        nq_5m=nq_5m,
        mnq_5m=mnq_5m,
        manifest=manifest,
        audit=audit,
        excluded_sessions=excluded,
    )
