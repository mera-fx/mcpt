from __future__ import annotations

from copy import deepcopy
import unittest

from exp026_phase_a_completion import (
    EXPECTED_EXP026_PHASE_A_COMPLETION_SHA256,
    EXPECTED_OUTPUT_FILES,
    UNCOMMITTED_COMPLETION_COMMIT,
    canonical_record_hash,
    get_exp026_phase_a_completion,
    resolve_exp026_phase_a_completion_commit,
    validate_exp026_phase_a_completion,
)
from exp026_runner import (
    PHASE_OUTPUT_DIRS,
    PHASE_PARTIAL_DIRS,
    load_phase_completion,
)


EXPECTED_SURVIVORS = (
    "gap_fade_0p75_1r",
    "gap_fade_0p25_1r",
    "opening_drive_0p75_1p5r",
    "opening_drive_0p75_time",
    "premarket_continuation_0p875_1p5r",
    "premarket_continuation_0p625_1p5r",
)


class Exp026PhaseACompletionTests(unittest.TestCase):
    def test_01_completion_is_valid(self) -> None:
        validate_exp026_phase_a_completion()

    def test_02_identity_and_ancestry_are_locked(
        self,
    ) -> None:
        record = get_exp026_phase_a_completion()

        self.assertEqual(
            record["experiment_id"],
            "EXP-026",
        )
        self.assertEqual(record["phase"], "A")
        self.assertTrue(record["completed"])
        self.assertEqual(
            record["implementation_commit"],
            "13ee0683dfcbbb5d763f7254f3b245ecc8e6d9cd",
        )
        self.assertEqual(
            record["authorization_commit"],
            "5fa417ed56c2d620c5d348e9ab43f3d7634518b8",
        )
        self.assertEqual(
            record["recovery_commit"],
            "d54289659ffa058ae31558ad3b99b646c31d0bf7",
        )

    def test_03_output_files_are_exact(self) -> None:
        output_dir = PHASE_OUTPUT_DIRS["A"]

        self.assertTrue(output_dir.is_dir())
        self.assertFalse(
            PHASE_PARTIAL_DIRS["A"].exists()
        )
        self.assertEqual(
            {
                path.name
                for path in output_dir.iterdir()
                if path.is_file()
            },
            set(EXPECTED_OUTPUT_FILES),
        )

    def test_04_counts_and_survivors_are_locked(
        self,
    ) -> None:
        record = get_exp026_phase_a_completion()

        self.assertEqual(
            record["decision_rows"],
            46584,
        )
        self.assertEqual(
            record["trade_rows"],
            11502,
        )
        self.assertEqual(
            tuple(
                record["survivor_candidate_ids"]
            ),
            EXPECTED_SURVIVORS,
        )

    def test_05_runner_accepts_completion_interface(
        self,
    ) -> None:
        record = load_phase_completion("A")

        self.assertTrue(record["completed"])
        self.assertFalse(
            record["protected_2026_accessed"]
        )
        self.assertFalse(
            record["paper_trading_authorized"]
        )
        self.assertFalse(
            record["live_trading_authorized"]
        )

    def test_06_completion_commit_resolution_is_safe(
        self,
    ) -> None:
        value = (
            resolve_exp026_phase_a_completion_commit()
        )

        self.assertEqual(len(value), 40)
        self.assertTrue(
            value == UNCOMMITTED_COMPLETION_COMMIT
            or all(
                character in "0123456789abcdef"
                for character in value.lower()
            )
        )

    def test_07_later_phases_remain_unauthorized(
        self,
    ) -> None:
        record = get_exp026_phase_a_completion()

        self.assertFalse(
            record["phase_b_execution_authorized"]
        )
        self.assertFalse(
            record["phase_c_execution_authorized"]
        )

    def test_08_protected_and_trading_boundaries_hold(
        self,
    ) -> None:
        record = get_exp026_phase_a_completion()

        for field in (
            "protected_2026_accessed",
            "protected_2026_access_authorized",
            "new_databento_download_authorized",
            "network_access",
            "paper_trading_authorized",
            "live_trading_authorized",
        ):
            self.assertFalse(record[field])

        self.assertEqual(
            record["databento_api_calls"],
            0,
        )

    def test_09_recovery_is_disclosed(self) -> None:
        record = get_exp026_phase_a_completion()

        self.assertEqual(
            record["recovery_id"],
            "EXP-026-A-R1",
        )
        self.assertFalse(
            record["recovery_read_market_values"]
        )
        self.assertFalse(
            record["recovery_recalculated_strategy"]
        )

    def test_10_hash_rejects_mutation(self) -> None:
        record = get_exp026_phase_a_completion()
        record.pop("completion_commit")

        self.assertEqual(
            canonical_record_hash(record),
            EXPECTED_EXP026_PHASE_A_COMPLETION_SHA256,
        )

        changed = deepcopy(record)
        changed["trade_rows"] = 11503

        with self.assertRaisesRegex(
            ValueError,
            "completion evidence changed",
        ):
            validate_exp026_phase_a_completion(
                changed
            )


if __name__ == "__main__":
    unittest.main()
