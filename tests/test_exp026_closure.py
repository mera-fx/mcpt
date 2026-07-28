from __future__ import annotations

from copy import deepcopy
import unittest

from exp026_closure import (
    EXPECTED_EXP026_CLOSURE_SHA256,
    canonical_record_hash,
    get_exp026_closure,
    validate_exp026_closure,
)
from experiment_lifecycle import get_experiment_lifecycle
from exp026_phase_a_completion import get_exp026_phase_a_completion
from exp026_phase_b_completion import get_exp026_phase_b_completion
from exp026_phase_c_completion import get_exp026_phase_c_completion


EXPECTED_FINALISTS = (
    "gap_fade_0p75_1r",
    "opening_drive_0p75_time",
    "premarket_continuation_0p875_1p5r",
)


class Exp026ClosureTests(unittest.TestCase):
    def test_01_closure_is_valid(self) -> None:
        validate_exp026_closure()

    def test_02_classification_is_locked(self) -> None:
        record = get_exp026_closure()
        self.assertEqual(record["research_status"], "REVIEW")
        self.assertEqual(record["classification"], "COMPLETED_MEASUREMENT_REVIEW")

    def test_03_repository_chain_is_locked(self) -> None:
        repository = get_exp026_closure()["repository"]
        self.assertEqual(repository["preregistration_commit"], "ce661c7785fa6d8d409378ee2ad63a00f0e0a9b9")
        self.assertEqual(repository["implementation_commit"], "13ee0683dfcbbb5d763f7254f3b245ecc8e6d9cd")
        self.assertEqual(repository["phase_c_completion_commit"], "a400a373b87b780c21dc2d15048b1e1a5ad1050a")

    def test_04_all_phase_completions_are_locked(self) -> None:
        self.assertEqual(get_exp026_phase_a_completion()["completion_commit"], "28bd4209711f0c9b98a7650ab91f6408c2bdf4b7")
        self.assertEqual(get_exp026_phase_b_completion()["completion_commit"], "da8456d254dc710336806ad5940afcec649be016")
        self.assertEqual(get_exp026_phase_c_completion()["completion_commit"], "a400a373b87b780c21dc2d15048b1e1a5ad1050a")

    def test_05_phase_a_recovery_is_disclosed(self) -> None:
        phase_a = get_exp026_closure()["phase_a_development"]
        self.assertTrue(phase_a["presentation_recovery_used"])
        self.assertFalse(phase_a["recovery_read_market_values"])
        self.assertFalse(phase_a["recovery_recalculated_strategy"])

    def test_06_finalists_are_locked(self) -> None:
        record = get_exp026_closure()
        self.assertEqual(tuple(record["phase_b_internal_validation"]["finalist_candidate_ids"]), EXPECTED_FINALISTS)
        self.assertEqual(tuple(record["phase_c_known_comparison"]["finalist_candidate_ids"]), EXPECTED_FINALISTS)

    def test_07_mcpt_interpretation_is_locked(self) -> None:
        record = get_exp026_closure()
        phase_b = record["phase_b_internal_validation"]
        self.assertEqual(phase_b["mcpt_plus_one_p_value"], 0.46553446553446554)
        self.assertFalse(phase_b["robustness_results_were_decision_gates"])
        self.assertFalse(record["interpretation"]["selection_aware_mcpt_establishes_edge"])

    def test_08_known_period_is_not_confirmation(self) -> None:
        record = get_exp026_closure()
        self.assertFalse(record["phase_c_known_comparison"]["known_period_is_confirmation"])
        self.assertFalse(record["interpretation"]["known_2020_2025_is_independent_confirmation"])

    def test_09_no_strategy_is_accepted_for_trading(self) -> None:
        record = get_exp026_closure()
        interpretation = record["interpretation"]
        execution = record["execution"]
        self.assertFalse(interpretation["strategy_edge_validated"])
        self.assertFalse(interpretation["candidate_accepted_for_trading"])
        self.assertTrue(interpretation["no_strategy_is_accepted_for_trading_by_exp026"])
        self.assertFalse(execution["paper_trading_authorized"])
        self.assertFalse(execution["live_trading_authorized"])

    def test_10_lifecycle_matches_closure(self) -> None:
        lifecycle = get_experiment_lifecycle("EXP-026")
        self.assertEqual(lifecycle.stage, "REVIEW")
        self.assertIn("COMPLETED_MEASUREMENT_REVIEW", lifecycle.stage_reason)
        self.assertIn("EXP-027", lifecycle.next_action)
        self.assertIn("does not authorise EXP-027", lifecycle.next_action)

    def test_11_next_research_boundary_is_closed(self) -> None:
        boundary = get_exp026_closure()["next_research_boundary"]
        self.assertTrue(boundary["exp026_frozen"])
        self.assertTrue(boundary["rerun_phase_a_prohibited"])
        self.assertTrue(boundary["rerun_phase_b_prohibited"])
        self.assertTrue(boundary["rerun_phase_c_prohibited"])
        self.assertTrue(boundary["exp027_requires_separate_preregistration"])
        self.assertFalse(boundary["exp027_authorized_by_closure"])
        self.assertTrue(boundary["paper_or_live_trading_not_authorized"])

    def test_12_hash_rejects_mutation(self) -> None:
        record = get_exp026_closure()
        self.assertEqual(canonical_record_hash(record), EXPECTED_EXP026_CLOSURE_SHA256)
        changed = deepcopy(record)
        changed["execution"]["protected_2026_accessed"] = True
        with self.assertRaisesRegex(ValueError, "execution boundary changed"):
            validate_exp026_closure(changed)


if __name__ == "__main__":
    unittest.main()
