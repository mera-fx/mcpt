from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd
from PIL import Image

from exp012_engine import get_exp012_candidate, run_exp012_candidate
from exp013_report import build_exp013_report
from exp013_selection import FINALIST_IDS
from tests.exp012_test_data import make_exp012_arrays, set_first_cash_bar


def _fixture():
    arrays = make_exp012_arrays(60)
    gap_candidate = get_exp012_candidate(FINALIST_IDS[0])
    set_first_cash_bar(
        arrays,
        opening=101,
        high=101.5,
        low=98.5,
        close=99,
        next_open=100,
    )
    gap = run_exp012_candidate(arrays, gap_candidate, symbol="NQ")
    set_first_cash_bar(
        arrays,
        opening=100,
        high=101.5,
        low=99.5,
        close=101,
        next_open=101,
    )
    premarket = {
        candidate_id: run_exp012_candidate(
            arrays,
            get_exp012_candidate(candidate_id),
            symbol="NQ",
        )
        for candidate_id in FINALIST_IDS[1:]
    }
    results = {FINALIST_IDS[0]: gap, **premarket}
    rows = []
    for candidate_id, result in results.items():
        rows.append(
            {
                **result.summary,
                "mnq_profit_factor": result.summary[
                    "trade_profit_factor"
                ],
                "two_tick_net_profit_usd": result.summary[
                    "net_profit_usd"
                ],
            }
        )
    table = pd.DataFrame.from_records(rows)
    walk = pd.DataFrame(
        {
            "test_year": [2022, 2023, 2024, 2025],
            "selected_candidate_id": list(FINALIST_IDS) + [FINALIST_IDS[0]],
            "test_completed_trades": [10, 11, 12, 13],
            "test_trade_profit_factor": [1.1, 1.2, 0.9, 1.3],
            "test_net_profit_usd": [100.0, 200.0, -50.0, 300.0],
        }
    )
    cost = pd.DataFrame(
        [
            {
                "candidate_id": candidate_id,
                "slippage_ticks_per_side": ticks,
                "net_profit_usd": 1000 - ticks * 100,
            }
            for candidate_id in FINALIST_IDS
            for ticks in (0, 1, 2)
        ]
    )
    mcpt = pd.DataFrame(
        {"maximum_trade_profit_factor": np.linspace(0.8, 2.2, 30)}
    )
    bootstrap = [
        {
            "candidate_id": candidate_id,
            "completed_trades": 100,
            "observed_trade_profit_factor": 1.2,
            "observed_average_trade_usd": 10.0,
            "profit_factor_probability_above_one": 0.9,
            "average_trade_probability_above_zero": 0.9,
        }
        for candidate_id in FINALIST_IDS
    ]
    decision = {
        "mcpt": {
            "real_maximum_trade_profit_factor": 2.02,
            "discovery_wide_p_value": 0.08,
            "permutations_at_least_real": 79,
            "permutations": 1000,
            "fixed_candidate_p_values": {
                value: 0.1 for value in FINALIST_IDS
            },
        },
        "evaluation": {
            "classification": "PROMISING_BUT_UNCERTAIN"
        },
        "plain_english_summary": "The strategies were measured.",
    }
    return arrays, results, table, walk, cost, mcpt, bootstrap, decision


class Exp013ReportTests(unittest.TestCase):
    def test_report_explains_rules_fractions_and_limits(self) -> None:
        values = _fixture()
        with tempfile.TemporaryDirectory() as directory:
            report = build_exp013_report(
                decision=values[7],
                candidate_table=values[2],
                nq_results=values[1],
                nq_arrays=values[0],
                walk_forward=values[3],
                cost_sensitivity=values[4],
                mcpt=values[5],
                bootstrap=values[6],
                output_dir=Path(directory),
            )
            text = report.read_text(encoding="utf-8")
        self.assertIn("How the strategies work", text)
        self.assertIn("100 ÷ 200 = 0.50", text)
        self.assertIn("not a 50% move in NQ", text)
        self.assertIn("not a 75% price change", text)
        self.assertIn("all 24 EXP-012 strategies", text)
        self.assertIn("No paper or live trading is authorized", text)

    def test_all_chart_canvases_are_opaque_white(self) -> None:
        values = _fixture()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            build_exp013_report(
                decision=values[7],
                candidate_table=values[2],
                nq_results=values[1],
                nq_arrays=values[0],
                walk_forward=values[3],
                cost_sensitivity=values[4],
                mcpt=values[5],
                bootstrap=values[6],
                output_dir=output,
            )
            charts = list(output.glob("*.png"))
            self.assertGreaterEqual(len(charts), 8)
            for chart in charts:
                with Image.open(chart).convert("RGBA") as image:
                    self.assertEqual(
                        image.getpixel((0, 0)),
                        (255, 255, 255, 255),
                        chart.name,
                    )


if __name__ == "__main__":
    unittest.main()
