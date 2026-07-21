from __future__ import annotations

import unittest

import pandas as pd

from exp016_measurements import canonicalize_vendor_frame


class Exp016TimestampSchemaTests(unittest.TestCase):
    def _vendor_schema_frame(self) -> pd.DataFrame:
        timestamps = pd.date_range(
            "2024-11-22 00:00:00",
            periods=3,
            freq="min",
            tz="UTC",
        )
        return pd.DataFrame(
            {
                "ts": timestamps,
                "symbol": ["NQ.F", "NQ.F", "NQ.F"],
                "open": [100.0, 101.0, 102.0],
                "high": [101.0, 102.0, 103.0],
                "low": [99.0, 100.0, 101.0],
                "close": [100.5, 101.5, 102.5],
                "volume": [10.0, 11.0, 12.0],
            }
        )

    def test_timezone_aware_ts_column_is_recognized(self) -> None:
        result = canonicalize_vendor_frame(
            self._vendor_schema_frame()
        )

        self.assertEqual(result.timestamp_source, "ts")
        self.assertTrue(result.timestamp_timezone_aware)
        self.assertEqual(str(result.frame.index.tz), "UTC")
        self.assertEqual(result.duplicate_timestamp_count, 0)
        self.assertEqual(result.invalid_ohlc_rows, 0)
        self.assertEqual(result.negative_volume_rows, 0)

    def test_naive_ts_column_is_not_assumed_utc(self) -> None:
        frame = self._vendor_schema_frame()
        frame["ts"] = frame["ts"].dt.tz_localize(None)

        result = canonicalize_vendor_frame(frame)

        self.assertEqual(result.timestamp_source, "ts")
        self.assertFalse(result.timestamp_timezone_aware)


if __name__ == "__main__":
    unittest.main()
