from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from exp009_engine import profit_factor


LOCKED_RESAMPLES = 10_000
LOCKED_RANDOM_SEED = 5301


def bootstrap_exp013_trade_metrics(
    trades: pd.DataFrame,
    *,
    candidate_id: str,
    resamples: int = LOCKED_RESAMPLES,
    random_seed: int = LOCKED_RANDOM_SEED,
) -> dict[str, Any]:
    if int(resamples) != LOCKED_RESAMPLES:
        raise ValueError("EXP-013 bootstrap is locked to 10,000 resamples.")
    if int(random_seed) != LOCKED_RANDOM_SEED:
        raise ValueError("EXP-013 bootstrap seed is locked to 5301.")
    if "net_pnl_usd" not in trades.columns:
        raise ValueError("EXP-013 bootstrap requires net_pnl_usd.")
    pnl = trades["net_pnl_usd"].to_numpy(dtype=float)
    if pnl.size < 2:
        raise ValueError(
            "EXP-013 bootstrap requires at least two completed trades."
        )

    generator = np.random.default_rng(int(random_seed))
    means = np.empty(int(resamples), dtype=float)
    factors = np.empty(int(resamples), dtype=float)
    for start in range(0, int(resamples), 250):
        stop = min(start + 250, int(resamples))
        samples = generator.choice(
            pnl, size=(stop - start, pnl.size), replace=True
        )
        means[start:stop] = samples.mean(axis=1)
        gains = np.where(samples > 0, samples, 0.0).sum(axis=1)
        losses = -np.where(samples < 0, samples, 0.0).sum(axis=1)
        local = np.divide(
            gains,
            losses,
            out=np.full_like(gains, np.inf),
            where=losses > 0,
        )
        local[(losses == 0) & (gains == 0)] = 0.0
        factors[start:stop] = local

    finite = factors[np.isfinite(factors)]
    pf_interval: list[float | None] = (
        [float(np.percentile(finite, 2.5)), float(np.percentile(finite, 97.5))]
        if finite.size
        else [None, None]
    )
    return {
        "candidate_id": str(candidate_id),
        "resamples": int(resamples),
        "random_seed": int(random_seed),
        "sampling_unit": "completed_trade",
        "completed_trades": int(pnl.size),
        "observed_average_trade_usd": float(pnl.mean()),
        "observed_trade_profit_factor": float(profit_factor(pnl)),
        "average_trade_usd_95_percentile_interval": [
            float(np.percentile(means, 2.5)),
            float(np.percentile(means, 97.5)),
        ],
        "trade_profit_factor_95_percentile_interval": pf_interval,
        "average_trade_probability_above_zero": float(
            np.mean(means > 0.0)
        ),
        "profit_factor_probability_above_one": float(
            np.mean(factors > 1.0)
        ),
        "decision_gate": False,
    }
