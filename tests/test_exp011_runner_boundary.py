from __future__ import annotations

from pathlib import Path
import unittest

import run_exp011_sizing_study


class Exp011RunnerBoundaryTests(unittest.TestCase):
    def test_result_path_is_separate_and_one_time(self) -> None:
        self.assertEqual(
            run_exp011_sizing_study.RESULT_FILE.name,
            "sizing_result.json",
        )
        self.assertIn(
            str(Path("results") / "EXP-011" / "position_sizing"),
            str(run_exp011_sizing_study.RESULT_FILE),
        )

    def test_runner_requires_explicit_preflight_or_run(self) -> None:
        source = Path(run_exp011_sizing_study.__file__).read_text(
            encoding="utf-8"
        )
        self.assertIn("add_mutually_exclusive_group(required=True)", source)
        self.assertIn('"--preflight"', source)
        self.assertIn('"--run"', source)
        self.assertIn("Do not rerun it", source)

    def test_runner_does_not_modify_lifecycle_source(self) -> None:
        source = Path(run_exp011_sizing_study.__file__).read_text(
            encoding="utf-8"
        )
        self.assertNotIn("write_lifecycle", source)
        self.assertIn('"automatic_lifecycle_source_edit": False', source)


if __name__ == "__main__":
    unittest.main()
