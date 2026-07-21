from __future__ import annotations

import unittest

import pandas as pd

from exp016_measurements import (
    ALL_WINDOW_IDS,
    OUTSIDE_ROLL_WINDOW_IDS,
    ROLL_WINDOW_IDS,
    canonicalize_vendor_frame,
    classify_audit,
    compare_with_reference,
)


class Exp016MeasurementAlignmentTests(unittest.TestCase):
    def _structural(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "invalid_ohlc_rows": 0,
                    "negative_volume_rows": 0,
                    "nonfinite_ohlcv_rows": 0,
                    "duplicate_timestamp_count": 0,
                    "timestamp_timezone_aware": True,
                }
                for _ in ALL_WINDOW_IDS
            ]
        )

    def _cross(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "window_id": window_id,
                    "comparison_status": "MEASURED",
                    "expected_minute_completeness": 1.0,
                    "matched_timestamp_share": 1.0,
                    "close_within_one_tick_share": 1.0,
                }
                for window_id in ALL_WINDOW_IDS
            ]
        )

    def test_window_partition_is_exact(self) -> None:
        self.assertEqual(len(ALL_WINDOW_IDS), 6)
        self.assertEqual(len(ROLL_WINDOW_IDS), 4)
        self.assertEqual(len(OUTSIDE_ROLL_WINDOW_IDS), 2)
        self.assertFalse(ROLL_WINDOW_IDS & OUTSIDE_ROLL_WINDOW_IDS)
        self.assertEqual(
            ROLL_WINDOW_IDS | OUTSIDE_ROLL_WINDOW_IDS,
            set(ALL_WINDOW_IDS),
        )

    def test_roll_window_close_share_does_not_fail_ordinary_gate(self) -> None:
        cross = self._cross()
        mask = cross["window_id"].eq("2022_june_roll")
        cross.loc[mask, "close_within_one_tick_share"] = 0.0
        self.assertEqual(
            classify_audit(self._structural(), cross),
            "SUPPLEMENTARY_ONLY",
        )

    def test_outside_roll_close_share_below_threshold_fails(self) -> None:
        cross = self._cross()
        mask = cross["window_id"].eq("2021_thanksgiving")
        cross.loc[mask, "close_within_one_tick_share"] = 0.994
        self.assertEqual(
            classify_audit(self._structural(), cross),
            "NOT_QUALIFIED",
        )

    def test_expected_minute_completeness_is_a_separate_gate(self) -> None:
        cross = self._cross()
        cross.loc[0, "expected_minute_completeness"] = 0.998
        self.assertEqual(
            classify_audit(self._structural(), cross),
            "NOT_QUALIFIED",
        )

    def test_matched_timestamp_share_remains_a_separate_gate(self) -> None:
        cross = self._cross()
        cross.loc[0, "matched_timestamp_share"] = 0.998
        self.assertEqual(
            classify_audit(self._structural(), cross),
            "NOT_QUALIFIED",
        )

    def test_missing_or_unknown_window_is_unresolved(self) -> None:
        cross = self._cross()
        cross.loc[0, "window_id"] = "unknown"
        self.assertEqual(
            classify_audit(self._structural(), cross),
            "STRUCTURE_UNRESOLVED",
        )

    def test_all_ohlc_bucket_families_are_reported(self) -> None:
        index = pd.date_range(
            "2024-11-22 00:00:00",
            periods=4,
            freq="min",
            tz="UTC",
        )
        reference = pd.DataFrame(
            {
                "open": [100.0, 100.0, 100.0, 100.0],
                "high": [101.0, 101.0, 101.0, 101.0],
                "low": [99.0, 99.0, 99.0, 99.0],
                "close": [100.0, 100.0, 100.0, 100.0],
                "volume": [10, 10, 10, 10],
            },
            index=index,
        )
        vendor_frame = reference.copy()
        differences = pd.Series(
            [0.0, 0.25, 1.0, 1.25],
            index=index,
        )
        for column in ("open", "high", "low", "close"):
            vendor_frame[column] = vendor_frame[column] + differences

        vendor = canonicalize_vendor_frame(vendor_frame)
        metrics, _ = compare_with_reference(
            vendor=vendor,
            reference=reference,
            start="2024-11-22",
            end="2024-11-22",
            window_id="2024_thanksgiving",
        )

        self.assertEqual(metrics["expected_minute_completeness"], 1.0)
        for column in ("open", "high", "low", "close"):
            self.assertEqual(metrics[f"{column}_diff_exact_rows"], 1)
            self.assertEqual(
                metrics[f"{column}_diff_gt_0_to_0p25_rows"],
                1,
            )
            self.assertEqual(
                metrics[f"{column}_diff_gt_0p25_to_1_rows"],
                1,
            )
            self.assertEqual(metrics[f"{column}_diff_gt_1_rows"], 1)


if __name__ == "__main__":
    unittest.main()
