from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import pandas as pd

from exp007_report import build_exp007_report


def summary(symbol: str, multiplier: float = 1.0) -> dict:
    return {
        "symbol": symbol,
        "completed_trades": 600,
        "long_trades": 600,
        "short_trades": 0,
        "net_profit_usd": 1000.0 * multiplier,
        "trade_profit_factor": 1.2,
        "win_rate_percent": 50.0,
        "average_trade_usd": 10.0 * multiplier,
        "maximum_drawdown_usd": -200.0 * multiplier,
        "maximum_drawdown_percent": -2.0,
        "return_percent": 10.0,
    }


def decision() -> dict:
    gates = {
        "nq_trade_profit_factor": {
            "actual": 1.2,
            "operator": ">",
            "threshold": 1.0,
            "passed": True,
        }
    }
    return {
        "results": {"NQ": summary("NQ"), "MNQ": summary("MNQ", 0.1)},
        "evaluation": {
            "decision": "LOCK_FIXED_EXP007_CANDIDATE_FOR_FORWARD_PAPER_COMPARISON",
            "passed": True,
            "failed_gates": [],
            "gates": gates,
        },
        "bootstrap": {
            "average_trade_usd_95_percentile_interval": [2.0, 18.0],
            "trade_profit_factor_95_percentile_interval": [1.05, 1.4],
        },
        "mcpt": {
            "permutations": 1000,
            "p_value": 0.02,
            "permutations_at_least_real": 19,
        },
    }


class Exp007ReportTests(unittest.TestCase):
    def build(self, directory: str) -> Path:
        equity = pd.DataFrame(
            {
                "session_date": ["2024-01-03", "2024-01-04"],
                "cumulative_net_pnl_usd": [10.0, 5.0],
                "drawdown_usd": [0.0, -5.0],
            }
        )
        yearly = pd.DataFrame(
            {
                "symbol": ["NQ", "MNQ"],
                "year": [2024, 2024],
                "net_profit_usd": [10.0, 1.0],
                "completed_trades": [1, 1],
            }
        )
        costs = pd.DataFrame(
            {
                "symbol": ["NQ", "NQ", "MNQ", "MNQ"],
                "slippage_ticks_per_side": [1.0, 2.0, 1.0, 2.0],
                "net_profit_usd": [10.0, 5.0, 1.0, 0.5],
            }
        )
        mcpt = pd.DataFrame(
            {"trade_profit_factor": [0.9, 1.0, 1.1, 1.2]}
        )
        return build_exp007_report(
            decision=decision(),
            nq_equity=equity,
            mnq_equity=equity,
            yearly=yearly,
            cost_sensitivity=costs,
            mcpt=mcpt,
            output_dir=Path(directory),
        )

    def test_report_is_vertical_and_complete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report = self.build(directory)
            source = report.read_text(encoding="utf-8")
        self.assertIn("margin-left:250px", source)
        self.assertIn("NQ total equity", source)
        self.assertIn("Locked decision gates", source)
        self.assertIn("All trades", source)

    def test_report_creates_all_primary_charts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.build(directory)
            assets = Path(directory) / "assets"
            names = {path.name for path in assets.glob("*.png")}
        self.assertIn("nq_total_equity.png", names)
        self.assertIn("nq_drawdown_percent.png", names)
        self.assertIn("mcpt_profit_factor.png", names)


if __name__ == "__main__":
    unittest.main()
