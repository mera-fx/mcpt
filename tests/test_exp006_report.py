from __future__ import annotations

from pathlib import Path
import unittest


class Exp006ReportTests(unittest.TestCase):
    def test_report_source_is_vertical(self) -> None:
        source = (
            Path(__file__)
            .resolve()
            .parents[1]
            / "exp006_report.py"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "EXP-005 control versus EXP-006 selection",
            source,
        )
        self.assertIn(
            "Selected candidate NQ total equity",
            source,
        )
        self.assertIn(
            "Selected candidate NQ drawdown",
            source,
        )
        self.assertNotIn(
            "grid-template-columns:repeat(3",
            source.replace(" ", ""),
        )

    def test_report_has_complete_grid_and_mcpt(self) -> None:
        source = (
            Path(__file__)
            .resolve()
            .parents[1]
            / "exp006_report.py"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "Complete ranked 27-candidate grid",
            source,
        )
        self.assertIn(
            "Selection-aware MCPT",
            source,
        )


if __name__ == "__main__":
    unittest.main()
