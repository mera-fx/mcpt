from __future__ import annotations

from datetime import date
import unittest

import numpy as np
import pandas as pd

from extended_session_data import (
    ExtendedSessionDataError,
    add_fallback_rows,
    aggregate_active_five_minute,
    build_expected_calendar,
    deduplicate_source_rows,
    expected_session_index,
    overlay_frozen_cash,
    session_segment,
)


def _frame(
    timestamps: list[str],
    closes: list[float],
    *,
    volumes: list[float] | None = None,
) -> pd.DataFrame:
    if volumes is None:
        volumes = [100.0] * len(timestamps)
    values = np.asarray(closes, dtype=float)
    return pd.DataFrame(
        {
            "open": values,
            "high": values + 0.25,
            "low": values - 0.25,
            "close": values,
            "volume": volumes,
        },
        index=pd.DatetimeIndex(
            pd.to_datetime(timestamps, utc=True)
        ),
    )


class ExtendedSessionCalendarTests(unittest.TestCase):
    def test_legacy_session_has_1365_minutes(self) -> None:
        index = expected_session_index(
            date(2021, 6, 25)
        )
        self.assertEqual(len(index), 1365)
        local = index.tz_convert(
            "America/New_York"
        )
        self.assertNotIn(
            pd.Timestamp(
                "2021-06-25 16:15",
                tz="America/New_York",
            ),
            local,
        )

    def test_pause_removed_session_has_1380_minutes(self) -> None:
        index = expected_session_index(
            date(2021, 6, 28)
        )
        self.assertEqual(len(index), 1380)
        local = index.tz_convert(
            "America/New_York"
        )
        self.assertIn(
            pd.Timestamp(
                "2021-06-28 16:15",
                tz="America/New_York",
            ),
            local,
        )

    def test_calendar_handles_new_york_daylight_saving(self) -> None:
        winter = expected_session_index(
            date(2021, 1, 11)
        )
        summer = expected_session_index(
            date(2021, 7, 12)
        )
        self.assertEqual(
            winter[0].hour,
            23,
        )
        self.assertEqual(
            summer[0].hour,
            22,
        )

    def test_session_segments_are_readable(self) -> None:
        values = {
            "2025-01-05 23:00+00:00": "evening",
            "2025-01-06 07:00+00:00": "overnight",
            "2025-01-06 10:00+00:00": "premarket",
            "2025-01-06 15:00+00:00": "cash",
            "2025-01-06 21:30+00:00": "post_cash",
        }
        for stamp, expected in values.items():
            with self.subTest(stamp=stamp):
                self.assertEqual(
                    session_segment(pd.Timestamp(stamp)),
                    expected,
                )


class ExtendedSessionNormalizationTests(unittest.TestCase):
    def test_volume_only_duplicate_keeps_maximum(self) -> None:
        frame = _frame(
            [
                "2025-01-06 15:00+00:00",
                "2025-01-06 15:00+00:00",
            ],
            [100.0, 100.0],
            volumes=[10.0, 25.0],
        )
        result, stats = deduplicate_source_rows(
            frame,
            symbol="NQ",
            source_name="fixture.csv",
            frozen_cash=frame.iloc[0:0],
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(float(result.iloc[0]["volume"]), 25.0)
        self.assertEqual(stats.volume_only_resolved, 1)

    def test_ohlc_conflict_uses_frozen_cash_candidate(self) -> None:
        frame = _frame(
            [
                "2025-01-06 15:00+00:00",
                "2025-01-06 15:00+00:00",
            ],
            [100.0, 101.0],
        )
        frozen = frame.iloc[[1]].copy()
        result, stats = deduplicate_source_rows(
            frame,
            symbol="NQ",
            source_name="fixture.csv",
            frozen_cash=frozen,
        )
        self.assertEqual(float(result.iloc[0]["close"]), 101.0)
        self.assertEqual(
            stats.frozen_cash_ohlc_resolved,
            1,
        )

    def test_unresolved_extended_ohlc_conflict_stops(self) -> None:
        frame = _frame(
            [
                "2025-01-06 02:00+00:00",
                "2025-01-06 02:00+00:00",
            ],
            [100.0, 101.0],
        )
        with self.assertRaises(ExtendedSessionDataError):
            deduplicate_source_rows(
                frame,
                symbol="NQ",
                source_name="fixture.csv",
                frozen_cash=frame.iloc[0:0],
            )

    def test_fallback_only_fills_missing_rows(self) -> None:
        primary = _frame(
            [
                "2025-01-06 00:00+00:00",
                "2025-01-06 00:01+00:00",
            ],
            [100.0, 101.0],
        )
        fallback = _frame(
            [
                "2025-01-06 00:01+00:00",
                "2025-01-06 00:02+00:00",
            ],
            [999.0, 102.0],
        )
        result, stats = add_fallback_rows(
            primary,
            fallback,
        )
        self.assertEqual(len(result), 3)
        self.assertEqual(
            float(
                result.loc[
                    pd.Timestamp(
                        "2025-01-06 00:01+00:00"
                    ),
                    "close",
                ]
            ),
            101.0,
        )
        self.assertEqual(stats.rows_added, 1)
        self.assertEqual(
            stats.overlap_price_disagreements,
            1,
        )

    def test_frozen_cash_overlay_replaces_source(self) -> None:
        source = _frame(
            ["2025-01-06 15:00+00:00"],
            [100.0],
        )
        frozen = _frame(
            ["2025-01-06 15:00+00:00"],
            [105.0],
        )
        result = overlay_frozen_cash(source, frozen)
        self.assertEqual(float(result.iloc[0]["close"]), 105.0)


class ExtendedSessionAggregationTests(unittest.TestCase):
    def test_active_five_minute_groups_skip_legacy_pause(self) -> None:
        calendar = build_expected_calendar(
            [date(2021, 6, 25)]
        )
        values = np.arange(len(calendar), dtype=float) + 10000
        frame = pd.DataFrame(
            {
                "open": values,
                "high": values + 0.25,
                "low": values - 0.25,
                "close": values,
                "volume": np.ones(len(calendar)),
            },
            index=calendar.index,
        ).join(calendar)
        result = aggregate_active_five_minute(frame)
        self.assertEqual(len(result), 273)
        self.assertTrue(
            result.groupby("session_date").size().eq(273).all()
        )

    def test_active_five_minute_uses_first_open_last_close(self) -> None:
        calendar = build_expected_calendar(
            [date(2021, 6, 28)]
        ).iloc[:5]
        frame = _frame(
            [item.isoformat() for item in calendar.index],
            [100.0, 101.0, 102.0, 103.0, 104.0],
        ).join(calendar)
        result = aggregate_active_five_minute(frame)
        self.assertEqual(len(result), 1)
        self.assertEqual(float(result.iloc[0]["open"]), 100.0)
        self.assertEqual(float(result.iloc[0]["close"]), 104.0)
        self.assertEqual(float(result.iloc[0]["volume"]), 500.0)


if __name__ == "__main__":
    unittest.main()
