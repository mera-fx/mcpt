from __future__ import annotations

import unittest

from exp020_preflight_correction_authorization import (
    LOCKED_CORRECTED_IMPLEMENTATION_COMMIT,
    LOCKED_ORIGINAL_AUTHORIZATION_COMMIT,
    get_exp020_preflight_correction_authorization,
    validate_exp020_preflight_correction_authorization,
)
from exp020_constructor import (
    load_preflight_correction_authorization,
)


class Exp020PreflightCorrectionAuthorizationTests(
    unittest.TestCase
):
    def test_authorization_is_valid(self):
        validate_exp020_preflight_correction_authorization()

    def test_exact_commits_are_locked(self):
        self.assertEqual(
            LOCKED_ORIGINAL_AUTHORIZATION_COMMIT,
            (
                "e497b1abf247ed83295caa9378c2a4e6"
                "869922b1"
            ),
        )
        self.assertEqual(
            LOCKED_CORRECTED_IMPLEMENTATION_COMMIT,
            (
                "fde5ee88b306f97b9e567fabe1b12267"
                "c9db4ae8"
            ),
        )

    def test_constructor_accepts_locked_interface(self):
        record = load_preflight_correction_authorization()

        self.assertTrue(
            record["correction_authorized"]
        )
        self.assertTrue(
            record["preflight_authorized"]
        )
        self.assertEqual(
            record["databento_api_calls"],
            0,
        )
        self.assertFalse(
            record["construction_run"]
        )

    def test_digest_protocol_is_locked(self):
        record = (
            get_exp020_preflight_correction_authorization()
        )

        self.assertEqual(
            record["archive_digest_protocol"],
            "EXP-019_INSERTION_ORDER_JSON_V1",
        )
        self.assertEqual(
            record["digest_evidence"][
                "frozen_exp019_archive_sha256"
            ],
            (
                "225a64dc06cb6bb303fd83d186f2e7d8"
                "1e2a8a8bec44382380c8ccc1b0b6baa3"
            ),
        )

    def test_authorization_scope_is_exact(self):
        record = (
            get_exp020_preflight_correction_authorization()
        )

        self.assertEqual(
            tuple(
                record["correction_authorization_files"]
            ),
            (
                "exp020_preflight_correction_authorization.py",
                (
                    "tests/"
                    "test_exp020_preflight_correction_"
                    "authorization.py"
                ),
                (
                    "research/"
                    "EXP-020_preflight_correction_"
                    "authorization.md"
                ),
            ),
        )

    def test_source_boundary_remains_read_only(self):
        record = (
            get_exp020_preflight_correction_authorization()
        )

        self.assertTrue(
            record["source_archive_read_only"]
        )
        self.assertFalse(
            record["source_archive_modified"]
        )
        self.assertFalse(
            record["digest_evidence"][
                "source_mutation_detected"
            ]
        )

    def test_original_construction_authorization_is_unchanged(
        self,
    ):
        record = (
            get_exp020_preflight_correction_authorization()
        )

        self.assertTrue(
            record[
                "construction_authorization_unchanged"
            ]
        )
        self.assertTrue(
            record[
                "one_time_construction_limit_unchanged"
            ]
        )
        self.assertFalse(
            record["construction_run"]
        )

    def test_research_and_trading_remain_prohibited(self):
        record = (
            get_exp020_preflight_correction_authorization()
        )

        prohibited = (
            "strategy_run_authorized",
            "optimization_authorized",
            "mcpt_authorized",
            "bootstrap_authorized",
            "walk_forward_authorized",
            "paper_trading_authorized",
            "live_trading_authorized",
        )

        self.assertTrue(
            all(
                record[key] is False
                for key in prohibited
            )
        )

    def test_getter_returns_independent_copy(self):
        first = (
            get_exp020_preflight_correction_authorization()
        )
        second = (
            get_exp020_preflight_correction_authorization()
        )

        first["digest_evidence"][
            "frozen_digest_matched"
        ] = False

        self.assertTrue(
            second["digest_evidence"][
                "frozen_digest_matched"
            ]
        )

    def test_validator_rejects_mutated_boundary(self):
        record = (
            get_exp020_preflight_correction_authorization()
        )
        record["databento_api_calls"] = 1

        with self.assertRaisesRegex(
            ValueError,
            "safety boundary changed",
        ):
            validate_exp020_preflight_correction_authorization(
                record
            )


if __name__ == "__main__":
    unittest.main()
