from __future__ import annotations

import unittest

from exp024_attribution import load_replacement_authorization
from exp024_replacement_authorization import (
    EXPECTED_EXP024_REPLACEMENT_AUTHORIZATION_SHA256,
    canonical_record_hash,
    get_exp024_replacement_authorization,
    validate_exp024_replacement_authorization,
)


class Exp024ReplacementAuthorizationTests(unittest.TestCase):
    def test_01_replacement_authorization_is_valid(self) -> None:
        validate_exp024_replacement_authorization()

    def test_02_identity_and_lineage_are_locked(self) -> None:
        record = get_exp024_replacement_authorization()
        self.assertEqual(record["experiment_id"], "EXP-024")
        self.assertEqual(
            record["authorization_id"],
            "EXP-024-ATTRIBUTION-AUTH-002",
        )
        self.assertEqual(
            record["original_authorization_commit"],
            "55ae174f5517bdb5afc48f5a36f5268fbc1eb42a",
        )
        self.assertEqual(
            record["failed_attempt_id"],
            "EXP-024-ATTEMPT-001",
        )
        self.assertEqual(
            record["locked_replacement_implementation_commit"],
            "fb5b8f02ac54cccf29c5d23452db6d8e9ac4589e",
        )

    def test_03_original_authorization_is_consumed(self) -> None:
        record = get_exp024_replacement_authorization()
        self.assertTrue(record["original_authorization_consumed"])
        self.assertFalse(record["failed_attempt_attribution_calculated"])
        self.assertEqual(
            record["failed_attempt_record_sha256"],
            (
                "556854e35ac217f62677cf15d3e6c03ab"
                "f38414bd65585d9decd441154f7be17"
            ),
        )

    def test_04_exactly_one_replacement_run_is_authorized(self) -> None:
        record = get_exp024_replacement_authorization()
        self.assertTrue(record["replacement_execution_authorized"])
        self.assertTrue(record["one_time_replacement_run"])
        self.assertEqual(record["maximum_replacement_runs"], 1)
        self.assertTrue(record["protected_preflight_authorized"])
        self.assertTrue(record["independent_rebuild_required"])

    def test_05_population_and_windows_are_unchanged(self) -> None:
        record = get_exp024_replacement_authorization()
        self.assertEqual(record["candidate_session_row_count"], 51)
        self.assertEqual(record["unique_session_count"], 51)
        self.assertEqual(
            tuple(record["candidate_ids"]),
            (
                "gap_fade_0p50_1r",
                "premarket_continuation_0p50_time",
                "premarket_continuation_0p75_time",
            ),
        )
        self.assertEqual(
            record["allowed_current_entry_field"],
            "09:35:00 open only",
        )

    def test_06_no_boundary_expansion_is_authorized(self) -> None:
        record = get_exp024_replacement_authorization()
        for key in (
            "exp023_output_modification_authorized",
            "exp022_output_modification_authorized",
            "quantower_output_modification_authorized",
            "session_quality_modification_authorized",
            "failed_attempt_record_modification_authorized",
            "out_of_overlap_access_authorized",
            "non_mismatch_session_access_authorized",
            "current_post_entry_access_authorized",
            "volume_access_authorized",
            "new_market_data_download_authorized",
            "network_access_authorized",
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
        self.assertEqual(record["databento_api_calls"], 0)
        self.assertFalse(record["credentials_required"])

    def test_07_runner_accepts_replacement_authorization(self) -> None:
        record = load_replacement_authorization()
        self.assertEqual(
            record["locked_replacement_implementation_commit"],
            "fb5b8f02ac54cccf29c5d23452db6d8e9ac4589e",
        )

    def test_08_hash_is_locked(self) -> None:
        record = get_exp024_replacement_authorization()
        self.assertEqual(
            canonical_record_hash(record),
            EXPECTED_EXP024_REPLACEMENT_AUTHORIZATION_SHA256,
        )

    def test_09_mutation_is_rejected(self) -> None:
        record = get_exp024_replacement_authorization()
        record["maximum_replacement_runs"] = 2
        with self.assertRaisesRegex(
            ValueError,
            "replacement authorization boundary changed",
        ):
            validate_exp024_replacement_authorization(record)


if __name__ == "__main__":
    unittest.main()
