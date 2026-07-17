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
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from exp005_quantower_import import (
    dataframe_sha256,
)
from exp005_session_mcpt import (
    Exp005PermutationComponents,
    _permuted_component_arrays,
    build_permutation_components,
    permutation_seed,
    resolve_exp005_workers,
    validate_one_minute_data,
)
from exp008_candidate_scoring import (
    evaluate_nq_grid,
    select_candidate,
)
from exp008_orb import Exp008Arrays


ENGINE_VERSION = (
    "exp008_selection_aware_session_mcpt_v1"
)
LOCKED_PERMUTATIONS = 1_000
LOCKED_BASE_SEED = 48
MINUTE_NS = 60 * 1_000_000_000


@dataclass(frozen=True)
class Exp008McptRunInfo:
    requested_workers: int
    workers_used: int
    resumed_permutations: int
    newly_completed_permutations: int
    checkpoint_file: str
    signature: str
    engine_version: str = ENGINE_VERSION

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
            "engine_version": (
                self.engine_version
            ),
        }


_WORKER_COMPONENTS: (
    Exp005PermutationComponents | None
) = None
_WORKER_BASE_SEED: int | None = None


def reconstruct_permuted_exp008_arrays(
    components: Exp005PermutationComponents,
    *,
    seed: int,
) -> Exp008Arrays:
    (
        open_gap,
        close_move,
        high_excursion,
        low_excursion,
        volume,
    ) = _permuted_component_arrays(
        components,
        seed=int(seed),
    )

    flat_gap = open_gap.reshape(-1)
    flat_close_move = close_move.reshape(-1)
    log_open = np.empty_like(flat_gap)
    log_close = np.empty_like(flat_gap)

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

    shape = components.open_gap.shape
    open_values = np.exp(
        log_open
    ).reshape(shape)
    close_values = np.exp(
        log_close
    ).reshape(shape)
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

    five_starts = (
        components.five_minute_index_ns[
            :,
            :,
            None,
        ]
    )
    minute_offsets = (
        np.arange(
            5,
            dtype=np.int64,
        )[
            None,
            None,
            :,
        ]
        * MINUTE_NS
    )
    index_ns = (
        five_starts
        + minute_offsets
    ).reshape(shape)

    session_dates = np.array(
        components.session_dates,
        dtype=object,
    )
    years = (
        pd.to_datetime(
            session_dates
        )
        .year
        .to_numpy(dtype=int)
    )

    return Exp008Arrays(
        session_dates=session_dates,
        years=years,
        open=open_values,
        high=high_values,
        low=low_values,
        close=close_values,
        volume=volume,
        index_ns=index_ns,
    )


def run_one_exp008_permutation(
    components: Exp005PermutationComponents,
    *,
    zero_based_permutation: int,
    base_seed: int,
) -> dict[str, Any]:
    seed = permutation_seed(
        int(base_seed),
        int(zero_based_permutation),
    )
    arrays = (
        reconstruct_permuted_exp008_arrays(
            components,
            seed=seed,
        )
    )
    grid = evaluate_nq_grid(arrays)
    selection = select_candidate(grid)

    if (
        selection.selected_parameters
        is None
    ):
        selected_pf = 0.0
        selected_net = 0.0
        selected_trades = 0
        selected_key = ""
    else:
        selected_rows = (
            selection.scored_grid.loc[
                selection.scored_grid[
                    "selected"
                ]
            ]
        )
        if len(selected_rows) != 1:
            raise RuntimeError(
                "EXP-008 permutation selection "
                "row is not unique."
            )
        selected_row = (
            selected_rows.iloc[0]
        )
        selected_pf = float(
            selected_row[
                "nq_trade_profit_factor"
            ]
        )
        selected_net = float(
            selected_row[
                "nq_net_profit_usd"
            ]
        )
        selected_trades = int(
            selected_row[
                "nq_completed_trades"
            ]
        )
        selected_key = (
            selection.selected_parameters.key
        )

    return {
        "permutation": int(
            zero_based_permutation + 1
        ),
        "seed": int(seed),
        "selected_parameter_key": (
            selected_key
        ),
        "selected_trade_profit_factor": (
            selected_pf
        ),
        "selected_net_profit_usd": (
            selected_net
        ),
        "selected_completed_trades": (
            selected_trades
        ),
        "eligible_candidates": (
            selection.eligible_count
        ),
        "stable_eligible_candidates": (
            selection.stable_eligible_count
        ),
    }


def _worker_initialize(
    components: Exp005PermutationComponents,
    base_seed: int,
) -> None:
    global _WORKER_COMPONENTS
    global _WORKER_BASE_SEED

    _WORKER_COMPONENTS = components
    _WORKER_BASE_SEED = int(
        base_seed
    )


def _worker_run(
    zero_based_permutation: int,
) -> dict[str, Any]:
    if (
        _WORKER_COMPONENTS is None
        or _WORKER_BASE_SEED is None
    ):
        raise RuntimeError(
            "EXP-008 MCPT worker was not "
            "initialized."
        )

    return run_one_exp008_permutation(
        _WORKER_COMPONENTS,
        zero_based_permutation=(
            zero_based_permutation
        ),
        base_seed=_WORKER_BASE_SEED,
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


def exp008_mcpt_signature(
    *,
    one_minute_fingerprint: str,
    permutations: int,
    base_seed: int,
) -> str:
    payload = {
        "engine_version": ENGINE_VERSION,
        "experiment_id": "EXP-008",
        "market": "NQ",
        "one_minute_fingerprint": (
            one_minute_fingerprint
        ),
        "permutations": int(
            permutations
        ),
        "base_seed": int(base_seed),
        "opening_range_minutes": [
            15,
            30,
            45,
        ],
        "reward_to_risk": [
            0.5,
            1.0,
            1.5,
        ],
        "forced_flat_time_new_york": [
            "12:00",
            "14:00",
            "15:55",
        ],
        "direction_mode": "long_only",
        "same_minute_ambiguity": (
            "STOP_FIRST_CONSERVATIVE"
        ),
        "selection_market": "NQ",
        "selection_primary_rank": (
            "trade_profit_factor_descending"
        ),
        "minimum_candidate_pf": 1.0,
        "minimum_candidate_net_profit": 0.0,
        "minimum_candidate_trades": 100,
        "minimum_profitable_neighbor_fraction": 0.5,
        "minimum_neighbor_median_pf": 1.0,
        "all_27_candidates_inside_permutation": True,
        "selection_inside_permutation": True,
        "slippage_ticks_per_side": 1.0,
    }
    return hashlib.sha256(
        _stable_json(
            payload
        ).encode("utf-8")
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
    if (
        payload.get("signature")
        != signature
    ):
        raise RuntimeError(
            "An incompatible EXP-008 MCPT "
            "checkpoint exists. Do not mix "
            "research runs."
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
            "experiment_id": "EXP-008",
            "engine_version": (
                ENGINE_VERSION
            ),
            "signature": signature,
            "rows": ordered,
        },
        path,
    )


def _run_exp008_mcpt_engine(
    one_minute_data: pd.DataFrame,
    *,
    real_selected_trade_profit_factor: float,
    permutations: int,
    base_seed: int,
    requested_workers: int | None,
    checkpoint_file: Path,
    one_minute_fingerprint: str | None,
    enforce_locked: bool,
) -> tuple[
    pd.DataFrame,
    float,
    Exp008McptRunInfo,
]:
    if enforce_locked:
        if (
            int(permutations)
            != LOCKED_PERMUTATIONS
        ):
            raise ValueError(
                "EXP-008 MCPT is locked to "
                "exactly 1,000 permutations."
            )
        if (
            int(base_seed)
            != LOCKED_BASE_SEED
        ):
            raise ValueError(
                "EXP-008 MCPT seed is "
                "locked to 48."
            )
    elif int(permutations) < 1:
        raise ValueError(
            "Testing permutations must "
            "be positive."
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
    signature = exp008_mcpt_signature(
        one_minute_fingerprint=(
            fingerprint
        ),
        permutations=int(
            permutations
        ),
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
        if (
            index + 1
            not in by_number
        )
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
        f"Running {int(permutations):,} "
        "EXP-008 selection-aware "
        "session permutations..."
    )
    print(
        "MCPT workers: "
        f"{workers} "
        f"(requested: {requested_workers})"
    )
    if existing:
        print(
            "Resuming from checkpoint: "
            f"{len(existing)}/"
            f"{int(permutations)} complete"
        )

    if workers == 1:
        for zero_based in missing:
            row = run_one_exp008_permutation(
                components,
                zero_based_permutation=(
                    zero_based
                ),
                base_seed=int(
                    base_seed
                ),
            )
            by_number[
                int(
                    row["permutation"]
                )
            ] = row
            newly_completed += 1

            if (
                newly_completed % 10 == 0
                or len(by_number)
                == int(permutations)
            ):
                _save_checkpoint(
                    checkpoint_file,
                    signature=signature,
                    rows=list(
                        by_number.values()
                    ),
                )
                print(
                    "EXP-008 MCPT: "
                    f"{len(by_number)}/"
                    f"{int(permutations)}"
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
                        row[
                            "permutation"
                        ]
                    )
                ] = row
                newly_completed += 1

                if (
                    newly_completed % 10
                    == 0
                    or len(by_number)
                    == int(permutations)
                ):
                    _save_checkpoint(
                        checkpoint_file,
                        signature=signature,
                        rows=list(
                            by_number.values()
                        ),
                    )
                    print(
                        "EXP-008 MCPT: "
                        f"{len(by_number)}/"
                        f"{int(permutations)}"
                    )

    if (
        len(by_number)
        != int(permutations)
    ):
        raise RuntimeError(
            "EXP-008 MCPT did not complete "
            "the locked permutation count."
        )

    ordered_rows = [
        by_number[number]
        for number in range(
            1,
            int(permutations) + 1,
        )
    ]
    frame = pd.DataFrame(
        ordered_rows
    )
    frame[
        "permutation_ge_real"
    ] = frame[
        "selected_trade_profit_factor"
    ].astype(float).ge(
        float(
            real_selected_trade_profit_factor
        )
    )
    exceedances = int(
        frame[
            "permutation_ge_real"
        ].sum()
    )
    p_value = (
        1.0 + exceedances
    ) / (
        1.0 + int(permutations)
    )

    info = Exp008McptRunInfo(
        requested_workers=(
            0
            if requested_workers is None
            else int(requested_workers)
        ),
        workers_used=int(workers),
        resumed_permutations=int(
            len(existing)
        ),
        newly_completed_permutations=int(
            newly_completed
        ),
        checkpoint_file=str(
            checkpoint_file
        ),
        signature=signature,
    )
    return frame, float(
        p_value
    ), info


def run_exp008_selection_mcpt(
    one_minute_data: pd.DataFrame,
    *,
    real_selected_trade_profit_factor: float,
    requested_workers: int | None = 0,
    checkpoint_file: Path,
    one_minute_fingerprint: str | None = None,
    permutations: int = LOCKED_PERMUTATIONS,
    base_seed: int = LOCKED_BASE_SEED,
) -> tuple[
    pd.DataFrame,
    float,
    Exp008McptRunInfo,
]:
    return _run_exp008_mcpt_engine(
        one_minute_data,
        real_selected_trade_profit_factor=(
            real_selected_trade_profit_factor
        ),
        permutations=int(
            permutations
        ),
        base_seed=int(base_seed),
        requested_workers=(
            requested_workers
        ),
        checkpoint_file=Path(
            checkpoint_file
        ),
        one_minute_fingerprint=(
            one_minute_fingerprint
        ),
        enforce_locked=True,
    )
