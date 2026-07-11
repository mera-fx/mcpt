from __future__ import annotations

import unittest
from pathlib import Path

from exp003_preregistration import (
    get_exp003_preregistration,
    validate_exp003_preregistration,
)


class Exp003PreregistrationTests(
    unittest.TestCase
):
    def test_preregistration_is_valid(
        self,
    ) -> None:
        validate_exp003_preregistration()

    def test_grid_has_27_locked_combinations(
        self,
    ) -> None:
        record = get_exp003_preregistration()
        grid = record["optimized_parameters"]

        count = 1

        for values in grid.values():
            count *= len(values)

        self.assertEqual(count, 27)
        self.assertEqual(
            record["parameter_count"],
            27,
        )

    def test_fixed_parameters_are_in_grid(
        self,
    ) -> None:
        record = get_exp003_preregistration()
        grid = record["optimized_parameters"]

        for name, value in (
            record[
                "fixed_parameters"
            ].items()
        ):
            self.assertIn(
                value,
                grid[name],
            )

    def test_quick_screen_blocks_oos_access(
        self,
    ) -> None:
        record = get_exp003_preregistration()
        rule = record[
            "quick_screen"
        ]["data_access_rule"].lower()

        self.assertIn(
            "only the in-sample period",
            rule,
        )

        self.assertIn(
            "must not be calculated",
            rule,
        )

    def test_human_readable_document_exists(
        self,
    ) -> None:
        project_directory = (
            Path(__file__).resolve().parents[1]
        )

        document = (
            project_directory
            / "research"
            / "EXP-003_preregistration.md"
        )

        self.assertTrue(document.exists())

        content = document.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "PRE_REGISTERED",
            content,
        )

        self.assertIn(
            "Total combinations: **27**",
            content,
        )


if __name__ == "__main__":
    unittest.main()
