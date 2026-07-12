from __future__ import annotations

import argparse
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
from time import perf_counter

import numpy as np
import pandas as pd

from mcpt_engine import run_mcpt_engine


def synthetic_ohlc(
    rows: int = 10000,
    seed: int = 20260712,
) -> pd.DataFrame:
    generator = np.random.default_rng(
        seed
    )

    close_returns = generator.normal(
        0.00005,
        0.009,
        size=rows,
    )

    close = 30_000 * np.exp(
        np.cumsum(close_returns)
    )

    open_price = np.r_[
        close[0],
        close[:-1],
    ] * np.exp(
        generator.normal(
            0.0,
            0.001,
            size=rows,
        )
    )

    spread = np.abs(
        generator.normal(
            0.003,
            0.0015,
            size=rows,
        )
    )

    high = np.maximum(
        open_price,
        close,
    ) * (1 + spread)

    low = np.minimum(
        open_price,
        close,
    ) * (1 - spread)

    return pd.DataFrame(
        {
            "open": open_price,
            "high": high,
            "low": low,
            "close": close,
        },
        index=pd.date_range(
            "2020-01-01",
            periods=rows,
            freq="h",
        ),
    )


def run_once(
    *,
    data: pd.DataFrame,
    workers: int,
    permutations: int,
    checkpoint_directory: Path,
) -> tuple[pd.DataFrame, float]:
    start = perf_counter()

    results, _, _, _ = run_mcpt_engine(
        in_sample_data=data,
        strategy_name=(
            "volatility_compression_breakout_long"
        ),
        optimization_grid={
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
        },
        random_seed=42,
        permutations=permutations,
        real_score=1.0,
        requested_workers=workers,
        checkpoint_directory=(
            checkpoint_directory
        ),
        checkpoint_every=2,
        resume=False,
        checkpoint_signature={
            "benchmark": "synthetic_exp003",
            "version": 1,
        },
    )

    elapsed = perf_counter() - start

    return results, elapsed


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Verify deterministic serial-versus-multicore "
            "MCPT output on synthetic data."
        )
    )

    parser.add_argument(
        "--permutations",
        type=int,
        default=8,
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=0,
        help=(
            "Parallel workers. 0 uses automatic mode."
        ),
    )

    parser.add_argument(
        "--rows",
        type=int,
        default=10000,
        help=(
            "Synthetic hourly bars used by the engineering "
            "benchmark."
        ),
    )

    arguments = parser.parse_args()

    data = synthetic_ohlc(
        rows=arguments.rows
    )

    with TemporaryDirectory() as temporary:
        root = Path(temporary)

        serial, serial_seconds = run_once(
            data=data,
            workers=1,
            permutations=arguments.permutations,
            checkpoint_directory=(
                root / "serial"
            ),
        )

        parallel, parallel_seconds = run_once(
            data=data,
            workers=arguments.workers,
            permutations=arguments.permutations,
            checkpoint_directory=(
                root / "parallel"
            ),
        )

    pd.testing.assert_frame_equal(
        serial,
        parallel,
        check_exact=True,
    )

    speedup = (
        serial_seconds / parallel_seconds
        if parallel_seconds > 0
        else float("inf")
    )

    print()
    print("MCPT MULTICORE BENCHMARK")
    print("========================")
    print(
        f"Synthetic bars:   {arguments.rows:,}"
    )
    print(
        f"Permutations:     {arguments.permutations}"
    )
    print(
        f"Serial time:      {serial_seconds:.2f}s"
    )
    print(
        f"Parallel time:    {parallel_seconds:.2f}s"
    )
    print(
        f"Observed speedup: {speedup:.2f}x"
    )
    print("Result equality:  EXACT PASS")
    print()
    print(
        "This benchmark uses synthetic data and does not "
        "rerun or alter any recorded experiment."
    )


if __name__ == "__main__":
    main()
