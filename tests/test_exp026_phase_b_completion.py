from __future__ import annotations

from copy import deepcopy
import unittest

from exp026_phase_b_completion import (
    EXPECTED_EXP026_PHASE_B_COMPLETION_SHA256,
    EXPECTED_OUTPUT_FILES,
    UNCOMMITTED_COMPLETION_COMMIT,
    canonical_record_hash,
    get_exp026_phase_b_completion,
    resolve_exp026_phase_b_completion_commit,
    validate_exp026_phase_b_completion,
)
from exp026_runner import (
    PHASE_OUTPUT_DIRS,
    PHASE_PARTIAL_DIRS,
    _locked_phase_b_finalists,
    load_phase_completion,
)

EXPECTED_FINALISTS = (
    "gap_fade_0p75_1r",
    "opening_drive_0p75_time",
    "premarket_continuation_0p875_1p5r",
)


class Exp026PhaseBCompletionTests(unittest.TestCase):
    def test_01_completion_is_valid(self) -> None:
        validate_exp026_phase_b_completion()

    def test_02_identity_and_ancestry_are_locked(self) -> None:
        record = get_exp026_phase_b_completion()
        self.assertEqual(record["experiment_id"], "EXP-026")
        self.assertEqual(record["phase"], "B")
        self.assertTrue(record["completed"])
        self.assertEqual(
            record["authorization_commit"],
            "20ed5ba203f2e4bb3940de389afface6b749d7c7",
        )

    def test_03_output_files_are_exact(self) -> None:
        output_dir = PHASE_OUTPUT_DIRS["B"]
        self.assertTrue(output_dir.is_dir())
        self.assertFalse(PHASE_PARTIAL_DIRS["B"].exists())
        actual = {
            str(path.relative_to(output_dir)).replace("\\", "/")
            for path in output_dir.rglob("*")
            if path.is_file()
        }
        self.assertEqual(actual, set(EXPECTED_OUTPUT_FILES))

    def test_04_finalists_are_locked(self) -> None:
        record = get_exp026_phase_b_completion()
        self.assertEqual(record["finalist_count"], 3)
        self.assertEqual(
            tuple(record["finalist_candidate_ids"]),
            EXPECTED_FINALISTS,
        )

    def test_05_runner_accepts_completion_interface(self) -> None:
        record = load_phase_completion("B")
        self.assertTrue(record["completed"])
        self.assertFalse(record["protected_2026_accessed"])
        self.assertFalse(record["paper_trading_authorized"])
        self.assertFalse(record["live_trading_authorized"])

    def test_06_runner_accepts_finalist_population(self) -> None:
        record = get_exp026_phase_b_completion()
        self.assertEqual(
            _locked_phase_b_finalists(record),
            EXPECTED_FINALISTS,
        )

    def test_07_robustness_is_frozen(self) -> None:
        record = get_exp026_phase_b_completion()
        self.assertEqual(record["mcpt_permutations"], 1000)
        self.assertEqual(
            record["mcpt_permutations_greater_or_equal_real"],
            465,
        )
        self.assertEqual(
            record["mcpt_plus_one_p_value"],
            0.46553446553446554,
        )
        self.assertFalse(record["robustness_results_are_decision_gates"])

    def test_08_phase_c_and_protected_access_remain_closed(self) -> None:
        record = get_exp026_phase_b_completion()
        for field in (
            "known_2020_2025_accessed",
            "known_2020_2025_access_authorized",
            "phase_c_execution_authorized",
            "protected_2026_accessed",
            "protected_2026_access_authorized",
            "new_databento_download_authorized",
            "network_access",
            "paper_trading_authorized",
            "live_trading_authorized",
        ):
            self.assertFalse(record[field])
        self.assertEqual(record["databento_api_calls"], 0)

    def test_09_completion_commit_resolution_is_safe(self) -> None:
        value = resolve_exp026_phase_b_completion_commit()
        self.assertEqual(len(value), 40)
        self.assertTrue(
            value == UNCOMMITTED_COMPLETION_COMMIT
            or all(ch in "0123456789abcdef" for ch in value.lower())
        )

    def test_10_hash_rejects_mutation(self) -> None:
        record = get_exp026_phase_b_completion()
        record.pop("completion_commit")
        self.assertEqual(
            canonical_record_hash(record),
            EXPECTED_EXP026_PHASE_B_COMPLETION_SHA256,
        )
        changed = deepcopy(record)
        changed["known_2020_2025_accessed"] = True
        with self.assertRaisesRegex(ValueError, "protected boundary changed"):
            validate_exp026_phase_b_completion(changed)


if __name__ == "__main__":
    unittest.main()
