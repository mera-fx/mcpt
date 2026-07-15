from __future__ import annotations

import unittest

import pandas as pd

from exp006_candidate_scoring import (
    BASELINE,
    parameter_distance_from_baseline,
    parameter_neighbors,
    select_candidate,
)
from exp006_orb import locked_parameters


class Exp006CandidateScoringTests(unittest.TestCase):
    def make_grid(self) -> pd.DataFrame:
        rows = []
        for index, parameters in enumerate(
            locked_parameters()
        ):
            bonus = (
                1.0
                if parameters.key()
                == "or5_entry1030_long"
                else 0.0
            )
            rows.append(
                {
                    **parameters.to_dict(),
                    "nq_trade_profit_factor": 1.10 + bonus,
                    "nq_net_profit_usd": 10000 + bonus * 10000,
                    "nq_maximum_drawdown_usd": -5000.0,
                    "nq_maximum_drawdown_percent": -5.0,
                    "nq_net_profit_to_drawdown": 2.0 + bonus,
                    "nq_average_trade_to_cost": 3.0 + bonus,
                    "nq_completed_trades": 1200,
                    "nq_profitable_calendar_years": 7,
                    "nq_win_rate_percent": 45.0,
                    "mnq_trade_profit_factor": 1.08 + bonus,
                    "mnq_net_profit_usd": 1000 + bonus * 1000,
                    "mnq_maximum_drawdown_usd": -500.0,
                    "mnq_completed_trades": 1200,
                    "fixed_candidate_2021_2025_nq_net_profit_usd": 8000 + bonus * 8000,
                    "distance_from_exp005_baseline": parameter_distance_from_baseline(parameters),
                }
            )
        return pd.DataFrame(rows)

    def test_baseline_distance_is_zero(self) -> None:
        self.assertEqual(
            parameter_distance_from_baseline(BASELINE),
            0,
        )

    def test_baseline_has_immediate_neighbors(self) -> None:
        neighbors = parameter_neighbors(BASELINE)
        self.assertEqual(len(neighbors), 4)
        self.assertNotIn(BASELINE, neighbors)

    def test_selection_returns_one_stable_candidate(self) -> None:
        selection = select_candidate(self.make_grid())
        self.assertIsNotNone(
            selection.selected_parameters
        )
        self.assertEqual(
            selection.selected_parameters.key(),
            "or5_entry1030_long",
        )
        self.assertEqual(
            int(selection.scored_grid["selected"].sum()),
            1,
        )


if __name__ == "__main__":
    unittest.main()
