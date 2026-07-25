from __future__ import annotations

import unittest

import pandas as pd

from exp019_archive_audit import (
    HARD_CHECK_NAMES,
    audit_dataframe,
    final_classification,
    minute_gap_diagnostics,
)


def valid_frame() -> pd.DataFrame:
    index = pd.date_range(
        "2024-01-02T00:00:00Z",
        periods=4,
        freq="1min",
    )

    return pd.DataFrame(
        {
            "instrument_id": [
                123,
                123,
                123,
                123,
            ],
            "open": [
                17000.00,
                17000.25,
                17000.50,
                17000.75,
            ],
            "high": [
                17000.25,
                17000.50,
                17000.75,
                17001.00,
            ],
            "low": [
                16999.75,
                17000.00,
                17000.25,
                17000.50,
            ],
            "close": [
                17000.25,
                17000.50,
                17000.75,
                17001.00,
            ],
            "volume": [
                10,
                12,
                15,
                20,
            ],
        },
        index=index,
    )


class Exp019ArchiveAuditTests(
    unittest.TestCase
):
    def test_locked_hard_check_count(self):
        self.assertEqual(
            len(HARD_CHECK_NAMES),
            17,
        )

    def test_valid_frame_passes_data_checks(self):
        result = audit_dataframe(
            valid_frame(),
            start="2024-01-02",
            end_exclusive="2024-01-03",
        )

        checks = (
            "nonempty_records",
            "required_columns",
            "single_instrument_id_per_file",
            "timestamps_inside_locked_window",
            "minute_timestamp_alignment",
            "monotonic_timestamp_order",
            "duplicate_timestamps",
            "duplicate_full_rows",
            "finite_ohlcv",
            "ohlc_invariants",
            "negative_volume",
            "nq_quarter_point_tick_alignment",
        )

        for check in checks:
            self.assertTrue(
                result[check],
                check,
            )

        self.assertEqual(
            result["record_count"],
            4,
        )
        self.assertEqual(
            result["instrument_id"],
            123,
        )

    def test_duplicate_timestamp_fails(self):
        frame = valid_frame()

        frame.index = pd.DatetimeIndex(
            [
                frame.index[0],
                frame.index[1],
                frame.index[1],
                frame.index[3],
            ]
        )

        result = audit_dataframe(
            frame,
            start="2024-01-02",
            end_exclusive="2024-01-03",
        )

        self.assertFalse(
            result[
                "duplicate_timestamps"
            ]
        )
        self.assertEqual(
            result[
                "duplicate_timestamp_count"
            ],
            1,
        )

    def test_off_tick_price_fails(self):
        frame = valid_frame()

        frame.loc[
            frame.index[0],
            "open",
        ] = 17000.10

        result = audit_dataframe(
            frame,
            start="2024-01-02",
            end_exclusive="2024-01-03",
        )

        self.assertFalse(
            result[
                "nq_quarter_point_tick_alignment"
            ]
        )
        self.assertGreater(
            result[
                "off_tick_value_count"
            ],
            0,
        )

    def test_invalid_ohlc_fails(self):
        frame = valid_frame()

        frame.loc[
            frame.index[0],
            "high",
        ] = 16999.50

        result = audit_dataframe(
            frame,
            start="2024-01-02",
            end_exclusive="2024-01-03",
        )

        self.assertFalse(
            result["ohlc_invariants"]
        )
        self.assertGreater(
            result[
                "ohlc_invariant_failure_count"
            ],
            0,
        )

    def test_negative_volume_fails(self):
        frame = valid_frame()

        frame.loc[
            frame.index[0],
            "volume",
        ] = -1

        result = audit_dataframe(
            frame,
            start="2024-01-02",
            end_exclusive="2024-01-03",
        )

        self.assertFalse(
            result["negative_volume"]
        )
        self.assertEqual(
            result[
                "negative_volume_count"
            ],
            1,
        )

    def test_missing_minute_runs_are_diagnostic(self):
        timestamps = pd.DatetimeIndex(
            [
                pd.Timestamp(
                    "2024-01-02T00:00:00Z"
                ),
                pd.Timestamp(
                    "2024-01-02T00:01:00Z"
                ),
                pd.Timestamp(
                    "2024-01-02T00:05:00Z"
                ),
            ]
        )

        result = minute_gap_diagnostics(
            timestamps
        )

        self.assertEqual(
            result[
                "missing_minute_run_count"
            ],
            1,
        )
        self.assertEqual(
            result[
                "largest_missing_minute_run"
            ],
            3,
        )

    def test_known_warnings_control_classification(self):
        checks = {
            name: True
            for name in HARD_CHECK_NAMES
        }

        self.assertEqual(
            final_classification(
                checks,
                warning_windows=16,
            ),
            (
                "QUALIFIED_WITH_KNOWN_"
                "PROVIDER_CONDITIONS"
            ),
        )

        self.assertEqual(
            final_classification(
                checks,
                warning_windows=0,
            ),
            "QUALIFIED",
        )

    def test_hard_failure_controls_classification(self):
        checks = {
            name: True
            for name in HARD_CHECK_NAMES
        }

        checks[
            "manifest_file_sha256"
        ] = False

        self.assertEqual(
            final_classification(
                checks,
                warning_windows=16,
            ),
            "NOT_QUALIFIED",
        )


if __name__ == "__main__":
    unittest.main()
