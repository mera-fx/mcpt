from __future__ import annotations

import ast
from pathlib import Path
import unittest


PROJECT_DIR = Path(__file__).resolve().parents[1]
RUNNER = PROJECT_DIR / "run_exp014_study.py"


class Exp014RunnerBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = RUNNER.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)

    def test_expensive_exp013_engines_are_not_imported_or_called(self) -> None:
        prohibited = (
            "exp013_selection_mcpt",
            "exp013_bootstrap",
            "exp013_walk_forward",
            "run_exp013_discovery_mcpt",
            "bootstrap_exp013_trade_metrics",
            "run_exp013_anchored_walk_forward",
        )
        for value in prohibited:
            self.assertNotIn(value, self.source)

    def test_runner_requires_clean_commit_and_one_time_result_boundary(self) -> None:
        self.assertIn("working_tree_clean", self.source)
        self.assertIn(
            "Commit the EXP-014 implementation before preflight or results.",
            self.source,
        )
        self.assertIn("EXP-014 already has a frozen result", self.source)
        self.assertIn("STAGING_RESULT_DIR", self.source)
        self.assertIn("STAGING_REPORT_DIR", self.source)

    def test_preflight_and_run_are_mutually_exclusive(self) -> None:
        self.assertIn('mode.add_argument(\n        "--preflight"', self.source)
        self.assertIn('mode.add_argument(\n        "--run"', self.source)
        self.assertIn("mutually_exclusive_group(required=True)", self.source)

    def test_no_selection_or_trading_authorization(self) -> None:
        self.assertIn('"no_automatic_winner": True', self.source)
        self.assertIn('"no_regime_filter_selection": True', self.source)
        self.assertIn('"paper_trading_authorized": False', self.source)
        self.assertIn('"live_trading_authorized": False', self.source)


if __name__ == "__main__":
    unittest.main()
