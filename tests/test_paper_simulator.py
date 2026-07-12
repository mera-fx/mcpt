from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from paper_simulator import (
    build_next_open_target,
    candle_fingerprints,
    isolate_post_activation_signal,
    run_paper_simulation,
    validate_fingerprint_history,
)


def data_frame(
    periods: int = 8,
) -> pd.DataFrame:
    index = pd.date_range(
        "2026-01-01",
        periods=periods,
        freq="h",
    )

    opens = np.arange(
        100,
        100 + periods,
        dtype=float,
    )

    return pd.DataFrame(
        {
            "open": opens,
            "high": opens + 1,
            "low": opens - 1,
            "close": opens + 0.5,
            "volume": 10.0,
        },
        index=index,
    )


class PaperSimulatorTests(
    unittest.TestCase
):
    def test_inherited_long_is_not_adopted(
        self,
    ) -> None:
        data = data_frame()
        signal = pd.Series(
            [1, 1, 1, 0, 1, 1, 0, 0],
            index=data.index,
            dtype=float,
        )

        isolated = (
            isolate_post_activation_signal(
                signal,
                activation_cutoff=(
                    data.index[1]
                ),
            )
        )

        self.assertEqual(
            isolated.iloc[2],
            0.0,
        )
        self.assertEqual(
            isolated.iloc[3],
            0.0,
        )
        self.assertEqual(
            isolated.iloc[4],
            1.0,
        )

    def test_signal_executes_at_next_open(
        self,
    ) -> None:
        data = data_frame()
        isolated = pd.Series(
            [0, 0, 1, 1, 0, 0, 0, 0],
            index=data.index,
            dtype=float,
        )

        target = build_next_open_target(
            isolated
        )

        self.assertEqual(
            target.iloc[2],
            0.0,
        )
        self.assertEqual(
            target.iloc[3],
            1.0,
        )
        self.assertEqual(
            target.iloc[5],
            0.0,
        )

    def test_open_position_is_not_forced_closed(
        self,
    ) -> None:
        data = data_frame()
        signal = pd.Series(
            [0, 0, 1, 1, 1, 1, 1, 1],
            index=data.index,
            dtype=float,
        )

        result = run_paper_simulation(
            data=data,
            raw_signal=signal,
            activation_cutoff=data.index[0],
            starting_capital=100_000,
            commission_bps_per_side=5,
            slippage_bps_per_side=2,
        )

        self.assertEqual(
            len(result.completed_trades),
            0,
        )
        self.assertIsNotNone(
            result.open_position
        )
        self.assertEqual(
            result.summary[
                "current_position"
            ],
            1,
        )

    def test_completed_trade_charges_round_trip_cost(
        self,
    ) -> None:
        data = data_frame()
        signal = pd.Series(
            [0, 1, 1, 0, 0, 0, 0, 0],
            index=data.index,
            dtype=float,
        )

        result = run_paper_simulation(
            data=data,
            raw_signal=signal,
            activation_cutoff=data.index[0],
            starting_capital=100_000,
            commission_bps_per_side=5,
            slippage_bps_per_side=2,
        )

        trade = result.completed_trades.iloc[
            0
        ]

        self.assertEqual(
            trade[
                "commission_bps_round_trip"
            ],
            10,
        )
        self.assertEqual(
            trade[
                "slippage_bps_round_trip"
            ],
            4,
        )

    def test_rebuild_is_deterministic(
        self,
    ) -> None:
        data = data_frame()
        signal = pd.Series(
            [0, 1, 1, 0, 1, 1, 0, 0],
            index=data.index,
            dtype=float,
        )

        arguments = {
            "data": data,
            "raw_signal": signal,
            "activation_cutoff": (
                data.index[0]
            ),
            "starting_capital": 100_000,
            "commission_bps_per_side": 5,
            "slippage_bps_per_side": 2,
        }

        first = run_paper_simulation(
            **arguments
        )

        second = run_paper_simulation(
            **arguments
        )

        pd.testing.assert_frame_equal(
            first.equity_curve,
            second.equity_curve,
        )

        pd.testing.assert_frame_equal(
            first.completed_trades,
            second.completed_trades,
        )

    def test_long_flat_only(
        self,
    ) -> None:
        data = data_frame()
        signal = pd.Series(
            [0, -1, 2, 1, -5, 0, 0, 0],
            index=data.index,
            dtype=float,
        )

        result = run_paper_simulation(
            data=data,
            raw_signal=signal,
            activation_cutoff=data.index[0],
            starting_capital=100_000,
            commission_bps_per_side=5,
            slippage_bps_per_side=2,
        )

        self.assertTrue(
            result.target_position.isin(
                [0.0, 1.0]
            ).all()
        )

    def test_reconciliation_passes(
        self,
    ) -> None:
        data = data_frame()
        signal = pd.Series(
            [0, 1, 1, 0, 1, 0, 0, 0],
            index=data.index,
            dtype=float,
        )

        result = run_paper_simulation(
            data=data,
            raw_signal=signal,
            activation_cutoff=data.index[0],
            starting_capital=100_000,
            commission_bps_per_side=5,
            slippage_bps_per_side=2,
        )

        self.assertTrue(
            result.reconciliation[
                "passed"
            ]
        )

        self.assertEqual(
            result.reconciliation[
                "unresolved_errors"
            ],
            0,
        )

    def test_changed_fingerprint_is_rejected(
        self,
    ) -> None:
        data = data_frame()
        previous = candle_fingerprints(
            data
        )

        changed = data.copy()
        changed.iloc[
            0,
            changed.columns.get_loc(
                "close"
            ),
        ] += 1.0

        current = candle_fingerprints(
            changed
        )

        with self.assertRaises(
            RuntimeError
        ):
            validate_fingerprint_history(
                previous=previous,
                current=current,
            )


if __name__ == "__main__":
    unittest.main()
