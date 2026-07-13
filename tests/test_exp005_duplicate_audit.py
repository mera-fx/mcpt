from __future__ import annotations

from pathlib import Path
import unittest

import pandas as pd

from audit_exp005_quantower_duplicates import (
    _audit_duplicate_group,
    build_summary,
)


class Exp005DuplicateAuditTests(
    unittest.TestCase
):
    def test_volume_only_conflict_is_classified(
        self,
    ) -> None:
        group = pd.DataFrame(
            {
                "open": [9166.75, 9166.75],
                "high": [9169.75, 9169.75],
                "low": [9164.0, 9164.0],
                "close": [9166.25, 9166.25],
                "volume": [5088, 1696],
            }
        )

        record = _audit_duplicate_group(
            symbol="NQ",
            path=pd.io.common.stringify_path(
                "NQ.csv"
            ),
            timestamp=pd.Timestamp(
                "2020-01-24 20:20:00+00:00"
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
        self.assertAlmostEqual(
            record.maximum_to_minimum_volume_ratio,
            3.0,
        )

    def test_ohlc_conflict_is_classified(
        self,
    ) -> None:
        group = pd.DataFrame(
            {
                "open": [9166.75, 9167.00],
                "high": [9169.75, 9169.75],
                "low": [9164.0, 9164.0],
                "close": [9166.25, 9166.25],
                "volume": [5088, 1696],
            }
        )

        record = _audit_duplicate_group(
            symbol="NQ",
            path=pd.io.common.stringify_path(
                "NQ.csv"
            ),
            timestamp=pd.Timestamp(
                "2020-01-24 20:20:00+00:00"
            ),
            group=group,
        )

        self.assertEqual(
            record.classification,
            "OHLC_CONFLICT",
        )

    def test_summary_supports_max_volume_only_without_price_conflict(
        self,
    ) -> None:
        group = pd.DataFrame(
            {
                "open": [1.0, 1.0],
                "high": [2.0, 2.0],
                "low": [0.5, 0.5],
                "close": [1.5, 1.5],
                "volume": [100, 300],
            }
        )

        record = _audit_duplicate_group(
            symbol="NQ",
            path=pd.io.common.stringify_path(
                "NQ.csv"
            ),
            timestamp=pd.Timestamp(
                "2020-01-24 20:20:00+00:00"
            ),
            group=group,
        )

        summary = build_summary(
            [record]
        )

        self.assertTrue(
            summary["decision_support"][
                "all_inside_session_conflicts_are_volume_only"
            ]
        )
        self.assertTrue(
            summary["decision_support"][
                "safe_to_consider_max_volume_rule"
            ]
        )


if __name__ == "__main__":
    unittest.main()
