from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from exp004_quick_screen import (
    evaluate_exp004_quick_screen,
    load_exp004_in_sample_data,
    validate_exp004_config_matches_preregistration,
)
from experiment_config import (
    load_experiment,
)
from intraday_market_foundation import (
    expected_regular_session_index,
)


def one_session(
    session_date: str,
) -> pd.DataFrame:
    index = (
        expected_regular_session_index(
            session_date
        )
        .tz_convert("UTC")
    )

    return pd.DataFrame(
        {
            "open": 100.0,
            "high": 100.5,
            "low": 99.5,
            "close": 100.0,
            "volume": 1000.0,
            "session_date": (
                session_date
            ),
            "slot": np.arange(
                78,
                dtype=int,
            ),
        },
        index=index,
    )


class Exp004QuickScreenTests(
    unittest.TestCase
):
    def test_config_matches_preregistration(
        self,
    ) -> None:
        config = load_experiment(
            "EXP-004"
        )

        validate_exp004_config_matches_preregistration(
            config
        )

    def test_all_gates_pass(
        self,
    ) -> None:
        evaluation = (
            evaluate_exp004_quick_screen(
                best_in_sample_trade_pf=1.11,
                fixed_in_sample_trade_pf=1.06,
                parameter_combinations_pf_ge_1=3,
                quick_mcpt_p_value=0.20,
                fixed_in_sample_completed_trades=250,
                fixed_in_sample_long_trades=50,
                fixed_in_sample_short_trades=50,
                included_invalid_sessions=0,
            )
        )

        self.assertTrue(
            evaluation.passed
        )
        self.assertEqual(
            evaluation.decision,
            "PASS_TO_FULL_VALIDATION",
        )

    def test_profit_factor_gates_are_strict(
        self,
    ) -> None:
        evaluation = (
            evaluate_exp004_quick_screen(
                best_in_sample_trade_pf=1.10,
                fixed_in_sample_trade_pf=1.05,
                parameter_combinations_pf_ge_1=9,
                quick_mcpt_p_value=0.01,
                fixed_in_sample_completed_trades=500,
                fixed_in_sample_long_trades=200,
                fixed_in_sample_short_trades=200,
                included_invalid_sessions=0,
            )
        )

        self.assertFalse(
            evaluation.passed
        )
        self.assertIn(
            "best_in_sample_trade_pf",
            evaluation.failed_gates,
        )
        self.assertIn(
            "fixed_in_sample_trade_pf",
            evaluation.failed_gates,
        )

    def test_any_failed_gate_rejects(
        self,
    ) -> None:
        evaluation = (
            evaluate_exp004_quick_screen(
                best_in_sample_trade_pf=1.30,
                fixed_in_sample_trade_pf=1.20,
                parameter_combinations_pf_ge_1=9,
                quick_mcpt_p_value=0.04,
                fixed_in_sample_completed_trades=500,
                fixed_in_sample_long_trades=200,
                fixed_in_sample_short_trades=49,
                included_invalid_sessions=0,
            )
        )

        self.assertEqual(
            evaluation.decision,
            "REJECT",
        )

    def test_loader_rejects_oos_session(
        self,
    ) -> None:
        data = one_session(
            "2023-01-03"
        )

        with TemporaryDirectory() as temporary:
            path = (
                Path(temporary)
                / "data.parquet"
            )

            path.touch()

            with patch(
                "exp004_quick_screen.pd.read_parquet",
                return_value=data,
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    "unauthorized|out-of-sample",
                ):
                    load_exp004_in_sample_data(
                        path
                    )


if __name__ == "__main__":
    unittest.main()
