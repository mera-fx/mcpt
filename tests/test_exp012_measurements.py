from __future__ import annotations

import unittest

from exp012_engine import get_exp012_candidate, run_exp012_candidate
from exp012_measurements import (
    add_pareto_context,
    calculate_exp012_candidate_measurements,
)
from tests.exp012_test_data import (
    make_exp012_arrays,
    set_first_cash_bar,
)


class Exp012MeasurementTests(unittest.TestCase):
    def test_context_measurements_remain_visible(self) -> None:
        arrays = make_exp012_arrays(2)
        set_first_cash_bar(
            arrays,
            opening=100.0,
            high=101.25,
            low=99.5,
            close=101.0,
            next_open=101.0,
        )
        candidate = get_exp012_candidate(
            "gap_continuation_0p25_time"
        )
        nq = run_exp012_candidate(arrays, candidate, symbol="NQ")
        mnq = run_exp012_candidate(arrays, candidate, symbol="MNQ")
        zero = run_exp012_candidate(
            arrays,
            candidate,
            symbol="NQ",
            slippage_ticks_per_side=0,
        )
        two = run_exp012_candidate(
            arrays,
            candidate,
            symbol="NQ",
            slippage_ticks_per_side=2,
        )
        record = calculate_exp012_candidate_measurements(
            nq,
            mnq,
            nq_zero_tick_result=zero,
            nq_two_tick_result=two,
            included_session_count=2,
        )
        self.assertEqual(record["feature_eligible_sessions"], 2)
        self.assertEqual(record["signal_confirmed_sessions"], 2)
        self.assertEqual(record["feature_eligible_rate"], 1.0)
        self.assertIn("signal_confirmation_rate", record)
        self.assertEqual(record["research_status"], "MEASURED_NOT_VALIDATED")
        self.assertNotIn("decision", record)

    def test_pareto_context_does_not_create_winner_or_score(self) -> None:
        import pandas as pd

        table = pd.DataFrame(
            [
                {
                    "candidate_id": "a",
                    "family_id": "gap_continuation",
                    "trade_profit_factor": 1.2,
                    "win_rate": 0.55,
                    "average_trade_to_round_trip_cost": 2.0,
                    "net_profit_to_drawdown": 3.0,
                    "profitable_year_fraction": 0.8,
                    "maximum_drawdown_usd": -100.0,
                },
                {
                    "candidate_id": "b",
                    "family_id": "gap_continuation",
                    "trade_profit_factor": 1.1,
                    "win_rate": 0.50,
                    "average_trade_to_round_trip_cost": 1.0,
                    "net_profit_to_drawdown": 2.0,
                    "profitable_year_fraction": 0.6,
                    "maximum_drawdown_usd": -200.0,
                },
            ]
        )
        result = add_pareto_context(table)
        self.assertNotIn("winner", result.columns)
        self.assertNotIn("score", result.columns)


if __name__ == "__main__":
    unittest.main()
