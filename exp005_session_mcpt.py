from __future__ import annotations

from concurrent.futures import (
    Future,
    ProcessPoolExecutor,
    as_completed,
)
from dataclasses import dataclass
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from exp005_futures_orb import (
    run_futures_orb,
)
from exp005_quantower_import import (
    EXPECTED_FIVE_MINUTE_BARS,
    EXPECTED_ONE_MINUTE_BARS,
    dataframe_sha256,
)


ENGINE_VERSION = "exp005_session_mcpt_v2"
_REQUIRED_ONE_MINUTE_COLUMNS = {
    "open",
    "high",
    "low",
    "close",
    "volume",
    "session_date",
    "minute_slot",
}


@dataclass(frozen=True)
class Exp005PermutationComponents:
    session_dates: tuple[str, ...]
    five_minute_index_ns: np.ndarray
    first_open: float
    open_gap: np.ndarray
    close_move: np.ndarray
    high_excursion: np.ndarray
    low_excursion: np.ndarray
    volume: np.ndarray

    @property
    def session_count(self) -> int:
        return int(
            self.open_gap.shape[0]
        )


@dataclass(frozen=True)
class Exp005McptRunInfo:
    requested_workers: int
    workers_used: int
    resumed_permutations: int
    newly_completed_permutations: int
    checkpoint_file: str
    signature: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "requested_workers": (
                self.requested_workers
            ),
            "workers_used": self.workers_used,
            "resumed_permutations": (
                self.resumed_permutations
            ),
            "newly_completed_permutations": (
                self.newly_completed_permutations
            ),
            "checkpoint_file": (
                self.checkpoint_file
            ),
            "signature": self.signature,
        }


_WORKER_COMPONENTS: (
    Exp005PermutationComponents
    | None
) = None
_WORKER_RANDOM_SEED: int | None = None


def resolve_exp005_workers(
    requested_workers: int | None,
) -> int:
    logical = max(
        1,
        int(
            os.cpu_count()
            or 1
        ),
    )

    if requested_workers in {
        None,
        0,
    }:
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
            "Workers must be 0 for automatic "
            "selection or a positive integer."
        )

    return min(
        workers,
        logical,
    )


def validate_one_minute_data(
    data: pd.DataFrame,
) -> None:
    missing = (
        _REQUIRED_ONE_MINUTE_COLUMNS
        .difference(data.columns)
    )

    if missing:
        raise ValueError(
            "EXP-005 one-minute data is missing: "
            f"{sorted(missing)}"
        )

    if not isinstance(
        data.index,
        pd.DatetimeIndex,
    ):
        raise TypeError(
            "EXP-005 one-minute data must use "
            "a DatetimeIndex."
        )

    if data.index.tz is None:
        raise ValueError(
            "EXP-005 one-minute timestamps "
            "must be timezone-aware."
        )

    if (
        data.index.has_duplicates
        or not data.index.is_monotonic_increasing
    ):
        raise ValueError(
            "EXP-005 one-minute timestamps must "
            "be unique and sorted."
        )

    counts = data.groupby(
        "session_date",
        sort=True,
    ).size()

    if (
        counts.empty
        or not counts.eq(
            EXPECTED_ONE_MINUTE_BARS
        ).all()
    ):
        raise ValueError(
            "Every EXP-005 one-minute session "
            "must contain 390 bars."
        )

    for session_date, session in data.groupby(
        "session_date",
        sort=True,
    ):
        slots = session[
            "minute_slot"
        ].to_numpy(
            dtype=int
        )

        if not np.array_equal(
            slots,
            np.arange(
                EXPECTED_ONE_MINUTE_BARS,
                dtype=int,
            ),
        ):
            raise ValueError(
                f"{session_date} minute slots "
                "are not 0 through 389."
            )


def build_permutation_components(
    data: pd.DataFrame,
) -> Exp005PermutationComponents:
    validate_one_minute_data(data)

    sessions = [
        session.copy()
        for _, session in data.groupby(
            "session_date",
            sort=True,
        )
    ]

    session_dates = tuple(
        str(
            session[
                "session_date"
            ].iloc[0]
        )
        for session in sessions
    )

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
        open_values
        / previous_close
    )
    close_move = np.log(
        close_values
        / open_values
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

    five_minute_indexes = []

    for session in sessions:
        index_ns = (
            session.index
            .asi8
            .reshape(
                EXPECTED_FIVE_MINUTE_BARS,
                5,
            )[:, 0]
        )
        five_minute_indexes.append(
            index_ns
        )

    return Exp005PermutationComponents(
        session_dates=session_dates,
        five_minute_index_ns=np.stack(
            five_minute_indexes
        ),
        first_open=float(
            open_values[0, 0]
        ),
        open_gap=open_gap,
        close_move=close_move,
        high_excursion=(
            high_excursion
        ),
        low_excursion=(
            low_excursion
        ),
        volume=volume_values,
    )


def _permuted_component_arrays(
    components: Exp005PermutationComponents,
    *,
    seed: int,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    generator = np.random.default_rng(
        int(seed)
    )
    session_count, slot_count = (
        components.open_gap.shape
    )

    permuted_open_gap = np.empty_like(
        components.open_gap
    )
    permuted_close_move = np.empty_like(
        components.close_move
    )
    permuted_high = np.empty_like(
        components.high_excursion
    )
    permuted_low = np.empty_like(
        components.low_excursion
    )
    permuted_volume = np.empty_like(
        components.volume
    )

    # The cash-session opening gap is never mixed
    # with intraday one-minute gaps.
    opening_order = generator.permutation(
        session_count
    )
    permuted_open_gap[:, 0] = (
        components.open_gap[
            opening_order,
            0,
        ]
    )

    for slot in range(
        1,
        slot_count,
    ):
        order = generator.permutation(
            session_count
        )
        permuted_open_gap[:, slot] = (
            components.open_gap[
                order,
                slot,
            ]
        )

    # Relative close movement, high excursion,
    # low excursion and volume are independently
    # permuted across complete sessions within
    # each locked one-minute time slot.
    for slot in range(slot_count):
        close_order = generator.permutation(
            session_count
        )
        high_order = generator.permutation(
            session_count
        )
        low_order = generator.permutation(
            session_count
        )
        volume_order = generator.permutation(
            session_count
        )

        permuted_close_move[:, slot] = (
            components.close_move[
                close_order,
                slot,
            ]
        )
        permuted_high[:, slot] = (
            components.high_excursion[
                high_order,
                slot,
            ]
        )
        permuted_low[:, slot] = (
            components.low_excursion[
                low_order,
                slot,
            ]
        )
        permuted_volume[:, slot] = (
            components.volume[
                volume_order,
                slot,
            ]
        )

    return (
        permuted_open_gap,
        permuted_close_move,
        permuted_high,
        permuted_low,
        permuted_volume,
    )


def reconstruct_permuted_five_minute_data(
    components: Exp005PermutationComponents,
    *,
    seed: int,
) -> pd.DataFrame:
    (
        open_gap,
        close_move,
        high_excursion,
        low_excursion,
        volume,
    ) = _permuted_component_arrays(
        components,
        seed=seed,
    )

    flat_gap = open_gap.reshape(-1)
    flat_close_move = (
        close_move.reshape(-1)
    )

    log_open = np.empty_like(
        flat_gap
    )
    log_close = np.empty_like(
        flat_gap
    )

    log_open[0] = np.log(
        components.first_open
    )
    log_close[0] = (
        log_open[0]
        + flat_close_move[0]
    )

    increments = (
        flat_gap[1:]
        + flat_close_move[1:]
    )

    log_close[1:] = (
        log_close[0]
        + np.cumsum(increments)
    )
    log_open[1:] = (
        log_close[:-1]
        + flat_gap[1:]
    )

    open_values = np.exp(
        log_open
    ).reshape(
        components.open_gap.shape
    )
    close_values = np.exp(
        log_close
    ).reshape(
        components.open_gap.shape
    )
    high_values = (
        np.maximum(
            open_values,
            close_values,
        )
        * np.exp(high_excursion)
    )
    low_values = (
        np.minimum(
            open_values,
            close_values,
        )
        * np.exp(low_excursion)
    )

    shape = (
        components.session_count,
        EXPECTED_FIVE_MINUTE_BARS,
        5,
    )

    open_5m = open_values.reshape(
        shape
    )[:, :, 0]
    high_5m = high_values.reshape(
        shape
    ).max(axis=2)
    low_5m = low_values.reshape(
        shape
    ).min(axis=2)
    close_5m = close_values.reshape(
        shape
    )[:, :, -1]
    volume_5m = volume.reshape(
        shape
    ).sum(axis=2)

    session_dates = np.repeat(
        np.array(
            components.session_dates,
            dtype=object,
        ),
        EXPECTED_FIVE_MINUTE_BARS,
    )
    slots = np.tile(
        np.arange(
            EXPECTED_FIVE_MINUTE_BARS,
            dtype=int,
        ),
        components.session_count,
    )
    index = pd.to_datetime(
        components.five_minute_index_ns
        .reshape(-1),
        utc=True,
    )

    result = pd.DataFrame(
        {
            "open": open_5m.reshape(-1),
            "high": high_5m.reshape(-1),
            "low": low_5m.reshape(-1),
            "close": close_5m.reshape(-1),
            "volume": volume_5m.reshape(-1),
            "session_date": session_dates,
            "slot": slots,
        },
        index=index,
    )
    result.index.name = "timestamp"

    return result


def permutation_seed(
    base_seed: int,
    zero_based_permutation: int,
) -> int:
    state = np.random.SeedSequence(
        [
            int(base_seed),
            int(zero_based_permutation),
        ]
    ).generate_state(
        1,
        dtype=np.uint32,
    )

    return int(state[0])


def run_one_permutation(
    components: Exp005PermutationComponents,
    *,
    zero_based_permutation: int,
    base_seed: int,
) -> dict[str, Any]:
    seed = permutation_seed(
        base_seed,
        zero_based_permutation,
    )
    market = (
        reconstruct_permuted_five_minute_data(
            components,
            seed=seed,
        )
    )
    result = run_futures_orb(
        market,
        symbol="NQ",
        slippage_ticks_per_side=1.0,
        validate_data=False,
    )

    return {
        "permutation": int(
            zero_based_permutation + 1
        ),
        "seed": int(seed),
        "trade_profit_factor": float(
            result.summary[
                "trade_profit_factor"
            ]
        ),
        "net_profit_usd": float(
            result.summary[
                "net_profit_usd"
            ]
        ),
        "completed_trades": int(
            result.summary[
                "completed_trades"
            ]
        ),
        "long_trades": int(
            result.summary[
                "long_trades"
            ]
        ),
        "short_trades": int(
            result.summary[
                "short_trades"
            ]
        ),
    }


def _worker_initialize(
    components: Exp005PermutationComponents,
    base_seed: int,
) -> None:
    global _WORKER_COMPONENTS
    global _WORKER_RANDOM_SEED

    _WORKER_COMPONENTS = components
    _WORKER_RANDOM_SEED = int(
        base_seed
    )


def _worker_run(
    zero_based_permutation: int,
) -> dict[str, Any]:
    if (
        _WORKER_COMPONENTS is None
        or _WORKER_RANDOM_SEED is None
    ):
        raise RuntimeError(
            "EXP-005 MCPT worker was not initialized."
        )

    return run_one_permutation(
        _WORKER_COMPONENTS,
        zero_based_permutation=(
            zero_based_permutation
        ),
        base_seed=_WORKER_RANDOM_SEED,
    )


def _stable_json(
    value: Any,
) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def mcpt_signature(
    *,
    one_minute_fingerprint: str,
    permutations: int,
    base_seed: int,
) -> str:
    payload = {
        "engine_version": ENGINE_VERSION,
        "experiment_id": "EXP-005",
        "market": "NQ",
        "one_minute_fingerprint": (
            one_minute_fingerprint
        ),
        "permutations": int(
            permutations
        ),
        "base_seed": int(
            base_seed
        ),
        "opening_range_minutes": 15,
        "direction_mode": "both",
        "optimization_inside_permutation": False,
        "slippage_ticks_per_side": 1.0,
    }

    return hashlib.sha256(
        _stable_json(payload).encode(
            "utf-8"
        )
    ).hexdigest()


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
            allow_nan=True,
        ),
        encoding="utf-8",
    )
    temporary.replace(path)


def _load_checkpoint(
    path: Path,
    *,
    signature: str,
) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    payload = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    if payload.get(
        "signature"
    ) != signature:
        raise RuntimeError(
            "An incompatible EXP-005 MCPT checkpoint "
            "exists. Do not mix research runs."
        )

    rows = list(
        payload.get(
            "rows",
            [],
        )
    )

    rows.sort(
        key=lambda row: int(
            row["permutation"]
        )
    )

    return rows


def _save_checkpoint(
    path: Path,
    *,
    signature: str,
    rows: list[dict[str, Any]],
) -> None:
    ordered = sorted(
        rows,
        key=lambda row: int(
            row["permutation"]
        ),
    )
    _atomic_json(
        {
            "experiment_id": "EXP-005",
            "engine_version": ENGINE_VERSION,
            "signature": signature,
            "rows": ordered,
        },
        path,
    )


def run_exp005_mcpt(
    one_minute_data: pd.DataFrame,
    *,
    real_trade_profit_factor: float,
    permutations: int = 25,
    base_seed: int = 45,
    requested_workers: int | None = 0,
    checkpoint_file: Path,
    one_minute_fingerprint: str | None = None,
) -> tuple[
    pd.DataFrame,
    float,
    Exp005McptRunInfo,
]:
    if int(permutations) != 25:
        raise ValueError(
            "EXP-005 quick MCPT is locked to "
            "exactly 25 permutations."
        )

    if int(base_seed) != 45:
        raise ValueError(
            "EXP-005 MCPT seed is locked to 45."
        )

    validate_one_minute_data(
        one_minute_data
    )

    fingerprint = (
        dataframe_sha256(
            one_minute_data
        )
        if one_minute_fingerprint is None
        else str(
            one_minute_fingerprint
        )
    )
    signature = mcpt_signature(
        one_minute_fingerprint=fingerprint,
        permutations=int(permutations),
        base_seed=int(base_seed),
    )
    existing = _load_checkpoint(
        checkpoint_file,
        signature=signature,
    )

    by_number = {
        int(row["permutation"]): row
        for row in existing
    }
    missing = [
        index
        for index in range(
            int(permutations)
        )
        if index + 1 not in by_number
    ]
    components = (
        build_permutation_components(
            one_minute_data
        )
    )
    workers = resolve_exp005_workers(
        requested_workers
    )
    newly_completed = 0

    print()
    print(
        "Running 25 locked EXP-005 "
        "session-aware NQ permutations..."
    )
    print(
        f"MCPT workers: {workers} "
        f"(requested: {requested_workers})"
    )

    if existing:
        print(
            "Resuming from checkpoint: "
            f"{len(existing)}/25 complete"
        )

    if workers == 1:
        for zero_based in missing:
            row = run_one_permutation(
                components,
                zero_based_permutation=(
                    zero_based
                ),
                base_seed=int(base_seed),
            )
            by_number[
                int(row["permutation"])
            ] = row
            newly_completed += 1
            _save_checkpoint(
                checkpoint_file,
                signature=signature,
                rows=list(
                    by_number.values()
                ),
            )
            print(
                "EXP-005 MCPT: "
                f"{len(by_number)}/25"
            )
    elif missing:
        context = (
            multiprocessing.get_context(
                "spawn"
            )
        )

        with ProcessPoolExecutor(
            max_workers=workers,
            mp_context=context,
            initializer=_worker_initialize,
            initargs=(
                components,
                int(base_seed),
            ),
        ) as executor:
            futures: dict[
                Future[dict[str, Any]],
                int,
            ] = {
                executor.submit(
                    _worker_run,
                    zero_based,
                ): zero_based
                for zero_based in missing
            }

            for future in as_completed(
                futures
            ):
                row = future.result()
                by_number[
                    int(
                        row["permutation"]
                    )
                ] = row
                newly_completed += 1
                _save_checkpoint(
                    checkpoint_file,
                    signature=signature,
                    rows=list(
                        by_number.values()
                    ),
                )
                print(
                    "EXP-005 MCPT: "
                    f"{len(by_number)}/25"
                )

    rows = [
        by_number[number]
        for number in range(
            1,
            int(permutations) + 1,
        )
    ]
    frame = pd.DataFrame(rows)

    if len(frame) != int(permutations):
        raise RuntimeError(
            "EXP-005 MCPT did not complete "
            "all 25 permutations."
        )

    real_pf = float(
        real_trade_profit_factor
    )
    permutation_pf = frame[
        "trade_profit_factor"
    ].to_numpy(
        dtype=float
    )

    comparable = np.where(
        np.isnan(permutation_pf),
        -np.inf,
        permutation_pf,
    )
    real_comparable = (
        -np.inf
        if np.isnan(real_pf)
        else real_pf
    )
    exceedances = int(
        np.count_nonzero(
            comparable
            >= real_comparable
        )
    )
    p_value = (
        1.0 + exceedances
    ) / (
        1.0
        + int(permutations)
    )

    frame[
        "real_trade_profit_factor"
    ] = real_pf
    frame["permutation_ge_real"] = (
        comparable
        >= real_comparable
    )

    info = Exp005McptRunInfo(
        requested_workers=int(
            requested_workers
            or 0
        ),
        workers_used=int(workers),
        resumed_permutations=int(
            len(existing)
        ),
        newly_completed_permutations=int(
            newly_completed
        ),
        checkpoint_file=str(
            checkpoint_file.resolve()
        ),
        signature=signature,
    )

    return (
        frame,
        float(p_value),
        info,
    )
