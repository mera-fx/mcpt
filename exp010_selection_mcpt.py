from __future__ import annotations

from concurrent.futures import Future, ProcessPoolExecutor, as_completed
from dataclasses import dataclass
import hashlib
import json
import multiprocessing
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from exp005_quantower_import import dataframe_sha256
from exp005_session_mcpt import (
    Exp005PermutationComponents,
    _permuted_component_arrays,
    build_permutation_components,
    permutation_seed,
    resolve_exp005_workers,
    validate_one_minute_data,
)
from exp009_engine import Exp009Arrays
from exp010_selection import (
    evaluate_opening_drive_grid,
    select_opening_drive_candidate,
    selected_candidate_row,
)


ENGINE_VERSION = "exp010_opening_drive_selection_mcpt_v1"
LOCKED_PERMUTATIONS = 1_000
LOCKED_BASE_SEED = 50
FIXED_REFERENCE_ID = "opening_drive_0p5_1p5r"
MINUTE_NS = 60 * 1_000_000_000


@dataclass(frozen=True)
class Exp010McptRunInfo:
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


_WORKER_COMPONENTS: Exp005PermutationComponents | None = None
_WORKER_BASE_SEED: int | None = None


def _build_exp009_arrays(
    *,
    components: Exp005PermutationComponents,
    open_values: np.ndarray,
    high_values: np.ndarray,
    low_values: np.ndarray,
    close_values: np.ndarray,
    volume: np.ndarray,
) -> Exp009Arrays:
    session_count = int(open_values.shape[0])
    five_shape = (session_count, 78, 5)
    open_5m = open_values.reshape(five_shape)[:, :, 0]
    high_5m = high_values.reshape(five_shape).max(axis=2)
    low_5m = low_values.reshape(five_shape).min(axis=2)
    close_5m = close_values.reshape(five_shape)[:, :, -1]
    volume_5m = volume.reshape(five_shape).sum(axis=2)
    typical = (high_values + low_values + close_values) / 3.0
    cumulative_volume = np.cumsum(volume, axis=1)
    safe_volume = np.where(cumulative_volume > 0, cumulative_volume, np.nan)
    cumulative_pv = np.cumsum(typical * volume, axis=1)
    cumulative_p2v = np.cumsum(typical * typical * volume, axis=1)
    vwap = cumulative_pv / safe_volume
    variance = np.maximum(cumulative_p2v / safe_volume - vwap * vwap, 0.0)
    session_dates = np.asarray(components.session_dates, dtype=object)
    years = pd.to_datetime(session_dates).year.to_numpy(dtype=int)
    return Exp009Arrays(
        session_dates=session_dates,
        years=years,
        open=open_values,
        high=high_values,
        low=low_values,
        close=close_values,
        volume=volume,
        open_5m=open_5m,
        high_5m=high_5m,
        low_5m=low_5m,
        close_5m=close_5m,
        volume_5m=volume_5m,
        vwap_5m=vwap[:, 4::5],
        vwap_std_5m=np.sqrt(variance[:, 4::5]),
    )


def reconstruct_permuted_exp010_arrays(
    components: Exp005PermutationComponents,
    *,
    seed: int,
) -> Exp009Arrays:
    (
        open_gap,
        close_move,
        high_excursion,
        low_excursion,
        volume,
    ) = _permuted_component_arrays(components, seed=int(seed))
    flat_gap = open_gap.reshape(-1)
    flat_close_move = close_move.reshape(-1)
    log_open = np.empty_like(flat_gap)
    log_close = np.empty_like(flat_gap)
    log_open[0] = np.log(components.first_open)
    log_close[0] = log_open[0] + flat_close_move[0]
    log_close[1:] = log_close[0] + np.cumsum(
        flat_gap[1:] + flat_close_move[1:]
    )
    log_open[1:] = log_close[:-1] + flat_gap[1:]
    shape = open_gap.shape
    open_values = np.exp(log_open).reshape(shape)
    close_values = np.exp(log_close).reshape(shape)
    high_values = np.maximum(open_values, close_values) * np.exp(
        high_excursion
    )
    low_values = np.minimum(open_values, close_values) * np.exp(
        low_excursion
    )
    return _build_exp009_arrays(
        components=components,
        open_values=open_values,
        high_values=high_values,
        low_values=low_values,
        close_values=close_values,
        volume=volume,
    )


def run_one_exp010_permutation(
    components: Exp005PermutationComponents,
    *,
    zero_based_permutation: int,
    base_seed: int,
) -> dict[str, Any]:
    seed = permutation_seed(int(base_seed), int(zero_based_permutation))
    arrays = reconstruct_permuted_exp010_arrays(components, seed=seed)
    grid = evaluate_opening_drive_grid(arrays)
    selection = select_opening_drive_candidate(grid)
    selected = selected_candidate_row(selection)
    reference_rows = grid.loc[
        grid["candidate_id"].eq(FIXED_REFERENCE_ID)
    ]
    if len(reference_rows) != 1:
        raise RuntimeError("EXP-010 fixed reference row is not unique.")
    reference = reference_rows.iloc[0]
    return {
        "permutation": int(zero_based_permutation + 1),
        "seed": int(seed),
        "selected_candidate_id": (
            ""
            if selection.selected_candidate is None
            else selection.selected_candidate.candidate_id
        ),
        "selected_trade_profit_factor": (
            0.0 if selected is None else float(selected["trade_profit_factor"])
        ),
        "selected_net_profit_usd": (
            0.0 if selected is None else float(selected["net_profit_usd"])
        ),
        "selected_completed_trades": (
            0 if selected is None else int(selected["completed_trades"])
        ),
        "eligible_candidates": int(selection.eligible_count),
        "fixed_reference_trade_profit_factor": float(
            reference["trade_profit_factor"]
        ),
        "fixed_reference_net_profit_usd": float(
            reference["net_profit_usd"]
        ),
    }


def _worker_initialize(
    components: Exp005PermutationComponents,
    base_seed: int,
) -> None:
    global _WORKER_COMPONENTS, _WORKER_BASE_SEED
    _WORKER_COMPONENTS = components
    _WORKER_BASE_SEED = int(base_seed)


def _worker_run(zero_based_permutation: int) -> dict[str, Any]:
    if _WORKER_COMPONENTS is None or _WORKER_BASE_SEED is None:
        raise RuntimeError("EXP-010 MCPT worker was not initialized.")
    return run_one_exp010_permutation(
        _WORKER_COMPONENTS,
        zero_based_permutation=zero_based_permutation,
        base_seed=_WORKER_BASE_SEED,
    )


def exp010_mcpt_signature(
    *,
    one_minute_fingerprint: str,
    permutations: int,
    base_seed: int,
) -> str:
    payload = {
        "engine_version": ENGINE_VERSION,
        "experiment_id": "EXP-010",
        "market": "NQ",
        "one_minute_fingerprint": str(one_minute_fingerprint),
        "permutations": int(permutations),
        "base_seed": int(base_seed),
        "candidate_ids": [
            "opening_drive_0p5_time",
            "opening_drive_0p5_1p5r",
            "opening_drive_0p75_time",
            "opening_drive_0p75_1p5r",
        ],
        "minimum_completed_trades": 100,
        "minimum_profit_factor": 1.0,
        "minimum_net_profit_usd": 0.0,
        "selection_inside_every_permutation": True,
        "fixed_reference_candidate": FIXED_REFERENCE_ID,
        "prior_six_family_selection_corrected": False,
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
        raise RuntimeError(
            "An incompatible EXP-010 MCPT checkpoint exists."
        )
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
            "experiment_id": "EXP-010",
            "engine_version": ENGINE_VERSION,
            "signature": signature,
            "rows": sorted(
                rows, key=lambda row: int(row["permutation"])
            ),
        },
        path,
    )


def _run_exp010_mcpt_engine(
    one_minute_data: pd.DataFrame,
    *,
    real_selected_trade_profit_factor: float,
    real_fixed_reference_trade_profit_factor: float,
    permutations: int,
    base_seed: int,
    requested_workers: int | None,
    checkpoint_file: Path,
    one_minute_fingerprint: str | None,
    enforce_locked: bool,
) -> tuple[pd.DataFrame, float, float, Exp010McptRunInfo]:
    if enforce_locked:
        if int(permutations) != LOCKED_PERMUTATIONS:
            raise ValueError("EXP-010 MCPT is locked to 1,000 permutations.")
        if int(base_seed) != LOCKED_BASE_SEED:
            raise ValueError("EXP-010 MCPT seed is locked to 50.")
    elif int(permutations) < 1:
        raise ValueError("Testing permutations must be positive.")

    validate_one_minute_data(one_minute_data)
    fingerprint = (
        dataframe_sha256(one_minute_data)
        if one_minute_fingerprint is None
        else str(one_minute_fingerprint)
    )
    signature = exp010_mcpt_signature(
        one_minute_fingerprint=fingerprint,
        permutations=int(permutations),
        base_seed=int(base_seed),
    )
    existing = _load_checkpoint(Path(checkpoint_file), signature=signature)
    by_number = {
        int(row["permutation"]): row for row in existing
    }
    missing = [
        index
        for index in range(int(permutations))
        if index + 1 not in by_number
    ]
    components = build_permutation_components(one_minute_data)
    workers = resolve_exp005_workers(requested_workers)
    newly_completed = 0

    print()
    print(
        f"Running {int(permutations):,} EXP-010 opening-drive "
        "selection-aware permutations..."
    )
    print(f"MCPT workers: {workers} (requested: {requested_workers})")
    if existing:
        print(
            f"Resuming from checkpoint: {len(existing)}/"
            f"{int(permutations)} complete"
        )

    if workers == 1:
        for zero_based in missing:
            row = run_one_exp010_permutation(
                components,
                zero_based_permutation=zero_based,
                base_seed=int(base_seed),
            )
            by_number[int(row["permutation"])] = row
            newly_completed += 1
            if newly_completed % 10 == 0 or len(by_number) == int(
                permutations
            ):
                _save_checkpoint(
                    Path(checkpoint_file),
                    signature=signature,
                    rows=list(by_number.values()),
                )
                print(
                    f"EXP-010 MCPT: {len(by_number)}/{int(permutations)}"
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
                executor.submit(_worker_run, zero_based): zero_based
                for zero_based in missing
            }
            for future in as_completed(futures):
                row = future.result()
                by_number[int(row["permutation"])] = row
                newly_completed += 1
                if newly_completed % 10 == 0 or len(by_number) == int(
                    permutations
                ):
                    _save_checkpoint(
                        Path(checkpoint_file),
                        signature=signature,
                        rows=list(by_number.values()),
                    )
                    print(
                        f"EXP-010 MCPT: {len(by_number)}/"
                        f"{int(permutations)}"
                    )

    if len(by_number) != int(permutations):
        raise RuntimeError("EXP-010 MCPT did not complete.")
    frame = pd.DataFrame(
        [
            by_number[number]
            for number in range(1, int(permutations) + 1)
        ]
    )
    frame["selected_ge_real"] = frame[
        "selected_trade_profit_factor"
    ].astype(float).ge(float(real_selected_trade_profit_factor))
    frame["fixed_reference_ge_real"] = frame[
        "fixed_reference_trade_profit_factor"
    ].astype(float).ge(float(real_fixed_reference_trade_profit_factor))
    selected_p = (1 + int(frame["selected_ge_real"].sum())) / (
        1 + int(permutations)
    )
    fixed_p = (1 + int(frame["fixed_reference_ge_real"].sum())) / (
        1 + int(permutations)
    )
    info = Exp010McptRunInfo(
        requested_workers=(
            0 if requested_workers is None else int(requested_workers)
        ),
        workers_used=int(workers),
        resumed_permutations=len(existing),
        newly_completed_permutations=newly_completed,
        checkpoint_file=str(checkpoint_file),
        signature=signature,
    )
    return frame, float(selected_p), float(fixed_p), info


def run_exp010_selection_mcpt(
    one_minute_data: pd.DataFrame,
    *,
    real_selected_trade_profit_factor: float,
    real_fixed_reference_trade_profit_factor: float,
    requested_workers: int | None = 0,
    checkpoint_file: Path,
    one_minute_fingerprint: str | None = None,
    permutations: int = LOCKED_PERMUTATIONS,
    base_seed: int = LOCKED_BASE_SEED,
) -> tuple[pd.DataFrame, float, float, Exp010McptRunInfo]:
    return _run_exp010_mcpt_engine(
        one_minute_data,
        real_selected_trade_profit_factor=(
            real_selected_trade_profit_factor
        ),
        real_fixed_reference_trade_profit_factor=(
            real_fixed_reference_trade_profit_factor
        ),
        permutations=int(permutations),
        base_seed=int(base_seed),
        requested_workers=requested_workers,
        checkpoint_file=Path(checkpoint_file),
        one_minute_fingerprint=one_minute_fingerprint,
        enforce_locked=True,
    )
