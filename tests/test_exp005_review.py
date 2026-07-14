from __future__ import annotations

from copy import deepcopy
import unittest

import pandas as pd

from exp005_full_validation_result import get_exp005_full_validation_result
from exp005_quick_transfer_result import get_exp005_quick_transfer_result
from exp005_review import evaluate_exp005_review


def trades(*, symbol: str, long_count: int, short_count: int, scale: float) -> pd.DataFrame:
    directions = ["long"] * long_count + ["short"] * short_count
    count = len(directions)
    pnl = [
        -1000.0 * scale if index < 300 else 1000.0 * scale
        for index in range(count)
    ]
    return pd.DataFrame(
        {
            "symbol": [symbol] * count,
            "direction": directions,
            "net_pnl_usd": pnl,
        }
    )


def inputs() -> dict:
    cost = pd.DataFrame(
        [
            {
                "symbol": "NQ",
                "slippage_ticks_per_side": 2.0,
                "net_profit_usd": 100000.0,
                "trade_profit_factor": 1.10,
            },
            {
                "symbol": "MNQ",
                "slippage_ticks_per_side": 2.0,
                "net_profit_usd": 9000.0,
                "trade_profit_factor": 1.08,
            },
        ]
    )
    yearly = pd.DataFrame(
        [
            {"symbol": "NQ", "year": 2023, "net_profit_usd": 30000.0},
            {"symbol": "NQ", "year": 2024, "net_profit_usd": 40000.0},
            {"symbol": "NQ", "year": 2025, "net_profit_usd": 46715.0},
            {"symbol": "MNQ", "year": 2023, "net_profit_usd": 3000.0},
        ]
    )
    return {
        "full_result": get_exp005_full_validation_result(),
        "quick_result": get_exp005_quick_transfer_result(),
        "cost_sensitivity": cost,
        "yearly_results": yearly,
        "nq_trades": trades(
            symbol="NQ",
            long_count=367,
            short_count=357,
            scale=1.0,
        ),
        "mnq_trades": trades(
            symbol="MNQ",
            long_count=368,
            short_count=356,
            scale=0.1,
        ),
    }


class Exp005ReviewTests(unittest.TestCase):
    def test_all_checks_pass(self) -> None:
        evaluation = evaluate_exp005_review(**inputs())
        self.assertTrue(evaluation.passed)
        self.assertEqual(evaluation.decision, "ACCEPT_FOR_PAPER_TESTING")
        self.assertEqual(evaluation.failed_checks, ())

    def test_any_failed_check_rejects(self) -> None:
        values = inputs()
        values["full_result"] = deepcopy(values["full_result"])
        values["full_result"]["fixed_rules"]["optimization"] = True
        evaluation = evaluate_exp005_review(**values)
        self.assertFalse(evaluation.passed)
        self.assertEqual(evaluation.decision, "REJECT")
        self.assertIn("fixed_rule_integrity", evaluation.failed_checks)

    def test_two_tick_cost_check_is_strict(self) -> None:
        values = inputs()
        values["cost_sensitivity"].loc[
            values["cost_sensitivity"]["symbol"].eq("MNQ"),
            "trade_profit_factor",
        ] = 1.0
        evaluation = evaluate_exp005_review(**values)
        self.assertIn("two_tick_cost_resilience", evaluation.failed_checks)

    def test_all_three_years_are_required(self) -> None:
        values = inputs()
        values["yearly_results"] = values["yearly_results"].loc[
            ~(
                values["yearly_results"]["symbol"].eq("NQ")
                & values["yearly_results"]["year"].eq(2025)
            )
        ]
        evaluation = evaluate_exp005_review(**values)
        self.assertIn(
            "all_confirmation_years_profitable",
            evaluation.failed_checks,
        )

    def test_drawdown_efficiency_boundary_passes(self) -> None:
        values = inputs()
        values["full_result"] = deepcopy(values["full_result"])
        values["full_result"]["results"]["NQ"]["net_profit_usd"] = 72350.0
        evaluation = evaluate_exp005_review(**values)
        self.assertTrue(evaluation.checks["drawdown_efficiency"]["passed"])

    def test_direction_imbalance_rejects(self) -> None:
        values = inputs()
        values["nq_trades"] = trades(
            symbol="NQ",
            long_count=650,
            short_count=74,
            scale=1.0,
        )
        evaluation = evaluate_exp005_review(**values)
        self.assertIn("direction_balance", evaluation.failed_checks)

    def test_tail_loss_concentration_rejects(self) -> None:
        values = inputs()
        frame = values["nq_trades"].copy()
        frame.loc[:4, "net_pnl_usd"] = -100000.0
        values["nq_trades"] = frame
        evaluation = evaluate_exp005_review(**values)
        self.assertIn("tail_loss_concentration", evaluation.failed_checks)

    def test_contract_consistency_rejects_large_gap(self) -> None:
        values = inputs()
        values["full_result"] = deepcopy(values["full_result"])
        values["full_result"]["results"]["MNQ"]["trade_profit_factor"] = 1.01
        evaluation = evaluate_exp005_review(**values)
        self.assertIn(
            "contract_implementation_consistency",
            evaluation.failed_checks,
        )


if __name__ == "__main__":
    unittest.main()
