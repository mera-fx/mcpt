from __future__ import annotations

import numpy as np
import pandas as pd

from exp009_engine import Exp009Arrays


def make_exp009_arrays(session_count: int = 1) -> Exp009Arrays:
    minute_shape = (session_count, 390)
    five_shape = (session_count, 78)
    dates = pd.date_range("2024-01-02", periods=session_count, freq="D")
    return Exp009Arrays(
        session_dates=dates.strftime("%Y-%m-%d").to_numpy(),
        years=dates.year.to_numpy(dtype=int),
        open=np.full(minute_shape, 100.0),
        high=np.full(minute_shape, 100.25),
        low=np.full(minute_shape, 99.75),
        close=np.full(minute_shape, 100.0),
        volume=np.full(minute_shape, 100.0),
        open_5m=np.full(five_shape, 100.0),
        high_5m=np.full(five_shape, 100.25),
        low_5m=np.full(five_shape, 99.75),
        close_5m=np.full(five_shape, 100.0),
        volume_5m=np.full(five_shape, 500.0),
        vwap_5m=np.full(five_shape, 100.0),
        vwap_std_5m=np.full(five_shape, 1.0),
    )


def set_opening_range(
    arrays: Exp009Arrays,
    *,
    high: float = 101.0,
    low: float = 99.0,
) -> None:
    arrays.high[:, :30] = high
    arrays.low[:, :30] = low
    arrays.high_5m[:, :6] = high
    arrays.low_5m[:, :6] = low


def make_exp009_one_minute_data(
    session_dates: list[str],
) -> pd.DataFrame:
    frames = []
    for session_number, session_date in enumerate(session_dates):
        base = 100.0 + session_number
        index = pd.date_range(
            pd.Timestamp(session_date, tz="America/New_York")
            + pd.Timedelta(hours=9, minutes=30),
            periods=390,
            freq="min",
        ).tz_convert("UTC")
        frames.append(
            pd.DataFrame(
                {
                    "open": base,
                    "high": base + 0.25,
                    "low": base - 0.25,
                    "close": base,
                    "volume": 100.0,
                    "session_date": session_date,
                    "minute_slot": np.arange(390),
                },
                index=index,
            )
        )
    return pd.concat(frames).sort_index()
