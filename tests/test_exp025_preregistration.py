from __future__ import annotations

from copy import deepcopy
import unittest

from exp025_preregistration import (
    EXPECTED_EXP019_EXACT_CONTRACT_ARCHIVE_SHA256,
    EXPECTED_EXP024_CLOSURE_SHA256,
    EXPECTED_EXP025_PREREGISTRATION_SHA256,
    canonical_record_hash,
    get_exp025_preregistration,
    validate_exp025_preregistration,
)


class Exp025PreregistrationTests(unittest.TestCase):
    def test_01_preregistration_is_valid(self) -> None:
        validate_exp025_preregistration()

    def test_02_identity_is_locked(self) -> None:
        record = get_exp025_preregistration()
        self.assertEqual(record["experiment_id"], "EXP-025")
        self.assertEqual(record["research_status"], "PRE_REGISTERED")
        self.assertEqual(record["implementation_status"], "NOT_IMPLEMENTED")
        self.assertEqual(record["execution_status"], "NOT_RUN")

    def test_03_exp024_closure_is_locked(self) -> None:
        frozen = get_exp025_preregistration()["frozen_inputs"]
        self.assertEqual(
            frozen["exp024_closure_record_sha256"],
            EXPECTED_EXP024_CLOSURE_SHA256,
        )
        self.assertEqual(
            frozen["exp024_classification"],
            "ATTRIBUTION_DIAGNOSTIC_NOT_QUALIFIED",
        )

    def test_04_exact_contract_archive_is_locked(self) -> None:
        archive = get_exp025_preregistration()["frozen_inputs"][
            "exp019_exact_contract_archive"
        ]
        self.assertEqual(
            archive["archive_sha256"],
            EXPECTED_EXP019_EXACT_CONTRACT_ARCHIVE_SHA256,
        )
        self.assertEqual(archive["contract_count"], 66)
        self.assertFalse(archive["new_databento_download_authorized"])
        self.assertEqual(archive["databento_api_calls"], 0)

    def test_05_all_43_unresolved_rows_are_required(self) -> None:
        population = get_exp025_preregistration()["population"]
        self.assertEqual(population["candidate_id"], "gap_fade_0p50_1r")
        self.assertEqual(population["candidate_session_row_count"], 43)
        self.assertEqual(population["unique_session_count"], 43)
        self.assertTrue(population["all_43_rows_must_be_retained"])
        self.assertTrue(population["sampling_prohibited"])

    def test_06_exact_contract_identity_is_mandatory(self) -> None:
        identity = get_exp025_preregistration()["contract_identity_rule"]
        self.assertTrue(identity["same_contract_required_across_sources"])
        self.assertTrue(identity["explicit_contract_symbol_required"])
        self.assertTrue(
            identity["continuous_symbols_prohibited_as_exact_contract_evidence"]
        )
        self.assertTrue(identity["ambiguous_or_missing_identity_is_hard_failure"])

    def test_07_quantower_export_is_not_yet_authorized(self) -> None:
        boundary = get_exp025_preregistration()["quantower_export_boundary"]
        self.assertFalse(boundary["exports_present_at_preregistration"])
        self.assertFalse(boundary["manual_export_authorized_by_preregistration"])
        self.assertTrue(boundary["separate_result_free_implementation_required"])
        self.assertTrue(boundary["separate_execution_authorization_required"])
        self.assertTrue(boundary["order_api_connection_prohibited"])

    def test_08_access_window_is_strict(self) -> None:
        boundary = get_exp025_preregistration()["data_access_boundary"]
        self.assertIn("09:35:00", boundary["allowed_current_window_new_york"])
        self.assertTrue(boundary["current_post_0935_ohlcv_access_prohibited"])
        self.assertTrue(boundary["out_of_population_session_access_prohibited"])
        self.assertFalse(boundary["missing_minutes_filled"])
        self.assertFalse(boundary["synthetic_bars_created"])
        self.assertFalse(boundary["network_access"])

    def test_09_two_engines_are_required(self) -> None:
        comparison = get_exp025_preregistration()[
            "decision_engine_comparison"
        ]
        self.assertTrue(
            comparison["both_engines_run_on_quantower_exact_contract_bars"]
        )
        self.assertTrue(
            comparison["both_engines_run_on_databento_exact_contract_bars"]
        )
        self.assertTrue(
            comparison["same_input_bar_hash_required_for_engine_pair"]
        )
        self.assertTrue(comparison["candidate_rule_change_prohibited"])

    def test_10_no_performance_or_trading_is_authorized(self) -> None:
        objective = get_exp025_preregistration()["objective"]
        prohibited = get_exp025_preregistration()["prohibited_actions"]
        self.assertFalse(objective["strategy_replay"])
        self.assertFalse(objective["profitability_measurement"])
        self.assertTrue(prohibited["calculate_profit_or_loss"])
        self.assertTrue(prohibited["calculate_return_equity_or_drawdown"])
        self.assertTrue(prohibited["paper_trading"])
        self.assertTrue(prohibited["live_trading"])

    def test_11_checks_outputs_and_sequence_are_locked(self) -> None:
        record = get_exp025_preregistration()
        self.assertEqual(len(record["hard_checks"]), 25)
        self.assertEqual(record["hard_check_count"], 25)
        self.assertEqual(len(record["required_outputs"]), 14)
        execution = record["execution_boundary"]
        self.assertTrue(
            execution["separate_result_free_implementation_commit_required"]
        )
        self.assertTrue(
            execution["separate_execution_authorization_commit_required"]
        )
        self.assertTrue(execution["one_authorized_diagnostic_run"])
        self.assertFalse(execution["rerun_after_completion"])

    def test_12_canonical_hash_detects_change(self) -> None:
        record = get_exp025_preregistration()
        self.assertEqual(
            canonical_record_hash(record),
            EXPECTED_EXP025_PREREGISTRATION_SHA256,
        )
        changed = deepcopy(record)
        changed["population"]["candidate_session_row_count"] = 42
        with self.assertRaisesRegex(
            ValueError,
            "population boundary changed",
        ):
            validate_exp025_preregistration(changed)


if __name__ == "__main__":
    unittest.main()
