from __future__ import annotations

import unittest

from exp024_attempt_002_failure import (
    EXPECTED_EXP024_ATTEMPT_002_FAILURE_SHA256,
    canonical_record_hash,
    get_exp024_attempt_002_failure,
    validate_exp024_attempt_002_failure,
)


class Exp024Attempt002FailureTests(unittest.TestCase):
    def test_01_record_is_valid(self) -> None:
        validate_exp024_attempt_002_failure()

    def test_02_execution_identity_is_locked(self) -> None:
        record = get_exp024_attempt_002_failure()
        self.assertEqual(record["attempt_id"], "EXP-024-ATTEMPT-002")
        self.assertEqual(
            record["execution_head"],
            "da7bbe843361fd9d08cf64cc1e772c9eabf82fb5",
        )
        self.assertEqual(
            record["authorization_id"],
            "EXP-024-ATTRIBUTION-AUTH-002",
        )
        self.assertEqual(
            record["failure_stage"],
            "MARKDOWN_REPORT_FORMATTING_AFTER_CHARTS",
        )

    def test_03_attribution_completed_before_publication_failure(
        self,
    ) -> None:
        record = get_exp024_attempt_002_failure()
        self.assertTrue(record["attribution_calculated"])
        self.assertTrue(record["independent_rebuild_completed"])
        self.assertTrue(record["independent_rebuild_hashes_matched"])
        self.assertTrue(record["aggregation_all_ohlc_match"])
        self.assertEqual(record["aggregation_check_rows"], 4_709)

    def test_04_locked_diagnostic_failure_is_preserved(self) -> None:
        record = get_exp024_attempt_002_failure()
        self.assertEqual(record["reference_rebuild_match_rows"], 8)
        self.assertEqual(record["reference_rebuild_failure_rows"], 43)
        self.assertEqual(record["transfer_rebuild_match_rows"], 51)
        self.assertEqual(record["unresolved_rows"], 43)
        self.assertEqual(
            record["reconstructed_classification"],
            "ATTRIBUTION_DIAGNOSTIC_NOT_QUALIFIED",
        )

    def test_05_partial_artifact_hashes_are_locked(self) -> None:
        artifacts = get_exp024_attempt_002_failure()[
            "partial_artifacts"
        ]
        self.assertEqual(len(artifacts), 9)
        self.assertEqual(
            artifacts["mismatch_attribution.csv"]["sha256"],
            (
                "1f762b2cbb2d53c0cd979171a584a42f"
                "b3e8742040b2c3bb9494155e7d55dbae"
            ),
        )
        self.assertEqual(
            artifacts["aggregation_check.csv"]["size_bytes"],
            641_094,
        )

    def test_06_recovery_cannot_rerun_market_data(self) -> None:
        record = get_exp024_attempt_002_failure()
        self.assertTrue(record["replacement_authorization_consumed"])
        self.assertFalse(record["market_data_rerun_authorized"])
        self.assertTrue(record["evidence_only_recovery_authorized"])

    def test_07_hash_is_locked(self) -> None:
        record = get_exp024_attempt_002_failure()
        self.assertEqual(
            canonical_record_hash(record),
            EXPECTED_EXP024_ATTEMPT_002_FAILURE_SHA256,
        )

    def test_08_mutation_is_rejected(self) -> None:
        record = get_exp024_attempt_002_failure()
        record["market_data_rerun_authorized"] = True
        with self.assertRaisesRegex(
            ValueError,
            "attempt-002 boundary changed",
        ):
            validate_exp024_attempt_002_failure(record)


if __name__ == "__main__":
    unittest.main()
