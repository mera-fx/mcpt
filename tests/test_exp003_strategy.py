from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from strategy_registry import (
    build_volatility_breakout_position_signal,
    calculate_volatility_compression_components,
    generate_signal,
    get_strategy,
)


class Exp003StrategyTests(unittest.TestCase):
    def test_strategy_is_registered_with_locked_parameters(
        self,
    ) -> None:
        strategy = get_strategy(
            "volatility_compression_breakout_long"
        )

        self.assertEqual(
            strategy.parameter_names,
            (
                "vol_lookback",
                "compression_quantile",
                "breakout_lookback",
            ),
        )

    def test_compression_threshold_is_shifted_one_bar(
        self,
    ) -> None:
        rng = np.random.default_rng(7)
        returns = rng.normal(
            0.0,
            0.002,
            size=2300,
        )
        close = 100 * np.exp(
            np.cumsum(returns)
        )
        index = pd.date_range(
            "2020-01-01",
            periods=len(close),
            freq="h",
        )
        data = pd.DataFrame(
            {
                "open": close,
                "high": close * 1.001,
                "low": close * 0.999,
                "close": close,
            },
            index=index,
        )

        components = (
            calculate_volatility_compression_components(
                data,
                vol_lookback=24,
                compression_quantile=0.2,
                breakout_lookback=24,
            )
        )

        expected_rv = np.log(
            data["close"]
        ).diff().rolling(
            24,
            min_periods=24,
        ).std(ddof=0)

        expected_threshold = expected_rv.rolling(
            2160,
            min_periods=2160,
        ).quantile(0.2).shift(1)

        pd.testing.assert_series_equal(
            components[
                "compression_threshold"
            ],
            expected_threshold.rename(
                "compression_threshold"
            ),
        )

    def test_state_machine_time_exit_and_no_same_bar_reentry(
        self,
    ) -> None:
        index = pd.date_range(
            "2024-01-01",
            periods=171,
            freq="h",
        )
        close = pd.Series(
            100.0,
            index=index,
        )
        recent = pd.Series(
            True,
            index=index,
        )
        breakout = pd.Series(
            99.0,
            index=index,
        )
        exit_level = pd.Series(
            1.0,
            index=index,
        )

        signal = (
            build_volatility_breakout_position_signal(
                close=close,
                recent_compression=recent,
                breakout_level=breakout,
                exit_level=exit_level,
                maximum_holding_bars=168,
            )
        )

        self.assertTrue(
            bool((signal.isin([0.0, 1.0])).all())
        )
        self.assertTrue(
            bool((signal >= 0).all())
        )
        self.assertEqual(
            signal.iloc[:168].tolist(),
            [1.0] * 168,
        )
        self.assertEqual(
            signal.iloc[168],
            0.0,
        )
        self.assertEqual(
            signal.iloc[169],
            1.0,
        )

    def test_future_price_change_does_not_change_past_signal(
        self,
    ) -> None:
        rng = np.random.default_rng(11)
        returns = rng.normal(
            0.0,
            0.002,
            size=2400,
        )
        close = 100 * np.exp(
            np.cumsum(returns)
        )
        index = pd.date_range(
            "2020-01-01",
            periods=len(close),
            freq="h",
        )
        data = pd.DataFrame(
            {
                "open": close,
                "high": close * 1.001,
                "low": close * 0.999,
                "close": close,
            },
            index=index,
        )

        parameters = {
            "vol_lookback": 24,
            "compression_quantile": 0.2,
            "breakout_lookback": 24,
        }

        original = generate_signal(
            "volatility_compression_breakout_long",
            data,
            parameters,
        )

        changed = data.copy()
        changed.iloc[-5:, changed.columns.get_loc(
            "close"
        )] *= 2.0
        changed.iloc[-5:, changed.columns.get_loc(
            "high"
        )] *= 2.0
        changed.iloc[-5:, changed.columns.get_loc(
            "low"
        )] *= 2.0

        changed_signal = generate_signal(
            "volatility_compression_breakout_long",
            changed,
            parameters,
        )

        pd.testing.assert_series_equal(
            original.iloc[:-5],
            changed_signal.iloc[:-5],
        )


if __name__ == "__main__":
    unittest.main()
