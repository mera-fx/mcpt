from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

import run_exp013_validation as runner


PROJECT_DIR = Path(__file__).resolve().parents[1]


class Exp013RunnerBoundaryTests(unittest.TestCase):
    def test_runner_requires_explicit_preflight_or_run(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(PROJECT_DIR / "run_exp013_validation.py")],
            cwd=PROJECT_DIR,
            text=True,
            capture_output=True,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("--preflight", completed.stderr)
        self.assertIn("--run", completed.stderr)

    def test_result_path_is_separate_and_one_time(self) -> None:
        self.assertIn("EXP-013", str(runner.RESULT_FILE))
        self.assertIn("extended_context_validation", str(runner.RESULT_FILE))
        source = (
            PROJECT_DIR / "run_exp013_validation.py"
        ).read_text(encoding="utf-8")
        self.assertIn("if RESULT_FILE.exists()", source)
        self.assertIn("Do not rerun it", source)

    def test_partial_results_use_staging_and_checkpoint_resume(self) -> None:
        source = (
            PROJECT_DIR / "run_exp013_validation.py"
        ).read_text(encoding="utf-8")
        self.assertIn("STAGING_RESULT_DIR", source)
        self.assertIn("STAGING_REPORT_DIR", source)
        self.assertIn("mcpt_checkpoint.json", source)
        self.assertIn("STAGING_RESULT_DIR.replace(RESULT_DIR)", source)

    def test_runner_does_not_modify_lifecycle_or_hide_full_search(self) -> None:
        source = (
            PROJECT_DIR / "run_exp013_validation.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn('"experiment_lifecycle.py"', source)
        self.assertIn(
            '"all_24_candidates_inside_every_permutation": True',
            source,
        )
        self.assertIn('"automatic_lifecycle_source_edit": False', source)
        self.assertIn('"live_trading_authorized": False', source)


if __name__ == "__main__":
    unittest.main()
