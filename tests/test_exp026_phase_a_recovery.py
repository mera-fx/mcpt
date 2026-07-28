from __future__ import annotations

import inspect
from pathlib import Path
import tempfile
import unittest

import pandas as pd

from exp026_phase_a_recovery import (
    AUTHORIZATION_COMMIT,
    EXPECTED_PARTIAL_FILES,
    EXPECTED_SURVIVORS,
    IMPLEMENTATION_COMMIT,
    REPORT_COLUMNS,
    build_report,
    metrics_markdown,
    partial_snapshot,
    validate_partial_evidence,
)
from exp026_runner import (
    PHASE_OUTPUT_DIRS,
    PHASE_PARTIAL_DIRS,
    PHASE_REQUIRED_OUTPUTS,
)


class Exp026PhaseARecoveryTests(unittest.TestCase):
    def test_01_commits_are_locked(self) -> None:
        self.assertEqual(AUTHORIZATION_COMMIT, "5fa417ed56c2d620c5d348e9ab43f3d7634518b8")
        self.assertEqual(IMPLEMENTATION_COMMIT, "13ee0683dfcbbb5d763f7254f3b245ecc8e6d9cd")

    def test_02_original_result_hashes_are_locked(
        self,
    ) -> None:
        output_dir = PHASE_OUTPUT_DIRS["A"]
        snapshot = {
            name: (
                int((output_dir / name).stat().st_size),
                __import__(
                    "exp026_runner"
                ).sha256_file(
                    output_dir / name
                ),
            )
            for name in EXPECTED_PARTIAL_FILES
        }
        self.assertEqual(
            snapshot,
            EXPECTED_PARTIAL_FILES,
        )

    def test_03_original_evidence_is_valid(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in EXPECTED_PARTIAL_FILES:
                source = (
                    PHASE_OUTPUT_DIRS["A"]
                    / name
                )
                (root / name).write_bytes(
                    source.read_bytes()
                )
            evidence = validate_partial_evidence(
                root
            )

        self.assertTrue(
            evidence["summary"][
                "independent_rebuild"
            ]
        )
        self.assertEqual(
            tuple(
                evidence["survivors"][
                    "candidate_ids"
                ]
            ),
            EXPECTED_SURVIVORS,
        )

    def test_04_required_outputs_are_exact(self) -> None:
        self.assertEqual(len(PHASE_REQUIRED_OUTPUTS["A"]), 8)
        self.assertIn("report.md", PHASE_REQUIRED_OUTPUTS["A"])
        self.assertIn("PHASE_A_COMPLETE.json", PHASE_REQUIRED_OUTPUTS["A"])

    def test_05_markdown_needs_no_tabulate(self) -> None:
        source = inspect.getsource(metrics_markdown)
        self.assertNotIn("to_markdown", source)
        self.assertNotIn("tabulate", source)

    def test_06_markdown_columns_are_present(self) -> None:
        row = {column: ("x" if column in {"candidate_id", "segment"} else 1.0) for column in REPORT_COLUMNS}
        value = metrics_markdown(pd.DataFrame([row]))
        for column in REPORT_COLUMNS:
            self.assertIn(column, value)

    def test_07_report_discloses_recovery(self) -> None:
        metrics = pd.read_csv(
            PHASE_OUTPUT_DIRS["A"]
            / "development_metrics.csv"
        )
        value = build_report(metrics)
        self.assertIn("EXP-026-A-R1", value)
        self.assertIn("did not read market data", value)
        for candidate_id in EXPECTED_SURVIVORS:
            self.assertIn(candidate_id, value)

    def test_08_source_has_no_strategy_replay(self) -> None:
        import exp026_phase_a_recovery as recovery
        source = inspect.getsource(recovery)
        self.assertNotIn("load_permitted_ohlcv(", source)
        self.assertNotIn("_phase_a_computation(", source)
        self.assertNotIn("replay_candidates(", source)

    def test_09_mutation_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in EXPECTED_PARTIAL_FILES:
                source = (
                    PHASE_OUTPUT_DIRS["A"]
                    / name
                )
                (root / name).write_bytes(source.read_bytes())
            (root / "candidate_registry.csv").write_text("changed\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "partial evidence changed"):
                validate_partial_evidence(root)


if __name__ == "__main__":
    unittest.main()
