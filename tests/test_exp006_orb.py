from __future__ import annotations

import unittest

import numpy as np

from exp005_futures_orb import run_futures_orb
from exp006_orb import (
    OrbParameters,
    locked_parameters,
    prepare_orb_arrays,
    run_candidate_summary,
    run_parameterized_orb,
)
from tests.exp006_test_data import (
    make_five_minute_data,
)


class Exp006OrbTests(unittest.TestCase):
    def test_locked_grid_has_27_parameters(self) -> None:
        parameters = locked_parameters()
        self.assertEqual(len(parameters), 27)
        self.assertEqual(
            len({item.key() for item in parameters}),
            27,
        )

    def test_exp005_baseline_is_exact(self) -> None:
        data = make_five_minute_data(
            ["2024-01-03", "2024-01-04"]
        )
        baseline = run_futures_orb(
            data,
            symbol="NQ",
        )
        candidate = run_parameterized_orb(
            data,
            parameters=OrbParameters(
                opening_range_minutes=15,
                final_entry_time_new_york="12:00",
                direction_mode="both",
            ),
            symbol="NQ",
        )
        for field in (
            "completed_trades",
            "long_trades",
            "short_trades",
            "net_profit_usd",
            "trade_profit_factor",
            "maximum_drawdown_usd",
        ):
            self.assertTrue(
                np.isclose(
                    float(candidate.summary[field]),
                    float(baseline.summary[field]),
                    equal_nan=True,
                )
            )

    def test_direction_mode_is_respected(self) -> None:
        data = make_five_minute_data(
            ["2024-01-03", "2024-01-04"]
        )
        arrays = prepare_orb_arrays(data)
        long_only = run_candidate_summary(
            arrays,
            parameters=OrbParameters(
                15,
                "12:00",
                "long",
            ),
            symbol="NQ",
        )
        short_only = run_candidate_summary(
            arrays,
            parameters=OrbParameters(
                15,
                "12:00",
                "short",
            ),
            symbol="NQ",
        )
        self.assertEqual(long_only["long_trades"], 1)
        self.assertEqual(long_only["short_trades"], 0)
        self.assertEqual(short_only["long_trades"], 0)
        self.assertEqual(short_only["short_trades"], 1)

    def test_reference_drawdown_percentage_is_reported(self) -> None:
        data = make_five_minute_data(
            ["2024-01-03", "2024-01-04"]
        )
        result = run_parameterized_orb(
            data,
            parameters=OrbParameters(
                15,
                "12:00",
                "both",
            ),
            symbol="NQ",
        )
        self.assertIn(
            "maximum_drawdown_percent",
            result.summary,
        )
        self.assertEqual(
            result.summary["reference_capital_usd"],
            100000.0,
        )


if __name__ == "__main__":
    unittest.main()
