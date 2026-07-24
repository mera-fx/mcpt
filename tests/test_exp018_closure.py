import unittest

from exp018_closure import (
    get_exp018_closure,
    validate_exp018_closure,
)


class Exp018ClosureTests(unittest.TestCase):
    def test_valid(self):
        validate_exp018_closure()

    def test_qualified_source(self):
        record = get_exp018_closure()

        self.assertEqual(
            record["classification"],
            "QUALIFIED_AS_ACCESSIBLE_EXACT_CONTRACT_SOURCE",
        )
        self.assertEqual(
            record["research_status"],
            "REVIEW",
        )

    def test_all_locked_requests_completed(self):
        result = get_exp018_closure()["request_result"]

        self.assertEqual(
            result["initial_windows_measured"],
            6,
        )
        self.assertEqual(
            result["repeatability_windows_measured"],
            2,
        )
        self.assertEqual(
            result["successful_bar_requests"],
            8,
        )
        self.assertEqual(
            result["automatic_retries"],
            0,
        )
        self.assertLessEqual(
            result["total_estimated_cost_usd"],
            1.0,
        )

    def test_coverage_passed(self):
        coverage = get_exp018_closure()["coverage"]

        self.assertGreaterEqual(
            coverage[
                "minimum_regular_trade_minute_coverage"
            ],
            0.999,
        )
        self.assertGreaterEqual(
            coverage[
                "minimum_extended_trade_minute_coverage"
            ],
            0.995,
        )

    def test_repeatability_passed(self):
        repeats = get_exp018_closure()["repeatability"]

        self.assertEqual(len(repeats), 2)

        for item in repeats:
            self.assertGreaterEqual(
                item["delay_hours"],
                24.0,
            )
            self.assertTrue(
                item["minimum_delay_met"]
            )
            self.assertTrue(
                item["canonical_hash_match"]
            )
            self.assertTrue(
                item["row_count_match"]
            )
            self.assertTrue(
                item["timestamp_set_match"]
            )

    def test_no_accuracy_or_trading_claim(self):
        interpretation = get_exp018_closure()[
            "interpretation"
        ]

        self.assertFalse(
            interpretation["exchange_accuracy_verified"]
        )
        self.assertFalse(
            interpretation["best_vendor_selected"]
        )
        self.assertFalse(
            interpretation["strategy_run"]
        )
        self.assertFalse(
            interpretation["paper_trading_authorized"]
        )
        self.assertFalse(
            interpretation["live_trading_authorized"]
        )

    def test_repeatability_mutation_rejected(self):
        record = get_exp018_closure()
        record["repeatability"][0][
            "canonical_hash_match"
        ] = False

        with self.assertRaisesRegex(
            ValueError,
            "repeatability",
        ):
            validate_exp018_closure(record)


if __name__ == "__main__":
    unittest.main()
