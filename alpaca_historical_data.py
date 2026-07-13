from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
import os
from pathlib import Path
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

from intraday_market_foundation import (
    expected_regular_session_index,
)


DATA_BASE_URL = "https://data.alpaca.markets"
PAPER_BASE_URL = "https://paper-api.alpaca.markets"
LIVE_BASE_URL = "https://api.alpaca.markets"


class AlpacaHistoricalDataError(RuntimeError):
    pass


@dataclass(frozen=True)
class CleanSessionData:
    data: pd.DataFrame
    calendar: pd.DataFrame
    excluded_sessions: pd.DataFrame
    audit: dict[str, Any]


def alpaca_headers_from_environment(
) -> dict[str, str]:
    key_id = os.environ.get(
        "APCA_API_KEY_ID",
        "",
    ).strip()

    secret_key = os.environ.get(
        "APCA_API_SECRET_KEY",
        "",
    ).strip()

    if not key_id or not secret_key:
        raise AlpacaHistoricalDataError(
            "Alpaca API credentials are not available. Run "
            "setup_alpaca_credentials.ps1 in PowerShell, then "
            "retry this command."
        )

    return {
        "APCA-API-KEY-ID": key_id,
        "APCA-API-SECRET-KEY": secret_key,
        "Accept": "application/json",
        "User-Agent": "mcpt-exp004-research/1.0",
    }


def _request_json(
    *,
    url: str,
    parameters: dict[str, Any] | None,
    headers: dict[str, str],
    timeout_seconds: int = 60,
    maximum_attempts: int = 4,
) -> Any:
    query = (
        "?" + urlencode(parameters)
        if parameters
        else ""
    )

    full_url = f"{url}{query}"
    failures: list[str] = []

    for attempt in range(
        1,
        maximum_attempts + 1,
    ):
        request = Request(
            full_url,
            headers=headers,
        )

        try:
            with urlopen(
                request,
                timeout=timeout_seconds,
            ) as response:
                payload = json.loads(
                    response.read().decode(
                        "utf-8"
                    )
                )

            return payload
        except HTTPError as error:
            try:
                body = error.read().decode(
                    "utf-8",
                    errors="replace",
                )
            except Exception:
                body = ""

            failures.append(
                f"attempt {attempt}: HTTP "
                f"{error.code} {body[:500]}"
            )

            if error.code in {
                400,
                401,
                403,
                404,
                422,
            }:
                break
        except (
            URLError,
            TimeoutError,
            json.JSONDecodeError,
        ) as error:
            failures.append(
                f"attempt {attempt}: "
                f"{type(error).__name__}: "
                f"{error}"
            )

        if attempt < maximum_attempts:
            time.sleep(
                min(
                    2 ** (attempt - 1),
                    8,
                )
            )

    raise AlpacaHistoricalDataError(
        "Alpaca request failed:\n"
        f"{full_url}\n- "
        + "\n- ".join(failures)
    )


def fetch_stock_bars(
    *,
    symbol: str,
    start: str,
    end: str,
    timeframe: str = "5Min",
    feed: str = "sip",
    adjustment: str = "split",
    limit: int = 10_000,
) -> pd.DataFrame:
    if not 1 <= limit <= 10_000:
        raise ValueError(
            "Alpaca page limit must be "
            "between 1 and 10,000."
        )

    headers = (
        alpaca_headers_from_environment()
    )

    page_token: str | None = None
    rows: list[dict[str, Any]] = []

    while True:
        parameters: dict[str, Any] = {
            "timeframe": timeframe,
            "start": start,
            "end": end,
            "limit": limit,
            "adjustment": adjustment,
            "feed": feed,
            "sort": "asc",
        }

        if page_token:
            parameters[
                "page_token"
            ] = page_token

        payload = _request_json(
            url=(
                f"{DATA_BASE_URL}/v2/stocks/"
                f"{symbol}/bars"
            ),
            parameters=parameters,
            headers=headers,
        )

        if not isinstance(
            payload,
            dict,
        ):
            raise AlpacaHistoricalDataError(
                "Unexpected stock-bar response."
            )

        page_rows = payload.get(
            "bars",
            [],
        )

        if not isinstance(
            page_rows,
            list,
        ):
            raise AlpacaHistoricalDataError(
                "Stock-bar response did not "
                "contain a list of bars."
            )

        rows.extend(page_rows)

        page_token = payload.get(
            "next_page_token"
        )

        if not page_token:
            break

        time.sleep(0.05)

    return parse_stock_bars(rows)


def parse_stock_bars(
    rows: list[dict[str, Any]],
) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(
            columns=[
                "open",
                "high",
                "low",
                "close",
                "volume",
                "trade_count",
                "vwap",
            ],
            index=pd.DatetimeIndex(
                [],
                tz="UTC",
                name="timestamp",
            ),
        )

    frame = pd.DataFrame(rows)

    required = {
        "t",
        "o",
        "h",
        "l",
        "c",
        "v",
    }

    missing = required.difference(
        frame.columns
    )

    if missing:
        raise AlpacaHistoricalDataError(
            "Historical bars are missing "
            f"fields: {sorted(missing)}"
        )

    result = pd.DataFrame(
        {
            "open": pd.to_numeric(
                frame["o"],
                errors="raise",
            ),
            "high": pd.to_numeric(
                frame["h"],
                errors="raise",
            ),
            "low": pd.to_numeric(
                frame["l"],
                errors="raise",
            ),
            "close": pd.to_numeric(
                frame["c"],
                errors="raise",
            ),
            "volume": pd.to_numeric(
                frame["v"],
                errors="raise",
            ),
            "trade_count": pd.to_numeric(
                (
                    frame["n"]
                    if "n" in frame.columns
                    else pd.Series(
                        0,
                        index=frame.index,
                    )
                ),
                errors="coerce",
            ).fillna(0),
            "vwap": pd.to_numeric(
                (
                    frame["vw"]
                    if "vw" in frame.columns
                    else pd.Series(
                        np.nan,
                        index=frame.index,
                    )
                ),
                errors="coerce",
            ),
        }
    )

    result.index = pd.DatetimeIndex(
        pd.to_datetime(
            frame["t"],
            utc=True,
            errors="raise",
        ),
        name="timestamp",
    )

    return result.sort_index()


def fetch_market_calendar(
    *,
    start: str,
    end: str,
) -> pd.DataFrame:
    """
    Fetch the US market calendar with whichever Alpaca credential
    environment the user generated.

    Alpaca paper and live Trading API credentials use different
    hosts. Historical market-data credentials may have been generated
    from either dashboard context, so try paper first and then live.
    """

    headers = (
        alpaca_headers_from_environment()
    )

    configured_base = os.environ.get(
        "APCA_TRADING_BASE_URL",
        "",
    ).strip().rstrip("/")

    base_urls = (
        [configured_base]
        if configured_base
        else [
            PAPER_BASE_URL,
            LIVE_BASE_URL,
        ]
    )

    failures: list[str] = []

    for base_url in base_urls:
        try:
            payload = _request_json(
                url=(
                    f"{base_url}/v2/calendar"
                ),
                parameters={
                    "start": start,
                    "end": end,
                },
                headers=headers,
            )
        except AlpacaHistoricalDataError as error:
            failures.append(
                f"{base_url}: {error}"
            )
            continue

        if not isinstance(payload, list):
            failures.append(
                f"{base_url}: unexpected "
                "market-calendar response"
            )
            continue

        return parse_market_calendar(
            payload
        )

    raise AlpacaHistoricalDataError(
        "Alpaca calendar authentication failed on both the "
        "paper and live Trading API hosts. The saved key and "
        "secret are visible to Python, but they are not accepted "
        "by either matching Trading API environment. Regenerate "
        "an API key pair in the Alpaca dashboard and save both "
        "values from the same key pair.\n- "
        + "\n- ".join(failures)
    )


def parse_market_calendar(
    rows: list[dict[str, Any]],
) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(
            columns=[
                "date",
                "open",
                "close",
                "is_full_session",
            ]
        )

    frame = pd.DataFrame(rows)

    required = {
        "date",
        "open",
        "close",
    }

    missing = required.difference(
        frame.columns
    )

    if missing:
        raise AlpacaHistoricalDataError(
            "Market calendar is missing "
            f"fields: {sorted(missing)}"
        )

    result = frame[
        [
            "date",
            "open",
            "close",
        ]
    ].copy()

    result["date"] = pd.to_datetime(
        result["date"],
        errors="raise",
    ).dt.date

    result["open"] = (
        result["open"]
        .astype(str)
        .str.slice(0, 5)
    )

    result["close"] = (
        result["close"]
        .astype(str)
        .str.slice(0, 5)
    )

    result[
        "is_full_session"
    ] = (
        result["open"].eq("09:30")
        & result["close"].eq("16:00")
    )

    return (
        result.sort_values("date")
        .reset_index(drop=True)
    )


def _validate_ohlc(
    frame: pd.DataFrame,
) -> None:
    prices = frame[
        [
            "open",
            "high",
            "low",
            "close",
        ]
    ].astype(float)

    if not np.isfinite(
        prices.to_numpy()
    ).all():
        raise ValueError(
            "Non-finite prices detected."
        )

    if (prices <= 0).any().any():
        raise ValueError(
            "Prices must be positive."
        )

    invalid_high = (
        prices["high"]
        < prices[
            [
                "open",
                "low",
                "close",
            ]
        ].max(axis=1)
    )

    invalid_low = (
        prices["low"]
        > prices[
            [
                "open",
                "high",
                "close",
            ]
        ].min(axis=1)
    )

    if (
        invalid_high.any()
        or invalid_low.any()
    ):
        raise ValueError(
            "Invalid OHLC relationships "
            "were detected."
        )


def clean_full_regular_sessions(
    *,
    bars: pd.DataFrame,
    calendar: pd.DataFrame,
    start_date: str,
    end_date: str,
    timezone_name: str = (
        "America/New_York"
    ),
) -> CleanSessionData:
    if not isinstance(
        bars.index,
        pd.DatetimeIndex,
    ):
        raise ValueError(
            "Bars must use a DatetimeIndex."
        )

    if bars.index.tz is None:
        raise ValueError(
            "Bar timestamps must be "
            "timezone-aware."
        )

    if bars.index.has_duplicates:
        raise ValueError(
            "Duplicate bar timestamps "
            "were detected."
        )

    _validate_ohlc(bars)

    start_day = pd.Timestamp(
        start_date
    ).date()

    end_day = pd.Timestamp(
        end_date
    ).date()

    calendar_window = calendar[
        calendar["date"].between(
            start_day,
            end_day,
        )
    ].copy()

    full_calendar = (
        calendar_window[
            calendar_window[
                "is_full_session"
            ]
        ].copy()
    )

    early_close_count = int(
        (
            ~calendar_window[
                "is_full_session"
            ]
        ).sum()
    )

    local_bars = bars.copy()
    local_bars.index = (
        local_bars.index.tz_convert(
            timezone_name
        )
    )

    included_frames: list[
        pd.DataFrame
    ] = []

    excluded_rows: list[
        dict[str, Any]
    ] = []

    for session_day in full_calendar[
        "date"
    ]:
        expected = (
            expected_regular_session_index(
                session_day,
                bar_minutes=5,
                timezone_name=(
                    timezone_name
                ),
                session_start="09:30",
                session_end="16:00",
            )
        )

        actual = local_bars[
            local_bars.index.date
            == session_day
        ].copy()

        actual = actual[
            (
                actual.index.time
                >= pd.Timestamp(
                    "09:30"
                ).time()
            )
            & (
                actual.index.time
                < pd.Timestamp(
                    "16:00"
                ).time()
            )
        ]

        missing = expected.difference(
            actual.index
        )

        unexpected = (
            actual.index.difference(
                expected
            )
        )

        duplicate_count = int(
            actual.index.duplicated().sum()
        )

        if (
            len(actual) != 78
            or len(missing)
            or len(unexpected)
            or duplicate_count
        ):
            excluded_rows.append(
                {
                    "session_date": (
                        session_day.isoformat()
                    ),
                    "reason": (
                        "incomplete_or_irregular"
                    ),
                    "actual_bars": int(
                        len(actual)
                    ),
                    "missing_bars": int(
                        len(missing)
                    ),
                    "unexpected_bars": int(
                        len(unexpected)
                    ),
                    "duplicate_bars": (
                        duplicate_count
                    ),
                }
            )

            continue

        actual = actual.reindex(
            expected
        ).copy()

        actual[
            "session_date"
        ] = session_day.isoformat()

        actual["slot"] = np.arange(
            78,
            dtype=int,
        )

        included_frames.append(
            actual
        )

    if not included_frames:
        raise ValueError(
            "No complete full regular "
            "sessions remained."
        )

    clean = pd.concat(
        included_frames,
        axis=0,
    )

    clean.index = clean.index.tz_convert(
        "UTC"
    )

    clean.index.name = "timestamp"

    clean = clean.sort_index()

    validate_exp004_clean_data(
        clean,
        maximum_session_date=(
            end_date
        ),
    )

    excluded = pd.DataFrame(
        excluded_rows,
        columns=[
            "session_date",
            "reason",
            "actual_bars",
            "missing_bars",
            "unexpected_bars",
            "duplicate_bars",
        ],
    )

    audit = {
        "requested_start": (
            start_day.isoformat()
        ),
        "requested_end": (
            end_day.isoformat()
        ),
        "calendar_sessions": int(
            len(calendar_window)
        ),
        "full_calendar_sessions": int(
            len(full_calendar)
        ),
        "early_close_sessions_excluded": (
            early_close_count
        ),
        "incomplete_sessions_excluded": int(
            len(excluded)
        ),
        "included_sessions": int(
            clean[
                "session_date"
            ].nunique()
        ),
        "included_rows": int(
            len(clean)
        ),
        "expected_bars_per_session": 78,
        "included_invalid_sessions": 0,
        "first_included_session": (
            clean[
                "session_date"
            ].iloc[0]
        ),
        "last_included_session": (
            clean[
                "session_date"
            ].iloc[-1]
        ),
    }

    return CleanSessionData(
        data=clean,
        calendar=calendar_window,
        excluded_sessions=excluded,
        audit=audit,
    )


def validate_exp004_clean_data(
    data: pd.DataFrame,
    *,
    maximum_session_date: (
        str | date | None
    ) = None,
) -> None:
    required = {
        "open",
        "high",
        "low",
        "close",
        "volume",
        "session_date",
        "slot",
    }

    missing = required.difference(
        data.columns
    )

    if missing:
        raise ValueError(
            "EXP-004 data is missing "
            f"columns: {sorted(missing)}"
        )

    if not isinstance(
        data.index,
        pd.DatetimeIndex,
    ):
        raise ValueError(
            "EXP-004 data must use a "
            "DatetimeIndex."
        )

    if data.index.tz is None:
        raise ValueError(
            "EXP-004 timestamps must "
            "be timezone-aware."
        )

    if not data.index.is_monotonic_increasing:
        raise ValueError(
            "EXP-004 timestamps are "
            "not increasing."
        )

    if data.index.has_duplicates:
        raise ValueError(
            "Duplicate EXP-004 timestamps "
            "were detected."
        )

    _validate_ohlc(data)

    counts = data.groupby(
        "session_date",
        sort=True,
    ).size()

    if not counts.eq(78).all():
        raise ValueError(
            "Every included EXP-004 "
            "session must contain 78 bars."
        )

    for _, session in data.groupby(
        "session_date",
        sort=True,
    ):
        slots = session[
            "slot"
        ].astype(int).to_numpy()

        if not np.array_equal(
            slots,
            np.arange(78),
        ):
            raise ValueError(
                "Session slot sequence must "
                "be exactly 0 through 77."
            )

    if maximum_session_date is not None:
        maximum = pd.Timestamp(
            maximum_session_date
        ).date()

        observed_maximum = max(
            pd.to_datetime(
                data["session_date"]
            ).dt.date
        )

        if observed_maximum > maximum:
            raise ValueError(
                "EXP-004 data contains "
                "unauthorized future/OOS "
                f"sessions through "
                f"{observed_maximum}."
            )


def atomic_parquet_write(
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
