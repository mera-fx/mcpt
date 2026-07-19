from __future__ import annotations

from copy import deepcopy
import unittest

from exp010_preregistration import (
    OPENING_DRIVE_CANDIDATES,
    get_exp010_preregistration,
    validate_exp010_preregistration,
)


class Exp010PreregistrationTests(unittest.TestCase):
    def test_preregistration_is_valid(self) -> None:
        validate_exp010_preregistration()

    def test_all_four_exp009_candidates_are_locked(self) -> None:
        lock = get_exp010_preregistration()["candidate_lock"]
        self.assertEqual(lock["candidate_count"], 4)
        self.assertEqual(
            tuple(lock["candidates"]),
            OPENING_DRIVE_CANDIDATES,
        )
        self.assertEqual(
            len({item["candidate_id"] for item in lock["candidates"]}),
            4,
        )

    def test_user_reference_is_not_called_independent(self) -> None:
        relationship = get_exp010_preregistration()[
            "relationship_to_exp009"
        ]
        self.assertEqual(
            relationship["user_preferred_reference_candidate"],
            "opening_drive_0p5_1p5r",
        )
        self.assertTrue(
            relationship["preference_is_not_independent_preselection"]
        )
        self.assertTrue(
            relationship[
                "prior_family_selection_across_24_candidates_is_not_corrected"
            ]
        )

    def test_walk_forward_has_five_anchored_folds(self) -> None:
        walk_forward = get_exp010_preregistration()[
            "anchored_walk_forward"
        ]
        self.assertEqual(walk_forward["fold_count"], 5)
        self.assertEqual(
            [fold["test_year"] for fold in walk_forward["folds"]],
            [2021, 2022, 2023, 2024, 2025],
        )
        self.assertTrue(
            walk_forward["selection_repeated_in_each_training_window"]
        )

    def test_mcpt_reselects_all_four_candidates(self) -> None:
        mcpt = get_exp010_preregistration()["selection_aware_mcpt"]
        self.assertEqual(mcpt["permutations"], 1000)
        self.assertEqual(mcpt["random_seed"], 50)
        self.assertTrue(
            mcpt["all_four_candidates_run_inside_each_permutation"]
        )
        self.assertTrue(
            mcpt["same_full_sample_rank_inside_every_permutation"]
        )
        self.assertTrue(
            mcpt["does_not_correct_prior_six_family_selection"]
        )

    def test_measurement_first_reporting_is_locked(self) -> None:
        record = get_exp010_preregistration()
        self.assertTrue(record["evidence_context"]["measurement_first"])
        self.assertTrue(
            record["evidence_context"]["classification_is_secondary"]
        )
        self.assertTrue(
            record["reporting_requirements"]["all_four_candidates_visible"]
        )
        self.assertFalse(
            record["full_sample_comparison"]["automatic_trading_winner"]
        )

    def test_no_paper_or_live_authorization(self) -> None:
        evidence = get_exp010_preregistration()["evidence_context"]
        self.assertFalse(evidence["paper_trading_authorized"])
        self.assertFalse(evidence["live_trading_authorized"])

    def test_candidate_mutation_is_rejected(self) -> None:
        changed = get_exp010_preregistration()
        changed["candidate_lock"]["candidates"] = changed[
            "candidate_lock"
        ]["candidates"][:-1]
        with self.assertRaisesRegex(ValueError, "four-candidate lock"):
            validate_exp010_preregistration(changed)

    def test_seed_mutation_is_rejected(self) -> None:
        changed = get_exp010_preregistration()
        changed["selection_aware_mcpt"]["random_seed"] = 51
        with self.assertRaisesRegex(ValueError, "MCPT plan"):
            validate_exp010_preregistration(changed)

    def test_reporting_colour_standard_is_preserved(self) -> None:
        reporting = get_exp010_preregistration()[
            "reporting_requirements"
        ]
        self.assertTrue(reporting["positive_numbers_use_neutral_text"])
        self.assertTrue(reporting["adverse_numbers_use_red_text"])
        self.assertTrue(reporting["green_reserved_for_status_words"])


if __name__ == "__main__":
    unittest.main()
