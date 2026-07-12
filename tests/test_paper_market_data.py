from __future__ import annotations

import unittest

import pandas as pd

from paper_market_data import (
    CandleRevisionError,
    merge_without_revisions,
    parse_public_klines,
    validate_hourly_candles,
)


def candle_frame(
    periods: int = 2300,
) -> pd.DataFrame:
    index = pd.date_range(
        "2025-01-01",
        periods=periods,
        freq="h",
    )

    close = pd.Series(
        range(100, 100 + periods),
        index=index,
        dtype=float,
    )

    return pd.DataFrame(
        {
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close + 0.5,
            "volume": 10.0,
            "close_time_ms": 0,
        },
        index=index,
    )


class PaperMarketDataTests(
    unittest.TestCase
):
    def test_parse_public_klines(
        self,
    ) -> None:
        rows = [
            [
                0,
                "100",
                "102",
                "99",
                "101",
                "12",
                3_599_999,
                "0",
                1,
                "0",
                "0",
                "0",
            ]
        ]

        frame = parse_public_klines(rows)

        self.assertEqual(len(frame), 1)
        self.assertEqual(
            float(frame.iloc[0]["close"]),
            101.0,
        )

    def test_valid_contiguous_candles_pass(
        self,
    ) -> None:
        validate_hourly_candles(
            candle_frame()
        )

    def test_gap_is_rejected(
        self,
    ) -> None:
        frame = candle_frame()
        frame = frame.drop(
            frame.index[100]
        )

        with self.assertRaises(
            ValueError
        ):
            validate_hourly_candles(
                frame,
                minimum_rows=2200,
            )

    def test_closed_candle_revision_is_rejected(
        self,
    ) -> None:
        original = candle_frame()
        fetched = original.tail(72).copy()

        fetched.loc[
            fetched.index[0],
            "close",
        ] += 1.0

        with self.assertRaises(
            CandleRevisionError
        ):
            merge_without_revisions(
                original,
                fetched,
            )


if __name__ == "__main__":
    unittest.main()
