from __future__ import annotations

from concurrent.futures import (
    Future,
    ProcessPoolExecutor,
    as_completed,
)
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from tqdm import tqdm

from bar_permute import get_permutation
from strategy_registry import (
    build_volatility_breakout_position_signal,
    expand_parameter_grid,
    generate_signal,
    get_strategy,
)


_WORKER_DATA: pd.DataFrame | None = None
_WORKER_STRATEGY_NAME: str | None = None
_WORKER_OPTIMIZATION_GRID: dict[str, list[Any]] | None = None
_WORKER_RANDOM_SEED: int | None = None


@dataclass(frozen=True)
class McptExecutionInfo:
    requested_workers: int
    workers_used: int
    resumed_permutations: int
    newly_completed_permutations: int
    checkpoint_file: str
    optimizer_mode: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "requested_workers": self.requested_workers,
            "workers_used": self.workers_used,
            "resumed_permutations": (
                self.resumed_permutations
            ),
            "newly_completed_permutations": (
                self.newly_completed_permutations
            ),
            "checkpoint_file": self.checkpoint_file,
            "optimizer_mode": self.optimizer_mode,
        }


def resolve_worker_count(
    requested_workers: int | None,
) -> int:
    """
    Resolve the number of process workers.

    0 or None means automatic. Automatic mode leaves capacity for
    Windows and normal desktop use, and caps the pool at eight workers.
    """

    logical_cpus = max(
        1,
        int(os.cpu_count() or 1),
    )

    if requested_workers in (None, 0):
        return max(
            1,
            min(
                8,
                logical_cpus - 1,
            ),
        )

    workers = int(requested_workers)

    if workers < 1:
        raise ValueError(
            "mcpt_workers must be 0 (automatic) "
            "or a positive integer."
        )

    return min(
        workers,
        logical_cpus,
    )


def bar_return_profit_factor_from_returns(
    *,
    signal: pd.Series,
    next_bar_return: pd.Series,
) -> float:
    strategy_returns = (
        signal.reindex(next_bar_return.index)
        * next_bar_return
    ).dropna()

    if len(strategy_returns) < 10:
        return float("nan")

    gains = strategy_returns[
        strategy_returns > 0
    ].sum()

    losses = strategy_returns[
        strategy_returns < 0
    ].abs().sum()

    if losses <= 0:
        return float("nan")

    return float(gains / losses)


def _generic_best_score(
    *,
    data: pd.DataFrame,
    strategy_name: str,
    optimization_grid: dict[str, list[Any]],
) -> tuple[dict[str, Any], float]:
    combinations = expand_parameter_grid(
        strategy_name,
        optimization_grid,
    )

    best_parameters: dict[str, Any] | None = None
    best_score = float("-inf")

    for parameters in combinations:
        signal = generate_signal(
            strategy_name,
            data,
            parameters,
        )

        next_bar_return = (
            np.log(data["close"])
            .diff()
            .shift(-1)
        )

        score = (
            bar_return_profit_factor_from_returns(
                signal=signal,
                next_bar_return=next_bar_return,
            )
        )

        if not np.isfinite(score):
            continue

        # Strict comparison preserves the original first-row tie break.
        if (
            best_parameters is None
            or score > best_score
        ):
            best_parameters = dict(parameters)
            best_score = float(score)

    if best_parameters is None:
        raise RuntimeError(
            "Every parameter combination produced "
            "an invalid score."
        )

    return best_parameters, best_score


def _exp003_fast_best_score(
    *,
    data: pd.DataFrame,
    optimization_grid: dict[str, list[Any]],
) -> tuple[dict[str, Any], float]:
    """
    Exact shared-indicator implementation for the locked EXP-003
    strategy.

    The formulas, state machine, grid order and tie-breaking match the
    original strategy implementation. Expensive rolling indicators are
    calculated once per unique parameter value rather than once for
    every one of the 27 combinations.
    """

    combinations = expand_parameter_grid(
        "volatility_compression_breakout_long",
        optimization_grid,
    )

    close = data["close"].astype(float)
    high = data["high"].astype(float)
    low = data["low"].astype(float)

    log_return = np.log(close).diff()

    next_bar_return = (
        np.log(close)
        .diff()
        .shift(-1)
    )

    vol_lookbacks = list(
        dict.fromkeys(
            int(parameters["vol_lookback"])
            for parameters in combinations
        )
    )

    compression_quantiles = list(
        dict.fromkeys(
            float(
                parameters[
                    "compression_quantile"
                ]
            )
            for parameters in combinations
        )
    )

    breakout_lookbacks = list(
        dict.fromkeys(
            int(
                parameters[
                    "breakout_lookback"
                ]
            )
            for parameters in combinations
        )
    )

    realized_volatility: dict[
        int,
        pd.Series,
    ] = {}

    recent_compression: dict[
        tuple[int, float],
        pd.Series,
    ] = {}

    breakout_levels: dict[
        int,
        pd.Series,
    ] = {}

    for vol_lookback in vol_lookbacks:
        realized = log_return.rolling(
            vol_lookback,
            min_periods=vol_lookback,
        ).std(ddof=0)

        realized_volatility[
            vol_lookback
        ] = realized

        for quantile in compression_quantiles:
            threshold = realized.rolling(
                2160,
                min_periods=2160,
            ).quantile(
                quantile
            ).shift(1)

            compressed = (
                realized <= threshold
            ).fillna(False)

            recent = (
                compressed.astype(float)
                .rolling(
                    24,
                    min_periods=1,
                )
                .max()
                .astype(bool)
            )

            recent_compression[
                (vol_lookback, quantile)
            ] = recent

    for breakout_lookback in breakout_lookbacks:
        breakout_levels[
            breakout_lookback
        ] = (
            high.shift(1)
            .rolling(
                breakout_lookback,
                min_periods=breakout_lookback,
            )
            .max()
        )

    exit_level = (
        low.shift(1)
        .rolling(
            24,
            min_periods=24,
        )
        .min()
    )

    best_parameters: dict[str, Any] | None = None
    best_score = float("-inf")

    for parameters in combinations:
        vol_lookback = int(
            parameters["vol_lookback"]
        )

        quantile = float(
            parameters[
                "compression_quantile"
            ]
        )

        breakout_lookback = int(
            parameters[
                "breakout_lookback"
            ]
        )

        signal = (
            build_volatility_breakout_position_signal(
                close=close,
                recent_compression=(
                    recent_compression[
                        (
                            vol_lookback,
                            quantile,
                        )
                    ]
                ),
                breakout_level=(
                    breakout_levels[
                        breakout_lookback
                    ]
                ),
                exit_level=exit_level,
                maximum_holding_bars=168,
            )
        )

        score = (
            bar_return_profit_factor_from_returns(
                signal=signal,
                next_bar_return=next_bar_return,
            )
        )

        if not np.isfinite(score):
            continue

        if (
            best_parameters is None
            or score > best_score
        ):
            best_parameters = dict(parameters)
            best_score = float(score)

    if best_parameters is None:
        raise RuntimeError(
            "Every parameter combination produced "
            "an invalid score."
        )

    return best_parameters, best_score


def optimize_permuted_market(
    *,
    data: pd.DataFrame,
    strategy_name: str,
    optimization_grid: dict[str, list[Any]],
    allow_fast_path: bool = True,
) -> tuple[dict[str, Any], float, str]:
    if (
        allow_fast_path
        and strategy_name
        == "volatility_compression_breakout_long"
    ):
        parameters, score = (
            _exp003_fast_best_score(
                data=data,
                optimization_grid=(
                    optimization_grid
                ),
            )
        )

        return (
            parameters,
            score,
            "shared_indicators_exp003_v1",
        )

    parameters, score = _generic_best_score(
        data=data,
        strategy_name=strategy_name,
        optimization_grid=optimization_grid,
    )

    return (
        parameters,
        score,
        "generic_grid_v1",
    )


def _initialize_worker(
    data: pd.DataFrame,
    strategy_name: str,
    optimization_grid: dict[str, list[Any]],
    random_seed: int,
) -> None:
    global _WORKER_DATA
    global _WORKER_STRATEGY_NAME
    global _WORKER_OPTIMIZATION_GRID
    global _WORKER_RANDOM_SEED

    _WORKER_DATA = data
    _WORKER_STRATEGY_NAME = strategy_name
    _WORKER_OPTIMIZATION_GRID = (
        optimization_grid
    )
    _WORKER_RANDOM_SEED = int(
        random_seed
    )


def _evaluate_permutation(
    permutation_number_zero_based: int,
) -> dict[str, Any]:
    if (
        _WORKER_DATA is None
        or _WORKER_STRATEGY_NAME is None
        or _WORKER_OPTIMIZATION_GRID is None
        or _WORKER_RANDOM_SEED is None
    ):
        raise RuntimeError(
            "MCPT worker was not initialized."
        )

    permuted_data = get_permutation(
        _WORKER_DATA,
        seed=(
            _WORKER_RANDOM_SEED
            + permutation_number_zero_based
        ),
    )

    (
        best_parameters,
        best_score,
        _,
    ) = optimize_permuted_market(
        data=permuted_data,
        strategy_name=_WORKER_STRATEGY_NAME,
        optimization_grid=(
            _WORKER_OPTIMIZATION_GRID
        ),
    )

    return {
        "permutation": (
            permutation_number_zero_based + 1
        ),
        "best_bar_profit_factor": (
            float(best_score)
        ),
        **best_parameters,
    }


def _stable_json(
    value: Any,
) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    )


def checkpoint_signature_digest(
    signature: dict[str, Any],
) -> str:
    return hashlib.sha256(
        _stable_json(signature).encode(
            "utf-8"
        )
    ).hexdigest()


def _atomic_text_write(
    path: Path,
    text: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    temporary.write_text(
        text,
        encoding="utf-8",
    )

    temporary.replace(path)


def _atomic_csv_write(
    frame: pd.DataFrame,
    path: Path,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    frame.to_csv(
        temporary,
        index=False,
    )

    temporary.replace(path)


def save_mcpt_checkpoint(
    *,
    checkpoint_directory: Path,
    rows: list[dict[str, Any]],
    base_signature: dict[str, Any],
    target_permutations: int,
    workers: int,
    status: str,
) -> Path:
    checkpoint_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    csv_path = (
        checkpoint_directory
        / "mcpt_checkpoint.csv"
    )

    metadata_path = (
        checkpoint_directory
        / "mcpt_checkpoint_metadata.json"
    )

    frame = pd.DataFrame(rows)

    if not frame.empty:
        frame = (
            frame
            .drop_duplicates(
                subset=["permutation"],
                keep="last",
            )
            .sort_values("permutation")
            .reset_index(drop=True)
        )

    _atomic_csv_write(
        frame,
        csv_path,
    )

    metadata = {
        "schema_version": 1,
        "signature_digest": (
            checkpoint_signature_digest(
                base_signature
            )
        ),
        "base_signature": base_signature,
        "target_permutations": int(
            target_permutations
        ),
        "completed_permutations": int(
            (
                frame["permutation"]
                <= int(target_permutations)
            ).sum()
            if (
                not frame.empty
                and "permutation" in frame.columns
            )
            else 0
        ),
        "stored_permutations": int(
            len(frame)
        ),
        "workers": int(workers),
        "status": status,
        "updated_at_utc": (
            datetime.now(timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        ),
        "csv_file": csv_path.name,
    }

    _atomic_text_write(
        metadata_path,
        json.dumps(
            metadata,
            indent=2,
            default=str,
        ),
    )

    return csv_path


def load_mcpt_checkpoint(
    *,
    checkpoint_directory: Path,
    base_signature: dict[str, Any],
    target_permutations: int,
    parameter_names: tuple[str, ...],
) -> pd.DataFrame:
    csv_path = (
        checkpoint_directory
        / "mcpt_checkpoint.csv"
    )

    metadata_path = (
        checkpoint_directory
        / "mcpt_checkpoint_metadata.json"
    )

    if (
        not csv_path.exists()
        or not metadata_path.exists()
    ):
        return pd.DataFrame()

    try:
        metadata = json.loads(
            metadata_path.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ):
        print(
            "Ignoring unreadable MCPT checkpoint metadata."
        )
        return pd.DataFrame()

    expected_digest = (
        checkpoint_signature_digest(
            base_signature
        )
    )

    if (
        metadata.get("signature_digest")
        != expected_digest
    ):
        print(
            "Ignoring incompatible MCPT checkpoint."
        )
        return pd.DataFrame()

    try:
        frame = pd.read_csv(
            csv_path
        )
    except (
        OSError,
        pd.errors.ParserError,
    ):
        print(
            "Ignoring unreadable MCPT checkpoint data."
        )
        return pd.DataFrame()

    required_columns = {
        "permutation",
        "best_bar_profit_factor",
        *parameter_names,
    }

    if not required_columns.issubset(
        frame.columns
    ):
        print(
            "Ignoring MCPT checkpoint with missing columns."
        )
        return pd.DataFrame()

    frame["permutation"] = pd.to_numeric(
        frame["permutation"],
        errors="coerce",
    )

    frame = frame.dropna(
        subset=[
            "permutation",
            "best_bar_profit_factor",
        ]
    )

    frame["permutation"] = (
        frame["permutation"].astype(int)
    )

    frame = frame[
        frame["permutation"] >= 1
    ]

    if frame["permutation"].duplicated().any():
        print(
            "Ignoring MCPT checkpoint with duplicate "
            "permutation numbers."
        )
        return pd.DataFrame()

    return (
        frame.sort_values(
            "permutation"
        )
        .reset_index(drop=True)
    )


def _rows_from_frame(
    frame: pd.DataFrame,
) -> list[dict[str, Any]]:
    if frame.empty:
        return []

    return frame.to_dict(
        orient="records"
    )


def run_mcpt_engine(
    *,
    in_sample_data: pd.DataFrame,
    strategy_name: str,
    optimization_grid: dict[str, list[Any]],
    random_seed: int,
    permutations: int,
    real_score: float,
    requested_workers: int = 0,
    checkpoint_directory: Path,
    checkpoint_every: int = 10,
    resume: bool = True,
    checkpoint_signature: dict[str, Any],
) -> tuple[
    pd.DataFrame,
    float,
    int,
    McptExecutionInfo,
]:
    if permutations < 1:
        raise ValueError(
            "permutations must be at least 1."
        )

    if checkpoint_every < 1:
        raise ValueError(
            "checkpoint_every must be at least 1."
        )

    strategy = get_strategy(
        strategy_name
    )

    workers = resolve_worker_count(
        requested_workers
    )

    if resume:
        loaded_checkpoint = load_mcpt_checkpoint(
            checkpoint_directory=(
                checkpoint_directory
            ),
            base_signature=(
                checkpoint_signature
            ),
            target_permutations=permutations,
            parameter_names=(
                strategy.parameter_names
            ),
        )
    else:
        loaded_checkpoint = pd.DataFrame()

    resumed = loaded_checkpoint[
        loaded_checkpoint["permutation"]
        <= permutations
    ].copy() if not loaded_checkpoint.empty else pd.DataFrame()

    preserved_future = loaded_checkpoint[
        loaded_checkpoint["permutation"]
        > permutations
    ].copy() if not loaded_checkpoint.empty else pd.DataFrame()

    rows = _rows_from_frame(
        resumed
    )

    preserved_future_rows = _rows_from_frame(
        preserved_future
    )

    completed = {
        int(row["permutation"])
        for row in rows
    }

    missing_zero_based = [
        permutation_number - 1
        for permutation_number in range(
            1,
            permutations + 1,
        )
        if permutation_number not in completed
    ]

    resumed_count = len(rows)
    newly_completed = 0

    optimizer_mode = (
        "shared_indicators_exp003_v1"
        if (
            strategy_name
            == "volatility_compression_breakout_long"
        )
        else "generic_grid_v1"
    )

    def checkpoint_rows(
    ) -> list[dict[str, Any]]:
        return [
            *rows,
            *preserved_future_rows,
        ]

    print()
    print(
        f"Running {permutations:,} in-sample "
        "market permutations..."
    )
    print(
        f"MCPT workers: {workers} "
        f"(requested: {requested_workers})"
    )
    print(
        "Optimizer: "
        f"{optimizer_mode}"
    )

    if resumed_count:
        print(
            "Resuming from checkpoint: "
            f"{resumed_count:,}/{permutations:,} "
            "permutations already complete"
        )

    if missing_zero_based:
        progress = tqdm(
            total=permutations,
            initial=resumed_count,
            desc="MCPT",
        )

        last_checkpoint_count = (
            resumed_count
        )

        if workers == 1:
            _initialize_worker(
                in_sample_data,
                strategy_name,
                optimization_grid,
                random_seed,
            )

            try:
                for permutation_number in (
                    missing_zero_based
                ):
                    row = _evaluate_permutation(
                        permutation_number
                    )

                    rows.append(row)
                    newly_completed += 1
                    progress.update(1)

                    if (
                        len(rows)
                        - last_checkpoint_count
                        >= checkpoint_every
                    ):
                        save_mcpt_checkpoint(
                            checkpoint_directory=(
                                checkpoint_directory
                            ),
                            rows=checkpoint_rows(),
                            base_signature=(
                                checkpoint_signature
                            ),
                            target_permutations=(
                                permutations
                            ),
                            workers=workers,
                            status="running",
                        )

                        last_checkpoint_count = (
                            len(rows)
                        )
            except BaseException:
                save_mcpt_checkpoint(
                    checkpoint_directory=(
                        checkpoint_directory
                    ),
                    rows=checkpoint_rows(),
                    base_signature=(
                        checkpoint_signature
                    ),
                    target_permutations=(
                        permutations
                    ),
                    workers=workers,
                    status="interrupted",
                )

                progress.close()
                raise
        else:
            context = (
                multiprocessing.get_context(
                    "spawn"
                )
            )

            executor = ProcessPoolExecutor(
                max_workers=workers,
                mp_context=context,
                initializer=_initialize_worker,
                initargs=(
                    in_sample_data,
                    strategy_name,
                    optimization_grid,
                    random_seed,
                ),
            )

            future_map: dict[
                Future[dict[str, Any]],
                int,
            ] = {}

            try:
                for permutation_number in (
                    missing_zero_based
                ):
                    future = executor.submit(
                        _evaluate_permutation,
                        permutation_number,
                    )

                    future_map[
                        future
                    ] = permutation_number

                for future in as_completed(
                    future_map
                ):
                    row = future.result()

                    rows.append(row)
                    newly_completed += 1
                    progress.update(1)

                    if (
                        len(rows)
                        - last_checkpoint_count
                        >= checkpoint_every
                    ):
                        save_mcpt_checkpoint(
                            checkpoint_directory=(
                                checkpoint_directory
                            ),
                            rows=checkpoint_rows(),
                            base_signature=(
                                checkpoint_signature
                            ),
                            target_permutations=(
                                permutations
                            ),
                            workers=workers,
                            status="running",
                        )

                        last_checkpoint_count = (
                            len(rows)
                        )
            except BaseException:
                for future in future_map:
                    future.cancel()

                save_mcpt_checkpoint(
                    checkpoint_directory=(
                        checkpoint_directory
                    ),
                    rows=checkpoint_rows(),
                    base_signature=(
                        checkpoint_signature
                    ),
                    target_permutations=(
                        permutations
                    ),
                    workers=workers,
                    status="interrupted",
                )

                executor.shutdown(
                    wait=False,
                    cancel_futures=True,
                )

                progress.close()
                raise
            else:
                executor.shutdown(
                    wait=True
                )
        progress.close()

    results = pd.DataFrame(rows)

    if results.empty:
        raise RuntimeError(
            "MCPT produced no permutation results."
        )

    results = (
        results
        .drop_duplicates(
            subset=["permutation"],
            keep="last",
        )
        .sort_values("permutation")
        .reset_index(drop=True)
    )

    expected_numbers = np.arange(
        1,
        permutations + 1,
    )

    actual_numbers = results[
        "permutation"
    ].to_numpy(dtype=int)

    if not np.array_equal(
        actual_numbers,
        expected_numbers,
    ):
        raise RuntimeError(
            "MCPT result sequence is incomplete "
            "after checkpoint recovery."
        )

    save_mcpt_checkpoint(
        checkpoint_directory=(
            checkpoint_directory
        ),
        rows=[
            *results.to_dict(
                orient="records"
            ),
            *preserved_future_rows,
        ],
        base_signature=(
            checkpoint_signature
        ),
        target_permutations=(
            permutations
        ),
        workers=workers,
        status="complete",
    )

    better_or_equal = int(
        (
            results[
                "best_bar_profit_factor"
            ]
            >= float(real_score)
        ).sum()
    )

    p_value = (
        better_or_equal + 1
    ) / (
        permutations + 1
    )

    info = McptExecutionInfo(
        requested_workers=(
            0
            if requested_workers is None
            else int(requested_workers)
        ),
        workers_used=workers,
        resumed_permutations=(
            resumed_count
        ),
        newly_completed_permutations=(
            newly_completed
        ),
        checkpoint_file=str(
            checkpoint_directory
            / "mcpt_checkpoint.csv"
        ),
        optimizer_mode=optimizer_mode,
    )

    return (
        results,
        float(p_value),
        better_or_equal,
        info,
    )
