from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import pandas as pd
from PIL import Image

from exp012_engine import (
    locked_exp012_candidates,
    run_exp012_candidate,
)
from exp012_measurements import (
    add_pareto_context,
    calculate_exp012_candidate_measurements,
)
from exp012_report import build_exp012_report
from tests.exp012_test_data import make_exp012_arrays


def _report_inputs() -> tuple[pd.DataFrame, dict[str, object], object]:
    arrays = make_exp012_arrays(1)
    records = []
    results: dict[str, object] = {}
    for candidate in locked_exp012_candidates():
        nq = run_exp012_candidate(arrays, candidate, symbol="NQ")
        mnq = run_exp012_candidate(arrays, candidate, symbol="MNQ")
        zero = run_exp012_candidate(
            arrays,
            candidate,
            symbol="NQ",
            slippage_ticks_per_side=0,
        )
        two = run_exp012_candidate(
            arrays,
            candidate,
            symbol="NQ",
            slippage_ticks_per_side=2,
        )
        records.append(
            calculate_exp012_candidate_measurements(
                nq,
                mnq,
                nq_zero_tick_result=zero,
                nq_two_tick_result=two,
                included_session_count=1,
            )
        )
        results[candidate.candidate_id] = nq
    return (
        add_pareto_context(pd.DataFrame.from_records(records)),
        results,
        arrays,
    )


class Exp012ReportTests(unittest.TestCase):
    def test_report_is_plain_english_complete_and_measurement_first(
        self,
    ) -> None:
        table, results, arrays = _report_inputs()
        with tempfile.TemporaryDirectory() as temporary:
            report = build_exp012_report(
                candidate_table=table,
                nq_results=results,
                arrays=arrays,
                report_dir=Path(temporary),
                metadata={"automatic_winner": False},
            )
            text = report.read_text(encoding="utf-8")
            self.assertIn("What we tested and how", text)
            self.assertIn("How to read the fractions", text)
            self.assertIn("All 24 candidates", text)
            self.assertIn("does not declare a winner", text)
            self.assertIn("cash-session entries", text)
            for label in (
                "Gap continuation",
                "Gap fade",
                "Overnight momentum continuation",
                "Overnight inventory reversal",
                "Overnight range breakout",
                "Premarket momentum continuation",
            ):
                self.assertIn(label, text)
            self.assertNotIn("EXP-009", text)

    def test_report_charts_have_visible_white_outer_canvas(self) -> None:
        table, results, arrays = _report_inputs()
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            build_exp012_report(
                candidate_table=table,
                nq_results=results,
                arrays=arrays,
                report_dir=directory,
                metadata={},
            )
            chart = directory / "extended_context_distributions.png"
            with Image.open(chart).convert("RGBA") as image:
                for pixel in (
                    image.getpixel((0, 0)),
                    image.getpixel((image.width - 1, 0)),
                    image.getpixel((0, image.height - 1)),
                ):
                    self.assertEqual(pixel, (255, 255, 255, 255))

    def test_report_refuses_incomplete_candidate_table(self) -> None:
        table, results, arrays = _report_inputs()
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "24 candidates"):
                build_exp012_report(
                    candidate_table=table.iloc[:-1],
                    nq_results=results,
                    arrays=arrays,
                    report_dir=Path(temporary),
                    metadata={},
                )


if __name__ == "__main__":
    unittest.main()
