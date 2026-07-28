from __future__ import annotations

import ast
import importlib
from pathlib import Path
import shutil
import sys
import unittest

from exp027_preregistration import (
    EXPECTED_EXP027_PREREGISTRATION_SHA256,
)


PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = (
    PROJECT_DIR
    / "results"
    / "EXP-027"
    / "protected_2026_measurement"
)
PARTIAL_DIR = OUTPUT_DIR.with_name(
    OUTPUT_DIR.name + ".partial"
)


class Exp027ImplementationTests(unittest.TestCase):
    def test_01_required_implementation_files_exist(
        self,
    ) -> None:
        for relative in (
            "exp027_core.py",
            "exp027_runner.py",
            "exp027_implementation_preflight.py",
            "research/EXP-027_implementation_report.md",
            "tests/test_exp027_core.py",
            "tests/test_exp027_implementation.py",
        ):
            self.assertTrue(
                (PROJECT_DIR / relative).is_file(),
                relative,
            )

    def test_02_import_does_not_create_outputs(
        self,
    ) -> None:
        self.assertFalse(OUTPUT_DIR.exists())
        self.assertFalse(PARTIAL_DIR.exists())
        for module_name in (
            "exp027_core",
            "exp027_runner",
            "exp027_implementation_preflight",
        ):
            sys.modules.pop(module_name, None)
            importlib.import_module(module_name)
        self.assertFalse(OUTPUT_DIR.exists())
        self.assertFalse(PARTIAL_DIR.exists())

    def test_03_runner_requires_separate_authorization(
        self,
    ) -> None:
        from exp027_runner import load_authorization

        with self.assertRaisesRegex(
            RuntimeError,
            "not authorized",
        ):
            load_authorization()

    def test_04_locked_preregistration_commit_is_exact(
        self,
    ) -> None:
        from exp027_runner import (
            LOCKED_PREREGISTRATION_COMMIT,
        )

        self.assertEqual(
            LOCKED_PREREGISTRATION_COMMIT,
            "21c182e119cde651e6c4fe22b1e4e8d6b99def5b",
        )

    def test_05_frozen_exp026_engine_commit_is_exact(
        self,
    ) -> None:
        from exp027_runner import (
            LOCKED_EXP026_IMPLEMENTATION_COMMIT,
        )

        self.assertEqual(
            LOCKED_EXP026_IMPLEMENTATION_COMMIT,
            "13ee0683dfcbbb5d763f7254f3b245ecc8e6d9cd",
        )

    def test_06_protected_loader_uses_exact_bounds(
        self,
    ) -> None:
        source = (
            PROJECT_DIR / "exp027_runner.py"
        ).read_text(encoding="utf-8")
        self.assertIn(
            'PERIOD_START = "2026-01-01"',
            source,
        )
        self.assertIn(
            'PERIOD_END = "2026-07-23"',
            source,
        )
        self.assertIn(
            'ds.field("trading_date")',
            source,
        )
        self.assertNotIn(
            "pd.read_parquet",
            source,
        )

    def test_07_no_network_or_databento_client_import(
        self,
    ) -> None:
        tree = ast.parse(
            (
                PROJECT_DIR / "exp027_runner.py"
            ).read_text(encoding="utf-8")
        )
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(
                    alias.name.split(".")[0]
                    for alias in node.names
                )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported.add(
                        node.module.split(".")[0]
                    )
        self.assertFalse(
            {
                "databento",
                "requests",
                "httpx",
                "urllib",
                "socket",
            }
            & imported
        )

    def test_08_implementation_scope_has_six_files(
        self,
    ) -> None:
        from exp027_runner import IMPLEMENTATION_PATHS

        self.assertEqual(
            len(IMPLEMENTATION_PATHS),
            6,
        )
        self.assertEqual(
            set(IMPLEMENTATION_PATHS),
            {
                "exp027_core.py",
                "exp027_runner.py",
                "exp027_implementation_preflight.py",
                "research/EXP-027_implementation_report.md",
                "tests/test_exp027_core.py",
                "tests/test_exp027_implementation.py",
            },
        )

    def test_09_authorization_scope_is_separate(
        self,
    ) -> None:
        from exp027_runner import (
            AUTHORIZATION_PATHS,
            IMPLEMENTATION_PATHS,
        )

        self.assertFalse(
            set(AUTHORIZATION_PATHS)
            & set(IMPLEMENTATION_PATHS)
        )
        for relative in AUTHORIZATION_PATHS:
            self.assertFalse(
                (PROJECT_DIR / relative).exists()
            )

    def test_10_output_contract_requires_24_series(
        self,
    ) -> None:
        from exp027_preregistration import (
            get_exp027_preregistration,
        )

        required = get_exp027_preregistration()[
            "required_outputs"
        ]
        self.assertEqual(
            required["per_series_count"],
            24,
        )
        self.assertEqual(
            len(required["per_series_pattern"]),
            4,
        )

    def test_11_preregistration_hash_is_unchanged(
        self,
    ) -> None:
        self.assertEqual(
            EXPECTED_EXP027_PREREGISTRATION_SHA256,
            "3177e5bb81bbf330b8a020c3bfee56b584cd284da3546fcdad4b90df5ffd76bd",
        )

    def test_12_no_result_directory_exists(
        self,
    ) -> None:
        self.assertFalse(OUTPUT_DIR.exists())
        self.assertFalse(PARTIAL_DIR.exists())


if __name__ == "__main__":
    unittest.main()
