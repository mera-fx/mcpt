from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np
import pandas as pd

from mcpt_engine import (
    checkpoint_signature_digest,
    load_mcpt_checkpoint,
    optimize_permuted_market,
    resolve_worker_count,
    run_mcpt_engine,
    save_mcpt_checkpoint,
)


def small_ohlc(
    rows: int = 180,
) -> pd.DataFrame:
    generator = np.random.default_rng(
        1234
    )

    returns = generator.normal(
        0.0002,
        0.01,
        size=rows,
    )

    close = 100 * np.exp(
        np.cumsum(returns)
    )

    open_price = np.r_[
        close[0],
        close[:-1],
    ]

    spread = 0.01

    return pd.DataFrame(
        {
            "open": open_price,
            "high": np.maximum(
                open_price,
                close,
            ) * (1 + spread),
            "low": np.minimum(
                open_price,
                close,
            ) * (1 - spread),
            "close": close,
        },
        index=pd.date_range(
            "2024-01-01",
            periods=rows,
            freq="h",
        ),
    )


class McptEngineTests(
    unittest.TestCase
):
    def test_worker_count_validation(
        self,
    ) -> None:
        self.assertEqual(
            resolve_worker_count(1),
            1,
        )

        with self.assertRaises(
            ValueError
        ):
            resolve_worker_count(-1)

    def test_signature_digest_is_stable(
        self,
    ) -> None:
        first = checkpoint_signature_digest(
            {
                "b": 2,
                "a": 1,
            }
        )

        second = checkpoint_signature_digest(
            {
                "a": 1,
                "b": 2,
            }
        )

        self.assertEqual(
            first,
            second,
        )

    def test_checkpoint_round_trip(
        self,
    ) -> None:
        signature = {
            "experiment": "TEST",
            "version": 1,
        }

        rows = [
            {
                "permutation": 1,
                "best_bar_profit_factor": 1.1,
                "lookback": 3,
                "optimizer_mode": (
                    "generic_grid_v1"
                ),
            }
        ]

        with TemporaryDirectory() as temporary:
            directory = Path(temporary)

            save_mcpt_checkpoint(
                checkpoint_directory=directory,
                rows=rows,
                base_signature=signature,
                target_permutations=3,
                workers=1,
                status="running",
            )

            loaded = load_mcpt_checkpoint(
                checkpoint_directory=directory,
                base_signature=signature,
                target_permutations=3,
                parameter_names=("lookback",),
            )

        self.assertEqual(
            loaded["permutation"].tolist(),
            [1],
        )

        self.assertEqual(
            loaded["lookback"].tolist(),
            [3],
        )

    def test_incompatible_checkpoint_is_ignored(
        self,
    ) -> None:
        rows = [
            {
                "permutation": 1,
                "best_bar_profit_factor": 1.1,
                "lookback": 3,
            }
        ]

        with TemporaryDirectory() as temporary:
            directory = Path(temporary)

            save_mcpt_checkpoint(
                checkpoint_directory=directory,
                rows=rows,
                base_signature={"version": 1},
                target_permutations=3,
                workers=1,
                status="running",
            )

            loaded = load_mcpt_checkpoint(
                checkpoint_directory=directory,
                base_signature={"version": 2},
                target_permutations=3,
                parameter_names=("lookback",),
            )

        self.assertTrue(
            loaded.empty
        )

    def test_resume_extends_checkpoint(
        self,
    ) -> None:
        data = small_ohlc()

        signature = {
            "experiment": "TEST",
            "strategy": "donchian_breakout",
        }

        common = {
            "in_sample_data": data,
            "strategy_name": (
                "donchian_breakout"
            ),
            "optimization_grid": {
                "lookback": [3, 5, 8],
            },
            "random_seed": 100,
            "real_score": 1.0,
            "requested_workers": 1,
            "checkpoint_every": 1,
            "resume": True,
            "checkpoint_signature": (
                signature
            ),
        }

        with TemporaryDirectory() as temporary:
            directory = Path(temporary)

            first, _, _, first_info = (
                run_mcpt_engine(
                    **common,
                    permutations=2,
                    checkpoint_directory=(
                        directory
                    ),
                )
            )

            second, _, _, second_info = (
                run_mcpt_engine(
                    **common,
                    permutations=4,
                    checkpoint_directory=(
                        directory
                    ),
                )
            )

        self.assertEqual(
            first["permutation"].tolist(),
            [1, 2],
        )

        self.assertEqual(
            second["permutation"].tolist(),
            [1, 2, 3, 4],
        )

        self.assertEqual(
            first_info.resumed_permutations,
            0,
        )

        self.assertEqual(
            second_info.resumed_permutations,
            2,
        )


    def test_exp003_fast_path_matches_generic_exactly(
        self,
    ) -> None:
        data = small_ohlc(
            rows=2300
        )

        grid = {
            "vol_lookback": [24, 48, 72],
            "compression_quantile": [
                0.10,
                0.20,
                0.30,
            ],
            "breakout_lookback": [
                24,
                48,
                72,
            ],
        }

        (
            generic_parameters,
            generic_score,
            generic_mode,
        ) = optimize_permuted_market(
            data=data,
            strategy_name=(
                "volatility_compression_breakout_long"
            ),
            optimization_grid=grid,
            allow_fast_path=False,
        )

        (
            fast_parameters,
            fast_score,
            fast_mode,
        ) = optimize_permuted_market(
            data=data,
            strategy_name=(
                "volatility_compression_breakout_long"
            ),
            optimization_grid=grid,
            allow_fast_path=True,
        )

        self.assertEqual(
            generic_parameters,
            fast_parameters,
        )

        self.assertEqual(
            generic_score,
            fast_score,
        )

        self.assertEqual(
            generic_mode,
            "generic_grid_v1",
        )

        self.assertEqual(
            fast_mode,
            "shared_indicators_exp003_v1",
        )


    def test_smaller_target_preserves_larger_checkpoint(
        self,
    ) -> None:
        data = small_ohlc()

        signature = {
            "experiment": "SUPERSET",
        }

        stored_rows = [
            {
                "permutation": number,
                "best_bar_profit_factor": (
                    1.0 + number / 100
                ),
                "lookback": 3,
            }
            for number in range(1, 5)
        ]

        with TemporaryDirectory() as temporary:
            directory = Path(temporary)

            save_mcpt_checkpoint(
                checkpoint_directory=directory,
                rows=stored_rows,
                base_signature=signature,
                target_permutations=4,
                workers=1,
                status="complete",
            )

            results, _, _, info = (
                run_mcpt_engine(
                    in_sample_data=data,
                    strategy_name=(
                        "donchian_breakout"
                    ),
                    optimization_grid={
                        "lookback": [3, 5],
                    },
                    random_seed=10,
                    permutations=2,
                    real_score=1.0,
                    requested_workers=1,
                    checkpoint_directory=directory,
                    checkpoint_every=1,
                    resume=True,
                    checkpoint_signature=signature,
                )
            )

            stored_after = load_mcpt_checkpoint(
                checkpoint_directory=directory,
                base_signature=signature,
                target_permutations=4,
                parameter_names=("lookback",),
            )

        self.assertEqual(
            results["permutation"].tolist(),
            [1, 2],
        )

        self.assertEqual(
            stored_after[
                "permutation"
            ].tolist(),
            [1, 2, 3, 4],
        )

        self.assertEqual(
            info.resumed_permutations,
            2,
        )

    def test_serial_and_parallel_are_exact(
        self,
    ) -> None:
        data = small_ohlc()

        common = {
            "in_sample_data": data,
            "strategy_name": (
                "donchian_breakout"
            ),
            "optimization_grid": {
                "lookback": [3, 5, 8],
            },
            "random_seed": 500,
            "permutations": 4,
            "real_score": 1.0,
            "checkpoint_every": 2,
            "resume": False,
            "checkpoint_signature": {
                "experiment": "PARITY",
            },
        }

        with TemporaryDirectory() as temporary:
            root = Path(temporary)

            serial, _, _, _ = (
                run_mcpt_engine(
                    **common,
                    requested_workers=1,
                    checkpoint_directory=(
                        root / "serial"
                    ),
                )
            )

            parallel, _, _, _ = (
                run_mcpt_engine(
                    **common,
                    requested_workers=2,
                    checkpoint_directory=(
                        root / "parallel"
                    ),
                )
            )

        pd.testing.assert_frame_equal(
            serial,
            parallel,
            check_exact=True,
        )


if __name__ == "__main__":
    unittest.main()
