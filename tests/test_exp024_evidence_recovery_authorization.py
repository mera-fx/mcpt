from __future__ import annotations

from copy import deepcopy
import unittest

from exp024_evidence_recovery_authorization import (
    EXPECTED_EXP024_EVIDENCE_RECOVERY_AUTHORIZATION_SHA256,
    canonical_record_hash,
    get_exp024_evidence_recovery_authorization,
    validate_exp024_evidence_recovery_authorization,
)


class Exp024EvidenceRecoveryAuthorizationTests(unittest.TestCase):
    def test_01_authorization_is_valid(self):
        validate_exp024_evidence_recovery_authorization()

    def test_02_identity_is_locked(self):
        record = get_exp024_evidence_recovery_authorization()
        self.assertEqual(record["experiment_id"], "EXP-024")
        self.assertEqual(
            record["authorization_id"],
            "EXP-024-EVIDENCE-RECOVERY-AUTH-001",
        )

    def test_03_implementation_commit_is_locked(self):
        record = get_exp024_evidence_recovery_authorization()
        self.assertEqual(
            record["locked_recovery_implementation_commit"],
            "a57ebcbc237e2e8e8696e9d6b3b13f584102beee",
        )

    def test_04_attempt_002_failure_is_locked(self):
        record = get_exp024_evidence_recovery_authorization()
        self.assertEqual(
            record["attempt_002_failure_commit"],
            "7acf180c9640079c560c992a00c4fd413f3b13b7",
        )
        self.assertEqual(
            record["attempt_002_failure_record_sha256"],
            "d58e747db36ae3c5e80a034e3b6de127d9771184805470a16f0d3adbbab77359",
        )

    def test_05_one_time_boundary_is_locked(self):
        record = get_exp024_evidence_recovery_authorization()
        self.assertTrue(record["evidence_recovery_authorized"])
        self.assertTrue(record["one_time_recovery"])
        self.assertEqual(record["maximum_recovery_runs"], 1)
        self.assertFalse(record["recovery_rerun_authorized"])

    def test_06_result_counts_are_locked(self):
        record = get_exp024_evidence_recovery_authorization()
        self.assertEqual(record["expected_candidate_session_rows"], 51)
        self.assertEqual(record["expected_reference_rebuild_matches"], 8)
        self.assertEqual(record["expected_reference_rebuild_failures"], 43)
        self.assertEqual(record["expected_transfer_rebuild_matches"], 51)
        self.assertEqual(record["expected_unresolved_rows"], 43)

    def test_07_exactly_nine_artifacts_are_locked(self):
        record = get_exp024_evidence_recovery_authorization()
        self.assertEqual(record["partial_artifact_count"], 9)
        self.assertEqual(len(record["preserved_artifacts"]), 9)

    def test_08_market_and_recalculation_access_are_prohibited(self):
        record = get_exp024_evidence_recovery_authorization()
        self.assertFalse(record["market_parquet_access_authorized"])
        self.assertFalse(record["attribution_recalculation_authorized"])
        self.assertFalse(record["feature_reconstruction_authorized"])
        self.assertFalse(record["chart_rebuild_authorized"])
        self.assertFalse(record["network_access_authorized"])

    def test_09_strategy_and_trading_are_prohibited(self):
        record = get_exp024_evidence_recovery_authorization()
        self.assertFalse(record["strategy_replay_authorized"])
        self.assertFalse(record["performance_evaluation_authorized"])
        self.assertFalse(record["optimization_authorized"])
        self.assertFalse(record["mcpt_authorized"])
        self.assertFalse(record["paper_trading_authorized"])
        self.assertFalse(record["live_trading_authorized"])

    def test_10_canonical_hash_rejects_mutation(self):
        record = get_exp024_evidence_recovery_authorization()
        self.assertEqual(
            canonical_record_hash(record),
            EXPECTED_EXP024_EVIDENCE_RECOVERY_AUTHORIZATION_SHA256,
        )
        changed = deepcopy(record)
        changed["maximum_recovery_runs"] = 2
        with self.assertRaisesRegex(ValueError, "identity changed"):
            validate_exp024_evidence_recovery_authorization(changed)


if __name__ == "__main__":
    unittest.main()
