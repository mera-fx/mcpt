from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, time, timedelta
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

from exp006_data import load_exp006_frozen_data


PROJECT_DIR = Path(__file__).resolve().parent
NEW_YORK_TZ = "America/New_York"
SOURCE_TZ = "UTC"

QUICK_MANIFEST = (
    PROJECT_DIR
    / "results"
    / "EXP-005"
    / "data"
    / "quantower_raw_manifest.json"
)
CONFIRMATION_MANIFEST = (
    PROJECT_DIR
    / "results"
    / "EXP-005"
    / "confirmation_data"
    / "quantower_confirmation_raw_manifest.json"
)

EXPECTED_QUICK_MANIFEST_SHA256 = (
    "af8c3c153c14be9784519b9ffe3ecec067d3d6897c78ba2265a4b42c3b183172"
)
EXPECTED_CONFIRMATION_MANIFEST_SHA256 = (
    "cb665a4aedda320b8229e1b44c34d56864d9242b0933f9f43756c2e23703eeb0"
)

OUTPUT_ROOT = (
    PROJECT_DIR
    / "data"
    / "extended_session"
    / "processed"
)
RESULTS_ROOT = (
    PROJECT_DIR
    / "results"
    / "extended_session_data"
)

OUTPUT_FILES = {
    "NQ_1m": OUTPUT_ROOT / "NQ_1m_extended.parquet",
    "MNQ_1m": OUTPUT_ROOT / "MNQ_1m_extended.parquet",
    "NQ_5m": OUTPUT_ROOT / "NQ_5m_extended.parquet",
    "MNQ_5m": OUTPUT_ROOT / "MNQ_5m_extended.parquet",
}
AUDIT_FILE = RESULTS_ROOT / "extended_session_audit.json"
SESSION_QUALITY_FILE = RESULTS_ROOT / "session_quality.csv"
SOURCE_MANIFEST_FILE = RESULTS_ROOT / "source_manifest.json"

REQUIRED_COLUMNS = (
    "Time left",
    "Time right",
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
)
PRICE_COLUMNS = ["open", "high", "low", "close"]
OHLCV_COLUMNS = PRICE_COLUMNS + ["volume"]
TICK_SIZE = 0.25

SESSION_OPEN = time(18, 0)
SESSION_CLOSE = time(17, 0)
CASH_OPEN = time(9, 30)
CASH_CLOSE = time(16, 0)
LEGACY_PAUSE_START = time(16, 15)
LEGACY_PAUSE_END = time(16, 30)
PAUSE_REMOVAL_TRADE_DATE = date(2021, 6, 28)


class ExtendedSessionDataError(RuntimeError):
    pass


@dataclass(frozen=True)
class SourceSpec:
    phase: str
    symbol: str
    role: str
    filename: str
    path: Path
    sha256: str
    size_bytes: int
    primary: bool

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["path"] = str(self.path)
        return value


@dataclass(frozen=True)
class DuplicateStats:
    duplicate_timestamps: int = 0
    exact_ohlcv_resolved: int = 0
    volume_only_resolved: int = 0
    frozen_cash_ohlc_resolved: int = 0

    def __add__(self, other: DuplicateStats) -> DuplicateStats:
        return DuplicateStats(
            duplicate_timestamps=(
                self.duplicate_timestamps
                + other.duplicate_timestamps
            ),
            exact_ohlcv_resolved=(
                self.exact_ohlcv_resolved
                + other.exact_ohlcv_resolved
            ),
            volume_only_resolved=(
                self.volume_only_resolved
                + other.volume_only_resolved
            ),
            frozen_cash_ohlc_resolved=(
                self.frozen_cash_ohlc_resolved
                + other.frozen_cash_ohlc_resolved
            ),
        )


@dataclass(frozen=True)
class FallbackStats:
    rows_added: int = 0
    overlap_rows_ignored: int = 0
    overlap_price_disagreements: int = 0

    def __add__(self, other: FallbackStats) -> FallbackStats:
        return FallbackStats(
            rows_added=self.rows_added + other.rows_added,
            overlap_rows_ignored=(
                self.overlap_rows_ignored
                + other.overlap_rows_ignored
            ),
            overlap_price_disagreements=(
                self.overlap_price_disagreements
                + other.overlap_price_disagreements
            ),
        )


@dataclass(frozen=True)
class ExtendedSessionBuild:
    nq_1m: pd.DataFrame
    mnq_1m: pd.DataFrame
    nq_5m: pd.DataFrame
    mnq_5m: pd.DataFrame
    session_quality: pd.DataFrame
    source_specs: tuple[SourceSpec, ...]
    source_diagnostics: dict[str, Any]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(block)
    return digest.hexdigest()


def _load_json(path: Path) -> Any:
    return json.loads(
        Path(path).read_text(encoding="utf-8")
    )


def _manifest_records(
    path: Path,
    *,
    expected_sha256: str,
    phase: str,
) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(
            f"Frozen {phase} raw manifest is missing: {path}"
        )
    if sha256_file(path) != expected_sha256:
        raise ExtendedSessionDataError(
            f"Frozen {phase} raw manifest hash changed."
        )

    value = _load_json(path)
    if isinstance(value, dict):
        records = value.get("files")
    else:
        records = value

    if not isinstance(records, list) or not records:
        raise ExtendedSessionDataError(
            f"Frozen {phase} raw manifest has no files."
        )
    return records


def _local_archived_path(
    *,
    phase: str,
    symbol: str,
    sha256: str,
    filename: str,
) -> Path:
    root = (
        PROJECT_DIR
        / "data"
        / "EXP-005"
    )
    if phase == "confirmation":
        root = root / "confirmation"
    return (
        root
        / "raw"
        / symbol
        / f"{sha256[:16]}_{filename}"
    )


def load_source_specs(
    *,
    verify_files: bool = True,
) -> tuple[SourceSpec, ...]:
    manifests = (
        (
            "quick",
            QUICK_MANIFEST,
            EXPECTED_QUICK_MANIFEST_SHA256,
        ),
        (
            "confirmation",
            CONFIRMATION_MANIFEST,
            EXPECTED_CONFIRMATION_MANIFEST_SHA256,
        ),
    )
    raw_records: list[tuple[str, dict[str, Any]]] = []

    for phase, path, digest in manifests:
        for record in _manifest_records(
            path,
            expected_sha256=digest,
            phase=phase,
        ):
            raw_records.append((phase, record))

    usable_roles = {
        "FULL_EXPORT",
        "CONFIRMATION_SESSION_RETRY",
    }
    candidates = [
        (phase, record)
        for phase, record in raw_records
        if record.get("source_role") in usable_roles
    ]

    largest_full: dict[tuple[str, str], int] = {}
    for phase, record in candidates:
        if record.get("source_role") != "FULL_EXPORT":
            continue
        key = (phase, str(record["symbol"]).upper())
        largest_full[key] = max(
            largest_full.get(key, 0),
            int(record["size_bytes"]),
        )

    specs: list[SourceSpec] = []
    for phase, record in candidates:
        symbol = str(record["symbol"]).upper()
        role = str(record["source_role"])
        digest = str(record["sha256"]).lower()
        filename = str(record["filename"])
        size_bytes = int(record["size_bytes"])
        path = _local_archived_path(
            phase=phase,
            symbol=symbol,
            sha256=digest,
            filename=filename,
        )
        primary = (
            role == "FULL_EXPORT"
            and size_bytes
            == largest_full[(phase, symbol)]
        )
        spec = SourceSpec(
            phase=phase,
            symbol=symbol,
            role=role,
            filename=filename,
            path=path,
            sha256=digest,
            size_bytes=size_bytes,
            primary=primary,
        )
        if verify_files:
            if not path.exists():
                raise FileNotFoundError(
                    f"Archived source file is missing: {path}"
                )
            if int(path.stat().st_size) != size_bytes:
                raise ExtendedSessionDataError(
                    f"Archived source size changed: {path.name}"
                )
            if sha256_file(path) != digest:
                raise ExtendedSessionDataError(
                    f"Archived source hash changed: {path.name}"
                )
        specs.append(spec)

    for phase in ("quick", "confirmation"):
        for symbol in ("NQ", "MNQ"):
            matches = [
                item
                for item in specs
                if (
                    item.phase == phase
                    and item.symbol == symbol
                    and item.primary
                )
            ]
            if len(matches) != 1:
                raise ExtendedSessionDataError(
                    f"{phase} {symbol} must have one primary export."
                )

    return tuple(
        sorted(
            specs,
            key=lambda item: (
                item.symbol,
                item.phase,
                not item.primary,
                item.filename.lower(),
            ),
        )
    )


def load_frozen_cash_frames(
) -> dict[str, pd.DataFrame]:
    frozen = load_exp006_frozen_data()
    output: dict[str, pd.DataFrame] = {}
    for symbol, frame in (
        ("NQ", frozen.nq_1m),
        ("MNQ", frozen.mnq_1m),
    ):
        local = frame.copy()
        local.index = pd.to_datetime(
            local.index,
            utc=True,
        )
        local = local.sort_index()
        local["session_date"] = (
            local["session_date"].astype(str)
        )
        output[symbol] = local

    if not output["NQ"].index.equals(
        output["MNQ"].index
    ):
        raise ExtendedSessionDataError(
            "Frozen NQ/MNQ cash timestamps are not aligned."
        )
    return output


def _drop_blank_columns(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    keep: list[str] = []
    for column in frame.columns:
        name = str(column).strip()
        if not name:
            continue
        if (
            name.lower().startswith("unnamed")
            and frame[column].isna().all()
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
        raise ExtendedSessionDataError(
            f"{symbol} source contains no rows."
        )
    values = frame[OHLCV_COLUMNS].astype(float)
    if not np.isfinite(values.to_numpy()).all():
        raise ExtendedSessionDataError(
            f"{symbol} source contains non-finite OHLCV."
        )
    prices = values[PRICE_COLUMNS]
    if (prices <= 0).any().any():
        raise ExtendedSessionDataError(
            f"{symbol} source contains non-positive prices."
        )
    if (values["volume"] < 0).any():
        raise ExtendedSessionDataError(
            f"{symbol} source contains negative volume."
        )
    invalid_high = (
        prices["high"]
        < prices[["open", "low", "close"]].max(axis=1)
    )
    invalid_low = (
        prices["low"]
        > prices[["open", "high", "close"]].min(axis=1)
    )
    if invalid_high.any() or invalid_low.any():
        raise ExtendedSessionDataError(
            f"{symbol} source contains invalid OHLC relationships."
        )
    scaled = prices.to_numpy() / TICK_SIZE
    if not np.allclose(
        scaled,
        np.round(scaled),
        atol=1e-8,
        rtol=0.0,
    ):
        raise ExtendedSessionDataError(
            f"{symbol} source contains off-tick prices."
        )


def _matching_frozen_cash_row(
    frozen_cash: pd.DataFrame,
    timestamp: pd.Timestamp,
) -> pd.Series | None:
    if timestamp not in frozen_cash.index:
        return None
    row = frozen_cash.loc[timestamp]
    if isinstance(row, pd.DataFrame):
        raise ExtendedSessionDataError(
            "Frozen cash data contains duplicate timestamps."
        )
    return row


def deduplicate_source_rows(
    frame: pd.DataFrame,
    *,
    symbol: str,
    source_name: str,
    frozen_cash: pd.DataFrame,
) -> tuple[pd.DataFrame, DuplicateStats]:
    if not frame.index.has_duplicates:
        return frame.sort_index(), DuplicateStats()

    duplicate_mask = frame.index.duplicated(
        keep=False
    )
    pieces: list[pd.DataFrame] = [
        frame.loc[~duplicate_mask]
    ]
    stats = DuplicateStats()

    for timestamp, group in frame.loc[
        duplicate_mask
    ].groupby(
        level=0,
        sort=True,
    ):
        unique_ohlcv = (
            group[OHLCV_COLUMNS]
            .astype(float)
            .drop_duplicates()
        )
        unique_ohlc = (
            group[PRICE_COLUMNS]
            .astype(float)
            .drop_duplicates()
        )
        current = DuplicateStats(
            duplicate_timestamps=1,
        )

        if len(unique_ohlcv) == 1:
            selected = group.iloc[[0]]
            current = current + DuplicateStats(
                exact_ohlcv_resolved=1,
            )
        elif len(unique_ohlc) == 1:
            maximum_volume = float(
                group["volume"].max()
            )
            selected = group.loc[
                group["volume"].astype(float)
                == maximum_volume
            ].iloc[[0]]
            current = current + DuplicateStats(
                volume_only_resolved=1,
            )
        else:
            frozen = _matching_frozen_cash_row(
                frozen_cash,
                pd.Timestamp(timestamp),
            )
            if frozen is None:
                raise ExtendedSessionDataError(
                    f"{symbol} unresolved extended-session OHLC "
                    f"conflict in {source_name} at "
                    f"{pd.Timestamp(timestamp).isoformat()}."
                )
            target = frozen[PRICE_COLUMNS].astype(float).to_numpy()
            prices = group[PRICE_COLUMNS].astype(float).to_numpy()
            matches = np.all(
                np.isclose(
                    prices,
                    target,
                    atol=1e-12,
                    rtol=0.0,
                ),
                axis=1,
            )
            if not matches.any():
                raise ExtendedSessionDataError(
                    f"{symbol} source conflict does not contain "
                    "the frozen cash bar at "
                    f"{pd.Timestamp(timestamp).isoformat()}."
                )
            candidates = group.loc[matches]
            maximum_volume = float(
                candidates["volume"].max()
            )
            selected = candidates.loc[
                candidates["volume"].astype(float)
                == maximum_volume
            ].iloc[[0]]
            current = current + DuplicateStats(
                frozen_cash_ohlc_resolved=1,
            )

        pieces.append(selected)
        stats = stats + current

    result = pd.concat(pieces).sort_index()
    if result.index.has_duplicates:
        raise ExtendedSessionDataError(
            f"{symbol} duplicate resolution failed for {source_name}."
        )
    return result, stats


def read_quantower_source(
    path: Path,
    *,
    symbol: str,
    frozen_cash: pd.DataFrame,
) -> tuple[pd.DataFrame, DuplicateStats]:
    raw = pd.read_csv(
        path,
        sep=";",
        engine="c",
        low_memory=False,
    )
    raw = _drop_blank_columns(raw)
    missing = set(REQUIRED_COLUMNS).difference(raw.columns)
    if missing:
        raise ExtendedSessionDataError(
            f"{path.name} is missing columns: {sorted(missing)}"
        )

    left = pd.to_datetime(
        raw["Time left"],
        errors="raise",
    )
    right = pd.to_datetime(
        raw["Time right"],
        errors="raise",
    )
    if left.dt.tz is not None or right.dt.tz is not None:
        raise ExtendedSessionDataError(
            "Quantower timestamps must be naive UTC clock values."
        )

    index = pd.DatetimeIndex(left).tz_localize(SOURCE_TZ)
    right_index = pd.DatetimeIndex(right).tz_localize(SOURCE_TZ)
    expected_right = (
        index
        + pd.Timedelta(seconds=59, milliseconds=999)
    )
    if not right_index.equals(expected_right):
        raise ExtendedSessionDataError(
            f"{path.name} does not contain exact one-minute intervals."
        )

    frame = pd.DataFrame(
        {
            "open": pd.to_numeric(
                raw["Open"],
                errors="raise",
            ).to_numpy(),
            "high": pd.to_numeric(
                raw["High"],
                errors="raise",
            ).to_numpy(),
            "low": pd.to_numeric(
                raw["Low"],
                errors="raise",
            ).to_numpy(),
            "close": pd.to_numeric(
                raw["Close"],
                errors="raise",
            ).to_numpy(),
            "volume": pd.to_numeric(
                raw["Volume"],
                errors="raise",
            ).to_numpy(),
        },
        index=index,
    )
    frame.index.name = "timestamp"
    frame, stats = deduplicate_source_rows(
        frame,
        symbol=symbol,
        source_name=path.name,
        frozen_cash=frozen_cash,
    )
    _validate_ohlcv(frame, symbol=symbol)
    return frame, stats


def merge_primary_frames(
    frames: Sequence[pd.DataFrame],
    *,
    symbol: str,
    frozen_cash: pd.DataFrame,
) -> pd.DataFrame:
    if not frames:
        raise ExtendedSessionDataError(
            f"No primary {symbol} frames were provided."
        )
    combined = pd.concat(frames).sort_index()
    if combined.index.has_duplicates:
        combined, _ = deduplicate_source_rows(
            combined,
            symbol=symbol,
            source_name="primary export overlap",
            frozen_cash=frozen_cash,
        )
    _validate_ohlcv(combined, symbol=symbol)
    return combined


def add_fallback_rows(
    primary: pd.DataFrame,
    fallback: pd.DataFrame,
) -> tuple[pd.DataFrame, FallbackStats]:
    overlap = primary.index.intersection(
        fallback.index
    )
    disagreement_count = 0
    if len(overlap):
        left = (
            primary.loc[overlap, PRICE_COLUMNS]
            .astype(float)
            .to_numpy()
        )
        right = (
            fallback.loc[overlap, PRICE_COLUMNS]
            .astype(float)
            .to_numpy()
        )
        same = np.all(
            np.isclose(
                left,
                right,
                atol=1e-12,
                rtol=0.0,
            ),
            axis=1,
        )
        disagreement_count = int((~same).sum())

    additions = fallback.loc[
        fallback.index.difference(primary.index)
    ]
    result = pd.concat(
        [primary, additions]
    ).sort_index()
    return result, FallbackStats(
        rows_added=int(len(additions)),
        overlap_rows_ignored=int(len(overlap)),
        overlap_price_disagreements=disagreement_count,
    )


def overlay_frozen_cash(
    frame: pd.DataFrame,
    frozen_cash: pd.DataFrame,
) -> pd.DataFrame:
    cash = frozen_cash[OHLCV_COLUMNS].copy()
    base = frame.drop(
        index=frame.index.intersection(cash.index)
    )
    result = pd.concat([base, cash]).sort_index()
    if result.index.has_duplicates:
        raise ExtendedSessionDataError(
            "Frozen cash overlay created duplicate timestamps."
        )
    actual = result.loc[cash.index, OHLCV_COLUMNS]
    if not np.allclose(
        actual.astype(float).to_numpy(),
        cash.astype(float).to_numpy(),
        atol=1e-12,
        rtol=0.0,
    ):
        raise ExtendedSessionDataError(
            "Frozen cash overlay parity failed."
        )
    return result


def expected_session_index(
    trade_date: date,
) -> pd.DatetimeIndex:
    previous = trade_date - timedelta(days=1)
    start = pd.Timestamp(
        f"{previous.isoformat()} 18:00:00",
        tz=NEW_YORK_TZ,
    )
    end = pd.Timestamp(
        f"{trade_date.isoformat()} 17:00:00",
        tz=NEW_YORK_TZ,
    )
    index = pd.date_range(
        start=start,
        end=end,
        freq="1min",
        inclusive="left",
    )
    if trade_date < PAUSE_REMOVAL_TRADE_DATE:
        local_times = index.time
        keep = ~(
            (local_times >= LEGACY_PAUSE_START)
            & (local_times < LEGACY_PAUSE_END)
        )
        index = index[keep]
    return index.tz_convert(SOURCE_TZ)


def session_segment(
    timestamp: pd.Timestamp,
) -> str:
    local = timestamp.tz_convert(NEW_YORK_TZ)
    value = local.time()
    if value >= SESSION_OPEN:
        return "evening"
    if value < time(4, 0):
        return "overnight"
    if value < CASH_OPEN:
        return "premarket"
    if value < CASH_CLOSE:
        return "cash"
    return "post_cash"


def session_segments(
    index: pd.DatetimeIndex,
) -> np.ndarray:
    local = index.tz_convert(NEW_YORK_TZ)
    minutes = (
        local.hour.to_numpy(dtype=np.int16) * 60
        + local.minute.to_numpy(dtype=np.int16)
    )
    return np.select(
        [
            minutes >= 18 * 60,
            minutes < 4 * 60,
            minutes < 9 * 60 + 30,
            minutes < 16 * 60,
        ],
        [
            "evening",
            "overnight",
            "premarket",
            "cash",
        ],
        default="post_cash",
    )


def build_expected_calendar(
    session_dates: Iterable[date],
) -> pd.DataFrame:
    pieces: list[pd.DataFrame] = []
    for trade_date in sorted(set(session_dates)):
        index = expected_session_index(trade_date)
        pieces.append(
            pd.DataFrame(
                {
                    "session_date": trade_date.isoformat(),
                    "session_minute": np.arange(
                        len(index),
                        dtype=np.int32,
                    ),
                    "segment": session_segments(index),
                },
                index=index,
            )
        )
    if not pieces:
        raise ExtendedSessionDataError(
            "No frozen session dates were provided."
        )
    result = pd.concat(pieces).sort_index()
    result.index.name = "timestamp"
    if result.index.has_duplicates:
        raise ExtendedSessionDataError(
            "Expected extended-session calendar overlaps."
        )
    return result


def _load_symbol_sources(
    *,
    symbol: str,
    specs: Sequence[SourceSpec],
    frozen_cash: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    selected = [
        item
        for item in specs
        if item.symbol == symbol
    ]
    primary_frames: list[pd.DataFrame] = []
    fallback_frames: list[tuple[SourceSpec, pd.DataFrame]] = []
    duplicate_stats = DuplicateStats()

    for spec in selected:
        frame, current_stats = read_quantower_source(
            spec.path,
            symbol=symbol,
            frozen_cash=frozen_cash,
        )
        duplicate_stats = duplicate_stats + current_stats
        if spec.primary:
            primary_frames.append(frame)
        else:
            fallback_frames.append((spec, frame))

    combined = merge_primary_frames(
        primary_frames,
        symbol=symbol,
        frozen_cash=frozen_cash,
    )
    fallback_stats = FallbackStats()
    fallback_details: list[dict[str, Any]] = []
    for spec, frame in fallback_frames:
        combined, current = add_fallback_rows(
            combined,
            frame,
        )
        fallback_stats = fallback_stats + current
        fallback_details.append(
            {
                "phase": spec.phase,
                "role": spec.role,
                "filename": spec.filename,
                **asdict(current),
            }
        )

    combined = overlay_frozen_cash(
        combined,
        frozen_cash,
    )
    return combined, {
        "duplicate_resolution": asdict(duplicate_stats),
        "fallback_resolution": asdict(fallback_stats),
        "fallback_files": fallback_details,
        "rows_after_cash_overlay": int(len(combined)),
    }


def measure_session_quality(
    *,
    calendar: pd.DataFrame,
    nq: pd.DataFrame,
    mnq: pd.DataFrame,
) -> pd.DataFrame:
    presence = calendar[["session_date"]].copy()
    presence["nq_present"] = presence.index.isin(
        nq.index
    )
    presence["mnq_present"] = presence.index.isin(
        mnq.index
    )
    presence["common_present"] = (
        presence["nq_present"]
        & presence["mnq_present"]
    )
    quality = (
        presence.groupby("session_date", sort=True)
        .agg(
            expected_rows=("nq_present", "size"),
            nq_rows=("nq_present", "sum"),
            mnq_rows=("mnq_present", "sum"),
            common_rows=("common_present", "sum"),
        )
        .reset_index()
    )
    for column in (
        "expected_rows",
        "nq_rows",
        "mnq_rows",
        "common_rows",
    ):
        quality[column] = quality[column].astype(int)
    quality["nq_missing_rows"] = (
        quality["expected_rows"] - quality["nq_rows"]
    )
    quality["mnq_missing_rows"] = (
        quality["expected_rows"] - quality["mnq_rows"]
    )
    quality["common_missing_rows"] = (
        quality["expected_rows"] - quality["common_rows"]
    )
    quality["legacy_pause_expected"] = [
        date.fromisoformat(value)
        < PAUSE_REMOVAL_TRADE_DATE
        for value in quality["session_date"]
    ]
    quality["complete_aligned"] = (
        quality["nq_rows"].eq(quality["expected_rows"])
        & quality["mnq_rows"].eq(quality["expected_rows"])
        & quality["common_rows"].eq(
            quality["expected_rows"]
        )
    )
    return quality


def _materialize_complete_rows(
    *,
    source: pd.DataFrame,
    calendar: pd.DataFrame,
    included_dates: set[str],
) -> pd.DataFrame:
    selected_calendar = calendar.loc[
        calendar["session_date"].isin(included_dates)
    ]
    result = source.reindex(
        selected_calendar.index
    )[OHLCV_COLUMNS]
    if result.isna().any().any():
        raise ExtendedSessionDataError(
            "Included extended session contains missing OHLCV."
        )
    result = result.join(selected_calendar)
    result.index.name = "timestamp"
    return result


def aggregate_active_five_minute(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    local = frame.copy()
    local["timestamp"] = frame.index
    local["active_5m_bar"] = (
        local["session_minute"].astype(int) // 5
    )
    grouped = local.groupby(
        ["session_date", "active_5m_bar"],
        sort=True,
    )
    counts = grouped.size()
    if not counts.eq(5).all():
        raise ExtendedSessionDataError(
            "Extended active-time five-minute aggregation "
            "encountered a non-five-minute group."
        )

    output = grouped.agg(
        timestamp=("timestamp", "first"),
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
        session_minute=("session_minute", "first"),
        segment=("segment", "first"),
    )
    group_keys = output.index.to_list()
    output.index = pd.DatetimeIndex(
        output.pop("timestamp")
    )
    output.index.name = "timestamp"
    output["session_date"] = [
        item[0]
        for item in group_keys
    ]
    output["active_5m_bar"] = [
        int(item[1])
        for item in group_keys
    ]
    return output[
        OHLCV_COLUMNS
        + [
            "session_date",
            "session_minute",
            "active_5m_bar",
            "segment",
        ]
    ].sort_index()


def verify_cash_parity(
    *,
    extended: pd.DataFrame,
    frozen_cash: pd.DataFrame,
) -> None:
    actual = extended.loc[
        extended["segment"].eq("cash"),
        OHLCV_COLUMNS,
    ]
    expected = frozen_cash.loc[
        frozen_cash.index.isin(actual.index),
        OHLCV_COLUMNS,
    ]
    if not actual.index.equals(expected.index):
        raise ExtendedSessionDataError(
            "Extended cash timestamps do not match frozen cash."
        )
    if not np.allclose(
        actual.astype(float).to_numpy(),
        expected.astype(float).to_numpy(),
        atol=1e-12,
        rtol=0.0,
    ):
        raise ExtendedSessionDataError(
            "Extended cash OHLCV changed from frozen data."
        )


def build_extended_session_dataset(
    *,
    verify_source_files: bool = True,
) -> ExtendedSessionBuild:
    specs = load_source_specs(
        verify_files=verify_source_files,
    )
    frozen_cash = load_frozen_cash_frames()
    session_dates = {
        date.fromisoformat(value)
        for value in frozen_cash["NQ"][
            "session_date"
        ].unique()
    }
    calendar = build_expected_calendar(session_dates)

    nq_raw, nq_diagnostics = _load_symbol_sources(
        symbol="NQ",
        specs=specs,
        frozen_cash=frozen_cash["NQ"],
    )
    mnq_raw, mnq_diagnostics = _load_symbol_sources(
        symbol="MNQ",
        specs=specs,
        frozen_cash=frozen_cash["MNQ"],
    )
    quality = measure_session_quality(
        calendar=calendar,
        nq=nq_raw,
        mnq=mnq_raw,
    )
    included_dates = set(
        quality.loc[
            quality["complete_aligned"],
            "session_date",
        ]
    )
    if not included_dates:
        raise ExtendedSessionDataError(
            "No complete aligned extended sessions were found."
        )

    nq_1m = _materialize_complete_rows(
        source=nq_raw,
        calendar=calendar,
        included_dates=included_dates,
    )
    mnq_1m = _materialize_complete_rows(
        source=mnq_raw,
        calendar=calendar,
        included_dates=included_dates,
    )
    if not nq_1m.index.equals(mnq_1m.index):
        raise ExtendedSessionDataError(
            "Final NQ/MNQ extended timestamps are not aligned."
        )
    verify_cash_parity(
        extended=nq_1m,
        frozen_cash=frozen_cash["NQ"],
    )
    verify_cash_parity(
        extended=mnq_1m,
        frozen_cash=frozen_cash["MNQ"],
    )
    nq_5m = aggregate_active_five_minute(nq_1m)
    mnq_5m = aggregate_active_five_minute(mnq_1m)
    if not nq_5m.index.equals(mnq_5m.index):
        raise ExtendedSessionDataError(
            "Final NQ/MNQ five-minute timestamps are not aligned."
        )

    return ExtendedSessionBuild(
        nq_1m=nq_1m,
        mnq_1m=mnq_1m,
        nq_5m=nq_5m,
        mnq_5m=mnq_5m,
        session_quality=quality,
        source_specs=specs,
        source_diagnostics={
            "NQ": nq_diagnostics,
            "MNQ": mnq_diagnostics,
        },
    )


def write_extended_session_dataset(
    build: ExtendedSessionBuild,
) -> dict[str, Any]:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    RESULTS_ROOT.mkdir(parents=True, exist_ok=True)

    frames = {
        "NQ_1m": build.nq_1m,
        "MNQ_1m": build.mnq_1m,
        "NQ_5m": build.nq_5m,
        "MNQ_5m": build.mnq_5m,
    }
    for name, frame in frames.items():
        frame.to_parquet(OUTPUT_FILES[name])

    build.session_quality.to_csv(
        SESSION_QUALITY_FILE,
        index=False,
        lineterminator="\n",
    )
    source_payload = {
        "schema_version": 1,
        "purpose": (
            "Immutable source inventory for the derived "
            "NQ/MNQ extended-session dataset."
        ),
        "quick_manifest_sha256": (
            EXPECTED_QUICK_MANIFEST_SHA256
        ),
        "confirmation_manifest_sha256": (
            EXPECTED_CONFIRMATION_MANIFEST_SHA256
        ),
        "files": [
            item.to_dict()
            for item in build.source_specs
        ],
    }
    SOURCE_MANIFEST_FILE.write_text(
        json.dumps(
            source_payload,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    included = build.session_quality.loc[
        build.session_quality["complete_aligned"]
    ]
    output_files = {
        name: {
            "path": str(path.resolve()),
            "sha256": sha256_file(path),
            "rows": int(len(frames[name])),
        }
        for name, path in OUTPUT_FILES.items()
    }
    audit = {
        "schema_version": 1,
        "dataset": "NQ/MNQ extended-session data foundation",
        "source": (
            "Frozen EXP-005 Quantower raw exports plus "
            "frozen EXP-005 cash-session overlays"
        ),
        "strategy_results_calculated": False,
        "optimization_calculated": False,
        "mcpt_calculated": False,
        "source_files_edited": False,
        "cash_session_data_changed": False,
        "expected_schedule": {
            "timezone": NEW_YORK_TZ,
            "session_open": "18:00 previous calendar day",
            "session_close": "17:00 trade date",
            "legacy_pause": "16:15-16:30",
            "legacy_pause_last_trade_date": (
                PAUSE_REMOVAL_TRADE_DATE
                - timedelta(days=1)
            ).isoformat(),
            "pause_removed_from_trade_date": (
                PAUSE_REMOVAL_TRADE_DATE.isoformat()
            ),
            "minutes_before_pause_removal": 1365,
            "minutes_after_pause_removal": 1380,
        },
        "frozen_cash_sessions_considered": int(
            len(build.session_quality)
        ),
        "complete_aligned_sessions": int(len(included)),
        "excluded_incomplete_sessions": int(
            len(build.session_quality) - len(included)
        ),
        "first_included_session": str(
            included["session_date"].min()
        ),
        "last_included_session": str(
            included["session_date"].max()
        ),
        "source_diagnostics": build.source_diagnostics,
        "outputs": output_files,
        "session_quality": {
            "path": str(SESSION_QUALITY_FILE.resolve()),
            "sha256": sha256_file(SESSION_QUALITY_FILE),
        },
        "source_manifest": {
            "path": str(SOURCE_MANIFEST_FILE.resolve()),
            "sha256": sha256_file(SOURCE_MANIFEST_FILE),
        },
    }
    AUDIT_FILE.write_text(
        json.dumps(
            audit,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return audit
