from __future__ import annotations

import ast
from pathlib import Path
import unittest


PROJECT_DIR = Path(__file__).resolve().parents[1]
RUNNER_FILE = PROJECT_DIR / "run_exp015_audit.py"
WORKER_FILE = PROJECT_DIR / "exp015_lse_worker.py"


class Exp015RunnerBoundaryTests(unittest.TestCase):
    def test_runner_modes_are_mutually_exclusive(self) -> None:
        source = RUNNER_FILE.read_text(encoding="utf-8")
        self.assertIn(
            "add_mutually_exclusive_group(required=True)",
            source,
        )
        self.assertIn('"--preflight"', source)
        self.assertIn('"--probe-client"', source)
        self.assertIn('"--catalog"', source)

    def test_catalog_worker_calls_only_catalog_futures(self) -> None:
        source = WORKER_FILE.read_text(encoding="utf-8")
        self.assertIn('client.catalog("futures")', source)
        for prohibited in (
            "client.candles(",
            "client.history(",
            "client.dataset(",
            "client.stream(",
            "client.connect(",
        ):
            self.assertNotIn(prohibited, source)

    def test_worker_does_not_import_strategy_modules(self) -> None:
        tree = ast.parse(WORKER_FILE.read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        self.assertFalse(
            any(
                name.startswith(
                    (
                        "exp012",
                        "exp013",
                        "exp014",
                        "trade_engine",
                    )
                )
                for name in imported
            )
        )

    def test_probe_removes_real_key_before_import(self) -> None:
        source = WORKER_FILE.read_text(encoding="utf-8")
        pop_at = source.index('os.environ.pop("LSE_API_KEY", None)')
        import_at = source.index("from lse import LSE", pop_at)
        self.assertLess(pop_at, import_at)
        self.assertIn("DUMMY_KEY", source)
        self.assertIn('"network_market_data_call": False', source)

    def test_catalog_requires_clean_git_and_probe(self) -> None:
        source = RUNNER_FILE.read_text(encoding="utf-8")
        self.assertIn("protected_preflight()", source)
        self.assertIn("_verified_probe_manifest()", source)
        self.assertIn("working_tree_clean", source)
        self.assertIn("CATALOG_RESULT_FILE.exists()", source)

    def test_runner_has_no_prior_result_write_paths(self) -> None:
        source = RUNNER_FILE.read_text(encoding="utf-8")
        self.assertNotIn('results" / "EXP-014', source)
        self.assertNotIn('results" / "EXP-013', source)
        self.assertNotIn('data" / "EXP-014', source)
        self.assertNotIn('data" / "EXP-013', source)
