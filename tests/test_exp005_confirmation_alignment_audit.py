from __future__ import annotations

import unittest

import pandas as pd

from audit_exp005_confirmation_alignment import (
    enrich_alignment_exclusions,
)


def make_session(
    session_date: str,
    *,
    nq_close: float,
    mnq_close: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    index = pd.date_range(
        f"{session_date} 14:30:00+00:00",
        periods=390,
        freq="min",
    )
    nq = pd.DataFrame(
        {
            "close": [nq_close] * 390,
            "session_date": [
                session_date
            ] * 390,
        },
        index=index,
    )
    mnq = pd.DataFrame(
        {
            "close": [mnq_close] * 390,
            "session_date": [
                session_date
            ] * 390,
        },
        index=index,
    )
    return nq, mnq


class Exp005ConfirmationAlignmentAuditTests(
    unittest.TestCase
):
    def test_empty_exclusions_return_empty_details(
        self,
    ) -> None:
        details = enrich_alignment_exclusions(
            pd.DataFrame(),
            nq_data=pd.DataFrame(),
            mnq_data=pd.DataFrame(),
        )
        self.assertTrue(details.empty)

    def test_difference_diagnostics_are_exact(
        self,
    ) -> None:
        nq, mnq = make_session(
            "2025-03-03",
            nq_close=20000.0,
            mnq_close=19970.0,
        )
        exclusions = pd.DataFrame(
            [
                {
                    "symbol": "BOTH",
                    "session_date": "2025-03-03",
                    "reason": (
                        "potential_front_month_mismatch"
                    ),
                    "median_close_difference": 30.0,
                    "maximum_close_difference": 30.0,
                }
            ]
        )

        details = enrich_alignment_exclusions(
            exclusions,
            nq_data=nq,
            mnq_data=mnq,
        )
        row = details.iloc[0]

        self.assertEqual(
            row[
                "minutes_difference_over_5_points"
            ],
            390,
        )
        self.assertEqual(
            row[
                "minutes_difference_over_20_points"
            ],
            390,
        )
        self.assertEqual(
            row[
                "signed_nq_minus_mnq_at_maximum"
            ],
            30.0,
        )

    def test_single_large_difference_is_counted(
        self,
    ) -> None:
        nq, mnq = make_session(
            "2025-03-04",
            nq_close=20000.0,
            mnq_close=20000.0,
        )
        mnq.iloc[
            100,
            mnq.columns.get_loc("close"),
        ] = 19975.0

        exclusions = pd.DataFrame(
            [
                {
                    "symbol": "BOTH",
                    "session_date": "2025-03-04",
                    "reason": (
                        "potential_front_month_mismatch"
                    ),
                    "median_close_difference": 0.0,
                    "maximum_close_difference": 25.0,
                }
            ]
        )

        details = enrich_alignment_exclusions(
            exclusions,
            nq_data=nq,
            mnq_data=mnq,
        )
        row = details.iloc[0]

        self.assertEqual(
            row[
                "minutes_difference_over_20_points"
            ],
            1,
        )
        self.assertEqual(
            row[
                "maximum_close_difference"
            ],
            25.0,
        )


if __name__ == "__main__":
    unittest.main()
