from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from analytics_evidence_registry import (
    AnalyticsKind,
    AnalyticsSeriesSpec,
    BenchmarkSchema,
    EquitySchema,
    ExperimentEvidenceSpec,
    TradeSchema,
)
from analytics_provenance import (
    assert_evidence_unchanged,
    build_evidence_inventory,
)


class AnalyticsProvenanceTests(unittest.TestCase):
    def _fixture(
        self,
        root: Path,
    ) -> tuple[
        dict[str, ExperimentEvidenceSpec],
        Path,
    ]:
        result_dir = root / "results" / "EXP-999"
        result_dir.mkdir(parents=True)
        trades = result_dir / "trades.csv"
        trades.write_text("net_pnl_usd\n10\n", encoding="utf-8")
        (result_dir / "equity.csv").write_text(
            "equity_usd\n100010\n",
            encoding="utf-8",
        )
        (result_dir / "decision.json").write_text(
            '{"decision":"LOCKED"}\n',
            encoding="utf-8",
        )
        series = AnalyticsSeriesSpec(
            series_id="EXP-999:test:NQ",
            experiment_id="EXP-999",
            display_name="Test",
            market="NQ",
            variant_id="test",
            candidate_id=None,
            family_id=None,
            trades_path=Path("results/EXP-999/trades.csv"),
            equity_path=Path("results/EXP-999/equity.csv"),
            trade_schema=TradeSchema.FUTURES_ORB,
            equity_schema=EquitySchema.SESSION_EQUITY,
            benchmark_schema=BenchmarkSchema.NONE,
        )
        registry = {
            "EXP-999": ExperimentEvidenceSpec(
                experiment_id="EXP-999",
                experiment_name="Test experiment",
                analytics_kind=AnalyticsKind.STRATEGY,
                series=(series,),
            )
        }
        return registry, trades

    def test_inventory_hashes_core_and_robustness_evidence(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            registry, _ = self._fixture(root)
            inventory = build_evidence_inventory(root, registry)

        self.assertEqual(len(inventory.records), 3)
        roles = {
            record.path: set(record.roles)
            for record in inventory.records
        }
        self.assertEqual(
            roles["results/EXP-999/trades.csv"],
            {"trade_ledger"},
        )
        self.assertEqual(
            roles["results/EXP-999/equity.csv"],
            {"equity_series"},
        )
        self.assertEqual(
            roles["results/EXP-999/decision.json"],
            {"existing_robustness"},
        )
        self.assertEqual(len(inventory.digest), 64)

    def test_changed_frozen_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            registry, trades = self._fixture(root)
            before = build_evidence_inventory(root, registry)
            trades.write_text(
                "net_pnl_usd\n11\n",
                encoding="utf-8",
            )
            after = build_evidence_inventory(root, registry)
            with self.assertRaisesRegex(
                RuntimeError,
                "changed",
            ):
                assert_evidence_unchanged(before, after)


if __name__ == "__main__":
    unittest.main()
