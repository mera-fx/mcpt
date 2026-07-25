from __future__ import annotations

import unittest

from exp019_archive_audit_preregistration import (
    get_exp019_archive_audit_preregistration,
    validate_exp019_archive_audit_preregistration,
)


class Exp019ArchiveAuditPreregistrationTests(
    unittest.TestCase
):
    def test_preregistration_is_valid(self):
        validate_exp019_archive_audit_preregistration()

    def test_acquisition_evidence_is_locked(self):
        record = (
            get_exp019_archive_audit_preregistration()
        )
        evidence = record[
            "acquisition_evidence"
        ]

        self.assertEqual(
            evidence["raw_file_count"],
            66,
        )
        self.assertEqual(
            evidence["compressed_total_bytes"],
            104491346,
        )
        self.assertEqual(
            evidence["automatic_retries"],
            0,
        )
        self.assertEqual(
            len(
                evidence["archive_sha256"]
            ),
            64,
        )

    def test_audit_is_local_and_read_only(self):
        scope = (
            get_exp019_archive_audit_preregistration()[
                "scope"
            ]
        )

        self.assertTrue(
            scope["local_files_only"]
        )
        self.assertEqual(
            scope["databento_api_calls"],
            0,
        )
        self.assertFalse(
            scope["credentials_required"]
        )
        self.assertFalse(
            scope["files_modified"]
        )

    def test_hard_checks_are_locked(self):
        checks = (
            get_exp019_archive_audit_preregistration()[
                "hard_failure_checks"
            ]
        )

        self.assertEqual(
            len(checks),
            17,
        )
        self.assertIn(
            "dbn_readability",
            checks,
        )
        self.assertIn(
            "duplicate_timestamps",
            checks,
        )
        self.assertIn(
            "ohlc_invariants",
            checks,
        )
        self.assertIn(
            "nq_quarter_point_tick_alignment",
            checks,
        )

    def test_minute_gaps_are_diagnostic(self):
        record = (
            get_exp019_archive_audit_preregistration()
        )

        interpretation = record[
            "missing_minute_interpretation"
        ]

        self.assertTrue(
            interpretation[
                "absence_is_not_automatically_failure"
            ]
        )

    def test_provider_warnings_are_preserved(self):
        record = (
            get_exp019_archive_audit_preregistration()
        )

        warnings = record[
            "known_provider_conditions"
        ]

        self.assertEqual(
            warnings["warning_windows_observed"],
            16,
        )
        self.assertTrue(
            warnings[
                "terminal_warning_output_not_exhaustive"
            ]
        )
        self.assertGreater(
            len(warnings["degraded_examples"]),
            0,
        )
        self.assertGreater(
            len(warnings["missing_examples"]),
            0,
        )

    def test_strategy_work_remains_prohibited(self):
        record = (
            get_exp019_archive_audit_preregistration()
        )

        prohibited = record[
            "prohibited_actions"
        ]

        self.assertTrue(
            prohibited[
                "continuous_series_construction"
            ]
        )
        self.assertTrue(
            prohibited["strategy_replay"]
        )
        self.assertTrue(
            prohibited["strategy_optimization"]
        )
        self.assertTrue(
            prohibited["paper_trading"]
        )
        self.assertTrue(
            prohibited["live_trading"]
        )

    def test_mutation_is_rejected(self):
        record = (
            get_exp019_archive_audit_preregistration()
        )

        record["scope"][
            "databento_api_calls"
        ] = 1

        with self.assertRaisesRegex(
            ValueError,
            "scope",
        ):
            validate_exp019_archive_audit_preregistration(
                record
            )


if __name__ == "__main__":
    unittest.main()
