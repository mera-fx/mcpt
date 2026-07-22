from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
import hashlib
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd


UTC = ZoneInfo("UTC")
NEW_YORK = ZoneInfo("America/New_York")
PRICE_SCALE = 1_000_000_000
TICK_RAW_UNITS = 250_000_000
OHLC = ("open", "high", "low", "close")
FIELDS = (
    "ts_event",
    "publisher_id",
    "instrument_id",
    "open",
    "high",
    "low",
    "close",
    "volume",
)

# These are the only non-standard sessions inside the six locked windows.
# Values are local New York time and represent interval end points.
SPECIAL_GLOBEX_CLOSE_ET: dict[date, time] = {
    date(2024, 11, 28): time(13, 0),
    date(2024, 11, 29): time(13, 15),
}
SPECIAL_RTH_ET: dict[date, tuple[time, time] | None] = {
    date(2024, 11, 28): None,
    date(2024, 11, 29): (time(9, 30), time(13, 0)),
}


class Exp018MeasurementError(RuntimeError):
    pass


@dataclass(frozen=True)
class LoadedArrays:
    ts_event: np.ndarray
    publisher_id: np.ndarray
    instrument_id: np.ndarray
    open: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    volume: np.ndarray

    @property
    def row_count(self) -> int:
        return int(len(self.ts_event))


@dataclass(frozen=True)
class ExpectedMinutes:
    regular: pd.DatetimeIndex
    extended: pd.DatetimeIndex
    full_globex: pd.DatetimeIndex


@dataclass(frozen=True)
class AuditResult:
    window: dict[str, Any]
    sessions: pd.DataFrame
    missing_runs: pd.DataFrame
    canonical_hash: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_npz(path: Path) -> LoadedArrays:
    path = Path(path)
    if not path.is_file():
        raise Exp018MeasurementError(f"Extracted file is missing: {path}")
    with np.load(path, allow_pickle=False) as archive:
        missing = [field for field in FIELDS if field not in archive.files]
        if missing:
            raise Exp018MeasurementError(
                "Extracted data is missing fields: " + ", ".join(missing)
            )
        arrays = {field: np.asarray(archive[field]) for field in FIELDS}

    lengths = {len(value) for value in arrays.values()}
    if len(lengths) != 1:
        raise Exp018MeasurementError("Extracted arrays have unequal lengths.")
    if not lengths or next(iter(lengths)) == 0:
        raise Exp018MeasurementError("Extracted sample contains no rows.")

    return LoadedArrays(**arrays)


def _to_le_bytes(array: np.ndarray, dtype: str) -> bytes:
    return np.asarray(array, dtype=np.dtype(dtype).newbyteorder("<")).tobytes(
        order="C"
    )


def canonical_row_hash(arrays: LoadedArrays) -> str:
    order = np.lexsort((arrays.instrument_id, arrays.ts_event))
    digest = hashlib.sha256()
    digest.update(b"EXP018_CANONICAL_V1\0")
    for field, dtype in (
        (arrays.ts_event[order], "u8"),
        (arrays.publisher_id[order], "u2"),
        (arrays.instrument_id[order], "u4"),
        (arrays.open[order], "i8"),
        (arrays.high[order], "i8"),
        (arrays.low[order], "i8"),
        (arrays.close[order], "i8"),
        (arrays.volume[order], "u8"),
    ):
        digest.update(_to_le_bytes(field, dtype))
    return digest.hexdigest()


def _local_dt(day: date, clock: time) -> datetime:
    return datetime.combine(day, clock, tzinfo=NEW_YORK)


def _minute_range(start: datetime, end: datetime) -> pd.DatetimeIndex:
    if end <= start:
        return pd.DatetimeIndex([], tz="UTC")
    return pd.date_range(
        pd.Timestamp(start).tz_convert("UTC"),
        pd.Timestamp(end).tz_convert("UTC"),
        freq="min",
        inclusive="left",
    )


def _trade_dates_covering(start_utc: pd.Timestamp, end_utc: pd.Timestamp) -> Iterable[date]:
    local_start = start_utc.tz_convert(NEW_YORK).date() - timedelta(days=1)
    local_end = end_utc.tz_convert(NEW_YORK).date() + timedelta(days=1)
    current = local_start
    while current <= local_end:
        if current.weekday() < 5:
            yield current
        current += timedelta(days=1)


def expected_minutes(start: str, end_exclusive: str) -> ExpectedMinutes:
    start_utc = pd.Timestamp(start, tz="UTC")
    end_utc = pd.Timestamp(end_exclusive, tz="UTC")
    if end_utc <= start_utc:
        raise Exp018MeasurementError("Expected-window end must be after start.")

    regular_parts: list[pd.DatetimeIndex] = []
    full_parts: list[pd.DatetimeIndex] = []

    for trade_date in _trade_dates_covering(start_utc, end_utc):
        session_open = _local_dt(trade_date - timedelta(days=1), time(18, 0))
        session_close = _local_dt(
            trade_date,
            SPECIAL_GLOBEX_CLOSE_ET.get(trade_date, time(17, 0)),
        )
        full_parts.append(_minute_range(session_open, session_close))

        rth = SPECIAL_RTH_ET.get(
            trade_date,
            (time(9, 30), time(16, 0)),
        )
        if rth is not None:
            regular_parts.append(
                _minute_range(
                    _local_dt(trade_date, rth[0]),
                    _local_dt(trade_date, rth[1]),
                )
            )

    full = (
        full_parts[0].append(full_parts[1:])
        if full_parts
        else pd.DatetimeIndex([], tz="UTC")
    )
    regular = (
        regular_parts[0].append(regular_parts[1:])
        if regular_parts
        else pd.DatetimeIndex([], tz="UTC")
    )

    full = full[(full >= start_utc) & (full < end_utc)].drop_duplicates()
    regular = regular[(regular >= start_utc) & (regular < end_utc)].drop_duplicates()
    extended = full.difference(regular)
    return ExpectedMinutes(
        regular=regular.sort_values(),
        extended=extended.sort_values(),
        full_globex=full.sort_values(),
    )


def _duplicate_full_rows(arrays: LoadedArrays) -> int:
    matrix = np.rec.fromarrays(
        [
            arrays.ts_event,
            arrays.publisher_id,
            arrays.instrument_id,
            arrays.open,
            arrays.high,
            arrays.low,
            arrays.close,
            arrays.volume,
        ],
        names=FIELDS,
    )
    _, counts = np.unique(matrix, return_counts=True)
    return int(counts[counts > 1].sum())


def _missing_run_table(
    missing: pd.DatetimeIndex,
    *,
    window_id: str,
    session_type: str,
) -> pd.DataFrame:
    columns = (
        "window_id",
        "session_type",
        "run_start_utc",
        "run_end_utc",
        "minutes",
    )
    if len(missing) == 0:
        return pd.DataFrame(columns=columns)

    values = missing.sort_values()
    groups = np.cumsum(
        np.r_[True, np.diff(values.asi8) != 60_000_000_000]
    )
    rows: list[dict[str, Any]] = []
    for group in np.unique(groups):
        block = values[groups == group]
        rows.append(
            {
                "window_id": window_id,
                "session_type": session_type,
                "run_start_utc": block[0].isoformat(),
                "run_end_utc": block[-1].isoformat(),
                "minutes": int(len(block)),
            }
        )
    return pd.DataFrame(rows, columns=columns)


def audit_arrays(
    arrays: LoadedArrays,
    *,
    window_id: str,
    canonical_contract: str,
    raw_symbol: str,
    expected_instrument_id: int,
    start: str,
    end_exclusive: str,
    raw_sha256: str,
    size_bytes: int,
) -> AuditResult:
    count = arrays.row_count
    timestamp_ns = arrays.ts_event.astype("uint64", copy=False)
    timestamp_index = pd.to_datetime(timestamp_ns, unit="ns", utc=True)
    observed = pd.DatetimeIndex(timestamp_index)

    minute_aligned = timestamp_ns % np.uint64(60_000_000_000) == 0
    duplicate_timestamp_rows = int(observed.duplicated(keep=False).sum())
    duplicate_full_rows = _duplicate_full_rows(arrays)
    out_of_order_pairs = int(np.sum(np.diff(timestamp_ns.astype("int64")) < 0))

    identity_mismatches = int(
        np.sum(arrays.instrument_id.astype("uint64") != expected_instrument_id)
    )
    publisher_ids = sorted(
        int(value) for value in np.unique(arrays.publisher_id.astype("uint64"))
    )
    instrument_ids = sorted(
        int(value) for value in np.unique(arrays.instrument_id.astype("uint64"))
    )

    high_invalid = (
        (arrays.high < arrays.open)
        | (arrays.high < arrays.low)
        | (arrays.high < arrays.close)
    )
    low_invalid = (
        (arrays.low > arrays.open)
        | (arrays.low > arrays.high)
        | (arrays.low > arrays.close)
    )
    invalid_ohlc_rows = int(np.sum(high_invalid | low_invalid))

    # DBN extraction stores volume as unsigned integers. Keep the explicit
    # metric for the preregistered gate and for schema-change detection.
    negative_volume_rows = 0
    nonfinite_ohlcv_rows = 0

    off_tick_values = 0
    for field in OHLC:
        values = getattr(arrays, field)
        off_tick_values += int(np.sum(values % TICK_RAW_UNITS != 0))

    expected = expected_minutes(start, end_exclusive)
    observed_unique = observed.drop_duplicates().sort_values()
    regular_observed = observed_unique.intersection(expected.regular)
    extended_observed = observed_unique.intersection(expected.extended)
    regular_missing = expected.regular.difference(observed_unique)
    extended_missing = expected.extended.difference(observed_unique)
    unexpected = observed_unique.difference(expected.full_globex)

    regular_coverage = (
        float(len(regular_observed) / len(expected.regular))
        if len(expected.regular)
        else float("nan")
    )
    extended_coverage = (
        float(len(extended_observed) / len(expected.extended))
        if len(expected.extended)
        else float("nan")
    )

    session_rows = [
        {
            "window_id": window_id,
            "session_type": "regular",
            "expected_minutes": int(len(expected.regular)),
            "observed_trade_minutes": int(len(regular_observed)),
            "missing_trade_minutes": int(len(regular_missing)),
            "trade_minute_coverage": regular_coverage,
        },
        {
            "window_id": window_id,
            "session_type": "extended_outside_regular",
            "expected_minutes": int(len(expected.extended)),
            "observed_trade_minutes": int(len(extended_observed)),
            "missing_trade_minutes": int(len(extended_missing)),
            "trade_minute_coverage": extended_coverage,
        },
    ]
    sessions = pd.DataFrame(session_rows)
    missing_runs = pd.concat(
        [
            _missing_run_table(
                regular_missing,
                window_id=window_id,
                session_type="regular",
            ),
            _missing_run_table(
                extended_missing,
                window_id=window_id,
                session_type="extended_outside_regular",
            ),
        ],
        ignore_index=True,
    )

    window = {
        "window_id": window_id,
        "canonical_contract": canonical_contract,
        "raw_symbol": raw_symbol,
        "expected_instrument_id": expected_instrument_id,
        "returned_instrument_ids": instrument_ids,
        "publisher_ids": publisher_ids,
        "start": start,
        "end_exclusive": end_exclusive,
        "size_bytes": int(size_bytes),
        "raw_sha256": raw_sha256,
        "canonical_sha256": canonical_row_hash(arrays),
        "row_count": count,
        "first_timestamp_utc": observed.min().isoformat(),
        "last_timestamp_utc": observed.max().isoformat(),
        "timestamp_timezone": "UTC",
        "timestamp_minute_aligned_rows": int(np.sum(minute_aligned)),
        "timestamp_not_minute_aligned_rows": int(np.sum(~minute_aligned)),
        "out_of_order_adjacent_pairs": out_of_order_pairs,
        "duplicate_timestamp_rows": duplicate_timestamp_rows,
        "duplicate_full_rows": duplicate_full_rows,
        "identity_mismatch_rows": identity_mismatches,
        "invalid_ohlc_rows": invalid_ohlc_rows,
        "negative_volume_rows": negative_volume_rows,
        "nonfinite_ohlcv_rows": nonfinite_ohlcv_rows,
        "off_tick_ohlc_values": off_tick_values,
        "expected_regular_minutes": int(len(expected.regular)),
        "observed_regular_trade_minutes": int(len(regular_observed)),
        "regular_trade_minute_coverage": regular_coverage,
        "expected_extended_minutes": int(len(expected.extended)),
        "observed_extended_trade_minutes": int(len(extended_observed)),
        "extended_trade_minute_coverage": extended_coverage,
        "unexpected_outside_session_minutes": int(len(unexpected)),
        "no_trade_minutes_are_not_automatically_vendor_errors": True,
    }
    return AuditResult(
        window=window,
        sessions=sessions,
        missing_runs=missing_runs,
        canonical_hash=window["canonical_sha256"],
    )


def classify(
    window_measurements: pd.DataFrame,
    repeatability: pd.DataFrame,
    *,
    total_estimated_cost_usd: float,
) -> str:
    if len(window_measurements) != 6:
        return "ACCESS_INCOMPLETE"

    structure_columns = (
        "identity_mismatch_rows",
        "timestamp_not_minute_aligned_rows",
        "duplicate_timestamp_rows",
        "duplicate_full_rows",
        "invalid_ohlc_rows",
        "negative_volume_rows",
        "nonfinite_ohlcv_rows",
        "off_tick_ohlc_values",
        "unexpected_outside_session_minutes",
    )
    if any(int(window_measurements[column].sum()) != 0 for column in structure_columns):
        return "STRUCTURE_FAILED"

    if (
        float(window_measurements["regular_trade_minute_coverage"].min()) < 0.999
        or float(window_measurements["extended_trade_minute_coverage"].min())
        < 0.995
    ):
        return "COMPLETENESS_FAILED"

    if total_estimated_cost_usd > 1.0:
        return "COST_CAP_EXCEEDED"

    if len(repeatability) != 2:
        return "REPEATABILITY_PENDING"
    if not bool(repeatability["minimum_delay_met"].all()):
        return "REPEATABILITY_FAILED"
    if not bool(repeatability["canonical_hash_match"].all()):
        return "REPEATABILITY_FAILED"
    if not bool(repeatability["row_count_match"].all()):
        return "REPEATABILITY_FAILED"
    if not bool(repeatability["timestamp_set_match"].all()):
        return "REPEATABILITY_FAILED"

    return "QUALIFIED_AS_ACCESSIBLE_EXACT_CONTRACT_SOURCE"
