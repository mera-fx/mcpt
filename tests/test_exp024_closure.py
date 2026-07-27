from __future__ import annotations

from copy import deepcopy
import unittest

from exp024_closure import (
    EXPECTED_EXP024_CLOSURE_SHA256,
    canonical_record_hash,
    get_exp024_closure,
    validate_exp024_closure,
)


class Exp024ClosureTests(unittest.TestCase):
    def test_01_closure_is_valid(self) -> None:
        validate_exp024_closure()

    def test_02_identity_and_classification_are_locked(self) -> None:
        record = get_exp024_closure()
        self.assertEqual(record["experiment_id"], "EXP-024")
        self.assertEqual(record["research_status"], "REVIEW")
        self.assertEqual(
            record["classification"],
            "ATTRIBUTION_DIAGNOSTIC_NOT_QUALIFIED",
        )

    def test_03_repository_chain_is_locked(self) -> None:
        repository = get_exp024_closure()["repository"]
        self.assertEqual(
            repository["preregistration_commit"],
            "37a6d007b103bb5baddfdbbe471a8b6626b8a35c",
        )
        self.assertEqual(
            repository["attempt_002_failure_commit"],
            "7acf180c9640079c560c992a00c4fd413f3b13b7",
        )
        self.assertEqual(
            repository["evidence_recovery_implementation_commit"],
            "a57ebcbc237e2e8e8696e9d6b3b13f584102beee",
        )
        self.assertEqual(
            repository["evidence_recovery_authorization_commit"],
            "b885c3fd8342d9d656c175c4c66f837954eb9452",
        )
        self.assertEqual(
            repository["evidence_recovery_execution_head"],
            repository["evidence_recovery_authorization_commit"],
        )

    def test_04_attempt_and_recovery_counts_are_locked(self) -> None:
        execution = get_exp024_closure()["execution"]
        self.assertTrue(execution["attempt_001_authorized"])
        self.assertFalse(execution["attempt_001_attribution_calculated"])
        self.assertTrue(execution["attempt_002_authorized"])
        self.assertTrue(execution["attempt_002_attribution_calculated"])
        self.assertTrue(
            execution["independent_attribution_rebuild_hashes_match"]
        )
        self.assertEqual(execution["publication_recovery_count"], 1)
        self.assertTrue(execution["publication_complete"])
        self.assertFalse(execution["rerun_authorized"])

    def test_05_diagnostic_counts_are_locked(self) -> None:
        result = get_exp024_closure()["diagnostic_result"]
        self.assertEqual(result["candidate_session_row_count"], 51)
        self.assertEqual(result["feature_row_count"], 153)
        self.assertEqual(result["raw_component_difference_row_count"], 1530)
        self.assertEqual(result["roll_context_row_count"], 51)
        self.assertEqual(result["aggregation_check_row_count"], 4709)
        self.assertEqual(result["reference_rebuild_match_rows"], 8)
        self.assertEqual(result["reference_rebuild_failure_rows"], 43)
        self.assertEqual(result["transfer_rebuild_match_rows"], 51)
        self.assertEqual(result["unresolved_rows"], 43)

    def test_06_category_counts_are_locked(self) -> None:
        counts = get_exp024_closure()["diagnostic_result"]["category_counts"]
        self.assertEqual(counts["ELIGIBILITY_DIFFERENCE"], 1)
        self.assertEqual(
            counts["NORMALIZED_CONTEXT_THRESHOLD_CROSSING"],
            5,
        )
        self.assertEqual(
            counts["MULTIPLE_DECISION_COMPONENT_DIFFERENCES"],
            2,
        )
        self.assertEqual(
            counts["UNRESOLVED_WITH_LOCKED_FEATURES"],
            43,
        )
        self.assertEqual(sum(counts.values()), 51)

    def test_07_hard_failure_is_locked(self) -> None:
        record = get_exp024_closure()
        execution = record["execution"]
        result = record["diagnostic_result"]
        self.assertEqual(execution["original_locked_hard_check_count"], 26)
        self.assertEqual(execution["diagnostic_hard_failure_count"], 1)
        self.assertEqual(execution["recovery_hard_failure_count"], 0)
        self.assertEqual(
            result["failed_hard_check"],
            "reference_decision_rebuild_matches_frozen_alignment",
        )
        self.assertTrue(result["reference_failures_all_gap_fade"])
        self.assertFalse(execution["diagnostic_qualified"])

    def test_08_all_fourteen_outputs_are_locked(self) -> None:
        record = get_exp024_closure()
        outputs = record["output_files"]
        self.assertEqual(len(outputs), 14)
        self.assertEqual(
            outputs["output_hashes.json"]["sha256"],
            record["output_manifest_sha256"],
        )
        self.assertEqual(
            outputs["ATTRIBUTION_DIAGNOSTIC_COMPLETE.json"]["sha256"],
            record["completion_marker_sha256"],
        )
        self.assertEqual(
            outputs["report.md"]["sha256"],
            "d5e796c6fc17375ca6d735e0c932d49ec0197ea6d3d5bb5dba35e0b4307b4571",
        )

    def test_09_original_nine_artifacts_remain_locked(self) -> None:
        outputs = get_exp024_closure()["output_files"]
        self.assertEqual(
            outputs["mismatch_attribution.csv"]["sha256"],
            "1f762b2cbb2d53c0cd979171a584a42fb3e8742040b2c3bb9494155e7d55dbae",
        )
        self.assertEqual(
            outputs["aggregation_check.csv"]["sha256"],
            "c2c693c142a076db404739047f8e683cb63e1c218f057e1c3d46b9c20f63a7fa",
        )
        self.assertEqual(
            outputs["assets/threshold_margins.png"]["sha256"],
            "f7489bb363b51e9a6250a53ca262d545c3dbf6cac93fa09b31132cd056dde7a6",
        )

    def test_10_no_source_strategy_or_trading_selection_exists(self) -> None:
        interpretation = get_exp024_closure()["interpretation"]
        self.assertFalse(interpretation["source_equivalence_established"])
        self.assertFalse(interpretation["source_winner_selected"])
        self.assertFalse(interpretation["candidate_winner_selected"])
        self.assertFalse(interpretation["strategy_edge_validated"])
        self.assertFalse(interpretation["protected_history_unlocked"])
        self.assertFalse(interpretation["paper_trading_authorized"])
        self.assertFalse(interpretation["live_trading_authorized"])

    def test_11_next_boundary_is_locked(self) -> None:
        boundary = get_exp024_closure()["next_research_boundary"]
        self.assertTrue(boundary["exp024_frozen"])
        self.assertTrue(boundary["rerun_any_exp024_mode_prohibited"])
        self.assertTrue(boundary["rerun_evidence_recovery_prohibited"])
        self.assertTrue(boundary["modify_exp024_outputs_prohibited"])
        self.assertTrue(boundary["new_experiment_id_required"])
        self.assertTrue(boundary["exp025_or_later_preregistration_required"])
        self.assertTrue(boundary["paper_or_live_trading_not_authorized"])

    def test_12_hash_rejects_mutation(self) -> None:
        record = get_exp024_closure()
        self.assertEqual(
            canonical_record_hash(record),
            EXPECTED_EXP024_CLOSURE_SHA256,
        )
        changed = deepcopy(record)
        changed["execution"]["publication_recovery_count"] = 2
        with self.assertRaisesRegex(
            ValueError,
            "result boundary changed",
        ):
            validate_exp024_closure(changed)


if __name__ == "__main__":
    unittest.main()
