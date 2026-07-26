from __future__ import annotations

import unittest

from exp021_diagnostic_authorization import (
    get_exp021_diagnostic_authorization,
    validate_exp021_diagnostic_authorization,
)


class Exp021DiagnosticAuthorizationTests(
    unittest.TestCase
):
    def test_01_authorization_is_valid(self):
        validate_exp021_diagnostic_authorization()

    def test_02_identity_and_commits_are_locked(self):
        record = (
            get_exp021_diagnostic_authorization()
        )

        self.assertEqual(
            record["experiment_id"],
            "EXP-021",
        )
        self.assertEqual(
            record["authorization_status"],
            "AUTHORIZED_FOR_ONE_TIME_DIAGNOSTIC",
        )
        self.assertEqual(
            record["locked_preregistration_commit"],
            "27a960ad68f2059e5ac9d60e42e41a9171fbda41",
        )
        self.assertEqual(
            record["locked_implementation_commit"],
            "9d365613619e21b9fe4eb9625bba907efd60ecfa",
        )

    def test_03_authorization_is_one_time(self):
        record = (
            get_exp021_diagnostic_authorization()
        )

        self.assertTrue(
            record["diagnostic_authorized"]
        )
        self.assertTrue(
            record["one_time_diagnostic"]
        )
        self.assertEqual(
            record["maximum_diagnostic_runs"],
            1,
        )
        self.assertFalse(
            record[
                "diagnostic_rerun_after_completion"
            ]
        )

    def test_04_preflight_and_confirmation_are_required(
        self,
    ):
        record = (
            get_exp021_diagnostic_authorization()
        )

        self.assertTrue(
            record["protected_preflight_required"]
        )
        self.assertTrue(
            record[
                "diagnostic_confirmation_flag_required"
            ]
        )

    def test_05_api_and_credentials_are_prohibited(self):
        record = (
            get_exp021_diagnostic_authorization()
        )

        self.assertEqual(
            record["databento_api_calls"],
            0,
        )
        self.assertFalse(
            record["credentials_required"]
        )
        self.assertTrue(
            record["prohibited_actions"][
                "databento_api_request"
            ]
        )

    def test_06_frozen_sources_are_read_only(self):
        source = (
            get_exp021_diagnostic_authorization()[
                "source_boundary"
            ]
        )

        self.assertTrue(
            source["exp019_archive_read_only"]
        )
        self.assertTrue(
            source["exp020_outputs_read_only"]
        )
        self.assertEqual(
            source["contract_count"],
            66,
        )
        self.assertEqual(
            source["record_count"],
            6_276_486,
        )

    def test_07_scope_is_diagnostic_only(self):
        record = (
            get_exp021_diagnostic_authorization()
        )
        scope = record["diagnostic_scope"]

        self.assertEqual(
            scope["candidate_method_count"],
            8,
        )
        self.assertEqual(
            scope["transition_count_per_candidate"],
            65,
        )
        self.assertEqual(
            scope["hard_check_count"],
            16,
        )
        self.assertTrue(
            scope["independent_rebuild_required"]
        )
        self.assertFalse(
            scope["continuous_series_construction"]
        )

    def test_08_no_continuous_construction_permission(self):
        record = (
            get_exp021_diagnostic_authorization()
        )

        self.assertFalse(
            record[
                "continuous_construction_authorized"
            ]
        )
        self.assertTrue(
            record["prohibited_actions"][
                "continuous_series_construction"
            ]
        )

    def test_09_no_strategy_or_trading_permission(self):
        record = (
            get_exp021_diagnostic_authorization()
        )

        for key in (
            "strategy_run_authorized",
            "strategy_use_authorized",
            "paper_trading_authorized",
            "live_trading_authorized",
        ):
            with self.subTest(key=key):
                self.assertFalse(record[key])

        for key in (
            "strategy_replay",
            "strategy_optimization",
            "mcpt",
            "bootstrap",
            "walk_forward",
            "paper_trading",
            "live_trading",
        ):
            with self.subTest(key=key):
                self.assertTrue(
                    record["prohibited_actions"][key]
                )

    def test_10_mutation_is_rejected(self):
        record = (
            get_exp021_diagnostic_authorization()
        )
        record["maximum_diagnostic_runs"] = 2

        with self.assertRaisesRegex(
            ValueError,
            "authorization record changed",
        ):
            validate_exp021_diagnostic_authorization(
                record
            )


if __name__ == "__main__":
    unittest.main()
