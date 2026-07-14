
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

import exp005_quantower_import as base


EXP005_CONFIRMATION_MISSING_SESSION_RESOLUTION: dict[str, Any] = {'schema_version': 1, 'experiment_id': 'EXP-005', 'record_id': 'EXP-005-DQ4', 'locked_date': '2026-07-14', 'status': 'LOCKED_BEFORE_FULL_VALIDATION_RESULTS', 'purpose': 'Resolve three confirmation-calendar sessions that remained missing or incomplete after the full provider-front-month export. Dedicated one-day NQ and MNQ retries are SHA-256 locked. Two sessions are excluded as paired provider-unavailable dates and one complete session is restored from its dedicated retry. No bars are filled or invented.', 'quick_transfer_result_frozen': True, 'confirmation_strategy_results_calculated': False, 'full_validation_results_calculated': False, 'raw_files_edited': False, 'policy': {'paired_exclusion': True, 'fill_missing_bars': False, 'edit_raw_files': False, 'change_strategy_rules': False, 'change_costs': False, 'change_gates': False, 'unrecorded_missing_session': 'STOP', 'complete_retry_replacement': 'Replace only the locked cash session from its SHA-256-locked dedicated retry.'}, 'excluded_sessions': {'2025-09-24': {'reason': 'Both NQ and MNQ dedicated retries contain 389 cash-session bars and omit 10:59 ET.', 'symbols': {'NQ': {'actual_bars': 389, 'missing_times': ['10:59']}, 'MNQ': {'actual_bars': 389, 'missing_times': ['10:59']}}}, '2025-11-07': {'reason': 'Both NQ and MNQ dedicated retries contain 321 cash-session bars and omit the same 69-minute provider-history profile.', 'symbols': {'NQ': {'actual_bars': 321, 'missing_times': ['11:50', '11:51', '11:52', '11:53', '11:54', '11:55', '11:56', '11:57', '11:58', '11:59', '12:00', '12:01', '12:02', '12:03', '12:04', '12:05', '12:06', '12:07', '12:08', '12:09', '12:10', '12:11', '12:12', '12:13', '12:14', '12:15', '12:16', '12:17', '12:18', '12:19', '12:20', '12:21', '12:22', '12:23', '12:24', '12:25', '12:26', '12:27', '12:28', '12:29', '12:30', '12:31', '12:32', '12:33', '12:34', '12:35', '12:36', '12:37', '12:38', '12:39', '12:40', '12:41', '12:42', '12:43', '12:44', '12:45', '12:46', '12:47', '12:48', '12:49', '12:50', '12:51', '12:52', '12:53', '12:54', '12:55', '12:56', '12:57', '12:59']}, 'MNQ': {'actual_bars': 321, 'missing_times': ['11:50', '11:51', '11:52', '11:53', '11:54', '11:55', '11:56', '11:57', '11:58', '11:59', '12:00', '12:01', '12:02', '12:03', '12:04', '12:05', '12:06', '12:07', '12:08', '12:09', '12:10', '12:11', '12:12', '12:13', '12:14', '12:15', '12:16', '12:17', '12:18', '12:19', '12:20', '12:21', '12:22', '12:23', '12:24', '12:25', '12:26', '12:27', '12:28', '12:29', '12:30', '12:31', '12:32', '12:33', '12:34', '12:35', '12:36', '12:37', '12:38', '12:39', '12:40', '12:41', '12:42', '12:43', '12:44', '12:45', '12:46', '12:47', '12:48', '12:49', '12:50', '12:51', '12:52', '12:53', '12:54', '12:55', '12:56', '12:57', '12:59']}}}}, 'restored_sessions': {'2025-12-31': {'reason': 'Both dedicated retries contain a complete duplicate-free 390-minute cash session.', 'symbols': {'NQ': {'actual_bars': 390, 'missing_times': []}, 'MNQ': {'actual_bars': 390, 'missing_times': []}}}}, 'retry_files': {'MNQ': {'2025-09-24': {'sha256': 'ae0f64f3ccc485dc7548aa7653fd5f19bc454fd6585c2265f587df109dc6c9ac', 'raw_rows': 1379, 'unique_timestamps': 1379, 'first_timestamp_utc': '2025-09-23T23:00:00+00:00', 'last_timestamp_utc': '2025-09-24T22:59:00+00:00', 'cash_rows': 389, 'missing_times_new_york': ['10:59']}, '2025-11-07': {'sha256': 'b161fe835fa45d9fa0d4c469fbe872e0a009b8da147d4c5774ba52cf60f5dc38', 'raw_rows': 1251, 'unique_timestamps': 1251, 'first_timestamp_utc': '2025-11-07T00:00:00+00:00', 'last_timestamp_utc': '2025-11-07T21:59:00+00:00', 'cash_rows': 321, 'missing_times_new_york': ['11:50', '11:51', '11:52', '11:53', '11:54', '11:55', '11:56', '11:57', '11:58', '11:59', '12:00', '12:01', '12:02', '12:03', '12:04', '12:05', '12:06', '12:07', '12:08', '12:09', '12:10', '12:11', '12:12', '12:13', '12:14', '12:15', '12:16', '12:17', '12:18', '12:19', '12:20', '12:21', '12:22', '12:23', '12:24', '12:25', '12:26', '12:27', '12:28', '12:29', '12:30', '12:31', '12:32', '12:33', '12:34', '12:35', '12:36', '12:37', '12:38', '12:39', '12:40', '12:41', '12:42', '12:43', '12:44', '12:45', '12:46', '12:47', '12:48', '12:49', '12:50', '12:51', '12:52', '12:53', '12:54', '12:55', '12:56', '12:57', '12:59']}, '2025-12-31': {'sha256': '479d01d70d8e3b4461a711ed4d7ebc5bef475ba3620e41f97b88f8c4e835a2d5', 'raw_rows': 1320, 'unique_timestamps': 1320, 'first_timestamp_utc': '2025-12-31T00:00:00+00:00', 'last_timestamp_utc': '2025-12-31T21:59:00+00:00', 'cash_rows': 390, 'missing_times_new_york': []}}, 'NQ': {'2025-09-24': {'sha256': 'daeb1763e31c19391a7cc9e916a24cabbcf7de7447743faa368340929411644f', 'raw_rows': 1379, 'unique_timestamps': 1379, 'first_timestamp_utc': '2025-09-23T23:00:00+00:00', 'last_timestamp_utc': '2025-09-24T22:59:00+00:00', 'cash_rows': 389, 'missing_times_new_york': ['10:59']}, '2025-11-07': {'sha256': 'aaf6d014c67fdc9a133c92977b1a2276f2e0a5cfdaf5a3161b649deec6f8e1df', 'raw_rows': 1251, 'unique_timestamps': 1251, 'first_timestamp_utc': '2025-11-07T00:00:00+00:00', 'last_timestamp_utc': '2025-11-07T21:59:00+00:00', 'cash_rows': 321, 'missing_times_new_york': ['11:50', '11:51', '11:52', '11:53', '11:54', '11:55', '11:56', '11:57', '11:58', '11:59', '12:00', '12:01', '12:02', '12:03', '12:04', '12:05', '12:06', '12:07', '12:08', '12:09', '12:10', '12:11', '12:12', '12:13', '12:14', '12:15', '12:16', '12:17', '12:18', '12:19', '12:20', '12:21', '12:22', '12:23', '12:24', '12:25', '12:26', '12:27', '12:28', '12:29', '12:30', '12:31', '12:32', '12:33', '12:34', '12:35', '12:36', '12:37', '12:38', '12:39', '12:40', '12:41', '12:42', '12:43', '12:44', '12:45', '12:46', '12:47', '12:48', '12:49', '12:50', '12:51', '12:52', '12:53', '12:54', '12:55', '12:56', '12:57', '12:59']}, '2025-12-31': {'sha256': 'e26cd0a57fd9ac42af58493e640bc8b4129bf3c92a1d8092b54df9b878033d22', 'raw_rows': 1320, 'unique_timestamps': 1320, 'first_timestamp_utc': '2025-12-31T00:00:00+00:00', 'last_timestamp_utc': '2025-12-31T21:59:00+00:00', 'cash_rows': 390, 'missing_times_new_york': []}}}, 'expected_missing_session_rows_after_restoration': {'2025-09-24': ['NQ', 'MNQ'], '2025-11-07': ['NQ', 'MNQ']}, 'result': {'calendar_full_sessions': 744, 'paired_sessions_excluded': 2, 'complete_sessions_restored': 1, 'expected_included_sessions': 742, 'expected_one_minute_rows_per_symbol': 289380, 'expected_five_minute_rows_per_symbol': 57876, 'included_invalid_sessions': 0, 'bars_synthesized': 0}, 'document': 'research/EXP-005_confirmation_missing_session_resolution.md'}

@dataclass(frozen=True)
class ConfirmationSessionRetryEvidence:
    symbol: str
    cash_sessions: dict[str, pd.DataFrame]
    records: tuple[base.RawFileRecord, ...]


def get_exp005_confirmation_missing_session_resolution(
) -> dict[str, Any]:
    return deepcopy(
        EXP005_CONFIRMATION_MISSING_SESSION_RESOLUTION
    )


def validate_exp005_confirmation_missing_session_resolution(
    record: dict[str, Any] | None = None,
) -> None:
    current = (
        EXP005_CONFIRMATION_MISSING_SESSION_RESOLUTION
        if record is None
        else record
    )

    if (
        current.get("experiment_id") != "EXP-005"
        or current.get("record_id") != "EXP-005-DQ4"
    ):
        raise ValueError(
            "Invalid EXP-005 confirmation missing-session record identity."
        )

    if current.get(
        "status"
    ) != "LOCKED_BEFORE_FULL_VALIDATION_RESULTS":
        raise ValueError(
            "Confirmation missing-session resolution must precede results."
        )

    if (
        current.get("quick_transfer_result_frozen") is not True
        or current.get("confirmation_strategy_results_calculated") is not False
        or current.get("full_validation_results_calculated") is not False
        or current.get("raw_files_edited") is not False
    ):
        raise ValueError(
            "Confirmation missing-session protection fields changed."
        )

    policy = current["policy"]

    if (
        policy["paired_exclusion"] is not True
        or policy["fill_missing_bars"] is not False
        or policy["edit_raw_files"] is not False
        or policy["unrecorded_missing_session"] != "STOP"
    ):
        raise ValueError(
            "Confirmation missing-session policy changed."
        )

    if set(
        current["excluded_sessions"]
    ) != {
        "2025-09-24",
        "2025-11-07",
    }:
        raise ValueError(
            "Locked confirmation exclusion dates changed."
        )

    if set(
        current["restored_sessions"]
    ) != {
        "2025-12-31",
    }:
        raise ValueError(
            "Locked confirmation restoration date changed."
        )

    expected_hashes: set[str] = set()

    for symbol, specifications in current[
        "retry_files"
    ].items():
        if symbol not in {"NQ", "MNQ"}:
            raise ValueError(
                "Unexpected symbol in confirmation retry record."
            )

        if set(specifications) != {
            "2025-09-24",
            "2025-11-07",
            "2025-12-31",
        }:
            raise ValueError(
                "Confirmation retry date set changed."
            )

        for specification in specifications.values():
            digest = specification["sha256"]

            if len(digest) != 64:
                raise ValueError(
                    "Every confirmation retry hash must be SHA-256."
                )

            expected_hashes.add(digest)

    if len(expected_hashes) != 6:
        raise ValueError(
            "Confirmation retry hashes must be unique."
        )

    expected_missing = current[
        "expected_missing_session_rows_after_restoration"
    ]

    if expected_missing != {
        "2025-09-24": ["NQ", "MNQ"],
        "2025-11-07": ["NQ", "MNQ"],
    }:
        raise ValueError(
            "Expected confirmation missing-session profile changed."
        )

    result = current["result"]

    if (
        result["calendar_full_sessions"] != 744
        or result["paired_sessions_excluded"] != 2
        or result["complete_sessions_restored"] != 1
        or result["expected_included_sessions"] != 742
        or result["expected_one_minute_rows_per_symbol"] != 289380
        or result["expected_five_minute_rows_per_symbol"] != 57876
        or result["included_invalid_sessions"] != 0
        or result["bars_synthesized"] != 0
    ):
        raise ValueError(
            "Locked confirmation missing-session result changed."
        )


def locked_confirmation_excluded_dates(
) -> tuple[date, ...]:
    validate_exp005_confirmation_missing_session_resolution()

    return tuple(
        date.fromisoformat(item)
        for item in sorted(
            EXP005_CONFIRMATION_MISSING_SESSION_RESOLUTION[
                "excluded_sessions"
            ]
        )
    )


def _cash_session(
    frame: pd.DataFrame,
    *,
    session_date: date,
) -> pd.DataFrame:
    local = frame.copy()
    local.index = local.index.tz_convert(
        base.NEW_YORK_TZ
    )

    times = local.index.time
    mask = (
        (times >= base.SESSION_START)
        & (times < base.SESSION_END)
        & (
            pd.Index(
                item.date()
                for item in local.index
            )
            == session_date
        )
    )

    cash = local.loc[mask].copy()
    cash.index.name = "timestamp"

    return cash


def _expected_cash_index(
    session_date: date,
) -> pd.DatetimeIndex:
    start = pd.Timestamp.combine(
        session_date,
        base.SESSION_START,
    ).tz_localize(
        base.NEW_YORK_TZ
    )

    return pd.date_range(
        start=start,
        periods=base.EXPECTED_ONE_MINUTE_BARS,
        freq="min",
    )


def _observed_retry_profile(
    frame: pd.DataFrame,
    *,
    session_date: date,
) -> dict[str, Any]:
    cash = _cash_session(
        frame,
        session_date=session_date,
    )
    expected = _expected_cash_index(
        session_date
    )
    actual_index = pd.DatetimeIndex(
        cash.index
    ).sort_values()

    return {
        "cash": cash,
        "actual_bars": int(
            len(actual_index)
        ),
        "missing_times": [
            item.strftime("%H:%M")
            for item in expected.difference(
                actual_index
            )
        ],
        "unexpected_bars": int(
            len(
                actual_index.difference(
                    expected
                )
            )
        ),
        "duplicate_bars": int(
            actual_index.duplicated().sum()
        ),
    }


def load_confirmation_session_retry_evidence(
    paths: Iterable[Path],
    *,
    symbol: str,
) -> ConfirmationSessionRetryEvidence:
    validate_exp005_confirmation_missing_session_resolution()
    normalized_symbol = symbol.strip().upper()

    if normalized_symbol not in {"NQ", "MNQ"}:
        raise base.QuantowerImportError(
            "Confirmation session retries accept only NQ or MNQ."
        )

    expected = (
        EXP005_CONFIRMATION_MISSING_SESSION_RESOLUTION[
            "retry_files"
        ][normalized_symbol]
    )
    expected_by_hash = {
        specification["sha256"]: (
            session_text,
            specification,
        )
        for session_text, specification
        in expected.items()
    }

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
            "session retry CSV files."
        )

    seen: set[str] = set()
    cash_sessions: dict[
        str,
        pd.DataFrame,
    ] = {}
    records: list[
        base.RawFileRecord
    ] = []

    for path in path_list:
        digest = base.sha256_file(
            path
        )

        if digest not in expected_by_hash:
            raise base.QuantowerImportError(
                f"Unexpected {normalized_symbol} confirmation "
                f"session retry hash: {path.name}."
            )

        if digest in seen:
            raise base.QuantowerImportError(
                f"Duplicate {normalized_symbol} confirmation "
                "session retry file."
            )

        (
            session_text,
            specification,
        ) = expected_by_hash[digest]
        target_date = date.fromisoformat(
            session_text
        )

        frame, file_record = (
            base.read_quantower_csv(
                path,
                symbol=normalized_symbol,
                source_role=(
                    "CONFIRMATION_SESSION_RETRY"
                ),
            )
        )

        if frame.index.has_duplicates:
            raise base.QuantowerImportError(
                f"{path.name} contains retry duplicates."
            )

        if (
            len(frame)
            != specification["raw_rows"]
            or frame.index.nunique()
            != specification["unique_timestamps"]
            or frame.index[0].isoformat()
            != specification["first_timestamp_utc"]
            or frame.index[-1].isoformat()
            != specification["last_timestamp_utc"]
        ):
            raise base.QuantowerImportError(
                f"{path.name} retry boundaries or row counts changed."
            )

        observed = _observed_retry_profile(
            frame,
            session_date=target_date,
        )

        if (
            observed["actual_bars"]
            != specification["cash_rows"]
            or observed["missing_times"]
            != specification["missing_times_new_york"]
            or observed["unexpected_bars"] != 0
            or observed["duplicate_bars"] != 0
        ):
            raise base.IncompleteExportError(
                f"Locked confirmation retry profile changed "
                f"for {normalized_symbol} {session_text}."
            )

        cash_sessions[
            session_text
        ] = observed["cash"]
        records.append(file_record)
        seen.add(digest)

    if seen != set(expected_by_hash):
        raise base.QuantowerImportError(
            f"{normalized_symbol} confirmation "
            "session retry set is incomplete."
        )

    return ConfirmationSessionRetryEvidence(
        symbol=normalized_symbol,
        cash_sessions=cash_sessions,
        records=tuple(records),
    )


def _cash_date_mask(
    index: pd.DatetimeIndex,
    *,
    session_date: date,
) -> list[bool]:
    local = index.tz_convert(
        base.NEW_YORK_TZ
    )

    return [
        (
            item.date() == session_date
            and base.SESSION_START
            <= item.time()
            < base.SESSION_END
        )
        for item in local
    ]


def restore_locked_confirmation_session(
    symbol_import: base.SymbolImport,
    evidence: ConfirmationSessionRetryEvidence,
) -> tuple[
    base.SymbolImport,
    int,
]:
    if symbol_import.symbol != evidence.symbol:
        raise base.QuantowerImportError(
            "Confirmation retry symbol does not match imported symbol."
        )

    session_text = "2025-12-31"
    target_date = date.fromisoformat(
        session_text
    )
    retry_cash = evidence.cash_sessions[
        session_text
    ].copy()
    retry_cash.index = retry_cash.index.tz_convert(
        symbol_import.frame.index.tz
    )

    existing_mask = _cash_date_mask(
        pd.DatetimeIndex(
            symbol_import.frame.index
        ),
        session_date=target_date,
    )
    existing_count = int(
        sum(existing_mask)
    )

    if existing_count >= base.EXPECTED_ONE_MINUTE_BARS:
        raise base.QuantowerImportError(
            f"{evidence.symbol} {session_text} was not "
            "missing or incomplete before the locked retry replacement."
        )

    remaining = symbol_import.frame.loc[
        [
            not item
            for item in existing_mask
        ]
    ].copy()

    restored = pd.concat(
        [
            remaining,
            retry_cash,
        ],
        axis=0,
    ).sort_index()

    if restored.index.has_duplicates:
        raise base.QuantowerImportError(
            f"{evidence.symbol} restored confirmation "
            "frame contains duplicate timestamps."
        )

    base._validate_ohlcv(
        restored,
        symbol=evidence.symbol,
    )

    return (
        base.SymbolImport(
            symbol=symbol_import.symbol,
            frame=restored,
            files=symbol_import.files,
            duplicate_overlap_rows_removed=(
                symbol_import
                .duplicate_overlap_rows_removed
            ),
        ),
        existing_count,
    )


def validate_locked_confirmation_missing_sessions(
    *,
    missing_expected: pd.DataFrame,
) -> pd.DataFrame:
    validate_exp005_confirmation_missing_session_resolution()
    expected = (
        EXP005_CONFIRMATION_MISSING_SESSION_RESOLUTION[
            "expected_missing_session_rows_after_restoration"
        ]
    )
    observed: dict[str, list[str]] = {}

    if not missing_expected.empty:
        for row in missing_expected.to_dict(
            orient="records"
        ):
            observed[
                str(row["session_date"])
            ] = str(
                row["symbol"]
            ).split(",")

    if observed != expected:
        raise base.IncompleteExportError(
            "The observed confirmation missing-session set "
            "does not exactly match locked record EXP-005-DQ4.",
            missing_sessions=missing_expected,
        )

    rows: list[
        dict[str, Any]
    ] = []

    for session_text, specification in (
        EXP005_CONFIRMATION_MISSING_SESSION_RESOLUTION[
            "excluded_sessions"
        ].items()
    ):
        rows.append(
            {
                "symbol": "BOTH",
                "session_date": session_text,
                "reason": (
                    "locked_confirmation_provider_history_unavailable"
                ),
                "actual_bars_nq": (
                    specification[
                        "symbols"
                    ]["NQ"]["actual_bars"]
                ),
                "actual_bars_mnq": (
                    specification[
                        "symbols"
                    ]["MNQ"]["actual_bars"]
                ),
                "missing_bars_nq": len(
                    specification[
                        "symbols"
                    ]["NQ"]["missing_times"]
                ),
                "missing_bars_mnq": len(
                    specification[
                        "symbols"
                    ]["MNQ"]["missing_times"]
                ),
                "bars_synthesized": 0,
                "resolution_record": (
                    "EXP-005-DQ4"
                ),
                "detail": specification[
                    "reason"
                ],
            }
        )

    return pd.DataFrame(
        rows
    )


if __name__ == "__main__":
    validate_exp005_confirmation_missing_session_resolution()
    print(
        "EXP-005 confirmation missing-session "
        "resolution is valid."
    )
