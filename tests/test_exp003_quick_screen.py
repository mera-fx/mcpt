from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

from exp003_quick_screen import (
    evaluate_exp003_quick_screen,
    validate_exp003_config_matches_preregistration,
)
from experiment_config import load_experiment
from run_exp003_quick_screen import (
    load_exp003_in_sample_data,
)


class Exp003QuickScreenTests(unittest.TestCase):
    def test_config_matches_locked_preregistration(
        self,
    ) -> None:
        config = load_experiment("EXP-003")
        validate_exp003_config_matches_preregistration(
            config
        )

    def test_all_gates_pass(self) -> None:
        result = evaluate_exp003_quick_screen(
            best_in_sample_bar_pf=1.10,
            break_even_combination_count=10,
            neighbor_retention_ratio=0.97,
            quick_mcpt_p_value=0.12,
            fixed_in_sample_completed_trades=70,
        )

        self.assertTrue(result.passed)
        self.assertEqual(
            result.decision,
            "PASS_TO_FULL_VALIDATION",
        )
        self.assertEqual(
            result.failed_gates,
            (),
        )

    def test_profit_factor_gate_is_strict(self) -> None:
        result = evaluate_exp003_quick_screen(
            best_in_sample_bar_pf=1.0,
            break_even_combination_count=10,
            neighbor_retention_ratio=0.97,
            quick_mcpt_p_value=0.12,
            fixed_in_sample_completed_trades=70,
        )

        self.assertFalse(result.passed)
        self.assertIn(
            "best_in_sample_bar_pf",
            result.failed_gates,
        )

    def test_any_failed_gate_rejects(self) -> None:
        result = evaluate_exp003_quick_screen(
            best_in_sample_bar_pf=1.10,
            break_even_combination_count=5,
            neighbor_retention_ratio=np.nan,
            quick_mcpt_p_value=0.21,
            fixed_in_sample_completed_trades=49,
        )

        self.assertFalse(result.passed)
        self.assertEqual(
            result.decision,
            "REJECT",
        )
        self.assertEqual(
            len(result.failed_gates),
            4,
        )

    def test_loader_excludes_out_of_sample_rows(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "data.parquet"
            index = pd.date_range(
                "2021-12-30",
                periods=96,
                freq="h",
            )
            close = np.linspace(
                100.0,
                110.0,
                len(index),
            )
            data = pd.DataFrame(
                {
                    "open": close,
                    "high": close + 1,
                    "low": close - 1,
                    "close": close,
                },
                index=index,
            )
            path.touch()

            with patch(
                "run_exp003_quick_screen.pd.read_parquet",
                return_value=data,
            ):
                loaded = load_exp003_in_sample_data(
                    path,
                    in_sample_start=(
                        "2021-12-30 00:00:00"
                    ),
                    in_sample_end=(
                        "2022-01-01 00:00:00"
                    ),
                )

            self.assertEqual(len(loaded), 48)
            self.assertTrue(
                bool(
                    (
                        loaded.index
                        < pd.Timestamp(
                            "2022-01-01"
                        )
                    ).all()
                )
            )


if __name__ == "__main__":
    unittest.main()
