from __future__ import annotations

from copy import deepcopy
import unittest

from exp026_phase_c_completion import (
    EXPECTED_EXP026_PHASE_C_COMPLETION_SHA256,
    EXPECTED_OUTPUT_FILES,
    UNCOMMITTED_COMPLETION_COMMIT,
    canonical_record_hash,
    get_exp026_phase_c_completion,
    resolve_exp026_phase_c_completion_commit,
    validate_exp026_phase_c_completion,
)
from exp026_runner import (
    PHASE_OUTPUT_DIRS,
    PHASE_PARTIAL_DIRS,
)


EXPECTED_FINALISTS = (
    "gap_fade_0p75_1r",
    "opening_drive_0p75_time",
    "premarket_continuation_0p875_1p5r",
)

EXPECTED_CONTROLS = (
    "orb_control_exp005_15m_both_time",
    "orb_control_exp007_30m_long_1r",
)


class Exp026PhaseCCompletionTests(
    unittest.TestCase
):
    def test_01_completion_is_valid(
        self,
    ) -> None:
        validate_exp026_phase_c_completion()

    def test_02_identity_and_ancestry_are_locked(
        self,
    ) -> None:
        record = (
            get_exp026_phase_c_completion()
        )

        self.assertEqual(
            record["experiment_id"],
            "EXP-026",
        )
        self.assertEqual(
            record["phase"],
            "C",
        )
        self.assertTrue(
            record["completed"]
        )
        self.assertEqual(
            record[
                "authorization_commit"
            ],
            "5e03bb449468b980e003c133ce076cf1b87b3ac7",
        )

    def test_03_output_files_are_exact(
        self,
    ) -> None:
        output_dir = PHASE_OUTPUT_DIRS["C"]

        self.assertTrue(
            output_dir.is_dir()
        )
        self.assertFalse(
            PHASE_PARTIAL_DIRS["C"].exists()
        )
        self.assertEqual(
            {
                str(
                    path.relative_to(
                        output_dir
                    )
                ).replace(
                    "\\",
                    "/",
                )
                for path in output_dir.rglob("*")
                if path.is_file()
            },
            set(EXPECTED_OUTPUT_FILES),
        )

    def test_04_candidates_are_locked(
        self,
    ) -> None:
        record = (
            get_exp026_phase_c_completion()
        )

        self.assertEqual(
            tuple(
                record[
                    "finalist_candidate_ids"
                ]
            ),
            EXPECTED_FINALISTS,
        )
        self.assertEqual(
            tuple(
                record[
                    "control_candidate_ids"
                ]
            ),
            EXPECTED_CONTROLS,
        )

    def test_05_period_and_interpretation_are_locked(
        self,
    ) -> None:
        record = (
            get_exp026_phase_c_completion()
        )

        self.assertEqual(
            record[
                "known_comparison_start"
            ],
            "2020-01-03",
        )
        self.assertEqual(
            record[
                "known_comparison_end"
            ],
            "2025-12-31",
        )
        self.assertFalse(
            record[
                "known_period_is_confirmation"
            ]
        )

    def test_06_no_reselection_or_parameter_changes(
        self,
    ) -> None:
        record = (
            get_exp026_phase_c_completion()
        )

        self.assertFalse(
            record[
                "candidate_reselection"
            ]
        )
        self.assertFalse(
            record[
                "parameter_changes"
            ]
        )
        self.assertTrue(
            record[
                "independent_rebuild"
            ]
        )

    def test_07_protected_and_trading_boundaries_hold(
        self,
    ) -> None:
        record = (
            get_exp026_phase_c_completion()
        )

        for field in (
            "protected_2026_accessed",
            "protected_2026_access_authorized",
            "exp027_execution_authorized",
            "new_databento_download_authorized",
            "network_access",
            "paper_trading_authorized",
            "live_trading_authorized",
            "exp026_closed",
        ):
            self.assertFalse(
                record[field]
            )

        self.assertEqual(
            record[
                "databento_api_calls"
            ],
            0,
        )

    def test_08_completion_commit_resolution_is_safe(
        self,
    ) -> None:
        value = (
            resolve_exp026_phase_c_completion_commit()
        )

        self.assertEqual(
            len(value),
            40,
        )
        self.assertTrue(
            value
            == UNCOMMITTED_COMPLETION_COMMIT
            or all(
                character
                in "0123456789abcdef"
                for character
                in value.lower()
            )
        )

    def test_09_output_manifest_and_marker_are_frozen(
        self,
    ) -> None:
        record = (
            get_exp026_phase_c_completion()
        )

        self.assertEqual(
            record[
                "output_manifest_sha256"
            ],
            EXPECTED_OUTPUT_FILES[
                "output_hashes.json"
            ]["sha256"],
        )
        self.assertEqual(
            record[
                "completion_marker_sha256"
            ],
            EXPECTED_OUTPUT_FILES[
                "PHASE_C_COMPLETE.json"
            ]["sha256"],
        )

    def test_10_hash_rejects_mutation(
        self,
    ) -> None:
        record = (
            get_exp026_phase_c_completion()
        )
        record.pop(
            "completion_commit"
        )

        self.assertEqual(
            canonical_record_hash(record),
            EXPECTED_EXP026_PHASE_C_COMPLETION_SHA256,
        )

        changed = deepcopy(record)
        changed[
            "protected_2026_accessed"
        ] = True

        with self.assertRaisesRegex(
            ValueError,
            "protected boundary changed",
        ):
            validate_exp026_phase_c_completion(
                changed
            )


if __name__ == "__main__":
    unittest.main()
