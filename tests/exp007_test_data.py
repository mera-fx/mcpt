from __future__ import annotations

import numpy as np
import pandas as pd


def make_exp007_one_minute_data(
    session_dates: list[str],
    *,
    outcomes: list[str] | None = None,
) -> pd.DataFrame:
    if outcomes is None:
        outcomes = ["target"] * len(session_dates)
    if len(outcomes) != len(session_dates):
        raise ValueError("outcomes must match session_dates")

    frames: list[pd.DataFrame] = []
    for session_number, (session_date, outcome) in enumerate(
        zip(session_dates, outcomes)
    ):
        local_index = pd.date_range(
            start=(
                pd.Timestamp(session_date, tz="America/New_York")
                + pd.Timedelta(hours=9, minutes=30)
            ),
            periods=390,
            freq="min",
        )
        base = 100.0 + session_number * 10.0
        open_values = np.full(390, base)
        close_values = np.full(390, base)
        high_values = np.full(390, base + 0.25)
        low_values = np.full(390, base - 0.25)

        # Opening range: high +1, low -1.
        high_values[:30] = base + 1.0
        low_values[:30] = base - 1.0

        if outcome != "no_signal":
            # First eligible 5-minute signal is the 10:00-10:05 bar.
            close_values[34] = base + 1.5
            high_values[34] = base + 1.6
            open_values[35] = base + 1.5
            close_values[35] = base + 1.5
            high_values[35] = base + 1.75
            low_values[35] = base + 1.25

            stop = base - 1.0
            target = base + 4.0
            if outcome == "target":
                high_values[36] = target + 0.5
                low_values[36] = base + 1.25
            elif outcome == "stop":
                low_values[36] = stop - 0.25
                high_values[36] = base + 1.75
            elif outcome == "both":
                low_values[36] = stop - 0.25
                high_values[36] = target + 0.5
            elif outcome == "gap_stop":
                open_values[36] = stop - 0.5
                close_values[36] = stop - 0.5
                high_values[36] = stop - 0.25
                low_values[36] = stop - 0.75
            elif outcome == "time":
                open_values[270] = base + 2.0
                close_values[270] = base + 2.0
                high_values[270] = base + 2.25
                low_values[270] = base + 1.75
            else:
                raise ValueError(f"Unknown outcome: {outcome}")

        frame = pd.DataFrame(
            {
                "open": open_values,
                "high": high_values,
                "low": low_values,
                "close": close_values,
                "volume": np.arange(390, dtype=float) + 1.0,
                "session_date": session_date,
                "minute_slot": np.arange(390, dtype=int),
            },
            index=local_index.tz_convert("UTC"),
        )
        frames.append(frame)

    result = pd.concat(frames).sort_index()
    result.index.name = "timestamp"
    return result
