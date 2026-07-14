from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import tempfile
import unittest

from build_research_dashboard import (
    build_lifecycle_only_record,
)
from research_dashboard_library import (
    artifact_label,
    build_artifact_preview,
    choose_primary_report,
    classify_artifact,
    detect_experiment_id,
    discover_artifacts,
    load_experiment_metrics,
)


@dataclass(frozen=True)
class FakeLifecycle:
    experiment_id: str = "EXP-099"
    experiment_name: str = "Test"
    hypothesis: str = "Test hypothesis."
    stage: str = "REVIEW"
    stage_reason: str = "Reviewing."
    next_action: str = "Review next."
    market_name: str = "Test market"
    timeframe: str = "5 minutes"
    strategy_name: str = "test_strategy"
    preregistration_file: Path | None = None


class ResearchDashboardLibraryTests(
    unittest.TestCase
):
    def test_lifecycle_only_record_compatibility(
        self,
    ) -> None:
        record = build_lifecycle_only_record(
            FakeLifecycle()
        )
        self.assertFalse(record["configured"])
        self.assertFalse(record["has_results"])
        self.assertEqual(
            record["status"],
            "REVIEW",
        )

    def test_experiment_detection_is_exact(
        self,
    ) -> None:
        identifiers = [
            "EXP-003",
            "EXP-005",
        ]
        self.assertEqual(
            detect_experiment_id(
                Path(
                    "results/EXP-005/review/"
                    "review_decision.json"
                ),
                identifiers,
            ),
            "EXP-005",
        )
        self.assertIsNone(
            detect_experiment_id(
                Path("results/general_summary.csv"),
                identifiers,
            )
        )

    def test_artifact_classification(
        self,
    ) -> None:
        self.assertEqual(
            classify_artifact(
                Path(
                    "reports/EXP-005-full-validation/"
                    "report.html"
                )
            ),
            "Visual report",
        )
        self.assertEqual(
            classify_artifact(
                Path(
                    "results/EXP-005/review/"
                    "review_decision.json"
                )
            ),
            "Review record",
        )
        self.assertEqual(
            classify_artifact(
                Path(
                    "results/EXP-005/full_validation/"
                    "nq_trades.csv"
                )
            ),
            "Trade ledger",
        )

    def test_primary_report_prefers_research_lab(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            first = (
                project
                / "reports"
                / "EXP-005-full-validation"
                / "report.html"
            )
            second = (
                project
                / "reports"
                / "EXP-005-research-lab"
                / "report.html"
            )
            first.parent.mkdir(parents=True)
            second.parent.mkdir(parents=True)
            first.write_text("full", encoding="utf-8")
            second.write_text("lab", encoding="utf-8")

            artifacts = discover_artifacts(
                project,
                ["EXP-005"],
            )
            chosen = choose_primary_report(
                artifacts,
                "EXP-005",
            )
            self.assertIsNotNone(chosen)
            self.assertEqual(
                chosen.path,
                second.resolve(),
            )

    def test_discovery_scans_only_research_roots(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            report = (
                project
                / "reports"
                / "EXP-005-full-validation"
                / "report.html"
            )
            result = (
                project
                / "results"
                / "EXP-005"
                / "review"
                / "review_decision.json"
            )
            raw = (
                project
                / "data"
                / "EXP-005"
                / "raw.csv"
            )
            report.parent.mkdir(parents=True)
            result.parent.mkdir(parents=True)
            raw.parent.mkdir(parents=True)
            report.write_text("report", encoding="utf-8")
            result.write_text("{}", encoding="utf-8")
            raw.write_text("price\n1\n", encoding="utf-8")

            artifacts = discover_artifacts(
                project,
                ["EXP-005"],
            )
            locations = {
                item.project_relative_path
                for item in artifacts
            }
            self.assertIn(
                "reports/EXP-005-full-validation/report.html",
                locations,
            )
            self.assertIn(
                "results/EXP-005/review/review_decision.json",
                locations,
            )
            self.assertNotIn(
                "data/EXP-005/raw.csv",
                locations,
            )

    def test_exp005_metrics_explain_drawdown_percent(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            result_path = (
                project
                / "research"
                / "EXP-005_full_validation_result.json"
            )
            result_path.parent.mkdir(parents=True)
            result_path.write_text(
                json.dumps(
                    {
                        "results": {
                            "NQ": {
                                "trade_profit_factor": 1.18,
                                "net_profit_usd": 116715.0,
                                "win_rate_percent": 43.37,
                                "maximum_drawdown_usd": -36175.0,
                                "completed_trades": 724,
                            }
                        },
                        "mcpt": {
                            "p_value": 0.037962
                        },
                        "evaluation": {
                            "decision": "PASS_TO_REVIEW"
                        },
                    }
                ),
                encoding="utf-8",
            )

            metrics = load_experiment_metrics(
                project,
                "EXP-005",
            )
            self.assertEqual(
                metrics["profit_factor"],
                1.18,
            )
            self.assertIn(
                "starting-capital",
                metrics[
                    "drawdown_percent_note"
                ],
            )

    def test_json_preview_is_generated(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            source = (
                project
                / "results"
                / "EXP-005"
                / "review"
                / "review_decision.json"
            )
            dashboard = (
                project
                / "reports"
                / "research_dashboard"
            )
            source.parent.mkdir(parents=True)
            source.write_text(
                '{"decision": "PASS"}',
                encoding="utf-8",
            )
            artifact = discover_artifacts(
                project,
                ["EXP-005"],
            )[0]

            preview = build_artifact_preview(
                artifact,
                dashboard,
            )
            self.assertIsNotNone(preview)
            self.assertTrue(preview.exists())
            self.assertIn(
                "PASS",
                preview.read_text(
                    encoding="utf-8"
                ),
            )


if __name__ == "__main__":
    unittest.main()
