from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from exp011_sizing import Exp011SizedResult


BOOTSTRAP_RESAMPLES = 10_000
BOOTSTRAP_SEED = 5_111


def _session_vectors(
    result: Exp011SizedResult,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    dates = result.equity_curve["session_date"].astype(str).to_numpy()
    pnl = result.equity_curve["session_net_pnl_usd"].to_numpy(
        dtype=float
    )
    risk_by_session = (
        result.trades.groupby("session_date")["initial_risk_usd"].sum()
        if not result.trades.empty
        else pd.Series(dtype=float)
    )
    risk = (
        pd.Series(dates)
        .map(risk_by_session)
        .fillna(0.0)
        .to_numpy(dtype=float)
    )
    return dates, pnl, risk


def paired_sizing_bootstrap(
    baseline: Exp011SizedResult,
    comparison: Exp011SizedResult,
    *,
    comparison_scale_to_nq: float = 1.0,
    resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, Any]:
    if baseline.signal_candidate_id != comparison.signal_candidate_id:
        raise ValueError(
            "Paired sizing bootstrap requires the same signal variant."
        )
    if baseline.sizing_id != "fixed_one_nq":
        raise ValueError("Paired sizing baseline must be fixed_one_nq.")
    if resamples <= 0:
        raise ValueError("Bootstrap resamples must be positive.")
    if comparison_scale_to_nq <= 0:
        raise ValueError("Comparison scale must be positive.")

    base_dates, base_pnl, base_risk = _session_vectors(baseline)
    comp_dates, comp_pnl, comp_risk = _session_vectors(comparison)
    if not np.array_equal(base_dates, comp_dates):
        raise ValueError(
            "Paired sizing bootstrap session dates do not match."
        )

    scaled_pnl = comp_pnl * comparison_scale_to_nq
    scaled_risk = comp_risk * comparison_scale_to_nq
    pnl_difference = scaled_pnl - base_pnl
    risk_difference = scaled_risk - base_risk
    absolute_risk_gap = np.abs(scaled_risk - base_risk)

    rng = np.random.default_rng(seed)
    sample_count = len(base_dates)
    sampled_pnl_means = np.empty(resamples, dtype=float)
    sampled_risk_means = np.empty(resamples, dtype=float)
    sampled_gap_means = np.empty(resamples, dtype=float)
    for index in range(resamples):
        chosen = rng.integers(0, sample_count, size=sample_count)
        sampled_pnl_means[index] = float(pnl_difference[chosen].mean())
        sampled_risk_means[index] = float(
            risk_difference[chosen].mean()
        )
        sampled_gap_means[index] = float(
            absolute_risk_gap[chosen].mean()
        )

    pnl_interval = np.percentile(sampled_pnl_means, [2.5, 97.5])
    risk_interval = np.percentile(sampled_risk_means, [2.5, 97.5])
    gap_interval = np.percentile(sampled_gap_means, [2.5, 97.5])
    return {
        "signal_candidate_id": baseline.signal_candidate_id,
        "baseline_sizing_id": baseline.sizing_id,
        "comparison_sizing_id": comparison.sizing_id,
        "comparison_scale_to_nq": float(comparison_scale_to_nq),
        "evaluation_sessions": int(sample_count),
        "resamples": int(resamples),
        "random_seed": int(seed),
        "paired_by_session": True,
        "observed_mean_session_pnl_difference_usd": float(
            pnl_difference.mean()
        ),
        "mean_session_pnl_difference_95_percentile_interval": [
            float(pnl_interval[0]),
            float(pnl_interval[1]),
        ],
        "probability_mean_session_pnl_difference_above_zero": float(
            np.mean(sampled_pnl_means > 0)
        ),
        "observed_mean_initial_risk_difference_usd": float(
            risk_difference.mean()
        ),
        "mean_absolute_risk_difference_95_percentile_interval": [
            float(risk_interval[0]),
            float(risk_interval[1]),
        ],
        "observed_mean_absolute_session_risk_gap_usd": float(
            absolute_risk_gap.mean()
        ),
        "mean_absolute_session_risk_gap_95_percentile_interval": [
            float(gap_interval[0]),
            float(gap_interval[1]),
        ],
        "decision_gate": False,
        "signal_edge_confirmation": False,
    }
