from __future__ import annotations

from typing import Any, Iterable

import numpy as np
import pandas as pd

from exp026_core import (
    ALL_CANDIDATE_IDS,
    BASE_ROUND_TRIP_COST_USD,
    CANDIDATE_SPEC_BY_ID,
    CONTROL_CANDIDATE_IDS,
    DEVELOPMENT_CANDIDATE_IDS,
    METRIC_SEGMENTS,
    REFERENCE_CAPITAL_USD,
    candidate_registry_frame,
    validate_candidate_specs,
)
from exp027_preregistration import (
    get_exp027_preregistration,
    validate_exp027_preregistration,
)


EXPERIMENT_ID = "EXP-027"
MARKET = "NQ"
SERIES_PREFIX = "EXP-027"
PRIMARY_COHORT_LABEL = "PRIMARY_CONFIRMATION_COHORT"
SECONDARY_COHORT_LABEL = "SECONDARY_MEASUREMENT_CONTEXT"
CONTROL_COHORT_LABEL = "FIXED_CONTROL"

CANONICAL_TRADE_COLUMNS = (
    "series_id",
    "experiment_id",
    "candidate_id",
    "family_id",
    "market",
    "trade_id",
    "session_date",
    "direction",
    "entry_time",
    "exit_time",
    "holding_minutes",
    "entry_price",
    "exit_price",
    "gross_pnl_usd",
    "transaction_cost_usd",
    "net_pnl_usd",
    "risk_points",
    "initial_risk_usd",
    "contracts",
    "exit_reason",
    "mae_usd",
    "mfe_usd",
    "captured_fraction_of_mfe",
    "source_row_number",
)

CANONICAL_EQUITY_COLUMNS = (
    "series_id",
    "experiment_id",
    "market",
    "session_date",
    "net_pnl_usd",
    "cumulative_net_pnl_usd",
    "equity_usd",
    "drawdown_usd",
    "drawdown_percent",
    "had_trade",
)


def exp027_candidate_ids() -> tuple[str, ...]:
    validate_exp027_preregistration()
    return tuple(
        get_exp027_preregistration()[
            "candidate_population"
        ]["all_candidate_ids"]
    )


def exp027_control_ids() -> tuple[str, ...]:
    validate_exp027_preregistration()
    return tuple(
        get_exp027_preregistration()[
            "candidate_population"
        ]["control_ids"]
    )


def exp027_reported_ids() -> tuple[str, ...]:
    return exp027_candidate_ids() + exp027_control_ids()


def primary_cohort_ids() -> tuple[str, ...]:
    validate_exp027_preregistration()
    return tuple(
        get_exp027_preregistration()[
            "candidate_population"
        ]["primary_confirmation_cohort"]
    )


def cohort_for(candidate_id: str) -> str:
    identifier = str(candidate_id)
    if identifier in primary_cohort_ids():
        return PRIMARY_COHORT_LABEL
    if identifier in exp027_control_ids():
        return CONTROL_COHORT_LABEL
    if identifier in exp027_candidate_ids():
        return SECONDARY_COHORT_LABEL
    raise ValueError(
        f"Unknown EXP-027 candidate identifier: {identifier}."
    )


def series_id_for(candidate_id: str) -> str:
    if candidate_id not in exp027_reported_ids():
        raise ValueError(
            f"Unknown EXP-027 series candidate: {candidate_id}."
        )
    return f"{SERIES_PREFIX}:{candidate_id}:{MARKET}"


def validate_exp027_population() -> None:
    validate_exp027_preregistration()
    validate_candidate_specs()

    candidates = exp027_candidate_ids()
    controls = exp027_control_ids()
    reported = exp027_reported_ids()
    primary = primary_cohort_ids()

    if candidates != tuple(DEVELOPMENT_CANDIDATE_IDS):
        raise ValueError(
            "EXP-027 strategy population differs from EXP-026."
        )
    if controls != tuple(CONTROL_CANDIDATE_IDS):
        raise ValueError(
            "EXP-027 control population differs from EXP-026."
        )
    if reported != tuple(ALL_CANDIDATE_IDS):
        raise ValueError(
            "EXP-027 reported order differs from EXP-026."
        )
    if len(candidates) != 22 or len(controls) != 2:
        raise ValueError(
            "EXP-027 population must contain 22 strategies and two controls."
        )
    if len(primary) != 3 or not set(primary).issubset(candidates):
        raise ValueError(
            "EXP-027 primary confirmation cohort changed."
        )


def candidate_registry_exp027() -> pd.DataFrame:
    validate_exp027_population()
    registry = candidate_registry_frame().copy()
    registry.insert(
        1,
        "exp027_cohort",
        registry["candidate_id"].map(cohort_for),
    )
    registry.insert(
        2,
        "primary_confirmation_cohort",
        registry["candidate_id"].isin(primary_cohort_ids()),
    )
    registry["selection_eligible_in_exp027"] = False
    return registry


def canonical_trade_ledger(
    trades: pd.DataFrame,
    *,
    candidate_id: str,
) -> pd.DataFrame:
    validate_exp027_population()
    if candidate_id not in exp027_reported_ids():
        raise ValueError(
            f"Unknown EXP-027 trade-ledger candidate: {candidate_id}."
        )

    if trades.empty:
        return pd.DataFrame(columns=CANONICAL_TRADE_COLUMNS)

    current = trades.loc[
        trades["candidate_id"].astype(str) == candidate_id
    ].copy()
    if current.empty:
        return pd.DataFrame(columns=CANONICAL_TRADE_COLUMNS)

    current = current.sort_values(
        ["session_date", "entry_timestamp_utc"],
        kind="stable",
    ).reset_index(drop=True)
    candidate = CANDIDATE_SPEC_BY_ID[candidate_id]

    entry_time = pd.to_datetime(
        current["entry_timestamp_utc"],
        errors="raise",
        utc=True,
    )
    exit_time = pd.to_datetime(
        current["exit_timestamp_utc"],
        errors="raise",
        utc=True,
    )
    holding = (
        pd.to_numeric(
            current["exit_session_minute"],
            errors="raise",
        )
        - pd.to_numeric(
            current["entry_session_minute"],
            errors="raise",
        )
    ).astype(float)

    ledger = pd.DataFrame(
        {
            "series_id": series_id_for(candidate_id),
            "experiment_id": EXPERIMENT_ID,
            "candidate_id": candidate_id,
            "family_id": candidate.family_id,
            "market": MARKET,
            "trade_id": np.arange(
                1,
                len(current) + 1,
                dtype=int,
            ),
            "session_date": current[
                "session_date"
            ].astype(str).to_numpy(),
            "direction": current[
                "direction"
            ].astype(str).to_numpy(),
            "entry_time": entry_time.map(
                lambda value: value.isoformat()
            ).to_numpy(),
            "exit_time": exit_time.map(
                lambda value: value.isoformat()
            ).to_numpy(),
            "holding_minutes": holding.to_numpy(),
            "entry_price": pd.to_numeric(
                current["entry_price"],
                errors="raise",
            ).to_numpy(dtype=float),
            "exit_price": pd.to_numeric(
                current["exit_price"],
                errors="raise",
            ).to_numpy(dtype=float),
            "gross_pnl_usd": pd.to_numeric(
                current["gross_pnl_usd"],
                errors="raise",
            ).to_numpy(dtype=float),
            "transaction_cost_usd": pd.to_numeric(
                current["transaction_cost_usd"],
                errors="raise",
            ).to_numpy(dtype=float),
            "net_pnl_usd": pd.to_numeric(
                current["net_pnl_usd"],
                errors="raise",
            ).to_numpy(dtype=float),
            "risk_points": pd.to_numeric(
                current["risk_points"],
                errors="raise",
            ).to_numpy(dtype=float),
            "initial_risk_usd": (
                pd.to_numeric(
                    current["risk_points"],
                    errors="raise",
                ).to_numpy(dtype=float)
                * 20.0
            ),
            "contracts": 1,
            "exit_reason": current[
                "exit_reason"
            ].astype(str).to_numpy(),
            "mae_usd": np.nan,
            "mfe_usd": np.nan,
            "captured_fraction_of_mfe": np.nan,
            "source_row_number": np.arange(
                1,
                len(current) + 1,
                dtype=int,
            ),
        }
    )

    if (ledger["holding_minutes"] < 0).any():
        raise ValueError(
            "EXP-027 canonical holding time cannot be negative."
        )
    if ledger["net_pnl_usd"].isna().any():
        raise ValueError(
            "EXP-027 canonical trade P&L contains missing values."
        )
    return ledger.loc[:, CANONICAL_TRADE_COLUMNS]


def dense_session_equity(
    decisions: pd.DataFrame,
    trades: pd.DataFrame,
    *,
    candidate_id: str,
) -> pd.DataFrame:
    validate_exp027_population()
    if candidate_id not in exp027_reported_ids():
        raise ValueError(
            f"Unknown EXP-027 equity candidate: {candidate_id}."
        )

    sessions = (
        decisions.loc[
            decisions["candidate_id"].astype(str)
            == candidate_id,
            "session_date",
        ]
        .astype(str)
        .drop_duplicates()
        .sort_values(kind="stable")
        .reset_index(drop=True)
    )
    if sessions.empty:
        raise ValueError(
            "EXP-027 dense equity requires a session axis."
        )

    candidate_trades = trades.loc[
        trades["candidate_id"].astype(str)
        == candidate_id
    ].copy()
    if candidate_trades.empty:
        session_pnl = pd.Series(
            dtype=float,
            name="net_pnl_usd",
        )
    else:
        session_pnl = (
            candidate_trades.groupby(
                candidate_trades["session_date"].astype(str),
                sort=True,
            )["net_pnl_usd"]
            .sum()
            .astype(float)
        )

    net = sessions.map(session_pnl).fillna(0.0).astype(float)
    cumulative = net.cumsum()
    equity = REFERENCE_CAPITAL_USD + cumulative
    running_peak = equity.cummax()
    drawdown = equity - running_peak
    drawdown_percent = (
        drawdown / running_peak.replace(0.0, np.nan) * 100.0
    )
    had_trade = sessions.isin(set(session_pnl.index))

    result = pd.DataFrame(
        {
            "series_id": series_id_for(candidate_id),
            "experiment_id": EXPERIMENT_ID,
            "market": MARKET,
            "session_date": sessions,
            "net_pnl_usd": net,
            "cumulative_net_pnl_usd": cumulative,
            "equity_usd": equity,
            "drawdown_usd": drawdown,
            "drawdown_percent": drawdown_percent,
            "had_trade": had_trade,
        }
    )
    return result.loc[:, CANONICAL_EQUITY_COLUMNS]


def comparison_timeseries(
    equity: pd.DataFrame,
    *,
    candidate_id: str,
) -> pd.DataFrame:
    candidate = CANDIDATE_SPEC_BY_ID[candidate_id]
    result = equity.copy()
    result.insert(2, "candidate_id", candidate_id)
    result.insert(3, "family_id", candidate.family_id)
    result.insert(4, "exp027_cohort", cohort_for(candidate_id))
    return result


def candidate_series_metrics(
    metrics: pd.DataFrame,
    *,
    candidate_id: str,
) -> pd.DataFrame:
    current = metrics.loc[
        metrics["candidate_id"].astype(str)
        == candidate_id
    ].copy()
    if tuple(current["segment"].astype(str)) != tuple(
        METRIC_SEGMENTS
    ):
        raise ValueError(
            "EXP-027 candidate metric segments are incomplete."
        )
    current.insert(
        1,
        "series_id",
        series_id_for(candidate_id),
    )
    current.insert(
        2,
        "exp027_cohort",
        cohort_for(candidate_id),
    )
    return current.reset_index(drop=True)


def trade_distribution(
    trades: pd.DataFrame,
    *,
    candidate_ids: Iterable[str] | None = None,
) -> pd.DataFrame:
    requested = (
        exp027_reported_ids()
        if candidate_ids is None
        else tuple(str(value) for value in candidate_ids)
    )
    rows: list[dict[str, Any]] = []
    for candidate_id in requested:
        current = trades.loc[
            trades["candidate_id"].astype(str)
            == candidate_id,
            "net_pnl_usd",
        ].astype(float)
        count = int(len(current))
        positive = current.loc[current > 0].sort_values(
            ascending=False
        )
        positive_sum = float(positive.sum())

        def share(top: int) -> float:
            if positive_sum <= 0:
                return float("nan")
            return float(
                positive.head(top).sum() / positive_sum
            )

        rows.append(
            {
                "candidate_id": candidate_id,
                "exp027_cohort": cohort_for(candidate_id),
                "completed_trades": count,
                "minimum_trade_usd": (
                    float(current.min())
                    if count
                    else float("nan")
                ),
                "q05_trade_usd": (
                    float(current.quantile(0.05))
                    if count
                    else float("nan")
                ),
                "median_trade_usd": (
                    float(current.median())
                    if count
                    else float("nan")
                ),
                "q95_trade_usd": (
                    float(current.quantile(0.95))
                    if count
                    else float("nan")
                ),
                "maximum_trade_usd": (
                    float(current.max())
                    if count
                    else float("nan")
                ),
                "top_1_winner_share": share(1),
                "top_5_winner_share": share(5),
                "top_10_winner_share": share(10),
            }
        )
    return pd.DataFrame(rows)


def drawdown_episodes(
    equity_by_candidate: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for candidate_id in exp027_reported_ids():
        equity = equity_by_candidate[candidate_id]
        active = False
        start_index = 0
        episode_number = 0
        for index, row in equity.reset_index(drop=True).iterrows():
            below_peak = float(row["drawdown_usd"]) < 0
            if below_peak and not active:
                active = True
                start_index = index
                episode_number += 1
            next_below = (
                index + 1 < len(equity)
                and float(
                    equity.iloc[index + 1]["drawdown_usd"]
                ) < 0
            )
            if active and not next_below:
                episode = equity.iloc[
                    start_index : index + 1
                ]
                trough_index = int(
                    episode["drawdown_usd"].astype(float).idxmin()
                )
                trough = equity.loc[trough_index]
                recovered = not below_peak or (
                    index + 1 < len(equity)
                    and float(
                        equity.iloc[index + 1]["drawdown_usd"]
                    ) == 0
                )
                rows.append(
                    {
                        "candidate_id": candidate_id,
                        "exp027_cohort": cohort_for(candidate_id),
                        "episode_number": episode_number,
                        "start_session": str(
                            episode.iloc[0]["session_date"]
                        ),
                        "trough_session": str(
                            trough["session_date"]
                        ),
                        "end_session": str(
                            equity.iloc[index]["session_date"]
                        ),
                        "maximum_drawdown_usd": float(
                            trough["drawdown_usd"]
                        ),
                        "maximum_drawdown_percent": float(
                            trough["drawdown_percent"]
                        ),
                        "duration_sessions": int(len(episode)),
                        "recovered": bool(recovered),
                    }
                )
                active = False
    return pd.DataFrame(rows)


def representation_sensitivity(
    primary_metrics: pd.DataFrame,
    secondary_metrics: pd.DataFrame,
) -> pd.DataFrame:
    keys = (
        "candidate_id",
        "family_id",
        "candidate_role",
        "segment",
    )
    columns = (
        "completed_trades",
        "net_profit_usd",
        "trade_profit_factor",
        "maximum_drawdown_usd",
        "win_rate",
    )
    left = primary_metrics.loc[:, (*keys, *columns)].copy()
    right = secondary_metrics.loc[:, (*keys, *columns)].copy()
    merged = left.merge(
        right,
        on=list(keys),
        how="outer",
        suffixes=(
            "_backward_adjusted",
            "_unadjusted",
        ),
        validate="one_to_one",
    )
    merged.insert(
        1,
        "exp027_cohort",
        merged["candidate_id"].map(cohort_for),
    )
    for column in columns:
        merged[f"{column}_difference"] = (
            pd.to_numeric(
                merged[f"{column}_unadjusted"],
                errors="coerce",
            )
            - pd.to_numeric(
                merged[f"{column}_backward_adjusted"],
                errors="coerce",
            )
        )
    return merged


def historical_context(
    phase_a: pd.DataFrame,
    phase_b: pd.DataFrame,
    phase_c: pd.DataFrame,
) -> pd.DataFrame:
    metric_columns = (
        "completed_trades",
        "net_profit_usd",
        "trade_profit_factor",
        "maximum_drawdown_usd",
        "win_rate",
    )

    def prepare(
        frame: pd.DataFrame,
        prefix: str,
    ) -> pd.DataFrame:
        if frame.empty:
            return pd.DataFrame(
                columns=("candidate_id",)
            )
        current = frame.loc[
            frame["segment"].astype(str) == "ALL_TRADES"
        ].copy()
        current = current.loc[
            :,
            (
                "candidate_id",
                *[
                    column
                    for column in metric_columns
                    if column in current.columns
                ],
            ),
        ]
        return current.rename(
            columns={
                column: f"{prefix}_{column}"
                for column in current.columns
                if column != "candidate_id"
            }
        )

    result = pd.DataFrame(
        {
            "candidate_id": exp027_reported_ids(),
        }
    )
    result.insert(
        1,
        "exp027_cohort",
        result["candidate_id"].map(cohort_for),
    )
    for frame, prefix in (
        (phase_a, "phase_a_2010_2017"),
        (phase_b, "phase_b_2018_2019"),
        (phase_c, "phase_c_2020_2025"),
    ):
        result = result.merge(
            prepare(frame, prefix),
            on="candidate_id",
            how="left",
            validate="one_to_one",
        )
    result["historical_context_available"] = result[
        [
            column
            for column in result.columns
            if column.endswith("_completed_trades")
        ]
    ].notna().any(axis=1)
    return result


def validate_result_frames(
    *,
    decisions: pd.DataFrame,
    trades: pd.DataFrame,
    metrics: pd.DataFrame,
) -> None:
    validate_exp027_population()
    expected_ids = set(exp027_reported_ids())
    decision_ids = set(
        decisions["candidate_id"].astype(str).unique()
    )
    metric_ids = set(
        metrics["candidate_id"].astype(str).unique()
    )
    if decision_ids != expected_ids:
        raise ValueError(
            "EXP-027 decisions do not cover all 24 rows."
        )
    if metric_ids != expected_ids:
        raise ValueError(
            "EXP-027 metrics do not cover all 24 rows."
        )
    if decisions.duplicated(
        ["candidate_id", "session_date"]
    ).any():
        raise ValueError(
            "EXP-027 decisions contain duplicates."
        )
    if not trades.empty and trades.duplicated(
        ["candidate_id", "session_date"]
    ).any():
        raise ValueError(
            "EXP-027 trades exceed one per candidate-session."
        )
    if len(metrics) != len(expected_ids) * len(METRIC_SEGMENTS):
        raise ValueError(
            "EXP-027 metrics must contain 72 candidate-segment rows."
        )
    if (
        pd.to_numeric(
            trades.get(
                "transaction_cost_usd",
                pd.Series(dtype=float),
            ),
            errors="coerce",
        )
        .dropna()
        .ne(BASE_ROUND_TRIP_COST_USD)
        .any()
    ):
        raise ValueError(
            "EXP-027 base transaction costs changed."
        )
