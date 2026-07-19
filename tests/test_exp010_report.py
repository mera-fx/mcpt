from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd

from exp009_engine import (
    get_exp009_candidate,
    run_exp009_candidate,
)
from exp010_report import build_exp010_report
from exp010_selection import OPENING_DRIVE_IDS
from tests.exp009_test_data import make_exp009_arrays


def report_fixture():
    arrays = make_exp009_arrays(8)
    arrays.open[:, 0] = 100.0
    arrays.close[:, 29] = 102.0
    arrays.high[:, :30] = 102.2
    arrays.low[:, :30] = 99.8
    arrays.open[:, 30] = 102.1
    arrays.open_5m[:, 6] = 102.1
    results = {
        candidate_id: run_exp009_candidate(
            arrays,
            get_exp009_candidate(candidate_id),
            symbol="NQ",
        )
        for candidate_id in OPENING_DRIVE_IDS
    }
    rows = []
    for candidate_id, result in results.items():
        candidate = result.candidate
        rows.append(
            {
                **result.summary,
                "minimum_drive_fraction": candidate.parameters[
                    "minimum_drive_fraction"
                ],
                "exit_mode": candidate.parameters["exit_mode"],
                "mnq_profit_factor": result.summary[
                    "trade_profit_factor"
                ],
                "two_tick_net_profit_usd": result.summary[
                    "net_profit_usd"
                ],
                "profitable_years": 0,
            }
        )
    table = pd.DataFrame.from_records(rows)
    selected_id = OPENING_DRIVE_IDS[0]
    reference_id = "opening_drive_0p5_1p5r"
    decision = {
        "selection": {
            "selected_candidate_id": selected_id,
            "user_reference_candidate_id": reference_id,
        },
        "mcpt": {
            "real_selected_trade_profit_factor": 1.1,
            "real_fixed_reference_trade_profit_factor": 1.1,
            "selection_aware_p_value": 0.05,
            "fixed_reference_p_value": 0.06,
        },
        "evaluation": {
            "classification": "STRONG_HISTORICAL_EVIDENCE",
        },
    }
    walk_forward = pd.DataFrame(
        {
            "test_year": [2021, 2022, 2023, 2024, 2025],
            "selected_candidate_id": [selected_id] * 5,
            "test_completed_trades": [10] * 5,
            "test_trade_profit_factor": [1.1] * 5,
            "test_net_profit_usd": [100.0, -10.0, 50.0, 25.0, 75.0],
        }
    )
    cost = pd.DataFrame(
        [
            {
                "candidate_id": candidate_id,
                "symbol": "NQ",
                "slippage_ticks_per_side": ticks,
                "net_profit_usd": 100.0 - ticks * 10,
            }
            for candidate_id in OPENING_DRIVE_IDS
            for ticks in (0, 1, 2)
        ]
    )
    mcpt = pd.DataFrame(
        {
            "selected_trade_profit_factor": np.linspace(0.8, 1.2, 20),
            "fixed_reference_trade_profit_factor": np.linspace(
                0.7, 1.1, 20
            ),
        }
    )
    bootstrap = [
        {
            "candidate_id": candidate_id,
            "completed_trades": 100,
            "observed_average_trade_usd": 10.0,
            "observed_trade_profit_factor": 1.1,
            "average_trade_probability_above_zero": 0.90,
            "profit_factor_probability_above_one": 0.90,
        }
        for candidate_id in (selected_id, reference_id)
    ]
    return (
        arrays,
        results,
        table,
        decision,
        walk_forward,
        cost,
        mcpt,
        bootstrap,
    )


class Exp010ReportTests(unittest.TestCase):
    def test_report_is_vertical_readable_and_complete(self) -> None:
        fixture = report_fixture()
        with tempfile.TemporaryDirectory() as directory:
            path = build_exp010_report(
                decision=fixture[3],
                candidate_table=fixture[2],
                nq_results=fixture[1],
                nq_arrays=fixture[0],
                walk_forward=fixture[4],
                cost_sensitivity=fixture[5],
                mcpt=fixture[6],
                bootstrap=fixture[7],
                output_dir=Path(directory),
            )
            text = path.read_text(encoding="utf-8")
        self.assertIn("What we tested and how", text)
        self.assertIn("What happened", text)
        self.assertIn("does not correct", text)
        self.assertIn("No paper or live trading", text)
        self.assertIn('class="status-good"', text)
        self.assertNotIn('class="status-good">$100.00', text)
        self.assertIn('class="adverse">$-10.00', text)

    def test_report_creates_primary_visuals(self) -> None:
        fixture = report_fixture()
        expected = {
            "equity_vs_nq_benchmark.png",
            "selected_reference_drawdown.png",
            "annual_candidate_comparison.png",
            "walk_forward_net_profit.png",
            "cost_sensitivity.png",
            "mcpt_distributions.png",
            "selected_reference_trade_distribution.png",
            "report.html",
        }
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            build_exp010_report(
                decision=fixture[3],
                candidate_table=fixture[2],
                nq_results=fixture[1],
                nq_arrays=fixture[0],
                walk_forward=fixture[4],
                cost_sensitivity=fixture[5],
                mcpt=fixture[6],
                bootstrap=fixture[7],
                output_dir=output,
            )
            self.assertTrue(
                expected.issubset({path.name for path in output.iterdir()})
            )


if __name__ == "__main__":
    unittest.main()
