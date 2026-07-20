from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from strategy_explanations import (
    FAMILY_EXPLANATIONS,
    FAMILY_REPORT_HEADINGS,
    STRATEGY_EXPLANATIONS,
    family_explanation_html,
    strategy_explanation_html,
)
from upgrade_strategy_explanations import (
    discover_experiment_reports,
    upgrade_report_document,
    upgrade_reports,
)


class StrategyExplanationTests(unittest.TestCase):
    def test_catalog_covers_every_current_experiment(self) -> None:
        expected = {f"EXP-{number:03d}" for number in range(1, 11)}
        self.assertEqual(set(STRATEGY_EXPLANATIONS), expected)

    def test_every_explanation_has_rules_parameters_and_example(self) -> None:
        for experiment_id, explanation in STRATEGY_EXPLANATIONS.items():
            with self.subTest(experiment_id=experiment_id):
                self.assertGreaterEqual(len(explanation.rules), 4)
                self.assertGreaterEqual(len(explanation.parameters), 2)
                self.assertTrue(explanation.idea)
                self.assertTrue(explanation.example)
                self.assertTrue(explanation.distinction)
                rendered = strategy_explanation_html(experiment_id)
                self.assertIn("How the strategy works", rendered)
                self.assertIn("What the parameters mean", rendered)
                self.assertIn("Worked example", rendered)
                self.assertIn("Important distinction", rendered)

    def test_opening_drive_fraction_is_explained_numerically(self) -> None:
        rendered = strategy_explanation_html("EXP-010")
        self.assertIn("60 / 100 = 0.60", rendered)
        self.assertIn("passes 0.50 but fails 0.75", rendered)
        self.assertIn("does not mean NQ rose 50%", rendered)

    def test_exp009_has_all_six_family_explanations(self) -> None:
        self.assertEqual(len(FAMILY_EXPLANATIONS), 6)
        for family_id in FAMILY_EXPLANATIONS:
            with self.subTest(family_id=family_id):
                rendered = family_explanation_html(family_id)
                self.assertIn("Worked example", rendered)
                self.assertIn("Important distinction", rendered)
                self.assertIn(f'family-rules-{family_id}', rendered)

    def test_unknown_experiment_has_visible_fallback(self) -> None:
        rendered = strategy_explanation_html("EXP-999")
        self.assertIn("has not yet been registered", rendered)
        self.assertIn('id="strategy-rules"', rendered)


class ExistingReportUpgradeTests(unittest.TestCase):
    def test_upgrade_is_idempotent_and_adds_navigation(self) -> None:
        original = """
        <!doctype html><html><head><style>body { color:white; }</style></head>
        <body><nav><a href="#overview">Overview</a></nav>
        <section id="overview"><h1>Report</h1></section></body></html>
        """
        upgraded = upgrade_report_document(original, "EXP-010")
        second = upgrade_report_document(upgraded, "EXP-010")
        self.assertEqual(upgraded, second)
        self.assertIn('href="#strategy-rules"', upgraded)
        self.assertIn('id="strategy-rules"', upgraded)
        self.assertIn("60 / 100 = 0.60", upgraded)

    def test_exp009_upgrade_adds_family_details(self) -> None:
        original = (
            "<html><head><style></style></head><body>"
            "<section><h1>EXP-009</h1></section>"
            + "".join(
                f"<section><h2>{FAMILY_REPORT_HEADINGS[family_id]}</h2></section>"
                for family_id in FAMILY_EXPLANATIONS
            )
            + "</body></html>"
        )
        upgraded = upgrade_report_document(original, "EXP-009")
        for family_id in FAMILY_EXPLANATIONS:
            self.assertIn(f'id="family-rules-{family_id}"', upgraded)

    def test_preflight_mode_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = root / "EXP-001-research-lab" / "report.html"
            report.parent.mkdir(parents=True)
            report.write_text(
                "<html><head><style></style></head><body><h1>Report</h1></body></html>",
                encoding="utf-8",
            )
            reports = discover_experiment_reports(root)
            before = report.read_text(encoding="utf-8")
            changed = upgrade_reports(reports, write=False)
            after = report.read_text(encoding="utf-8")

        self.assertEqual(changed, (report,))
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
