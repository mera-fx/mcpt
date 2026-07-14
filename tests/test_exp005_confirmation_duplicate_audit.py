from __future__ import annotations

from pathlib import Path
import unittest

import pandas as pd

from audit_exp005_confirmation_duplicates import (
    _audit_duplicate_group,
    build_summary,
)


class Exp005ConfirmationDuplicateAuditTests(
    unittest.TestCase
):
    def test_volume_only_conflict_is_classified(
        self,
    ) -> None:
        group = pd.DataFrame(
            {
                "open": [100.0, 100.0],
                "high": [101.0, 101.0],
                "low": [99.0, 99.0],
                "close": [100.5, 100.5],
                "volume": [300, 100],
            }
        )

        record = _audit_duplicate_group(
            symbol="NQ",
            path=Path("NQ.csv"),
            timestamp=pd.Timestamp(
                "2024-11-06T14:40:00+00:00"
            ),
            group=group,
        )

        self.assertEqual(
            record.classification,
            "VOLUME_ONLY_CONFLICT",
        )
        self.assertTrue(
            record.inside_locked_cash_session
        )

    def test_ohlc_conflict_is_classified(
        self,
    ) -> None:
        group = pd.DataFrame(
            {
                "open": [20793.0, 20793.0],
                "high": [20805.25, 20805.25],
                "low": [20778.25, 20778.25],
                "close": [20783.5, 20783.75],
                "volume": [11534, 3845],
            }
        )

        record = _audit_duplicate_group(
            symbol="NQ",
            path=Path("NQ.csv"),
            timestamp=pd.Timestamp(
                "2024-11-06T14:40:00+00:00"
            ),
            group=group,
        )

        self.assertEqual(
            record.classification,
            "OHLC_CONFLICT",
        )
        self.assertTrue(
            record.inside_locked_cash_session
        )
        self.assertEqual(
            record.session_date,
            "2024-11-06",
        )

    def test_summary_creates_unique_symbol_date_plan(
        self,
    ) -> None:
        group = pd.DataFrame(
            {
                "open": [1.0, 1.0],
                "high": [2.0, 2.0],
                "low": [0.5, 0.5],
                "close": [1.0, 1.25],
                "volume": [300, 100],
            }
        )

        first = _audit_duplicate_group(
            symbol="NQ",
            path=Path("NQ.csv"),
            timestamp=pd.Timestamp(
                "2024-11-06T14:40:00+00:00"
            ),
            group=group,
        )
        second = _audit_duplicate_group(
            symbol="NQ",
            path=Path("NQ.csv"),
            timestamp=pd.Timestamp(
                "2024-11-06T14:41:00+00:00"
            ),
            group=group,
        )

        summary = build_summary(
            [first, second]
        )

        self.assertEqual(
            summary[
                "inside_session_classifications"
            ]["OHLC_CONFLICT"],
            2,
        )
        self.assertEqual(
            summary[
                "ohlc_conflict_dates"
            ],
            [
                {
                    "symbol": "NQ",
                    "session_date": (
                        "2024-11-06"
                    ),
                }
            ],
        )
        self.assertFalse(
            summary[
                "strategy_results_calculated"
            ]
        )


if __name__ == "__main__":
    unittest.main()
