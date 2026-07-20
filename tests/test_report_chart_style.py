from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np

from report_chart_style import save_report_figure


PROJECT_DIR = Path(__file__).resolve().parents[1]
CURRENT_REPORT_GENERATORS = (
    "exp005_research_report.py",
    "exp006_report.py",
    "exp007_report.py",
    "exp008_report.py",
    "exp009_report.py",
    "exp010_report.py",
    "exp011_report.py",
    "strategy_measurement_report.py",
    "strategy_comparison_dashboard.py",
)


class ReportChartStyleTests(unittest.TestCase):
    def test_saved_chart_has_opaque_white_outer_canvas(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "chart.png"
            figure, axis = plt.subplots(figsize=(3, 2))
            figure.patch.set_facecolor("#0b1220")
            axis.plot([0, 1], [0, 1])
            axis.set_title("Readable title")

            save_report_figure(figure, output, dpi=80)
            plt.close(figure)

            image = mpimg.imread(output)
            corner = image[0, 0]
            np.testing.assert_allclose(corner[:3], [1.0, 1.0, 1.0])
            if len(corner) == 4:
                self.assertEqual(float(corner[3]), 1.0)

    def test_every_current_report_generator_uses_shared_saver(self) -> None:
        for filename in CURRENT_REPORT_GENERATORS:
            with self.subTest(filename=filename):
                source = (PROJECT_DIR / filename).read_text(encoding="utf-8")
                self.assertIn("save_report_figure", source)
                self.assertNotIn(".savefig(", source)


if __name__ == "__main__":
    unittest.main()
