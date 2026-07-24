from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from build_analytics_expansion import build_analytics_expansion


PROJECT_DIR = Path(__file__).resolve().parents[1]


class AnalyticsExpansionBuildTests(unittest.TestCase):
    def test_single_experiment_build_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory(
            dir=PROJECT_DIR,
        ) as directory:
            output = Path(directory) / "analytics"
            first = build_analytics_expansion(
                PROJECT_DIR,
                output_dir=output,
                experiment_ids=("EXP-004",),
            )
            second = build_analytics_expansion(
                PROJECT_DIR,
                output_dir=output,
                experiment_ids=("EXP-004",),
            )

            self.assertEqual(first.strategy_series_count, 1)
            self.assertGreater(first.files_written, 0)
            self.assertEqual(second.files_written, 0)
            self.assertEqual(
                first.evidence_digest,
                second.evidence_digest,
            )
            self.assertTrue((output / "manifest.json").is_file())
            self.assertTrue(
                (
                    output
                    / "EXP-004"
                    / "exp-004--fixed_in_sample--qqq"
                    / "report.html"
                ).is_file()
            )

    def test_preflight_does_not_create_output(self) -> None:
        with tempfile.TemporaryDirectory(
            dir=PROJECT_DIR,
        ) as directory:
            output = Path(directory) / "not-created"
            result = build_analytics_expansion(
                PROJECT_DIR,
                output_dir=output,
                experiment_ids=("EXP-004",),
                preflight_only=True,
            )
            self.assertTrue(result.preflight_only)
            self.assertEqual(result.files_written, 0)
            self.assertFalse(output.exists())

    def test_frozen_result_directory_is_rejected_as_output(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "frozen experiment result",
        ):
            build_analytics_expansion(
                PROJECT_DIR,
                output_dir=PROJECT_DIR / "results" / "EXP-004",
                experiment_ids=("EXP-004",),
                preflight_only=True,
            )


if __name__ == "__main__":
    unittest.main()
