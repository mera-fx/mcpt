from __future__ import annotations

from pathlib import Path
import hashlib
import unittest

import pandas as pd

from exp025_exact_contract_diagnostic import (
    PROJECT_DIR,
    load_population,
)
from exp025_quantower_export_authorization import (
    EXPECTED_EXP025_QUANTOWER_EXPORT_AUTHORIZATION_SHA256,
    canonical_record_hash,
    get_exp025_quantower_export_authorization,
    validate_exp025_quantower_export_authorization,
)
from exp025_quantower_export_preflight import (
    PLAN_COLUMNS,
    PLAN_PATH,
    verify_plan,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class Exp025QuantowerExportAuthorizationTests(
    unittest.TestCase
):
    def test_01_authorization_is_valid(self) -> None:
        validate_exp025_quantower_export_authorization()

    def test_02_authorization_hash_is_locked(self) -> None:
        record = get_exp025_quantower_export_authorization()
        self.assertEqual(
            canonical_record_hash(record),
            EXPECTED_EXP025_QUANTOWER_EXPORT_AUTHORIZATION_SHA256,
        )

    def test_03_implementation_is_locked(self) -> None:
        record = get_exp025_quantower_export_authorization()
        self.assertEqual(
            record["implementation_commit"],
            "2011745145b9799a4a42b556d57780002d30e317",
        )
        self.assertEqual(record["population_rows"], 43)
        self.assertEqual(record["unique_session_count"], 43)

    def test_04_exact_export_counts_are_locked(self) -> None:
        record = get_exp025_quantower_export_authorization()
        self.assertEqual(
            record["authorized_window_export_count"],
            86,
        )
        self.assertEqual(
            record["authorized_final_file_count"],
            43,
        )
        self.assertEqual(record["maximum_export_phases"], 1)

    def test_05_plan_hash_and_columns_are_locked(self) -> None:
        record = get_exp025_quantower_export_authorization()
        self.assertTrue(PLAN_PATH.is_file())
        self.assertEqual(
            sha256_file(PLAN_PATH),
            record["export_plan_sha256"],
        )
        frame = pd.read_csv(
            PLAN_PATH,
            dtype=str,
            keep_default_na=False,
        )
        self.assertEqual(tuple(frame.columns), PLAN_COLUMNS)
        self.assertEqual(len(frame), 43)
        self.assertEqual(frame["session_date"].nunique(), 43)

    def test_06_plan_matches_frozen_population(self) -> None:
        population = load_population()
        record = get_exp025_quantower_export_authorization()
        frame = verify_plan(population, record)
        self.assertEqual(len(frame), 43)

    def test_07_only_exact_contracts_are_planned(self) -> None:
        frame = pd.read_csv(
            PLAN_PATH,
            dtype=str,
            keep_default_na=False,
        )
        self.assertTrue(
            frame["explicit_contract_symbol"]
            .str.fullmatch(r"NQ[HMUZ]\d{2}")
            .all()
        )
        self.assertTrue(
            frame["pretrimmed_to_allowed_windows"]
            .eq("true")
            .all()
        )

    def test_08_diagnostic_and_trading_are_not_authorized(
        self,
    ) -> None:
        record = get_exp025_quantower_export_authorization()
        for key in (
            "diagnostic_execution_authorized",
            "performance_calculation_authorized",
            "strategy_replay_authorized",
            "strategy_search_authorized",
            "strategy_optimization_authorized",
            "mcpt_authorized",
            "bootstrap_authorized",
            "walk_forward_authorized",
            "paper_trading_authorized",
            "live_trading_authorized",
            "order_api_access_authorized",
            "python_network_access_authorized",
            "new_databento_download_authorized",
        ):
            with self.subTest(key=key):
                self.assertFalse(record[key])
        self.assertEqual(
            record["databento_api_calls_authorized"],
            0,
        )

    def test_09_mutation_is_rejected(self) -> None:
        record = get_exp025_quantower_export_authorization()
        record["authorized_window_export_count"] = 87
        with self.assertRaisesRegex(
            ValueError,
            "authorization identity changed",
        ):
            validate_exp025_quantower_export_authorization(
                record
            )

    def test_10_preflight_has_no_network_or_order_client(
        self,
    ) -> None:
        source = (
            PROJECT_DIR
            / "exp025_quantower_export_preflight.py"
        ).read_text(encoding="utf-8")
        for prohibited in (
            "import requests",
            "from requests",
            "import urllib",
            "from urllib",
            "import socket",
            "Historical(",
            "PlaceOrder",
            "SendOrder",
        ):
            with self.subTest(prohibited=prohibited):
                self.assertNotIn(prohibited, source)


if __name__ == "__main__":
    unittest.main()
