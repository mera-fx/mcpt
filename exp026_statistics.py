from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

from exp026_core import (
    CANDIDATE_SPEC_BY_ID,
    DEVELOPMENT_CANDIDATE_IDS,
    DIRECTION_ALL,
    annual_results,
    candidate_metrics,
    select_phase_a_survivors,
    select_phase_b_finalists,
)


@dataclass(frozen=True)
class SessionOutcomeMatrices:
    session_dates: tuple[str, ...]
    candidate_ids: tuple[str, ...]
    real_net: np.ndarray
    mirrored_net: np.ndarray
    trade_flags: np.ndarray


def build_session_outcome_matrices(
    trades: pd.DataFrame,
    mirrored_outcomes: pd.DataFrame,
    *,
    session_dates: Iterable[str],
    candidate_ids: Iterable[str] = DEVELOPMENT_CANDIDATE_IDS,
) -> SessionOutcomeMatrices:
    dates = tuple(str(value) for value in session_dates)
    candidates = tuple(str(value) for value in candidate_ids)
    if not dates or dates != tuple(sorted(set(dates))):
        raise ValueError(
            "EXP-026 session outcomes require a sorted unique date axis."
        )
    if (
        not candidates
        or len(set(candidates)) != len(candidates)
        or not set(candidates).issubset(
            DEVELOPMENT_CANDIDATE_IDS
        )
    ):
        raise ValueError(
            "EXP-026 session outcomes contain invalid candidates."
        )

    date_index = {
        value: index
        for index, value in enumerate(dates)
    }
    candidate_index = {
        value: index
        for index, value in enumerate(candidates)
    }
    shape = (len(dates), len(candidates))
    real = np.zeros(shape, dtype=np.float64)
    mirrored = np.zeros(shape, dtype=np.float64)
    flags = np.zeros(shape, dtype=bool)

    mirror_lookup = {
        (
            str(row.candidate_id),
            str(row.session_date),
        ): float(row.mirrored_net_pnl_usd)
        for row in mirrored_outcomes.itertuples(
            index=False
        )
    }
    for row in trades.itertuples(index=False):
        candidate_id = str(row.candidate_id)
        session_date = str(row.session_date)
        if candidate_id not in candidate_index:
            continue
        if session_date not in date_index:
            raise ValueError(
                "EXP-026 trade lies outside the session-outcome axis."
            )
        key = (candidate_id, session_date)
        if key not in mirror_lookup:
            raise ValueError(
                "EXP-026 mirrored outcome is missing for a real trade."
            )
        i = date_index[session_date]
        j = candidate_index[candidate_id]
        if flags[i, j]:
            raise ValueError(
                "EXP-026 session outcomes exceed one trade per "
                "candidate-session."
            )
        flags[i, j] = True
        real[i, j] = float(row.net_pnl_usd)
        mirrored[i, j] = mirror_lookup[key]

    expected_keys = {
        (
            str(row.candidate_id),
            str(row.session_date),
        )
        for row in trades.itertuples(index=False)
        if str(row.candidate_id) in candidate_index
    }
    extra_keys = set(mirror_lookup).difference(
        expected_keys
    )
    if extra_keys:
        raise ValueError(
            "EXP-026 mirrored outcomes contain unmatched trades."
        )
    return SessionOutcomeMatrices(
        session_dates=dates,
        candidate_ids=candidates,
        real_net=real,
        mirrored_net=mirrored,
        trade_flags=flags,
    )


def _maximum_drawdown(values: np.ndarray) -> float:
    if len(values) == 0:
        return 0.0
    equity = np.cumsum(values, dtype=float)
    with_zero = np.concatenate(([0.0], equity))
    running = np.maximum.accumulate(with_zero)
    return float((with_zero - running).min())


def _metric_rows_from_matrix(
    values: np.ndarray,
    flags: np.ndarray,
    *,
    candidate_ids: Sequence[str],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for column, candidate_id in enumerate(
        candidate_ids
    ):
        current = values[:, column][
            flags[:, column]
        ]
        positives = float(
            current[current > 0].sum()
        )
        negatives = float(
            current[current < 0].sum()
        )
        if negatives < 0:
            profit_factor = (
                positives / abs(negatives)
            )
        elif positives > 0:
            profit_factor = float("inf")
        else:
            profit_factor = float("nan")
        drawdown = _maximum_drawdown(current)
        net_profit = float(current.sum())
        rows.append(
            {
                "candidate_id": candidate_id,
                "family_id": (
                    CANDIDATE_SPEC_BY_ID[
                        candidate_id
                    ].family_id
                ),
                "candidate_role": "DEVELOPMENT",
                "segment": DIRECTION_ALL,
                "completed_trades": int(
                    len(current)
                ),
                "net_profit_usd": net_profit,
                "trade_profit_factor": float(
                    profit_factor
                ),
                "maximum_drawdown_usd": drawdown,
                "net_profit_to_drawdown": (
                    net_profit / abs(drawdown)
                    if drawdown < 0
                    else (
                        float("inf")
                        if net_profit > 0
                        else float("nan")
                    )
                ),
            }
        )
    return pd.DataFrame(rows)


def _annual_rows_from_matrix(
    values: np.ndarray,
    flags: np.ndarray,
    *,
    session_dates: Sequence[str],
    candidate_ids: Sequence[str],
) -> pd.DataFrame:
    years = np.array(
        [
            int(value[:4])
            for value in session_dates
        ],
        dtype=int,
    )
    rows: list[dict[str, Any]] = []
    for column, candidate_id in enumerate(
        candidate_ids
    ):
        for year in sorted(set(years)):
            mask = (
                (years == year)
                & flags[:, column]
            )
            current = values[:, column][mask]
            positives = float(
                current[current > 0].sum()
            )
            negatives = float(
                current[current < 0].sum()
            )
            if negatives < 0:
                pf = positives / abs(negatives)
            elif positives > 0:
                pf = float("inf")
            else:
                pf = float("nan")
            rows.append(
                {
                    "candidate_id": candidate_id,
                    "family_id": (
                        CANDIDATE_SPEC_BY_ID[
                            candidate_id
                        ].family_id
                    ),
                    "candidate_role": (
                        "DEVELOPMENT"
                    ),
                    "year": int(year),
                    "completed_trades": int(
                        len(current)
                    ),
                    "net_profit_usd": float(
                        current.sum()
                    ),
                    "trade_profit_factor": float(
                        pf
                    ),
                    "maximum_drawdown_usd": (
                        _maximum_drawdown(current)
                    ),
                    "win_rate": (
                        float((current > 0).mean())
                        if len(current)
                        else float("nan")
                    ),
                }
            )
    return pd.DataFrame(rows)


def select_from_matrix(
    values: np.ndarray,
    flags: np.ndarray,
    *,
    session_dates: Sequence[str],
    candidate_ids: Sequence[str],
    phase_a_end: str,
    phase_b_start: str,
    phase_b_end: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    dates = np.array(
        tuple(str(value) for value in session_dates)
    )
    development_mask = dates <= phase_a_end
    validation_mask = (
        (dates >= phase_b_start)
        & (dates <= phase_b_end)
    )
    development_metrics = (
        _metric_rows_from_matrix(
            values[development_mask],
            flags[development_mask],
            candidate_ids=candidate_ids,
        )
    )
    survivors = select_phase_a_survivors(
        development_metrics,
        candidate_ids=candidate_ids,
        maximum_per_family=2,
    )
    survivor_ids = tuple(
        survivors["candidate_id"].astype(str)
    )
    validation_metrics = _metric_rows_from_matrix(
        values[validation_mask],
        flags[validation_mask],
        candidate_ids=candidate_ids,
    )
    validation_annual = _annual_rows_from_matrix(
        values[validation_mask],
        flags[validation_mask],
        session_dates=dates[
            validation_mask
        ],
        candidate_ids=candidate_ids,
    )
    finalists = select_phase_b_finalists(
        development_metrics,
        validation_metrics,
        validation_annual,
        phase_a_candidate_ids=survivor_ids,
        maximum_per_family=1,
    )
    return survivors, finalists


def selection_rank_statistic(
    validation_metrics: pd.DataFrame,
    finalists: pd.DataFrame,
) -> float:
    if finalists.empty:
        return 0.0
    current = validation_metrics.loc[
        (validation_metrics["segment"] == DIRECTION_ALL)
        & (
            validation_metrics["candidate_role"]
            == "DEVELOPMENT"
        )
        & (
            validation_metrics["completed_trades"]
            > 0
        )
    ].copy()
    total = 0.0
    for family_id, family in current.groupby(
        "family_id",
        sort=True,
    ):
        family = family.sort_values(
            [
                "net_profit_to_drawdown",
                "candidate_id",
            ],
            ascending=[False, True],
            kind="stable",
            na_position="last",
        ).reset_index(drop=True)
        points = {
            str(candidate_id): (
                len(family) - index
            )
            for index, candidate_id in enumerate(
                family["candidate_id"]
            )
        }
        selected = finalists.loc[
            finalists["family_id"] == family_id,
            "candidate_id",
        ]
        if not selected.empty:
            total += float(
                points.get(
                    str(selected.iloc[0]),
                    0,
                )
            )
    return total


def selection_aware_market_mcpt(
    matrices: SessionOutcomeMatrices,
    *,
    phase_a_end: str = "2017-12-31",
    phase_b_start: str = "2018-01-01",
    phase_b_end: str = "2019-12-31",
    permutations: int = 1_000,
    random_seed: int = 26_026,
) -> tuple[dict[str, Any], pd.DataFrame]:
    if permutations < 1:
        raise ValueError(
            "EXP-026 MCPT requires at least one permutation."
        )
    dates = np.array(matrices.session_dates)
    validation_mask = (
        (dates >= phase_b_start)
        & (dates <= phase_b_end)
    )

    real_survivors, real_finalists = (
        select_from_matrix(
            matrices.real_net,
            matrices.trade_flags,
            session_dates=matrices.session_dates,
            candidate_ids=matrices.candidate_ids,
            phase_a_end=phase_a_end,
            phase_b_start=phase_b_start,
            phase_b_end=phase_b_end,
        )
    )
    real_validation_metrics = (
        _metric_rows_from_matrix(
            matrices.real_net[validation_mask],
            matrices.trade_flags[
                validation_mask
            ],
            candidate_ids=matrices.candidate_ids,
        )
    )
    real_statistic = selection_rank_statistic(
        real_validation_metrics,
        real_finalists,
    )

    rng = np.random.default_rng(
        random_seed
    )
    rows: list[dict[str, Any]] = []
    greater_or_equal = 0
    for permutation_index in range(
        permutations
    ):
        # One session-shared sign choice is used across all 22 candidates.
        # This preserves cross-candidate dependence while conditionally
        # breaking the alignment between entry-known setups and the realised
        # post-entry path.
        use_mirror = rng.integers(
            0,
            2,
            size=(len(matrices.session_dates), 1),
            dtype=np.int8,
        ).astype(bool)
        current = np.where(
            use_mirror,
            matrices.mirrored_net,
            matrices.real_net,
        )
        survivors, finalists = select_from_matrix(
            current,
            matrices.trade_flags,
            session_dates=matrices.session_dates,
            candidate_ids=matrices.candidate_ids,
            phase_a_end=phase_a_end,
            phase_b_start=phase_b_start,
            phase_b_end=phase_b_end,
        )
        validation_metrics = (
            _metric_rows_from_matrix(
                current[validation_mask],
                matrices.trade_flags[
                    validation_mask
                ],
                candidate_ids=(
                    matrices.candidate_ids
                ),
            )
        )
        statistic = selection_rank_statistic(
            validation_metrics,
            finalists,
        )
        if statistic >= real_statistic:
            greater_or_equal += 1
        rows.append(
            {
                "permutation_index": int(
                    permutation_index
                ),
                "random_seed": int(
                    random_seed
                    + permutation_index
                ),
                "statistic": float(statistic),
                "phase_a_survivor_count": int(
                    len(survivors)
                ),
                "phase_b_finalist_count": int(
                    len(finalists)
                ),
                "selected_candidate_ids": "|".join(
                    finalists["candidate_id"].astype(
                        str
                    )
                ),
            }
        )

    plus_one_p_value = (
        greater_or_equal + 1
    ) / (permutations + 1)
    summary = {
        "permutations": int(permutations),
        "random_seed": int(random_seed),
        "null_method": (
            "SESSION_SHARED_POST_ENTRY_PATH_SIGN_PERMUTATION"
        ),
        "signals_conditioned_on_entry_known_data": True,
        "all_22_candidates_inside_each_permutation": True,
        "phase_a_and_phase_b_selection_repeated": True,
        "real_statistic": float(real_statistic),
        "permutations_greater_or_equal_real": int(
            greater_or_equal
        ),
        "plus_one_p_value": float(
            plus_one_p_value
        ),
        "decision_gate": False,
        "real_phase_a_survivors": tuple(
            real_survivors[
                "candidate_id"
            ].astype(str)
        ),
        "real_phase_b_finalists": tuple(
            real_finalists[
                "candidate_id"
            ].astype(str)
        ),
    }
    return summary, pd.DataFrame(rows)


def bootstrap_session_blocks(
    trades: pd.DataFrame,
    *,
    candidate_ids: Iterable[str],
    session_dates: Iterable[str],
    resamples: int = 10_000,
    random_seed: int = 26_027,
    confidence_level: float = 0.95,
) -> pd.DataFrame:
    if resamples < 1:
        raise ValueError(
            "EXP-026 bootstrap requires at least one resample."
        )
    if not 0 < confidence_level < 1:
        raise ValueError(
            "EXP-026 bootstrap confidence level is invalid."
        )

    dates = tuple(str(value) for value in session_dates)
    candidates = tuple(str(value) for value in candidate_ids)
    date_index = {
        value: index
        for index, value in enumerate(dates)
    }
    candidate_index = {
        value: index
        for index, value in enumerate(candidates)
    }
    net = np.zeros(
        (len(dates), len(candidates)),
        dtype=float,
    )
    positive = np.zeros_like(net)
    negative = np.zeros_like(net)
    flags = np.zeros_like(net, dtype=bool)

    for row in trades.itertuples(index=False):
        candidate_id = str(row.candidate_id)
        session_date = str(row.session_date)
        if candidate_id not in candidate_index:
            continue
        i = date_index[session_date]
        j = candidate_index[candidate_id]
        value = float(row.net_pnl_usd)
        net[i, j] = value
        positive[i, j] = max(value, 0.0)
        negative[i, j] = min(value, 0.0)
        flags[i, j] = True

    rng = np.random.default_rng(random_seed)
    sample_indices = rng.integers(
        0,
        len(dates),
        size=(resamples, len(dates)),
    )
    sampled_net = net[sample_indices].sum(axis=1)
    sampled_positive = positive[
        sample_indices
    ].sum(axis=1)
    sampled_negative = negative[
        sample_indices
    ].sum(axis=1)
    sampled_trade_count = flags[
        sample_indices
    ].sum(axis=1)
    sampled_pf = np.divide(
        sampled_positive,
        np.abs(sampled_negative),
        out=np.full_like(
            sampled_positive,
            np.nan,
            dtype=float,
        ),
        where=sampled_negative < 0,
    )
    no_loss = (
        (sampled_negative == 0)
        & (sampled_positive > 0)
    )
    sampled_pf[no_loss] = np.inf

    alpha = (1.0 - confidence_level) / 2.0
    rows: list[dict[str, Any]] = []
    for column, candidate_id in enumerate(
        candidates
    ):
        finite_pf = sampled_pf[:, column][
            np.isfinite(sampled_pf[:, column])
        ]
        rows.append(
            {
                "candidate_id": candidate_id,
                "resamples": int(resamples),
                "random_seed": int(random_seed),
                "confidence_level": float(
                    confidence_level
                ),
                "net_profit_mean_usd": float(
                    sampled_net[:, column].mean()
                ),
                "net_profit_lower_usd": float(
                    np.quantile(
                        sampled_net[:, column],
                        alpha,
                    )
                ),
                "net_profit_upper_usd": float(
                    np.quantile(
                        sampled_net[:, column],
                        1.0 - alpha,
                    )
                ),
                "profit_factor_median": (
                    float(np.median(finite_pf))
                    if len(finite_pf)
                    else float("nan")
                ),
                "profit_factor_lower": (
                    float(
                        np.quantile(
                            finite_pf,
                            alpha,
                        )
                    )
                    if len(finite_pf)
                    else float("nan")
                ),
                "profit_factor_upper": (
                    float(
                        np.quantile(
                            finite_pf,
                            1.0 - alpha,
                        )
                    )
                    if len(finite_pf)
                    else float("nan")
                ),
                "trade_count_mean": float(
                    sampled_trade_count[
                        :, column
                    ].mean()
                ),
                "probability_net_profit_positive": float(
                    (
                        sampled_net[:, column] > 0
                    ).mean()
                ),
                "decision_gate": False,
            }
        )
    return pd.DataFrame(rows)


def anchored_walk_forward(
    trades: pd.DataFrame,
    *,
    test_years: Sequence[int] = (
        2014,
        2015,
        2016,
        2017,
        2018,
        2019,
    ),
    training_start: str = "2010-06-07",
) -> pd.DataFrame:
    local = trades.loc[
        trades["candidate_id"].isin(
            DEVELOPMENT_CANDIDATE_IDS
        )
    ].copy()
    rows: list[dict[str, Any]] = []
    for test_year in test_years:
        development_end_year = int(
            test_year
        ) - 3
        validation_start_year = int(
            test_year
        ) - 2
        validation_end_year = int(
            test_year
        ) - 1
        development_end = (
            f"{development_end_year}-12-31"
        )
        validation_start = (
            f"{validation_start_year}-01-01"
        )
        validation_end = (
            f"{validation_end_year}-12-31"
        )
        test_start = f"{test_year}-01-01"
        test_end = f"{test_year}-12-31"

        development_metrics = candidate_metrics(
            local,
            candidate_ids=(
                DEVELOPMENT_CANDIDATE_IDS
            ),
            period_start=training_start,
            period_end=development_end,
        )
        survivors = select_phase_a_survivors(
            development_metrics,
            maximum_per_family=2,
        )
        survivor_ids = tuple(
            survivors["candidate_id"].astype(
                str
            )
        )

        validation_metrics = candidate_metrics(
            local,
            candidate_ids=(
                DEVELOPMENT_CANDIDATE_IDS
            ),
            period_start=validation_start,
            period_end=validation_end,
        )
        validation_annual = annual_results(
            local.loc[
                local["session_date"].astype(
                    str
                ).between(
                    validation_start,
                    validation_end,
                )
            ],
            candidate_ids=(
                DEVELOPMENT_CANDIDATE_IDS
            ),
            start_year=validation_start_year,
            end_year=validation_end_year,
        )
        finalists = select_phase_b_finalists(
            development_metrics,
            validation_metrics,
            validation_annual,
            phase_a_candidate_ids=survivor_ids,
            maximum_per_family=1,
        )
        finalist_ids = tuple(
            finalists["candidate_id"].astype(
                str
            )
        )
        test_metrics = candidate_metrics(
            local,
            candidate_ids=finalist_ids,
            period_start=test_start,
            period_end=test_end,
        )
        test_all = test_metrics.loc[
            test_metrics["segment"]
            == DIRECTION_ALL
        ]
        for family_id in (
            "gap_fade",
            "premarket_momentum_continuation",
            "opening_drive_continuation",
        ):
            selected = finalists.loc[
                finalists["family_id"]
                == family_id
            ]
            if selected.empty:
                rows.append(
                    {
                        "test_year": int(test_year),
                        "training_start": (
                            training_start
                        ),
                        "development_end": (
                            development_end
                        ),
                        "validation_start": (
                            validation_start
                        ),
                        "validation_end": (
                            validation_end
                        ),
                        "family_id": family_id,
                        "selected_candidate_id": "",
                        "completed_trades": 0,
                        "net_profit_usd": 0.0,
                        "trade_profit_factor": np.nan,
                        "maximum_drawdown_usd": 0.0,
                        "no_candidate_selected": True,
                    }
                )
                continue
            candidate_id = str(
                selected.iloc[0][
                    "candidate_id"
                ]
            )
            metric = test_all.loc[
                test_all["candidate_id"]
                == candidate_id
            ].iloc[0]
            rows.append(
                {
                    "test_year": int(test_year),
                    "training_start": (
                        training_start
                    ),
                    "development_end": (
                        development_end
                    ),
                    "validation_start": (
                        validation_start
                    ),
                    "validation_end": (
                        validation_end
                    ),
                    "family_id": family_id,
                    "selected_candidate_id": (
                        candidate_id
                    ),
                    "completed_trades": int(
                        metric[
                            "completed_trades"
                        ]
                    ),
                    "net_profit_usd": float(
                        metric["net_profit_usd"]
                    ),
                    "trade_profit_factor": float(
                        metric[
                            "trade_profit_factor"
                        ]
                    ),
                    "maximum_drawdown_usd": float(
                        metric[
                            "maximum_drawdown_usd"
                        ]
                    ),
                    "no_candidate_selected": False,
                }
            )
    return pd.DataFrame(rows)
