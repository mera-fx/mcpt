from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd


# ============================================================
# SETTINGS — these are the parts you will normally edit
# ============================================================

SYMBOL = "BTCUSDT"
INTERVAL = "1h"
START_DATE = "2017-01-01"

OUTPUT_FILE = Path("data/BTCUSDT_1h.parquet")

# Binance's public market-data-only endpoint.
BASE_URL = "https://data-api.binance.vision/api/v3/klines"

# Binance allows up to 1,000 candles per request.
LIMIT = 1000


INTERVAL_MILLISECONDS = {
    "1m": 60_000,
    "3m": 3 * 60_000,
    "5m": 5 * 60_000,
    "15m": 15 * 60_000,
    "30m": 30 * 60_000,
    "1h": 60 * 60_000,
    "2h": 2 * 60 * 60_000,
    "4h": 4 * 60 * 60_000,
    "6h": 6 * 60 * 60_000,
    "8h": 8 * 60 * 60_000,
    "12h": 12 * 60 * 60_000,
    "1d": 24 * 60 * 60_000,
}


def date_to_milliseconds(date_text: str) -> int:
    """Convert a YYYY-MM-DD date into a UTC Unix timestamp."""
    date = datetime.strptime(date_text, "%Y-%m-%d")
    date = date.replace(tzinfo=timezone.utc)
    return int(date.timestamp() * 1000)


def last_completed_bar_time(interval_ms: int) -> int:
    """
    Return the final millisecond before the currently forming candle.

    This prevents incomplete live candles from entering a backtest.
    """
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    current_bar_start = now_ms - (now_ms % interval_ms)
    return current_bar_start - 1


def request_klines(start_ms: int, end_ms: int) -> list:
    """Download one page of candles from Binance."""
    parameters = {
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "startTime": start_ms,
        "endTime": end_ms,
        "limit": LIMIT,
    }

    url = f"{BASE_URL}?{urlencode(parameters)}"
    request = Request(url, headers={"User-Agent": "TradingResearchLab/1.0"})

    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    except HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Binance returned HTTP {error.code}: {body}"
        ) from error

    except URLError as error:
        raise RuntimeError(
            f"Could not connect to Binance: {error.reason}"
        ) from error


def download_all_klines() -> list:
    """Download all candles, automatically handling pagination."""
    if INTERVAL not in INTERVAL_MILLISECONDS:
        raise ValueError(f"Unsupported interval: {INTERVAL}")

    interval_ms = INTERVAL_MILLISECONDS[INTERVAL]
    next_start_ms = date_to_milliseconds(START_DATE)
    end_ms = last_completed_bar_time(interval_ms)

    all_rows = []
    page_number = 0

    print(f"Downloading {SYMBOL} {INTERVAL} candles...")
    print(f"Start date: {START_DATE}")
    print()

    while next_start_ms <= end_ms:
        rows = request_klines(next_start_ms, end_ms)

        if not rows:
            break

        page_number += 1
        all_rows.extend(rows)

        last_open_ms = int(rows[-1][0])
        last_date = datetime.fromtimestamp(
            last_open_ms / 1000,
            tz=timezone.utc,
        )

        print(
            f"Page {page_number:>3}: "
            f"{len(rows):>4} candles | "
            f"through {last_date:%Y-%m-%d %H:%M} UTC"
        )

        new_start_ms = last_open_ms + interval_ms

        # Safety check against an accidental infinite loop.
        if new_start_ms <= next_start_ms:
            raise RuntimeError("The download cursor did not move forward.")

        next_start_ms = new_start_ms

        # Be polite to the public API.
        time.sleep(0.1)

    return all_rows


def rows_to_dataframe(rows: list) -> pd.DataFrame:
    """Convert Binance's raw response into clean research data."""
    if not rows:
        raise RuntimeError("No market data was downloaded.")

    columns = [
        "open_time",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time",
        "quote_volume",
        "number_of_trades",
        "taker_buy_volume",
        "taker_buy_quote_volume",
        "ignore",
    ]

    df = pd.DataFrame(rows, columns=columns)

    numeric_columns = [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "quote_volume",
        "taker_buy_volume",
        "taker_buy_quote_volume",
    ]

    df[numeric_columns] = df[numeric_columns].astype(float)
    df["number_of_trades"] = df["number_of_trades"].astype(int)

    # Store timestamps as timezone-naive UTC for compatibility
    # with the existing MCPT repository.
    df["timestamp"] = pd.to_datetime(
        df["open_time"],
        unit="ms",
        utc=True,
    ).dt.tz_localize(None)

    df = df.set_index("timestamp")

    useful_columns = [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "quote_volume",
        "number_of_trades",
        "taker_buy_volume",
        "taker_buy_quote_volume",
    ]

    df = df[useful_columns]
    df = df[~df.index.duplicated(keep="first")]
    df = df.sort_index()

    return df


def check_data(df: pd.DataFrame) -> None:
    """Run basic checks before trusting and saving the dataset."""
    if df.empty:
        raise RuntimeError("The resulting dataset is empty.")

    if df.index.has_duplicates:
        raise RuntimeError("Duplicate timestamps remain in the data.")

    if not df.index.is_monotonic_increasing:
        raise RuntimeError("Timestamps are not in chronological order.")

    expected_difference = pd.Timedelta(INTERVAL)
    differences = df.index.to_series().diff()
    gaps = differences[differences > expected_difference]

    print()
    print("Data checks")
    print("-----------")
    print(f"Rows:       {len(df):,}")
    print(f"First bar:  {df.index.min()} UTC")
    print(f"Last bar:   {df.index.max()} UTC")
    print(f"Duplicates: {df.index.duplicated().sum()}")
    print(f"Gaps:       {len(gaps)}")

    if len(gaps) > 0:
        print()
        print("Warning: gaps were detected.")
        print("The first few occur at:")
        print(gaps.head())


def main() -> None:
    rows = download_all_klines()
    df = rows_to_dataframe(rows)
    check_data(df)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUTPUT_FILE, engine="pyarrow")

    print()
    print(f"Saved successfully: {OUTPUT_FILE.resolve()}")


if __name__ == "__main__":
    main()