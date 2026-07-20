from __future__ import annotations

import numpy as np
import pandas as pd

from exp012_engine import Exp012Arrays
from tests.exp009_test_data import make_exp009_arrays


def make_exp012_arrays(session_count: int = 2) -> Exp012Arrays:
    cash = make_exp009_arrays(session_count)
    return Exp012Arrays(
        cash=cash,
        overnight_open=np.full(session_count, 98.0),
        overnight_high=np.full(session_count, 101.0),
        overnight_low=np.full(session_count, 97.0),
        overnight_close=np.full(session_count, 100.0),
        overnight_drive_fraction=np.full(session_count, 0.50),
        overnight_direction=np.ones(session_count, dtype=np.int8),
        premarket_open=np.full(session_count, 99.0),
        premarket_high=np.full(session_count, 101.0),
        premarket_low=np.full(session_count, 98.0),
        premarket_close=np.full(session_count, 100.5),
        premarket_drive_fraction=np.full(session_count, 0.50),
        premarket_direction=np.ones(session_count, dtype=np.int8),
        previous_cash_available=np.ones(session_count, dtype=bool),
        previous_cash_close=np.full(session_count, 98.0),
        previous_cash_range=np.full(session_count, 4.0),
        gap_fraction=np.full(session_count, 0.50),
        gap_direction=np.ones(session_count, dtype=np.int8),
    )


def set_first_cash_bar(
    arrays: Exp012Arrays,
    *,
    opening: float,
    high: float,
    low: float,
    close: float,
    next_open: float,
) -> None:
    arrays.cash.open_5m[:, 0] = opening
    arrays.cash.high_5m[:, 0] = high
    arrays.cash.low_5m[:, 0] = low
    arrays.cash.close_5m[:, 0] = close
    arrays.cash.open_5m[:, 1] = next_open
    arrays.cash.open[:, :5] = opening
    arrays.cash.high[:, :5] = high
    arrays.cash.low[:, :5] = low
    arrays.cash.close[:, :5] = close
    arrays.cash.open[:, 5] = next_open


def make_extended_frame(session_dates: list[str]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for session_number, session_date in enumerate(session_dates):
        base = 100.0 + session_number
        slots = np.arange(1320)
        segment = np.select(
            [
                slots < 360,
                slots < 600,
                slots < 930,
            ],
            ["evening", "overnight", "premarket"],
            default="cash",
        )
        frames.append(
            pd.DataFrame(
                {
                    "open": base,
                    "high": base + 0.25,
                    "low": base - 0.25,
                    "close": base,
                    "volume": 100.0,
                    "session_date": session_date,
                    "session_minute": slots,
                    "segment": segment,
                },
                index=pd.RangeIndex(
                    session_number * 1320,
                    (session_number + 1) * 1320,
                ),
            )
        )
    return pd.concat(frames)
