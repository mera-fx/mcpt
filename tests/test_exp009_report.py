from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

import pandas as pd

from exp009_engine import locked_exp009_candidates
from exp009_report import build_exp009_report
from tests.exp009_test_data import make_exp009_arrays
from tests.test_exp009_measurements import _result


def _report_inputs() -> tuple[pd.DataFrame, dict[str, object]]:
    records = []
    results: dict[str, object] = {}
    for index, candidate in enumerate(locked_exp009_candidates()):
        base = _result(
            "orb_pullback_long_1r",
            symbol="NQ",
            pnl=[100.0 + index, -50.0, 80.0],
        )
        candidate_result = replace(
            base,
            candidate=candidate,
            summary={
                **base.summary,
                "candidate_id": candidate.candidate_id,
                "family_id": candidate.family_id,
            },
            trades=base.trades.assign(
                candidate_id=candidate.candidate_id,
                family_id=candidate.family_id,
            ),
        )
        results[candidate.candidate_id] = candidate_result
        records.append(
            {
                **candidate_result.summary,
                "candidate_id": candidate.candidate_id,
                "family_id": candidate.family_id,
                "two_tick_net_profit_usd": 90.0,
                "mnq_profit_factor": 1.05,
                "profitable_year_fraction": 0.75,
                "average_holding_minutes": 35.0,
                "pareto_nondominated": index < 3,
                "reliability_flag_count": 0,
                "mnq_divergence": False,
                "longest_drawdown_duration_trades": 8,
                "top_5_trade_profit_contribution": 0.6,
                "best_year_profit_contribution": 0.5,
            }
        )
    return pd.DataFrame(records), results


class Exp009ReportTests(unittest.TestCase):
    def test_report_contains_context_all_families_and_no_winner(self) -> None:
        candidate_table, results = _report_inputs()
        with tempfile.TemporaryDirectory() as temporary:
            report = build_exp009_report(
                candidate_table=candidate_table,
                nq_results=results,
                arrays=make_exp009_arrays(3),
                report_dir=Path(temporary),
                metadata={"automatic_winner": False},
            )
            text = report.read_text(encoding="utf-8")
            self.assertIn("What we tested and how", text)
            self.assertIn("All 24 candidates", text)
            self.assertIn("What happened", text)
            self.assertIn("does not declare a winner", text)
            self.assertIn("normalized NQ benchmark", text)
            for label in (
                "ORB pullback continuation",
                "Failed ORB reversal",
                "VWAP mean reversion",
                "VWAP trend pullback",
                "Compression breakout",
                "Opening drive continuation",
            ):
                self.assertIn(label, text)
            self.assertTrue(
                (Path(temporary) / "orb_pullback_continuation_monthly_heatmap.png").is_file()
            )
            self.assertTrue(
                (Path(temporary) / "opening_drive_continuation_trade_behaviour.png").is_file()
            )

    def test_positive_numbers_are_neutral_and_status_words_green(self) -> None:
        candidate_table, results = _report_inputs()
        with tempfile.TemporaryDirectory() as temporary:
            report = build_exp009_report(
                candidate_table=candidate_table,
                nq_results=results,
                arrays=make_exp009_arrays(3),
                report_dir=Path(temporary),
                metadata={"automatic_winner": False},
            )
            text = report.read_text(encoding="utf-8")
            self.assertIn(".status-good", text)
            self.assertIn(".adverse", text)
            self.assertIn("font-weight:inherit", text)
            self.assertNotIn("value-positive", text)

    def test_report_refuses_incomplete_candidate_table(self) -> None:
        candidate_table, results = _report_inputs()
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(ValueError):
                build_exp009_report(
                    candidate_table=candidate_table.iloc[:-1],
                    nq_results=results,
                    arrays=make_exp009_arrays(3),
                    report_dir=Path(temporary),
                    metadata={},
                )


if __name__ == "__main__":
    unittest.main()
