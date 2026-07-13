from __future__ import annotations

from pathlib import Path
import unittest

from exp004_preregistration import (
    get_exp004_preregistration,
)
from exp005_preregistration import (
    get_exp005_preregistration,
    validate_exp005_preregistration,
)


class Exp005PreregistrationTests(
    unittest.TestCase
):
    def test_preregistration_is_valid(
        self,
    ) -> None:
        validate_exp005_preregistration()

    def test_fixed_rules_match_exp004(
        self,
    ) -> None:
        exp004 = get_exp004_preregistration()
        exp005 = get_exp005_preregistration()

        self.assertEqual(
            exp005[
                "optimization"
            ]["fixed_parameters"],
            exp004["fixed_parameters"],
        )

    def test_optimization_is_disabled(
        self,
    ) -> None:
        record = get_exp005_preregistration()

        self.assertFalse(
            record["optimization"]["enabled"]
        )
        self.assertEqual(
            record[
                "optimization"
            ]["parameter_combinations"],
            1,
        )

    def test_free_rithmic_source_is_locked(
        self,
    ) -> None:
        market = get_exp005_preregistration()[
            "market_and_data"
        ]

        self.assertEqual(
            market["data_provider"],
            (
                "Lucid Trading / Rithmic via Quantower "
                "History Exporter"
            ),
        )
        self.assertEqual(
            market["additional_data_cost"],
            0.0,
        )
        self.assertEqual(
            market["symbols"],
            {
                "NQ": "NQ",
                "MNQ": "MNQ",
            },
        )
        self.assertEqual(
            market["input_symbol_type"],
            "provider_front_month",
        )

    def test_roll_and_adjustment_are_not_overclaimed(
        self,
    ) -> None:
        market = get_exp005_preregistration()[
            "market_and_data"
        ]

        self.assertIn(
            "not exposed",
            market["continuous_roll_rule"],
        )
        self.assertIn(
            "unknown",
            market["price_adjustment"],
        )
        self.assertEqual(
            market["roll_observability"],
            "INDIRECT_ONLY",
        )

    def test_source_samples_are_not_results(
        self,
    ) -> None:
        record = get_exp005_preregistration()
        samples = record[
            "market_and_data"
        ]["source_validation_samples"]

        self.assertEqual(
            record["results_viewed"],
            "NONE",
        )
        self.assertTrue(
            record[
                "source_validation_samples_viewed"
            ]
        )
        self.assertFalse(
            samples["research_results_calculated"]
        )

        for symbol in ("NQ", "MNQ"):
            self.assertEqual(
                samples[symbol][
                    "cash_session_rows"
                ],
                390,
            )
            self.assertEqual(
                samples[symbol][
                    "five_minute_bars"
                ],
                78,
            )

    def test_confirmation_lock_is_unchanged(
        self,
    ) -> None:
        record = get_exp005_preregistration()
        split = record["research_split"]
        acquisition = record[
            "market_and_data"
        ]["data_acquisition"]

        self.assertEqual(
            split["quick_transfer_start"],
            "2019-05-06",
        )
        self.assertEqual(
            split["quick_transfer_end"],
            "2022-12-30",
        )
        self.assertEqual(
            split["confirmation_access"],
            "LOCKED_UNTIL_QUICK_PASS",
        )
        self.assertTrue(
            acquisition[
                "confirmation_export_prohibited"
            ]
        )
        self.assertFalse(
            acquisition[
                "full_quick_export_completed"
            ]
        )

    def test_contract_costs_are_consistent(
        self,
    ) -> None:
        costs = get_exp005_preregistration()[
            "contract_and_cost_model"
        ]

        self.assertEqual(
            costs["NQ"]["tick_value_usd"],
            5.0,
        )
        self.assertEqual(
            costs["MNQ"]["tick_value_usd"],
            0.5,
        )
        self.assertEqual(
            costs["NQ"]["round_trip_cost_usd"],
            15.0,
        )
        self.assertEqual(
            costs["MNQ"]["round_trip_cost_usd"],
            3.0,
        )

    def test_human_documents_exist(
        self,
    ) -> None:
        root = Path(
            __file__
        ).resolve().parents[1]

        preregistration = (
            root
            / "research"
            / "EXP-005_preregistration.md"
        )
        amendment = (
            root
            / "research"
            / "EXP-005_source_amendment.md"
        )
        roadmap = (
            root
            / "research"
            / "ORB_structured_variant_roadmap.md"
        )

        self.assertTrue(
            preregistration.exists()
        )
        self.assertTrue(
            amendment.exists()
        )
        self.assertTrue(
            roadmap.exists()
        )

        content = preregistration.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "Lucid Trading / Rithmic",
            content,
        )
        self.assertIn(
            "Strategy results viewed:** None",
            content,
        )


if __name__ == "__main__":
    unittest.main()
