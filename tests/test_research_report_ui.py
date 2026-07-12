from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import pandas as pd

from rebuild_research_report import discover_chart_sections
from research_report_ui import write_research_report


def sample_summary() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ending_capital": [131107.4, 137367.5, 189156.4, 100000.0],
            "total_return_percent": [31.107, 37.367, 89.156, 0.0],
            "max_drawdown_percent": [-28.075, -24.891, -67.38, 0.0],
            "total_trades": [128, 81, 1, 0],
            "win_rate_percent": [34.375, 37.037, 100.0, 0.0],
            "trade_profit_factor": [1.167, 1.317, float("inf"), float("nan")],
            "average_trade_percent": [0.309, 0.514, 89.156, float("nan")],
            "average_holding_hours": [56.492, 60.42, 34966.0, float("nan")],
            "exposure_percent": [20.68, 13.996, 100.0, 0.0],
            "long_trades": [128, 81, 1, 0],
            "short_trades": [0, 0, 0, 0],
            "long_net_profit": [31107.4, 37367.5, 89156.4, 0.0],
            "short_net_profit": [0.0, 0.0, 0.0, 0.0],
        },
        index=[
            "Fixed parameters",
            "Walk-forward",
            "Buy and Hold",
            "Cash",
        ],
    )


def sample_diagnostics() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "total_trades": [128, 81],
            "win_rate_percent": [34.375, 37.037],
            "trade_profit_factor": [1.167, 1.317],
            "average_winner_percent": [4.631, 4.922],
            "average_loser_percent": [-1.955, -2.078],
            "payoff_ratio": [2.369, 2.368],
            "largest_win_percent": [18.0, 17.0],
            "largest_loss_percent": [-8.277, -8.277],
            "fifth_percentile_trade_percent": [-3.0, -3.2],
            "top_1_loss_share_percent": [5.0, 7.0],
            "top_5_loss_share_percent": [16.383, 24.235],
            "max_consecutive_wins": [3, 4],
            "max_consecutive_losses": [8, 6],
            "average_winner_holding_hours": [72.0, 75.0],
            "average_loser_holding_hours": [48.0, 50.0],
        },
        index=["Fixed parameters", "Walk-forward"],
    )


class ResearchReportUiTests(unittest.TestCase):
    def build_report(self, directory: Path) -> Path:
        return write_research_report(
            report_file=directory / "report.html",
            experiment_id="EXP-003",
            experiment_name="Volatility Compression Breakout",
            market_name="BTCUSDT spot",
            timeframe="1h",
            hypothesis="Quiet markets may precede upside continuation.",
            effective_oos_start="2022-01-05",
            oos_end="2025-12-31",
            lifecycle_stage="Accepted For Paper Testing",
            lifecycle_reason="All locked checks passed.",
            lifecycle_next_action="Continue paper testing.",
            best_parameters={
                "vol_lookback": 48,
                "compression_quantile": 0.1,
                "breakout_lookback": 48,
            },
            fixed_parameters={
                "vol_lookback": 48,
                "compression_quantile": 0.2,
                "breakout_lookback": 48,
            },
            best_score=1.115,
            mcpt_p_value=0.038,
            mcpt_source="full_run",
            summary=sample_summary(),
            parameter_stability={
                "edge_assessment": "BROAD_IN_SAMPLE_EDGE",
                "local_surface_assessment": "BROAD_STABLE_REGION",
                "valid_combinations": 27,
                "break_even_count": 27,
                "near_best_count": 21,
                "neighbor_retention_ratio": 0.9917,
                "best_vs_second_gap": 0.0059,
                "interpretation": "Broad and locally stable.",
            },
            diagnostic_summary=sample_diagnostics(),
            diagnostic_by_side=pd.DataFrame(),
            chart_sections=[("Equity", "01_equity.png")],
            generated_from_saved_results=True,
        )

    def test_report_contains_responsive_containment(self) -> None:
        with TemporaryDirectory() as temporary:
            report = self.build_report(Path(temporary))
            text = report.read_text(encoding="utf-8")

        self.assertIn("overflow-x: hidden", text)
        self.assertIn('class="table-shell"', text)
        self.assertIn("grid-template-columns: repeat(2", text)
        self.assertIn('meta name="viewport"', text)

    def test_parameters_are_readable_not_raw_json(self) -> None:
        with TemporaryDirectory() as temporary:
            report = self.build_report(Path(temporary))
            text = report.read_text(encoding="utf-8")

        self.assertIn("Compression Quantile", text)
        self.assertIn("Fixed out-of-sample parameters", text)
        self.assertNotIn('&quot;compression_quantile&quot;', text)

    def test_core_table_uses_readable_labels(self) -> None:
        with TemporaryDirectory() as temporary:
            report = self.build_report(Path(temporary))
            text = report.read_text(encoding="utf-8")

        self.assertIn("Max drawdown", text)
        self.assertIn("Avg trade", text)
        self.assertIn("Additional account and position metrics", text)
        self.assertNotIn("total_return_percent", text)

    def test_chart_discovery_is_ordered_and_readable(self) -> None:
        with TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "02_drawdown.png").touch()
            (directory / "01_equity.png").touch()
            (directory / "parameter_heatmap_slice.png").touch()

            sections = discover_chart_sections(directory)

        self.assertEqual(
            sections[0],
            ("Out-of-Sample Equity", "01_equity.png"),
        )
        self.assertEqual(
            sections[1],
            ("Out-of-Sample Drawdown", "02_drawdown.png"),
        )
        self.assertEqual(
            sections[2][0],
            "Parameter Heatmap Slice",
        )


if __name__ == "__main__":
    unittest.main()
