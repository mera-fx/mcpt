from __future__ import annotations

import unittest

from exp024_attribution import load_authorization
from exp024_attribution_authorization import (
    EXPECTED_EXP024_ATTRIBUTION_AUTHORIZATION_SHA256,
    canonical_record_hash,
    get_exp024_attribution_authorization,
    validate_exp024_attribution_authorization,
)


class Exp024AttributionAuthorizationTests(unittest.TestCase):
    def test_01_authorization_is_valid(self) -> None:
        validate_exp024_attribution_authorization()

    def test_02_identity_and_commits_are_locked(self) -> None:
        record = get_exp024_attribution_authorization()
        self.assertEqual(record["experiment_id"], "EXP-024")
        self.assertEqual(
            record["authorization_id"],
            "EXP-024-ATTRIBUTION-AUTH-001",
        )
        self.assertEqual(
            record["locked_preregistration_commit"],
            "37a6d007b103bb5baddfdbbe471a8b6626b8a35c",
        )
        self.assertEqual(
            record["locked_preregistration_sha256"],
            (
                "6bc6b7b493aa5eb4a58699fd8cd2c0af"
                "15d6c8cfe5323edf9cb3bba1193e3871"
            ),
        )
        self.assertEqual(
            record["locked_implementation_commit"],
            "34f7d4c83dee025108229d5247e9cb4f87398a59",
        )

    def test_03_exact_population_is_authorized(self) -> None:
        record = get_exp024_attribution_authorization()
        self.assertEqual(
            tuple(record["candidate_ids"]),
            (
                "gap_fade_0p50_1r",
                "premarket_continuation_0p50_time",
                "premarket_continuation_0p75_time",
            ),
        )
        self.assertEqual(record["candidate_session_row_count"], 51)
        self.assertEqual(record["unique_session_count"], 51)

    def test_04_exactly_one_attribution_run_is_authorized(self) -> None:
        record = get_exp024_attribution_authorization()
        self.assertTrue(record["attribution_execution_authorized"])
        self.assertTrue(record["one_time_attribution_run"])
        self.assertEqual(record["maximum_attribution_runs"], 1)
        self.assertTrue(record["protected_preflight_authorized"])
        self.assertTrue(record["independent_rebuild_required"])

    def test_05_value_windows_are_locked(self) -> None:
        record = get_exp024_attribution_authorization()
        self.assertEqual(
            record["allowed_session_date_start"],
            "2020-01-03",
        )
        self.assertEqual(
            record["allowed_session_date_end"],
            "2025-12-31",
        )
        self.assertEqual(
            record["allowed_current_entry_field"],
            "09:35:00 open only",
        )
        for key in (
            "out_of_overlap_access_authorized",
            "non_mismatch_session_access_authorized",
            "current_post_entry_access_authorized",
            "volume_access_authorized",
        ):
            with self.subTest(key=key):
                self.assertFalse(record[key])

    def test_06_frozen_inputs_cannot_be_modified(self) -> None:
        record = get_exp024_attribution_authorization()
        for key in (
            "exp023_output_modification_authorized",
            "exp022_output_modification_authorized",
            "quantower_output_modification_authorized",
            "session_quality_modification_authorized",
            "new_market_data_download_authorized",
        ):
            with self.subTest(key=key):
                self.assertFalse(record[key])

    def test_07_no_replay_performance_search_or_trading(self) -> None:
        record = get_exp024_attribution_authorization()
        self.assertFalse(record["network_access_authorized"])
        self.assertEqual(record["databento_api_calls"], 0)
        self.assertFalse(record["credentials_required"])
        for key in (
            "strategy_replay_authorized",
            "exit_evaluation_authorized",
            "pnl_return_equity_evaluation_authorized",
            "strategy_search_authorized",
            "optimization_authorized",
            "mcpt_authorized",
            "bootstrap_authorized",
            "walk_forward_authorized",
            "candidate_ranking_authorized",
            "source_winner_selection_authorized",
            "protected_history_validation_authorized",
            "paper_trading_authorized",
            "live_trading_authorized",
        ):
            with self.subTest(key=key):
                self.assertFalse(record[key])

    def test_08_runner_accepts_the_locked_authorization(self) -> None:
        record = load_authorization()
        self.assertEqual(
            record["locked_implementation_commit"],
            "34f7d4c83dee025108229d5247e9cb4f87398a59",
        )

    def test_09_authorization_hash_is_locked(self) -> None:
        record = get_exp024_attribution_authorization()
        self.assertEqual(
            canonical_record_hash(record),
            EXPECTED_EXP024_ATTRIBUTION_AUTHORIZATION_SHA256,
        )

    def test_10_mutation_is_rejected(self) -> None:
        record = get_exp024_attribution_authorization()
        record["maximum_attribution_runs"] = 2
        with self.assertRaisesRegex(
            ValueError,
            "authorization boundary changed",
        ):
            validate_exp024_attribution_authorization(record)


if __name__ == "__main__":
    unittest.main()
