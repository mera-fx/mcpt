from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, time
import hashlib
from pathlib import Path
import shutil
from typing import Any, Iterable

import numpy as np
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent
QUICK_START = date(2019, 5, 6)
QUICK_END = date(2022, 12, 30)
NEW_YORK_TZ = "America/New_York"
SOURCE_TZ = "UTC"
SESSION_START = time(9, 30)
SESSION_END = time(16, 0)
EXPECTED_ONE_MINUTE_BARS = 390
EXPECTED_FIVE_MINUTE_BARS = 78
TICK_SIZE = 0.25
MAX_MEDIAN_CLOSE_DIFFERENCE = 5.0
MAX_SINGLE_CLOSE_DIFFERENCE = 20.0

INCOMING_ROOT = (
    PROJECT_DIR
    / "data"
    / "EXP-005"
    / "incoming"
)
RAW_ROOT = (
    PROJECT_DIR
    / "data"
    / "EXP-005"
    / "raw"
)
PROCESSED_ROOT = (
    PROJECT_DIR
    / "data"
    / "EXP-005"
    / "processed"
)
RESULTS_ROOT = (
    PROJECT_DIR
    / "results"
    / "EXP-005"
    / "data"
)
QQQ_CALENDAR_FILE = (
    PROJECT_DIR
    / "data"
    / "QQQ_5m_SIP.parquet"
)

REQUIRED_COLUMNS = (
    "Time left",
    "Time right",
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
)


class QuantowerImportError(RuntimeError):
    pass


class ProtectedPeriodError(QuantowerImportError):
    pass


class IncompleteExportError(QuantowerImportError):
    def __init__(
        self,
        message: str,
        *,
        missing_sessions: pd.DataFrame | None = None,
    ) -> None:
        super().__init__(message)
        self.missing_sessions = missing_sessions


class AlignmentError(QuantowerImportError):
    pass


@dataclass(frozen=True)
class RawFileRecord:
    symbol: str
    source_path: str
    filename: str
    sha256: str
    size_bytes: int
    rows: int
    first_timestamp_utc: str
    last_timestamp_utc: str
    duplicate_rows_removed: int = 0
    non_research_conflicting_duplicate_rows_removed: int = 0
    archived_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SymbolImport:
    symbol: str
    frame: pd.DataFrame
    files: tuple[RawFileRecord, ...]
    duplicate_overlap_rows_removed: int

    @property
    def raw_rows(self) -> int:
        return int(len(self.frame))


@dataclass(frozen=True)
class SessionExtraction:
    symbol: str
    data: pd.DataFrame
    incomplete_sessions: pd.DataFrame
    unexpected_sessions: pd.DataFrame


@dataclass(frozen=True)
class AlignedDataset:
    nq_1m: pd.DataFrame
    mnq_1m: pd.DataFrame
    excluded_mismatch_sessions: pd.DataFrame


@dataclass(frozen=True)
class ProcessedDataset:
    nq_1m: pd.DataFrame
    mnq_1m: pd.DataFrame
    nq_5m: pd.DataFrame
    mnq_5m: pd.DataFrame
    manifest: tuple[RawFileRecord, ...]
    audit: dict[str, Any]
    excluded_sessions: pd.DataFrame


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for block in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def dataframe_sha256(frame: pd.DataFrame) -> str:
    canonical = frame.copy()
    canonical = canonical.sort_index()
    payload = canonical.to_csv(
        index=True,
        date_format="%Y-%m-%dT%H:%M:%S.%f%z",
        float_format="%.10f",
        lineterminator="\n",
    ).encode("utf-8")

    return hashlib.sha256(payload).hexdigest()


def _validate_symbol(symbol: str) -> str:
    normalized = symbol.strip().upper()

    if normalized not in {"NQ", "MNQ"}:
        raise QuantowerImportError(
            "EXP-005 accepts only NQ or MNQ."
        )

    return normalized


def _drop_blank_columns(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    keep: list[str] = []

    for column in frame.columns:
        name = str(column).strip()

        if not name:
            continue

        series = frame[column]

        if (
            name.lower().startswith("unnamed")
            and series.isna().all()
        ):
            continue

        keep.append(column)

    return frame.loc[:, keep].copy()


def _validate_ohlcv(
    frame: pd.DataFrame,
    *,
    symbol: str,
) -> None:
    if frame.empty:
        raise QuantowerImportError(
            f"{symbol} CSV contains no rows."
        )

    prices = frame[
        ["open", "high", "low", "close"]
    ].astype(float)

    if not np.isfinite(
        prices.to_numpy()
    ).all():
        raise QuantowerImportError(
            f"{symbol} contains non-finite prices."
        )

    if (prices <= 0).any().any():
        raise QuantowerImportError(
            f"{symbol} prices must be positive."
        )

    invalid_high = (
        prices["high"]
        < prices[
            ["open", "low", "close"]
        ].max(axis=1)
    )

    invalid_low = (
        prices["low"]
        > prices[
            ["open", "high", "close"]
        ].min(axis=1)
    )

    if invalid_high.any() or invalid_low.any():
        raise QuantowerImportError(
            f"{symbol} contains invalid OHLC relationships."
        )

    scaled = prices.to_numpy() / TICK_SIZE

    if not np.allclose(
        scaled,
        np.round(scaled),
        atol=1e-8,
        rtol=0.0,
    ):
        raise QuantowerImportError(
            f"{symbol} contains prices that do not conform "
            "to the 0.25-point tick."
        )

    volume = frame["volume"].astype(float)

    if not np.isfinite(volume.to_numpy()).all():
        raise QuantowerImportError(
            f"{symbol} contains non-finite volume."
        )

    if (volume < 0).any():
        raise QuantowerImportError(
            f"{symbol} contains negative volume."
        )


def _is_locked_cash_timestamp(
    timestamp: pd.Timestamp,
) -> bool:
    local = timestamp.tz_convert(
        NEW_YORK_TZ
    )

    return (
        QUICK_START <= local.date() <= QUICK_END
        and SESSION_START <= local.time() < SESSION_END
    )


def _deduplicate_identical_timestamp_rows(
    frame: pd.DataFrame,
    *,
    path: Path,
    symbol: str,
) -> tuple[pd.DataFrame, int, int]:
    if not frame.index.has_duplicates:
        return frame, 0, 0

    columns = [
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]

    pieces: list[pd.DataFrame] = []
    removed = 0
    non_research_conflicting_removed = 0

    for timestamp, group in frame.groupby(
        level=0,
        sort=True,
    ):
        if len(group) == 1:
            pieces.append(group)
            continue

        values = group[columns].astype(float).to_numpy()
        reference = np.repeat(
            values[[0]],
            repeats=len(values),
            axis=0,
        )

        rows_match = np.allclose(
            values,
            reference,
            atol=1e-12,
            rtol=0.0,
        )

        if (
            not rows_match
            and _is_locked_cash_timestamp(
                pd.Timestamp(timestamp)
            )
        ):
            preview = (
                group[columns]
                .head(4)
                .to_dict(orient="records")
            )

            raise QuantowerImportError(
                f"{path.name} contains research-session "
                f"conflicting duplicate timestamp "
                f"{timestamp.isoformat()} for {symbol}. "
                f"The duplicate bars have different OHLCV "
                f"values: {preview}"
            )

        pieces.append(
            group.iloc[[0]]
        )

        duplicate_rows = len(group) - 1
        removed += duplicate_rows

        if not rows_match:
            non_research_conflicting_removed += (
                duplicate_rows
            )

    deduplicated = pd.concat(
        pieces,
        axis=0,
    ).sort_index()

    if deduplicated.index.has_duplicates:
        raise QuantowerImportError(
            f"{path.name} duplicate cleanup failed."
        )

    return (
        deduplicated,
        removed,
        non_research_conflicting_removed,
    )


def read_quantower_csv(
    path: Path,
    *,
    symbol: str,
) -> tuple[pd.DataFrame, RawFileRecord]:
    path = Path(path)
    normalized_symbol = _validate_symbol(symbol)

    if not path.exists():
        raise FileNotFoundError(
            f"Quantower CSV not found: {path}"
        )

    frame = pd.read_csv(
        path,
        sep=";",
        engine="python",
    )

    frame = _drop_blank_columns(frame)

    missing = set(
        REQUIRED_COLUMNS
    ).difference(frame.columns)

    if missing:
        raise QuantowerImportError(
            f"{path.name} is missing Quantower columns: "
            f"{sorted(missing)}"
        )

    left = pd.to_datetime(
        frame["Time left"],
        errors="raise",
    )

    right = pd.to_datetime(
        frame["Time right"],
        errors="raise",
    )

    if left.dt.tz is not None or right.dt.tz is not None:
        raise QuantowerImportError(
            "Quantower source timestamps must be exported "
            "as naive UTC clock values."
        )

    index = pd.DatetimeIndex(
        left,
    ).tz_localize(SOURCE_TZ)

    right_index = pd.DatetimeIndex(
        right,
    ).tz_localize(SOURCE_TZ)

    expected_right = (
        index
        + pd.Timedelta(seconds=59, milliseconds=999)
    )

    if not right_index.equals(expected_right):
        raise QuantowerImportError(
            f"{path.name} does not contain exact one-minute "
            "Time left/Time right intervals."
        )

    numeric = pd.DataFrame(
        {
            "open": pd.to_numeric(
                frame["Open"],
                errors="raise",
            ).to_numpy(),
            "high": pd.to_numeric(
                frame["High"],
                errors="raise",
            ).to_numpy(),
            "low": pd.to_numeric(
                frame["Low"],
                errors="raise",
            ).to_numpy(),
            "close": pd.to_numeric(
                frame["Close"],
                errors="raise",
            ).to_numpy(),
            "volume": pd.to_numeric(
                frame["Volume"],
                errors="raise",
            ).to_numpy(),
        },
        index=index,
    )

    numeric.index.name = "timestamp"

    (
        numeric,
        duplicate_rows_removed,
        non_research_conflicting_duplicate_rows_removed,
    ) = _deduplicate_identical_timestamp_rows(
        numeric,
        path=path,
        symbol=normalized_symbol,
    )

    if not numeric.index.is_monotonic_increasing:
        numeric = numeric.sort_index()

    _validate_ohlcv(
        numeric,
        symbol=normalized_symbol,
    )

    record = RawFileRecord(
        symbol=normalized_symbol,
        source_path=str(path.resolve()),
        filename=path.name,
        sha256=sha256_file(path),
        size_bytes=int(path.stat().st_size),
        rows=int(len(numeric)),
        first_timestamp_utc=(
            numeric.index[0].isoformat()
        ),
        last_timestamp_utc=(
            numeric.index[-1].isoformat()
        ),
        duplicate_rows_removed=(
            duplicate_rows_removed
        ),
        non_research_conflicting_duplicate_rows_removed=(
            non_research_conflicting_duplicate_rows_removed
        ),
    )

    return numeric, record


def _rows_equal(
    first: pd.DataFrame,
    second: pd.DataFrame,
) -> bool:
    columns = [
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]

    left = first[columns].astype(float)
    right = second[columns].astype(float)

    return bool(
        np.allclose(
            left.to_numpy(),
            right.to_numpy(),
            atol=1e-12,
            rtol=0.0,
        )
    )


def load_symbol_chunks(
    paths: Iterable[Path],
    *,
    symbol: str,
) -> SymbolImport:
    normalized_symbol = _validate_symbol(symbol)
    path_list = sorted(
        {
            Path(path).resolve()
            for path in paths
        },
        key=lambda item: str(item).lower(),
    )

    if not path_list:
        raise FileNotFoundError(
            f"No {normalized_symbol} Quantower CSV files found."
        )

    frames: list[pd.DataFrame] = []
    records: list[RawFileRecord] = []

    for path in path_list:
        frame, record = read_quantower_csv(
            path,
            symbol=normalized_symbol,
        )

        frames.append(frame)
        records.append(record)

    combined = pd.concat(
        frames,
        axis=0,
    ).sort_index()

    duplicate_count = int(
        combined.index.duplicated(
            keep=False
        ).sum()
    )

    removed = 0

    if duplicate_count:
        pieces: list[pd.DataFrame] = []

        for timestamp, group in combined.groupby(
            level=0,
            sort=True,
        ):
            if len(group) == 1:
                pieces.append(group)
                continue

            first = group.iloc[[0]]

            if not _rows_equal(
                group,
                pd.concat(
                    [first] * len(group),
                    axis=0,
                ),
            ):
                raise QuantowerImportError(
                    f"{normalized_symbol} overlapping CSV files "
                    f"disagree at {timestamp}."
                )

            pieces.append(first)
            removed += len(group) - 1

        combined = pd.concat(
            pieces,
            axis=0,
        ).sort_index()

    if combined.index.has_duplicates:
        raise QuantowerImportError(
            f"{normalized_symbol} duplicate removal failed."
        )

    _validate_ohlcv(
        combined,
        symbol=normalized_symbol,
    )

    return SymbolImport(
        symbol=normalized_symbol,
        frame=combined,
        files=tuple(records),
        duplicate_overlap_rows_removed=removed,
    )


def load_expected_full_sessions(
    qqq_path: Path = QQQ_CALENDAR_FILE,
) -> tuple[date, ...]:
    path = Path(qqq_path)

    if not path.exists():
        raise FileNotFoundError(
            "The validated QQQ calendar file is missing: "
            f"{path}. EXP-005 reuses its already-validated "
            "full cash-session list."
        )

    if path.suffix.lower() == ".csv":
        frame = pd.read_csv(path)
    else:
        frame = pd.read_parquet(path)

    if "session_date" not in frame.columns:
        raise QuantowerImportError(
            "QQQ calendar data is missing session_date."
        )

    dates = pd.to_datetime(
        frame["session_date"],
        errors="raise",
    ).dt.date

    counts = pd.Series(
        dates,
    ).value_counts()

    invalid_counts = counts[
        counts != EXPECTED_FIVE_MINUTE_BARS
    ]

    if not invalid_counts.empty:
        raise QuantowerImportError(
            "QQQ calendar source contains non-full sessions."
        )

    expected = tuple(
        sorted(
            session
            for session in set(dates)
            if QUICK_START <= session <= QUICK_END
        )
    )

    if not expected:
        raise QuantowerImportError(
            "No full QQQ sessions remain in the EXP-005 "
            "quick-transfer window."
        )

    if expected[0] < QUICK_START or expected[-1] > QUICK_END:
        raise ProtectedPeriodError(
            "Expected session calendar escaped the quick period."
        )

    return expected


def _cash_only(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    local = frame.copy()
    local.index = local.index.tz_convert(
        NEW_YORK_TZ
    )

    times = local.index.time

    mask = (
        (times >= SESSION_START)
        & (times < SESSION_END)
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
            if item < QUICK_START or item > QUICK_END
        }
    )

    if unauthorized:
        raise ProtectedPeriodError(
            "Quantower CSV contains cash-session rows outside "
            "the locked quick-transfer period. First detected: "
            f"{unauthorized[0]}. Do not export 2023–2025."
        )

    return cash


def expected_cash_index(
    session_date: date,
) -> pd.DatetimeIndex:
    start = pd.Timestamp.combine(
        session_date,
        SESSION_START,
    ).tz_localize(NEW_YORK_TZ)

    return pd.date_range(
        start=start,
        periods=EXPECTED_ONE_MINUTE_BARS,
        freq="min",
    )


def extract_complete_sessions(
    symbol_import: SymbolImport,
    *,
    expected_sessions: Iterable[date],
) -> SessionExtraction:
    expected = tuple(
        sorted(set(expected_sessions))
    )

    if not expected:
        raise QuantowerImportError(
            "Expected session list is empty."
        )

    cash = _cash_only(
        symbol_import.frame
    )

    available_dates = set(
        cash["session_date"]
    )

    unexpected_rows: list[dict[str, Any]] = []

    for session in sorted(
        available_dates.difference(expected)
    ):
        session_rows = cash[
            cash["session_date"] == session
        ]

        unexpected_rows.append(
            {
                "symbol": symbol_import.symbol,
                "session_date": session.isoformat(),
                "reason": (
                    "not_in_validated_full_equity_calendar"
                ),
                "actual_bars": int(len(session_rows)),
                "missing_bars": None,
                "unexpected_bars": int(
                    len(session_rows)
                ),
            }
        )

    included: list[pd.DataFrame] = []
    incomplete_rows: list[dict[str, Any]] = []

    for session in expected:
        expected_index = expected_cash_index(
            session
        )

        actual = cash[
            cash["session_date"] == session
        ].drop(
            columns=["session_date"]
        )

        missing = expected_index.difference(
            actual.index
        )

        unexpected = actual.index.difference(
            expected_index
        )

        duplicate_count = int(
            actual.index.duplicated().sum()
        )

        if (
            len(actual) != EXPECTED_ONE_MINUTE_BARS
            or len(missing)
            or len(unexpected)
            or duplicate_count
        ):
            incomplete_rows.append(
                {
                    "symbol": symbol_import.symbol,
                    "session_date": session.isoformat(),
                    "reason": (
                        "missing_or_irregular_cash_minutes"
                    ),
                    "actual_bars": int(len(actual)),
                    "missing_bars": int(len(missing)),
                    "unexpected_bars": int(
                        len(unexpected)
                    ),
                    "duplicate_bars": duplicate_count,
                }
            )
            continue

        actual = actual.reindex(
            expected_index
        ).copy()

        actual["session_date"] = (
            session.isoformat()
        )

        actual["minute_slot"] = np.arange(
            EXPECTED_ONE_MINUTE_BARS,
            dtype=int,
        )

        included.append(actual)

    if not included:
        raise IncompleteExportError(
            f"No complete {symbol_import.symbol} cash sessions "
            "were available."
        )

    data = pd.concat(
        included,
        axis=0,
    )

    data.index = data.index.tz_convert(
        "UTC"
    )

    data.index.name = "timestamp"
    data = data.sort_index()

    incomplete = pd.DataFrame(
        incomplete_rows,
        columns=[
            "symbol",
            "session_date",
            "reason",
            "actual_bars",
            "missing_bars",
            "unexpected_bars",
            "duplicate_bars",
        ],
    )

    unexpected_frame = pd.DataFrame(
        unexpected_rows,
        columns=[
            "symbol",
            "session_date",
            "reason",
            "actual_bars",
            "missing_bars",
            "unexpected_bars",
        ],
    )

    return SessionExtraction(
        symbol=symbol_import.symbol,
        data=data,
        incomplete_sessions=incomplete,
        unexpected_sessions=unexpected_frame,
    )


def _session_dates(
    frame: pd.DataFrame,
) -> set[str]:
    return set(
        frame["session_date"].astype(str)
    )


def align_nq_mnq(
    nq: SessionExtraction,
    mnq: SessionExtraction,
) -> AlignedDataset:
    nq_dates = _session_dates(nq.data)
    mnq_dates = _session_dates(mnq.data)

    common = sorted(
        nq_dates.intersection(mnq_dates)
    )

    if not common:
        raise AlignmentError(
            "NQ and MNQ have no common complete sessions."
        )

    excluded: list[dict[str, Any]] = []
    accepted: list[str] = []

    for session in common:
        nq_session = nq.data[
            nq.data["session_date"] == session
        ]

        mnq_session = mnq.data[
            mnq.data["session_date"] == session
        ]

        if not nq_session.index.equals(
            mnq_session.index
        ):
            excluded.append(
                {
                    "symbol": "BOTH",
                    "session_date": session,
                    "reason": (
                        "nq_mnq_timestamp_mismatch"
                    ),
                    "median_close_difference": None,
                    "maximum_close_difference": None,
                }
            )
            continue

        difference = (
            nq_session["close"].astype(float)
            - mnq_session["close"].astype(float)
        ).abs()

        median_difference = float(
            difference.median()
        )

        maximum_difference = float(
            difference.max()
        )

        if (
            median_difference
            > MAX_MEDIAN_CLOSE_DIFFERENCE
            or maximum_difference
            > MAX_SINGLE_CLOSE_DIFFERENCE
        ):
            excluded.append(
                {
                    "symbol": "BOTH",
                    "session_date": session,
                    "reason": (
                        "potential_front_month_mismatch"
                    ),
                    "median_close_difference": (
                        median_difference
                    ),
                    "maximum_close_difference": (
                        maximum_difference
                    ),
                }
            )
            continue

        accepted.append(session)

    if not accepted:
        raise AlignmentError(
            "Every common NQ/MNQ session failed alignment."
        )

    nq_aligned = nq.data[
        nq.data["session_date"].isin(
            accepted
        )
    ].copy()

    mnq_aligned = mnq.data[
        mnq.data["session_date"].isin(
            accepted
        )
    ].copy()

    if not nq_aligned.index.equals(
        mnq_aligned.index
    ):
        raise AlignmentError(
            "Aligned NQ/MNQ timestamps are not identical."
        )

    excluded_frame = pd.DataFrame(
        excluded,
        columns=[
            "symbol",
            "session_date",
            "reason",
            "median_close_difference",
            "maximum_close_difference",
        ],
    )

    return AlignedDataset(
        nq_1m=nq_aligned,
        mnq_1m=mnq_aligned,
        excluded_mismatch_sessions=excluded_frame,
    )


def aggregate_to_five_minutes(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    required = {
        "open",
        "high",
        "low",
        "close",
        "volume",
        "session_date",
        "minute_slot",
    }

    missing = required.difference(
        frame.columns
    )

    if missing:
        raise QuantowerImportError(
            "One-minute data is missing aggregation columns: "
            f"{sorted(missing)}"
        )

    pieces: list[pd.DataFrame] = []

    for session, session_frame in frame.groupby(
        "session_date",
        sort=True,
    ):
        ordered = session_frame.sort_values(
            "minute_slot"
        )

        if len(ordered) != EXPECTED_ONE_MINUTE_BARS:
            raise QuantowerImportError(
                f"{session} does not contain 390 one-minute bars."
            )

        if not np.array_equal(
            ordered["minute_slot"].to_numpy(
                dtype=int
            ),
            np.arange(EXPECTED_ONE_MINUTE_BARS),
        ):
            raise QuantowerImportError(
                f"{session} minute slots are not 0 through 389."
            )

        grouped = ordered.assign(
            slot=(
                ordered["minute_slot"].astype(int)
                // 5
            )
        ).groupby(
            "slot",
            sort=True,
        )

        aggregated = grouped.agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            volume=("volume", "sum"),
        )

        if len(aggregated) != EXPECTED_FIVE_MINUTE_BARS:
            raise QuantowerImportError(
                f"{session} did not aggregate to 78 bars."
            )

        first_timestamps = [
            group.index[0]
            for _, group in grouped
        ]

        aggregated.index = pd.DatetimeIndex(
            first_timestamps
        )

        aggregated.index.name = "timestamp"
        aggregated["session_date"] = str(
            session
        )
        aggregated["slot"] = np.arange(
            EXPECTED_FIVE_MINUTE_BARS,
            dtype=int,
        )

        pieces.append(aggregated)

    result = pd.concat(
        pieces,
        axis=0,
    ).sort_index()

    result.index = pd.to_datetime(
        result.index,
        utc=True,
    )

    _validate_ohlcv(
        result,
        symbol="aggregated futures",
    )

    return result


def validate_processed_one_minute(
    frame: pd.DataFrame,
    *,
    symbol: str,
) -> None:
    if frame.index.tz is None:
        raise QuantowerImportError(
            f"{symbol} one-minute timestamps are naive."
        )

    if frame.index.has_duplicates:
        raise QuantowerImportError(
            f"{symbol} one-minute timestamps are duplicated."
        )

    counts = frame.groupby(
        "session_date"
    ).size()

    if not counts.eq(
        EXPECTED_ONE_MINUTE_BARS
    ).all():
        raise QuantowerImportError(
            f"Every included {symbol} session must contain "
            "390 one-minute bars."
        )

    for session, group in frame.groupby(
        "session_date",
        sort=True,
    ):
        if not np.array_equal(
            group["minute_slot"].to_numpy(
                dtype=int
            ),
            np.arange(EXPECTED_ONE_MINUTE_BARS),
        ):
            raise QuantowerImportError(
                f"{symbol} session {session} has bad minute slots."
            )

    _validate_ohlcv(
        frame,
        symbol=symbol,
    )


def validate_processed_five_minute(
    frame: pd.DataFrame,
    *,
    symbol: str,
) -> None:
    if frame.index.tz is None:
        raise QuantowerImportError(
            f"{symbol} five-minute timestamps are naive."
        )

    if frame.index.has_duplicates:
        raise QuantowerImportError(
            f"{symbol} five-minute timestamps are duplicated."
        )

    counts = frame.groupby(
        "session_date"
    ).size()

    if not counts.eq(
        EXPECTED_FIVE_MINUTE_BARS
    ).all():
        raise QuantowerImportError(
            f"Every included {symbol} session must contain "
            "78 five-minute bars."
        )

    for session, group in frame.groupby(
        "session_date",
        sort=True,
    ):
        if not np.array_equal(
            group["slot"].to_numpy(
                dtype=int
            ),
            np.arange(EXPECTED_FIVE_MINUTE_BARS),
        ):
            raise QuantowerImportError(
                f"{symbol} session {session} has bad five-minute slots."
            )

    _validate_ohlcv(
        frame,
        symbol=symbol,
    )


def archive_raw_files(
    records: Iterable[RawFileRecord],
    *,
    raw_root: Path = RAW_ROOT,
) -> tuple[RawFileRecord, ...]:
    archived: list[RawFileRecord] = []

    for record in records:
        source = Path(record.source_path)
        destination_dir = (
            Path(raw_root)
            / record.symbol
        )

        destination_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        destination = (
            destination_dir
            / (
                f"{record.sha256[:16]}_"
                f"{record.filename}"
            )
        )

        if destination.exists():
            if sha256_file(destination) != record.sha256:
                raise QuantowerImportError(
                    "Archived raw file hash conflict: "
                    f"{destination}"
                )
        else:
            temporary = destination.with_suffix(
                destination.suffix + ".tmp"
            )

            shutil.copyfile(
                source,
                temporary,
            )

            if sha256_file(temporary) != record.sha256:
                temporary.unlink(
                    missing_ok=True
                )

                raise QuantowerImportError(
                    "Raw-file archive copy failed hash validation."
                )

            temporary.replace(destination)

        archived.append(
            RawFileRecord(
                **{
                    **record.to_dict(),
                    "archived_path": str(
                        destination.resolve()
                    ),
                }
            )
        )

    return tuple(archived)


def _strict_missing_session_rows(
    expected_sessions: Iterable[date],
    nq: SessionExtraction,
    mnq: SessionExtraction,
) -> pd.DataFrame:
    expected = {
        item.isoformat()
        for item in expected_sessions
    }

    nq_complete = _session_dates(nq.data)
    mnq_complete = _session_dates(mnq.data)

    rows: list[dict[str, Any]] = []

    for session in sorted(expected):
        missing_symbols = [
            symbol
            for symbol, available in (
                ("NQ", nq_complete),
                ("MNQ", mnq_complete),
            )
            if session not in available
        ]

        if missing_symbols:
            rows.append(
                {
                    "symbol": ",".join(
                        missing_symbols
                    ),
                    "session_date": session,
                    "reason": (
                        "expected_full_session_missing_or_incomplete"
                    ),
                    "actual_bars": None,
                    "missing_bars": None,
                    "unexpected_bars": None,
                    "duplicate_bars": None,
                    "median_close_difference": None,
                    "maximum_close_difference": None,
                }
            )

    return pd.DataFrame(
        rows
    )


def build_processed_dataset(
    *,
    nq_paths: Iterable[Path],
    mnq_paths: Iterable[Path],
    qqq_calendar_path: Path = QQQ_CALENDAR_FILE,
    archive_files: bool = True,
) -> ProcessedDataset:
    expected_sessions = load_expected_full_sessions(
        qqq_calendar_path
    )

    nq_import = load_symbol_chunks(
        nq_paths,
        symbol="NQ",
    )

    mnq_import = load_symbol_chunks(
        mnq_paths,
        symbol="MNQ",
    )

    nq = extract_complete_sessions(
        nq_import,
        expected_sessions=expected_sessions,
    )

    mnq = extract_complete_sessions(
        mnq_import,
        expected_sessions=expected_sessions,
    )

    missing_expected = _strict_missing_session_rows(
        expected_sessions,
        nq,
        mnq,
    )

    if not missing_expected.empty:
        preview = ", ".join(
            missing_expected[
                "session_date"
            ].head(10)
        )

        raise IncompleteExportError(
            "The full quick-period export is incomplete. "
            f"{len(missing_expected)} expected full sessions "
            f"are missing from NQ, MNQ or both. First: {preview}. "
            "Re-export the missing date range before importing.",
            missing_sessions=missing_expected,
        )

    aligned = align_nq_mnq(
        nq,
        mnq,
    )

    nq_5m = aggregate_to_five_minutes(
        aligned.nq_1m
    )

    mnq_5m = aggregate_to_five_minutes(
        aligned.mnq_1m
    )

    validate_processed_one_minute(
        aligned.nq_1m,
        symbol="NQ",
    )

    validate_processed_one_minute(
        aligned.mnq_1m,
        symbol="MNQ",
    )

    validate_processed_five_minute(
        nq_5m,
        symbol="NQ",
    )

    validate_processed_five_minute(
        mnq_5m,
        symbol="MNQ",
    )

    if not aligned.nq_1m.index.equals(
        aligned.mnq_1m.index
    ):
        raise AlignmentError(
            "Final NQ and MNQ one-minute timestamps differ."
        )

    if not nq_5m.index.equals(
        mnq_5m.index
    ):
        raise AlignmentError(
            "Final NQ and MNQ five-minute timestamps differ."
        )

    original_records = (
        *nq_import.files,
        *mnq_import.files,
    )

    manifest = (
        archive_raw_files(
            original_records
        )
        if archive_files
        else tuple(original_records)
    )

    excluded_frames = [
        nq.incomplete_sessions,
        mnq.incomplete_sessions,
        nq.unexpected_sessions,
        mnq.unexpected_sessions,
        aligned.excluded_mismatch_sessions,
    ]

    excluded = pd.concat(
        [
            frame
            for frame in excluded_frames
            if not frame.empty
        ],
        axis=0,
        ignore_index=True,
        sort=False,
    ) if any(
        not frame.empty
        for frame in excluded_frames
    ) else pd.DataFrame(
        columns=[
            "symbol",
            "session_date",
            "reason",
        ]
    )

    included_sessions = int(
        aligned.nq_1m[
            "session_date"
        ].nunique()
    )

    audit = {
        "experiment_id": "EXP-005",
        "research_stage": (
            "PRE_REGISTERED_QUICK_DATA_ONLY"
        ),
        "source": (
            "Lucid Trading / Rithmic via Quantower "
            "History Exporter"
        ),
        "symbols": ["NQ", "MNQ"],
        "input_timeframe": "1 minute",
        "output_timeframe": "5 minutes",
        "source_timezone": SOURCE_TZ,
        "research_timezone": NEW_YORK_TZ,
        "quick_start": QUICK_START.isoformat(),
        "quick_end": QUICK_END.isoformat(),
        "confirmation_period_requested": False,
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
        "nq_overlap_rows_deduplicated": (
            nq_import.duplicate_overlap_rows_removed
        ),
        "mnq_overlap_rows_deduplicated": (
            mnq_import.duplicate_overlap_rows_removed
        ),
        "nq_within_file_rows_deduplicated": int(
            sum(
                record.duplicate_rows_removed
                for record in nq_import.files
            )
        ),
        "mnq_within_file_rows_deduplicated": int(
            sum(
                record.duplicate_rows_removed
                for record in mnq_import.files
            )
        ),
        "nq_non_research_conflicting_duplicate_rows_ignored": int(
            sum(
                record.non_research_conflicting_duplicate_rows_removed
                for record in nq_import.files
            )
        ),
        "mnq_non_research_conflicting_duplicate_rows_ignored": int(
            sum(
                record.non_research_conflicting_duplicate_rows_removed
                for record in mnq_import.files
            )
        ),
        "potential_front_month_mismatch_sessions_excluded": int(
            (
                aligned.excluded_mismatch_sessions[
                    "reason"
                ]
                == "potential_front_month_mismatch"
            ).sum()
        ) if not aligned.excluded_mismatch_sessions.empty else 0,
        "included_invalid_sessions": 0,
        "included_front_month_mismatch_sessions": 0,
        "first_included_session": (
            aligned.nq_1m[
                "session_date"
            ].iloc[0]
        ),
        "last_included_session": (
            aligned.nq_1m[
                "session_date"
            ].iloc[-1]
        ),
        "fingerprints": {
            "NQ_1m": dataframe_sha256(
                aligned.nq_1m
            ),
            "MNQ_1m": dataframe_sha256(
                aligned.mnq_1m
            ),
            "NQ_5m": dataframe_sha256(
                nq_5m
            ),
            "MNQ_5m": dataframe_sha256(
                mnq_5m
            ),
        },
    }

    return ProcessedDataset(
        nq_1m=aligned.nq_1m,
        mnq_1m=aligned.mnq_1m,
        nq_5m=nq_5m,
        mnq_5m=mnq_5m,
        manifest=manifest,
        audit=audit,
        excluded_sessions=excluded,
    )
