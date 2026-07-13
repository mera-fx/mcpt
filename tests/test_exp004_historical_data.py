from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from alpaca_historical_data import (
    clean_full_regular_sessions,
    parse_market_calendar,
    parse_stock_bars,
    validate_exp004_clean_data,
)
from intraday_market_foundation import (
    expected_regular_session_index,
)


def api_rows_for_session(
    session_date: str,
) -> list[dict]:
    index = (
        expected_regular_session_index(
            session_date
        )
        .tz_convert("UTC")
    )

    rows = []

    for position, timestamp in (
        enumerate(index)
    ):
        price = 100.0 + position / 100

        rows.append(
            {
                "t": (
                    timestamp.isoformat()
                    .replace(
                        "+00:00",
                        "Z",
                    )
                ),
                "o": price,
                "h": price + 0.2,
                "l": price - 0.2,
                "c": price + 0.05,
                "v": 1000 + position,
                "n": 100,
                "vw": price + 0.02,
            }
        )

    return rows


class Exp004HistoricalDataTests(
    unittest.TestCase
):
    def test_parse_stock_bars(
        self,
    ) -> None:
        frame = parse_stock_bars(
            api_rows_for_session(
                "2022-01-03"
            )[:1]
        )

        self.assertEqual(
            len(frame),
            1,
        )
        self.assertEqual(
            str(frame.index.tz),
            "UTC",
        )
        self.assertAlmostEqual(
            frame.iloc[0]["close"],
            100.05,
        )

    def test_calendar_marks_early_close(
        self,
    ) -> None:
        calendar = (
            parse_market_calendar(
                [
                    {
                        "date": "2022-11-23",
                        "open": "09:30",
                        "close": "16:00",
                    },
                    {
                        "date": "2022-11-25",
                        "open": "09:30",
                        "close": "13:00",
                    },
                ]
            )
        )

        self.assertEqual(
            calendar[
                "is_full_session"
            ].tolist(),
            [True, False],
        )

    def test_complete_session_is_included(
        self,
    ) -> None:
        bars = parse_stock_bars(
            api_rows_for_session(
                "2022-01-03"
            )
        )

        calendar = parse_market_calendar(
            [
                {
                    "date": "2022-01-03",
                    "open": "09:30",
                    "close": "16:00",
                }
            ]
        )

        cleaned = (
            clean_full_regular_sessions(
                bars=bars,
                calendar=calendar,
                start_date="2022-01-03",
                end_date="2022-01-03",
            )
        )

        self.assertEqual(
            len(cleaned.data),
            78,
        )
        self.assertEqual(
            cleaned.audit[
                "included_sessions"
            ],
            1,
        )
        self.assertEqual(
            cleaned.audit[
                "included_invalid_sessions"
            ],
            0,
        )

    def test_missing_bar_session_is_excluded(
        self,
    ) -> None:
        rows = api_rows_for_session(
            "2022-01-03"
        )

        bars = parse_stock_bars(
            rows[:-1]
        )

        complete_rows = (
            api_rows_for_session(
                "2022-01-04"
            )
        )

        bars = pd.concat(
            [
                bars,
                parse_stock_bars(
                    complete_rows
                ),
            ]
        ).sort_index()

        calendar = parse_market_calendar(
            [
                {
                    "date": "2022-01-03",
                    "open": "09:30",
                    "close": "16:00",
                },
                {
                    "date": "2022-01-04",
                    "open": "09:30",
                    "close": "16:00",
                },
            ]
        )

        cleaned = (
            clean_full_regular_sessions(
                bars=bars,
                calendar=calendar,
                start_date="2022-01-03",
                end_date="2022-01-04",
            )
        )

        self.assertEqual(
            cleaned.audit[
                "included_sessions"
            ],
            1,
        )
        self.assertEqual(
            cleaned.audit[
                "incomplete_sessions_excluded"
            ],
            1,
        )

    def test_oos_session_is_rejected(
        self,
    ) -> None:
        bars = parse_stock_bars(
            api_rows_for_session(
                "2023-01-03"
            )
        )

        bars["session_date"] = (
            "2023-01-03"
        )
        bars["slot"] = np.arange(
            78,
            dtype=int,
        )

        with self.assertRaisesRegex(
            ValueError,
            "unauthorized",
        ):
            validate_exp004_clean_data(
                bars,
                maximum_session_date=(
                    "2022-12-30"
                ),
            )


if __name__ == "__main__":
    unittest.main()
