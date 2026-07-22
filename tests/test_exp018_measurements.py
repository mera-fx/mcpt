from __future__ import annotations

from datetime import date
import unittest

import numpy as np
import pandas as pd

from exp018_measurements import (
    LoadedArrays,
    audit_arrays,
    canonical_row_hash,
    classify,
    expected_minutes,
)


TICK = 250_000_000


def arrays_for_timestamps(
    timestamps: pd.DatetimeIndex,
    *,
    instrument_id: int = 750,
) -> LoadedArrays:
    rows = len(timestamps)
    base = np.full(rows, 20_000 * 1_000_000_000, dtype="int64")
    return LoadedArrays(
        ts_event=np.asarray(
            [timestamp.value for timestamp in timestamps],
            dtype="uint64",
        ),
        publisher_id=np.ones(rows, dtype="uint16"),
        instrument_id=np.full(rows, instrument_id, dtype="uint32"),
        open=base.copy(),
        high=base + TICK,
        low=base - TICK,
        close=base.copy(),
        volume=np.ones(rows, dtype="uint64"),
    )


class Exp018MeasurementTests(unittest.TestCase):
    def test_dst_changes_utc_session_open_without_timestamp_shift(self) -> None:
        minutes = expected_minutes("2025-03-06", "2025-03-11")
        self.assertIn(pd.Timestamp("2025-03-06T23:00:00Z"), minutes.full_globex)
        self.assertIn(pd.Timestamp("2025-03-09T22:00:00Z"), minutes.full_globex)

    def test_thanksgiving_exceptions_are_locked(self) -> None:
        minutes = expected_minutes("2024-11-28", "2024-11-30")
        thanksgiving_rth = minutes.regular[
            minutes.regular.tz_convert("America/New_York").date
            == date(2024, 11, 28)
        ]
        friday_rth = minutes.regular[
            minutes.regular.tz_convert("America/New_York").date
            == date(2024, 11, 29)
        ]
        self.assertEqual(len(thanksgiving_rth), 0)
        self.assertEqual(len(friday_rth), 210)
        self.assertNotIn(pd.Timestamp("2024-11-28T18:00:00Z"), minutes.full_globex)
        self.assertIn(pd.Timestamp("2024-11-29T18:14:00Z"), minutes.full_globex)
        self.assertNotIn(pd.Timestamp("2024-11-29T18:15:00Z"), minutes.full_globex)

    def test_complete_synthetic_window_passes_structure_and_coverage(self) -> None:
        expected = expected_minutes("2024-02-05", "2024-02-06")
        arrays = arrays_for_timestamps(expected.full_globex)
        result = audit_arrays(
            arrays,
            window_id="synthetic",
            canonical_contract="NQH24",
            raw_symbol="NQH4",
            expected_instrument_id=750,
            start="2024-02-05",
            end_exclusive="2024-02-06",
            raw_sha256="0" * 64,
            size_bytes=123,
        )
        row = result.window
        self.assertEqual(row["identity_mismatch_rows"], 0)
        self.assertEqual(row["duplicate_timestamp_rows"], 0)
        self.assertEqual(row["invalid_ohlc_rows"], 0)
        self.assertEqual(row["off_tick_ohlc_values"], 0)
        self.assertEqual(row["regular_trade_minute_coverage"], 1.0)
        self.assertEqual(row["extended_trade_minute_coverage"], 1.0)

    def test_canonical_hash_is_order_independent(self) -> None:
        timestamps = pd.DatetimeIndex(
            [
                pd.Timestamp("2024-02-05T00:00:00Z"),
                pd.Timestamp("2024-02-05T00:01:00Z"),
            ]
        )
        first = arrays_for_timestamps(timestamps)
        order = np.array([1, 0])
        second = LoadedArrays(
            **{
                field: getattr(first, field)[order]
                for field in (
                    "ts_event",
                    "publisher_id",
                    "instrument_id",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                )
            }
        )
        self.assertEqual(canonical_row_hash(first), canonical_row_hash(second))

    def test_classification_waits_for_repeats(self) -> None:
        rows = []
        for index in range(6):
            rows.append(
                {
                    "identity_mismatch_rows": 0,
                    "timestamp_not_minute_aligned_rows": 0,
                    "duplicate_timestamp_rows": 0,
                    "duplicate_full_rows": 0,
                    "invalid_ohlc_rows": 0,
                    "negative_volume_rows": 0,
                    "nonfinite_ohlcv_rows": 0,
                    "off_tick_ohlc_values": 0,
                    "unexpected_outside_session_minutes": 0,
                    "regular_trade_minute_coverage": 1.0,
                    "extended_trade_minute_coverage": 1.0,
                }
            )
        self.assertEqual(
            classify(
                pd.DataFrame(rows),
                pd.DataFrame(),
                total_estimated_cost_usd=0.30,
            ),
            "REPEATABILITY_PENDING",
        )

    def test_classification_requires_exact_repeatability(self) -> None:
        rows = []
        for index in range(6):
            rows.append(
                {
                    "identity_mismatch_rows": 0,
                    "timestamp_not_minute_aligned_rows": 0,
                    "duplicate_timestamp_rows": 0,
                    "duplicate_full_rows": 0,
                    "invalid_ohlc_rows": 0,
                    "negative_volume_rows": 0,
                    "nonfinite_ohlcv_rows": 0,
                    "off_tick_ohlc_values": 0,
                    "unexpected_outside_session_minutes": 0,
                    "regular_trade_minute_coverage": 1.0,
                    "extended_trade_minute_coverage": 1.0,
                }
            )
        repeat = pd.DataFrame(
            [
                {
                    "minimum_delay_met": True,
                    "canonical_hash_match": True,
                    "row_count_match": True,
                    "timestamp_set_match": True,
                },
                {
                    "minimum_delay_met": True,
                    "canonical_hash_match": False,
                    "row_count_match": True,
                    "timestamp_set_match": True,
                },
            ]
        )
        self.assertEqual(
            classify(
                pd.DataFrame(rows),
                repeat,
                total_estimated_cost_usd=0.40,
            ),
            "REPEATABILITY_FAILED",
        )


if __name__ == "__main__":
    unittest.main()
