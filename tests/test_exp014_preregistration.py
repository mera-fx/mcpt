from __future__ import annotations

from copy import deepcopy
import unittest

from exp014_preregistration import (
    FINALIST_IDS,
    PAIR_DEFINITIONS,
    get_exp014_preregistration,
    validate_exp014_preregistration,
)


class Exp014PreregistrationTests(unittest.TestCase):
    def test_preregistration_is_valid(self) -> None:
        validate_exp014_preregistration()

    def test_exact_three_finalists_are_unchanged(self) -> None:
        lock = get_exp014_preregistration()["candidate_lock"]
        self.assertEqual(tuple(lock["candidate_ids"]), FINALIST_IDS)
        self.assertEqual(lock["candidate_count"], 3)
        self.assertFalse(lock["strategy_rules_changed"])
        self.assertFalse(lock["parameters_changed"])
        self.assertFalse(lock["position_sizing_changed"])

    def test_trade_reconstruction_must_match_exp013(self) -> None:
        reconstruction = get_exp014_preregistration()[
            "trade_reconstruction"
        ]
        self.assertTrue(reconstruction["same_exp012_engine"])
        self.assertTrue(
            reconstruction[
                "summary_must_match_exp013_candidate_measurements"
            ]
        )
        self.assertEqual(
            reconstruction["mismatch_action"],
            "STOP_WITHOUT_WRITING_FINAL_RESULT",
        )

    def test_2025_failure_analysis_is_locked(self) -> None:
        behaviour = get_exp014_preregistration()[
            "behaviour_measurements"
        ]
        self.assertEqual(behaviour["focus_year"], 2025)
        self.assertEqual(
            behaviour["focus_comparisons"],
            ["2020-2024", "2022-2024"],
        )
        self.assertEqual(
            behaviour["holding_time_bins_minutes"],
            [0, 15, 60, 180, 391],
        )

    def test_regimes_use_only_information_known_before_entry(self) -> None:
        behaviour = get_exp014_preregistration()[
            "behaviour_measurements"
        ]
        self.assertTrue(
            behaviour["entry_known_trend_regime"][
                "current_session_excluded"
            ]
        )
        self.assertTrue(
            behaviour["entry_known_volatility_regime"][
                "current_session_excluded"
            ]
        )
        self.assertEqual(
            behaviour["entry_known_volatility_regime"][
                "calibration_period"
            ],
            "2020-01-03 through 2021-12-31",
        )

    def test_overlap_uses_complete_zero_filled_session_axis(self) -> None:
        overlap = get_exp014_preregistration()[
            "overlap_and_dependence"
        ]
        self.assertIn("1331", overlap["calendar_axis"])
        self.assertTrue(overlap["active_overlap_count"])
        self.assertTrue(overlap["opposite_direction_overlap_count"])
        self.assertTrue(overlap["simultaneous_underwater_share"])

    def test_only_two_fixed_cross_family_pairs_are_allowed(self) -> None:
        pairs = get_exp014_preregistration()[
            "sleeve_pair_comparison"
        ]
        self.assertEqual(tuple(pairs["pairs"]), PAIR_DEFINITIONS)
        self.assertEqual(pairs["pair_count"], 2)
        self.assertTrue(pairs["nested_premarket_candidates_never_combined"])
        self.assertTrue(pairs["all_three_candidates_never_combined"])

    def test_sleeves_are_diagnostic_and_unweighted(self) -> None:
        pairs = get_exp014_preregistration()[
            "sleeve_pair_comparison"
        ]
        self.assertTrue(pairs["one_contract_per_active_sleeve"])
        self.assertEqual(pairs["maximum_gross_contracts"], 2)
        self.assertTrue(pairs["no_weights"])
        self.assertTrue(pairs["no_weight_optimization"])
        self.assertTrue(pairs["diagnostic_not_executable_portfolio"])

    def test_existing_exp013_validation_is_not_rerun(self) -> None:
        relationship = get_exp014_preregistration()[
            "relationship_to_exp013"
        ]
        self.assertTrue(
            relationship["existing_exp013_mcpt_reused_not_rerun"]
        )
        self.assertTrue(
            relationship["existing_exp013_bootstrap_reused_not_rerun"]
        )
        self.assertTrue(
            relationship[
                "existing_exp013_walk_forward_reused_not_rerun"
            ]
        )

    def test_no_winner_filter_or_trading_authorization(self) -> None:
        interpretation = get_exp014_preregistration()[
            "result_interpretation"
        ]
        self.assertTrue(interpretation["no_pass_fail_gates"])
        self.assertTrue(interpretation["no_automatic_winner"])
        self.assertTrue(interpretation["no_regime_filter_selection"])
        self.assertFalse(interpretation["paper_trading_authorized"])
        self.assertFalse(interpretation["live_trading_authorized"])

    def test_candidate_mutation_is_rejected(self) -> None:
        changed = get_exp014_preregistration()
        changed["candidate_lock"]["candidate_ids"] = FINALIST_IDS[:-1]
        with self.assertRaisesRegex(ValueError, "candidate lock"):
            validate_exp014_preregistration(changed)

    def test_pair_weight_optimization_is_rejected(self) -> None:
        changed = get_exp014_preregistration()
        changed["sleeve_pair_comparison"]["no_weight_optimization"] = False
        with self.assertRaisesRegex(ValueError, "sleeve-pair lock"):
            validate_exp014_preregistration(changed)

    def test_reporting_standard_is_preserved(self) -> None:
        reporting = get_exp014_preregistration()[
            "reporting_requirements"
        ]
        self.assertTrue(
            reporting["plain_english_strategy_rules_and_fraction_examples"]
        )
        self.assertTrue(reporting["2025_failure_decomposition"])
        self.assertTrue(reporting["overlap_matrix"])
        self.assertTrue(reporting["positive_numbers_use_neutral_text"])
        self.assertTrue(reporting["adverse_numbers_use_red_text"])
        self.assertTrue(reporting["green_reserved_for_status_words"])
        self.assertTrue(
            reporting["charts_use_solid_opaque_white_canvas"]
        )


if __name__ == "__main__":
    unittest.main()
