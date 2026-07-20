from __future__ import annotations

from concurrent.futures import Future, ProcessPoolExecutor, as_completed
from dataclasses import dataclass
import hashlib
import json
import multiprocessing
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from exp005_session_mcpt import permutation_seed, resolve_exp005_workers
from exp009_engine import Exp009Arrays
from exp012_engine import (
    CASH_START_MINUTE,
    CONTEXT_END_MINUTE,
    PREMARKET_START_MINUTE,
    Exp012Arrays,
    locked_exp012_candidates,
    run_exp012_candidate,
)
from exp013_selection import FINALIST_IDS
from extended_session_data import SESSION_QUALITY_FILE


ENGINE_VERSION = "exp013_extended_discovery_wide_mcpt_v1"
LOCKED_PERMUTATIONS = 1_000
LOCKED_BASE_SEED = 53


@dataclass(frozen=True)
class Exp013PermutationComponents:
    session_dates: np.ndarray
    first_open: float
    open_gap: np.ndarray
    close_move: np.ndarray
    high_excursion: np.ndarray
    low_excursion: np.ndarray
    volume: np.ndarray
    previous_session_index: np.ndarray


@dataclass(frozen=True)
class Exp013McptRunInfo:
    requested_workers: int
    workers_used: int
    resumed_permutations: int
    newly_completed_permutations: int
    checkpoint_file: str
    signature: str
    engine_version: str = ENGINE_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "requested_workers": self.requested_workers,
            "workers_used": self.workers_used,
            "resumed_permutations": self.resumed_permutations,
            "newly_completed_permutations": (
                self.newly_completed_permutations
            ),
            "checkpoint_file": self.checkpoint_file,
            "signature": self.signature,
            "engine_version": self.engine_version,
        }


def _calendar_dates(values: Iterable[str] | None) -> list[str]:
    if values is not None:
        return sorted({str(value) for value in values})
    frame = pd.read_csv(SESSION_QUALITY_FILE, usecols=["session_date"])
    return sorted(frame["session_date"].astype(str).unique())


def build_exp013_permutation_components(
    data: pd.DataFrame,
    *,
    calendar_session_dates: Iterable[str] | None = None,
) -> Exp013PermutationComponents:
    required = {
        "open",
        "high",
        "low",
        "close",
        "volume",
        "session_date",
        "session_minute",
    }
    missing = sorted(required.difference(data.columns))
    if missing:
        raise ValueError(
            "EXP-013 MCPT data are missing: " + ", ".join(missing)
        )
    local = data.copy()
    local["session_date"] = local["session_date"].astype(str)
    years = pd.to_datetime(local["session_date"]).dt.year
    local = local.loc[years.between(2020, 2025)]
    local = local.loc[
        local["session_minute"].between(0, CONTEXT_END_MINUTE - 1)
    ].sort_values(["session_date", "session_minute"], kind="stable")
    if local.duplicated(["session_date", "session_minute"]).any():
        raise ValueError("EXP-013 MCPT data contain duplicate minutes.")
    counts = local.groupby("session_date", sort=True).size()
    if counts.empty or not counts.eq(CONTEXT_END_MINUTE).all():
        raise ValueError(
            "EXP-013 MCPT requires 1,320 active minutes per session."
        )

    shape = (len(counts), CONTEXT_END_MINUTE)
    slots = local["session_minute"].to_numpy(dtype=int).reshape(shape)
    if not np.all(slots == np.arange(CONTEXT_END_MINUTE)):
        raise ValueError("EXP-013 MCPT minute-slot sequence changed.")
    session_dates = (
        local["session_date"].to_numpy(dtype=object).reshape(shape)[:, 0]
    )
    opening = local["open"].to_numpy(dtype=float).reshape(shape)
    high = local["high"].to_numpy(dtype=float).reshape(shape)
    low = local["low"].to_numpy(dtype=float).reshape(shape)
    close = local["close"].to_numpy(dtype=float).reshape(shape)
    volume = local["volume"].to_numpy(dtype=float).reshape(shape)
    if (
        not np.all(np.isfinite(opening))
        or not np.all(np.isfinite(high))
        or not np.all(np.isfinite(low))
        or not np.all(np.isfinite(close))
        or np.any(opening <= 0)
        or np.any(high <= 0)
        or np.any(low <= 0)
        or np.any(close <= 0)
        or np.any(volume < 0)
    ):
        raise ValueError("EXP-013 MCPT requires finite positive OHLC data.")

    log_open = np.log(opening)
    log_close = np.log(close)
    flat_open = log_open.reshape(-1)
    flat_close = log_close.reshape(-1)
    flat_gap = np.zeros_like(flat_open)
    flat_gap[1:] = flat_open[1:] - flat_close[:-1]
    open_gap = flat_gap.reshape(shape)
    close_move = log_close - log_open
    high_excursion = np.log(high) - np.log(np.maximum(opening, close))
    low_excursion = np.log(low) - np.log(np.minimum(opening, close))

    calendar = _calendar_dates(calendar_session_dates)
    calendar_position = {
        value: position for position, value in enumerate(calendar)
    }
    included = {
        str(value): position for position, value in enumerate(session_dates)
    }
    previous = np.full(len(session_dates), -1, dtype=np.int32)
    for index, value in enumerate(session_dates):
        position = calendar_position.get(str(value))
        if position is None or position == 0:
            continue
        previous[index] = int(included.get(calendar[position - 1], -1))

    return Exp013PermutationComponents(
        session_dates=session_dates.copy(),
        first_open=float(opening[0, 0]),
        open_gap=open_gap,
        close_move=close_move,
        high_excursion=np.maximum(high_excursion, 0.0),
        low_excursion=np.minimum(low_excursion, 0.0),
        volume=volume,
        previous_session_index=previous,
    )


def _permute_by_exact_slot(
    values: np.ndarray,
    generator: np.random.Generator,
) -> np.ndarray:
    order = np.argsort(generator.random(values.shape), axis=0)
    return np.take_along_axis(values, order, axis=0)


def _build_cash_arrays(
    *,
    session_dates: np.ndarray,
    opening: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    volume: np.ndarray,
) -> Exp009Arrays:
    five_shape = (len(session_dates), 78, 5)
    open_5m = opening.reshape(five_shape)[:, :, 0]
    high_5m = high.reshape(five_shape).max(axis=2)
    low_5m = low.reshape(five_shape).min(axis=2)
    close_5m = close.reshape(five_shape)[:, :, -1]
    volume_5m = volume.reshape(five_shape).sum(axis=2)
    typical = (high + low + close) / 3.0
    cumulative_volume = np.cumsum(volume, axis=1)
    safe_volume = np.where(cumulative_volume > 0, cumulative_volume, np.nan)
    cumulative_pv = np.cumsum(typical * volume, axis=1)
    cumulative_p2v = np.cumsum(typical * typical * volume, axis=1)
    vwap = cumulative_pv / safe_volume
    variance = np.maximum(cumulative_p2v / safe_volume - vwap * vwap, 0.0)
    return Exp009Arrays(
        session_dates=session_dates.copy(),
        years=pd.to_datetime(session_dates).year.to_numpy(dtype=int),
        open=opening,
        high=high,
        low=low,
        close=close,
        volume=volume,
        open_5m=open_5m,
        high_5m=high_5m,
        low_5m=low_5m,
        close_5m=close_5m,
        volume_5m=volume_5m,
        vwap_5m=vwap[:, 4::5],
        vwap_std_5m=np.sqrt(variance[:, 4::5]),
    )


def _safe_fraction(
    numerator: np.ndarray,
    denominator: np.ndarray,
) -> np.ndarray:
    result = np.full(len(numerator), np.nan, dtype=float)
    valid = (
        np.isfinite(numerator)
        & np.isfinite(denominator)
        & (denominator > 0)
    )
    result[valid] = np.abs(numerator[valid]) / denominator[valid]
    return result


def _direction(values: np.ndarray) -> np.ndarray:
    return np.where(values > 0, 1, np.where(values < 0, -1, 0)).astype(
        np.int8
    )


def reconstruct_permuted_exp013_arrays(
    components: Exp013PermutationComponents,
    *,
    seed: int,
) -> Exp012Arrays:
    generator = np.random.default_rng(int(seed))
    open_gap = _permute_by_exact_slot(components.open_gap, generator)
    close_move = _permute_by_exact_slot(components.close_move, generator)
    high_excursion = _permute_by_exact_slot(
        components.high_excursion, generator
    )
    low_excursion = _permute_by_exact_slot(
        components.low_excursion, generator
    )
    volume = _permute_by_exact_slot(components.volume, generator)

    flat_gap = open_gap.reshape(-1)
    flat_move = close_move.reshape(-1)
    log_open = np.empty_like(flat_gap)
    log_close = np.empty_like(flat_gap)
    log_open[0] = np.log(components.first_open)
    log_close[0] = log_open[0] + flat_move[0]
    log_close[1:] = log_close[0] + np.cumsum(
        flat_gap[1:] + flat_move[1:]
    )
    log_open[1:] = log_close[:-1] + flat_gap[1:]
    shape = components.open_gap.shape
    opening = np.exp(log_open).reshape(shape)
    close = np.exp(log_close).reshape(shape)
    high = np.maximum(opening, close) * np.exp(high_excursion)
    low = np.minimum(opening, close) * np.exp(low_excursion)

    cash_slice = slice(CASH_START_MINUTE, CONTEXT_END_MINUTE)
    cash = _build_cash_arrays(
        session_dates=components.session_dates,
        opening=opening[:, cash_slice],
        high=high[:, cash_slice],
        low=low[:, cash_slice],
        close=close[:, cash_slice],
        volume=volume[:, cash_slice],
    )
    overnight_open = opening[:, 0]
    overnight_close = close[:, CASH_START_MINUTE - 1]
    overnight_high = high[:, :CASH_START_MINUTE].max(axis=1)
    overnight_low = low[:, :CASH_START_MINUTE].min(axis=1)
    overnight_move = overnight_close - overnight_open
    premarket_open = opening[:, PREMARKET_START_MINUTE]
    premarket_close = close[:, CASH_START_MINUTE - 1]
    premarket_high = high[
        :, PREMARKET_START_MINUTE:CASH_START_MINUTE
    ].max(axis=1)
    premarket_low = low[
        :, PREMARKET_START_MINUTE:CASH_START_MINUTE
    ].min(axis=1)
    premarket_move = premarket_close - premarket_open

    previous_available = components.previous_session_index >= 0
    previous_close = np.full(len(components.session_dates), np.nan)
    previous_range = np.full(len(components.session_dates), np.nan)
    valid_current = np.flatnonzero(previous_available)
    previous_indices = components.previous_session_index[valid_current]
    previous_close[valid_current] = close[
        previous_indices, CONTEXT_END_MINUTE - 1
    ]
    previous_range[valid_current] = (
        high[previous_indices, cash_slice].max(axis=1)
        - low[previous_indices, cash_slice].min(axis=1)
    )
    gap_move = cash.open[:, 0] - previous_close
    gap_fraction = _safe_fraction(gap_move, previous_range)
    gap_fraction[~previous_available] = np.nan
    return Exp012Arrays(
        cash=cash,
        overnight_open=overnight_open,
        overnight_high=overnight_high,
        overnight_low=overnight_low,
        overnight_close=overnight_close,
        overnight_drive_fraction=_safe_fraction(
            overnight_move, overnight_high - overnight_low
        ),
        overnight_direction=_direction(overnight_move),
        premarket_open=premarket_open,
        premarket_high=premarket_high,
        premarket_low=premarket_low,
        premarket_close=premarket_close,
        premarket_drive_fraction=_safe_fraction(
            premarket_move, premarket_high - premarket_low
        ),
        premarket_direction=_direction(premarket_move),
        previous_cash_available=previous_available,
        previous_cash_close=previous_close,
        previous_cash_range=previous_range,
        gap_fraction=gap_fraction,
        gap_direction=_direction(gap_move),
    )


def _fixed_column(candidate_id: str) -> str:
    return f"fixed_{candidate_id}_profit_factor"


def run_one_exp013_permutation(
    components: Exp013PermutationComponents,
    *,
    zero_based_permutation: int,
    base_seed: int,
) -> dict[str, Any]:
    seed = permutation_seed(int(base_seed), int(zero_based_permutation))
    arrays = reconstruct_permuted_exp013_arrays(components, seed=seed)
    factors: dict[str, float] = {}
    for candidate in locked_exp012_candidates():
        result = run_exp012_candidate(
            arrays,
            candidate,
            symbol="NQ",
            slippage_ticks_per_side=1.0,
        )
        factors[candidate.candidate_id] = float(
            result.summary["trade_profit_factor"]
        )
    selected_id = sorted(
        factors,
        key=lambda candidate_id: (
            -factors[candidate_id],
            candidate_id,
        ),
    )[0]
    row: dict[str, Any] = {
        "permutation": int(zero_based_permutation + 1),
        "seed": int(seed),
        "maximum_candidate_id": selected_id,
        "maximum_trade_profit_factor": float(factors[selected_id]),
    }
    for candidate_id in FINALIST_IDS:
        row[_fixed_column(candidate_id)] = float(factors[candidate_id])
    return row


_WORKER_COMPONENTS: Exp013PermutationComponents | None = None
_WORKER_BASE_SEED: int | None = None


def _worker_initialize(
    components: Exp013PermutationComponents,
    base_seed: int,
) -> None:
    global _WORKER_COMPONENTS, _WORKER_BASE_SEED
    _WORKER_COMPONENTS = components
    _WORKER_BASE_SEED = int(base_seed)


def _worker_run(zero_based_permutation: int) -> dict[str, Any]:
    if _WORKER_COMPONENTS is None or _WORKER_BASE_SEED is None:
        raise RuntimeError("EXP-013 MCPT worker was not initialized.")
    return run_one_exp013_permutation(
        _WORKER_COMPONENTS,
        zero_based_permutation=zero_based_permutation,
        base_seed=_WORKER_BASE_SEED,
    )


def exp013_mcpt_signature(
    *,
    one_minute_fingerprint: str,
    permutations: int,
    base_seed: int,
) -> str:
    payload = {
        "engine_version": ENGINE_VERSION,
        "experiment_id": "EXP-013",
        "market": "NQ",
        "one_minute_fingerprint": str(one_minute_fingerprint),
        "permutations": int(permutations),
        "base_seed": int(base_seed),
        "candidate_ids": [
            candidate.candidate_id
            for candidate in locked_exp012_candidates()
        ],
        "finalist_ids": list(FINALIST_IDS),
        "source_slots": 1320,
        "components_shuffled_independently_by_exact_slot": True,
        "statistic": "maximum_trade_profit_factor_across_all_24_candidates",
        "slippage_ticks_per_side": 1.0,
    }
    stable = json.dumps(
        payload, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(stable).hexdigest()


def _atomic_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, allow_nan=True),
        encoding="utf-8",
    )
    temporary.replace(path)


def _load_checkpoint(path: Path, *, signature: str) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("signature") != signature:
        raise RuntimeError("An incompatible EXP-013 MCPT checkpoint exists.")
    return sorted(
        list(payload.get("rows", [])),
        key=lambda row: int(row["permutation"]),
    )


def _save_checkpoint(
    path: Path,
    *,
    signature: str,
    rows: list[dict[str, Any]],
) -> None:
    _atomic_json(
        {
            "experiment_id": "EXP-013",
            "signature": signature,
            "rows": sorted(rows, key=lambda row: int(row["permutation"])),
        },
        path,
    )


def _run_exp013_mcpt_engine(
    data: pd.DataFrame,
    *,
    real_maximum_profit_factor: float,
    real_fixed_profit_factors: dict[str, float],
    requested_workers: int,
    checkpoint_file: Path,
    one_minute_fingerprint: str,
    permutations: int,
    base_seed: int,
    calendar_session_dates: Iterable[str] | None = None,
) -> tuple[pd.DataFrame, float, dict[str, float], Exp013McptRunInfo]:
    if set(real_fixed_profit_factors) != set(FINALIST_IDS):
        raise ValueError("EXP-013 fixed-candidate real statistics changed.")
    signature = exp013_mcpt_signature(
        one_minute_fingerprint=one_minute_fingerprint,
        permutations=permutations,
        base_seed=base_seed,
    )
    existing = _load_checkpoint(
        Path(checkpoint_file), signature=signature
    )
    by_number = {int(row["permutation"]): row for row in existing}
    missing = [
        index
        for index in range(int(permutations))
        if index + 1 not in by_number
    ]
    components = build_exp013_permutation_components(
        data, calendar_session_dates=calendar_session_dates
    )
    workers = resolve_exp005_workers(requested_workers)
    newly_completed = 0

    print()
    print(
        f"Running {int(permutations):,} EXP-013 discovery-wide "
        "session permutations..."
    )
    print(f"MCPT workers: {workers} (requested: {requested_workers})")
    if existing:
        print(
            f"Resuming from checkpoint: {len(existing)}/"
            f"{int(permutations)} complete"
        )
    if workers == 1:
        for zero_based in missing:
            row = run_one_exp013_permutation(
                components,
                zero_based_permutation=zero_based,
                base_seed=base_seed,
            )
            by_number[int(row["permutation"])] = row
            newly_completed += 1
            if newly_completed % 10 == 0 or len(by_number) == permutations:
                _save_checkpoint(
                    Path(checkpoint_file),
                    signature=signature,
                    rows=list(by_number.values()),
                )
                print(
                    f"EXP-013 MCPT: {len(by_number)}/{int(permutations)}"
                )
    elif missing:
        context = multiprocessing.get_context("spawn")
        with ProcessPoolExecutor(
            max_workers=workers,
            mp_context=context,
            initializer=_worker_initialize,
            initargs=(components, int(base_seed)),
        ) as executor:
            futures: dict[Future[dict[str, Any]], int] = {
                executor.submit(_worker_run, index): index
                for index in missing
            }
            for future in as_completed(futures):
                row = future.result()
                by_number[int(row["permutation"])] = row
                newly_completed += 1
                if (
                    newly_completed % 10 == 0
                    or len(by_number) == permutations
                ):
                    _save_checkpoint(
                        Path(checkpoint_file),
                        signature=signature,
                        rows=list(by_number.values()),
                    )
                    print(
                        f"EXP-013 MCPT: {len(by_number)}/"
                        f"{int(permutations)}"
                    )
    if len(by_number) != int(permutations):
        raise RuntimeError("EXP-013 MCPT did not complete.")

    frame = pd.DataFrame(
        [by_number[number] for number in range(1, permutations + 1)]
    )
    frame["maximum_ge_real"] = frame[
        "maximum_trade_profit_factor"
    ].astype(float).ge(float(real_maximum_profit_factor))
    primary_p = (1 + int(frame["maximum_ge_real"].sum())) / (
        1 + int(permutations)
    )
    fixed_p: dict[str, float] = {}
    for candidate_id in FINALIST_IDS:
        compare_column = f"fixed_{candidate_id}_ge_real"
        frame[compare_column] = frame[_fixed_column(candidate_id)].astype(
            float
        ).ge(float(real_fixed_profit_factors[candidate_id]))
        fixed_p[candidate_id] = (
            1 + int(frame[compare_column].sum())
        ) / (1 + int(permutations))
    info = Exp013McptRunInfo(
        requested_workers=int(requested_workers),
        workers_used=int(workers),
        resumed_permutations=len(existing),
        newly_completed_permutations=newly_completed,
        checkpoint_file=str(checkpoint_file),
        signature=signature,
    )
    return frame, float(primary_p), fixed_p, info


def run_exp013_discovery_mcpt(
    data: pd.DataFrame,
    *,
    real_maximum_profit_factor: float,
    real_fixed_profit_factors: dict[str, float],
    requested_workers: int,
    checkpoint_file: Path,
    one_minute_fingerprint: str,
) -> tuple[pd.DataFrame, float, dict[str, float], Exp013McptRunInfo]:
    return _run_exp013_mcpt_engine(
        data,
        real_maximum_profit_factor=real_maximum_profit_factor,
        real_fixed_profit_factors=real_fixed_profit_factors,
        requested_workers=requested_workers,
        checkpoint_file=checkpoint_file,
        one_minute_fingerprint=one_minute_fingerprint,
        permutations=LOCKED_PERMUTATIONS,
        base_seed=LOCKED_BASE_SEED,
    )
