from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import pandas as pd
from PIL import Image

from exp014_measurements import (
    behaviour_breakdowns,
    concentration_measurements,
    drawdown_diagnostics,
    enrich_trade_ledger,
    monthly_measurements,
    overlap_measurements,
    period_comparison,
    rolling_trade_measurements,
    session_pnl_table,
    session_regime_table,
    sleeve_pair_measurements,
)
from exp014_preregistration import FINALIST_IDS
from exp014_report import build_exp014_report
from tests.exp014_test_data import (
    synthetic_exp014_arrays,
    synthetic_exp014_results,
)


EXPECTED_CHARTS = {
    "standalone_equity_vs_benchmark.png",
    "standalone_drawdown.png",
    "sleeve_pair_equity.png",
    "sleeve_pair_drawdown.png",
    "pnl_correlation.png",
    "overlap_matrix.png",
    "overlap_detail.png",
    "period_comparison.png",
    "regime_heatmaps.png",
    "context_strength.png",
    "direction_exit.png",
    "holding_time.png",
    "entry_exit_time.png",
    "mfe_mae.png",
    "profit_concentration.png",
    "annual_comparison.png",
    "monthly_heatmaps.png",
    "rolling_trade_behaviour.png",
}


class Exp014ReportTests(unittest.TestCase):
    def test_complete_vertical_report_and_opaque_charts(self) -> None:
        arrays = synthetic_exp014_arrays()
        results = synthetic_exp014_results(arrays)
        regimes, boundary = session_regime_table(arrays)
        ledgers = {
            candidate_id: enrich_trade_ledger(
                arrays, results[candidate_id], regimes
            )
            for candidate_id in FINALIST_IDS
        }
        behaviour = behaviour_breakdowns(ledgers)
        periods = period_comparison(ledgers)
        session_pnl = session_pnl_table(arrays, ledgers)
        monthly = monthly_measurements(session_pnl, ledgers)
        rolling = rolling_trade_measurements(ledgers)
        concentration = concentration_measurements(ledgers)
        overlap = overlap_measurements(session_pnl, ledgers)
        pairs, pair_daily = sleeve_pair_measurements(session_pnl, ledgers)
        drawdowns = drawdown_diagnostics(session_pnl, pair_daily)
        candidate_table = pd.DataFrame(
            [results[value].summary for value in FINALIST_IDS]
        )
        decision = {
            "plain_english_summary": "Synthetic explanatory summary.",
            "regime_context": {"volatility_boundary": boundary},
            "exp013_context": {
                "classification": "STRONG_HISTORICAL_EVIDENCE",
                "walk_forward_profitable_folds": 3,
                "walk_forward_total_folds": 4,
                "walk_forward_net_profit_usd": 26295.0,
                "discovery_wide_mcpt_p_value": 4 / 1001,
                "mcpt_candidate_count": 24,
                "bootstrap_resamples_per_finalist": 10000,
            },
        }
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            report = build_exp014_report(
                decision=decision,
                candidate_table=candidate_table,
                arrays=arrays,
                ledgers=ledgers,
                behaviour=behaviour,
                periods=periods,
                monthly=monthly,
                rolling=rolling,
                drawdown_diagnostics=drawdowns,
                concentration=concentration,
                overlap=overlap,
                pair_measurements=pairs,
                session_pnl=session_pnl,
                pair_session_pnl=pair_daily,
                output_dir=output,
            )
            self.assertTrue(report.is_file())
            self.assertEqual(
                {path.name for path in output.glob("*.png")},
                EXPECTED_CHARTS,
            )
            page = report.read_text(encoding="utf-8")
            self.assertIn("How the strategies work", page)
            self.assertIn("Frozen EXP-013 evidence retained", page)
            self.assertIn("What changed in 2025?", page)
            self.assertIn("Drawdown duration and recovery", page)
            self.assertIn("No optimization, winner or trading", page)
            self.assertNotIn("grid-template-columns", page)
            for candidate_id in FINALIST_IDS:
                self.assertIn(
                    results[candidate_id].summary["candidate_id"],
                    candidate_table["candidate_id"].tolist(),
                )
            for image_path in output.glob("*.png"):
                image = Image.open(image_path)
                if image.mode == "RGBA":
                    alpha = image.getchannel("A")
                    self.assertEqual(alpha.getextrema(), (255, 255))


if __name__ == "__main__":
    unittest.main()
