from __future__ import annotations

import unittest

from exp020_construction_authorization import (
    LOCKED_IMPLEMENTATION_COMMIT,
    LOCKED_PREREGISTRATION_COMMIT,
    get_exp020_construction_authorization,
    validate_exp020_construction_authorization,
)
from exp020_constructor import load_authorization


class Exp020ConstructionAuthorizationTests(
    unittest.TestCase
):
    def test_authorization_is_valid(self):
        validate_exp020_construction_authorization()

    def test_one_time_construction_is_authorized(self):
        record = (
            get_exp020_construction_authorization()
        )

        self.assertTrue(
            record["construction_authorized"]
        )
        self.assertEqual(
            record["databento_api_calls"],
            0,
        )
        self.assertTrue(
            record["one_time_construction"]
        )
        self.assertEqual(
            record["maximum_construction_runs"],
            1,
        )

    def test_exact_commits_are_locked(self):
        record = (
            get_exp020_construction_authorization()
        )

        self.assertEqual(
            record[
                "locked_preregistration_commit"
            ],
            LOCKED_PREREGISTRATION_COMMIT,
        )
        self.assertEqual(
            record[
                "locked_implementation_commit"
            ],
            LOCKED_IMPLEMENTATION_COMMIT,
        )
        self.assertEqual(
            LOCKED_IMPLEMENTATION_COMMIT,
            (
                "36473b354c0b1a200c01494d4b64a78c"
                "ee1e3430"
            ),
        )

    def test_core_module_is_inside_locked_scope(self):
        record = (
            get_exp020_construction_authorization()
        )

        self.assertIn(
            "exp020_constructor_core.py",
            record["implementation_files"],
        )
        self.assertEqual(
            len(
                record[
                    "implementation_files"
                ]
            ),
            4,
        )

    def test_source_boundary_is_read_only(self):
        source = (
            get_exp020_construction_authorization()[
                "source_boundary"
            ]
        )

        self.assertEqual(
            source["source_contract_count"],
            66,
        )
        self.assertEqual(
            source["source_record_count"],
            6_276_486,
        )
        self.assertTrue(
            source[
                "source_archive_read_only"
            ]
        )

    def test_zero_api_and_no_credentials(self):
        execution = (
            get_exp020_construction_authorization()[
                "execution_boundary"
            ]
        )

        self.assertEqual(
            execution["databento_api_calls"],
            0,
        )
        self.assertFalse(
            execution["credentials_required"]
        )
        self.assertFalse(
            execution[
                "source_archive_modifications"
            ]
        )

    def test_twenty_checks_and_eleven_outputs(self):
        record = (
            get_exp020_construction_authorization()
        )

        self.assertEqual(
            record[
                "expected_hard_check_count"
            ],
            20,
        )
        self.assertEqual(
            len(
                record["required_outputs"]
            ),
            11,
        )

    def test_strategy_and_trading_remain_blocked(self):
        record = (
            get_exp020_construction_authorization()
        )

        for key in (
            "strategy_run_authorized",
            "optimization_authorized",
            "mcpt_authorized",
            "bootstrap_authorized",
            "walk_forward_authorized",
            "paper_trading_authorized",
            "live_trading_authorized",
        ):
            with self.subTest(key=key):
                self.assertFalse(
                    record[key]
                )

    def test_constructor_accepts_locked_interface(self):
        record = load_authorization()

        self.assertEqual(
            record[
                "locked_implementation_commit"
            ],
            LOCKED_IMPLEMENTATION_COMMIT,
        )
        self.assertTrue(
            record["construction_authorized"]
        )

    def test_mutated_run_limit_is_rejected(self):
        record = (
            get_exp020_construction_authorization()
        )
        record["maximum_construction_runs"] = 2

        with self.assertRaisesRegex(
            ValueError,
            "identity",
        ):
            validate_exp020_construction_authorization(
                record
            )


if __name__ == "__main__":
    unittest.main()
