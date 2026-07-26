from __future__ import annotations

import unittest

from exp024_attempt_001_failure import (
    EXPECTED_EXP024_ATTEMPT_001_FAILURE_SHA256,
    canonical_record_hash,
    get_exp024_attempt_001_failure,
    validate_exp024_attempt_001_failure,
)


class Exp024Attempt001FailureTests(unittest.TestCase):
    def test_01_failure_record_is_valid(self) -> None:
        validate_exp024_attempt_001_failure()

    def test_02_execution_identity_is_locked(self) -> None:
        record = get_exp024_attempt_001_failure()
        self.assertEqual(record["experiment_id"], "EXP-024")
        self.assertEqual(record["attempt_id"], "EXP-024-ATTEMPT-001")
        self.assertEqual(
            record["execution_head"],
            "55ae174f5517bdb5afc48f5a36f5268fbc1eb42a",
        )
        self.assertEqual(
            record["implementation_commit"],
            "34f7d4c83dee025108229d5247e9cb4f87398a59",
        )
        self.assertEqual(
            record["authorization_id"],
            "EXP-024-ATTRIBUTION-AUTH-001",
        )

    def test_03_failure_preceded_attribution(self) -> None:
        record = get_exp024_attempt_001_failure()
        self.assertEqual(
            record["failure_stage"],
            "FIRST_QUANTOWER_CURRENT_WINDOW_AFTER_ARROW_TO_PANDAS",
        )
        self.assertEqual(record["exception_type"], "KeyError")
        self.assertEqual(record["exception_message"], "'timestamp'")
        self.assertFalse(record["feature_reconstruction_started"])
        self.assertFalse(record["attribution_calculated"])
        self.assertFalse(record["independent_rebuild_completed"])
        self.assertFalse(record["report_generated"])

    def test_04_materialized_boundary_is_exact(self) -> None:
        access = get_exp024_attempt_001_failure()[
            "market_value_access"
        ]
        self.assertTrue(
            access["quantower_current_mismatch_window_materialized"]
        )
        self.assertEqual(
            tuple(access["quantower_current_fields"]),
            ("open", "high", "low", "close"),
        )
        for key in (
            "quantower_entry_open_materialized",
            "quantower_previous_gap_cash_materialized",
            "quantower_five_minute_materialized",
            "databento_values_materialized",
            "non_mismatch_values_materialized",
            "current_post_entry_values_materialized",
            "out_of_overlap_values_materialized",
            "volume_materialized",
        ):
            with self.subTest(key=key):
                self.assertFalse(access[key])

    def test_05_no_output_or_frozen_mutation_occurred(self) -> None:
        record = get_exp024_attempt_001_failure()
        for key in (
            "final_output_created",
            "partial_output_created",
            "frozen_input_modified",
            "network_access",
            "strategy_replay",
            "performance_metric_calculated",
            "paper_or_live_action",
        ):
            with self.subTest(key=key):
                self.assertFalse(record[key])
        self.assertEqual(record["databento_api_calls"], 0)

    def test_06_original_authorization_is_consumed(self) -> None:
        record = get_exp024_attempt_001_failure()
        self.assertTrue(record["original_authorization_consumed"])
        self.assertFalse(record["retry_under_original_authorization"])

    def test_07_hash_is_locked(self) -> None:
        record = get_exp024_attempt_001_failure()
        self.assertEqual(
            canonical_record_hash(record),
            EXPECTED_EXP024_ATTEMPT_001_FAILURE_SHA256,
        )

    def test_08_mutation_is_rejected(self) -> None:
        record = get_exp024_attempt_001_failure()
        record["attribution_calculated"] = True
        with self.assertRaisesRegex(
            ValueError,
            "attempt-001 boundary changed",
        ):
            validate_exp024_attempt_001_failure(record)


if __name__ == "__main__":
    unittest.main()
