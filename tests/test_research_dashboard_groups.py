from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from build_research_dashboard import (
    _artifact_groups_html,
    artifact_group_name,
)
from research_dashboard_library import ResearchArtifact


def artifact(
    *,
    category: str,
    relative_path: str,
    label: str,
) -> ResearchArtifact:
    path = Path(relative_path).resolve()
    return ResearchArtifact(
        experiment_id="EXP-005",
        path=path,
        project_relative_path=relative_path,
        category=category,
        label=label,
        extension=path.suffix,
        size_bytes=100,
        modified_utc="2026-07-14T00:00:00+00:00",
    )


class ResearchDashboardGroupTests(unittest.TestCase):
    def test_visual_reports_use_main_group(self) -> None:
        item = artifact(
            category="Visual report",
            relative_path=(
                "reports/EXP-005-research-lab/report.html"
            ),
            label="Research lab",
        )
        self.assertEqual(
            artifact_group_name(item),
            "Main reports",
        )

    def test_data_audits_use_quality_group(self) -> None:
        item = artifact(
            category="Data-quality record",
            relative_path=(
                "results/EXP-005/confirmation_data/import_audit.json"
            ),
            label="Import audit",
        )
        self.assertEqual(
            artifact_group_name(item),
            "Data quality and audits",
        )

    def test_trade_ledgers_use_performance_group(self) -> None:
        item = artifact(
            category="Trade ledger",
            relative_path=(
                "results/EXP-005/full_validation/nq_trades.csv"
            ),
            label="NQ trades",
        )
        self.assertEqual(
            artifact_group_name(item),
            "Performance results",
        )

    def test_groups_are_collapsed_by_default(self) -> None:
        items = [
            artifact(
                category="Visual report",
                relative_path=(
                    "reports/EXP-005-research-lab/report.html"
                ),
                label="Research lab",
            ),
            artifact(
                category="Decision record",
                relative_path=(
                    "results/EXP-005/review/review_decision.json"
                ),
                label="Review decision",
            ),
        ]

        with tempfile.TemporaryDirectory() as temp:
            markup = _artifact_groups_html(
                items,
                dashboard_directory=Path(temp),
                previews={},
            )

        self.assertIn(
            '<details class="artifact-group"',
            markup,
        )
        self.assertNotIn(
            '<details class="artifact-group" open',
            markup,
        )
        self.assertIn("Main reports", markup)
        self.assertIn("Decisions and lifecycle", markup)


if __name__ == "__main__":
    unittest.main()
