from __future__ import annotations

from pathlib import Path
import unittest

from exp005_source_amendment import (
    get_exp005_source_amendment,
    validate_exp005_source_amendment,
)


class Exp005SourceAmendmentTests(
    unittest.TestCase
):
    def test_amendment_is_valid(
        self,
    ) -> None:
        validate_exp005_source_amendment()

    def test_amendment_precedes_full_export(
        self,
    ) -> None:
        record = get_exp005_source_amendment()

        self.assertEqual(
            record["status"],
            "LOCKED_BEFORE_FULL_DATA_EXPORT",
        )
        self.assertEqual(
            record["results_viewed"],
            "NONE",
        )
        self.assertTrue(
            record["source_validation_only"]
        )

    def test_source_is_zero_additional_cost(
        self,
    ) -> None:
        source = get_exp005_source_amendment()[
            "new_source"
        ]

        self.assertEqual(
            source["additional_data_cost"],
            0.0,
        )
        self.assertEqual(
            source["symbols"],
            {
                "NQ": "NQ",
                "MNQ": "MNQ",
            },
        )

    def test_sample_hashes_and_counts_are_frozen(
        self,
    ) -> None:
        evidence = get_exp005_source_amendment()[
            "sample_evidence"
        ]

        self.assertFalse(
            evidence["strategy_metrics_calculated"]
        )
        self.assertEqual(
            evidence["NQ"]["raw_rows"],
            1305,
        )
        self.assertEqual(
            evidence["MNQ"]["raw_rows"],
            1300,
        )
        self.assertEqual(
            evidence["NQ"]["cash_session_rows"],
            390,
        )
        self.assertEqual(
            evidence["MNQ"]["cash_session_rows"],
            390,
        )
        self.assertEqual(
            len(evidence["NQ"]["sha256"]),
            64,
        )
        self.assertEqual(
            len(evidence["MNQ"]["sha256"]),
            64,
        )

    def test_roll_risk_controls_are_locked(
        self,
    ) -> None:
        controls = get_exp005_source_amendment()[
            "roll_risk_controls"
        ]

        self.assertTrue(
            controls["same_session_strategy_only"]
        )
        self.assertFalse(
            controls["previous_close_used"]
        )
        self.assertFalse(
            controls["overnight_gap_used"]
        )
        self.assertEqual(
            controls[
                "maximum_median_close_difference_points"
            ],
            5.0,
        )
        self.assertEqual(
            controls[
                "maximum_single_close_difference_points"
            ],
            20.0,
        )
        self.assertEqual(
            controls[
                "included_mismatch_sessions_allowed"
            ],
            0,
        )

    def test_signal_and_gates_are_declared_unchanged(
        self,
    ) -> None:
        record = get_exp005_source_amendment()
        unchanged = " ".join(
            record["unchanged_research_components"]
        )

        self.assertIn(
            "15-minute both-direction ORB",
            unchanged,
        )
        self.assertIn(
            "No optimization",
            unchanged,
        )
        self.assertIn(
            "Every quick-transfer and full-validation threshold",
            unchanged,
        )

    def test_human_amendment_exists(
        self,
    ) -> None:
        root = Path(
            __file__
        ).resolve().parents[1]

        path = (
            root
            / "research"
            / "EXP-005_source_amendment.md"
        )

        self.assertTrue(path.exists())

        content = path.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "Strategy results viewed:** None",
            content,
        )
        self.assertIn(
            "zero additional data cost",
            content,
        )


if __name__ == "__main__":
    unittest.main()
