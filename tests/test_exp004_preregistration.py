from __future__ import annotations

from pathlib import Path
import unittest

from exp004_preregistration import (
    get_exp004_preregistration,
    validate_exp004_preregistration,
)


class Exp004PreregistrationTests(
    unittest.TestCase
):
    def test_preregistration_is_valid(
        self,
    ) -> None:
        validate_exp004_preregistration()

    def test_grid_has_nine_combinations(
        self,
    ) -> None:
        record = get_exp004_preregistration()

        count = 1

        for values in record[
            "optimized_parameters"
        ].values():
            count *= len(values)

        self.assertEqual(count, 9)
        self.assertEqual(
            record["parameter_count"],
            9,
        )

    def test_fixed_parameters_are_in_grid(
        self,
    ) -> None:
        record = get_exp004_preregistration()
        grid = record["optimized_parameters"]

        for name, value in record[
            "fixed_parameters"
        ].items():
            self.assertIn(
                value,
                grid[name],
            )

    def test_quick_screen_blocks_oos(
        self,
    ) -> None:
        record = get_exp004_preregistration()
        rule = record[
            "quick_screen"
        ]["data_access_rule"].lower()

        self.assertIn(
            "only the in-sample",
            rule,
        )
        self.assertIn(
            "must not be calculated",
            rule,
        )

    def test_mcpt_is_session_aware(
        self,
    ) -> None:
        record = get_exp004_preregistration()
        method = record[
            "statistical_plan"
        ]["permutation_method"].lower()

        self.assertIn(
            "time-of-day",
            method,
        )
        self.assertIn(
            "session",
            method,
        )

    def test_human_document_and_implementation_record(
        self,
    ) -> None:
        root = Path(
            __file__
        ).resolve().parents[1]

        document = (
            root
            / "research"
            / "EXP-004_preregistration.md"
        )

        implementation = (
            root
            / "experiments"
            / "exp_004.py"
        )

        implementation_record = (
            root
            / "research"
            / "EXP-004_implementation_record.md"
        )

        self.assertTrue(
            document.exists()
        )
        self.assertTrue(
            implementation.exists()
        )
        self.assertTrue(
            implementation_record.exists()
        )

        content = document.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "Total combinations: **9**",
            content,
        )
        self.assertIn(
            "QQQ-only discovery",
            content,
        )

        record_content = (
            implementation_record.read_text(
                encoding="utf-8"
            )
        )

        self.assertIn(
            "Out-of-sample access:** Prohibited",
            record_content,
        )


if __name__ == "__main__":
    unittest.main()
