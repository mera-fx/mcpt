from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd

from exp023_preregistration import (
    FINALIST_IDS,
    validate_exp023_preregistration,
)
from exp023_transfer import (
    CORE_OUTPUT_NAMES,
    IMPLEMENTATION_PATHS,
    LOCKED_PREREGISTRATION_COMMIT,
    PREREGISTRATION_PATHS,
    REQUIRED_OUTPUT_NAMES,
    atomic_write_json,
    load_permitted_ohlcv,
)
from exp023_transfer_core import (
    CANDIDATE_SPECS,
    REPRESENTATION_IDS,
    SESSION_ALIGNMENT_FIELDS,
    SOURCE_COLUMNS,
    TRADE_ALIGNMENT_FIELDS,
    TRANSFER_METRIC_FIELDS,
    aggregate_observed_five_minute,
    build_reference_decisions,
    build_trade_alignment,
    candidate_transfer_metrics,
    canonical_dataframe_sha256,
    final_classification,
    normalise_source_frame,
    replay_representation,
    representation_sensitivity,
    safe_correlation,
    validate_candidate_specs,
    validate_reference_session_dates,
)


PROJECT_DIR = Path(__file__).resolve().parents[1]
TEST_DATES = ("2024-01-02", "2024-01-03")


def _timestamp(session_date: str, session_minute: int) -> pd.Timestamp:
    if session_minute < 360:
        local_date = pd.Timestamp(session_date) - pd.Timedelta(days=1)
        clock_minute = 18 * 60 + session_minute
    else:
        local_date = pd.Timestamp(session_date)
        clock_minute = session_minute - 360
    local = pd.Timestamp(
        (
            f"{local_date.date().isoformat()} "
            f"{clock_minute // 60:02d}:{clock_minute % 60:02d}:00"
        ),
        tz="America/New_York",
    )
    return local.tz_convert("UTC")


def make_observed_frame(
    dates: tuple[str, ...] = TEST_DATES,
    *,
    gap_signal_on_last: bool = False,
    premarket_signal_on_last: bool = False,
    stop_and_target_same_minute: bool = False,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    session_minutes = list(range(840, 1320, 5))
    for session_date in dates:
        for session_minute in session_minutes:
            opening = 100.0
            closing = 100.0
            high = 101.0
            low = 99.0
            if session_date == dates[-1]:
                if premarket_signal_on_last and session_minute == 840:
                    opening = 99.0
                    closing = 99.0
                    high = 100.0
                    low = 98.0
                if premarket_signal_on_last and session_minute == 925:
                    opening = 101.0
                    closing = 102.0
                    high = 102.0
                    low = 101.0
                if gap_signal_on_last and session_minute == 930:
                    opening = 102.0
                    closing = 101.5
                    high = 103.0
                    low = 101.0
                elif premarket_signal_on_last and session_minute == 930:
                    opening = 102.0
                    closing = 102.5
                    high = 103.0
                    low = 101.0
                if session_minute == 935:
                    opening = 101.5
                    closing = 100.0
                    high = (
                        104.0
                        if stop_and_target_same_minute
                        else 102.0
                    )
                    low = 99.0
                if session_minute == 1315:
                    opening = 100.5
                    closing = 100.25
                    high = 101.0
                    low = 100.0
            rows.append(
                {
                    "ts_event": _timestamp(
                        session_date,
                        session_minute,
                    ),
                    "open": opening,
                    "high": high,
                    "low": low,
                    "close": closing,
                    "volume": 10,
                    "trading_date": session_date,
                }
            )
    return pd.DataFrame(rows).sort_values(
        "ts_event",
        kind="stable",
    ).reset_index(drop=True)


def make_reference_ledgers() -> dict[str, pd.DataFrame]:
    return {
        candidate_id: pd.DataFrame(
            [
                {
                    "candidate_id": candidate_id,
                    "session_date": TEST_DATES[-1],
                    "direction": "short",
                    "entry_time": "09:35",
                    "gross_pnl_usd": 30.0,
                    "net_pnl_usd": 15.0,
                }
            ]
        )
        for candidate_id in FINALIST_IDS
    }


def make_perfect_alignment(
    *,
    pnl_values: tuple[float, float] = (-20.0, -10.0),
    transfer_values: tuple[float, float] | None = None,
    candidate_id: str = "gap_fade_0p50_1r",
    representation_id: str = "BACKWARD_ADJUSTED",
) -> pd.DataFrame:
    transfer_values = (
        pnl_values
        if transfer_values is None
        else transfer_values
    )
    rows = []
    for index, (reference_pnl, transfer_pnl) in enumerate(
        zip(pnl_values, transfer_values)
    ):
        rows.append(
            {
                "representation_id": representation_id,
                "candidate_id": candidate_id,
                "session_date": f"2024-01-{index + 2:02d}",
                "eligible": True,
                "reference_trade_flag": True,
                "transfer_trade_flag": True,
                "reference_direction": "long",
                "transfer_direction": "long",
                "trade_indicator_and_direction_match": True,
                "common_trade": True,
                "reference_entry_timestamp_utc": (
                    f"2024-01-{index + 2:02d}T14:35:00+00:00"
                ),
                "transfer_entry_timestamp_utc": (
                    f"2024-01-{index + 2:02d}T14:35:00+00:00"
                ),
                "entry_timestamp_match": True,
                "reference_gross_pnl_usd": reference_pnl,
                "transfer_gross_pnl_usd": transfer_pnl,
                "reference_net_pnl_usd": reference_pnl - 15.0,
                "transfer_net_pnl_usd": transfer_pnl - 15.0,
                "gross_pnl_sign_match": (
                    np.sign(reference_pnl) == np.sign(transfer_pnl)
                ),
            }
        )
    return pd.DataFrame(rows, columns=TRADE_ALIGNMENT_FIELDS)


class Exp023TransferCoreTests(unittest.TestCase):
    def test_01_preregistration_and_candidate_lock_remain_valid(
        self,
    ) -> None:
        validate_exp023_preregistration()
        validate_candidate_specs()
        self.assertEqual(
            tuple(item.candidate_id for item in CANDIDATE_SPECS),
            FINALIST_IDS,
        )

    def test_02_representation_roles_are_exact(self) -> None:
        self.assertEqual(
            REPRESENTATION_IDS,
            ("BACKWARD_ADJUSTED", "UNADJUSTED"),
        )

    def test_03_reference_axis_is_sorted_unique_and_bounded(
        self,
    ) -> None:
        self.assertEqual(
            validate_reference_session_dates(TEST_DATES),
            TEST_DATES,
        )
        with self.assertRaisesRegex(ValueError, "sorted and unique"):
            validate_reference_session_dates(
                ("2024-01-03", "2024-01-02")
            )

    def test_04_source_normalization_uses_new_york_session_minutes(
        self,
    ) -> None:
        frame = normalise_source_frame(
            make_observed_frame(),
            representation_id="BACKWARD_ADJUSTED",
        )
        first = frame.iloc[0]
        self.assertEqual(first["session_date"], TEST_DATES[0])
        self.assertEqual(int(first["session_minute"]), 840)
        self.assertEqual(
            tuple(SOURCE_COLUMNS),
            (
                "ts_event",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "trading_date",
            ),
        )

    def test_05_out_of_window_source_row_is_rejected(self) -> None:
        frame = make_observed_frame()
        frame.loc[0, "ts_event"] = pd.Timestamp(
            "2026-01-02T14:00:00+00:00"
        )
        with self.assertRaisesRegex(ValueError, "out-of-window"):
            normalise_source_frame(
                frame,
                representation_id="BACKWARD_ADJUSTED",
            )

    def test_06_observed_five_minute_bars_are_not_filled(
        self,
    ) -> None:
        source = normalise_source_frame(
            make_observed_frame(),
            representation_id="BACKWARD_ADJUSTED",
        )
        aggregated = aggregate_observed_five_minute(source)
        self.assertTrue(aggregated["observation_count"].eq(1).all())
        self.assertEqual(len(aggregated), 96 * len(TEST_DATES))

    def test_07_all_reference_sessions_are_accounted_for(
        self,
    ) -> None:
        alignment, _ = replay_representation(
            make_observed_frame(),
            representation_id="BACKWARD_ADJUSTED",
            reference_session_dates=TEST_DATES,
        )
        self.assertEqual(
            tuple(alignment.columns),
            SESSION_ALIGNMENT_FIELDS,
        )
        self.assertEqual(len(alignment), 3 * len(TEST_DATES))
        self.assertEqual(
            alignment.groupby("candidate_id")["session_date"]
            .nunique()
            .to_dict(),
            {candidate_id: 2 for candidate_id in FINALIST_IDS},
        )

    def test_08_first_gap_session_is_ineligible_without_predecessor(
        self,
    ) -> None:
        alignment, _ = replay_representation(
            make_observed_frame(),
            representation_id="BACKWARD_ADJUSTED",
            reference_session_dates=TEST_DATES,
        )
        first = alignment.loc[
            (alignment["candidate_id"] == "gap_fade_0p50_1r")
            & (alignment["session_date"] == TEST_DATES[0])
        ].iloc[0]
        self.assertFalse(bool(first["eligible"]))
        self.assertIn(
            "PREVIOUS_REFERENCE_SESSION_UNAVAILABLE",
            first["ineligibility_reason"],
        )

    def test_09_gap_fade_rule_and_one_r_target_are_exact(self) -> None:
        alignment, trades = replay_representation(
            make_observed_frame(gap_signal_on_last=True),
            representation_id="BACKWARD_ADJUSTED",
            reference_session_dates=TEST_DATES,
        )
        decision = alignment.loc[
            (alignment["candidate_id"] == "gap_fade_0p50_1r")
            & (alignment["session_date"] == TEST_DATES[-1])
        ].iloc[0]
        trade = trades.loc[
            trades["candidate_id"] == "gap_fade_0p50_1r"
        ].iloc[0]
        self.assertTrue(bool(decision["trade_flag"]))
        self.assertEqual(trade["direction"], "short")
        self.assertEqual(float(trade["stop_price"]), 103.0)
        self.assertEqual(float(trade["target_price"]), 100.0)
        self.assertEqual(trade["exit_reason"], "profit_target")

    def test_10_premarket_rule_uses_all_eighteen_bins(self) -> None:
        alignment, trades = replay_representation(
            make_observed_frame(premarket_signal_on_last=True),
            representation_id="BACKWARD_ADJUSTED",
            reference_session_dates=TEST_DATES,
        )
        decisions = alignment.loc[
            alignment["candidate_id"].str.startswith(
                "premarket_continuation"
            )
            & (alignment["session_date"] == TEST_DATES[-1])
        ]
        self.assertTrue(decisions["eligible"].all())
        self.assertEqual(
            set(trades["candidate_id"]),
            {
                "premarket_continuation_0p50_time",
                "premarket_continuation_0p75_time",
            },
        )

    def test_11_same_minute_stop_and_target_uses_stop_first(
        self,
    ) -> None:
        _, trades = replay_representation(
            make_observed_frame(
                gap_signal_on_last=True,
                stop_and_target_same_minute=True,
            ),
            representation_id="BACKWARD_ADJUSTED",
            reference_session_dates=TEST_DATES,
        )
        trade = trades.loc[
            trades["candidate_id"] == "gap_fade_0p50_1r"
        ].iloc[0]
        self.assertEqual(trade["exit_reason"], "protective_stop")
        self.assertEqual(float(trade["exit_price"]), 103.0)

    def test_12_missing_entry_minute_is_logged_not_repaired(
        self,
    ) -> None:
        frame = make_observed_frame()
        entry_timestamp = _timestamp(
            TEST_DATES[-1],
            935,
        )
        frame = frame.loc[frame["ts_event"] != entry_timestamp]
        alignment, _ = replay_representation(
            frame,
            representation_id="BACKWARD_ADJUSTED",
            reference_session_dates=TEST_DATES,
        )
        current = alignment.loc[
            alignment["session_date"] == TEST_DATES[-1]
        ]
        self.assertFalse(current["eligible"].any())
        self.assertTrue(
            current["ineligibility_reason"].str.contains(
                "ENTRY_MINUTE_0935_MISSING"
            ).all()
        )

    def test_13_reference_decisions_rebuild_utc_entry_timestamp(
        self,
    ) -> None:
        decisions = build_reference_decisions(
            make_reference_ledgers(),
            reference_session_dates=TEST_DATES,
        )
        traded = decisions.loc[
            decisions["reference_trade_flag"]
        ]
        self.assertEqual(len(traded), 3)
        self.assertTrue(
            traded["reference_entry_timestamp_utc"].str.endswith(
                "+00:00"
            ).all()
        )

    def test_14_trade_alignment_keys_are_unique(self) -> None:
        session_alignment, trades = replay_representation(
            make_observed_frame(gap_signal_on_last=True),
            representation_id="BACKWARD_ADJUSTED",
            reference_session_dates=TEST_DATES,
        )
        reference = build_reference_decisions(
            make_reference_ledgers(),
            reference_session_dates=TEST_DATES,
        )
        alignment = build_trade_alignment(
            session_alignment,
            trades,
            reference,
        )
        self.assertEqual(
            tuple(alignment.columns),
            TRADE_ALIGNMENT_FIELDS,
        )
        self.assertFalse(
            alignment.duplicated(
                ["representation_id", "candidate_id", "session_date"]
            ).any()
        )

    def test_15_profitability_is_not_a_transfer_gate(self) -> None:
        metrics = candidate_transfer_metrics(
            make_perfect_alignment()
        )
        self.assertEqual(
            tuple(metrics.columns),
            TRANSFER_METRIC_FIELDS,
        )
        self.assertTrue(
            bool(metrics.iloc[0]["all_transfer_gates_pass"])
        )
        self.assertLess(
            float(metrics.iloc[0]["transfer_net_profit_usd"]),
            0.0,
        )

    def test_16_zero_variance_correlation_fails_gate(self) -> None:
        metrics = candidate_transfer_metrics(
            make_perfect_alignment(
                pnl_values=(-10.0, -10.0),
                transfer_values=(-10.0, -10.0),
            )
        )
        self.assertTrue(
            np.isnan(
                metrics.iloc[0][
                    "common_trade_gross_pnl_correlation"
                ]
            )
        )
        self.assertFalse(
            bool(metrics.iloc[0]["gate_gross_pnl_correlation"])
        )
        self.assertTrue(np.isnan(safe_correlation([1, 1], [1, 1])))

    def test_17_representation_sensitivity_keeps_candidates_separate(
        self,
    ) -> None:
        pieces = []
        for candidate_id in FINALIST_IDS:
            for representation_id in REPRESENTATION_IDS:
                pieces.append(
                    make_perfect_alignment(
                        candidate_id=candidate_id,
                        representation_id=representation_id,
                    )
                )
        sensitivity = representation_sensitivity(
            pd.concat(pieces, ignore_index=True)
        )
        self.assertEqual(
            tuple(sensitivity["candidate_id"]),
            FINALIST_IDS,
        )
        self.assertTrue(
            sensitivity[
                "trade_indicator_and_direction_agreement"
            ].eq(1.0).all()
        )

    def test_18_classification_requires_all_three_primary_passes(
        self,
    ) -> None:
        metrics = pd.concat(
            [
                candidate_transfer_metrics(
                    make_perfect_alignment(
                        candidate_id=candidate_id,
                    )
                )
                for candidate_id in FINALIST_IDS
            ],
            ignore_index=True,
        )
        checks = {f"check_{index}": True for index in range(20)}
        self.assertEqual(
            final_classification(metrics, checks),
            (
                "QUALIFIED_FOR_SEPARATE_FIXED_RULE_"
                "HISTORY_VALIDATION"
            ),
        )
        checks["check_0"] = False
        self.assertEqual(
            final_classification(metrics, checks),
            "TRANSFER_DIAGNOSTIC_NOT_QUALIFIED",
        )

    def test_19_canonical_frame_hash_is_deterministic(self) -> None:
        frame = make_perfect_alignment()
        first = canonical_dataframe_sha256(frame)
        second = canonical_dataframe_sha256(frame.copy())
        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)

    def test_20_output_field_sets_are_unique(self) -> None:
        for fields in (
            SESSION_ALIGNMENT_FIELDS,
            TRADE_ALIGNMENT_FIELDS,
            TRANSFER_METRIC_FIELDS,
            CORE_OUTPUT_NAMES,
        ):
            self.assertTrue(fields)
            self.assertEqual(len(fields), len(set(fields)))


class Exp023TransferBoundaryTests(unittest.TestCase):
    def test_21_preregistration_commit_is_locked(self) -> None:
        self.assertEqual(
            LOCKED_PREREGISTRATION_COMMIT,
            "66ba6a46f31cc8715447179c19caf2f4c1a1e8be",
        )
        self.assertEqual(
            PREREGISTRATION_PATHS,
            (
                "exp023_preregistration.py",
                "research/EXP-023_preregistration.md",
                "tests/test_exp023_preregistration.py",
            ),
        )

    def test_22_implementation_scope_is_exact(self) -> None:
        self.assertEqual(
            IMPLEMENTATION_PATHS,
            (
                "exp023_transfer.py",
                "exp023_transfer_core.py",
                "tests/test_exp023_transfer.py",
                "research/EXP-023_implementation_report.md",
            ),
        )

    def test_23_runner_requires_separate_authorization(self) -> None:
        source = (PROJECT_DIR / "exp023_transfer.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("exp023_transfer_authorization", source)
        self.assertIn("maximum_transfer_runs", source)
        self.assertIn("locked_implementation_commit", source)

    def test_24_runner_uses_predicate_before_pandas_conversion(
        self,
    ) -> None:
        source = (PROJECT_DIR / "exp023_transfer.py").read_text(
            encoding="utf-8"
        )
        scanner = source.index("source.scanner(")
        conversion = source.index("table.to_pandas(")
        self.assertLess(scanner, conversion)
        self.assertIn("filter=predicate", source)
        self.assertNotIn("pd.read_parquet(", source)

    def test_25_runner_has_no_api_or_network_client(self) -> None:
        source = (PROJECT_DIR / "exp023_transfer.py").read_text(
            encoding="utf-8"
        )
        for token in (
            "import databento",
            "requests.",
            "urllib.",
            "socket.",
            "paper_trade(",
            "live_trade(",
            "walk_forward(",
            "bootstrap(",
        ):
            with self.subTest(token=token):
                self.assertNotIn(token, source)

    def test_26_runner_builds_required_vertical_report_assets(
        self,
    ) -> None:
        required = {
            "transfer_summary.json",
            "candidate_transfer_metrics.csv",
            "session_alignment.csv",
            "trade_alignment.csv",
            "representation_sensitivity.csv",
            "ineligible_sessions.csv",
            "output_hashes.json",
            "report.md",
            "report.html",
        }
        self.assertTrue(required.issubset(set(REQUIRED_OUTPUT_NAMES)))
        source = (PROJECT_DIR / "exp023_transfer.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("max-width: 980px", source)
        self.assertIn('facecolor="white"', source)

    def test_27_filtered_arrow_loader_accepts_synthetic_parquet(
        self,
    ) -> None:
        frame = make_observed_frame()
        frame["trading_date"] = pd.to_datetime(
            frame["trading_date"]
        ).dt.date
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.parquet"
            frame.to_parquet(path, index=False)
            loaded = load_permitted_ohlcv(
                path,
                representation_id="BACKWARD_ADJUSTED",
            )
        self.assertEqual(len(loaded), len(frame))
        self.assertTrue(
            loaded["session_date"].isin(TEST_DATES).all()
        )

    def test_28_json_writer_replaces_nonfinite_measurements(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "safe.json"
            atomic_write_json(
                path,
                {"nan": np.nan, "infinity": np.inf},
            )
            value = json.loads(path.read_text(encoding="utf-8"))
        self.assertIsNone(value["nan"])
        self.assertIsNone(value["infinity"])


if __name__ == "__main__":
    unittest.main()
