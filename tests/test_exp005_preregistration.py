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

    def test_nq_is_primary_and_mnq_is_not_independent(
        self,
    ) -> None:
        market = get_exp005_preregistration()[
            "market_and_data"
        ]

        self.assertEqual(
            market["primary_evidence_market"],
            "NQ",
        )
        self.assertEqual(
            market["secondary_cost_market"],
            "MNQ",
        )
        self.assertFalse(
            market[
                "secondary_is_independent_evidence"
            ]
        )

    def test_continuous_roll_and_confirmation_lock(
        self,
    ) -> None:
        record = get_exp005_preregistration()
        market = record["market_and_data"]
        split = record["research_split"]

        self.assertEqual(
            market["symbols"],
            {
                "NQ": "NQ.v.0",
                "MNQ": "MNQ.v.0",
            },
        )
        self.assertEqual(
            market["continuous_roll_rule"],
            "volume-ranked front contract",
        )
        self.assertEqual(
            split["quick_transfer_start"],
            "2019-05-06",
        )
        self.assertEqual(
            split["confirmation_access"],
            "LOCKED_UNTIL_QUICK_PASS",
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

    def test_human_preregistration_and_roadmap_exist(
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

        roadmap = (
            root
            / "research"
            / "ORB_structured_variant_roadmap.md"
        )

        self.assertTrue(
            preregistration.exists()
        )
        self.assertTrue(
            roadmap.exists()
        )

        content = preregistration.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "no-optimization transfer test",
            content,
        )
        self.assertIn(
            "NQ.v.0",
            content,
        )
        self.assertIn(
            "MNQ.v.0",
            content,
        )


if __name__ == "__main__":
    unittest.main()
