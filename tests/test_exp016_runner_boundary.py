from __future__ import annotations

import ast
from pathlib import Path
import unittest


PROJECT_DIR = Path(__file__).resolve().parents[1]


class Exp016RunnerBoundaryTests(unittest.TestCase):
    def test_runner_modes_are_mutually_exclusive(self) -> None:
        source = (PROJECT_DIR / "run_exp016_audit.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("add_mutually_exclusive_group(required=True)", source)
        self.assertIn('"--preflight"', source)
        self.assertIn('"--download-samples"', source)
        self.assertIn('"--retry-rate-limited-window"', source)
        self.assertIn('"--audit-local"', source)
        self.assertNotIn('"--catalog"', source)
        self.assertNotIn('"--strategy"', source)

    def test_worker_uses_only_locked_history_call(self) -> None:
        source = (
            PROJECT_DIR / "exp016_lse_history_worker.py"
        ).read_text(encoding="utf-8")
        tree = ast.parse(source)
        methods = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "client"
        }
        self.assertEqual(methods, {"history"})
        self.assertIn('"NQ.F"', source)
        self.assertIn('dataset="futures"', source)
        self.assertIn('timeframe="1m"', source)
        self.assertIn("dataframe=False", source)

    def test_runner_does_not_import_strategy_modules(self) -> None:
        source = (PROJECT_DIR / "run_exp016_audit.py").read_text(
            encoding="utf-8"
        ).lower()
        prohibited = (
            "exp012_engine",
            "exp013_selection",
            "exp014_measurements",
            "trade_engine",
            "optimization",
            "mcpt",
        )
        for token in prohibited:
            self.assertNotIn(f"import {token}", source)

    def test_original_request_lock_precedes_worker_call(self) -> None:
        source = (PROJECT_DIR / "run_exp016_audit.py").read_text(
            encoding="utf-8"
        )
        lock_write = source.index("_atomic_json(started, lock)")
        worker_call = source.index("completed = subprocess.run(", lock_write)
        self.assertLess(lock_write, worker_call)

    def test_amended_retry_lock_precedes_retry_worker_call(self) -> None:
        source = (PROJECT_DIR / "run_exp016_audit.py").read_text(
            encoding="utf-8"
        )
        function_start = source.index("def run_retry_rate_limited_window")
        lock_write = source.index("_atomic_json(started, retry_lock)", function_start)
        worker_call = source.index("completed = subprocess.run(", lock_write)
        self.assertLess(lock_write, worker_call)

    def test_amended_retry_is_only_for_frozen_failed_window(self) -> None:
        source = (PROJECT_DIR / "run_exp016_audit.py").read_text(
            encoding="utf-8"
        )
        function_start = source.index("def run_retry_rate_limited_window")
        function_end = source.index("def run_local_audit", function_start)
        retry_source = source[function_start:function_end]
        self.assertIn('OBSERVED_RATE_LIMIT_FAILURE["window_id"]', retry_source)
        self.assertIn("additional_retry_authorized", retry_source)
        self.assertIn("False", retry_source)

    def test_prior_data_has_no_write_path(self) -> None:
        source = (PROJECT_DIR / "run_exp016_audit.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("to_parquet(OUTPUT_FILES", source)
        self.assertNotIn("write_extended_session_dataset", source)
