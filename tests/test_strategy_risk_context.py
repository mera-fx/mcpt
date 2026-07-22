from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from strategy_explanations import (
    family_explanation_html,
    strategy_explanation_html,
)
from upgrade_strategy_explanations import (
    upgrade_report_document,
    upgrade_reports,
)


class StrategyRiskContextTests(unittest.TestCase):
    def test_fixed_nq_experiments_explain_fixed_quantity_variable_risk(self) -> None:
        for experiment_id in (
            "EXP-005",
            "EXP-006",
            "EXP-007",
            "EXP-008",
            "EXP-009",
            "EXP-010",
        ):
            with self.subTest(experiment_id=experiment_id):
                rendered = strategy_explanation_html(experiment_id)
                self.assertIn("Position sizing and risk", rendered)
                self.assertIn(
                    "Fixed contract quantity; variable dollar risk.",
                    rendered,
                )
                self.assertIn(
                    "one NQ contract on every valid signal",
                    rendered,
                )
                self.assertIn(
                    "one MNQ contract",
                    rendered,
                )
                self.assertIn(
                    "80 × $20 + $15 costs = $1,615",
                    rendered,
                )

    def test_exp011_explains_all_three_sizing_methods(self) -> None:
        rendered = strategy_explanation_html("EXP-011")
        self.assertIn("Position sizing and risk", rendered)
        self.assertIn("Fixed one NQ always uses one NQ contract", rendered)
        self.assertIn("frozen $1,005 target", rendered)
        self.assertIn("0.5025 NQ", rendered)
        self.assertIn("= 4 contracts", rendered)
        self.assertIn("$2,156.99 initial risk per trade", rendered)

    def test_exp009_family_explanations_include_shared_risk_context(self) -> None:
        rendered = family_explanation_html("opening_drive_continuation")
        self.assertIn("Position sizing and risk", rendered)
        self.assertIn(
            "Fixed contract quantity; variable dollar risk.",
            rendered,
        )

    def test_existing_strategy_section_is_refreshed_idempotently(self) -> None:
        original = (
            "<!doctype html><html><head><style></style></head><body>"
            '<section id="strategy-rules" '
            'class="strategy-explanation-section">'
            "<h2>Old explanation</h2></section>"
            "</body></html>"
        )
        upgraded = upgrade_report_document(original, "EXP-010")
        second = upgrade_report_document(upgraded, "EXP-010")
        self.assertEqual(upgraded, second)
        self.assertNotIn("Old explanation", upgraded)
        self.assertIn("Position sizing and risk", upgraded)
        self.assertIn(
            "Fixed contract quantity; variable dollar risk.",
            upgraded,
        )

    def test_bulk_refresh_skips_unregistered_non_strategy_reports(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            strategy_report = root / "EXP-010-report.html"
            data_report = root / "EXP-015-report.html"
            original = (
                "<html><head><style></style></head><body>"
                '<section id="strategy-rules" '
                'class="strategy-explanation-section">'
                "<h2>Old explanation</h2></section>"
                "</body></html>"
            )
            strategy_report.write_text(original, encoding="utf-8")
            data_report.write_text(original, encoding="utf-8")

            changed = upgrade_reports(
                (
                    ("EXP-010", strategy_report),
                    ("EXP-015", data_report),
                ),
                write=True,
            )

            self.assertEqual(changed, (strategy_report,))
            self.assertIn(
                "Position sizing and risk",
                strategy_report.read_text(encoding="utf-8"),
            )
            self.assertEqual(
                data_report.read_text(encoding="utf-8"),
                original,
            )


if __name__ == "__main__":
    unittest.main()
