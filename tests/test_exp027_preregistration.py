from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import hashlib
import unittest

from exp027_preregistration import (
    EXPECTED_EXP027_PREREGISTRATION_SHA256,
    canonical_record_hash,
    get_exp027_preregistration,
    validate_exp027_preregistration,
)
from experiment_lifecycle import (
    get_experiment_lifecycle,
)


POLICY_PATH = Path(
    "research/HISTORICAL_DATA_POLICY.md"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(block)
    return digest.hexdigest()


class Exp027PreregistrationTests(unittest.TestCase):
    def test_01_preregistration_is_valid(self) -> None:
        validate_exp027_preregistration()

    def test_02_identity_is_locked(self) -> None:
        record = get_exp027_preregistration()
        self.assertEqual(record["experiment_id"], "EXP-027")
        self.assertEqual(record["research_status"], "PRE_REGISTERED")
        self.assertEqual(record["implementation_status"], "NOT_IMPLEMENTED")
        self.assertEqual(record["execution_status"], "NOT_RUN")

    def test_03_exp026_closure_is_locked(self) -> None:
        frozen = get_exp027_preregistration()["frozen_inputs"]
        self.assertEqual(
            frozen["exp026_closure_commit"],
            "7fc1994e396bfb237fd5f05f5a4298e6c5b5e307",
        )
        self.assertEqual(
            frozen["exp026_closure_record_sha256"],
            "8ec79810a26b58f2d445d47d3f496539f121d6f3e139eae4a9fd38ef029a386f",
        )
        self.assertEqual(
            frozen["exp026_classification"],
            "COMPLETED_MEASUREMENT_REVIEW",
        )

    def test_04_exp022_series_and_policy_are_locked(self) -> None:
        frozen = get_exp027_preregistration()["frozen_inputs"]
        self.assertEqual(frozen["selected_roll_method"], "VOL_GT_OUT_2S_E3")
        self.assertEqual(frozen["series_row_count"], 5_457_606)
        self.assertEqual(len(frozen["series"]), 2)
        self.assertEqual(
            frozen["historical_data_policy_sha256"],
            sha256_file(POLICY_PATH),
        )

    def test_05_protected_period_is_locked(self) -> None:
        record = get_exp027_preregistration()
        period = record["research_period"]
        boundary = record["data_access_boundary"]
        self.assertEqual(period["session_start"], "2026-01-01")
        self.assertEqual(period["session_end"], "2026-07-23")
        self.assertFalse(period["results_viewed_before_lock"])
        self.assertTrue(
            boundary[
                "historical_2010_2025_market_row_deserialization_prohibited"
            ]
        )

    def test_06_all_24_rows_are_locked(self) -> None:
        population = get_exp027_preregistration()["candidate_population"]
        self.assertEqual(population["strategy_candidate_count"], 22)
        self.assertEqual(population["control_candidate_count"], 2)
        self.assertEqual(population["total_reported_count"], 24)
        self.assertEqual(len(population["all_reported_ids"]), 24)
        self.assertEqual(len(set(population["all_reported_ids"])), 24)

    def test_07_primary_cohort_is_exact(self) -> None:
        primary = get_exp027_preregistration()[
            "candidate_population"
        ]["primary_confirmation_cohort"]
        self.assertEqual(
            primary,
            (
                "gap_fade_0p75_1r",
                "opening_drive_0p75_time",
                "premarket_continuation_0p875_1p5r",
            ),
        )

    def test_08_secondary_candidates_cannot_replace_primary(self) -> None:
        population = get_exp027_preregistration()["candidate_population"]
        primary = set(population["primary_confirmation_cohort"])
        secondary = set(population["secondary_candidate_ids"])
        candidates = set(population["all_candidate_ids"])
        self.assertFalse(primary & secondary)
        self.assertEqual(primary | secondary, candidates)
        self.assertTrue(
            population["secondary_promotion_to_primary_prohibited"]
        )

    def test_09_no_selection_or_optimization(self) -> None:
        objective = get_exp027_preregistration()["objective"]
        self.assertFalse(objective["candidate_selection"])
        self.assertFalse(objective["parameter_optimization"])
        self.assertFalse(objective["single_winner_selection"])
        self.assertFalse(objective["formal_accept_reject_gates"])

    def test_10_rules_and_costs_are_unchanged(self) -> None:
        record = get_exp027_preregistration()
        rules = record["strategy_and_execution_rules"]
        costs = record["position_and_cost_model"]
        self.assertTrue(rules["all_rules_unchanged_from_exp026"])
        self.assertEqual(
            rules["same_minute_stop_target_rule"],
            "STOP_FIRST_CONSERVATIVE",
        )
        self.assertEqual(costs["base_round_trip_cost_usd"], 15.0)
        self.assertEqual(
            costs["cost_sensitivity_ticks_per_side"],
            (0, 1, 2, 3),
        )

    def test_11_only_2026_market_rows_may_be_read(self) -> None:
        boundary = get_exp027_preregistration()["data_access_boundary"]
        self.assertEqual(
            boundary["allowed_strategy_session_start"],
            "2026-01-01",
        )
        self.assertEqual(
            boundary["allowed_strategy_session_end"],
            "2026-07-23",
        )
        self.assertTrue(
            boundary["session_date_filter_before_materialization_required"]
        )
        self.assertTrue(
            boundary[
                "historical_2010_2025_market_row_deserialization_prohibited"
            ]
        )

    def test_12_reporting_is_measurement_first(self) -> None:
        record = get_exp027_preregistration()
        reporting = record["reporting_requirements"]
        measurement = record["measurement_plan"]
        self.assertTrue(reporting["all_24_rows_visible"])
        self.assertEqual(
            measurement["metric_columns"],
            ("ALL_TRADES", "LONG_TRADES", "SHORT_TRADES"),
        )
        self.assertTrue(measurement["no_composite_score"])
        self.assertTrue(measurement["sample_bands_are_not_decision_gates"])

    def test_13_canonical_evidence_is_required(self) -> None:
        record = get_exp027_preregistration()
        required = record["required_outputs"]
        reporting = record["reporting_requirements"]
        self.assertEqual(required["per_series_count"], 24)
        self.assertIn(
            "series/<candidate_id>/trades.csv",
            required["per_series_pattern"],
        )
        self.assertIn(
            "series/<candidate_id>/equity.csv",
            required["per_series_pattern"],
        )
        self.assertTrue(reporting["canonical_trade_ledgers"])
        self.assertTrue(reporting["canonical_equity_series"])

    def test_14_no_download_or_trading_is_authorized(self) -> None:
        record = get_exp027_preregistration()
        execution = record["execution_boundary"]
        prohibited = record["prohibited_actions"]
        self.assertEqual(execution["databento_api_calls"], 0)
        self.assertFalse(execution["new_databento_download"])
        self.assertTrue(prohibited["download_market_data"])
        self.assertTrue(prohibited["paper_trading"])
        self.assertTrue(prohibited["live_trading"])

    def test_15_lifecycle_matches_preregistration(self) -> None:
        lifecycle = get_experiment_lifecycle("EXP-027")
        self.assertEqual(lifecycle.stage, "PRE_REGISTERED")
        self.assertIn("Protected 2026", lifecycle.experiment_name)
        self.assertIn("22", lifecycle.stage_reason)
        self.assertIn(
            "separate one-time execution authorisation",
            lifecycle.next_action,
        )

    def test_16_hash_rejects_mutation(self) -> None:
        record = get_exp027_preregistration()
        self.assertEqual(
            canonical_record_hash(record),
            EXPECTED_EXP027_PREREGISTRATION_SHA256,
        )
        changed = deepcopy(record)
        changed["candidate_population"]["selection_in_exp027"] = True
        with self.assertRaisesRegex(
            ValueError,
            "measurement-only|candidate population|record changed",
        ):
            validate_exp027_preregistration(changed)


if __name__ == "__main__":
    unittest.main()
