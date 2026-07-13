from __future__ import annotations

from pathlib import Path
import unittest

from exp004_quick_screen_record import (
    get_exp004_quick_screen_record,
    validate_exp004_quick_screen_record,
)


class Exp004QuickScreenRecordTests(
    unittest.TestCase
):
    def test_record_is_valid(
        self,
    ) -> None:
        validate_exp004_quick_screen_record()

    def test_rejection_and_oos_lock_are_preserved(
        self,
    ) -> None:
        record = get_exp004_quick_screen_record()

        self.assertEqual(
            record["decision"],
            "REJECT",
        )
        self.assertEqual(
            record["lifecycle_stage"],
            "REJECTED",
        )
        self.assertEqual(
            record["out_of_sample_disclosure"],
            "BLOCKED",
        )
        self.assertFalse(
            record["out_of_sample_period_viewed"]
        )

    def test_three_locked_gates_failed(
        self,
    ) -> None:
        record = get_exp004_quick_screen_record()

        self.assertEqual(
            set(record["failed_gates"]),
            {
                "best_in_sample_trade_pf",
                "fixed_in_sample_trade_pf",
                "quick_mcpt_p_value",
            },
        )

    def test_observed_values_are_frozen(
        self,
    ) -> None:
        record = get_exp004_quick_screen_record()
        observed = record["observed"]

        self.assertAlmostEqual(
            observed["best_in_sample_trade_pf"],
            1.0463260050583139,
        )
        self.assertAlmostEqual(
            observed["fixed_in_sample_trade_pf"],
            1.02106173584336,
        )
        self.assertEqual(
            observed[
                "fixed_in_sample_completed_trades"
            ],
            973,
        )
        self.assertAlmostEqual(
            record["mcpt"]["p_value"],
            0.3076923076923077,
        )

    def test_human_result_record_exists(
        self,
    ) -> None:
        root = Path(
            __file__
        ).resolve().parents[1]

        path = (
            root
            / "research"
            / "EXP-004_quick_screen_result.md"
        )

        self.assertTrue(path.exists())

        content = path.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "**Decision:** REJECT",
            content,
        )
        self.assertIn(
            "**Out-of-sample disclosure:** BLOCKED",
            content,
        )


if __name__ == "__main__":
    unittest.main()
