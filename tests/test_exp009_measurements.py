from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from exp009_engine import Exp009Result, get_exp009_candidate
from exp009_measurements import (
    add_pareto_context,
    calculate_candidate_measurements,
    family_measurement_summary,
    rolling_trade_measurements,
)


def _result(
    candidate_id: str,
    *,
    symbol: str,
    pnl: list[float],
) -> Exp009Result:
    candidate = get_exp009_candidate(candidate_id)
    dates = pd.date_range("2021-01-01", periods=len(pnl), freq="180D")
    values = np.asarray(pnl, dtype=float)
    wins = values[values > 0]
    losses = values[values < 0]
    gross_loss = float(losses.sum())
    pf = (
        float(wins.sum() / abs(gross_loss))
        if gross_loss < 0
        else float("inf")
    )
    max_dd = -100.0
    summary = {
        "candidate_id": candidate_id,
        "family_id": candidate.family_id,
        "symbol": symbol,
        "completed_trades": len(values),
        "gross_profit_usd": float(wins.sum()),
        "gross_loss_usd": gross_loss,
        "net_profit_usd": float(values.sum()),
        "trade_profit_factor": pf,
        "win_rate": float(np.mean(values > 0)),
        "average_trade_usd": float(values.mean()),
        "median_trade_usd": float(np.median(values)),
        "average_winner_usd": float(wins.mean()) if len(wins) else 0.0,
        "average_loser_usd": (
            float(losses.mean()) if len(losses) else 0.0
        ),
        "payoff_ratio": 2.0,
        "maximum_drawdown_usd": max_dd,
        "maximum_drawdown_percent": 0.001,
        "net_profit_to_drawdown": float(values.sum() / abs(max_dd)),
        "round_trip_cost_usd": 15.0 if symbol == "NQ" else 3.0,
        "average_trade_to_round_trip_cost": float(
            values.mean() / (15.0 if symbol == "NQ" else 3.0)
        ),
    }
    trades = pd.DataFrame(
        {
            "session_date": dates.strftime("%Y-%m-%d"),
            "year": dates.year,
            "net_pnl_usd": values,
            "holding_minutes": np.arange(len(values)) + 5,
        }
    )
    yearly = (
        trades.groupby("year", as_index=False)
        .agg(
            completed_trades=("net_pnl_usd", "size"),
            net_profit_usd=("net_pnl_usd", "sum"),
        )
    )
    equity = pd.DataFrame(
        {
            "session_date": trades["session_date"],
            "net_pnl_usd": values,
            "cumulative_net_profit_usd": values.cumsum(),
        }
    )
    return Exp009Result(
        candidate=candidate,
        symbol=symbol,
        summary=summary,
        trades=trades,
        equity_curve=equity,
        yearly_results=yearly,
    )


class Exp009MeasurementTests(unittest.TestCase):
    def test_candidate_measurement_retains_context_not_rejection(self) -> None:
        nq = _result(
            "orb_pullback_long_1r",
            symbol="NQ",
            pnl=[100, -50, 120, -40, 90, -30, 80, -20],
        )
        mnq = _result(
            "orb_pullback_long_1r",
            symbol="MNQ",
            pnl=[10, -5, 12, -4, 9, -3, 8, -2],
        )
        zero = _result(
            "orb_pullback_long_1r",
            symbol="NQ",
            pnl=[110, -40, 130, -30, 100, -20, 90, -10],
        )
        two = _result(
            "orb_pullback_long_1r",
            symbol="NQ",
            pnl=[90, -60, 110, -50, 80, -40, 70, -30],
        )
        record = calculate_candidate_measurements(
            nq,
            mnq,
            nq_zero_tick_result=zero,
            nq_two_tick_result=two,
            included_session_count=100,
        )
        self.assertEqual(record["research_status"], "MEASURED_NOT_VALIDATED")
        self.assertIn("maximum_consecutive_losses", record)
        self.assertIn("profitable_month_fraction", record)
        self.assertNotIn("decision", record)

    def test_pareto_context_does_not_create_a_winner(self) -> None:
        table = pd.DataFrame(
            [
                {
                    "candidate_id": "a",
                    "family_id": "f",
                    "trade_profit_factor": 1.2,
                    "win_rate": 0.5,
                    "average_trade_to_round_trip_cost": 2.0,
                    "net_profit_to_drawdown": 3.0,
                    "profitable_year_fraction": 0.8,
                    "maximum_drawdown_usd": -100.0,
                },
                {
                    "candidate_id": "b",
                    "family_id": "f",
                    "trade_profit_factor": 1.1,
                    "win_rate": 0.4,
                    "average_trade_to_round_trip_cost": 1.0,
                    "net_profit_to_drawdown": 2.0,
                    "profitable_year_fraction": 0.6,
                    "maximum_drawdown_usd": -200.0,
                },
            ]
        )
        result = add_pareto_context(table)
        self.assertTrue(bool(result.loc[0, "pareto_nondominated"]))
        self.assertFalse(bool(result.loc[1, "pareto_nondominated"]))
        self.assertNotIn("winner", result.columns)
        self.assertNotIn("score", result.columns)

    def test_family_summary_keeps_all_families(self) -> None:
        rows = []
        for family in ("a", "b"):
            for index in range(4):
                rows.append(
                    {
                        "family_id": family,
                        "net_profit_usd": index,
                        "trade_profit_factor": 1.0 + index / 10,
                        "win_rate": 0.5,
                        "maximum_drawdown_usd": -100.0,
                        "pareto_nondominated": index == 3,
                        "reliability_flag_count": 0,
                    }
                )
        summary = family_measurement_summary(pd.DataFrame(rows))
        self.assertEqual(len(summary), 2)
        self.assertTrue((summary["candidate_count"] == 4).all())

    def test_rolling_trade_measurements_use_locked_100_trade_window(self) -> None:
        trades = pd.DataFrame(
            {
                "session_date": pd.date_range(
                    "2024-01-01", periods=105, freq="D"
                ).strftime("%Y-%m-%d"),
                "net_pnl_usd": np.where(
                    np.arange(105) % 2 == 0, 20.0, -10.0
                ),
            }
        )
        rolling = rolling_trade_measurements(trades)
        self.assertEqual(len(rolling), 6)
        self.assertEqual(int(rolling.iloc[0]["trade_number"]), 100)


if __name__ == "__main__":
    unittest.main()
