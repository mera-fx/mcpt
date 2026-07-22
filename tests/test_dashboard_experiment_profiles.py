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


    def test_data_result_parser_reads_exp015_assessment_shape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = (
                root
                / "results"
                / "EXP-015"
                / "source_qualification"
                / "catalog_result.json"
            )
            path.parent.mkdir(parents=True)
            path.write_text(
                json.dumps(
                    {
                        "result_phase": "CATALOG_ONLY",
                        "client_probe": {"version": "0.14.0"},
                        "assessment": {
                            "classification": "IDENTITY_UNRESOLVED",
                            "futures_catalog_rows": 69,
                            "nq_candidate_count": 1,
                            "mnq_candidate_count": 0,
                            "nq_identified": True,
                            "mnq_identified": False,
                            "contract_method_resolved": False,
                            "history_download_authorized": False,
                            "paper_trading_authorized": False,
                            "live_trading_authorized": False,
                        },
                    }
                ),
                encoding="utf-8",
            )
            artifact = ResearchArtifact(
                experiment_id="EXP-015",
                path=path,
                project_relative_path=path.relative_to(root).as_posix(),
                category="Structured record",
                label="Catalog result",
                extension=".json",
                size_bytes=path.stat().st_size,
                modified_utc="2026-07-22T00:00:00+00:00",
            )
            metrics, _ = load_data_source_measurements(
                root,
                "EXP-015",
                [artifact],
            )
            self.assertEqual(metrics["classification"], "IDENTITY_UNRESOLVED")
            self.assertEqual(metrics["futures_rows"], 69)
            self.assertEqual(metrics["nq_candidates"], 1)
            self.assertFalse(metrics["history_download_authorized"])

    def test_exp016_csv_augmentation_uses_minimums_and_sums(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result_root = (
                root
                / "results"
                / "EXP-016"
                / "source_qualification"
            )
            result_root.mkdir(parents=True)
            json_path = result_root / "audit_result.json"
            json_path.write_text(
                json.dumps(
                    {
                        "classification": "NOT_QUALIFIED",
                        "sample_windows": 2,
                        "research_boundary": {
                            "primary_source_qualified": False,
                            "strategy_run": False,
                        },
                    }
                ),
                encoding="utf-8",
            )
            import pandas as pd

            pd.DataFrame(
                [
                    {
                        "raw_rows": 100,
                        "duplicate_timestamp_count": 0,
                        "invalid_ohlc_rows": 0,
                        "negative_volume_rows": 0,
                        "nonfinite_ohlcv_rows": 0,
                    },
                    {
                        "raw_rows": 120,
                        "duplicate_timestamp_count": 0,
                        "invalid_ohlc_rows": 0,
                        "negative_volume_rows": 0,
                        "nonfinite_ohlcv_rows": 0,
                    },
                ]
            ).to_csv(
                result_root / "structural_measurements.csv",
                index=False,
            )
            pd.DataFrame(
                [
                    {
                        "expected_minute_completeness": 0.99,
                        "matched_timestamp_share": 0.98,
                        "close_within_one_tick_share": 0.97,
                    },
                    {
                        "expected_minute_completeness": 0.95,
                        "matched_timestamp_share": 0.96,
                        "close_within_one_tick_share": 0.94,
                    },
                ]
            ).to_csv(
                result_root / "cross_source_measurements.csv",
                index=False,
            )
            artifact = ResearchArtifact(
                experiment_id="EXP-016",
                path=json_path,
                project_relative_path=json_path.relative_to(root).as_posix(),
                category="Structured record",
                label="Audit result",
                extension=".json",
                size_bytes=json_path.stat().st_size,
                modified_utc="2026-07-22T00:00:00+00:00",
            )
            metrics, _ = load_data_source_measurements(
                root,
                "EXP-016",
                [artifact],
            )
            self.assertEqual(metrics["total_vendor_rows"], 220)
            self.assertEqual(metrics["structural_windows"], 2)
            self.assertAlmostEqual(
                metrics["minimum_expected_minute_completeness"],
                0.95,
            )
            self.assertAlmostEqual(
                metrics["minimum_close_within_one_tick_share"],
                0.94,
            )
if __name__ == "__main__":
    unittest.main()
