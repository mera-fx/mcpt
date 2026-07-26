from __future__ import annotations

import unittest

from exp022_construction_authorization import (
    get_exp022_construction_authorization,
    validate_exp022_construction_authorization,
)


class Exp022ConstructionAuthorizationTests(
    unittest.TestCase
):
    def test_01_authorization_is_valid(self):
        validate_exp022_construction_authorization()

    def test_02_identity_is_locked(self):
        record = (
            get_exp022_construction_authorization()
        )
        self.assertEqual(
            record["experiment_id"],
            "EXP-022",
        )
        self.assertEqual(
            record["authorization_id"],
            "EXP-022-CONSTRUCTION-AUTH-001",
        )

    def test_03_preregistration_commit_is_locked(self):
        record = (
            get_exp022_construction_authorization()
        )
        self.assertEqual(
            record["locked_preregistration_commit"],
            "73c1255bcb904e71d927ed1097788de9b791bb54",
        )
        self.assertEqual(
            record["locked_preregistration_sha256"],
            "527b7222fb56e8f070e404e0f49977730fd9709b254157cbb73710ccc6cee252",
        )

    def test_04_implementation_commit_is_locked(self):
        record = (
            get_exp022_construction_authorization()
        )
        self.assertEqual(
            record["locked_implementation_commit"],
            "6dd69307c3dcfed876c57d6f62ae6d98bcb6ad93",
        )

    def test_05_selected_method_is_locked(self):
        record = (
            get_exp022_construction_authorization()
        )
        self.assertEqual(
            record["selected_method"],
            "VOL_GT_OUT_2S_E3",
        )
        self.assertEqual(
            record["output_series_count"],
            2,
        )

    def test_06_one_time_construction_is_authorized(self):
        record = (
            get_exp022_construction_authorization()
        )
        self.assertTrue(
            record["construction_authorized"]
        )
        self.assertTrue(
            record["one_time_construction"]
        )
        self.assertEqual(
            record["maximum_construction_runs"],
            1,
        )
        self.assertTrue(
            record["protected_preflight_authorized"]
        )

    def test_07_no_api_or_credentials_are_authorized(self):
        record = (
            get_exp022_construction_authorization()
        )
        self.assertEqual(
            record["databento_api_calls"],
            0,
        )
        self.assertFalse(
            record["credentials_required"]
        )

    def test_08_frozen_inputs_cannot_be_modified(self):
        record = (
            get_exp022_construction_authorization()
        )
        for key in (
            "source_archive_modification_authorized",
            "exp020_output_modification_authorized",
            "exp021_output_modification_authorized",
            "roll_rule_reselection_authorized",
            "roll_date_recalculation_authorized",
        ):
            with self.subTest(key=key):
                self.assertFalse(record[key])

    def test_09_no_strategy_or_trading_permission(self):
        record = (
            get_exp022_construction_authorization()
        )
        for key in (
            "strategy_run_authorized",
            "strategy_optimization_authorized",
            "mcpt_authorized",
            "bootstrap_authorized",
            "walk_forward_authorized",
            "paper_trading_authorized",
            "live_trading_authorized",
        ):
            with self.subTest(key=key):
                self.assertFalse(record[key])

    def test_10_mutation_is_rejected(self):
        record = (
            get_exp022_construction_authorization()
        )
        record["maximum_construction_runs"] = 2

        with self.assertRaisesRegex(
            ValueError,
            "authorization boundary changed",
        ):
            validate_exp022_construction_authorization(
                record
            )


if __name__ == "__main__":
    unittest.main()
