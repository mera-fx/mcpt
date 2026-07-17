from __future__ import annotations

from copy import deepcopy
import unittest

from exp007_preregistration import (
    get_exp007_preregistration,
    validate_exp007_preregistration,
)


class Exp007PreregistrationTests(
    unittest.TestCase
):
    def test_preregistration_is_valid(
        self,
    ) -> None:
        validate_exp007_preregistration()

    def test_strategy_is_one_fixed_combination(
        self,
    ) -> None:
        rules = get_exp007_preregistration()[
            "fixed_strategy_rules"
        ]
        self.assertFalse(
            rules["optimization_enabled"]
        )
        self.assertEqual(
            rules["parameter_combinations"],
            1,
        )
        self.assertEqual(
            rules["opening_range_minutes"],
            30,
        )
        self.assertEqual(
            rules["direction_mode"],
            "long_only",
        )
        self.assertEqual(
            rules["reward_to_risk"],
            1.0,
        )
        self.assertEqual(
            rules["forced_flat_time_new_york"],
            "14:00",
        )

    def test_sizing_is_isolated(
        self,
    ) -> None:
        sizing = get_exp007_preregistration()[
            "position_sizing"
        ]
        self.assertEqual(
            sizing["method"],
            "FIXED_ONE_CONTRACT",
        )
        self.assertFalse(
            sizing[
                "volatility_targeting_enabled"
            ]
        )

    def test_no_exp005_pf_improvement_gate(
        self,
    ) -> None:
        gates = get_exp007_preregistration()[
            "historical_decision_gates"
        ]
        self.assertFalse(
            gates[
                "profit_factor_improvement_vs_exp005_required"
            ]
        )
        self.assertEqual(
            gates[
                "minimum_nq_trade_profit_factor_strict"
            ],
            1.0,
        )

    def test_mcpt_is_fixed_strategy_1000(
        self,
    ) -> None:
        mcpt = get_exp007_preregistration()[
            "session_aware_mcpt"
        ]
        self.assertEqual(
            mcpt["permutations"],
            1000,
        )
        self.assertFalse(
            mcpt[
                "strategy_reoptimized_inside_permutation"
            ]
        )
        self.assertEqual(
            mcpt["random_seed"],
            47,
        )

    def test_rule_mutation_is_rejected(
        self,
    ) -> None:
        changed = (
            get_exp007_preregistration()
        )
        changed["fixed_strategy_rules"][
            "reward_to_risk"
        ] = 1.5

        with self.assertRaisesRegex(
            ValueError,
            "fixed strategy changed",
        ):
            validate_exp007_preregistration(
                changed
            )

    def test_historical_claim_is_exploratory(
        self,
    ) -> None:
        interpretation = (
            get_exp007_preregistration()[
                "interpretation"
            ]
        )
        self.assertEqual(
            interpretation[
                "historical_status"
            ],
            "EXPLORATORY_BECAUSE_2019_2025_WAS_ALREADY_VIEWED",
        )
        self.assertTrue(
            interpretation[
                "historical_result_cannot_authorize_live_trading"
            ]
        )


if __name__ == "__main__":
    unittest.main()
