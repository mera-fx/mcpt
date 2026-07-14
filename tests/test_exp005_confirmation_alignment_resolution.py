from __future__ import annotations

from copy import deepcopy
from datetime import date
import unittest

import pandas as pd

import exp005_quantower_import as base
from exp005_confirmation_alignment_resolution import (
    EXP005_CONFIRMATION_ALIGNMENT_RESOLUTION,
    get_exp005_confirmation_alignment_resolution,
    locked_confirmation_alignment_excluded_dates,
    validate_exp005_confirmation_alignment_resolution,
    validate_locked_confirmation_alignment_exclusions,
)


def make_exclusions() -> pd.DataFrame:
    specifications = (
        EXP005_CONFIRMATION_ALIGNMENT_RESOLUTION[
            "excluded_sessions"
        ]
    )
    return pd.DataFrame(
        [
            {
                "symbol": "BOTH",
                "session_date": session_text,
                "reason": (
                    "potential_front_month_mismatch"
                ),
                "median_close_difference": (
                    specification[
                        "median_close_difference"
                    ]
                ),
                "maximum_close_difference": (
                    specification[
                        "maximum_close_difference"
                    ]
                ),
            }
            for session_text, specification
            in specifications.items()
        ]
    )


class Exp005ConfirmationAlignmentResolutionTests(
    unittest.TestCase
):
    def test_record_is_valid(
        self,
    ) -> None:
        validate_exp005_confirmation_alignment_resolution()

    def test_locked_dates_are_exact(
        self,
    ) -> None:
        self.assertEqual(
            locked_confirmation_alignment_excluded_dates(),
            (
                date(2023, 3, 14),
                date(2023, 12, 12),
                date(2024, 3, 12),
                date(2025, 3, 24),
                date(2025, 4, 1),
                date(2025, 4, 9),
                date(2025, 5, 19),
                date(2025, 7, 1),
                date(2025, 10, 24),
            ),
        )

    def test_category_counts_are_exact(
        self,
    ) -> None:
        record = (
            get_exp005_confirmation_alignment_resolution()
        )
        categories = [
            item["category"]
            for item in record[
                "excluded_sessions"
            ].values()
        ]

        self.assertEqual(
            categories.count(
                "PERSISTENT_CROSS_SYMBOL_DIVERGENCE"
            ),
            3,
        )
        self.assertEqual(
            categories.count(
                "ISOLATED_CROSS_SYMBOL_PRICE_DIVERGENCE"
            ),
            6,
        )

    def test_locked_final_counts_are_exact(
        self,
    ) -> None:
        result = (
            EXP005_CONFIRMATION_ALIGNMENT_RESOLUTION[
                "result"
            ]
        )

        self.assertEqual(
            result["expected_included_sessions"],
            733,
        )
        self.assertEqual(
            result[
                "expected_one_minute_rows_per_symbol"
            ],
            285870,
        )
        self.assertEqual(
            result[
                "expected_five_minute_rows_per_symbol"
            ],
            57174,
        )
        self.assertEqual(
            result["bars_synthesized"],
            0,
        )

    def test_exact_exclusions_are_accepted(
        self,
    ) -> None:
        result = (
            validate_locked_confirmation_alignment_exclusions(
                exclusions=make_exclusions(),
            )
        )

        self.assertEqual(
            len(result),
            9,
        )
        self.assertTrue(
            result[
                "resolution_record"
            ].eq("EXP-005-DQ5").all()
        )
        self.assertTrue(
            result[
                "bars_synthesized"
            ].eq(0).all()
        )

    def test_missing_date_stops(
        self,
    ) -> None:
        changed = make_exclusions().iloc[
            :-1
        ].copy()

        with self.assertRaisesRegex(
            base.AlignmentError,
            "count|dates",
        ):
            validate_locked_confirmation_alignment_exclusions(
                exclusions=changed,
            )

    def test_changed_metric_stops(
        self,
    ) -> None:
        changed = make_exclusions()
        changed.loc[
            0,
            "maximum_close_difference",
        ] += 0.25

        with self.assertRaisesRegex(
            base.AlignmentError,
            "metric changed",
        ):
            validate_locked_confirmation_alignment_exclusions(
                exclusions=changed,
            )

    def test_changed_reason_stops(
        self,
    ) -> None:
        changed = make_exclusions()
        changed.loc[
            0,
            "reason",
        ] = "manual_override"

        with self.assertRaisesRegex(
            base.AlignmentError,
            "identity changed",
        ):
            validate_locked_confirmation_alignment_exclusions(
                exclusions=changed,
            )

    def test_mutated_record_is_rejected(
        self,
    ) -> None:
        changed = deepcopy(
            EXP005_CONFIRMATION_ALIGNMENT_RESOLUTION
        )
        changed["result"][
            "expected_included_sessions"
        ] = 734

        with self.assertRaisesRegex(
            ValueError,
            "result changed",
        ):
            validate_exp005_confirmation_alignment_resolution(
                changed
            )


if __name__ == "__main__":
    unittest.main()
