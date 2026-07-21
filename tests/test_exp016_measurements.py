from __future__ import annotations

import unittest

import pandas as pd

from exp016_measurements import (
    canonicalize_vendor_frame,
    classify_audit,
    compare_with_reference,
)


class Exp016MeasurementTests(unittest.TestCase):
    def _frame(self, *, tz: str | None = "UTC") -> pd.DataFrame:
        index = pd.date_range(
            "2024-11-22 00:00:00",
            periods=3,
            freq="min",
            tz=tz,
        )
        return pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0],
                "high": [101.0, 102.0, 103.0],
                "low": [99.0, 100.0, 101.0],
                "close": [100.5, 101.5, 102.5],
                "volume": [10, 11, 12],
            },
            index=index,
        )

    def test_timezone_aware_frame_is_preserved(self) -> None:
        result = canonicalize_vendor_frame(self._frame())
        self.assertTrue(result.timestamp_timezone_aware)
        self.assertEqual(result.duplicate_timestamp_count, 0)
        self.assertEqual(result.invalid_ohlc_rows, 0)

    def test_naive_timestamp_is_not_assumed_utc(self) -> None:
        result = canonicalize_vendor_frame(self._frame(tz=None))
        self.assertFalse(result.timestamp_timezone_aware)

    def test_duplicates_are_measured_not_removed_silently(self) -> None:
        frame = self._frame()
        frame = pd.concat([frame, frame.iloc[[0]]])
        result = canonicalize_vendor_frame(frame)
        self.assertEqual(result.duplicate_timestamp_count, 2)
        self.assertEqual(len(result.frame), 4)

    def test_invalid_ohlc_is_measured(self) -> None:
        frame = self._frame()
        frame.iloc[0, frame.columns.get_loc("high")] = 98.0
        result = canonicalize_vendor_frame(frame)
        self.assertEqual(result.invalid_ohlc_rows, 1)

    def test_exact_comparison_matches_all_rows(self) -> None:
        frame = self._frame()
        vendor = canonicalize_vendor_frame(frame)
        metrics, detail = compare_with_reference(
            vendor=vendor,
            reference=frame,
            start="2024-11-22",
            end="2024-11-22",
            window_id="example",
        )
        self.assertEqual(metrics["matched_rows"], 3)
        self.assertEqual(metrics["vendor_only_rows"], 0)
        self.assertEqual(metrics["quantower_only_rows"], 0)
        self.assertEqual(metrics["matched_timestamp_share"], 1.0)
        self.assertEqual(metrics["close_within_one_tick_share"], 1.0)
        self.assertEqual(len(detail), 3)

    def test_naive_timestamps_block_cross_source_matching(self) -> None:
        vendor = canonicalize_vendor_frame(self._frame(tz=None))
        metrics, detail = compare_with_reference(
            vendor=vendor,
            reference=self._frame(),
            start="2024-11-22",
            end="2024-11-22",
            window_id="example",
        )
        self.assertEqual(
            metrics["comparison_status"],
            "TIMESTAMP_TIMEZONE_UNRESOLVED",
        )
        self.assertTrue(detail.empty)

    def test_methodology_caps_good_measurements_at_supplementary(self) -> None:
        structural = pd.DataFrame(
            [
                {
                    "invalid_ohlc_rows": 0,
                    "negative_volume_rows": 0,
                    "nonfinite_ohlcv_rows": 0,
                    "duplicate_timestamp_count": 0,
                    "timestamp_timezone_aware": True,
                }
                for _ in range(6)
            ]
        )
        cross = pd.DataFrame(
            [
                {
                    "comparison_status": "MEASURED",
                    "matched_timestamp_share": 1.0,
                    "close_within_one_tick_share": 1.0,
                }
                for _ in range(6)
            ]
        )
        self.assertEqual(
            classify_audit(structural, cross),
            "SUPPLEMENTARY_ONLY",
        )
