from __future__ import annotations

from datetime import date
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd

from exp005_quantower_import import (
    QuantowerImportError,
    expected_cash_index,
    read_quantower_csv,
)


def write_csv(
    path: Path,
    index: pd.DatetimeIndex,
) -> None:
    values = (
        9_000.0
        + np.arange(len(index)) * 0.25
    )

    frame = pd.DataFrame(
        {
            "Time left": (
                index.tz_convert("UTC")
                .tz_localize(None)
                .strftime("%Y-%m-%d %H:%M:%S.000")
            ),
            "Time right": (
                (
                    index.tz_convert("UTC")
                    .tz_localize(None)
                    + pd.Timedelta(
                        seconds=59,
                        milliseconds=999,
                    )
                )
                .strftime("%Y-%m-%d %H:%M:%S.%f")
                .str[:-3]
            ),
            "Open": values,
            "High": values + 0.50,
            "Median": values + 0.25,
            "Low": values - 0.50,
            "Close": values + 0.25,
            "Typical": values + 0.0833333333,
            "Volume": np.arange(len(index)) + 1,
            "Quote asset volume": 0,
            "Weighted": values + 0.125,
            "": "",
        }
    )

    frame.to_csv(
        path,
        sep=";",
        index=False,
    )


def duplicate_row(
    raw: pd.DataFrame,
    row_number: int,
    *,
    volume: float,
) -> pd.DataFrame:
    duplicate = raw.iloc[
        [row_number]
    ].copy()

    duplicate.loc[
        duplicate.index[0],
        "Volume",
    ] = volume

    return pd.concat(
        [
            raw,
            duplicate,
        ],
        ignore_index=True,
    )


class Exp005NonResearchDuplicateTests(
    unittest.TestCase
):
    def test_conflicting_duplicate_after_cash_session_is_ignored(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "NQ.csv"

            cash = expected_cash_index(
                date(2020, 1, 17)
            ).tz_convert("UTC")

            outside = pd.DatetimeIndex(
                [
                    pd.Timestamp(
                        "2020-01-17 21:40:00+00:00"
                    )
                ]
            )

            index = cash.append(outside)

            write_csv(
                path,
                index,
            )

            raw = pd.read_csv(
                path,
                sep=";",
            )

            raw = duplicate_row(
                raw,
                len(raw) - 1,
                volume=47,
            )

            raw.to_csv(
                path,
                sep=";",
                index=False,
            )

            frame, record = read_quantower_csv(
                path,
                symbol="NQ",
            )

            self.assertEqual(
                len(frame),
                391,
            )
            self.assertFalse(
                frame.index.has_duplicates
            )
            self.assertEqual(
                record.duplicate_rows_removed,
                1,
            )
            self.assertEqual(
                record
                .non_research_conflicting_duplicate_rows_removed,
                1,
            )

    def test_ohlc_duplicate_during_cash_session_still_stops(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "NQ.csv"

            index = expected_cash_index(
                date(2020, 1, 17)
            ).tz_convert("UTC")

            write_csv(
                path,
                index,
            )

            raw = pd.read_csv(
                path,
                sep=";",
            )

            raw = duplicate_row(
                raw,
                125,
                volume=47,
            )

            raw.loc[
                raw.index[-1],
                "High",
            ] = (
                float(
                    raw.loc[
                        raw.index[-1],
                        "High",
                    ]
                )
                + 0.25
            )

            raw.to_csv(
                path,
                sep=";",
                index=False,
            )

            with self.assertRaisesRegex(
                QuantowerImportError,
                "unresolved research-session OHLC conflict",
            ):
                read_quantower_csv(
                    path,
                    symbol="NQ",
                )


if __name__ == "__main__":
    unittest.main()
