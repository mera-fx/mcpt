from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from exp005_review_implementation import (
    EXP005_REVIEW_IMPLEMENTATION,
    validate_exp005_review_implementation,
)


class Exp005ReviewImplementationTests(unittest.TestCase):
    def test_implementation_is_valid(self) -> None:
        validate_exp005_review_implementation()

    def test_review_is_read_only(self) -> None:
        protections = EXP005_REVIEW_IMPLEMENTATION["protections"]
        self.assertFalse(protections["strategy_rerun"])
        self.assertFalse(protections["mcpt_rerun"])
        self.assertFalse(protections["parameter_change"])
        self.assertFalse(protections["data_change"])

    def test_all_twelve_checks_are_locked(self) -> None:
        self.assertEqual(len(EXP005_REVIEW_IMPLEMENTATION["checks"]), 12)
        self.assertTrue(EXP005_REVIEW_IMPLEMENTATION["all_checks_required"])

    def test_human_document_exists(self) -> None:
        path = (
            Path(__file__).resolve().parents[1]
            / "research"
            / "EXP-005_review_implementation.md"
        )
        self.assertTrue(path.exists())

    def test_mutated_check_set_is_rejected(self) -> None:
        changed = deepcopy(EXP005_REVIEW_IMPLEMENTATION)
        changed["checks"].pop("direction_balance")
        with self.assertRaisesRegex(ValueError, "check set changed"):
            validate_exp005_review_implementation(changed)


if __name__ == "__main__":
    unittest.main()
