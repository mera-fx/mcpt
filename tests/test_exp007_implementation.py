from __future__ import annotations

from copy import deepcopy
import unittest

from exp007_implementation import (
    get_exp007_implementation,
    validate_exp007_implementation,
)


class Exp007ImplementationTests(unittest.TestCase):
    def test_implementation_is_valid_and_pre_result(self) -> None:
        validate_exp007_implementation()
        record = get_exp007_implementation()
        self.assertEqual(record["implementation_status"], "IMPLEMENTED_NOT_RUN")
        self.assertEqual(record["results_viewed"], "NONE")

    def test_strategy_has_one_fixed_combination(self) -> None:
        record = get_exp007_implementation()
        self.assertFalse(record["optimization_enabled"])
        self.assertEqual(record["parameter_combinations"], 1)
        self.assertEqual(record["signal_engine"]["target_r_multiple"], 1.0)

    def test_mcpt_does_not_optimize(self) -> None:
        analysis = get_exp007_implementation()["analysis"]
        self.assertEqual(analysis["mcpt_permutations"], 1000)
        self.assertFalse(analysis["optimization_inside_mcpt"])

    def test_mutation_is_rejected(self) -> None:
        changed = deepcopy(get_exp007_implementation())
        changed["signal_engine"]["target_r_multiple"] = 1.5
        with self.assertRaisesRegex(ValueError, "signal changed"):
            validate_exp007_implementation(changed, require_files=False)


if __name__ == "__main__":
    unittest.main()
