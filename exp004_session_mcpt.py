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

from alpaca_historical_data import (
    validate_exp004_clean_data,
)
from exp004_orb_engine import (
    optimize_orb,
)


_WORKER_DATA: pd.DataFrame | None = None
_WORKER_GRID: dict[str, list[Any]] | None = None
_WORKER_STARTING_CAPITAL: float | None = None
_WORKER_COST: float | None = None
_WORKER_MINIMUM_TRADES: int | None = None
_WORKER_RANDOM_SEED: int | None = None


@dataclass(frozen=True)
class Exp004McptInfo:
    requested_workers: int
    workers_used: int
    resumed_permutations: int
    newly_completed_permutations: int
    checkpoint_file: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "requested_workers": (
                self.requested_workers
            ),
            "workers_used": (
                self.workers_used
            ),
            "resumed_permutations": (
                self.resumed_permutations
            ),
            "newly_completed_permutations": (
                self.newly_completed_permutations
            ),
            "checkpoint_file": (
                self.checkpoint_file
            ),
        }


def resolve_exp004_workers(
    requested_workers: int | None,
) -> int:
    logical = max(
        1,
        int(os.cpu_count() or 1),
    )

    if requested_workers in (
        None,
        0,
    ):
        return max(
            1,
            min(
                8,
                logical - 1,
            ),
        )

    workers = int(
        requested_workers
    )

    if workers < 1:
        raise ValueError(
            "Workers must be 0 for "
            "automatic or a positive "
            "integer."
        )

    return min(
        workers,
        logical,
    )


def _component_arrays(
    data: pd.DataFrame,
) -> dict[str, Any]:
    validate_exp004_clean_data(
        data
    )

    sessions = [
        session.copy()
        for _, session in data.groupby(
            "session_date",
            sort=True,
        )
    ]

    session_dates = [
        str(
            session[
                "session_date"
            ].iloc[0]
        )
        for session in sessions
    ]

    indexes = [
        session.index
        for session in sessions
    ]

    open_values = np.stack(
        [
            session["open"].to_numpy(
                dtype=float
            )
            for session in sessions
        ]
    )

    high_values = np.stack(
        [
            session["high"].to_numpy(
                dtype=float
            )
            for session in sessions
        ]
    )

    low_values = np.stack(
        [
            session["low"].to_numpy(
                dtype=float
            )
            for session in sessions
        ]
    )

    close_values = np.stack(
        [
            session["close"].to_numpy(
                dtype=float
            )
            for session in sessions
        ]
    )

    volume_values = np.stack(
        [
            session["volume"].to_numpy(
                dtype=float
            )
            for session in sessions
        ]
    )

    previous_close = np.empty_like(
        open_values
    )

    previous_close[:, 1:] = (
        close_values[:, :-1]
    )

    previous_close[1:, 0] = (
        close_values[:-1, -1]
    )

    previous_close[0, 0] = (
        open_values[0, 0]
    )

    open_gap = np.log(
        open_values / previous_close
    )

    close_move = np.log(
        close_values / open_values
    )

    high_excursion = np.log(
        high_values
        / np.maximum(
            open_values,
            close_values,
        )
    )

    low_excursion = np.log(
        low_values
        / np.minimum(
            open_values,
            close_values,
        )
    )

    return {
        "session_dates": session_dates,
        "indexes": indexes,
        "first_open": float(
            open_values[0, 0]
        ),
        "open_gap": open_gap,
        "close_move": close_move,
        "high_excursion": (
            high_excursion
        ),
        "low_excursion": (
            low_excursion
        ),
        "volume": volume_values,
    }


def permute_exp004_sessions(
    data: pd.DataFrame,
    *,
    seed: int,
) -> pd.DataFrame:
    components = _component_arrays(
        data
    )

    generator = np.random.default_rng(
        int(seed)
    )

    open_gap = components[
        "open_gap"
    ].copy()

    close_move = components[
        "close_move"
    ].copy()

    high_excursion = components[
        "high_excursion"
    ].copy()

    low_excursion = components[
        "low_excursion"
    ].copy()

    volume = components[
        "volume"
    ].copy()

    session_count, slot_count = (
        open_gap.shape
    )

    permuted_open_gap = np.empty_like(
        open_gap
    )

    permuted_close_move = np.empty_like(
        close_move
    )

    permuted_high = np.empty_like(
        high_excursion
    )

    permuted_low = np.empty_like(
        low_excursion
    )

    permuted_volume = np.empty_like(
        volume
    )

    # Session-opening/overnight gaps are
    # permuted separately from intraday
    # open gaps.
    permuted_open_gap[0, 0] = 0.0

    if session_count > 1:
        overnight_order = (
            generator.permutation(
                np.arange(
                    1,
                    session_count,
                )
            )
        )

        permuted_open_gap[
            1:,
            0,
        ] = open_gap[
            overnight_order,
            0,
        ]

    for slot in range(
        slot_count
    ):
        close_order = (
            generator.permutation(
                session_count
            )
        )

        high_order = (
            generator.permutation(
                session_count
            )
        )

        low_order = (
            generator.permutation(
                session_count
            )
        )

        volume_order = (
            generator.permutation(
                session_count
            )
        )

        permuted_close_move[
            :,
            slot,
        ] = close_move[
            close_order,
            slot,
        ]

        permuted_high[
            :,
            slot,
        ] = high_excursion[
            high_order,
            slot,
        ]

        permuted_low[
            :,
            slot,
        ] = low_excursion[
            low_order,
            slot,
        ]

        permuted_volume[
            :,
            slot,
        ] = volume[
            volume_order,
            slot,
        ]

        if slot == 0:
            continue

        open_order = (
            generator.permutation(
                session_count
            )
        )

        permuted_open_gap[
            :,
            slot,
        ] = open_gap[
            open_order,
            slot,
        ]

    synthetic_open = np.empty_like(
        permuted_open_gap
    )

    synthetic_close = np.empty_like(
        permuted_close_move
    )

    synthetic_high = np.empty_like(
        permuted_high
    )

    synthetic_low = np.empty_like(
        permuted_low
    )

    previous_session_close = (
        components["first_open"]
    )

    for session_number in range(
        session_count
    ):
        for slot in range(
            slot_count
        ):
            if (
                session_number == 0
                and slot == 0
            ):
                current_open = (
                    components[
                        "first_open"
                    ]
                )
            elif slot == 0:
                current_open = (
                    previous_session_close
                    * np.exp(
                        permuted_open_gap[
                            session_number,
                            0,
                        ]
                    )
                )
            else:
                current_open = (
                    synthetic_close[
                        session_number,
                        slot - 1,
                    ]
                    * np.exp(
                        permuted_open_gap[
                            session_number,
                            slot,
                        ]
                    )
                )

            current_close = (
                current_open
                * np.exp(
                    permuted_close_move[
                        session_number,
                        slot,
                    ]
                )
            )

            current_high = (
                max(
                    current_open,
                    current_close,
                )
                * np.exp(
                    permuted_high[
                        session_number,
                        slot,
                    ]
                )
            )

            current_low = (
                min(
                    current_open,
                    current_close,
                )
                * np.exp(
                    permuted_low[
                        session_number,
                        slot,
                    ]
                )
            )

            synthetic_open[
                session_number,
                slot,
            ] = current_open

            synthetic_close[
                session_number,
                slot,
            ] = current_close

            synthetic_high[
                session_number,
                slot,
            ] = current_high

            synthetic_low[
                session_number,
                slot,
            ] = current_low

        previous_session_close = (
            synthetic_close[
                session_number,
                -1,
            ]
        )

    frames: list[pd.DataFrame] = []

    for session_number in range(
        session_count
    ):
        index = components[
            "indexes"
        ][session_number]

        frame = pd.DataFrame(
            {
                "open": (
                    synthetic_open[
                        session_number
                    ]
                ),
                "high": (
                    synthetic_high[
                        session_number
                    ]
                ),
                "low": (
                    synthetic_low[
                        session_number
                    ]
                ),
                "close": (
                    synthetic_close[
                        session_number
                    ]
                ),
                "volume": (
                    permuted_volume[
                        session_number
                    ]
                ),
                "session_date": (
                    components[
                        "session_dates"
                    ][session_number]
                ),
                "slot": np.arange(
                    slot_count,
                    dtype=int,
                ),
            },
            index=index,
        )

        frames.append(frame)

    result = pd.concat(
        frames,
        axis=0,
    ).sort_index()

    validate_exp004_clean_data(
        result
    )

    return result


def _worker_initialize(
    data: pd.DataFrame,
    grid: dict[str, list[Any]],
    starting_capital: float,
    total_cost_bps_per_side: float,
    minimum_valid_trades: int,
    random_seed: int,
) -> None:
    global _WORKER_DATA
    global _WORKER_GRID
    global _WORKER_STARTING_CAPITAL
    global _WORKER_COST
    global _WORKER_MINIMUM_TRADES
    global _WORKER_RANDOM_SEED

    _WORKER_DATA = data
    _WORKER_GRID = grid
    _WORKER_STARTING_CAPITAL = (
        float(starting_capital)
    )
    _WORKER_COST = float(
        total_cost_bps_per_side
    )
    _WORKER_MINIMUM_TRADES = int(
        minimum_valid_trades
    )
    _WORKER_RANDOM_SEED = int(
        random_seed
    )


def _worker_evaluate(
    zero_based_permutation: int,
) -> dict[str, Any]:
    if (
        _WORKER_DATA is None
        or _WORKER_GRID is None
        or _WORKER_STARTING_CAPITAL
        is None
        or _WORKER_COST is None
        or _WORKER_MINIMUM_TRADES
        is None
        or _WORKER_RANDOM_SEED is None
    ):
        raise RuntimeError(
            "EXP-004 MCPT worker was "
            "not initialized."
        )

    permuted = permute_exp004_sessions(
        _WORKER_DATA,
        seed=(
            _WORKER_RANDOM_SEED
            + zero_based_permutation
        ),
    )

    try:
        (
            optimization,
            best_parameters,
            best,
        ) = optimize_orb(
            permuted,
            grid=_WORKER_GRID,
            starting_capital=(
                _WORKER_STARTING_CAPITAL
            ),
            total_cost_bps_per_side=(
                _WORKER_COST
            ),
            minimum_valid_trades=(
                _WORKER_MINIMUM_TRADES
            ),
        )
    except RuntimeError as error:
        if (
            "Every ORB parameter combination"
            not in str(error)
        ):
            raise

        return {
            "permutation": (
                zero_based_permutation + 1
            ),
            "best_trade_profit_factor": 0.0,
            "best_total_return_percent": 0.0,
            "best_completed_trades": 0,
            "opening_range_minutes": np.nan,
            "direction_mode": (
                "no_valid_combination"
            ),
        }

    return {
        "permutation": (
            zero_based_permutation + 1
        ),
        "best_trade_profit_factor": (
            float(
                best.summary[
                    "trade_profit_factor"
                ]
            )
        ),
        "best_total_return_percent": (
            float(
                best.summary[
                    "total_return_percent"
                ]
            )
        ),
        "best_completed_trades": (
            int(
                best.summary[
                    "completed_trades"
                ]
            )
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
        default=str,
    )


def signature_digest(
    signature: dict[str, Any],
) -> str:
    return hashlib.sha256(
        _stable_json(
            signature
        ).encode("utf-8")
    ).hexdigest()


def _atomic_csv(
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


def _atomic_json(
    payload: dict[str, Any],
    path: Path,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    temporary.write_text(
        json.dumps(
            payload,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    temporary.replace(path)


def _load_checkpoint(
    *,
    directory: Path,
    signature: dict[str, Any],
    permutations: int,
) -> pd.DataFrame:
    csv_path = (
        directory
        / "mcpt_checkpoint.csv"
    )

    metadata_path = (
        directory
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

        frame = pd.read_csv(
            csv_path
        )
    except (
        OSError,
        json.JSONDecodeError,
        pd.errors.ParserError,
    ):
        return pd.DataFrame()

    if (
        metadata.get(
            "signature_digest"
        )
        != signature_digest(signature)
    ):
        return pd.DataFrame()

    required = {
        "permutation",
        "best_trade_profit_factor",
        "opening_range_minutes",
        "direction_mode",
    }

    if not required.issubset(
        frame.columns
    ):
        return pd.DataFrame()

    frame["permutation"] = (
        pd.to_numeric(
            frame["permutation"],
            errors="coerce",
        )
    )

    frame = frame.dropna(
        subset=[
            "permutation",
            "best_trade_profit_factor",
        ]
    )

    frame["permutation"] = (
        frame["permutation"].astype(int)
    )

    frame = frame[
        frame["permutation"].between(
            1,
            permutations,
        )
    ]

    if frame[
        "permutation"
    ].duplicated().any():
        return pd.DataFrame()

    return (
        frame.sort_values(
            "permutation"
        )
        .reset_index(drop=True)
    )


def _save_checkpoint(
    *,
    directory: Path,
    rows: list[dict[str, Any]],
    signature: dict[str, Any],
    permutations: int,
    workers: int,
    status: str,
) -> None:
    frame = pd.DataFrame(rows)

    if not frame.empty:
        frame = (
            frame.drop_duplicates(
                subset=["permutation"],
                keep="last",
            )
            .sort_values(
                "permutation"
            )
            .reset_index(drop=True)
        )

    csv_path = (
        directory
        / "mcpt_checkpoint.csv"
    )

    metadata_path = (
        directory
        / "mcpt_checkpoint_metadata.json"
    )

    _atomic_csv(
        frame,
        csv_path,
    )

    _atomic_json(
        {
            "schema_version": 1,
            "signature_digest": (
                signature_digest(
                    signature
                )
            ),
            "signature": signature,
            "target_permutations": int(
                permutations
            ),
            "completed_permutations": int(
                len(frame)
            ),
            "workers": int(
                workers
            ),
            "status": status,
            "updated_at_utc": (
                datetime.now(
                    timezone.utc
                ).isoformat(
                    timespec="seconds"
                )
            ),
        },
        metadata_path,
    )


def run_exp004_mcpt(
    *,
    data: pd.DataFrame,
    grid: dict[str, list[Any]],
    starting_capital: float,
    total_cost_bps_per_side: float,
    minimum_valid_trades: int,
    random_seed: int,
    permutations: int,
    real_best_profit_factor: float,
    requested_workers: int = 0,
    checkpoint_directory: Path,
    checkpoint_signature: dict[str, Any],
    checkpoint_every: int = 1,
    resume: bool = True,
) -> tuple[
    pd.DataFrame,
    float,
    int,
    Exp004McptInfo,
]:
    validate_exp004_clean_data(
        data
    )

    if permutations < 1:
        raise ValueError(
            "permutations must be positive."
        )

    if checkpoint_every < 1:
        raise ValueError(
            "checkpoint_every must be "
            "positive."
        )

    workers = resolve_exp004_workers(
        requested_workers
    )

    resumed = (
        _load_checkpoint(
            directory=(
                checkpoint_directory
            ),
            signature=(
                checkpoint_signature
            ),
            permutations=permutations,
        )
        if resume
        else pd.DataFrame()
    )

    rows = resumed.to_dict(
        orient="records"
    )

    completed = {
        int(row["permutation"])
        for row in rows
    }

    missing = [
        number - 1
        for number in range(
            1,
            permutations + 1,
        )
        if number not in completed
    ]

    resumed_count = len(rows)
    newly_completed = 0
    last_checkpoint_count = (
        resumed_count
    )

    print()
    print(
        f"Running {permutations:,} "
        "session-aware market "
        "permutations..."
    )
    print(
        f"MCPT workers: {workers} "
        f"(requested: "
        f"{requested_workers})"
    )

    if resumed_count:
        print(
            "Resuming checkpoint: "
            f"{resumed_count}/"
            f"{permutations}"
        )

    progress = tqdm(
        total=permutations,
        initial=resumed_count,
        desc="EXP-004 MCPT",
    )

    try:
        if workers == 1:
            _worker_initialize(
                data,
                grid,
                starting_capital,
                total_cost_bps_per_side,
                minimum_valid_trades,
                random_seed,
            )

            for zero_based in missing:
                rows.append(
                    _worker_evaluate(
                        zero_based
                    )
                )

                newly_completed += 1
                progress.update(1)

                if (
                    len(rows)
                    - last_checkpoint_count
                    >= checkpoint_every
                ):
                    _save_checkpoint(
                        directory=(
                            checkpoint_directory
                        ),
                        rows=rows,
                        signature=(
                            checkpoint_signature
                        ),
                        permutations=(
                            permutations
                        ),
                        workers=workers,
                        status="running",
                    )

                    last_checkpoint_count = (
                        len(rows)
                    )
        else:
            context = (
                multiprocessing.get_context(
                    "spawn"
                )
            )

            executor = (
                ProcessPoolExecutor(
                    max_workers=workers,
                    mp_context=context,
                    initializer=(
                        _worker_initialize
                    ),
                    initargs=(
                        data,
                        grid,
                        starting_capital,
                        total_cost_bps_per_side,
                        minimum_valid_trades,
                        random_seed,
                    ),
                )
            )

            futures: dict[
                Future[dict[str, Any]],
                int,
            ] = {}

            try:
                for zero_based in missing:
                    future = executor.submit(
                        _worker_evaluate,
                        zero_based,
                    )

                    futures[
                        future
                    ] = zero_based

                for future in as_completed(
                    futures
                ):
                    rows.append(
                        future.result()
                    )

                    newly_completed += 1
                    progress.update(1)

                    if (
                        len(rows)
                        - last_checkpoint_count
                        >= checkpoint_every
                    ):
                        _save_checkpoint(
                            directory=(
                                checkpoint_directory
                            ),
                            rows=rows,
                            signature=(
                                checkpoint_signature
                            ),
                            permutations=(
                                permutations
                            ),
                            workers=workers,
                            status="running",
                        )

                        last_checkpoint_count = (
                            len(rows)
                        )
            except BaseException:
                for future in futures:
                    future.cancel()

                executor.shutdown(
                    wait=False,
                    cancel_futures=True,
                )
                raise
            else:
                executor.shutdown(
                    wait=True
                )
    except BaseException:
        _save_checkpoint(
            directory=(
                checkpoint_directory
            ),
            rows=rows,
            signature=(
                checkpoint_signature
            ),
            permutations=permutations,
            workers=workers,
            status="interrupted",
        )

        raise
    finally:
        progress.close()

    results = pd.DataFrame(
        rows
    )

    results = (
        results.drop_duplicates(
            subset=["permutation"],
            keep="last",
        )
        .sort_values(
            "permutation"
        )
        .reset_index(drop=True)
    )

    expected = np.arange(
        1,
        permutations + 1,
    )

    actual = results[
        "permutation"
    ].to_numpy(dtype=int)

    if not np.array_equal(
        expected,
        actual,
    ):
        raise RuntimeError(
            "EXP-004 MCPT results are "
            "incomplete."
        )

    _save_checkpoint(
        directory=(
            checkpoint_directory
        ),
        rows=results.to_dict(
            orient="records"
        ),
        signature=(
            checkpoint_signature
        ),
        permutations=permutations,
        workers=workers,
        status="complete",
    )

    better_or_equal = int(
        (
            results[
                "best_trade_profit_factor"
            ]
            >= float(
                real_best_profit_factor
            )
        ).sum()
    )

    p_value = (
        better_or_equal + 1
    ) / (
        permutations + 1
    )

    info = Exp004McptInfo(
        requested_workers=int(
            requested_workers
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
    )

    return (
        results,
        float(p_value),
        better_or_equal,
        info,
    )
