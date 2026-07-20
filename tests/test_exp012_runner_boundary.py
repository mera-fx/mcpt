from __future__ import annotations

from pathlib import Path
import unittest

import run_exp012_tournament


class Exp012RunnerBoundaryTests(unittest.TestCase):
    def test_runner_requires_explicit_preflight_or_run_mode(self) -> None:
        source = Path(run_exp012_tournament.__file__).read_text(
            encoding="utf-8"
        )
        self.assertIn("add_mutually_exclusive_group(required=True)", source)
        self.assertIn('"--preflight"', source)
        self.assertIn('"--run"', source)

    def test_expensive_tests_remain_absent(self) -> None:
        source = Path(run_exp012_tournament.__file__).read_text(
            encoding="utf-8"
        )
        self.assertNotIn("run_exp012_mcpt", source)
        self.assertNotIn("bootstrap_exp012", source)
        self.assertIn('"mcpt_run": False', source)
        self.assertIn('"bootstrap_run": False', source)
        self.assertIn('"walk_forward_run": False', source)

    def test_manifest_is_written_after_all_candidates(self) -> None:
        source = Path(run_exp012_tournament.__file__).read_text(
            encoding="utf-8"
        )
        loop_position = source.index(
            "for index, candidate in enumerate(candidates, start=1)"
        )
        manifest_position = source.index(
            'STAGING_RESULT_DIR / "tournament_manifest.json"'
        )
        self.assertLess(loop_position, manifest_position)

    def test_partial_run_uses_staging_paths(self) -> None:
        source = Path(run_exp012_tournament.__file__).read_text(
            encoding="utf-8"
        )
        self.assertIn("STAGING_RESULT_DIR", source)
        self.assertIn("STAGING_REPORT_DIR", source)
        self.assertIn("STAGING_RESULT_DIR.replace(RESULT_DIR)", source)


if __name__ == "__main__":
    unittest.main()
