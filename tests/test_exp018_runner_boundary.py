from __future__ import annotations

from pathlib import Path
import unittest

import exp018_databento_worker
import run_exp018_qualification


PROJECT_DIR = Path(__file__).resolve().parents[1]


class Exp018RunnerBoundaryTests(unittest.TestCase):
    def test_worker_does_not_import_databento_at_module_import(self) -> None:
        source = (PROJECT_DIR / "exp018_databento_worker.py").read_text(
            encoding="utf-8"
        )
        prefix = source.split("def estimate_cost", 1)[0]
        self.assertNotIn("import databento", prefix)

    def test_only_official_streaming_method_is_present(self) -> None:
        source = (PROJECT_DIR / "exp018_databento_worker.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("client.timeseries.get_range", source)
        self.assertNotIn("client.batch", source)
        self.assertNotIn('stype_in="continuous"', source)
        self.assertNotIn('stype_in="parent"', source)

    def test_runner_exposes_no_full_history_or_strategy_mode(self) -> None:
        source = (PROJECT_DIR / "run_exp018_qualification.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('modes.add_argument("--initial-downloads"', source)
        self.assertIn('modes.add_argument("--repeat-downloads"', source)
        self.assertIn('modes.add_argument("--audit-local"', source)
        self.assertNotIn('modes.add_argument("--full-history"', source)
        self.assertNotIn('modes.add_argument("--strategy"', source)

    def test_request_lock_is_written_before_remote_worker(self) -> None:
        source = (PROJECT_DIR / "run_exp018_qualification.py").read_text(
            encoding="utf-8"
        )
        function = source.split("def _request_one", 1)[1].split(
            "def run_initial_downloads", 1
        )[0]
        self.assertLess(
            function.index("_atomic_json(started, lock)"),
            function.index('"estimate-cost"'),
        )
        self.assertIn("No retry is allowed", function)

    def test_worker_safe_error_redacts_current_key(self) -> None:
        old = exp018_databento_worker.os.environ.get("DATABENTO_API_KEY")
        try:
            exp018_databento_worker.os.environ["DATABENTO_API_KEY"] = "db-secret"
            rendered = exp018_databento_worker._safe_error(
                RuntimeError("failed db-secret")
            )
            self.assertNotIn("db-secret", rendered)
            self.assertIn("<redacted>", rendered)
        finally:
            if old is None:
                exp018_databento_worker.os.environ.pop(
                    "DATABENTO_API_KEY", None
                )
            else:
                exp018_databento_worker.os.environ[
                    "DATABENTO_API_KEY"
                ] = old

    def test_modes_remain_mutually_exclusive(self) -> None:
        source = (PROJECT_DIR / "run_exp018_qualification.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("add_mutually_exclusive_group(required=True)", source)


if __name__ == "__main__":
    unittest.main()
