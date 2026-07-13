from __future__ import annotations

import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from alpaca_historical_data import (
    AlpacaHistoricalDataError,
    clean_full_regular_sessions,
    fetch_market_calendar,
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

    def test_calendar_falls_back_from_paper_to_live(
        self,
    ) -> None:
        response = [
            {
                "date": "2022-01-03",
                "open": "09:30",
                "close": "16:00",
            }
        ]

        with patch(
            "alpaca_historical_data."
            "alpaca_headers_from_environment",
            return_value={
                "APCA-API-KEY-ID": "test",
                "APCA-API-SECRET-KEY": "test",
            },
        ), patch(
            "alpaca_historical_data._request_json",
            side_effect=[
                AlpacaHistoricalDataError(
                    "paper rejected credentials"
                ),
                response,
            ],
        ) as request_json:
            calendar = fetch_market_calendar(
                start="2022-01-03",
                end="2022-01-03",
            )

        self.assertEqual(
            len(calendar),
            1,
        )

        self.assertEqual(
            request_json.call_count,
            2,
        )

        self.assertIn(
            "paper-api.alpaca.markets",
            request_json.call_args_list[
                0
            ].kwargs["url"],
        )

        self.assertIn(
            "api.alpaca.markets",
            request_json.call_args_list[
                1
            ].kwargs["url"],
        )

    def test_calendar_reports_both_auth_failures(
        self,
    ) -> None:
        with patch(
            "alpaca_historical_data."
            "alpaca_headers_from_environment",
            return_value={
                "APCA-API-KEY-ID": "test",
                "APCA-API-SECRET-KEY": "test",
            },
        ), patch(
            "alpaca_historical_data._request_json",
            side_effect=AlpacaHistoricalDataError(
                "HTTP 401"
            ),
        ):
            with self.assertRaisesRegex(
                AlpacaHistoricalDataError,
                "both the paper and live",
            ):
                fetch_market_calendar(
                    start="2022-01-03",
                    end="2022-01-03",
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
