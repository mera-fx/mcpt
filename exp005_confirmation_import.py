from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict
from datetime import date
import hashlib
from pathlib import Path
from typing import Any, Iterable, Iterator

import numpy as np
import pandas as pd

import exp005_quantower_import as base
from exp005_confirmation_recheck_resolution import (
    get_exp005_confirmation_recheck_resolution,
    validate_exp005_confirmation_recheck_resolution,
)
from exp005_confirmation_missing_session_resolution import (
    load_confirmation_session_retry_evidence,
    restore_locked_confirmation_session,
    validate_locked_confirmation_missing_sessions,
)
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
RECHECK_ROOT = CONFIRMATION_ROOT / "recheck"
SESSION_RETRY_ROOT = (
    CONFIRMATION_ROOT
    / "session_retry"
)
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
EXPECTED_INCLUDED_SESSIONS = 742
EXPECTED_ONE_MINUTE_ROWS_PER_SYMBOL = (
    EXPECTED_INCLUDED_SESSIONS
    * base.EXPECTED_ONE_MINUTE_BARS
)
EXPECTED_FIVE_MINUTE_ROWS_PER_SYMBOL = (
    EXPECTED_INCLUDED_SESSIONS
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



def load_confirmation_recheck_corrections(
    paths: Iterable[Path],
    *,
    symbol: str,
) -> tuple[
    pd.DataFrame,
    tuple[base.RawFileRecord, ...],
]:
    validate_exp005_confirmation_recheck_resolution()
    normalized_symbol = symbol.strip().upper()

    if normalized_symbol not in {"NQ", "MNQ"}:
        raise base.QuantowerImportError(
            "Confirmation rechecks accept only NQ or MNQ."
        )

    record = (
        get_exp005_confirmation_recheck_resolution()
    )
    expected = record[
        "recheck_files"
    ][normalized_symbol]

    path_list = sorted(
        {
            Path(path).resolve()
            for path in paths
        },
        key=lambda item: str(item).lower(),
    )

    if len(path_list) != len(expected):
        raise base.QuantowerImportError(
            f"{normalized_symbol} requires exactly "
            f"{len(expected)} locked confirmation "
            "recheck CSV file."
        )

    expected_hashes = {
        item["sha256"]: item
        for item in expected.values()
    }
    seen_hashes: set[str] = set()
    rows: list[pd.DataFrame] = []
    records: list[
        base.RawFileRecord
    ] = []

    for path in path_list:
        digest = base.sha256_file(
            path
        )

        if digest not in expected_hashes:
            raise base.QuantowerImportError(
                f"Unexpected {normalized_symbol} confirmation "
                f"recheck file hash: {path.name}."
            )

        if digest in seen_hashes:
            raise base.QuantowerImportError(
                f"Duplicate {normalized_symbol} confirmation "
                "recheck file."
            )

        frame, file_record = base.read_quantower_csv(
            path,
            symbol=normalized_symbol,
            source_role=(
                "CONFIRMATION_RECHECK_CORRECTION"
            ),
        )
        specification = expected_hashes[
            digest
        ]

        if frame.index.has_duplicates:
            raise base.QuantowerImportError(
                f"{path.name} contains confirmation "
                "recheck duplicates."
            )

        if len(frame) != specification[
            "raw_rows"
        ]:
            raise base.QuantowerImportError(
                f"{path.name} confirmation recheck row "
                "count changed."
            )

        if frame.index.nunique() != specification[
            "unique_timestamps"
        ]:
            raise base.QuantowerImportError(
                f"{path.name} confirmation recheck unique "
                "timestamp count changed."
            )

        if (
            frame.index[0].isoformat()
            != specification["first_timestamp_utc"]
            or frame.index[-1].isoformat()
            != specification["last_timestamp_utc"]
        ):
            raise base.QuantowerImportError(
                f"{path.name} confirmation recheck "
                "boundaries changed."
            )

        expected_full_index = pd.date_range(
            start=pd.Timestamp(
                specification["first_timestamp_utc"]
            ),
            end=pd.Timestamp(
                specification["last_timestamp_utc"]
            ),
            freq="1min",
        )
        missing = expected_full_index.difference(
            frame.index
        )
        expected_missing = pd.date_range(
            start=pd.Timestamp(
                specification[
                    "expected_missing_start_utc"
                ]
            ),
            end=pd.Timestamp(
                specification[
                    "expected_missing_end_utc"
                ]
            ),
            freq="1min",
        )

        if (
            len(missing)
            != specification[
                "expected_missing_minutes"
            ]
            or not missing.equals(
                expected_missing
            )
        ):
            raise base.QuantowerImportError(
                f"{path.name} confirmation recheck missing "
                "minute profile changed."
            )

        timestamp = pd.Timestamp(
            specification["timestamp_utc"]
        )
        expected_bar = specification[
            "bar"
        ]

        if timestamp not in frame.index:
            raise base.QuantowerImportError(
                f"{path.name} is missing its locked "
                f"confirmation correction timestamp "
                f"{timestamp}."
            )

        actual = frame.loc[
            [timestamp],
            [
                "open",
                "high",
                "low",
                "close",
                "volume",
            ],
        ].astype(float)
        expected_values = np.array(
            [
                expected_bar["open"],
                expected_bar["high"],
                expected_bar["low"],
                expected_bar["close"],
                expected_bar["volume"],
            ],
            dtype=float,
        )

        if not np.allclose(
            actual.to_numpy()[0],
            expected_values,
            atol=1e-12,
            rtol=0.0,
        ):
            raise base.QuantowerImportError(
                f"{path.name} confirmation correction "
                "bar changed."
            )

        rows.append(actual)
        records.append(file_record)
        seen_hashes.add(digest)

    if seen_hashes != set(
        expected_hashes
    ):
        raise base.QuantowerImportError(
            f"{normalized_symbol} confirmation recheck "
            "set is incomplete."
        )

    corrections = pd.concat(
        rows,
        axis=0,
    ).sort_index()

    if corrections.index.has_duplicates:
        raise base.QuantowerImportError(
            f"{normalized_symbol} confirmation correction "
            "timestamps are duplicated."
        )

    return corrections, tuple(records)

def _without_session_dates(
    frame: pd.DataFrame,
    session_dates: set[str],
) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()

    if "session_date" not in frame.columns:
        return frame.copy()

    return frame.loc[
        ~frame[
            "session_date"
        ].astype(str).isin(
            session_dates
        )
    ].copy()


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
    nq_recheck_paths: Iterable[Path],
    mnq_recheck_paths: Iterable[Path],
    nq_session_retry_paths: Iterable[Path],
    mnq_session_retry_paths: Iterable[Path],
    archive_files: bool = True,
) -> base.ProcessedDataset:
    verify_local_quick_transfer_decision()
    expected_sessions = (
        load_confirmation_calendar()
    )

    with confirmation_period_context():
        (
            nq_corrections,
            nq_recheck_records,
        ) = load_confirmation_recheck_corrections(
            nq_recheck_paths,
            symbol="NQ",
        )
        (
            mnq_corrections,
            mnq_recheck_records,
        ) = load_confirmation_recheck_corrections(
            mnq_recheck_paths,
            symbol="MNQ",
        )

        nq_session_retry = (
            load_confirmation_session_retry_evidence(
                nq_session_retry_paths,
                symbol="NQ",
            )
        )
        mnq_session_retry = (
            load_confirmation_session_retry_evidence(
                mnq_session_retry_paths,
                symbol="MNQ",
            )
        )

        nq_import = base.load_symbol_chunks(
            nq_paths,
            symbol="NQ",
            corrections=nq_corrections,
        )
        mnq_import = base.load_symbol_chunks(
            mnq_paths,
            symbol="MNQ",
            corrections=mnq_corrections,
        )

        (
            nq_import,
            nq_restored_original_bars,
        ) = restore_locked_confirmation_session(
            nq_import,
            nq_session_retry,
        )
        (
            mnq_import,
            mnq_restored_original_bars,
        ) = restore_locked_confirmation_session(
            mnq_import,
            mnq_session_retry,
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

        locked_missing_exclusions = (
            validate_locked_confirmation_missing_sessions(
                missing_expected=missing_expected,
            )
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


    expected_duplicate_profile = {
        "NQ": {
            "within_file_rows_removed": 100,
            "non_research_conflicting_rows_removed": 73,
            "research_volume_only_conflicts_resolved": 26,
            "research_ohlc_conflicts_resolved_by_recheck": 1,
        },
        "MNQ": {
            "within_file_rows_removed": 100,
            "non_research_conflicting_rows_removed": 73,
            "research_volume_only_conflicts_resolved": 26,
            "research_ohlc_conflicts_resolved_by_recheck": 1,
        },
    }

    for symbol, imported in (
        ("NQ", nq_import),
        ("MNQ", mnq_import),
    ):
        observed = {
            "within_file_rows_removed": int(
                sum(
                    item.duplicate_rows_removed
                    for item in imported.files
                )
            ),
            "non_research_conflicting_rows_removed": int(
                sum(
                    item.non_research_conflicting_duplicate_rows_removed
                    for item in imported.files
                )
            ),
            "research_volume_only_conflicts_resolved": int(
                sum(
                    item.research_volume_only_conflicts_resolved
                    for item in imported.files
                )
            ),
            "research_ohlc_conflicts_resolved_by_recheck": int(
                sum(
                    item.research_ohlc_conflicts_resolved_by_recheck
                    for item in imported.files
                )
            ),
        }

        if observed != expected_duplicate_profile[
            symbol
        ]:
            raise base.QuantowerImportError(
                f"{symbol} confirmation duplicate profile "
                f"changed. Observed: {observed}."
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
        *nq_recheck_records,
        *mnq_recheck_records,
        *nq_session_retry.records,
        *mnq_session_retry.records,
    )

    manifest = (
        base.archive_raw_files(
            original_records,
            raw_root=RAW_ROOT,
        )
        if archive_files
        else tuple(original_records)
    )

    locked_missing_dates = {
        "2025-09-24",
        "2025-11-07",
    }

    excluded = _combine_exclusions(
        (
            _without_session_dates(
                nq.incomplete_sessions,
                locked_missing_dates,
            ),
            _without_session_dates(
                mnq.incomplete_sessions,
                locked_missing_dates,
            ),
            locked_missing_exclusions,
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

    if included_sessions != EXPECTED_INCLUDED_SESSIONS:
        raise base.IncompleteExportError(
            "EXP-005 confirmation included-session count "
            f"changed: {included_sessions}."
        )

    if (
        len(aligned.nq_1m)
        != EXPECTED_ONE_MINUTE_ROWS_PER_SYMBOL
        or len(aligned.mnq_1m)
        != EXPECTED_ONE_MINUTE_ROWS_PER_SYMBOL
        or len(nq_5m)
        != EXPECTED_FIVE_MINUTE_ROWS_PER_SYMBOL
        or len(mnq_5m)
        != EXPECTED_FIVE_MINUTE_ROWS_PER_SYMBOL
    ):
        raise base.IncompleteExportError(
            "EXP-005 confirmation processed row counts changed."
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
        "nq_confirmation_recheck_files": len(
            nq_recheck_records
        ),
        "mnq_confirmation_recheck_files": len(
            mnq_recheck_records
        ),
        "confirmation_recheck_record_id": (
            "EXP-005-DQ3"
        ),
        "nq_confirmation_session_retry_files": len(
            nq_session_retry.records
        ),
        "mnq_confirmation_session_retry_files": len(
            mnq_session_retry.records
        ),
        "confirmation_missing_session_record_id": (
            "EXP-005-DQ4"
        ),
        "provider_unavailable_sessions_excluded": 2,
        "provider_complete_sessions_restored": 1,
        "restored_session_dates": [
            "2025-12-31"
        ],
        "restored_original_nq_cash_bars": (
            nq_restored_original_bars
        ),
        "restored_original_mnq_cash_bars": (
            mnq_restored_original_bars
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
        "nq_research_ohlc_conflicts_resolved_by_recheck": int(
            sum(
                item.research_ohlc_conflicts_resolved_by_recheck
                for item in nq_import.files
            )
        ),
        "mnq_research_ohlc_conflicts_resolved_by_recheck": int(
            sum(
                item.research_ohlc_conflicts_resolved_by_recheck
                for item in mnq_import.files
            )
        ),
        "nq_non_research_conflicting_duplicate_rows_removed": int(
            sum(
                item.non_research_conflicting_duplicate_rows_removed
                for item in nq_import.files
            )
        ),
        "mnq_non_research_conflicting_duplicate_rows_removed": int(
            sum(
                item.non_research_conflicting_duplicate_rows_removed
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
