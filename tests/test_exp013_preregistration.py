from __future__ import annotations

from copy import deepcopy
import unittest

from exp013_preregistration import (
    FINALIST_CANDIDATES,
    get_exp013_preregistration,
    validate_exp013_preregistration,
)


class Exp013PreregistrationTests(unittest.TestCase):
    def test_preregistration_is_valid(self) -> None:
        validate_exp013_preregistration()

    def test_three_review_candidates_are_locked(self) -> None:
        lock = get_exp013_preregistration()["candidate_lock"]
        self.assertEqual(lock["candidate_count"], 3)
        self.assertEqual(tuple(lock["candidates"]), FINALIST_CANDIDATES)
        self.assertEqual(
            {item["candidate_id"] for item in lock["candidates"]},
            {
                "gap_fade_0p50_1r",
                "premarket_continuation_0p50_time",
                "premarket_continuation_0p75_time",
            },
        )

    def test_selection_is_explicitly_post_result(self) -> None:
        relationship = get_exp013_preregistration()[
            "relationship_to_exp012"
        ]
        self.assertTrue(
            relationship["review_candidates_selected_after_results"]
        )
        self.assertTrue(
            relationship["selection_reasons_are_post_result_judgments"]
        )
        self.assertTrue(
            relationship["preference_is_not_independent_preselection"]
        )
        self.assertTrue(
            relationship["mcpt_cannot_erase_post_result_rule_design"]
        )

    def test_low_sample_warning_is_frozen(self) -> None:
        record = get_exp013_preregistration()
        self.assertTrue(
            record["candidate_lock"][
                "low_sample_warning_must_remain_visible"
            ]
        )
        strict = next(
            item
            for item in record["candidate_lock"]["candidates"]
            if item["candidate_id"]
            == "premarket_continuation_0p75_time"
        )
        self.assertIn("88", strict["known_limitation"])

    def test_walk_forward_has_four_anchored_folds(self) -> None:
        walk_forward = get_exp013_preregistration()[
            "anchored_walk_forward"
        ]
        self.assertEqual(walk_forward["fold_count"], 4)
        self.assertEqual(
            [fold["test_year"] for fold in walk_forward["folds"]],
            [2022, 2023, 2024, 2025],
        )
        self.assertTrue(
            walk_forward[
                "selection_repeated_among_three_in_each_training_window"
            ]
        )

    def test_primary_mcpt_reruns_all_24_candidates(self) -> None:
        mcpt = get_exp013_preregistration()[
            "discovery_wide_selection_aware_mcpt"
        ]
        self.assertEqual(mcpt["permutations"], 1000)
        self.assertEqual(mcpt["random_seed"], 53)
        self.assertTrue(
            mcpt["all_24_exp012_candidates_run_inside_each_permutation"]
        )
        self.assertEqual(
            mcpt["primary_test_statistic"],
            "maximum_trade_profit_factor_across_all_24_candidates",
        )
        self.assertTrue(
            mcpt["does_not_make_post_result_selection_independent"]
        )
        engine = mcpt["permutation_engine"]
        self.assertIn("1,320 active minutes", engine["source_session_shape"])
        self.assertIn("within each exact", engine["shuffle_axis"])
        self.assertTrue(
            engine["preserves_time_of_day_component_distributions"]
        )
        self.assertTrue(
            engine[
                "destroys_cross_slot_and_cross_session_predictive_alignment"
            ]
        )

    def test_bootstrap_is_report_only(self) -> None:
        bootstrap = get_exp013_preregistration()[
            "bootstrap_diagnostics"
        ]
        self.assertEqual(bootstrap["resamples"], 10000)
        self.assertEqual(bootstrap["random_seed"], 5301)
        self.assertTrue(bootstrap["report_all_three_candidates"])
        self.assertFalse(bootstrap["decision_gate"])

    def test_no_automatic_winner_or_trading_authorization(self) -> None:
        record = get_exp013_preregistration()
        self.assertFalse(
            record["full_sample_comparison"]["automatic_trading_winner"]
        )
        self.assertFalse(
            record["evidence_context"]["paper_trading_authorized"]
        )
        self.assertFalse(
            record["evidence_context"]["live_trading_authorized"]
        )

    def test_candidate_mutation_is_rejected(self) -> None:
        changed = get_exp013_preregistration()
        changed["candidate_lock"]["candidates"] = changed[
            "candidate_lock"
        ]["candidates"][:-1]
        with self.assertRaisesRegex(ValueError, "three-candidate lock"):
            validate_exp013_preregistration(changed)

    def test_mcpt_shortcut_is_rejected(self) -> None:
        changed = get_exp013_preregistration()
        changed["discovery_wide_selection_aware_mcpt"][
            "all_24_exp012_candidates_run_inside_each_permutation"
        ] = False
        with self.assertRaisesRegex(ValueError, "MCPT plan"):
            validate_exp013_preregistration(changed)

    def test_reporting_standard_is_preserved(self) -> None:
        reporting = get_exp013_preregistration()[
            "reporting_requirements"
        ]
        self.assertTrue(reporting["all_three_candidates_visible"])
        self.assertTrue(
            reporting["selection_reasons_and_limitations_visible"]
        )
        self.assertTrue(reporting["positive_numbers_use_neutral_text"])
        self.assertTrue(reporting["adverse_numbers_use_red_text"])
        self.assertTrue(reporting["green_reserved_for_status_words"])
        self.assertTrue(
            reporting["charts_use_solid_opaque_white_canvas"]
        )


if __name__ == "__main__":
    unittest.main()
