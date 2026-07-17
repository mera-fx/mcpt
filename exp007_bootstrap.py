from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from exp007_orb import profit_factor


def bootstrap_trade_metrics(
    trades: pd.DataFrame,
    *,
    resamples: int = 10_000,
    random_seed: int = 4701,
) -> dict[str, Any]:
    if int(resamples) != 10_000:
        raise ValueError(
            "EXP-007 bootstrap is locked to 10,000 resamples."
        )
    if int(random_seed) != 4701:
        raise ValueError("EXP-007 bootstrap seed is locked to 4701.")
    if "net_pnl_usd" not in trades.columns:
        raise ValueError("EXP-007 bootstrap requires net_pnl_usd.")

    pnl = trades["net_pnl_usd"].to_numpy(dtype=float)
    if pnl.size < 2:
        raise ValueError(
            "EXP-007 bootstrap requires at least two completed trades."
        )

    generator = np.random.default_rng(int(random_seed))
    average_trade = np.empty(int(resamples), dtype=float)
    trade_pf = np.empty(int(resamples), dtype=float)

    for start in range(0, int(resamples), 250):
        stop = min(start + 250, int(resamples))
        samples = generator.choice(
            pnl,
            size=(stop - start, pnl.size),
            replace=True,
        )
        average_trade[start:stop] = samples.mean(axis=1)
        for offset, sample in enumerate(samples):
            trade_pf[start + offset] = profit_factor(sample)

    finite_pf = trade_pf[np.isfinite(trade_pf)]
    if finite_pf.size == 0:
        pf_interval = [None, None]
    else:
        pf_interval = [
            float(np.percentile(finite_pf, 2.5)),
            float(np.percentile(finite_pf, 97.5)),
        ]

    return {
        "resamples": int(resamples),
        "random_seed": int(random_seed),
        "sampling_unit": "completed_trade",
        "completed_trades": int(pnl.size),
        "observed_average_trade_usd": float(pnl.mean()),
        "observed_trade_profit_factor": float(profit_factor(pnl)),
        "average_trade_usd_95_percentile_interval": [
            float(np.percentile(average_trade, 2.5)),
            float(np.percentile(average_trade, 97.5)),
        ],
        "trade_profit_factor_95_percentile_interval": pf_interval,
        "average_trade_probability_above_zero": float(
            np.mean(average_trade > 0.0)
        ),
        "decision_gate": False,
    }
