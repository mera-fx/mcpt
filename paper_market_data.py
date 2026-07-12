from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd


ONE_HOUR_MS = 60 * 60 * 1000

PUBLIC_API_BASES = (
    "https://api.binance.com",
    "https://data-api.binance.vision",
    "https://api1.binance.com",
    "https://api2.binance.com",
    "https://api3.binance.com",
)


class PublicMarketDataError(RuntimeError):
    pass


class CandleRevisionError(PublicMarketDataError):
    pass


@dataclass(frozen=True)
class MarketDataUpdate:
    data: pd.DataFrame
    server_time_utc: str
    source_base_url: str
    rows_before: int
    rows_after: int
    new_rows: int


def _request_json(
    *,
    path: str,
    parameters: dict[str, Any] | None = None,
    preferred_base: str | None = None,
    timeout_seconds: int = 30,
) -> tuple[Any, str]:
    bases = list(PUBLIC_API_BASES)

    if preferred_base in bases:
        bases.remove(preferred_base)
        bases.insert(0, preferred_base)

    query = (
        "?" + urlencode(parameters)
        if parameters
        else ""
    )

    failures: list[str] = []

    for base_url in bases:
        url = f"{base_url}{path}{query}"

        request = Request(
            url,
            headers={
                "User-Agent": (
                    "mcpt-exp003-paper-simulator/1.0"
                ),
                "Accept": "application/json",
            },
        )

        try:
            with urlopen(
                request,
                timeout=timeout_seconds,
            ) as response:
                payload = json.loads(
                    response.read().decode("utf-8")
                )

            return payload, base_url
        except (
            HTTPError,
            URLError,
            TimeoutError,
            json.JSONDecodeError,
        ) as error:
            failures.append(
                f"{base_url}: {type(error).__name__}: {error}"
            )

    raise PublicMarketDataError(
        "All public market-data endpoints failed:\n- "
        + "\n- ".join(failures)
    )


def get_public_server_time(
) -> tuple[int, str]:
    payload, base_url = _request_json(
        path="/api/v3/time",
    )

    if (
        not isinstance(payload, dict)
        or "serverTime" not in payload
    ):
        raise PublicMarketDataError(
            "Unexpected public server-time response."
        )

    return int(payload["serverTime"]), base_url


def parse_public_klines(
    rows: list[list[Any]],
) -> pd.DataFrame:
    columns = [
        "open_time_ms",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time_ms",
        "quote_volume",
        "trade_count",
        "taker_buy_base_volume",
        "taker_buy_quote_volume",
        "ignore",
    ]

    if not rows:
        return pd.DataFrame(
            columns=[
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time_ms",
            ]
        )

    frame = pd.DataFrame(
        rows,
        columns=columns,
    )

    numeric_columns = [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time_ms",
    ]

    for column in numeric_columns:
        frame[column] = pd.to_numeric(
            frame[column],
            errors="raise",
        )

    index = pd.to_datetime(
        frame["open_time_ms"],
        unit="ms",
        utc=True,
    ).dt.tz_localize(None)

    result = frame[
        [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time_ms",
        ]
    ].copy()

    result.index = pd.DatetimeIndex(
        index,
        name="timestamp",
    )

    return result.sort_index()


def fetch_closed_hourly_klines(
    *,
    symbol: str = "BTCUSDT",
    start_time: pd.Timestamp | None = None,
    history_bars: int = 3000,
) -> tuple[pd.DataFrame, int, str]:
    if history_bars < 2300:
        raise ValueError(
            "history_bars must be at least 2300 "
            "for the locked EXP-003 indicators."
        )

    server_time_ms, base_url = (
        get_public_server_time()
    )

    latest_closed_open_ms = (
        server_time_ms
        // ONE_HOUR_MS
        * ONE_HOUR_MS
        - ONE_HOUR_MS
    )

    if start_time is None:
        start_ms = (
            latest_closed_open_ms
            - (history_bars - 1) * ONE_HOUR_MS
        )
    else:
        start_timestamp = pd.Timestamp(
            start_time
        )

        if start_timestamp.tzinfo is not None:
            start_timestamp = (
                start_timestamp.tz_convert("UTC")
                .tz_localize(None)
            )

        start_ms = int(
            start_timestamp.timestamp() * 1000
        )

    cursor = max(0, start_ms)
    all_rows: list[list[Any]] = []

    while cursor <= latest_closed_open_ms:
        payload, base_url = _request_json(
            path="/api/v3/klines",
            parameters={
                "symbol": symbol,
                "interval": "1h",
                "startTime": cursor,
                "endTime": (
                    latest_closed_open_ms
                    + ONE_HOUR_MS
                    - 1
                ),
                "limit": 1000,
            },
            preferred_base=base_url,
        )

        if not isinstance(payload, list):
            raise PublicMarketDataError(
                "Unexpected public kline response."
            )

        if not payload:
            break

        all_rows.extend(payload)

        last_open_ms = int(payload[-1][0])
        next_cursor = (
            last_open_ms + ONE_HOUR_MS
        )

        if next_cursor <= cursor:
            raise PublicMarketDataError(
                "Public kline pagination did not advance."
            )

        cursor = next_cursor

        if len(payload) < 1000:
            break

        time.sleep(0.05)

    frame = parse_public_klines(
        all_rows
    )

    if frame.empty:
        raise PublicMarketDataError(
            "No closed hourly candles were returned."
        )

    frame = frame[
        frame["close_time_ms"]
        < server_time_ms
    ]

    latest_closed_timestamp = pd.to_datetime(
        latest_closed_open_ms,
        unit="ms",
    )

    frame = frame.loc[
        frame.index <= latest_closed_timestamp
    ]

    frame = frame[
        ~frame.index.duplicated(
            keep="last"
        )
    ].sort_index()

    return frame, server_time_ms, base_url


def validate_hourly_candles(
    data: pd.DataFrame,
    *,
    minimum_rows: int = 2300,
) -> None:
    required = {
        "open",
        "high",
        "low",
        "close",
    }

    missing = required.difference(
        data.columns
    )

    if missing:
        raise ValueError(
            f"Missing candle columns: {sorted(missing)}"
        )

    if len(data) < minimum_rows:
        raise ValueError(
            f"At least {minimum_rows} candles are required; "
            f"received {len(data)}."
        )

    if not data.index.is_monotonic_increasing:
        raise ValueError(
            "Candle timestamps are not increasing."
        )

    if data.index.has_duplicates:
        raise ValueError(
            "Duplicate candle timestamps were detected."
        )

    prices = data[
        ["open", "high", "low", "close"]
    ].astype(float)

    if not np.isfinite(
        prices.to_numpy()
    ).all():
        raise ValueError(
            "Non-finite candle prices were detected."
        )

    if (prices <= 0).any().any():
        raise ValueError(
            "Candle prices must be positive."
        )

    invalid_high = (
        prices["high"]
        < prices[
            ["open", "close", "low"]
        ].max(axis=1)
    )

    invalid_low = (
        prices["low"]
        > prices[
            ["open", "close", "high"]
        ].min(axis=1)
    )

    if invalid_high.any() or invalid_low.any():
        raise ValueError(
            "Invalid OHLC relationships were detected."
        )

    differences = (
        data.index.to_series().diff().dropna()
    )

    bad_gaps = differences[
        differences != pd.Timedelta(hours=1)
    ]

    if not bad_gaps.empty:
        first_gap = bad_gaps.index[0]

        raise ValueError(
            "Missing or irregular hourly candles detected "
            f"near {first_gap}."
        )


def merge_without_revisions(
    existing: pd.DataFrame,
    fetched: pd.DataFrame,
) -> pd.DataFrame:
    if existing.empty:
        return fetched.copy()

    overlap = existing.index.intersection(
        fetched.index
    )

    compare_columns = [
        column
        for column in (
            "open",
            "high",
            "low",
            "close",
            "volume",
        )
        if (
            column in existing.columns
            and column in fetched.columns
        )
    ]

    if len(overlap) and compare_columns:
        old_values = (
            existing.loc[
                overlap,
                compare_columns,
            ]
            .astype(float)
            .to_numpy()
        )

        new_values = (
            fetched.loc[
                overlap,
                compare_columns,
            ]
            .astype(float)
            .to_numpy()
        )

        equal = np.isclose(
            old_values,
            new_values,
            rtol=1e-10,
            atol=1e-12,
            equal_nan=True,
        )

        if not bool(equal.all()):
            locations = np.argwhere(
                ~equal
            )

            row_number, column_number = (
                locations[0]
            )

            timestamp = overlap[
                row_number
            ]

            column = compare_columns[
                column_number
            ]

            raise CandleRevisionError(
                "A previously stored closed candle changed: "
                f"{timestamp} column={column}."
            )

    combined = pd.concat(
        [existing, fetched],
        axis=0,
    )

    return (
        combined[
            ~combined.index.duplicated(
                keep="last"
            )
        ]
        .sort_index()
    )


def _atomic_parquet_write(
    data: pd.DataFrame,
    path: Path,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    data.to_parquet(temporary)
    temporary.replace(path)


def update_public_hourly_data(
    *,
    destination: Path,
    symbol: str = "BTCUSDT",
    initial_history_bars: int = 3000,
    overlap_bars: int = 72,
) -> MarketDataUpdate:
    if destination.exists():
        existing = pd.read_parquet(
            destination
        )

        existing.index = pd.to_datetime(
            existing.index
        )

        existing = existing.sort_index()

        rows_before = len(existing)

        fetch_start = (
            existing.index[-1]
            - pd.Timedelta(
                hours=overlap_bars - 1
            )
        )
    else:
        existing = pd.DataFrame()
        rows_before = 0
        fetch_start = None

    fetched, server_time_ms, base_url = (
        fetch_closed_hourly_klines(
            symbol=symbol,
            start_time=fetch_start,
            history_bars=initial_history_bars,
        )
    )

    combined = merge_without_revisions(
        existing,
        fetched,
    )

    validate_hourly_candles(
        combined,
        minimum_rows=2300,
    )

    _atomic_parquet_write(
        combined,
        destination,
    )

    server_time = datetime.fromtimestamp(
        server_time_ms / 1000,
        tz=timezone.utc,
    ).isoformat(
        timespec="seconds"
    )

    return MarketDataUpdate(
        data=combined,
        server_time_utc=server_time,
        source_base_url=base_url,
        rows_before=rows_before,
        rows_after=len(combined),
        new_rows=max(
            0,
            len(combined) - rows_before,
        ),
    )
