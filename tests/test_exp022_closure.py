from __future__ import annotations

import unittest

from exp022_closure import (
    EXPECTED_EXP022_CLOSURE_SHA256,
    canonical_record_hash,
    get_exp022_closure,
    validate_exp022_closure,
)


class Exp022ClosureTests(unittest.TestCase):
    def test_01_closure_is_valid(self):
        validate_exp022_closure()

    def test_02_identity_and_classification_are_locked(self):
        record = get_exp022_closure()
        self.assertEqual(record["experiment_id"], "EXP-022")
        self.assertEqual(record["research_status"], "REVIEW")
        self.assertEqual(
            record["classification"],
            "QUALIFIED_AS_SELECTED_VOLUME_ROLL_CONTINUOUS_SERIES",
        )

    def test_03_repository_chain_is_locked(self):
        repository = get_exp022_closure()["repository"]
        self.assertEqual(
            repository["preregistration_commit"],
            "73c1255bcb904e71d927ed1097788de9b791bb54",
        )
        self.assertEqual(
            repository["implementation_commit"],
            "6dd69307c3dcfed876c57d6f62ae6d98bcb6ad93",
        )
        self.assertEqual(
            repository["authorization_commit"],
            "22d89d7d4521c7f34283fe01342377dceb286b94",
        )
        self.assertEqual(
            repository["construction_head"],
            repository["authorization_commit"],
        )

    def test_04_source_and_construction_counts_are_locked(self):
        record = get_exp022_closure()
        self.assertEqual(record["source"]["contract_count"], 66)
        self.assertEqual(record["source"]["record_count"], 6_276_486)
        construction = record["construction"]
        self.assertEqual(construction["series_count"], 2)
        self.assertEqual(
            construction["row_count_per_series"],
            5_457_606,
        )
        self.assertEqual(construction["transition_count"], 65)

    def test_05_selected_transition_counts_are_locked(self):
        construction = get_exp022_closure()["construction"]
        self.assertEqual(
            (
                construction["clean_transition_count"],
                construction["volume_driven_transition_count"],
                construction["calendar_fallback_count"],
                construction["warning_calendar_fallback_count"],
                construction["clean_calendar_fallback_count"],
            ),
            (42, 40, 25, 23, 2),
        )

    def test_06_hard_checks_and_rebuild_are_locked(self):
        construction = get_exp022_closure()["construction"]
        self.assertEqual(construction["hard_checks"], 20)
        self.assertEqual(construction["hard_failure_count"], 0)
        self.assertTrue(construction["independent_rebuild"])
        self.assertTrue(construction["construction_complete"])
        self.assertFalse(
            construction["construction_rerun_authorized"]
        )

    def test_07_all_eight_output_files_are_locked(self):
        outputs = get_exp022_closure()["output_files"]
        self.assertEqual(len(outputs), 8)
        self.assertEqual(
            outputs["selected_roll_unadjusted.parquet"][
                "size_bytes"
            ],
            73_760_121,
        )
        self.assertEqual(
            outputs["selected_roll_backward_adjusted.parquet"][
                "size_bytes"
            ],
            71_964_074,
        )

    def test_08_semantic_hashes_are_locked(self):
        semantic = get_exp022_closure()["semantic_hashes"]
        self.assertEqual(len(semantic), 3)
        self.assertEqual(
            semantic["roll_ledger_semantic_sha256"],
            "c800004230ae0db630a4414db81d1c030c02976ec06c47731ba4384265069090",
        )

    def test_09_no_strategy_or_trading_authorization_exists(self):
        record = get_exp022_closure()
        interpretation = record["interpretation"]
        self.assertFalse(interpretation["strategy_edge_tested"])
        self.assertFalse(interpretation["strategy_run"])
        self.assertFalse(
            interpretation["strategy_use_authorized"]
        )
        self.assertFalse(
            interpretation["paper_trading_authorized"]
        )
        self.assertFalse(
            interpretation["live_trading_authorized"]
        )
        self.assertEqual(
            record["construction"]["databento_api_calls"],
            0,
        )

    def test_10_hash_and_next_boundary_are_locked(self):
        record = get_exp022_closure()
        self.assertEqual(
            canonical_record_hash(record),
            EXPECTED_EXP022_CLOSURE_SHA256,
        )
        boundary = record["next_research_boundary"]
        self.assertTrue(boundary["exp022_frozen"])
        self.assertTrue(boundary["rerun_exp022_prohibited"])
        self.assertTrue(
            boundary["exp023_preregistration_required"]
        )
        record["construction"]["row_count_per_series"] += 1
        with self.assertRaisesRegex(
            ValueError,
            "closure record changed",
        ):
            validate_exp022_closure(record)


if __name__ == "__main__":
    unittest.main()
