from __future__ import annotations

import unittest

from exp011_preregistration import (
    SIGNAL_VARIANTS,
    SIZING_METHODS,
    get_exp011_preregistration,
    validate_exp011_preregistration,
)


class Exp011PreregistrationTests(unittest.TestCase):
    def test_preregistration_is_valid(self) -> None:
        validate_exp011_preregistration()

    def test_two_exp010_signal_variants_are_frozen(self) -> None:
        signal = get_exp011_preregistration()["signal_lock"]
        self.assertEqual(signal["variant_count"], 2)
        self.assertEqual(tuple(signal["variants"]), SIGNAL_VARIANTS)
        self.assertEqual(signal["minimum_drive_fraction"], 0.5)
        self.assertTrue(signal["new_signal_parameters_prohibited"])

    def test_three_sizing_methods_are_locked(self) -> None:
        sizing = get_exp011_preregistration()["sizing_lock"]
        self.assertEqual(sizing["method_count"], 3)
        self.assertEqual(tuple(sizing["methods"]), SIZING_METHODS)
        self.assertEqual(sizing["fractional_nq_max_contracts"], 2.0)
        self.assertEqual(sizing["integer_mnq_max_contracts"], 20)
        self.assertFalse(sizing["automatic_sizing_winner"])

    def test_calibration_precedes_evaluation(self) -> None:
        record = get_exp011_preregistration()
        data = record["market_and_data"]
        calibration = record["risk_target_calibration"]
        self.assertEqual(
            data["calibration_period"],
            "2019-05-06 through 2020-12-31",
        )
        self.assertEqual(
            data["evaluation_period"],
            "2021-01-04 through 2025-12-31",
        )
        self.assertTrue(
            data["calibration_sessions_are_not_in_evaluation_metrics"]
        )
        self.assertTrue(calibration["evaluation_data_cannot_set_target"])
        self.assertTrue(
            calibration["target_risk_optimization_prohibited"]
        )

    def test_position_sizing_cannot_claim_signal_edge(self) -> None:
        record = get_exp011_preregistration()
        self.assertTrue(
            record["relationship_to_exp010"][
                "position_sizing_cannot_establish_signal_edge"
            ]
        )
        self.assertFalse(
            record["statistical_scope"]["new_mcpt_enabled"]
        )
        self.assertFalse(
            record["statistical_scope"]["independent_confirmation"]
        )

    def test_all_six_measurements_remain_visible(self) -> None:
        measurement = get_exp011_preregistration()["measurement_plan"]
        self.assertEqual(measurement["total_measurement_rows"], 6)
        self.assertTrue(measurement["all_rows_reported"])
        self.assertTrue(measurement["no_single_composite_score"])
        self.assertTrue(measurement["no_pass_fail_gate"])

    def test_bootstrap_is_paired_and_diagnostic(self) -> None:
        bootstrap = get_exp011_preregistration()[
            "paired_bootstrap_diagnostics"
        ]
        self.assertEqual(bootstrap["resamples"], 10000)
        self.assertEqual(bootstrap["random_seed"], 5111)
        self.assertEqual(bootstrap["sampling_unit"], "evaluation_session")
        self.assertTrue(bootstrap["paired_by_session"])
        self.assertFalse(bootstrap["decision_gate"])

    def test_no_paper_or_live_authorization(self) -> None:
        scope = get_exp011_preregistration()["statistical_scope"]
        self.assertFalse(scope["paper_trading_authorized"])
        self.assertFalse(scope["live_trading_authorized"])

    def test_sizing_mutation_is_rejected(self) -> None:
        changed = get_exp011_preregistration()
        changed["sizing_lock"]["integer_mnq_max_contracts"] = 30
        with self.assertRaisesRegex(ValueError, "sizing lock"):
            validate_exp011_preregistration(changed)

    def test_evaluation_leakage_is_rejected(self) -> None:
        changed = get_exp011_preregistration()
        changed["risk_target_calibration"][
            "evaluation_data_cannot_set_target"
        ] = False
        with self.assertRaisesRegex(ValueError, "calibration"):
            validate_exp011_preregistration(changed)

    def test_reporting_standard_is_preserved(self) -> None:
        reporting = get_exp011_preregistration()[
            "reporting_requirements"
        ]
        self.assertTrue(
            reporting["plain_english_strategy_and_sizing_explanation"]
        )
        self.assertTrue(reporting["positive_numbers_use_neutral_text"])
        self.assertTrue(reporting["adverse_numbers_use_red_text"])
        self.assertTrue(reporting["green_reserved_for_status_words"])


if __name__ == "__main__":
    unittest.main()
