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
    ENGINE_VERSION as SOURCE_ENGINE_VERSION,
    Exp005PermutationComponents,
    build_permutation_components,
    resolve_exp005_workers,
    run_one_permutation,
    validate_one_minute_data,
)


ENGINE_VERSION = "exp005_full_session_mcpt_v1"
FULL_PERMUTATIONS = 1000
LOCKED_BASE_SEED = 45
CHECKPOINT_INTERVAL = 5


@dataclass(frozen=True)
class Exp005FullMcptRunInfo:
    requested_workers: int
    workers_used: int
    resumed_permutations: int
    newly_completed_permutations: int
    checkpoint_file: str
    signature: str
    source_engine_version: str

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
            "signature": self.signature,
            "source_engine_version": (
                self.source_engine_version
            ),
        }


_WORKER_COMPONENTS: (
    Exp005PermutationComponents | None
) = None
_WORKER_BASE_SEED: int | None = None


def validate_full_mcpt_request(
    *,
    permutations: int,
    base_seed: int,
) -> None:
    if int(permutations) != FULL_PERMUTATIONS:
        raise ValueError(
            "EXP-005 full MCPT is locked to "
            "exactly 1,000 permutations."
        )

    if int(base_seed) != LOCKED_BASE_SEED:
        raise ValueError(
            "EXP-005 MCPT seed is locked to 45."
        )


def full_mcpt_p_value(
    *,
    permutation_profit_factors: np.ndarray,
    real_trade_profit_factor: float,
) -> tuple[float, int, np.ndarray]:
    values = np.asarray(
        permutation_profit_factors,
        dtype=float,
    )

    if len(values) != FULL_PERMUTATIONS:
        raise ValueError(
            "Full MCPT p-value requires exactly "
            "1,000 permutation values."
        )

    comparable = np.where(
        np.isnan(values),
        -np.inf,
        values,
    )
    real = float(real_trade_profit_factor)
    real_comparable = (
        -np.inf
        if np.isnan(real)
        else real
    )
    flags = comparable >= real_comparable
    exceedances = int(
        np.count_nonzero(flags)
    )
    p_value = (
        1.0 + exceedances
    ) / (
        1.0 + FULL_PERMUTATIONS
    )

    return (
        float(p_value),
        exceedances,
        flags,
    )


def _stable_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def full_mcpt_signature(
    *,
    one_minute_fingerprint: str,
    permutations: int = FULL_PERMUTATIONS,
    base_seed: int = LOCKED_BASE_SEED,
) -> str:
    validate_full_mcpt_request(
        permutations=permutations,
        base_seed=base_seed,
    )
    payload = {
        "engine_version": ENGINE_VERSION,
        "source_engine_version": (
            SOURCE_ENGINE_VERSION
        ),
        "experiment_id": "EXP-005",
        "stage": "FULL_VALIDATION",
        "market": "NQ",
        "period": "2023-01-03/2025-12-31",
        "one_minute_fingerprint": str(
            one_minute_fingerprint
        ),
        "permutations": int(permutations),
        "base_seed": int(base_seed),
        "opening_range_minutes": 15,
        "direction_mode": "both",
        "optimization_inside_permutation": False,
        "slippage_ticks_per_side": 1.0,
    }

    return hashlib.sha256(
        _stable_json(payload).encode("utf-8")
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
        path.read_text(encoding="utf-8")
    )

    if (
        payload.get("experiment_id") != "EXP-005"
        or payload.get("stage")
        != "FULL_VALIDATION"
        or payload.get("engine_version")
        != ENGINE_VERSION
        or payload.get("signature")
        != signature
    ):
        raise RuntimeError(
            "An incompatible EXP-005 full-MCPT "
            "checkpoint exists. Do not mix research runs."
        )

    rows = list(payload.get("rows", []))
    numbers = [
        int(row["permutation"])
        for row in rows
    ]

    if (
        len(numbers) != len(set(numbers))
        or any(
            number < 1
            or number > FULL_PERMUTATIONS
            for number in numbers
        )
    ):
        raise RuntimeError(
            "EXP-005 full-MCPT checkpoint rows "
            "are invalid."
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
            "stage": "FULL_VALIDATION",
            "engine_version": ENGINE_VERSION,
            "source_engine_version": (
                SOURCE_ENGINE_VERSION
            ),
            "signature": signature,
            "target_permutations": (
                FULL_PERMUTATIONS
            ),
            "rows": ordered,
        },
        path,
    )


def _worker_initialize(
    components: Exp005PermutationComponents,
    base_seed: int,
) -> None:
    global _WORKER_COMPONENTS
    global _WORKER_BASE_SEED

    _WORKER_COMPONENTS = components
    _WORKER_BASE_SEED = int(base_seed)


def _worker_run(
    zero_based_permutation: int,
) -> dict[str, Any]:
    if (
        _WORKER_COMPONENTS is None
        or _WORKER_BASE_SEED is None
    ):
        raise RuntimeError(
            "EXP-005 full-MCPT worker was not initialized."
        )

    return run_one_permutation(
        _WORKER_COMPONENTS,
        zero_based_permutation=(
            zero_based_permutation
        ),
        base_seed=_WORKER_BASE_SEED,
    )


def _print_progress(completed: int) -> None:
    if (
        completed == FULL_PERMUTATIONS
        or completed % 10 == 0
    ):
        print(
            "EXP-005 full MCPT: "
            f"{completed}/{FULL_PERMUTATIONS}"
        )


def run_exp005_full_mcpt(
    one_minute_data: pd.DataFrame,
    *,
    real_trade_profit_factor: float,
    permutations: int = FULL_PERMUTATIONS,
    base_seed: int = LOCKED_BASE_SEED,
    requested_workers: int | None = 0,
    checkpoint_file: Path,
    one_minute_fingerprint: str | None = None,
) -> tuple[
    pd.DataFrame,
    float,
    Exp005FullMcptRunInfo,
]:
    validate_full_mcpt_request(
        permutations=permutations,
        base_seed=base_seed,
    )
    validate_one_minute_data(one_minute_data)

    fingerprint = (
        dataframe_sha256(one_minute_data)
        if one_minute_fingerprint is None
        else str(one_minute_fingerprint)
    )
    signature = full_mcpt_signature(
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
        for index in range(FULL_PERMUTATIONS)
        if index + 1 not in by_number
    ]
    workers = resolve_exp005_workers(
        requested_workers
    )
    components = build_permutation_components(
        one_minute_data
    )
    newly_completed = 0

    print()
    print(
        "Running 1,000 locked EXP-005 "
        "session-aware NQ permutations..."
    )
    print(
        f"MCPT workers: {workers} "
        f"(requested: {requested_workers})"
    )

    if existing:
        print(
            "Resuming from checkpoint: "
            f"{len(existing)}/1,000 complete"
        )

    def record_row(row: dict[str, Any]) -> None:
        nonlocal newly_completed
        by_number[int(row["permutation"])] = row
        newly_completed += 1
        completed = len(by_number)

        if (
            completed % CHECKPOINT_INTERVAL == 0
            or completed == FULL_PERMUTATIONS
        ):
            _save_checkpoint(
                checkpoint_file,
                signature=signature,
                rows=list(by_number.values()),
            )

        _print_progress(completed)

    if workers == 1:
        for zero_based in missing:
            record_row(
                run_one_permutation(
                    components,
                    zero_based_permutation=(
                        zero_based
                    ),
                    base_seed=int(base_seed),
                )
            )
    elif missing:
        context = multiprocessing.get_context(
            "spawn"
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

            for future in as_completed(futures):
                record_row(future.result())

    if missing and (
        not checkpoint_file.exists()
        or len(by_number) == FULL_PERMUTATIONS
    ):
        _save_checkpoint(
            checkpoint_file,
            signature=signature,
            rows=list(by_number.values()),
        )

    rows = [
        by_number[number]
        for number in range(
            1,
            FULL_PERMUTATIONS + 1,
        )
    ]
    frame = pd.DataFrame(rows)

    if len(frame) != FULL_PERMUTATIONS:
        raise RuntimeError(
            "EXP-005 full MCPT did not complete "
            "all 1,000 permutations."
        )

    p_value, exceedances, flags = (
        full_mcpt_p_value(
            permutation_profit_factors=(
                frame[
                    "trade_profit_factor"
                ].to_numpy(dtype=float)
            ),
            real_trade_profit_factor=float(
                real_trade_profit_factor
            ),
        )
    )
    frame["real_trade_profit_factor"] = float(
        real_trade_profit_factor
    )
    frame["permutation_ge_real"] = flags

    info = Exp005FullMcptRunInfo(
        requested_workers=int(
            requested_workers or 0
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
        source_engine_version=(
            SOURCE_ENGINE_VERSION
        ),
    )

    frame.attrs[
        "permutations_at_least_real"
    ] = exceedances

    return frame, p_value, info
