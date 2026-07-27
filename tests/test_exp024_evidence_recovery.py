from __future__ import annotations

import inspect
import tempfile
from pathlib import Path
import shutil
import unittest

import exp024_evidence_recovery as recovery


class Exp024EvidenceRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Path(recovery.__file__).read_text(encoding="utf-8")

    def test_01_identity_is_locked(self):
        self.assertEqual(
            recovery.LOCKED_ATTEMPT_002_FAILURE_COMMIT,
            "7acf180c9640079c560c992a00c4fd413f3b13b7",
        )
        self.assertEqual(
            recovery.CLASSIFICATION,
            "ATTRIBUTION_DIAGNOSTIC_NOT_QUALIFIED",
        )

    def test_02_exactly_nine_preserved_artifacts_are_locked(self):
        self.assertEqual(len(recovery.PRESERVED_ARTIFACTS), 9)

    def test_03_generated_output_set_is_locked(self):
        self.assertEqual(
            recovery.GENERATED_OUTPUTS,
            (
                "attribution_summary.json",
                "report.md",
                "report.html",
                "output_hashes.json",
                "ATTRIBUTION_DIAGNOSTIC_COMPLETE.json",
            ),
        )
        self.assertEqual(len(recovery.FINAL_OUTPUTS), 14)

    def test_04_candidate_counts_are_locked(self):
        self.assertEqual(
            recovery.EXPECTED_CANDIDATE_COUNTS,
            {
                "gap_fade_0p50_1r": 48,
                "premarket_continuation_0p50_time": 2,
                "premarket_continuation_0p75_time": 1,
            },
        )

    def test_05_category_counts_are_locked(self):
        self.assertEqual(
            recovery.EXPECTED_CATEGORY_COUNTS[
                "UNRESOLVED_WITH_LOCKED_FEATURES"
            ],
            43,
        )
        self.assertEqual(sum(recovery.EXPECTED_CATEGORY_COUNTS.values()), 51)

    def test_06_no_parquet_reader_is_present(self):
        lowered = self.source.lower()
        self.assertNotIn("read_parquet", lowered)
        self.assertNotIn("pyarrow", lowered)
        self.assertNotIn("scan_parquet_intervals", lowered)

    def test_07_no_market_reconstruction_function_is_called(self):
        self.assertNotIn("load_permitted_market_windows", self.source)
        self.assertNotIn("build_candidate_features", self.source)
        self.assertNotIn("build_attribution(", self.source)
        self.assertNotIn("_build_once(", self.source)

    def test_08_no_chart_rebuild_library_is_present(self):
        lowered = self.source.lower()
        self.assertNotIn("matplotlib", lowered)
        self.assertNotIn("savefig", lowered)

    def test_09_authorization_module_is_separate(self):
        self.assertEqual(
            recovery.RECOVERY_AUTHORIZATION_MODULE,
            "exp024_evidence_recovery_authorization",
        )
        self.assertEqual(len(recovery.RECOVERY_AUTHORIZATION_PATHS), 3)

    def test_10_recovery_requires_explicit_confirmation(self):
        source = inspect.getsource(recovery.main)
        self.assertIn("--recover requires --confirm-evidence-only-recovery", source)

    def test_11_strict_boolean_accepts_only_locked_values(self):
        self.assertTrue(recovery._strict_bool("True"))
        self.assertFalse(recovery._strict_bool("false"))
        with self.assertRaisesRegex(ValueError, "strict boolean"):
            recovery._strict_bool("yes")

    def test_12_actual_preserved_hashes_match(self):
        snapshot = recovery.snapshot_preserved_artifacts()
        self.assertEqual(snapshot, recovery.PRESERVED_ARTIFACTS)

    def test_13_actual_evidence_counts_match(self):
        evidence = recovery.inspect_preserved_evidence()
        self.assertEqual(len(evidence["mismatch_rows"]), 51)
        self.assertEqual(len(evidence["feature_rows"]), 153)
        self.assertEqual(len(evidence["raw_rows"]), 1530)
        self.assertEqual(len(evidence["roll_rows"]), 51)
        self.assertEqual(len(evidence["aggregation_rows"]), 4709)

    def test_14_rebuild_result_is_not_qualified(self):
        evidence = recovery.inspect_preserved_evidence()
        self.assertEqual(evidence["reference_rebuild_match_rows"], 8)
        self.assertEqual(evidence["reference_rebuild_failure_rows"], 43)
        self.assertEqual(evidence["transfer_rebuild_match_rows"], 51)
        self.assertEqual(evidence["unresolved_rows"], 43)

    def test_15_reference_hard_check_remains_failed(self):
        checks = recovery.inspect_preserved_evidence()[
            "diagnostic_hard_checks"
        ]
        self.assertFalse(
            checks["reference_decision_rebuild_matches_frozen_alignment"]
        )
        self.assertEqual(sum(not value for value in checks.values()), 1)

    def test_16_documents_are_built_without_modifying_evidence(self):
        before = recovery.snapshot_preserved_artifacts()
        evidence = recovery.inspect_preserved_evidence()
        docs = recovery.build_recovery_documents(
            evidence,
            repository={
                "attempt_002_failure_commit": (
                    recovery.LOCKED_ATTEMPT_002_FAILURE_COMMIT
                ),
                "recovery_implementation_commit": "1" * 40,
                "recovery_authorization_commit": "2" * 40,
                "recovery_execution_head": "2" * 40,
            },
            recovered_at_utc="2026-07-26T23:00:00+00:00",
            preserved=before,
        )
        self.assertEqual(
            set(docs),
            {"attribution_summary.json", "report.md", "report.html"},
        )
        self.assertEqual(before, recovery.snapshot_preserved_artifacts())

    def test_17_report_states_the_failed_reference_rebuild(self):
        evidence = recovery.inspect_preserved_evidence()
        docs = recovery.build_recovery_documents(
            evidence,
            repository={
                "attempt_002_failure_commit": "0" * 40,
                "recovery_implementation_commit": "1" * 40,
                "recovery_authorization_commit": "2" * 40,
                "recovery_execution_head": "2" * 40,
            },
            recovered_at_utc="2026-07-26T23:00:00+00:00",
            preserved=recovery.PRESERVED_ARTIFACTS,
        )
        markdown = docs["report.md"].decode("utf-8")
        self.assertIn("8 / 51", markdown)
        self.assertIn("43 gap-fade rows", markdown)
        self.assertIn("prove either source is wrong or superior", markdown)

    def test_18_tampered_artifact_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "partial"
            shutil.copytree(recovery.PARTIAL_DIR, target)
            path = target / "mismatch_attribution.csv"
            path.write_bytes(path.read_bytes() + b"\n")
            with self.assertRaisesRegex(RuntimeError, "artifact changed"):
                recovery.snapshot_preserved_artifacts(target)

    def test_19_generated_files_are_rejected_before_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "partial"
            shutil.copytree(recovery.PARTIAL_DIR, target)
            (target / "report.md").write_text("unexpected", encoding="utf-8")
            snapshot = recovery.snapshot_preserved_artifacts(target)
            self.assertEqual(snapshot, recovery.PRESERVED_ARTIFACTS)
            self.assertTrue((target / "report.md").is_file())

    def test_20_runner_does_not_authorize_strategy_or_trading(self):
        lowered = self.source.lower()
        self.assertIn('"strategy_replay": false', lowered)
        self.assertIn('"performance_evaluation": false', lowered)
        self.assertIn('"paper_trading_authorized": false', lowered)
        self.assertIn('"live_trading_authorized": false', lowered)


if __name__ == "__main__":
    unittest.main()
