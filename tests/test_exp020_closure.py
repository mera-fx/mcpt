from __future__ import annotations

import unittest

from exp020_closure import (
    get_exp020_closure,
    validate_exp020_closure,
)


class Exp020ClosureTests(unittest.TestCase):
    def test_closure_is_valid(self):
        validate_exp020_closure()

    def test_classification_is_locked(self):
        record = get_exp020_closure()

        self.assertEqual(
            record["research_status"],
            "REVIEW",
        )
        self.assertEqual(
            record["classification"],
            "QUALIFIED_WITH_DISCLOSED_CALENDAR_FALLBACKS",
        )

    def test_source_and_construction_counts_are_locked(self):
        record = get_exp020_closure()

        self.assertEqual(
            record["source"]["contract_count"],
            66,
        )
        self.assertEqual(
            record["source"]["record_count"],
            6_276_486,
        )
        self.assertEqual(
            record["construction"]["row_count_per_series"],
            5_463_753,
        )
        self.assertEqual(
            record["construction"]["series_count"],
            4,
        )

    def test_all_hard_checks_passed(self):
        construction = get_exp020_closure()[
            "construction"
        ]

        self.assertEqual(
            construction["hard_checks"],
            20,
        )
        self.assertEqual(
            construction["hard_failure_count"],
            0,
        )
        self.assertTrue(
            construction["construction_complete"]
        )

    def test_primary_volume_trigger_was_inactive(self):
        result = get_exp020_closure()[
            "method_result"
        ]

        self.assertEqual(
            result["volume_crossovers_selected"],
            0,
        )
        self.assertEqual(
            result["primary_calendar_fallbacks"],
            65,
        )
        self.assertEqual(
            result["fallbacks_without_provider_warnings"],
            42,
        )

    def test_primary_and_calendar_data_are_identical(self):
        result = get_exp020_closure()[
            "method_result"
        ]

        self.assertEqual(
            result["identical_roll_dates"],
            65,
        )
        self.assertEqual(
            result["identical_roll_differences"],
            65,
        )
        self.assertTrue(
            result["unadjusted_market_data_identical"]
        )
        self.assertTrue(
            result["adjusted_market_data_identical"]
        )
        self.assertEqual(
            result["distinct_continuous_datasets"],
            2,
        )

    def test_outputs_and_rebuild_are_locked(self):
        record = get_exp020_closure()

        self.assertEqual(
            len(record["output_hashes"]),
            11,
        )
        self.assertTrue(
            record["construction"]["independent_rebuild"]
        )
        self.assertFalse(
            record["source"]["archive_modified"]
        )

    def test_no_strategy_or_trading_authorization(self):
        interpretation = get_exp020_closure()[
            "interpretation"
        ]

        prohibited = (
            "strategy_edge_tested",
            "strategy_run",
            "strategy_use_authorized",
            "paper_trading_authorized",
            "live_trading_authorized",
        )

        self.assertTrue(
            all(
                interpretation[key] is False
                for key in prohibited
            )
        )

    def test_exp021_is_required(self):
        boundary = get_exp020_closure()[
            "next_research_boundary"
        ]

        self.assertTrue(
            boundary["exp020_frozen"]
        )
        self.assertTrue(
            boundary["rerun_exp020_prohibited"]
        )
        self.assertTrue(
            boundary["exp021_preregistration_required"]
        )
        self.assertTrue(
            boundary["strategy_research_not_authorized"]
        )

    def test_mutation_is_rejected(self):
        record = get_exp020_closure()
        record["method_result"][
            "volume_crossovers_selected"
        ] = 1

        with self.assertRaisesRegex(
            ValueError,
            "closure record changed",
        ):
            validate_exp020_closure(record)


if __name__ == "__main__":
    unittest.main()
