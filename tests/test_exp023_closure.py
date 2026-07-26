from __future__ import annotations

import unittest

from exp023_closure import (
    EXPECTED_EXP023_CLOSURE_SHA256,
    canonical_record_hash,
    get_exp023_closure,
    validate_exp023_closure,
)


class Exp023ClosureTests(unittest.TestCase):
    def test_01_closure_is_valid(self) -> None:
        validate_exp023_closure()

    def test_02_identity_and_classification_are_locked(self) -> None:
        record = get_exp023_closure()
        self.assertEqual(record["experiment_id"], "EXP-023")
        self.assertEqual(record["research_status"], "REVIEW")
        self.assertEqual(
            record["classification"],
            "TRANSFER_DIAGNOSTIC_COMPLETE_WITH_MATERIAL_DIFFERENCES",
        )

    def test_03_repository_chain_is_locked(self) -> None:
        repository = get_exp023_closure()["repository"]
        self.assertEqual(
            repository["preregistration_commit"],
            "66ba6a46f31cc8715447179c19caf2f4c1a1e8be",
        )
        self.assertEqual(
            repository["implementation_commit"],
            "c17e9ea567c234e2d941f949168d62721f6d4963",
        )
        self.assertEqual(
            repository["authorization_commit"],
            "9dbce86c040fa468a55fdb53501a13a0c74609f5",
        )
        self.assertEqual(
            repository["execution_head"],
            repository["authorization_commit"],
        )

    def test_04_one_run_and_all_hard_checks_are_locked(self) -> None:
        execution = get_exp023_closure()["execution"]
        self.assertEqual(execution["authorized_run_count"], 1)
        self.assertEqual(execution["hard_check_count"], 20)
        self.assertEqual(execution["hard_failure_count"], 0)
        self.assertTrue(execution["independent_rebuild"])
        self.assertTrue(
            execution["independent_rebuild_hashes_match"]
        )
        self.assertTrue(execution["transfer_diagnostic_complete"])
        self.assertFalse(execution["rerun_authorized"])

    def test_05_all_three_primary_rows_remain_separate(self) -> None:
        results = get_exp023_closure()["primary_candidate_results"]
        self.assertEqual(
            tuple(row["candidate_id"] for row in results),
            (
                "gap_fade_0p50_1r",
                "premarket_continuation_0p50_time",
                "premarket_continuation_0p75_time",
            ),
        )
        self.assertEqual(
            tuple(row["all_transfer_gates_pass"] for row in results),
            (False, True, False),
        )

    def test_06_failed_gates_are_locked(self) -> None:
        results = get_exp023_closure()["primary_candidate_results"]
        self.assertEqual(
            results[0]["failed_gates"],
            (
                "trade_indicator_and_direction_agreement",
                "trade_count_relative_difference",
                "common_trade_match_share",
            ),
        )
        self.assertEqual(results[1]["failed_gates"], ())
        self.assertEqual(
            results[2]["failed_gates"],
            ("trade_count_relative_difference",),
        )
        self.assertAlmostEqual(
            results[2]["trade_count_relative_difference"],
            1 / 88,
        )

    def test_07_secondary_representation_does_not_change_outcome(
        self,
    ) -> None:
        results = get_exp023_closure()[
            "secondary_representation_results"
        ]
        self.assertEqual(
            tuple(row["all_transfer_gates_pass"] for row in results),
            (False, True, False),
        )

    def test_08_all_twenty_output_files_are_locked(self) -> None:
        record = get_exp023_closure()
        outputs = record["output_files"]
        self.assertEqual(len(outputs), 20)
        self.assertEqual(
            outputs["output_hashes.json"]["sha256"],
            record["output_manifest_sha256"],
        )
        self.assertEqual(
            outputs["TRANSFER_DIAGNOSTIC_COMPLETE.json"]["sha256"],
            (
                "aac79a622ee09618d304a0c7b5cf41d6"
                "f810c1fcf7ffb58b63f16fc2cf78e150"
            ),
        )

    def test_09_no_protected_or_trading_authorization_exists(
        self,
    ) -> None:
        record = get_exp023_closure()
        execution = record["execution"]
        interpretation = record["interpretation"]
        self.assertFalse(execution["protected_history_accessed"])
        self.assertFalse(execution["network_access"])
        self.assertEqual(execution["databento_api_calls"], 0)
        self.assertFalse(
            interpretation["protected_history_validation_authorized"]
        )
        self.assertFalse(
            interpretation["automatic_candidate_promotion_authorized"]
        )
        self.assertFalse(
            interpretation["paper_trading_authorized"]
        )
        self.assertFalse(
            interpretation["live_trading_authorized"]
        )

    def test_10_hash_and_next_boundary_are_locked(self) -> None:
        record = get_exp023_closure()
        self.assertEqual(
            canonical_record_hash(record),
            EXPECTED_EXP023_CLOSURE_SHA256,
        )
        boundary = record["next_research_boundary"]
        self.assertTrue(boundary["exp023_frozen"])
        self.assertTrue(boundary["rerun_exp023_prohibited"])
        self.assertTrue(boundary["protected_history_remains_locked"])
        self.assertTrue(boundary["new_experiment_id_required"])
        record["execution"]["authorized_run_count"] += 1
        with self.assertRaisesRegex(
            ValueError,
            "closure record changed",
        ):
            validate_exp023_closure(record)


if __name__ == "__main__":
    unittest.main()
