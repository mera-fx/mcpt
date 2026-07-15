from __future__ import annotations

import numpy as np
import pandas as pd


def make_five_minute_data(
    session_dates: list[str],
    *,
    pattern: str = "alternating",
) -> pd.DataFrame:
    frames = []
    for session_number, session_date in enumerate(
        session_dates
    ):
        local_index = pd.date_range(
            start=(
                pd.Timestamp(
                    session_date,
                    tz="America/New_York",
                )
                + pd.Timedelta(
                    hours=9,
                    minutes=30,
                )
            ),
            periods=78,
            freq="5min",
        )
        base = 100.0 + session_number * 0.25
        open_values = np.full(78, base)
        close_values = np.full(78, base)
        high_values = np.full(78, base + 1.0)
        low_values = np.full(78, base - 1.0)

        direction = (
            1
            if pattern == "long"
            or (
                pattern == "alternating"
                and session_number % 2 == 0
            )
            else -1
        )
        if direction == 1:
            close_values[3] = base + 1.5
            high_values[3] = base + 1.75
            low_values[3] = base - 0.25
            open_values[4:] = base + 1.5
            close_values[4:] = base + 3.0
            high_values[4:] = base + 3.25
            low_values[4:] = base + 1.25
            open_values[77] = base + 3.0
        else:
            close_values[3] = base - 1.5
            high_values[3] = base + 0.25
            low_values[3] = base - 1.75
            open_values[4:] = base - 1.5
            close_values[4:] = base - 3.0
            high_values[4:] = base - 1.25
            low_values[4:] = base - 3.25
            open_values[77] = base - 3.0

        frame = pd.DataFrame(
            {
                "open": open_values,
                "high": high_values,
                "low": low_values,
                "close": close_values,
                "volume": np.arange(78) + 1,
                "session_date": session_date,
                "slot": np.arange(78),
            },
            index=local_index.tz_convert("UTC"),
        )
        frames.append(frame)

    result = pd.concat(frames).sort_index()
    result.index.name = "timestamp"
    return result


def make_one_minute_data(
    session_dates: list[str],
) -> pd.DataFrame:
    frames = []
    for session_number, session_date in enumerate(
        session_dates
    ):
        local_index = pd.date_range(
            start=(
                pd.Timestamp(
                    session_date,
                    tz="America/New_York",
                )
                + pd.Timedelta(
                    hours=9,
                    minutes=30,
                )
            ),
            periods=390,
            freq="min",
        )
        base = 100.0 + session_number
        movement = np.sin(
            np.linspace(0, 8, 390)
        ) * 0.05
        open_values = base + movement
        close_values = open_values + 0.01
        high_values = np.maximum(
            open_values,
            close_values,
        ) + 0.02
        low_values = np.minimum(
            open_values,
            close_values,
        ) - 0.02
        frames.append(
            pd.DataFrame(
                {
                    "open": open_values,
                    "high": high_values,
                    "low": low_values,
                    "close": close_values,
                    "volume": np.arange(390) + 1,
                    "session_date": session_date,
                    "minute_slot": np.arange(390),
                },
                index=local_index.tz_convert("UTC"),
            )
        )
    result = pd.concat(frames).sort_index()
    result.index.name = "timestamp"
    return result
