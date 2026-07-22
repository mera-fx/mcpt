from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from dashboard_experiment_profiles import (
    load_data_source_measurements,
    populated_strategy_metric_count,
    research_type_for,
)
from research_dashboard_library import ResearchArtifact


class DashboardExperimentProfileTests(unittest.TestCase):
    def test_research_types_are_separate(self) -> None:
        self.assertEqual(research_type_for("EXP-014"), "strategy")
        self.assertEqual(research_type_for("EXP-015"), "data_source")
        self.assertEqual(research_type_for("EXP-018"), "data_source")

    def test_strategy_metric_count_is_honest(self) -> None:
        self.assertEqual(
            populated_strategy_metric_count(
                {
                    "profit_factor": 1.2,
                    "net_profit_usd": 1000,
                    "win_rate_percent": float("nan"),
                }
            ),
            2,
        )

    def test_data_result_parser_reads_exp018_shape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = (
                root
                / "results"
                / "EXP-018"
                / "source_qualification"
                / "audit_result.json"
            )
            path.parent.mkdir(parents=True)
            path.write_text(
                json.dumps(
                    {
                        "classification": "REPEATABILITY_PENDING",
                        "initial_windows_measured": 6,
                        "repeatability_windows_measured": 0,
                        "total_estimated_cost_usd": 0.283447,
                        "observed": {
                            "minimum_regular_trade_minute_coverage": 1.0,
                            "minimum_extended_trade_minute_coverage": 0.99918699,
                            "identity_mismatch_rows": 0,
                        },
                        "boundaries": {
                            "exchange_accuracy_claim": False,
                            "strategy_run": False,
                        },
                    }
                ),
                encoding="utf-8",
            )
            artifact = ResearchArtifact(
                experiment_id="EXP-018",
                path=path,
                project_relative_path=path.relative_to(root).as_posix(),
                category="Structured record",
                label="Audit result",
                extension=".json",
                size_bytes=path.stat().st_size,
                modified_utc="2026-07-22T00:00:00+00:00",
            )
            metrics, source = load_data_source_measurements(
                root,
                "EXP-018",
                [artifact],
            )
            self.assertEqual(metrics["classification"], "REPEATABILITY_PENDING")
            self.assertEqual(metrics["initial_windows_measured"], 6)
            self.assertAlmostEqual(
                metrics["extended_trade_minute_coverage"],
                0.99918699,
            )
            self.assertEqual(
                source,
                "results/EXP-018/source_qualification/audit_result.json",
            )


if __name__ == "__main__":
    unittest.main()
