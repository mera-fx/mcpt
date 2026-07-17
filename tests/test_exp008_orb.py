from __future__ import annotations

import unittest

from exp007_orb import (
    run_exp007_orb,
)
from exp008_orb import (
    Exp008Parameters,
    locked_exp008_parameters,
    run_exp008_candidate,
    run_exp008_grid_summaries,
    prepare_exp008_arrays,
)
from tests.exp008_test_data import (
    make_exp008_one_minute_data,
)


class Exp008OrbTests(
    unittest.TestCase
):
    def test_locked_grid_has_27_parameters(
        self,
    ) -> None:
        parameters = (
            locked_exp008_parameters()
        )
        self.assertEqual(
            len(parameters),
            27,
        )
        self.assertEqual(
            len(
                {
                    item.key
                    for item in parameters
                }
            ),
            27,
        )

    def test_half_r_target_fills_exactly(
        self,
    ) -> None:
        data = (
            make_exp008_one_minute_data(
                ["2024-01-03"],
                outcomes=[
                    "target_all"
                ],
            )
        )
        parameters = Exp008Parameters(
            45,
            0.5,
            "14:00",
        )
        result = run_exp008_candidate(
            data,
            parameters=parameters,
            symbol="NQ",
        )
        trade = result.trades.iloc[0]
        self.assertEqual(
            trade["exit_reason"],
            "target_0p5r",
        )
        self.assertAlmostEqual(
            trade[
                "gross_r_multiple"
            ],
            0.5,
        )
        self.assertAlmostEqual(
            trade["gross_pnl_usd"],
            25.0,
        )
        self.assertAlmostEqual(
            trade["net_pnl_usd"],
            10.0,
        )

    def test_one_and_half_r_target_fills_exactly(
        self,
    ) -> None:
        data = (
            make_exp008_one_minute_data(
                ["2024-01-03"],
                outcomes=[
                    "target_all"
                ],
            )
        )
        parameters = Exp008Parameters(
            45,
            1.5,
            "15:55",
        )
        result = run_exp008_candidate(
            data,
            parameters=parameters,
            symbol="NQ",
        )
        trade = result.trades.iloc[0]
        self.assertAlmostEqual(
            trade[
                "gross_r_multiple"
            ],
            1.5,
        )
        self.assertAlmostEqual(
            trade["gross_pnl_usd"],
            75.0,
        )
        self.assertAlmostEqual(
            trade["net_pnl_usd"],
            60.0,
        )

    def test_same_minute_stop_and_target_uses_stop(
        self,
    ) -> None:
        data = (
            make_exp008_one_minute_data(
                ["2024-01-03"],
                outcomes=["both"],
            )
        )
        parameters = Exp008Parameters(
            30,
            1.5,
            "14:00",
        )
        result = run_exp008_candidate(
            data,
            parameters=parameters,
            symbol="NQ",
        )
        self.assertEqual(
            result.trades.iloc[0][
                "exit_reason"
            ],
            "opening_range_stop",
        )
        self.assertLess(
            result.trades.iloc[0][
                "net_pnl_usd"
            ],
            0.0,
        )

    def test_gap_through_stop_uses_open(
        self,
    ) -> None:
        data = (
            make_exp008_one_minute_data(
                ["2024-01-03"],
                outcomes=[
                    "gap_stop"
                ],
            )
        )
        parameters = Exp008Parameters(
            15,
            1.0,
            "12:00",
        )
        result = run_exp008_candidate(
            data,
            parameters=parameters,
            symbol="NQ",
        )
        trade = result.trades.iloc[0]
        self.assertEqual(
            trade["exit_reason"],
            "gap_through_opening_range_stop",
        )
        self.assertAlmostEqual(
            trade["exit_price"],
            98.5,
        )

    def test_forced_flat_uses_candidate_open(
        self,
    ) -> None:
        data = (
            make_exp008_one_minute_data(
                ["2024-01-03"],
                outcomes=["time"],
            )
        )
        noon = run_exp008_candidate(
            data,
            parameters=Exp008Parameters(
                45,
                1.5,
                "12:00",
            ),
            symbol="NQ",
        )
        close = run_exp008_candidate(
            data,
            parameters=Exp008Parameters(
                45,
                1.5,
                "15:55",
            ),
            symbol="NQ",
        )
        self.assertEqual(
            noon.trades.iloc[0][
                "exit_reason"
            ],
            "forced_flat_1200",
        )
        self.assertAlmostEqual(
            noon.trades.iloc[0][
                "exit_price"
            ],
            101.75,
        )
        self.assertEqual(
            close.trades.iloc[0][
                "exit_reason"
            ],
            "forced_flat_1555",
        )
        self.assertAlmostEqual(
            close.trades.iloc[0][
                "exit_price"
            ],
            102.25,
        )

    def test_exp007_baseline_matches_exactly(
        self,
    ) -> None:
        data = (
            make_exp008_one_minute_data(
                [
                    "2024-01-03",
                    "2024-01-04",
                ],
                outcomes=[
                    "target_all",
                    "stop",
                ],
            )
        )
        baseline = (
            run_exp008_candidate(
                data,
                parameters=(
                    Exp008Parameters(
                        30,
                        1.0,
                        "14:00",
                    )
                ),
                symbol="NQ",
            )
        )
        frozen_engine = (
            run_exp007_orb(
                data,
                symbol="NQ",
            )
        )
        self.assertEqual(
            baseline.summary[
                "completed_trades"
            ],
            frozen_engine.summary[
                "completed_trades"
            ],
        )
        self.assertAlmostEqual(
            baseline.summary[
                "net_profit_usd"
            ],
            frozen_engine.summary[
                "net_profit_usd"
            ],
        )
        self.assertAlmostEqual(
            baseline.summary[
                "trade_profit_factor"
            ],
            frozen_engine.summary[
                "trade_profit_factor"
            ],
        )
        self.assertEqual(
            baseline.trades[
                "exit_reason"
            ].tolist(),
            frozen_engine.trades[
                "exit_reason"
            ].tolist(),
        )

    def test_grid_summary_runs_all_candidates(
        self,
    ) -> None:
        data = (
            make_exp008_one_minute_data(
                ["2024-01-03"],
                outcomes=[
                    "target_all"
                ],
            )
        )
        arrays = prepare_exp008_arrays(
            data
        )
        grid = (
            run_exp008_grid_summaries(
                arrays,
                symbol="NQ",
            )
        )
        self.assertEqual(
            len(grid),
            27,
        )
        self.assertTrue(
            (
                grid[
                    "short_trades"
                ]
                == 0
            ).all()
        )

    def test_two_tick_stress_reduces_net_profit(
        self,
    ) -> None:
        data = (
            make_exp008_one_minute_data(
                ["2024-01-03"],
                outcomes=[
                    "target_all"
                ],
            )
        )
        parameters = Exp008Parameters(
            30,
            1.0,
            "14:00",
        )
        base = run_exp008_candidate(
            data,
            parameters=parameters,
            symbol="NQ",
            slippage_ticks_per_side=1.0,
        )
        stress = run_exp008_candidate(
            data,
            parameters=parameters,
            symbol="NQ",
            slippage_ticks_per_side=2.0,
        )
        self.assertAlmostEqual(
            base.summary[
                "net_profit_usd"
            ]
            - stress.summary[
                "net_profit_usd"
            ],
            10.0,
        )


if __name__ == "__main__":
    unittest.main()
