from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

import exp024_attribution as runner
from exp024_attribution_core import (
    ATTRIBUTION_CATEGORIES,
    CANDIDATE_IDS,
    CANDIDATE_RULES,
    SOURCE_IDS,
    aggregate_observed_ohlc,
    attribution_category,
    build_attribution,
    build_candidate_features,
    canonical_dataframe_sha256,
    compare_quantower_aggregation,
    final_classification,
    normalise_restricted_rows,
    select_frozen_mismatch_population,
    validate_candidate_rules,
    validate_feature_rows,
)


def _normalised(
    rows: list[dict[str, object]],
    *,
    source_id: str = "QUANTOWER_REFERENCE",
) -> pd.DataFrame:
    return normalise_restricted_rows(
        pd.DataFrame(rows),
        source_id=source_id,
        timestamp_column="timestamp",
        window="synthetic",
    )


def _row(
    timestamp: str,
    open_price: float,
    high: float,
    low: float,
    close: float,
) -> dict[str, object]:
    return {
        "timestamp": pd.Timestamp(timestamp),
        "open": open_price,
        "high": high,
        "low": low,
        "close": close,
    }


def _component_record(**overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "eligibility": True,
        "threshold_passes": True,
        "context_direction": 1,
        "first_cash_bar_confirmation": True,
        "entry_risk_positive": True,
    }
    record.update(overrides)
    return record


class Exp024AttributionCoreTests(unittest.TestCase):
    def test_candidate_rules_remain_frozen(self) -> None:
        validate_candidate_rules()
        self.assertEqual(tuple(CANDIDATE_RULES), CANDIDATE_IDS)
        self.assertEqual(CANDIDATE_RULES["gap_fade_0p50_1r"]["threshold"], 0.50)
        self.assertEqual(
            CANDIDATE_RULES["premarket_continuation_0p75_time"]["threshold"],
            0.75,
        )

    def test_locked_mismatch_selector_retains_exact_51_without_pnl(self) -> None:
        session_dates = pd.bdate_range(
            "2024-01-02",
            periods=51,
        ).strftime("%Y-%m-%d")
        candidates = (
            ["gap_fade_0p50_1r"] * 48
            + ["premarket_continuation_0p50_time"] * 2
            + ["premarket_continuation_0p75_time"]
        )
        rows: list[dict[str, object]] = []
        for index, (candidate_id, session_date) in enumerate(
            zip(candidates, session_dates)
        ):
            reference_only = index < 2 or index >= 48
            rows.append(
                {
                    "representation_id": "BACKWARD_ADJUSTED",
                    "candidate_id": candidate_id,
                    "session_date": session_date,
                    "eligible": index != 47,
                    "reference_trade_flag": reference_only,
                    "transfer_trade_flag": not reference_only,
                    "reference_direction": (
                        "long" if reference_only else ""
                    ),
                    "transfer_direction": (
                        "" if reference_only else "short"
                    ),
                    "trade_indicator_and_direction_match": False,
                    "reference_net_pnl_usd": 999_999.0,
                    "transfer_net_pnl_usd": -999_999.0,
                }
            )
        rows.append(
            {
                **rows[0],
                "representation_id": "UNADJUSTED",
                "trade_indicator_and_direction_match": True,
            }
        )
        selected = select_frozen_mismatch_population(
            pd.DataFrame(rows),
            require_production_count=True,
        )
        self.assertEqual(len(selected), 51)
        self.assertEqual(selected["session_date"].nunique(), 51)
        self.assertNotIn("reference_net_pnl_usd", selected.columns)
        self.assertNotIn("transfer_net_pnl_usd", selected.columns)

    def test_gap_features_rebuild_only_entry_decision(self) -> None:
        current = _normalised(
            [
                _row(
                    "2024-01-03T14:30:00Z",
                    111.0,
                    112.0,
                    108.0,
                    109.0,
                )
            ]
        )
        entry = normalise_restricted_rows(
            pd.DataFrame(
                {
                    "timestamp": [
                        pd.Timestamp("2024-01-03T14:35:00Z")
                    ],
                    "open": [110.0],
                }
            ),
            source_id="QUANTOWER_REFERENCE",
            timestamp_column="timestamp",
            window="entry_open_only",
        )
        previous = _normalised(
            [
                _row(
                    "2024-01-02T14:30:00Z",
                    101.0,
                    110.0,
                    100.0,
                    104.0,
                ),
                _row(
                    "2024-01-02T20:59:00Z",
                    104.0,
                    106.0,
                    103.0,
                    105.0,
                ),
            ]
        )
        record = build_candidate_features(
            source_id="QUANTOWER_REFERENCE",
            candidate_id="gap_fade_0p50_1r",
            session_date="2024-01-03",
            eligible=True,
            current_rows=current,
            entry_rows=entry,
            previous_cash_rows=previous,
        )
        self.assertAlmostEqual(record["normalized_gap"], 0.60)
        self.assertAlmostEqual(record["threshold_margin"], 0.10)
        self.assertEqual(record["gap_direction"], 1)
        self.assertEqual(record["fade_direction"], -1)
        self.assertTrue(record["first_cash_bar_confirmation"])
        self.assertAlmostEqual(record["entry_risk_points"], 2.0)
        self.assertTrue(record["entry_risk_positive"])
        self.assertTrue(record["setup_passes"])
        prohibited = {
            "stop_price",
            "target_price",
            "exit_price",
            "gross_pnl_usd",
            "net_pnl_usd",
            "equity",
            "drawdown",
        }
        self.assertTrue(prohibited.isdisjoint(record))

    def test_premarket_threshold_and_risk_are_rebuilt(self) -> None:
        current = _normalised(
            [
                _row(
                    "2024-01-03T13:00:00Z",
                    100.0,
                    101.0,
                    99.0,
                    100.0,
                ),
                _row(
                    "2024-01-03T14:29:00Z",
                    105.0,
                    110.0,
                    100.0,
                    106.0,
                ),
                _row(
                    "2024-01-03T14:30:00Z",
                    106.0,
                    109.0,
                    105.0,
                    108.0,
                ),
            ]
        )
        entry = normalise_restricted_rows(
            pd.DataFrame(
                {
                    "timestamp": [
                        pd.Timestamp("2024-01-03T14:35:00Z")
                    ],
                    "open": [107.0],
                }
            ),
            source_id="QUANTOWER_REFERENCE",
            timestamp_column="timestamp",
            window="entry_open_only",
        )
        record = build_candidate_features(
            source_id="QUANTOWER_REFERENCE",
            candidate_id="premarket_continuation_0p50_time",
            session_date="2024-01-03",
            eligible=True,
            current_rows=current,
            entry_rows=entry,
        )
        self.assertAlmostEqual(record["normalized_premarket_move"], 6 / 11)
        self.assertGreater(record["threshold_margin"], 0)
        self.assertEqual(record["premarket_direction"], 1)
        self.assertTrue(record["first_cash_bar_confirmation"])
        self.assertAlmostEqual(record["entry_risk_points"], 2.0)
        self.assertTrue(record["setup_passes"])

    def test_each_single_component_maps_to_exact_locked_category(self) -> None:
        expected = {
            "eligibility": "ELIGIBILITY_DIFFERENCE",
            "threshold_passes": (
                "NORMALIZED_CONTEXT_THRESHOLD_CROSSING"
            ),
            "context_direction": "CONTEXT_DIRECTION_DIFFERENCE",
            "first_cash_bar_confirmation": (
                "FIRST_CASH_BAR_CONFIRMATION_DIFFERENCE"
            ),
            "entry_risk_positive": "ENTRY_RISK_VALIDITY_DIFFERENCE",
        }
        reference = _component_record()
        for component, category in expected.items():
            changed = dict(reference)
            changed[component] = (
                -1
                if component == "context_direction"
                else not bool(reference[component])
            )
            differing, actual = attribution_category(
                reference,
                changed,
            )
            self.assertEqual(differing, (component,))
            self.assertEqual(actual, category)
            self.assertIn(actual, ATTRIBUTION_CATEGORIES)

    def test_multiple_and_unresolved_categories_are_deterministic(self) -> None:
        reference = _component_record()
        differing, category = attribution_category(
            reference,
            _component_record(
                threshold_passes=False,
                entry_risk_positive=False,
            ),
        )
        self.assertEqual(
            differing,
            ("threshold_passes", "entry_risk_positive"),
        )
        self.assertEqual(
            category,
            "MULTIPLE_DECISION_COMPONENT_DIFFERENCES",
        )
        self.assertEqual(
            attribution_category(reference, dict(reference)),
            ((), "UNRESOLVED_WITH_LOCKED_FEATURES"),
        )

    def test_attribution_checks_rebuilt_frozen_decisions(self) -> None:
        mismatch = pd.DataFrame(
            [
                {
                    "candidate_id": "gap_fade_0p50_1r",
                    "session_date": "2024-01-03",
                    "reference_trade_flag": True,
                    "transfer_trade_flag": False,
                    "reference_direction": "short",
                    "transfer_direction": "",
                }
            ]
        )
        common = {
            "candidate_id": "gap_fade_0p50_1r",
            "session_date": "2024-01-03",
            "eligibility": True,
            "context_direction": 1,
            "first_cash_bar_confirmation": True,
            "entry_risk_positive": True,
        }
        features = pd.DataFrame(
            [
                {
                    **common,
                    "source_id": "QUANTOWER_REFERENCE",
                    "threshold_passes": True,
                    "setup_passes": True,
                    "decision_direction": "short",
                },
                {
                    **common,
                    "source_id": "BACKWARD_ADJUSTED",
                    "threshold_passes": False,
                    "setup_passes": False,
                    "decision_direction": "short",
                },
            ]
        )
        result = build_attribution(mismatch, features)
        self.assertTrue(result.loc[0, "reference_rebuild_matches_frozen"])
        self.assertTrue(result.loc[0, "transfer_rebuild_matches_frozen"])
        self.assertEqual(
            result.loc[0, "primary_attribution_category"],
            "NORMALIZED_CONTEXT_THRESHOLD_CROSSING",
        )

    def test_feature_row_validator_requires_three_sources(self) -> None:
        mismatch = pd.DataFrame(
            [
                {
                    "candidate_id": "gap_fade_0p50_1r",
                    "session_date": "2024-01-03",
                }
            ]
        )
        frame = pd.DataFrame(
            [
                {
                    "source_id": source_id,
                    "candidate_id": "gap_fade_0p50_1r",
                    "session_date": "2024-01-03",
                }
                for source_id in SOURCE_IDS
            ]
        )
        validate_feature_rows(frame, mismatch)
        with self.assertRaisesRegex(ValueError, "three source rows"):
            validate_feature_rows(frame.iloc[:-1], mismatch)

    def test_observed_one_minute_aggregation_matches_frozen_five(self) -> None:
        one = _normalised(
            [
                _row(
                    f"2024-01-03T14:3{minute}:00Z",
                    100.0 + minute,
                    102.0 + minute,
                    99.0 + minute,
                    101.0 + minute,
                )
                for minute in range(5)
            ]
        )
        rebuilt = aggregate_observed_ohlc(one)
        self.assertEqual(rebuilt.loc[0, "observation_count"], 5)
        frozen = rebuilt.drop(columns=["observation_count"])
        comparison = compare_quantower_aggregation(one, frozen)
        self.assertTrue(comparison["all_ohlc_match"].all())
        frozen.loc[0, "close"] += 0.25
        comparison = compare_quantower_aggregation(one, frozen)
        self.assertFalse(comparison["all_ohlc_match"].all())

    def test_final_classification_uses_hard_checks_and_unresolved_count(
        self,
    ) -> None:
        self.assertEqual(
            final_classification({"a": True}, unresolved_count=0),
            "ATTRIBUTION_COMPLETE_WITH_IDENTIFIED_COMPONENTS",
        )
        self.assertEqual(
            final_classification({"a": True}, unresolved_count=1),
            "ATTRIBUTION_COMPLETE_WITH_UNRESOLVED_CASES",
        )
        self.assertEqual(
            final_classification({"a": False}, unresolved_count=0),
            "ATTRIBUTION_DIAGNOSTIC_NOT_QUALIFIED",
        )

    def test_canonical_hash_is_stable(self) -> None:
        frame = pd.DataFrame(
            [{"a": np.int64(1), "b": np.float64(2.5)}]
        )
        self.assertEqual(
            canonical_dataframe_sha256(frame),
            canonical_dataframe_sha256(frame.copy()),
        )


class Exp024ProtectedScannerTests(unittest.TestCase):
    def test_arrow_filter_and_projection_precede_materialization(self) -> None:
        import pyarrow as pa
        import pyarrow.parquet as pq

        timestamps = pd.to_datetime(
            [
                "2024-01-03T12:59:00Z",
                "2024-01-03T13:00:00Z",
                "2024-01-03T14:34:00Z",
                "2024-01-03T14:35:00Z",
                "2024-01-03T14:36:00Z",
            ],
            utc=True,
        )
        table = pa.Table.from_pydict(
            {
                "ts_event": pa.array(timestamps),
                "open": [1.0, 2.0, 3.0, 4.0, 5.0],
                "high": [9.0] * 5,
                "low": [0.0] * 5,
                "close": [8.0] * 5,
                "volume": [999] * 5,
                "prohibited_sentinel": ["secret"] * 5,
            }
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "restricted.parquet"
            pq.write_table(table, path)
            audit: list[dict[str, object]] = []
            result = runner.scan_parquet_intervals(
                path,
                timestamp_column="ts_event",
                columns=("ts_event", "open"),
                intervals=(
                    (
                        pd.Timestamp("2024-01-03T13:00:00Z"),
                        pd.Timestamp("2024-01-03T14:35:00Z"),
                    ),
                ),
                audit=audit,
                audit_label="synthetic",
            )
        self.assertEqual(result.columns.tolist(), ["ts_event", "open"])
        self.assertEqual(result["open"].tolist(), [2.0, 3.0])
        self.assertNotIn("volume", result.columns)
        self.assertNotIn("prohibited_sentinel", result.columns)
        self.assertTrue(audit[0]["row_filter_before_materialization"])
        self.assertTrue(audit[0]["column_projection_before_materialization"])

    def test_volume_projection_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "volume materialization"):
            runner.scan_parquet_intervals(
                Path("not-opened.parquet"),
                timestamp_column="ts_event",
                columns=("ts_event", "open", "volume"),
                intervals=(
                    (
                        pd.Timestamp("2024-01-03T13:00:00Z"),
                        pd.Timestamp("2024-01-03T14:35:00Z"),
                    ),
                ),
            )

    def test_window_loader_reads_entry_open_only_and_can_skip_it(
        self,
    ) -> None:
        import pyarrow as pa
        import pyarrow.parquet as pq

        timestamps = pd.to_datetime(
            [
                "2024-01-02T14:30:00Z",
                "2024-01-02T20:59:00Z",
                "2024-01-03T13:00:00Z",
                "2024-01-03T14:34:00Z",
                "2024-01-03T14:35:00Z",
            ],
            utc=True,
        )
        table = pa.Table.from_pydict(
            {
                "timestamp": pa.array(timestamps),
                "open": [100.0, 101.0, 102.0, 103.0, 104.0],
                "high": [101.0, 102.0, 103.0, 104.0, 999.0],
                "low": [99.0, 100.0, 101.0, 102.0, -999.0],
                "close": [100.5, 101.5, 102.5, 103.5, 999.0],
                "volume": [999] * 5,
            }
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "windows.parquet"
            pq.write_table(table, path)
            audit: list[dict[str, object]] = []
            windows = runner._load_source_windows(
                path=path,
                source_id="QUANTOWER_REFERENCE",
                timestamp_column="timestamp",
                mismatch_dates=["2024-01-03"],
                previous_dates=["2024-01-02"],
                metadata_columns=(),
                audit=audit,
            )
            no_entry = runner._load_source_windows(
                path=path,
                source_id="QUANTOWER_REFERENCE",
                timestamp_column="timestamp",
                mismatch_dates=["2024-01-03"],
                previous_dates=["2024-01-02"],
                metadata_columns=(),
                audit=[],
                include_entry=False,
            )
        self.assertEqual(
            set(windows),
            {"current", "entry", "previous"},
        )
        self.assertEqual(windows["entry"].columns.isin(["high"]).sum(), 0)
        self.assertEqual(windows["entry"]["open"].tolist(), [104.0])
        self.assertEqual(set(no_entry), {"current", "previous"})
        entry_audit = [
            item
            for item in audit
            if str(item["label"]).endswith("entry_open_only")
        ]
        self.assertEqual(len(entry_audit), 1)
        self.assertEqual(
            set(str(entry_audit[0]["projected_columns"]).split("|")),
            {"timestamp", "open"},
        )

    def test_interval_builder_rejects_protected_dates(self) -> None:
        with self.assertRaisesRegex(ValueError, "locked boundary"):
            runner._utc_intervals(
                ["2019-12-31"],
                start_time="08:00:00",
                end_time="09:35:00",
            )
        with self.assertRaisesRegex(ValueError, "locked boundary"):
            runner._utc_intervals(
                ["2026-01-02"],
                start_time="08:00:00",
                end_time="09:35:00",
            )

    def test_authorized_run_is_blocked_while_file_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            absent = Path(temporary) / "authorization_is_absent.py"
            with patch.object(runner, "AUTHORIZATION_PATH", absent):
                self.assertFalse(runner.AUTHORIZATION_PATH.exists())
                with self.assertRaisesRegex(RuntimeError, "not authorized"):
                    runner.load_authorization()

    def test_runner_has_permanent_output_and_partial_guards(self) -> None:
        source = Path(runner.__file__).read_text(encoding="utf-8")
        self.assertIn("for path in (OUTPUT_DIR, PARTIAL_OUTPUT_DIR)", source)
        self.assertIn("output already exists. Refusing to rerun.", source)
        self.assertIn(
            "os.replace(PARTIAL_OUTPUT_DIR, OUTPUT_DIR)",
            source,
        )
        self.assertNotEqual(runner.OUTPUT_DIR, runner.PARTIAL_OUTPUT_DIR)

    def test_implementation_scope_is_exact(self) -> None:
        self.assertEqual(
            set(runner.IMPLEMENTATION_PATHS),
            {
                "exp024_attribution.py",
                "exp024_attribution_core.py",
                "tests/test_exp024_attribution.py",
                "research/EXP-024_implementation_report.md",
            },
        )
        self.assertNotIn(
            "exp024_attribution_authorization.py",
            runner.IMPLEMENTATION_PATHS,
        )


if __name__ == "__main__":
    unittest.main()
