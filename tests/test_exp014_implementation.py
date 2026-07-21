from __future__ import annotations

from copy import deepcopy
import unittest

from exp014_implementation import (
    get_exp014_implementation,
    validate_exp014_implementation,
)


class Exp014ImplementationTests(unittest.TestCase):
    def test_locked_result_free_implementation_is_valid(self) -> None:
        record = get_exp014_implementation()
        validate_exp014_implementation(record, require_files=False)
        self.assertEqual(record["implementation_status"], "IMPLEMENTED_NOT_RUN")
        self.assertEqual(record["results_viewed"], "NONE")
        self.assertEqual(len(record["outputs"]), 13)
        self.assertEqual(
            record["diagnostic_definitions"]["rolling_trade_windows"],
            [20, 50],
        )
        self.assertFalse(any(record["protections"].values()))

    def test_search_or_trading_switch_is_rejected(self) -> None:
        record = deepcopy(get_exp014_implementation())
        record["protections"]["weight_search_enabled"] = True
        with self.assertRaises(ValueError):
            validate_exp014_implementation(record, require_files=False)

        record = deepcopy(get_exp014_implementation())
        record["protections"]["live_trading_authorized"] = True
        with self.assertRaises(ValueError):
            validate_exp014_implementation(record, require_files=False)

    def test_diagnostic_definition_drift_is_rejected(self) -> None:
        record = deepcopy(get_exp014_implementation())
        record["diagnostic_definitions"]["rolling_trade_windows"] = [10, 20]
        with self.assertRaises(ValueError):
            validate_exp014_implementation(record, require_files=False)


if __name__ == "__main__":
    unittest.main()
