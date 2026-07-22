from __future__ import annotations

import unittest

from exp018_implementation import (
    EXPECTED_DATABENTO_CLIENT_VERSION,
    EXPECTED_PREREGISTRATION_COMMIT,
    get_exp018_implementation,
    validate_exp018_implementation,
)


class Exp018ImplementationTests(unittest.TestCase):
    def test_implementation_is_valid(self) -> None:
        validate_exp018_implementation()

    def test_preregistration_dependency_is_frozen(self) -> None:
        self.assertEqual(
            EXPECTED_PREREGISTRATION_COMMIT,
            "fd0844dacab65f25d160e0b32a2273504528551f",
        )
        self.assertEqual(EXPECTED_DATABENTO_CLIENT_VERSION, "0.81.0")

    def test_only_eight_locked_bar_requests_exist(self) -> None:
        record = get_exp018_implementation()["request_boundary"]
        self.assertEqual(record["initial_bar_requests"], 6)
        self.assertEqual(record["repeat_bar_requests"], 2)
        self.assertEqual(record["maximum_successful_bar_requests"], 8)
        self.assertFalse(record["automatic_retry"])
        self.assertTrue(record["failure_requires_review"])
        self.assertEqual(record["maximum_total_estimated_cost_usd"], 1.0)

    def test_remote_method_excludes_continuous_and_batch(self) -> None:
        remote = get_exp018_implementation()["remote_method"]
        self.assertEqual(remote["method"], "timeseries.get_range")
        self.assertEqual(remote["dataset"], "GLBX.MDP3")
        self.assertEqual(remote["schema"], "ohlcv-1m")
        self.assertFalse(remote["batch_calls"])
        self.assertFalse(remote["continuous_symbols"])
        self.assertFalse(remote["parent_symbols"])
        self.assertFalse(remote["unlocked_symbols"])
        self.assertFalse(remote["unlocked_dates"])

    def test_local_audit_cannot_repair_data(self) -> None:
        audit = get_exp018_implementation()["local_audit_boundary"]
        self.assertFalse(audit["timestamp_shift"])
        self.assertFalse(audit["price_rounding"])
        self.assertFalse(audit["bar_fill"])
        self.assertFalse(audit["bar_delete"])
        self.assertFalse(audit["price_repair"])
        self.assertFalse(audit["duplicate_rows_silently_removed"])

    def test_no_strategy_or_trading_authority(self) -> None:
        result = get_exp018_implementation()["result_boundary"]
        self.assertFalse(result["exchange_accuracy_claim"])
        self.assertFalse(result["best_vendor_claim"])
        self.assertFalse(result["full_history_migration"])
        self.assertFalse(result["continuous_roll_construction"])
        self.assertFalse(result["strategy_results"])
        self.assertFalse(result["paper_trading_authorized"])
        self.assertFalse(result["live_trading_authorized"])

    def test_request_mutation_is_rejected(self) -> None:
        changed = get_exp018_implementation()
        changed["request_boundary"]["automatic_retry"] = True
        with self.assertRaisesRegex(ValueError, "request boundary"):
            validate_exp018_implementation(changed)


if __name__ == "__main__":
    unittest.main()
