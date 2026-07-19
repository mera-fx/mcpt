from __future__ import annotations

import inspect
import unittest

import run_exp010_validation


class Exp010RunnerBoundaryTests(unittest.TestCase):
    def test_runner_requires_explicit_preflight_or_run_mode(self) -> None:
        source = inspect.getsource(run_exp010_validation.parse_args)
        self.assertIn("add_mutually_exclusive_group(required=True)", source)
        self.assertIn('"--preflight"', source)
        self.assertIn('"--run"', source)

    def test_preflight_checks_clean_commit_and_existing_result(self) -> None:
        source = inspect.getsource(
            run_exp010_validation.protected_preflight
        )
        self.assertIn("working_tree_clean", source)
        self.assertIn("RESULT_FILE.exists()", source)
        self.assertIn("verify_local_exp009_tournament_result", source)

    def test_result_writer_does_not_edit_lifecycle(self) -> None:
        source = inspect.getsource(run_exp010_validation.run_validation)
        self.assertIn('"automatic_lifecycle_source_edit": False', source)
        self.assertIn('"paper_trading_authorized": False', source)
        self.assertIn('"live_trading_authorized": False', source)

    def test_runner_keeps_prior_family_selection_limit(self) -> None:
        source = inspect.getsource(run_exp010_validation.run_validation)
        self.assertIn('"prior_six_family_selection_corrected": False', source)


if __name__ == "__main__":
    unittest.main()
