from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

from run_provenance import (
    append_run_history,
    load_compatible_mcpt_cache,
    mcpt_base_signature,
    save_mcpt_cache,
)


def make_config() -> SimpleNamespace:
    return SimpleNamespace(
        experiment_id="EXP-TEST",
        strategy_name="test_strategy",
        optimization_grid={
            "lookback": [10, 20],
        },
        in_sample_start="2020-01-01",
        in_sample_end="2021-01-01",
        random_seed=123,
        mcpt_permutations=1000,
    )


class McptCacheTests(unittest.TestCase):
    def test_compatible_cache_is_loaded(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            config = make_config()

            signature = mcpt_base_signature(
                config=config,
                data_file_sha256="data-a",
                code_fingerprint="code-a",
            )

            results = pd.DataFrame(
                {
                    "permutation": [1, 2],
                    "best_bar_profit_factor": [
                        1.0,
                        1.1,
                    ],
                }
            )

            save_mcpt_cache(
                results_directory=directory,
                results=results,
                p_value=0.5,
                better_or_equal=1,
                permutations=2,
                configured_full_permutations=1000,
                base_signature=signature,
                real_score=1.05,
            )

            loaded, metadata = (
                load_compatible_mcpt_cache(
                    results_directory=directory,
                    base_signature=signature,
                )
            )

            self.assertIsNotNone(loaded)
            self.assertIsNotNone(metadata)
            self.assertEqual(len(loaded), 2)
            self.assertEqual(
                metadata["cache_kind"],
                "quick",
            )

    def test_changed_data_rejects_cache(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            config = make_config()

            original_signature = (
                mcpt_base_signature(
                    config=config,
                    data_file_sha256="data-a",
                    code_fingerprint="code-a",
                )
            )

            changed_signature = (
                mcpt_base_signature(
                    config=config,
                    data_file_sha256="data-b",
                    code_fingerprint="code-a",
                )
            )

            results = pd.DataFrame(
                {
                    "permutation": [1],
                    "best_bar_profit_factor": [
                        1.0,
                    ],
                }
            )

            save_mcpt_cache(
                results_directory=directory,
                results=results,
                p_value=1.0,
                better_or_equal=1,
                permutations=1,
                configured_full_permutations=1000,
                base_signature=original_signature,
                real_score=1.05,
            )

            loaded, metadata = (
                load_compatible_mcpt_cache(
                    results_directory=directory,
                    base_signature=changed_signature,
                )
            )

            self.assertIsNone(loaded)
            self.assertIsNone(metadata)


class RunHistoryTests(unittest.TestCase):
    def test_history_appends_without_overwriting(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as folder:
            history_file = (
                Path(folder) / "history.csv"
            )

            append_run_history(
                history_file=history_file,
                row={
                    "run_id": "one",
                    "value": 1,
                },
            )

            append_run_history(
                history_file=history_file,
                row={
                    "run_id": "two",
                    "value": 2,
                },
            )

            history = pd.read_csv(
                history_file
            )

            self.assertEqual(
                history["run_id"].tolist(),
                ["one", "two"],
            )


if __name__ == "__main__":
    unittest.main()
