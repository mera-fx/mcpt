from __future__ import annotations

import csv
from datetime import date
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest

import pandas as pd

from exp025_exact_contract_core import (
    CANDIDATE_ID,
    DBN_FIXED_PRICE_SCALE,
    EXPECTED_POPULATION_ROWS,
    OUTPUT_SCHEMAS,
    QUANTOWER_REQUIRED_COLUMNS,
    REQUIRED_OUTPUT_NAMES,
    UNRESOLVED_CATEGORY,
    Exp025DataError,
    aggregate_observed_five_minute,
    archive_digest,
    attach_previous_session_dates,
    build_archive_index,
    canonical_gap_fade_decision,
    canonical_object_sha256,
    compare_one_minute_sources,
    dbn_fixed_price_to_float,
    decision_vectors_match,
    final_classification,
    independent_gap_fade_decision,
    local_window_label,
    normalise_contract_symbol,
    normalise_source_rows,
    parse_timestamp,
    price_to_ticks,
    required_output_set,
    safe_relative_path,
    select_unresolved_population,
    session_classification,
    stream_quantower_csv,
    stream_restricted_dbn_records,
    strict_bool,
    validate_output_schemas,
    validate_population_contracts_in_archive,
    validate_quantower_export_manifest,
)


PROJECT_DIR = Path(__file__).resolve().parents[1]
RUNNER_PATH = PROJECT_DIR / "exp025_exact_contract_diagnostic.py"


def make_population_inputs(count: int = 43):
    dates = pd.date_range("2020-01-22", periods=count, freq="7D")
    mismatch_rows = []
    roll_rows = []
    contracts = ("NQH20", "NQM20", "NQU20", "NQZ20")
    for index, timestamp in enumerate(dates):
        session_date = timestamp.date().isoformat()
        symbol = contracts[index % len(contracts)]
        mismatch_rows.append(
            {
                "candidate_id": CANDIDATE_ID,
                "session_date": session_date,
                "frozen_reference_trade_flag": False,
                "frozen_transfer_trade_flag": True,
                "frozen_reference_direction": "",
                "frozen_transfer_direction": "short" if index % 2 == 0 else "long",
                "reference_rebuild_matches_frozen": False,
                "transfer_rebuild_matches_frozen": True,
                "primary_attribution_category": UNRESOLVED_CATEGORY,
            }
        )
        roll_rows.append(
            {
                "candidate_id": CANDIDATE_ID,
                "session_date": session_date,
                "backward_adjusted_source_contract": symbol,
                "backward_adjusted_instrument_id": 10000 + index % 4,
                "unadjusted_source_contract": symbol,
                "unadjusted_instrument_id": 10000 + index % 4,
            }
        )
    return pd.DataFrame(mismatch_rows), pd.DataFrame(roll_rows)


def make_session_calendar():
    dates = pd.bdate_range(
        "2019-12-20",
        "2021-01-31",
    )
    return pd.DataFrame(
        {"session_date": dates.strftime("%Y-%m-%d")}
    )


def make_archive_manifest():
    completed = []
    month_codes = ("H", "M", "U", "Z")
    sequence = 0
    for year in range(10, 27):
        for month_code in month_codes:
            if sequence >= 66:
                break
            sequence += 1
            symbol = f"NQ{month_code}{year:02d}"
            completed.append(
                {
                    "sequence": sequence,
                    "canonical_symbol": symbol,
                    "relative_path": f"raw/{symbol}.dbn.zst",
                    "size_bytes": 1000 + sequence,
                    "sha256": f"{sequence:064x}"[-64:],
                }
            )
    return {
        "experiment_id": "EXP-019",
        "status": "COMPLETE",
        "completed": completed,
    }


def make_quantower_manifest(population: pd.DataFrame):
    files = []
    for index, row in enumerate(population.itertuples(index=False)):
        files.append(
            {
                "session_date": str(row.session_date),
                "previous_session_date": str(
                    row.previous_session_date
                ),
                "explicit_contract_symbol": str(row.exact_contract_symbol),
                "relative_path": f"raw/{row.session_date}_{row.exact_contract_symbol}.csv",
                "size_bytes": 1000 + index,
                "sha256": f"{index + 100:064x}"[-64:],
                "row_count": 3,
                "timestamp_timezone": "America/New_York",
                "pretrimmed_to_allowed_windows": True,
            }
        )
    return {
        "schema_version": 1,
        "experiment_id": "EXP-025",
        "status": "COMPLETE",
        "source": "Lucid/Rithmic via Quantower History Exporter",
        "resolution": "1 minute",
        "research_timezone": "America/New_York",
        "required_columns": QUANTOWER_REQUIRED_COLUMNS,
        "files": files,
    }


def make_short_rows():
    return [
        {
            "timestamp": "2020-01-21 09:30:00",
            "open": 100.0,
            "high": 102.0,
            "low": 98.0,
            "close": 100.0,
            "volume": 100,
            "explicit_contract_symbol": "NQH20",
        },
        {
            "timestamp": "2020-01-22 09:30:00",
            "open": 103.0,
            "high": 104.0,
            "low": 101.0,
            "close": 102.0,
            "volume": 100,
            "explicit_contract_symbol": "NQH20",
        },
        {
            "timestamp": "2020-01-22 09:35:00",
            "open": 102.5,
            "high": 103.0,
            "low": 102.0,
            "close": 102.75,
            "volume": 100,
            "explicit_contract_symbol": "NQH20",
        },
    ]


def make_long_rows():
    return [
        {
            "timestamp": "2020-01-21 09:30:00",
            "open": 100.0,
            "high": 102.0,
            "low": 98.0,
            "close": 100.0,
            "volume": 100,
            "explicit_contract_symbol": "NQH20",
        },
        {
            "timestamp": "2020-01-22 09:30:00",
            "open": 97.0,
            "high": 99.0,
            "low": 96.0,
            "close": 98.0,
            "volume": 100,
            "explicit_contract_symbol": "NQH20",
        },
        {
            "timestamp": "2020-01-22 09:35:00",
            "open": 97.5,
            "high": 98.0,
            "low": 97.0,
            "close": 97.75,
            "volume": 100,
            "explicit_contract_symbol": "NQH20",
        },
    ]


def normalised(rows=None):
    return normalise_source_rows(
        make_short_rows() if rows is None else rows,
        source_id="QUANTOWER_EXACT",
        session_date="2020-01-22",
        previous_session_date="2020-01-21",
        exact_contract_symbol="NQH20",
        timestamp_timezone="America/New_York",
    )


class Exp025ExactContractTests(unittest.TestCase):
    def test_01_canonical_hash_is_deterministic(self):
        left = canonical_object_sha256({"b": 2, "a": 1})
        right = canonical_object_sha256({"a": 1, "b": 2})
        self.assertEqual(left, right)

    def test_02_strict_bool_accepts_locked_encodings(self):
        self.assertTrue(strict_bool("true", name="x"))
        self.assertFalse(strict_bool("FALSE", name="x"))
        self.assertTrue(strict_bool(1, name="x"))
        self.assertFalse(strict_bool(0, name="x"))

    def test_03_strict_bool_rejects_unknown_value(self):
        with self.assertRaisesRegex(Exp025DataError, "non-boolean"):
            strict_bool("yes", name="x")

    def test_04_exact_contract_symbol_is_locked(self):
        self.assertEqual(normalise_contract_symbol(" nqh20 "), "NQH20")
        for value in ("NQ.v.0", "ESM20", "NQ20", "NQF20"):
            with self.assertRaises(Exp025DataError):
                normalise_contract_symbol(value)

    def test_05_relative_paths_reject_escape(self):
        self.assertEqual(safe_relative_path("raw/NQH20.csv"), "raw/NQH20.csv")
        for value in ("../x.csv", "/tmp/x.csv", "", "."):
            with self.assertRaises(Exp025DataError):
                safe_relative_path(value)

    def test_06_selects_all_43_locked_rows(self):
        mismatch, roll = make_population_inputs()
        selected = select_unresolved_population(mismatch, roll)
        self.assertEqual(len(selected), EXPECTED_POPULATION_ROWS)
        self.assertEqual(selected["session_date"].nunique(), 43)
        self.assertTrue(selected["frozen_transfer_trade_flag"].all())
        self.assertFalse(selected["frozen_reference_trade_flag"].any())

    def test_07_population_rejects_42_rows(self):
        mismatch, roll = make_population_inputs(42)
        with self.assertRaisesRegex(Exp025DataError, "requires 43"):
            select_unresolved_population(mismatch, roll)

    def test_08_population_rejects_changed_relationship(self):
        mismatch, roll = make_population_inputs()
        mismatch.loc[0, "frozen_reference_trade_flag"] = True
        with self.assertRaisesRegex(Exp025DataError, "non-trades"):
            select_unresolved_population(mismatch, roll)

    def test_09_population_rejects_contract_disagreement(self):
        mismatch, roll = make_population_inputs()
        roll.loc[0, "unadjusted_source_contract"] = "NQM20"
        with self.assertRaisesRegex(Exp025DataError, "disagree on exact contract"):
            select_unresolved_population(mismatch, roll)

    def test_09a_previous_session_uses_frozen_calendar(self):
        population = pd.DataFrame(
            {
                "candidate_id": [CANDIDATE_ID],
                "session_date": ["2020-01-06"],
            }
        )
        calendar = pd.DataFrame(
            {
                "session_date": [
                    "2020-01-02",
                    "2020-01-03",
                    "2020-01-06",
                ]
            }
        )
        attached = attach_previous_session_dates(
            population,
            calendar,
        )
        self.assertEqual(
            attached.iloc[0]["previous_session_date"],
            "2020-01-03",
        )

    def test_09b_previous_session_requires_calendar_membership(self):
        population = pd.DataFrame(
            {
                "candidate_id": [CANDIDATE_ID],
                "session_date": ["2020-01-07"],
            }
        )
        calendar = pd.DataFrame(
            {
                "session_date": [
                    "2020-01-03",
                    "2020-01-06",
                ]
            }
        )
        with self.assertRaisesRegex(
            Exp025DataError,
            "absent from the frozen session calendar",
        ):
            attach_previous_session_dates(
                population,
                calendar,
            )

    def test_10_archive_digest_is_sequence_ordered(self):
        manifest = make_archive_manifest()
        forward = archive_digest(manifest["completed"])
        reverse = archive_digest(list(reversed(manifest["completed"])))
        self.assertEqual(forward, reverse)

    def test_11_archive_index_accepts_66_contracts(self):
        index = build_archive_index(make_archive_manifest())
        self.assertEqual(len(index), 66)
        self.assertIn("NQH10", index)

    def test_12_archive_index_rejects_duplicate_contract(self):
        manifest = make_archive_manifest()
        manifest["completed"][1]["canonical_symbol"] = manifest["completed"][0][
            "canonical_symbol"
        ]
        with self.assertRaisesRegex(Exp025DataError, "contract is duplicated"):
            build_archive_index(manifest)

    def test_13_population_contracts_must_exist_in_archive(self):
        mismatch, roll = make_population_inputs()
        population = attach_previous_session_dates(
            select_unresolved_population(mismatch, roll),
            make_session_calendar(),
        )
        with self.assertRaisesRegex(Exp025DataError, "absent from archive"):
            validate_population_contracts_in_archive(population, {})

    def test_14_quantower_manifest_accepts_exact_43_session_set(self):
        mismatch, roll = make_population_inputs()
        population = attach_previous_session_dates(
            select_unresolved_population(mismatch, roll),
            make_session_calendar(),
        )
        frame = validate_quantower_export_manifest(
            make_quantower_manifest(population), population
        )
        self.assertEqual(len(frame), 43)
        self.assertEqual(frame["session_date"].nunique(), 43)

    def test_15_quantower_manifest_rejects_missing_session(self):
        mismatch, roll = make_population_inputs()
        population = attach_previous_session_dates(
            select_unresolved_population(mismatch, roll),
            make_session_calendar(),
        )
        manifest = make_quantower_manifest(population)
        manifest["files"].pop()
        with self.assertRaisesRegex(Exp025DataError, "requires 43"):
            validate_quantower_export_manifest(manifest, population)

    def test_16_quantower_manifest_rejects_contract_change(self):
        mismatch, roll = make_population_inputs()
        population = attach_previous_session_dates(
            select_unresolved_population(mismatch, roll),
            make_session_calendar(),
        )
        manifest = make_quantower_manifest(population)
        manifest["files"][0]["explicit_contract_symbol"] = "NQZ26"
        with self.assertRaisesRegex(Exp025DataError, "contract mismatch"):
            validate_quantower_export_manifest(manifest, population)

    def test_16a_quantower_manifest_rejects_wrong_previous_session(
        self,
    ):
        mismatch, roll = make_population_inputs()
        population = attach_previous_session_dates(
            select_unresolved_population(mismatch, roll),
            make_session_calendar(),
        )
        manifest = make_quantower_manifest(population)
        manifest["files"][0]["previous_session_date"] = "2019-01-01"
        with self.assertRaisesRegex(
            Exp025DataError,
            "previous-session mismatch",
        ):
            validate_quantower_export_manifest(
                manifest,
                population,
            )

    def test_17_quantower_manifest_rejects_path_escape(self):
        mismatch, roll = make_population_inputs()
        population = attach_previous_session_dates(
            select_unresolved_population(mismatch, roll),
            make_session_calendar(),
        )
        manifest = make_quantower_manifest(population)
        manifest["files"][0]["relative_path"] = "../outside.csv"
        with self.assertRaisesRegex(Exp025DataError, "Unsafe relative path"):
            validate_quantower_export_manifest(manifest, population)

    def test_18_timestamp_parsing_respects_declared_timezone(self):
        local = parse_timestamp(
            "2020-01-22 09:30:00", declared_timezone="America/New_York"
        )
        aware = parse_timestamp(
            "2020-01-22T14:30:00Z", declared_timezone="America/New_York"
        )
        self.assertEqual(local, aware)

    def test_19_locked_window_labels_are_exact(self):
        prior = parse_timestamp(
            "2020-01-21 09:30:00", declared_timezone="America/New_York"
        )
        current = parse_timestamp(
            "2020-01-22 09:35:00", declared_timezone="America/New_York"
        )
        outside = parse_timestamp(
            "2020-01-22 09:36:00", declared_timezone="America/New_York"
        )
        self.assertEqual(
            local_window_label(
                prior,
                session_date="2020-01-22",
                previous_session_date="2020-01-21",
            ),
            "PREVIOUS_CASH",
        )
        self.assertEqual(
            local_window_label(
                current,
                session_date="2020-01-22",
                previous_session_date="2020-01-21",
            ),
            "CURRENT_ENTRY_WINDOW",
        )
        self.assertIsNone(
            local_window_label(
                outside,
                session_date="2020-01-22",
                previous_session_date="2020-01-21",
            )
        )

    def test_20_tick_normalisation_is_exact(self):
        self.assertEqual(price_to_ticks(100.25, name="price"), 401)
        with self.assertRaisesRegex(Exp025DataError, "tick size"):
            price_to_ticks(100.1, name="price")

    def test_21_dbn_fixed_price_conversion_is_locked(self):
        self.assertEqual(
            dbn_fixed_price_to_float(10025 * (DBN_FIXED_PRICE_SCALE // 100)),
            100.25,
        )
        with self.assertRaises(Exp025DataError):
            dbn_fixed_price_to_float(2**63 - 1)

    def test_22_dbn_stream_does_not_access_outside_prices(self):
        class GuardedRecord:
            def __init__(self, timestamp_ns, allowed):
                self.ts_event = timestamp_ns
                self._allowed = allowed
                self.instrument_id = 123

            def __getattr__(self, name):
                if name in {"open", "high", "low", "close", "volume"}:
                    if not self._allowed:
                        raise AssertionError("outside price accessed")
                    values = {
                        "open": 100 * DBN_FIXED_PRICE_SCALE,
                        "high": 101 * DBN_FIXED_PRICE_SCALE,
                        "low": 99 * DBN_FIXED_PRICE_SCALE,
                        "close": 100 * DBN_FIXED_PRICE_SCALE,
                        "volume": 10,
                    }
                    return values[name]
                raise AttributeError(name)

        outside = pd.Timestamp("2020-01-22T15:00:00Z").value
        inside = pd.Timestamp("2020-01-22T14:30:00Z").value
        rows = stream_restricted_dbn_records(
            [GuardedRecord(outside, False), GuardedRecord(inside, True)],
            session_date="2020-01-22",
            previous_session_date="2020-01-21",
            exact_contract_symbol="NQH20",
        )
        self.assertEqual(len(rows), 1)

    def test_23_quantower_csv_requires_exact_columns(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "valid.csv"
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=QUANTOWER_REQUIRED_COLUMNS)
                writer.writeheader()
                writer.writerow(make_short_rows()[0])
            self.assertEqual(len(stream_quantower_csv(path)), 1)
            bad = Path(directory) / "bad.csv"
            bad.write_text("timestamp,open\n2020-01-21,100\n", encoding="utf-8")
            with self.assertRaisesRegex(Exp025DataError, "columns or order"):
                stream_quantower_csv(bad)

    def test_24_source_rows_normalise_without_fill(self):
        frame = normalised()
        self.assertEqual(len(frame), 3)
        self.assertEqual(frame["timestamp_utc"].nunique(), 3)
        self.assertEqual(set(frame["window"]), {"PREVIOUS_CASH", "CURRENT_ENTRY_WINDOW"})

    def test_25_source_rows_reject_out_of_window_materialisation(self):
        rows = make_short_rows()
        rows.append(
            {
                **rows[-1],
                "timestamp": "2020-01-22 09:36:00",
            }
        )
        with self.assertRaisesRegex(Exp025DataError, "outside the locked"):
            normalised(rows)

    def test_26_source_rows_reject_duplicate_timestamp(self):
        rows = make_short_rows()
        rows.append(dict(rows[-1]))
        with self.assertRaisesRegex(Exp025DataError, "duplicated"):
            normalised(rows)

    def test_27_five_minute_aggregation_uses_observed_rows_only(self):
        frame = normalised()
        aggregated = aggregate_observed_five_minute(frame)
        current_930 = aggregated.loc[
            aggregated["five_minute_start"].eq(9 * 60 + 30)
            & aggregated["window"].eq("CURRENT_ENTRY_WINDOW")
        ]
        self.assertEqual(len(current_930), 1)
        self.assertEqual(int(current_930.iloc[0]["observation_count"]), 1)

    def test_28_independent_engine_builds_short_gap_fade(self):
        result = independent_gap_fade_decision(
            normalised(),
            session_date="2020-01-22",
            previous_session_date="2020-01-21",
        )
        self.assertTrue(result["setup_passes"])
        self.assertEqual(result["decision_direction"], "short")
        self.assertEqual(result["normalized_gap"], 0.75)

    def test_29_independent_engine_builds_long_gap_fade(self):
        frame = normalised(make_long_rows())
        result = independent_gap_fade_decision(
            frame,
            session_date="2020-01-22",
            previous_session_date="2020-01-21",
        )
        self.assertTrue(result["setup_passes"])
        self.assertEqual(result["decision_direction"], "long")

    def test_30_canonical_wrapper_uses_frozen_candidate_and_source_mapping(self):
        captured = {}
        fake = types.ModuleType("exp024_attribution_core")

        def build_candidate_features(**kwargs):
            captured.update(kwargs)
            return {"setup_passes": True}

        fake.build_candidate_features = build_candidate_features
        previous = sys.modules.get("exp024_attribution_core")
        sys.modules["exp024_attribution_core"] = fake
        try:
            result = canonical_gap_fade_decision(
                normalised(),
                source_id="QUANTOWER_EXACT",
                session_date="2020-01-22",
                previous_session_date="2020-01-21",
            )
        finally:
            if previous is None:
                del sys.modules["exp024_attribution_core"]
            else:
                sys.modules["exp024_attribution_core"] = previous
        self.assertTrue(result["setup_passes"])
        self.assertEqual(captured["candidate_id"], CANDIDATE_ID)
        self.assertEqual(captured["source_id"], "QUANTOWER_REFERENCE")

    def test_31_decision_vector_comparison_detects_change(self):
        left = independent_gap_fade_decision(
            normalised(),
            session_date="2020-01-22",
            previous_session_date="2020-01-21",
        )
        right = dict(left)
        self.assertTrue(decision_vectors_match(left, right))
        right["setup_passes"] = False
        self.assertFalse(decision_vectors_match(left, right))

    def test_32_one_minute_source_comparison_detects_tick_change(self):
        left = normalised()
        right = left.copy()
        equal = compare_one_minute_sources(left, right)
        self.assertTrue(equal["all_ohlc_match"].all())
        right.loc[0, "close_ticks"] += 1
        changed = compare_one_minute_sources(left, right)
        self.assertFalse(changed["all_ohlc_match"].all())
        self.assertEqual(int(changed.iloc[0]["close_difference_ticks"]), 1)

    def test_33_session_classification_is_exhaustive(self):
        self.assertEqual(
            session_classification(
                source_bar_difference=False,
                same_input_engine_difference=False,
            ),
            "EQUIVALENT",
        )
        self.assertEqual(
            session_classification(
                source_bar_difference=True,
                same_input_engine_difference=False,
            ),
            "SOURCE_DIFFERENCE",
        )
        self.assertEqual(
            session_classification(
                source_bar_difference=False,
                same_input_engine_difference=True,
            ),
            "ENGINE_DIFFERENCE",
        )
        self.assertEqual(
            session_classification(
                source_bar_difference=True,
                same_input_engine_difference=True,
            ),
            "MIXED_DIFFERENCE",
        )

    def test_34_final_classification_requires_all_hard_checks(self):
        checks = {"a": True, "b": True}
        self.assertEqual(
            final_classification(
                checks,
                source_difference_present=False,
                engine_difference_present=False,
            ),
            "EXACT_CONTRACT_DIAGNOSTIC_COMPLETE_EQUIVALENT",
        )
        self.assertEqual(
            final_classification(
                checks,
                source_difference_present=True,
                engine_difference_present=False,
            ),
            "EXACT_CONTRACT_DIAGNOSTIC_COMPLETE_SOURCE_DIFFERENCES",
        )
        self.assertEqual(
            final_classification(
                checks,
                source_difference_present=False,
                engine_difference_present=True,
            ),
            "EXACT_CONTRACT_DIAGNOSTIC_COMPLETE_ENGINE_DIFFERENCES",
        )
        self.assertEqual(
            final_classification(
                checks,
                source_difference_present=True,
                engine_difference_present=True,
            ),
            "EXACT_CONTRACT_DIAGNOSTIC_COMPLETE_MIXED_DIFFERENCES",
        )
        self.assertEqual(
            final_classification(
                {"a": False},
                source_difference_present=False,
                engine_difference_present=False,
            ),
            "EXACT_CONTRACT_DIAGNOSTIC_NOT_QUALIFIED",
        )

    def test_35_output_schemas_exclude_performance_fields(self):
        validate_output_schemas()
        forbidden = (
            "pnl",
            "profit",
            "return",
            "equity",
            "drawdown",
            "exit_price",
        )
        for columns in OUTPUT_SCHEMAS.values():
            for column in columns:
                self.assertFalse(any(token in column.lower() for token in forbidden))

    def test_36_required_output_count_is_locked(self):
        self.assertEqual(len(REQUIRED_OUTPUT_NAMES), 14)
        self.assertEqual(len(required_output_set()), 14)

    def test_37_runner_has_no_network_client_import(self):
        source = RUNNER_PATH.read_text(encoding="utf-8")
        for prohibited in (
            "import requests",
            "from requests",
            "import urllib",
            "from urllib",
            "import socket",
            "Historical(",
        ):
            self.assertNotIn(prohibited, source)

    def test_38_runner_locks_25_hard_checks_and_three_modes(self):
        source = RUNNER_PATH.read_text(encoding="utf-8")
        self.assertEqual(source.count('    "') >= 25, True)
        self.assertIn("--implementation-preflight", source)
        self.assertIn("--execution-preflight", source)
        self.assertIn("--execute", source)
        self.assertIn("HARD_CHECK_NAMES", source)
        self.assertIn("commit_that_last_modified", source)
        self.assertNotIn("commit_that_added", source)
        self.assertIn("EXPECTED_SESSION_QUALITY_SHA256", source)


if __name__ == "__main__":
    unittest.main()
