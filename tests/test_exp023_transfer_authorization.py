from __future__ import annotations

import unittest

from exp023_transfer import load_authorization
from exp023_transfer_authorization import (
    get_exp023_transfer_authorization,
    validate_exp023_transfer_authorization,
)


class Exp023TransferAuthorizationTests(unittest.TestCase):
    def test_01_authorization_is_valid(self) -> None:
        validate_exp023_transfer_authorization()

    def test_02_identity_is_locked(self) -> None:
        record = get_exp023_transfer_authorization()
        self.assertEqual(record["experiment_id"], "EXP-023")
        self.assertEqual(
            record["authorization_id"],
            "EXP-023-TRANSFER-AUTH-001",
        )

    def test_03_preregistration_and_implementation_are_locked(
        self,
    ) -> None:
        record = get_exp023_transfer_authorization()
        self.assertEqual(
            record["locked_preregistration_commit"],
            "66ba6a46f31cc8715447179c19caf2f4c1a1e8be",
        )
        self.assertEqual(
            record["locked_preregistration_sha256"],
            (
                "20c7295123adead63b5e9c398419a3129"
                "aa93c4fcd3e597e6e92c295dc2841be"
            ),
        )
        self.assertEqual(
            record["locked_implementation_commit"],
            "c17e9ea567c234e2d941f949168d62721f6d4963",
        )

    def test_04_exactly_three_finalists_are_authorized(self) -> None:
        record = get_exp023_transfer_authorization()
        self.assertEqual(
            tuple(record["candidate_ids"]),
            (
                "gap_fade_0p50_1r",
                "premarket_continuation_0p50_time",
                "premarket_continuation_0p75_time",
            ),
        )

    def test_05_one_time_known_overlap_run_is_authorized(self) -> None:
        record = get_exp023_transfer_authorization()
        self.assertTrue(record["transfer_execution_authorized"])
        self.assertTrue(record["one_time_transfer_run"])
        self.assertEqual(record["maximum_transfer_runs"], 1)
        self.assertTrue(record["protected_preflight_authorized"])
        self.assertEqual(
            record["allowed_session_date_start"],
            "2020-01-03",
        )
        self.assertEqual(
            record["allowed_session_date_end"],
            "2025-12-31",
        )

    def test_06_frozen_inputs_cannot_be_modified(self) -> None:
        record = get_exp023_transfer_authorization()
        for key in (
            "exp022_output_modification_authorized",
            "exp014_output_modification_authorized",
            "session_quality_modification_authorized",
            "out_of_overlap_access_authorized",
            "new_market_data_download_authorized",
        ):
            with self.subTest(key=key):
                self.assertFalse(record[key])

    def test_07_no_network_search_robustness_or_trading(
        self,
    ) -> None:
        record = get_exp023_transfer_authorization()
        self.assertFalse(record["network_access_authorized"])
        self.assertEqual(record["databento_api_calls"], 0)
        self.assertFalse(record["credentials_required"])
        for key in (
            "strategy_search_authorized",
            "strategy_optimization_authorized",
            "mcpt_authorized",
            "bootstrap_authorized",
            "walk_forward_authorized",
            "strategy_ranking_authorized",
            "paper_trading_authorized",
            "live_trading_authorized",
            "protected_history_validation_authorized",
        ):
            with self.subTest(key=key):
                self.assertFalse(record[key])

    def test_08_runner_accepts_the_locked_authorization(self) -> None:
        record = load_authorization()
        self.assertEqual(
            record["locked_implementation_commit"],
            "c17e9ea567c234e2d941f949168d62721f6d4963",
        )

    def test_09_mutation_is_rejected(self) -> None:
        record = get_exp023_transfer_authorization()
        record["maximum_transfer_runs"] = 2
        with self.assertRaisesRegex(
            ValueError,
            "authorization boundary changed",
        ):
            validate_exp023_transfer_authorization(record)


if __name__ == "__main__":
    unittest.main()
