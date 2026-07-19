from __future__ import annotations

from copy import deepcopy
import unittest

from exp010_implementation import (
    get_exp010_implementation,
    validate_exp010_implementation,
)


class Exp010ImplementationTests(unittest.TestCase):
    def test_implementation_is_valid_and_result_free(self) -> None:
        validate_exp010_implementation()
        record = get_exp010_implementation()
        self.assertEqual(
            record["implementation_status"], "IMPLEMENTED_NOT_RUN"
        )
        self.assertEqual(record["results_viewed"], "NONE")

    def test_all_four_candidates_are_inside_mcpt(self) -> None:
        record = get_exp010_implementation()
        self.assertEqual(record["candidate_count"], 4)
        self.assertTrue(
            record["analysis"]["all_four_candidates_inside_mcpt"]
        )
        self.assertTrue(record["analysis"]["selection_inside_mcpt"])
        self.assertFalse(
            record["analysis"]["prior_six_family_selection_corrected"]
        )

    def test_user_reference_is_locked(self) -> None:
        self.assertEqual(
            get_exp010_implementation()["user_reference_candidate"],
            "opening_drive_0p5_1p5r",
        )

    def test_mutation_is_rejected(self) -> None:
        changed = deepcopy(get_exp010_implementation())
        changed["analysis"]["mcpt_seed"] = 51
        with self.assertRaisesRegex(ValueError, "analysis"):
            validate_exp010_implementation(
                changed,
                require_files=False,
            )

    def test_prior_experiments_are_protected(self) -> None:
        protections = get_exp010_implementation()["protections"]
        for experiment in (
            "exp005_changed",
            "exp006_changed",
            "exp007_changed",
            "exp008_changed",
            "exp009_changed",
        ):
            self.assertFalse(protections[experiment])
        self.assertFalse(
            protections["result_calculated_during_implementation"]
        )


if __name__ == "__main__":
    unittest.main()
