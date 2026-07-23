from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from report_monochrome_theme import (
    REPORT_SHELL_CSS,
    REPORT_SHELL_JS,
    THEME_MARKER,
    discover_report_files,
    theme_report_document,
    theme_report_files,
)


class ReportShellV4Tests(unittest.TestCase):
    def test_upgrade_is_idempotent(self) -> None:
        original = (
            "<html><head><style>:root{--accent:#60a5fa}</style></head>"
            "<body><main><h1>Report</h1><h2>Results</h2>"
            "<h3>Detail</h3><table><tr><th>A</th><th>B</th>"
            "<th>C</th><th>D</th><th>E</th></tr>"
            "<tr><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td>"
            "</tr></table></main></body></html>"
        )
        first = theme_report_document(original)
        second = theme_report_document(first)
        self.assertEqual(first, second)
        self.assertEqual(first.count(THEME_MARKER), 3)

    def test_requested_menu_behaviour_is_present(self) -> None:
        for expected in (
            "mcpt-menu-parent",
            "mcpt-menu-children",
            "IntersectionObserver",
            "openGroup(g)",
            "setActive(active)",
            "scrollIntoView",
        ):
            self.assertIn(expected, REPORT_SHELL_JS)
        self.assertNotIn('textContent="+"', REPORT_SHELL_JS)
        self.assertNotIn('textContent="−"', REPORT_SHELL_JS)

    def test_compare_all_writes_new_tab_document(self) -> None:
        for expected in (
            'window.open("","_blank")',
            "pop.document.write(doc)",
            "pop.document.close()",
            "new Blob([doc]",
            "Compare all",
        ):
            self.assertIn(expected, REPORT_SHELL_JS)

    def test_three_records_use_matrix_and_larger_sets_can_group(self) -> None:
        self.assertIn("if(rows<=3)", REPORT_SHELL_JS)
        self.assertIn("matrix(heads,records)", REPORT_SHELL_JS)
        self.assertIn("groupIndex(heads,records)", REPORT_SHELL_JS)
        self.assertIn("rs.length<=3", REPORT_SHELL_JS)

    def test_bronze_labels_and_compact_stats_are_locked(self) -> None:
        for expected in (
            ".mcpt-matrix-table th:first-child",
            ".mcpt-record-grid dt",
            ".stat span",
            ".strategy-rule-card h3",
            "color:var(--accent)!important",
            ".grid.mcpt-stat-grid",
            "grid-template-columns:repeat(3",
        ):
            self.assertIn(expected, REPORT_SHELL_CSS)

    def test_discovery_skips_dashboard(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            report = project / "reports" / "EXP-010" / "report.html"
            dashboard = project / "reports" / "research_dashboard" / "report.html"
            report.parent.mkdir(parents=True)
            dashboard.parent.mkdir(parents=True)
            report.write_text("<html><head></head><body>R</body></html>", encoding="utf-8")
            dashboard.write_text("<html><head></head><body>D</body></html>", encoding="utf-8")

            self.assertEqual(discover_report_files(project), (report,))
            self.assertEqual(theme_report_files(project, write=True), (report,))
            self.assertIn(THEME_MARKER, report.read_text(encoding="utf-8"))
            self.assertNotIn(THEME_MARKER, dashboard.read_text(encoding="utf-8"))

    def test_menu_and_matrix_cleanup(self) -> None:
        self.assertIn(
            "--silver:#c8c5bf !important;",
            REPORT_SHELL_CSS,
        )
        self.assertIn(
            ".mcpt-menu-children{display:block;",
            REPORT_SHELL_CSS,
        )
        self.assertNotIn(
            ".mcpt-menu-group.mcpt-open>"
            ".mcpt-menu-children",
            REPORT_SHELL_CSS,
        )
        self.assertIn(
            "function identityIndex(heads,records)",
            REPORT_SHELL_JS,
        )
        self.assertIn(
            'mh.textContent=""',
            REPORT_SHELL_JS,
        )
        self.assertNotIn(
            'mh.textContent="Metric"',
            REPORT_SHELL_JS,
        )
        self.assertIn(
            "if(identity>=0)hidden.add(identity)",
            REPORT_SHELL_JS,
        )
        self.assertIn(
            "g.append(p);"
            "if(children.length)g.append(box);",
            REPORT_SHELL_JS,
        )


if __name__ == "__main__":
    unittest.main()
