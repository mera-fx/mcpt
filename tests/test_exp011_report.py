from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from exp011_bootstrap import paired_sizing_bootstrap
from exp011_measurements import build_exp011_measurement_table
from exp011_report import build_exp011_report
from tests.exp009_test_data import make_exp009_arrays
from tests.exp011_test_data import make_calibration, make_sized_results


class Exp011ReportTests(unittest.TestCase):
    def _fixture(self):
        results = make_sized_results()
        bootstrap = []
        for signal_id in (
            "opening_drive_0p5_time",
            "opening_drive_0p5_1p5r",
        ):
            fixed = results[(signal_id, "fixed_one_nq")]
            bootstrap.append(
                paired_sizing_bootstrap(
                    fixed,
                    results[
                        (signal_id, "fractional_nq_equal_risk")
                    ],
                    resamples=50,
                )
            )
            bootstrap.append(
                paired_sizing_bootstrap(
                    fixed,
                    results[
                        (signal_id, "integer_mnq_equal_risk")
                    ],
                    comparison_scale_to_nq=10.0,
                    resamples=50,
                )
            )
        decision = {
            "signal_context": {
                "exp010_selection_aware_mcpt_p_value": 0.025974
            }
        }
        return results, bootstrap, decision

    def test_report_explains_strategy_fraction_and_measurement(self) -> None:
        results, bootstrap, decision = self._fixture()
        arrays = make_exp009_arrays(5)
        with tempfile.TemporaryDirectory() as directory:
            path = build_exp011_report(
                decision=decision,
                calibration=make_calibration(),
                results=results,
                measurement_table=build_exp011_measurement_table(
                    results
                ),
                bootstrap=bootstrap,
                nq_arrays=arrays,
                output_dir=Path(directory),
            )
            text = path.read_text(encoding="utf-8")
        self.assertIn("How the strategy works", text)
        self.assertIn("Worked sizing example", text)
        self.assertIn("contract quantity", text)
        self.assertIn("all methods and both exit variants", text)
        self.assertIn("does not declare a sizing winner", text)
        self.assertIn("does not confirm the signal edge", text)
        self.assertIn('class="status-good">LOCKED', text)
        self.assertNotIn('class="status-good">$', text)

    def test_report_creates_locked_visuals(self) -> None:
        results, bootstrap, decision = self._fixture()
        expected = {
            "sizing_equity_vs_nq.png",
            "sizing_drawdowns.png",
            "initial_risk_distribution.png",
            "contract_count_distribution.png",
            "annual_sizing_comparison.png",
            "monthly_sizing_heatmap.png",
            "report.html",
        }
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            build_exp011_report(
                decision=decision,
                calibration=make_calibration(),
                results=results,
                measurement_table=build_exp011_measurement_table(
                    results
                ),
                bootstrap=bootstrap,
                nq_arrays=make_exp009_arrays(5),
                output_dir=output,
            )
            self.assertTrue(
                expected.issubset(
                    {path.name for path in output.iterdir()}
                )
            )


if __name__ == "__main__":
    unittest.main()
