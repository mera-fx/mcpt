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

from exp005_session_mcpt import (
    Exp005PermutationComponents,
    build_permutation_components,
    permutation_seed,
    reconstruct_permuted_five_minute_data,
    resolve_exp005_workers,
)
from exp006_orb import (
    locked_parameters,
    prepare_orb_arrays,
    run_candidate_summary,
)

ENGINE_VERSION = "exp006_selection_mcpt_v1"
FORMAL_PERMUTATIONS = 1000
FORMAL_BASE_SEED = 46
FORMAL_MINIMUM_TRADES = 1000

_WORKER_COMPONENTS: Exp005PermutationComponents | None = None
_WORKER_BASE_SEED: int | None = None
_WORKER_MINIMUM_TRADES: int | None = None


@dataclass(frozen=True)
class SelectionMcptRunInfo:
    requested_workers: int
    workers_used: int
    resumed_permutations: int
    newly_completed_permutations: int
    checkpoint_file: str
    signature: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "engine_version": ENGINE_VERSION,
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
            "checkpoint_file": self.checkpoint_file,
            "signature": self.signature,
        }



def _bounded_quality(
    *,
    profit_factor: float,
    net_profit_to_drawdown: float,
    average_trade_to_cost: float,
    profitable_year_fraction: float,
) -> float:
    values = np.array(
        [
            np.tanh(
                max(float(profit_factor) - 1.0, 0.0)
                * 3.0
            ),
            np.tanh(
                max(
                    float(net_profit_to_drawdown),
                    0.0,
                )
                / 3.0
            ),
            np.tanh(
                max(
                    float(average_trade_to_cost),
                    0.0,
                )
                / 10.0
            ),
            min(
                max(
                    float(profitable_year_fraction),
                    0.0,
                ),
                1.0,
            ),
        ],
        dtype=float,
    )
    return float(np.median(values))



def nq_selection_statistic_table(
    five_minute_data: pd.DataFrame,
    *,
    minimum_trades: int = FORMAL_MINIMUM_TRADES,
) -> pd.DataFrame:
    arrays = prepare_orb_arrays(
        five_minute_data,
        validate_data=False,
    )
    year_count = max(1, len(set(arrays.years)))
    rows: list[dict[str, Any]] = []

    for parameters in locked_parameters():
        summary = run_candidate_summary(
            arrays,
            parameters=parameters,
            symbol="NQ",
        )
        eligible = (
            float(
                summary["trade_profit_factor"]
            )
            > 1.0
            and float(summary["net_profit_usd"])
            > 0.0
            and int(summary["completed_trades"])
            >= int(minimum_trades)
        )
        statistic = (
            _bounded_quality(
                profit_factor=float(
                    summary["trade_profit_factor"]
                ),
                net_profit_to_drawdown=float(
                    summary[
                        "net_profit_to_drawdown"
                    ]
                ),
                average_trade_to_cost=float(
                    summary[
                        "average_trade_to_cost"
                    ]
                ),
                profitable_year_fraction=(
                    int(
                        summary[
                            "profitable_calendar_years"
                        ]
                    )
                    / year_count
                ),
            )
            if eligible
            else 0.0
        )
        rows.append(
            {
                **parameters.to_dict(),
                "eligible_for_mcpt_selection": eligible,
                "selection_statistic": statistic,
                "trade_profit_factor": summary[
                    "trade_profit_factor"
                ],
                "net_profit_usd": summary[
                    "net_profit_usd"
                ],
                "completed_trades": summary[
                    "completed_trades"
                ],
                "net_profit_to_drawdown": summary[
                    "net_profit_to_drawdown"
                ],
                "average_trade_to_cost": summary[
                    "average_trade_to_cost"
                ],
                "profitable_calendar_years": summary[
                    "profitable_calendar_years"
                ],
            }
        )

    return pd.DataFrame(rows)



def best_nq_selection_statistic(
    five_minute_data: pd.DataFrame,
    *,
    minimum_trades: int = FORMAL_MINIMUM_TRADES,
) -> tuple[float, str, pd.DataFrame]:
    table = nq_selection_statistic_table(
        five_minute_data,
        minimum_trades=minimum_trades,
    )
    ordered = table.sort_values(
        by=[
            "selection_statistic",
            "trade_profit_factor",
            "net_profit_usd",
            "parameter_key",
        ],
        ascending=[False, False, False, True],
        kind="mergesort",
    )
    top = ordered.iloc[0]
    return (
        float(top["selection_statistic"]),
        str(top["parameter_key"]),
        table,
    )



def run_one_selection_permutation(
    components: Exp005PermutationComponents,
    *,
    zero_based_permutation: int,
    base_seed: int,
    minimum_trades: int = FORMAL_MINIMUM_TRADES,
) -> dict[str, Any]:
    seed = permutation_seed(
        base_seed,
        zero_based_permutation,
    )
    market = reconstruct_permuted_five_minute_data(
        components,
        seed=seed,
    )
    statistic, parameter_key, table = (
        best_nq_selection_statistic(
            market,
            minimum_trades=minimum_trades,
        )
    )
    eligible = int(
        table[
            "eligible_for_mcpt_selection"
        ].sum()
    )
    return {
        "permutation": int(
            zero_based_permutation + 1
        ),
        "seed": int(seed),
        "best_selection_statistic": statistic,
        "best_parameter_key": parameter_key,
        "eligible_candidate_count": eligible,
    }



def _worker_initialize(
    components: Exp005PermutationComponents,
    base_seed: int,
    minimum_trades: int,
) -> None:
    global _WORKER_COMPONENTS
    global _WORKER_BASE_SEED
    global _WORKER_MINIMUM_TRADES
    _WORKER_COMPONENTS = components
    _WORKER_BASE_SEED = int(base_seed)
    _WORKER_MINIMUM_TRADES = int(
        minimum_trades
    )



def _worker_run(
    zero_based_permutation: int,
) -> dict[str, Any]:
    if (
        _WORKER_COMPONENTS is None
        or _WORKER_BASE_SEED is None
        or _WORKER_MINIMUM_TRADES is None
    ):
        raise RuntimeError(
            "EXP-006 MCPT worker was not initialized."
        )
    return run_one_selection_permutation(
        _WORKER_COMPONENTS,
        zero_based_permutation=(
            zero_based_permutation
        ),
        base_seed=_WORKER_BASE_SEED,
        minimum_trades=_WORKER_MINIMUM_TRADES,
    )



def mcpt_signature(
    *,
    one_minute_fingerprint: str,
    permutations: int,
    base_seed: int,
    minimum_trades: int,
) -> str:
    payload = {
        "engine_version": ENGINE_VERSION,
        "experiment_id": "EXP-006",
        "market": "NQ",
        "one_minute_fingerprint": (
            one_minute_fingerprint
        ),
        "permutations": int(permutations),
        "base_seed": int(base_seed),
        "minimum_trades": int(minimum_trades),
        "parameter_combinations": 27,
        "optimization_inside_permutation": True,
        "selection_components": [
            "profit_factor_excess",
            "net_profit_to_drawdown",
            "average_trade_to_cost",
            "profitable_year_fraction",
        ],
    }
    stable = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(
        stable.encode("utf-8")
    ).hexdigest()



def _atomic_checkpoint(
    *,
    path: Path,
    signature: str,
    rows: list[dict[str, Any]],
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
            {
                "signature": signature,
                "rows": sorted(
                    rows,
                    key=lambda item: item[
                        "permutation"
                    ],
                ),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    temporary.replace(path)



def _load_checkpoint(
    *,
    path: Path,
    signature: str,
) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    payload = json.loads(
        path.read_text(encoding="utf-8")
    )
    if payload.get("signature") != signature:
        raise RuntimeError(
            "An incompatible EXP-006 MCPT checkpoint exists."
        )
    rows = payload.get("rows", [])
    if not isinstance(rows, list):
        raise RuntimeError(
            "EXP-006 MCPT checkpoint rows are invalid."
        )
    return rows



def run_selection_aware_mcpt(
    one_minute_data: pd.DataFrame,
    *,
    real_selection_statistic: float,
    permutations: int = FORMAL_PERMUTATIONS,
    base_seed: int = FORMAL_BASE_SEED,
    requested_workers: int = 0,
    checkpoint_file: Path,
    one_minute_fingerprint: str,
    minimum_trades: int = FORMAL_MINIMUM_TRADES,
) -> tuple[
    pd.DataFrame,
    float,
    SelectionMcptRunInfo,
]:
    if permutations < 1:
        raise ValueError(
            "EXP-006 MCPT permutations must be positive."
        )
    workers = resolve_exp005_workers(
        requested_workers
    )
    components = build_permutation_components(
        one_minute_data
    )
    signature = mcpt_signature(
        one_minute_fingerprint=(
            one_minute_fingerprint
        ),
        permutations=permutations,
        base_seed=base_seed,
        minimum_trades=minimum_trades,
    )
    rows = _load_checkpoint(
        path=checkpoint_file,
        signature=signature,
    )
    completed = {
        int(item["permutation"])
        for item in rows
    }
    pending = [
        index
        for index in range(permutations)
        if index + 1 not in completed
    ]
    resumed = len(rows)

    print(
        f"Running {permutations:,} EXP-006 "
        "selection-aware permutations..."
    )
    print(
        f"MCPT workers: {workers} "
        f"(requested: {requested_workers})"
    )
    if resumed:
        print(
            "Resuming from checkpoint: "
            f"{resumed:,}/{permutations:,} complete"
        )

    newly_completed = 0
    if workers == 1:
        for index in pending:
            rows.append(
                run_one_selection_permutation(
                    components,
                    zero_based_permutation=index,
                    base_seed=base_seed,
                    minimum_trades=minimum_trades,
                )
            )
            newly_completed += 1
            if (
                newly_completed % 5 == 0
                or newly_completed == len(pending)
            ):
                _atomic_checkpoint(
                    path=checkpoint_file,
                    signature=signature,
                    rows=rows,
                )
            if (
                (resumed + newly_completed) % 10
                == 0
            ):
                print(
                    "EXP-006 selection MCPT: "
                    f"{resumed + newly_completed}/"
                    f"{permutations}"
                )
    elif pending:
        context = multiprocessing.get_context(
            "spawn"
        )
        with ProcessPoolExecutor(
            max_workers=workers,
            mp_context=context,
            initializer=_worker_initialize,
            initargs=(
                components,
                base_seed,
                minimum_trades,
            ),
        ) as executor:
            futures: dict[
                Future[dict[str, Any]],
                int,
            ] = {
                executor.submit(
                    _worker_run,
                    index,
                ): index
                for index in pending
            }
            for future in as_completed(futures):
                rows.append(future.result())
                newly_completed += 1
                if (
                    newly_completed % 5 == 0
                    or newly_completed
                    == len(pending)
                ):
                    _atomic_checkpoint(
                        path=checkpoint_file,
                        signature=signature,
                        rows=rows,
                    )
                if (
                    (resumed + newly_completed) % 10
                    == 0
                ):
                    print(
                        "EXP-006 selection MCPT: "
                        f"{resumed + newly_completed}/"
                        f"{permutations}"
                    )

    frame = pd.DataFrame(rows).sort_values(
        "permutation"
    ).reset_index(drop=True)
    if len(frame) != permutations:
        raise RuntimeError(
            "EXP-006 MCPT did not complete every permutation."
        )
    frame["permutation_ge_real"] = frame[
        "best_selection_statistic"
    ].astype(float).ge(
        float(real_selection_statistic)
    )
    exceedances = int(
        frame["permutation_ge_real"].sum()
    )
    p_value = (
        exceedances + 1
    ) / (permutations + 1)
    info = SelectionMcptRunInfo(
        requested_workers=int(
            requested_workers
        ),
        workers_used=int(workers),
        resumed_permutations=int(resumed),
        newly_completed_permutations=int(
            newly_completed
        ),
        checkpoint_file=str(
            checkpoint_file.resolve()
        ),
        signature=signature,
    )
    return frame, float(p_value), info
