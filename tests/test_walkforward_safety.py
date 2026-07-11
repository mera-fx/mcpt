from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd

from run_research_lab import build_walkforward_signal


class WalkForwardSafetyTests(unittest.TestCase):
    def test_training_data_ends_before_test_block_starts(
        self,
    ) -> None:
        index = pd.date_range(
            "2024-01-01",
            periods=10,
            freq="h",
        )

        research_data = pd.DataFrame(
            {
                "open": range(100, 110),
                "high": range(101, 111),
                "low": range(99, 109),
                "close": range(100, 110),
            },
            index=index,
        )

        out_of_sample_data = (
            research_data.iloc[6:].copy()
        )

        config = SimpleNamespace(
            walkforward_retrain_bars=2,
            walkforward_training_bars=4,
            strategy_name="dummy",
        )

        def fake_optimize(
            training_data,
            _config,
        ):
            return (
                {"lookback": 2},
                1.1,
                pd.DataFrame(),
            )

        def fake_generate_signal(
            _strategy_name,
            data,
            _parameters,
        ):
            return pd.Series(
                0.0,
                index=data.index,
            )

        with (
            patch(
                "run_research_lab.optimize_strategy",
                side_effect=fake_optimize,
            ),
            patch(
                "run_research_lab.generate_signal",
                side_effect=fake_generate_signal,
            ),
        ):
            _, parameter_table = (
                build_walkforward_signal(
                    research_data,
                    out_of_sample_data,
                    config,
                )
            )

        self.assertEqual(
            len(parameter_table),
            2,
        )

        for _, row in parameter_table.iterrows():
            self.assertLess(
                pd.Timestamp(row["training_end"]),
                pd.Timestamp(row["test_start"]),
            )

            self.assertEqual(
                int(row["training_rows"]),
                4,
            )


if __name__ == "__main__":
    unittest.main()
