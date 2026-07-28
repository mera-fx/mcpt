from __future__ import annotations

# EXP-026-I1: pre-result authorization-lifecycle compatibility correction.

from dataclasses import dataclass
from datetime import date, datetime
import hashlib
import json
import math
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

from exp026_preregistration import (
    get_exp026_preregistration,
    validate_exp026_preregistration,
)


RESEARCH_TIMEZONE = "America/New_York"
REPRESENTATION_IDS = (
    "BACKWARD_ADJUSTED",
    "UNADJUSTED",
)
SOURCE_COLUMNS = (
    "ts_event",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "trading_date",
)

SESSION_START_CLOCK_MINUTE = 18 * 60
SESSION_LAST_MINUTE = 1319
PREMARKET_START_SESSION_MINUTE = 840
CASH_START_SESSION_MINUTE = 930
CASH_END_SESSION_MINUTE = 1320

GAP_AND_PREMARKET_ENTRY_MINUTE = 935
OPENING_DRIVE_ENTRY_MINUTE = 960
STANDARD_FORCED_FLAT_MINUTE = 1315
EXP007_FORCED_FLAT_MINUTE = 1200

PREMARKET_FIVE_MINUTE_BINS = tuple(range(168, 186))
CASH_FIVE_MINUTE_BINS = tuple(range(186, 264))
FIRST_CASH_FIVE_MINUTE_BIN = 186
OPENING_DRIVE_RANGE_BINS = tuple(range(186, 192))

NQ_MULTIPLIER_USD_PER_POINT = 20.0
NQ_TICK_SIZE_POINTS = 0.25
NQ_TICK_VALUE_USD = 5.0
NQ_FEES_USD_PER_SIDE = 2.50
BASE_SLIPPAGE_TICKS_PER_SIDE = 1.0
BASE_ROUND_TRIP_COST_USD = 15.0
REFERENCE_CAPITAL_USD = 100_000.0

DIRECTION_ALL = "ALL_TRADES"
DIRECTION_LONG = "LONG_TRADES"
DIRECTION_SHORT = "SHORT_TRADES"
METRIC_SEGMENTS = (
    DIRECTION_ALL,
    DIRECTION_LONG,
    DIRECTION_SHORT,
)

DECISION_COLUMNS = (
    "representation_id",
    "candidate_id",
    "family_id",
    "candidate_role",
    "session_date",
    "eligible",
    "ineligibility_reason",
    "trade_flag",
    "direction",
    "entry_timestamp_utc",
    "entry_session_minute",
    "forced_flat_session_minute",
    "context_value",
    "threshold",
    "exit_mode",
    "setup_kind",
)

TRADE_COLUMNS = (
    "representation_id",
    "candidate_id",
    "family_id",
    "candidate_role",
    "session_date",
    "direction",
    "entry_timestamp_utc",
    "exit_timestamp_utc",
    "entry_session_minute",
    "exit_session_minute",
    "forced_flat_session_minute",
    "entry_price",
    "stop_price",
    "target_price",
    "exit_price",
    "risk_points",
    "gross_pnl_usd",
    "transaction_cost_usd",
    "net_pnl_usd",
    "exit_reason",
    "context_value",
    "threshold",
    "exit_mode",
    "setup_kind",
)

METRIC_COLUMNS = (
    "candidate_id",
    "family_id",
    "candidate_role",
    "segment",
    "completed_trades",
    "net_profit_usd",
    "gross_profit_usd",
    "gross_loss_usd",
    "trade_profit_factor",
    "win_rate",
    "average_trade_usd",
    "median_trade_usd",
    "average_winner_usd",
    "average_loser_usd",
    "payoff_ratio",
    "maximum_drawdown_usd",
    "maximum_drawdown_percent",
    "net_profit_to_drawdown",
    "drawdown_duration_trades",
    "recovery_duration_trades",
    "maximum_consecutive_losses",
    "worst_20_trade_result",
    "worst_50_trade_result",
    "worst_100_trade_result",
    "trades_per_year",
    "average_holding_minutes",
    "median_holding_minutes",
    "average_trade_to_round_trip_cost",
)


@dataclass(frozen=True)
class CandidateSpec:
    candidate_id: str
    family_id: str
    candidate_role: str
    setup_kind: str
    threshold: float | None
    exit_mode: str
    selectable: bool
    opening_range_minutes: int | None = None
    direction_mode: str = "both"
    last_signal_start_session_minute: int | None = None
    forced_flat_session_minute: int = STANDARD_FORCED_FLAT_MINUTE


def _normalise_scalar(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer, int)) and not isinstance(value, bool):
        return int(value)
    if isinstance(value, (np.floating, float)):
        numeric = float(value)
        if math.isnan(numeric):
            return None
        if math.isinf(numeric):
            return "Infinity" if numeric > 0 else "-Infinity"
        return numeric
    if pd.isna(value):
        return None
    return value


def canonical_object_sha256(value: Any) -> str:
    def normalise(item: Any) -> Any:
        if isinstance(item, Mapping):
            return {
                str(key): normalise(current)
                for key, current in item.items()
            }
        if isinstance(item, (list, tuple)):
            return [normalise(current) for current in item]
        return _normalise_scalar(item)

    encoded = json.dumps(
        normalise(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def canonical_dataframe_sha256(frame: pd.DataFrame) -> str:
    records = [
        {
            str(key): _normalise_scalar(value)
            for key, value in row.items()
        }
        for row in frame.to_dict(orient="records")
    ]
    return canonical_object_sha256(records)


def candidate_specs() -> tuple[CandidateSpec, ...]:
    validate_exp026_preregistration()
    record = get_exp026_preregistration()
    grid = record["candidate_grid"]

    specs: list[CandidateSpec] = []
    for item in grid["development_candidates"]:
        family_id = str(item["family_id"])
        if family_id == "gap_fade":
            setup_kind = "gap_fade"
            threshold = float(item["minimum_gap_fraction"])
        elif family_id == "premarket_momentum_continuation":
            setup_kind = "premarket_continuation"
            threshold = float(item["minimum_drive_fraction"])
        elif family_id == "opening_drive_continuation":
            setup_kind = "opening_drive_continuation"
            threshold = float(item["minimum_drive_fraction"])
        else:
            raise ValueError(
                f"Unknown EXP-026 development family: {family_id}."
            )
        specs.append(
            CandidateSpec(
                candidate_id=str(item["candidate_id"]),
                family_id=family_id,
                candidate_role="DEVELOPMENT",
                setup_kind=setup_kind,
                threshold=threshold,
                exit_mode=str(item["exit_mode"]),
                selectable=bool(item["eligible_for_selection"]),
            )
        )

    for item in grid["control_candidates"]:
        source_experiment = str(item["source_experiment"])
        if source_experiment == "EXP-005":
            specs.append(
                CandidateSpec(
                    candidate_id=str(item["candidate_id"]),
                    family_id=str(item["family_id"]),
                    candidate_role="CONTROL",
                    setup_kind="orb_exp005",
                    threshold=None,
                    exit_mode=str(item["exit_mode"]),
                    selectable=False,
                    opening_range_minutes=15,
                    direction_mode="both",
                    last_signal_start_session_minute=1075,
                    forced_flat_session_minute=STANDARD_FORCED_FLAT_MINUTE,
                )
            )
        elif source_experiment == "EXP-007":
            specs.append(
                CandidateSpec(
                    candidate_id=str(item["candidate_id"]),
                    family_id=str(item["family_id"]),
                    candidate_role="CONTROL",
                    setup_kind="orb_exp007",
                    threshold=None,
                    exit_mode=str(item["exit_mode"]),
                    selectable=False,
                    opening_range_minutes=30,
                    direction_mode="long_only",
                    last_signal_start_session_minute=1190,
                    forced_flat_session_minute=EXP007_FORCED_FLAT_MINUTE,
                )
            )
        else:
            raise ValueError(
                f"Unknown EXP-026 control source: {source_experiment}."
            )

    return tuple(specs)


CANDIDATE_SPECS = candidate_specs()
CANDIDATE_SPEC_BY_ID = {
    item.candidate_id: item
    for item in CANDIDATE_SPECS
}
DEVELOPMENT_CANDIDATE_IDS = tuple(
    item.candidate_id
    for item in CANDIDATE_SPECS
    if item.candidate_role == "DEVELOPMENT"
)
CONTROL_CANDIDATE_IDS = tuple(
    item.candidate_id
    for item in CANDIDATE_SPECS
    if item.candidate_role == "CONTROL"
)
ALL_CANDIDATE_IDS = tuple(
    item.candidate_id
    for item in CANDIDATE_SPECS
)


def validate_candidate_specs() -> None:
    record = get_exp026_preregistration()
    grid = record["candidate_grid"]

    if len(CANDIDATE_SPECS) != 24:
        raise ValueError("EXP-026 must contain exactly 24 reported candidates.")
    if len(DEVELOPMENT_CANDIDATE_IDS) != 22:
        raise ValueError("EXP-026 must contain exactly 22 development candidates.")
    if len(CONTROL_CANDIDATE_IDS) != 2:
        raise ValueError("EXP-026 must contain exactly two fixed controls.")
    if len(set(ALL_CANDIDATE_IDS)) != len(ALL_CANDIDATE_IDS):
        raise ValueError("EXP-026 candidate identifiers are not unique.")

    expected_development = tuple(
        str(item["candidate_id"])
        for item in grid["development_candidates"]
    )
    expected_controls = tuple(
        str(item["candidate_id"])
        for item in grid["control_candidates"]
    )
    if DEVELOPMENT_CANDIDATE_IDS != expected_development:
        raise ValueError("EXP-026 development candidate order changed.")
    if CONTROL_CANDIDATE_IDS != expected_controls:
        raise ValueError("EXP-026 control candidate order changed.")
    if not all(
        item.selectable
        for item in CANDIDATE_SPECS
        if item.candidate_role == "DEVELOPMENT"
    ):
        raise ValueError("An EXP-026 development candidate became unselectable.")
    if any(
        item.selectable
        for item in CANDIDATE_SPECS
        if item.candidate_role == "CONTROL"
    ):
        raise ValueError("An EXP-026 fixed control became selection eligible.")

    family_counts = {
        family_id: sum(
            item.family_id == family_id
            and item.candidate_role == "DEVELOPMENT"
            for item in CANDIDATE_SPECS
        )
        for family_id in (
            "gap_fade",
            "premarket_momentum_continuation",
            "opening_drive_continuation",
        )
    }
    if family_counts != {
        "gap_fade": 6,
        "premarket_momentum_continuation": 8,
        "opening_drive_continuation": 8,
    }:
        raise ValueError("EXP-026 family candidate counts changed.")


def _as_date_string(values: pd.Series) -> pd.Series:
    return pd.to_datetime(
        values,
        errors="raise",
    ).dt.strftime("%Y-%m-%d")


def normalise_source_frame(
    frame: pd.DataFrame,
    *,
    representation_id: str,
    allowed_session_start: str,
    allowed_session_end: str,
) -> pd.DataFrame:
    if representation_id not in REPRESENTATION_IDS:
        raise ValueError(
            f"Unknown EXP-026 representation: {representation_id}."
        )
    if allowed_session_start > allowed_session_end:
        raise ValueError("EXP-026 allowed session bounds are reversed.")

    missing = sorted(set(SOURCE_COLUMNS).difference(frame.columns))
    if missing:
        raise ValueError(
            "EXP-026 source frame is missing columns: "
            + ", ".join(missing)
        )

    local = frame.loc[:, SOURCE_COLUMNS].copy()
    if local.empty:
        raise ValueError("EXP-026 permitted source scan is empty.")

    local["ts_event"] = pd.to_datetime(
        local["ts_event"],
        utc=True,
        errors="raise",
    )
    if local["ts_event"].duplicated().any():
        raise ValueError("EXP-026 source timestamps are not unique.")
    if not local["ts_event"].is_monotonic_increasing:
        local = local.sort_values(
            "ts_event",
            kind="stable",
        ).reset_index(drop=True)

    local["session_date"] = _as_date_string(
        local["trading_date"]
    )
    if (
        local["session_date"].min() < allowed_session_start
        or local["session_date"].max() > allowed_session_end
    ):
        raise ValueError(
            "EXP-026 source scan returned an out-of-window trading date."
        )

    numeric_columns = ("open", "high", "low", "close", "volume")
    for column in numeric_columns:
        local[column] = pd.to_numeric(
            local[column],
            errors="raise",
        )
    numeric = local.loc[:, numeric_columns].to_numpy(dtype=float)
    if not np.isfinite(numeric).all():
        raise ValueError("EXP-026 source OHLCV contains nonfinite values.")
    if (local["volume"] < 0).any():
        raise ValueError("EXP-026 source volume is negative.")
    if (
        (local["high"] < local[["open", "close", "low"]].max(axis=1))
        | (local["low"] > local[["open", "close", "high"]].min(axis=1))
    ).any():
        raise ValueError("EXP-026 source OHLC geometry is invalid.")

    prices = local.loc[:, ["open", "high", "low", "close"]].to_numpy(
        dtype=float
    )
    tick_units = prices / NQ_TICK_SIZE_POINTS
    if not np.allclose(
        tick_units,
        np.round(tick_units),
        atol=1e-7,
        rtol=0.0,
    ):
        raise ValueError("EXP-026 source prices are not valid NQ ticks.")

    local_timestamp = local["ts_event"].dt.tz_convert(
        RESEARCH_TIMEZONE
    )
    if (
        (local_timestamp.dt.second != 0)
        | (local_timestamp.dt.microsecond != 0)
    ).any():
        raise ValueError(
            "EXP-026 timestamps must be exact UTC minute starts."
        )

    clock_minute = (
        local_timestamp.dt.hour.astype(int) * 60
        + local_timestamp.dt.minute.astype(int)
    )
    local["session_minute"] = np.where(
        clock_minute >= SESSION_START_CLOCK_MINUTE,
        clock_minute - SESSION_START_CLOCK_MINUTE,
        clock_minute
        + (24 * 60 - SESSION_START_CLOCK_MINUTE),
    ).astype(np.int16)

    local_dates = local_timestamp.dt.strftime("%Y-%m-%d")
    derived = pd.to_datetime(local_dates)
    evening = clock_minute >= SESSION_START_CLOCK_MINUTE
    derived = derived.where(
        ~evening,
        derived + pd.Timedelta(days=1),
    ).dt.strftime("%Y-%m-%d")
    if not derived.equals(local["session_date"]):
        raise ValueError(
            "EXP-026 trading-date and New York session semantics differ."
        )

    local = local.loc[
        local["session_minute"].between(
            0,
            SESSION_LAST_MINUTE,
        )
    ].copy()
    if local.duplicated(
        ["session_date", "session_minute"]
    ).any():
        raise ValueError(
            "EXP-026 source contains duplicate session minutes."
        )

    local["representation_id"] = representation_id
    return local.sort_values(
        ["session_date", "session_minute"],
        kind="stable",
    ).reset_index(drop=True)


def aggregate_observed_five_minute(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    required = {
        "session_date",
        "session_minute",
        "ts_event",
        "open",
        "high",
        "low",
        "close",
        "volume",
    }
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(
            "EXP-026 five-minute input is missing: "
            + ", ".join(missing)
        )

    local = frame.loc[
        frame["session_minute"].between(
            PREMARKET_START_SESSION_MINUTE,
            CASH_END_SESSION_MINUTE - 1,
        )
    ].copy()
    columns = (
        "session_date",
        "five_minute_bin",
        "first_timestamp_utc",
        "last_timestamp_utc",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "observation_count",
    )
    if local.empty:
        return pd.DataFrame(columns=columns)

    local["five_minute_bin"] = (
        local["session_minute"].astype(int) // 5
    )
    result = (
        local.groupby(
            ["session_date", "five_minute_bin"],
            sort=True,
            as_index=False,
        )
        .agg(
            first_timestamp_utc=("ts_event", "first"),
            last_timestamp_utc=("ts_event", "last"),
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            volume=("volume", "sum"),
            observation_count=("ts_event", "size"),
        )
        .sort_values(
            ["session_date", "five_minute_bin"],
            kind="stable",
        )
        .reset_index(drop=True)
    )
    return result.loc[:, columns]


def _sign(value: float) -> int:
    return 1 if value > 0 else -1 if value < 0 else 0


def _iso_timestamp(value: Any) -> str:
    return pd.Timestamp(value).isoformat()


def _empty_five_minute() -> pd.DataFrame:
    return pd.DataFrame(
        columns=(
            "session_date",
            "five_minute_bin",
            "first_timestamp_utc",
            "last_timestamp_utc",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "observation_count",
        )
    )


def _complete_bins(
    five_rows: pd.DataFrame,
    bins: Sequence[int],
) -> bool:
    current = five_rows.loc[
        five_rows["five_minute_bin"].isin(tuple(bins))
    ]
    return (
        current["five_minute_bin"].nunique() == len(tuple(bins))
        and len(current) == len(tuple(bins))
        and current["observation_count"].eq(5).all()
    )


def _one_minute_row(
    session_rows: pd.DataFrame,
    session_minute: int,
) -> pd.Series | None:
    current = session_rows.loc[
        session_rows["session_minute"] == session_minute
    ]
    if len(current) != 1:
        return None
    return current.iloc[0]


def _target_for_exit_mode(
    *,
    exit_mode: str,
    direction: int,
    entry_price: float,
    risk_points: float,
    prior_cash_close: float | None = None,
) -> float:
    if exit_mode in {
        "time",
        "15:55_time",
    }:
        return float("nan")
    if exit_mode in {
        "1r_or_time",
        "1r_or_14:00_time",
    }:
        return float(
            entry_price
            + direction * risk_points
        )
    if exit_mode == "1p5r_or_time":
        return float(
            entry_price
            + direction * 1.5 * risk_points
        )
    if exit_mode == "prior_cash_close_or_time":
        if prior_cash_close is None:
            raise ValueError(
                "Prior-cash-close target requires the prior close."
            )
        return float(prior_cash_close)
    raise ValueError(
        f"Unknown EXP-026 exit mode: {exit_mode}."
    )


def execute_trade_from_levels(
    session_rows: pd.DataFrame,
    *,
    representation_id: str,
    candidate: CandidateSpec,
    session_date: str,
    direction: int,
    entry_session_minute: int,
    forced_flat_session_minute: int,
    stop_price: float,
    target_price: float,
    context_value: float,
    mirror_post_entry_path: bool = False,
) -> tuple[dict[str, Any] | None, str]:
    entry_row = _one_minute_row(
        session_rows,
        entry_session_minute,
    )
    forced_row = _one_minute_row(
        session_rows,
        forced_flat_session_minute,
    )
    if entry_row is None:
        return None, "ENTRY_MINUTE_UNAVAILABLE"
    if forced_row is None:
        return None, "FORCED_FLAT_MINUTE_UNAVAILABLE"

    entry_price = float(entry_row["open"])
    risk_points = direction * (
        entry_price - float(stop_price)
    )
    if (
        not np.isfinite(risk_points)
        or risk_points <= 0
    ):
        return None, "NONPOSITIVE_INITIAL_RISK"

    if np.isfinite(target_price):
        favourable_distance = direction * (
            float(target_price) - entry_price
        )
        if favourable_distance <= 0:
            return None, "TARGET_NOT_FAVOURABLE_FROM_ENTRY"

    chosen_price = float(forced_row["open"])
    chosen_timestamp = forced_row["ts_event"]
    chosen_minute = forced_flat_session_minute
    chosen_reason = (
        f"forced_flat_{forced_flat_session_minute}"
    )

    exit_rows = session_rows.loc[
        session_rows["session_minute"].between(
            entry_session_minute,
            forced_flat_session_minute - 1,
        )
    ].sort_values(
        "ts_event",
        kind="stable",
    )
    for row in exit_rows.itertuples(index=False):
        bar_open = float(row.open)
        bar_high = float(row.high)
        bar_low = float(row.low)
        if mirror_post_entry_path:
            original_high = bar_high
            original_low = bar_low
            bar_open = 2.0 * entry_price - bar_open
            bar_high = 2.0 * entry_price - original_low
            bar_low = 2.0 * entry_price - original_high

        if direction == 1:
            stop_gap = bar_open <= stop_price
            stop_touch = bar_low <= stop_price
            target_touch = (
                np.isfinite(target_price)
                and bar_high >= target_price
            )
        else:
            stop_gap = bar_open >= stop_price
            stop_touch = bar_high >= stop_price
            target_touch = (
                np.isfinite(target_price)
                and bar_low <= target_price
            )

        if stop_gap:
            chosen_price = bar_open
            chosen_timestamp = row.ts_event
            chosen_minute = int(row.session_minute)
            chosen_reason = (
                "mirrored_gap_through_stop"
                if mirror_post_entry_path
                else "gap_through_stop"
            )
            break
        if stop_touch:
            chosen_price = float(stop_price)
            chosen_timestamp = row.ts_event
            chosen_minute = int(row.session_minute)
            chosen_reason = (
                "mirrored_protective_stop"
                if mirror_post_entry_path
                else "protective_stop"
            )
            break
        if target_touch:
            chosen_price = float(target_price)
            chosen_timestamp = row.ts_event
            chosen_minute = int(row.session_minute)
            chosen_reason = (
                "mirrored_profit_target"
                if mirror_post_entry_path
                else "profit_target"
            )
            break
    else:
        if mirror_post_entry_path:
            chosen_price = (
                2.0 * entry_price
                - float(forced_row["open"])
            )
            chosen_reason = (
                f"mirrored_forced_flat_{forced_flat_session_minute}"
            )

    gross_pnl = (
        direction
        * (float(chosen_price) - entry_price)
        * NQ_MULTIPLIER_USD_PER_POINT
    )
    trade = {
        "representation_id": representation_id,
        "candidate_id": candidate.candidate_id,
        "family_id": candidate.family_id,
        "candidate_role": candidate.candidate_role,
        "session_date": session_date,
        "direction": (
            "long"
            if direction == 1
            else "short"
        ),
        "entry_timestamp_utc": _iso_timestamp(
            entry_row["ts_event"]
        ),
        "exit_timestamp_utc": _iso_timestamp(
            chosen_timestamp
        ),
        "entry_session_minute": int(
            entry_session_minute
        ),
        "exit_session_minute": int(chosen_minute),
        "forced_flat_session_minute": int(
            forced_flat_session_minute
        ),
        "entry_price": float(entry_price),
        "stop_price": float(stop_price),
        "target_price": (
            float(target_price)
            if np.isfinite(target_price)
            else np.nan
        ),
        "exit_price": float(chosen_price),
        "risk_points": float(risk_points),
        "gross_pnl_usd": float(gross_pnl),
        "transaction_cost_usd": (
            BASE_ROUND_TRIP_COST_USD
        ),
        "net_pnl_usd": float(
            gross_pnl - BASE_ROUND_TRIP_COST_USD
        ),
        "exit_reason": chosen_reason,
        "context_value": float(context_value),
        "threshold": (
            float(candidate.threshold)
            if candidate.threshold is not None
            else np.nan
        ),
        "exit_mode": candidate.exit_mode,
        "setup_kind": candidate.setup_kind,
    }
    return trade, ""


def _base_decision(
    *,
    representation_id: str,
    candidate: CandidateSpec,
    session_date: str,
) -> dict[str, Any]:
    return {
        "representation_id": representation_id,
        "candidate_id": candidate.candidate_id,
        "family_id": candidate.family_id,
        "candidate_role": candidate.candidate_role,
        "session_date": session_date,
        "eligible": False,
        "ineligibility_reason": "",
        "trade_flag": False,
        "direction": "",
        "entry_timestamp_utc": "",
        "entry_session_minute": np.nan,
        "forced_flat_session_minute": (
            candidate.forced_flat_session_minute
        ),
        "context_value": np.nan,
        "threshold": (
            float(candidate.threshold)
            if candidate.threshold is not None
            else np.nan
        ),
        "exit_mode": candidate.exit_mode,
        "setup_kind": candidate.setup_kind,
    }


def _first_cash_bar(
    five_rows: pd.DataFrame,
) -> pd.Series | None:
    current = five_rows.loc[
        five_rows["five_minute_bin"]
        == FIRST_CASH_FIVE_MINUTE_BIN
    ]
    if (
        len(current) != 1
        or int(current.iloc[0]["observation_count"]) != 5
    ):
        return None
    return current.iloc[0]


def _evaluate_gap_fade(
    *,
    candidate: CandidateSpec,
    representation_id: str,
    session_date: str,
    session_rows: pd.DataFrame,
    five_rows: pd.DataFrame,
    previous_date: str,
    previous_five: pd.DataFrame,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    decision = _base_decision(
        representation_id=representation_id,
        candidate=candidate,
        session_date=session_date,
    )
    if not previous_date:
        decision["ineligibility_reason"] = (
            "PREVIOUS_REFERENCE_SESSION_UNAVAILABLE"
        )
        return decision, None
    if not _complete_bins(
        previous_five,
        CASH_FIVE_MINUTE_BINS,
    ):
        decision["ineligibility_reason"] = (
            "PREVIOUS_CASH_SESSION_INCOMPLETE"
        )
        return decision, None

    first_bar = _first_cash_bar(five_rows)
    if first_bar is None:
        decision["ineligibility_reason"] = (
            "FIRST_CASH_BAR_INCOMPLETE"
        )
        return decision, None
    entry_row = _one_minute_row(
        session_rows,
        GAP_AND_PREMARKET_ENTRY_MINUTE,
    )
    forced_row = _one_minute_row(
        session_rows,
        STANDARD_FORCED_FLAT_MINUTE,
    )
    if entry_row is None:
        decision["ineligibility_reason"] = (
            "ENTRY_MINUTE_UNAVAILABLE"
        )
        return decision, None
    if forced_row is None:
        decision["ineligibility_reason"] = (
            "FORCED_FLAT_MINUTE_UNAVAILABLE"
        )
        return decision, None

    previous_cash = previous_five.loc[
        previous_five["five_minute_bin"].isin(
            CASH_FIVE_MINUTE_BINS
        )
    ].sort_values(
        "five_minute_bin",
        kind="stable",
    )
    prior_close = float(
        previous_cash.iloc[-1]["close"]
    )
    prior_high = float(previous_cash["high"].max())
    prior_low = float(previous_cash["low"].min())
    prior_range = prior_high - prior_low
    if (
        not np.isfinite(prior_range)
        or prior_range <= 0
    ):
        decision["ineligibility_reason"] = (
            "PREVIOUS_CASH_RANGE_NONPOSITIVE"
        )
        return decision, None

    opening_gap = float(first_bar["open"]) - prior_close
    gap_direction = _sign(opening_gap)
    if gap_direction == 0:
        decision["eligible"] = True
        decision["ineligibility_reason"] = (
            "ZERO_OPENING_GAP"
        )
        return decision, None

    gap_fraction = abs(opening_gap) / prior_range
    decision["eligible"] = True
    decision["context_value"] = float(gap_fraction)
    if gap_fraction < float(candidate.threshold):
        decision["ineligibility_reason"] = (
            "SETUP_THRESHOLD_NOT_MET"
        )
        return decision, None

    first_return = (
        float(first_bar["close"])
        - float(first_bar["open"])
    )
    signal_direction = _sign(first_return)
    if signal_direction != -gap_direction:
        decision["ineligibility_reason"] = (
            "SIGNAL_NOT_CONFIRMED"
        )
        return decision, None

    direction = -gap_direction
    stop_price = (
        float(first_bar["low"])
        if direction == 1
        else float(first_bar["high"])
    )
    entry_price = float(entry_row["open"])
    risk_points = direction * (
        entry_price - stop_price
    )
    if risk_points <= 0:
        decision["ineligibility_reason"] = (
            "NONPOSITIVE_INITIAL_RISK"
        )
        return decision, None

    target_price = _target_for_exit_mode(
        exit_mode=candidate.exit_mode,
        direction=direction,
        entry_price=entry_price,
        risk_points=risk_points,
        prior_cash_close=prior_close,
    )
    trade, reason = execute_trade_from_levels(
        session_rows,
        representation_id=representation_id,
        candidate=candidate,
        session_date=session_date,
        direction=direction,
        entry_session_minute=(
            GAP_AND_PREMARKET_ENTRY_MINUTE
        ),
        forced_flat_session_minute=(
            STANDARD_FORCED_FLAT_MINUTE
        ),
        stop_price=stop_price,
        target_price=target_price,
        context_value=gap_fraction,
    )
    if trade is None:
        decision["ineligibility_reason"] = reason
        return decision, None

    decision["trade_flag"] = True
    decision["direction"] = trade["direction"]
    decision["entry_timestamp_utc"] = trade[
        "entry_timestamp_utc"
    ]
    decision["entry_session_minute"] = (
        GAP_AND_PREMARKET_ENTRY_MINUTE
    )
    decision["ineligibility_reason"] = ""
    return decision, trade


def _evaluate_premarket(
    *,
    candidate: CandidateSpec,
    representation_id: str,
    session_date: str,
    session_rows: pd.DataFrame,
    five_rows: pd.DataFrame,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    decision = _base_decision(
        representation_id=representation_id,
        candidate=candidate,
        session_date=session_date,
    )
    if not _complete_bins(
        five_rows,
        PREMARKET_FIVE_MINUTE_BINS,
    ):
        decision["ineligibility_reason"] = (
            "PREMARKET_WINDOW_INCOMPLETE"
        )
        return decision, None

    first_bar = _first_cash_bar(five_rows)
    if first_bar is None:
        decision["ineligibility_reason"] = (
            "FIRST_CASH_BAR_INCOMPLETE"
        )
        return decision, None
    entry_row = _one_minute_row(
        session_rows,
        GAP_AND_PREMARKET_ENTRY_MINUTE,
    )
    forced_row = _one_minute_row(
        session_rows,
        STANDARD_FORCED_FLAT_MINUTE,
    )
    if entry_row is None:
        decision["ineligibility_reason"] = (
            "ENTRY_MINUTE_UNAVAILABLE"
        )
        return decision, None
    if forced_row is None:
        decision["ineligibility_reason"] = (
            "FORCED_FLAT_MINUTE_UNAVAILABLE"
        )
        return decision, None

    premarket = five_rows.loc[
        five_rows["five_minute_bin"].isin(
            PREMARKET_FIVE_MINUTE_BINS
        )
    ].sort_values(
        "five_minute_bin",
        kind="stable",
    )
    premarket_open = float(premarket.iloc[0]["open"])
    premarket_close = float(premarket.iloc[-1]["close"])
    premarket_high = float(premarket["high"].max())
    premarket_low = float(premarket["low"].min())
    premarket_range = premarket_high - premarket_low
    if (
        not np.isfinite(premarket_range)
        or premarket_range <= 0
    ):
        decision["ineligibility_reason"] = (
            "PREMARKET_RANGE_NONPOSITIVE"
        )
        return decision, None

    drive_return = premarket_close - premarket_open
    direction = _sign(drive_return)
    if direction == 0:
        decision["eligible"] = True
        decision["ineligibility_reason"] = (
            "ZERO_PREMARKET_DIRECTION"
        )
        return decision, None

    drive_fraction = abs(drive_return) / premarket_range
    decision["eligible"] = True
    decision["context_value"] = float(drive_fraction)
    if drive_fraction < float(candidate.threshold):
        decision["ineligibility_reason"] = (
            "SETUP_THRESHOLD_NOT_MET"
        )
        return decision, None

    first_return = (
        float(first_bar["close"])
        - float(first_bar["open"])
    )
    if _sign(first_return) != direction:
        decision["ineligibility_reason"] = (
            "SIGNAL_NOT_CONFIRMED"
        )
        return decision, None

    stop_price = (
        float(first_bar["low"])
        if direction == 1
        else float(first_bar["high"])
    )
    entry_price = float(entry_row["open"])
    risk_points = direction * (
        entry_price - stop_price
    )
    if risk_points <= 0:
        decision["ineligibility_reason"] = (
            "NONPOSITIVE_INITIAL_RISK"
        )
        return decision, None

    target_price = _target_for_exit_mode(
        exit_mode=candidate.exit_mode,
        direction=direction,
        entry_price=entry_price,
        risk_points=risk_points,
    )
    trade, reason = execute_trade_from_levels(
        session_rows,
        representation_id=representation_id,
        candidate=candidate,
        session_date=session_date,
        direction=direction,
        entry_session_minute=(
            GAP_AND_PREMARKET_ENTRY_MINUTE
        ),
        forced_flat_session_minute=(
            STANDARD_FORCED_FLAT_MINUTE
        ),
        stop_price=stop_price,
        target_price=target_price,
        context_value=drive_fraction,
    )
    if trade is None:
        decision["ineligibility_reason"] = reason
        return decision, None

    decision["trade_flag"] = True
    decision["direction"] = trade["direction"]
    decision["entry_timestamp_utc"] = trade[
        "entry_timestamp_utc"
    ]
    decision["entry_session_minute"] = (
        GAP_AND_PREMARKET_ENTRY_MINUTE
    )
    decision["ineligibility_reason"] = ""
    return decision, trade


def _evaluate_opening_drive(
    *,
    candidate: CandidateSpec,
    representation_id: str,
    session_date: str,
    session_rows: pd.DataFrame,
    five_rows: pd.DataFrame,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    decision = _base_decision(
        representation_id=representation_id,
        candidate=candidate,
        session_date=session_date,
    )
    if not _complete_bins(
        five_rows,
        OPENING_DRIVE_RANGE_BINS,
    ):
        decision["ineligibility_reason"] = (
            "OPENING_DRIVE_WINDOW_INCOMPLETE"
        )
        return decision, None

    entry_row = _one_minute_row(
        session_rows,
        OPENING_DRIVE_ENTRY_MINUTE,
    )
    forced_row = _one_minute_row(
        session_rows,
        STANDARD_FORCED_FLAT_MINUTE,
    )
    if entry_row is None:
        decision["ineligibility_reason"] = (
            "ENTRY_MINUTE_UNAVAILABLE"
        )
        return decision, None
    if forced_row is None:
        decision["ineligibility_reason"] = (
            "FORCED_FLAT_MINUTE_UNAVAILABLE"
        )
        return decision, None

    opening_drive = five_rows.loc[
        five_rows["five_minute_bin"].isin(
            OPENING_DRIVE_RANGE_BINS
        )
    ].sort_values(
        "five_minute_bin",
        kind="stable",
    )
    drive_open = float(opening_drive.iloc[0]["open"])
    drive_close = float(opening_drive.iloc[-1]["close"])
    drive_high = float(opening_drive["high"].max())
    drive_low = float(opening_drive["low"].min())
    drive_range = drive_high - drive_low
    if (
        not np.isfinite(drive_range)
        or drive_range <= 0
    ):
        decision["ineligibility_reason"] = (
            "OPENING_DRIVE_RANGE_NONPOSITIVE"
        )
        return decision, None

    drive_return = drive_close - drive_open
    direction = _sign(drive_return)
    if direction == 0:
        decision["eligible"] = True
        decision["ineligibility_reason"] = (
            "ZERO_OPENING_DRIVE_DIRECTION"
        )
        return decision, None

    drive_fraction = abs(drive_return) / drive_range
    decision["eligible"] = True
    decision["context_value"] = float(drive_fraction)
    if drive_fraction < float(candidate.threshold):
        decision["ineligibility_reason"] = (
            "SETUP_THRESHOLD_NOT_MET"
        )
        return decision, None

    stop_price = (
        drive_low
        if direction == 1
        else drive_high
    )
    entry_price = float(entry_row["open"])
    risk_points = direction * (
        entry_price - stop_price
    )
    if risk_points <= 0:
        decision["ineligibility_reason"] = (
            "NONPOSITIVE_INITIAL_RISK"
        )
        return decision, None

    target_price = _target_for_exit_mode(
        exit_mode=candidate.exit_mode,
        direction=direction,
        entry_price=entry_price,
        risk_points=risk_points,
    )
    trade, reason = execute_trade_from_levels(
        session_rows,
        representation_id=representation_id,
        candidate=candidate,
        session_date=session_date,
        direction=direction,
        entry_session_minute=(
            OPENING_DRIVE_ENTRY_MINUTE
        ),
        forced_flat_session_minute=(
            STANDARD_FORCED_FLAT_MINUTE
        ),
        stop_price=stop_price,
        target_price=target_price,
        context_value=drive_fraction,
    )
    if trade is None:
        decision["ineligibility_reason"] = reason
        return decision, None

    decision["trade_flag"] = True
    decision["direction"] = trade["direction"]
    decision["entry_timestamp_utc"] = trade[
        "entry_timestamp_utc"
    ]
    decision["entry_session_minute"] = (
        OPENING_DRIVE_ENTRY_MINUTE
    )
    decision["ineligibility_reason"] = ""
    return decision, trade


def _evaluate_orb_control(
    *,
    candidate: CandidateSpec,
    representation_id: str,
    session_date: str,
    session_rows: pd.DataFrame,
    five_rows: pd.DataFrame,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    decision = _base_decision(
        representation_id=representation_id,
        candidate=candidate,
        session_date=session_date,
    )
    if candidate.opening_range_minutes is None:
        raise ValueError("ORB control lacks an opening-range length.")

    range_bin_count = candidate.opening_range_minutes // 5
    range_bins = tuple(
        range(
            FIRST_CASH_FIVE_MINUTE_BIN,
            FIRST_CASH_FIVE_MINUTE_BIN
            + range_bin_count,
        )
    )
    if not _complete_bins(five_rows, range_bins):
        decision["ineligibility_reason"] = (
            "OPENING_RANGE_INCOMPLETE"
        )
        return decision, None

    forced_row = _one_minute_row(
        session_rows,
        candidate.forced_flat_session_minute,
    )
    if forced_row is None:
        decision["ineligibility_reason"] = (
            "FORCED_FLAT_MINUTE_UNAVAILABLE"
        )
        return decision, None

    opening_range = five_rows.loc[
        five_rows["five_minute_bin"].isin(
            range_bins
        )
    ]
    range_high = float(opening_range["high"].max())
    range_low = float(opening_range["low"].min())
    if range_high <= range_low:
        decision["ineligibility_reason"] = (
            "OPENING_RANGE_NONPOSITIVE"
        )
        return decision, None

    first_signal_start = (
        CASH_START_SESSION_MINUTE
        + candidate.opening_range_minutes
    )
    last_signal_start = int(
        candidate.last_signal_start_session_minute
    )
    signal_bins = tuple(
        range(
            first_signal_start // 5,
            last_signal_start // 5 + 1,
        )
    )
    signal_rows = five_rows.loc[
        five_rows["five_minute_bin"].isin(
            signal_bins
        )
        & five_rows["observation_count"].eq(5)
    ].sort_values(
        "five_minute_bin",
        kind="stable",
    )

    decision["eligible"] = True
    signal: pd.Series | None = None
    direction = 0
    for _, row in signal_rows.iterrows():
        close_price = float(row["close"])
        if close_price > range_high:
            direction = 1
            signal = row
            break
        if (
            candidate.direction_mode == "both"
            and close_price < range_low
        ):
            direction = -1
            signal = row
            break

    if signal is None:
        decision["ineligibility_reason"] = (
            "SIGNAL_NOT_CONFIRMED"
        )
        return decision, None

    entry_session_minute = (
        int(signal["five_minute_bin"]) + 1
    ) * 5
    entry_row = _one_minute_row(
        session_rows,
        entry_session_minute,
    )
    if entry_row is None:
        decision["eligible"] = False
        decision["ineligibility_reason"] = (
            "ENTRY_MINUTE_UNAVAILABLE"
        )
        return decision, None

    stop_price = (
        range_low
        if direction == 1
        else range_high
    )
    entry_price = float(entry_row["open"])
    risk_points = direction * (
        entry_price - stop_price
    )
    if risk_points <= 0:
        decision["ineligibility_reason"] = (
            "NONPOSITIVE_INITIAL_RISK"
        )
        return decision, None

    target_price = _target_for_exit_mode(
        exit_mode=candidate.exit_mode,
        direction=direction,
        entry_price=entry_price,
        risk_points=risk_points,
    )
    trade, reason = execute_trade_from_levels(
        session_rows,
        representation_id=representation_id,
        candidate=candidate,
        session_date=session_date,
        direction=direction,
        entry_session_minute=entry_session_minute,
        forced_flat_session_minute=(
            candidate.forced_flat_session_minute
        ),
        stop_price=stop_price,
        target_price=target_price,
        context_value=(
            candidate.opening_range_minutes
        ),
    )
    if trade is None:
        decision["ineligibility_reason"] = reason
        return decision, None

    decision["trade_flag"] = True
    decision["direction"] = trade["direction"]
    decision["entry_timestamp_utc"] = trade[
        "entry_timestamp_utc"
    ]
    decision["entry_session_minute"] = (
        entry_session_minute
    )
    decision["context_value"] = (
        candidate.opening_range_minutes
    )
    decision["ineligibility_reason"] = ""
    return decision, trade


def replay_candidates(
    frame: pd.DataFrame,
    *,
    representation_id: str,
    allowed_session_start: str,
    allowed_session_end: str,
    candidate_ids: Iterable[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    validate_candidate_specs()
    source = normalise_source_frame(
        frame,
        representation_id=representation_id,
        allowed_session_start=allowed_session_start,
        allowed_session_end=allowed_session_end,
    )
    five_minute = aggregate_observed_five_minute(
        source
    )
    session_dates = tuple(
        sorted(source["session_date"].unique())
    )
    if (
        not session_dates
        or session_dates[0] < allowed_session_start
        or session_dates[-1] > allowed_session_end
    ):
        raise ValueError(
            "EXP-026 replay session axis left its permitted period."
        )

    requested = (
        ALL_CANDIDATE_IDS
        if candidate_ids is None
        else tuple(str(value) for value in candidate_ids)
    )
    if (
        not requested
        or len(set(requested)) != len(requested)
        or not set(requested).issubset(
            CANDIDATE_SPEC_BY_ID
        )
    ):
        raise ValueError(
            "EXP-026 requested candidate identifiers are invalid."
        )

    source_groups = {
        str(key): group.reset_index(drop=True)
        for key, group in source.groupby(
            "session_date",
            sort=False,
        )
    }
    five_groups = {
        str(key): group.reset_index(drop=True)
        for key, group in five_minute.groupby(
            "session_date",
            sort=False,
        )
    }
    date_position = {
        session_date: index
        for index, session_date in enumerate(
            session_dates
        )
    }

    decision_rows: list[dict[str, Any]] = []
    trade_rows: list[dict[str, Any]] = []

    for candidate_id in requested:
        candidate = CANDIDATE_SPEC_BY_ID[
            candidate_id
        ]
        for session_date in session_dates:
            session_rows = source_groups[
                session_date
            ]
            five_rows = five_groups.get(
                session_date,
                _empty_five_minute(),
            )
            position = date_position[session_date]
            previous_date = (
                session_dates[position - 1]
                if position > 0
                else ""
            )
            previous_five = five_groups.get(
                previous_date,
                _empty_five_minute(),
            )

            if candidate.setup_kind == "gap_fade":
                decision, trade = _evaluate_gap_fade(
                    candidate=candidate,
                    representation_id=representation_id,
                    session_date=session_date,
                    session_rows=session_rows,
                    five_rows=five_rows,
                    previous_date=previous_date,
                    previous_five=previous_five,
                )
            elif candidate.setup_kind == (
                "premarket_continuation"
            ):
                decision, trade = _evaluate_premarket(
                    candidate=candidate,
                    representation_id=representation_id,
                    session_date=session_date,
                    session_rows=session_rows,
                    five_rows=five_rows,
                )
            elif candidate.setup_kind == (
                "opening_drive_continuation"
            ):
                decision, trade = _evaluate_opening_drive(
                    candidate=candidate,
                    representation_id=representation_id,
                    session_date=session_date,
                    session_rows=session_rows,
                    five_rows=five_rows,
                )
            elif candidate.setup_kind in {
                "orb_exp005",
                "orb_exp007",
            }:
                decision, trade = _evaluate_orb_control(
                    candidate=candidate,
                    representation_id=representation_id,
                    session_date=session_date,
                    session_rows=session_rows,
                    five_rows=five_rows,
                )
            else:
                raise ValueError(
                    "Unknown EXP-026 setup kind: "
                    f"{candidate.setup_kind}."
                )

            decision_rows.append(decision)
            if trade is not None:
                trade_rows.append(trade)

    decisions = pd.DataFrame(
        decision_rows,
        columns=DECISION_COLUMNS,
    ).sort_values(
        ["candidate_id", "session_date"],
        kind="stable",
    ).reset_index(drop=True)
    trades = pd.DataFrame(
        trade_rows,
        columns=TRADE_COLUMNS,
    )
    if not trades.empty:
        trades = trades.sort_values(
            [
                "candidate_id",
                "session_date",
                "entry_timestamp_utc",
            ],
            kind="stable",
        ).reset_index(drop=True)

    expected_decision_rows = (
        len(requested) * len(session_dates)
    )
    if len(decisions) != expected_decision_rows:
        raise ValueError(
            "EXP-026 replay did not account for every "
            "candidate-session combination."
        )
    if decisions.duplicated(
        ["candidate_id", "session_date"]
    ).any():
        raise ValueError(
            "EXP-026 replay produced duplicate decisions."
        )
    if not trades.empty and trades.duplicated(
        ["candidate_id", "session_date"]
    ).any():
        raise ValueError(
            "EXP-026 replay exceeded one trade per "
            "candidate per session."
        )
    return decisions, trades


def mirrored_trade_outcomes(
    source_frame: pd.DataFrame,
    trades: pd.DataFrame,
    *,
    representation_id: str,
    allowed_session_start: str,
    allowed_session_end: str,
) -> pd.DataFrame:
    source = normalise_source_frame(
        source_frame,
        representation_id=representation_id,
        allowed_session_start=allowed_session_start,
        allowed_session_end=allowed_session_end,
    )
    groups = {
        str(key): group.reset_index(drop=True)
        for key, group in source.groupby(
            "session_date",
            sort=False,
        )
    }
    rows: list[dict[str, Any]] = []
    for trade in trades.itertuples(index=False):
        candidate = CANDIDATE_SPEC_BY_ID[
            str(trade.candidate_id)
        ]
        target = float(trade.target_price)
        mirrored, reason = execute_trade_from_levels(
            groups[str(trade.session_date)],
            representation_id=representation_id,
            candidate=candidate,
            session_date=str(trade.session_date),
            direction=(
                1
                if str(trade.direction) == "long"
                else -1
            ),
            entry_session_minute=int(
                trade.entry_session_minute
            ),
            forced_flat_session_minute=int(
                trade.forced_flat_session_minute
            ),
            stop_price=float(trade.stop_price),
            target_price=target,
            context_value=float(trade.context_value),
            mirror_post_entry_path=True,
        )
        if mirrored is None:
            raise ValueError(
                "EXP-026 mirrored path could not be executed: "
                f"{reason}."
            )
        rows.append(
            {
                "candidate_id": str(trade.candidate_id),
                "session_date": str(trade.session_date),
                "real_net_pnl_usd": float(
                    trade.net_pnl_usd
                ),
                "mirrored_net_pnl_usd": float(
                    mirrored["net_pnl_usd"]
                ),
                "real_gross_pnl_usd": float(
                    trade.gross_pnl_usd
                ),
                "mirrored_gross_pnl_usd": float(
                    mirrored["gross_pnl_usd"]
                ),
            }
        )
    return pd.DataFrame(
        rows,
        columns=(
            "candidate_id",
            "session_date",
            "real_net_pnl_usd",
            "mirrored_net_pnl_usd",
            "real_gross_pnl_usd",
            "mirrored_gross_pnl_usd",
        ),
    ).sort_values(
        ["candidate_id", "session_date"],
        kind="stable",
    ).reset_index(drop=True)


def _safe_divide(
    numerator: float,
    denominator: float,
) -> float:
    if not np.isfinite(denominator) or denominator == 0:
        return float("nan")
    return float(numerator / denominator)


def _profit_factor(values: np.ndarray) -> float:
    positives = float(values[values > 0].sum())
    negatives = float(values[values < 0].sum())
    if negatives < 0:
        return float(positives / abs(negatives))
    if positives > 0:
        return float("inf")
    return float("nan")


def _maximum_drawdown(
    values: np.ndarray,
) -> tuple[float, int, int]:
    if len(values) == 0:
        return 0.0, 0, 0
    equity = np.cumsum(values, dtype=float)
    equity_with_zero = np.concatenate(
        ([0.0], equity)
    )
    running_max = np.maximum.accumulate(
        equity_with_zero
    )
    drawdown = equity_with_zero - running_max
    maximum_drawdown = float(drawdown.min())

    longest = 0
    current = 0
    for value in drawdown[1:]:
        if value < 0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0

    recovery = 0
    trough_index = int(np.argmin(drawdown))
    if maximum_drawdown < 0:
        prior_peak = running_max[trough_index]
        later = np.flatnonzero(
            equity_with_zero[trough_index:]
            >= prior_peak
        )
        if len(later):
            recovery = int(later[0])
        else:
            recovery = int(
                len(equity_with_zero) - trough_index - 1
            )
    return maximum_drawdown, longest, recovery


def _max_consecutive_losses(
    values: np.ndarray,
) -> int:
    maximum = 0
    current = 0
    for value in values:
        if value < 0:
            current += 1
            maximum = max(maximum, current)
        else:
            current = 0
    return maximum


def _worst_rolling(
    values: np.ndarray,
    window: int,
) -> float:
    if len(values) < window:
        return float("nan")
    return float(
        pd.Series(values).rolling(window).sum().min()
    )


def _years_in_span(
    trades: pd.DataFrame,
    period_start: str | None,
    period_end: str | None,
) -> float:
    if period_start is not None and period_end is not None:
        start = pd.Timestamp(period_start)
        end = pd.Timestamp(period_end)
        days = max((end - start).days + 1, 1)
        return max(days / 365.2425, 1 / 365.2425)
    if trades.empty:
        return 1.0
    dates = pd.to_datetime(trades["session_date"])
    days = max(
        (dates.max() - dates.min()).days + 1,
        1,
    )
    return max(days / 365.2425, 1 / 365.2425)


def summarise_trade_slice(
    trades: pd.DataFrame,
    *,
    round_trip_cost_usd: float = BASE_ROUND_TRIP_COST_USD,
    period_start: str | None = None,
    period_end: str | None = None,
) -> dict[str, Any]:
    if trades.empty:
        values = np.array([], dtype=float)
        gross_values = np.array([], dtype=float)
        holding = np.array([], dtype=float)
    else:
        ordered = trades.sort_values(
            ["session_date", "entry_timestamp_utc"],
            kind="stable",
        )
        gross_values = ordered[
            "gross_pnl_usd"
        ].to_numpy(dtype=float)
        values = (
            gross_values - float(round_trip_cost_usd)
        )
        holding = (
            ordered["exit_session_minute"].to_numpy(
                dtype=float
            )
            - ordered["entry_session_minute"].to_numpy(
                dtype=float
            )
        )

    count = int(len(values))
    winners = values[values > 0]
    losers = values[values < 0]
    maximum_drawdown, drawdown_duration, recovery_duration = (
        _maximum_drawdown(values)
    )
    net_profit = float(values.sum())
    gross_profit = float(winners.sum())
    gross_loss = float(losers.sum())
    average_winner = (
        float(winners.mean())
        if len(winners)
        else float("nan")
    )
    average_loser = (
        float(losers.mean())
        if len(losers)
        else float("nan")
    )
    years = _years_in_span(
        trades,
        period_start,
        period_end,
    )
    return {
        "completed_trades": count,
        "net_profit_usd": net_profit,
        "gross_profit_usd": gross_profit,
        "gross_loss_usd": gross_loss,
        "trade_profit_factor": _profit_factor(values),
        "win_rate": (
            float((values > 0).mean())
            if count
            else float("nan")
        ),
        "average_trade_usd": (
            float(values.mean())
            if count
            else float("nan")
        ),
        "median_trade_usd": (
            float(np.median(values))
            if count
            else float("nan")
        ),
        "average_winner_usd": average_winner,
        "average_loser_usd": average_loser,
        "payoff_ratio": _safe_divide(
            average_winner,
            abs(average_loser),
        ),
        "maximum_drawdown_usd": maximum_drawdown,
        "maximum_drawdown_percent": (
            maximum_drawdown
            / REFERENCE_CAPITAL_USD
            * 100.0
        ),
        "net_profit_to_drawdown": _safe_divide(
            net_profit,
            abs(maximum_drawdown),
        ),
        "drawdown_duration_trades": (
            drawdown_duration
        ),
        "recovery_duration_trades": (
            recovery_duration
        ),
        "maximum_consecutive_losses": (
            _max_consecutive_losses(values)
        ),
        "worst_20_trade_result": _worst_rolling(
            values,
            20,
        ),
        "worst_50_trade_result": _worst_rolling(
            values,
            50,
        ),
        "worst_100_trade_result": _worst_rolling(
            values,
            100,
        ),
        "trades_per_year": float(count / years),
        "average_holding_minutes": (
            float(holding.mean())
            if count
            else float("nan")
        ),
        "median_holding_minutes": (
            float(np.median(holding))
            if count
            else float("nan")
        ),
        "average_trade_to_round_trip_cost": _safe_divide(
            float(values.mean())
            if count
            else float("nan"),
            float(round_trip_cost_usd),
        ),
    }


def candidate_metrics(
    trades: pd.DataFrame,
    *,
    candidate_ids: Iterable[str] = ALL_CANDIDATE_IDS,
    period_start: str | None = None,
    period_end: str | None = None,
    round_trip_cost_usd: float = BASE_ROUND_TRIP_COST_USD,
) -> pd.DataFrame:
    requested = tuple(str(value) for value in candidate_ids)
    rows: list[dict[str, Any]] = []

    if period_start is not None:
        trades = trades.loc[
            trades["session_date"].astype(str)
            >= period_start
        ]
    if period_end is not None:
        trades = trades.loc[
            trades["session_date"].astype(str)
            <= period_end
        ]

    for candidate_id in requested:
        candidate = CANDIDATE_SPEC_BY_ID[
            candidate_id
        ]
        candidate_trades = trades.loc[
            trades["candidate_id"] == candidate_id
        ]
        for segment in METRIC_SEGMENTS:
            if segment == DIRECTION_LONG:
                current = candidate_trades.loc[
                    candidate_trades["direction"] == "long"
                ]
            elif segment == DIRECTION_SHORT:
                current = candidate_trades.loc[
                    candidate_trades["direction"] == "short"
                ]
            else:
                current = candidate_trades

            summary = summarise_trade_slice(
                current,
                round_trip_cost_usd=round_trip_cost_usd,
                period_start=period_start,
                period_end=period_end,
            )
            rows.append(
                {
                    "candidate_id": candidate_id,
                    "family_id": candidate.family_id,
                    "candidate_role": (
                        candidate.candidate_role
                    ),
                    "segment": segment,
                    **summary,
                }
            )

    return pd.DataFrame(
        rows,
        columns=METRIC_COLUMNS,
    )


def annual_results(
    trades: pd.DataFrame,
    *,
    candidate_ids: Iterable[str] = ALL_CANDIDATE_IDS,
    start_year: int | None = None,
    end_year: int | None = None,
) -> pd.DataFrame:
    requested = tuple(str(value) for value in candidate_ids)
    local = trades.copy()
    local["year"] = pd.to_datetime(
        local["session_date"],
        errors="coerce",
    ).dt.year
    years = (
        list(range(start_year, end_year + 1))
        if (
            start_year is not None
            and end_year is not None
        )
        else sorted(
            local["year"].unique()
            if not local.empty
            else []
        )
    )
    rows: list[dict[str, Any]] = []
    for candidate_id in requested:
        candidate = CANDIDATE_SPEC_BY_ID[
            candidate_id
        ]
        for year in years:
            current = local.loc[
                (local["candidate_id"] == candidate_id)
                & (local["year"] == year)
            ]
            summary = summarise_trade_slice(
                current,
                period_start=f"{year}-01-01",
                period_end=f"{year}-12-31",
            )
            rows.append(
                {
                    "candidate_id": candidate_id,
                    "family_id": candidate.family_id,
                    "candidate_role": (
                        candidate.candidate_role
                    ),
                    "year": int(year),
                    "completed_trades": summary[
                        "completed_trades"
                    ],
                    "net_profit_usd": summary[
                        "net_profit_usd"
                    ],
                    "trade_profit_factor": summary[
                        "trade_profit_factor"
                    ],
                    "maximum_drawdown_usd": summary[
                        "maximum_drawdown_usd"
                    ],
                    "win_rate": summary["win_rate"],
                }
            )
    return pd.DataFrame(rows)


def monthly_results(
    trades: pd.DataFrame,
    *,
    candidate_ids: Iterable[str],
    start_month: str,
    end_month: str,
) -> pd.DataFrame:
    requested = tuple(str(value) for value in candidate_ids)
    months = pd.period_range(
        start=start_month,
        end=end_month,
        freq="M",
    )
    local = trades.copy()
    local["month"] = pd.to_datetime(
        local["session_date"],
        errors="coerce",
    ).dt.to_period("M").astype(str)

    rows: list[dict[str, Any]] = []
    for candidate_id in requested:
        for month in months:
            label = str(month)
            current = local.loc[
                (local["candidate_id"] == candidate_id)
                & (local["month"] == label)
            ]
            summary = summarise_trade_slice(current)
            rows.append(
                {
                    "candidate_id": candidate_id,
                    "month": label,
                    "completed_trades": summary[
                        "completed_trades"
                    ],
                    "net_profit_usd": summary[
                        "net_profit_usd"
                    ],
                    "trade_profit_factor": summary[
                        "trade_profit_factor"
                    ],
                    "maximum_drawdown_usd": summary[
                        "maximum_drawdown_usd"
                    ],
                }
            )
    return pd.DataFrame(rows)


def cost_sensitivity(
    trades: pd.DataFrame,
    *,
    candidate_ids: Iterable[str],
    slippage_ticks_per_side: Iterable[int] = (
        0,
        1,
        2,
        3,
    ),
    period_start: str | None = None,
    period_end: str | None = None,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for ticks in slippage_ticks_per_side:
        round_trip_cost = (
            2.0 * NQ_FEES_USD_PER_SIDE
            + 2.0 * int(ticks) * NQ_TICK_VALUE_USD
        )
        metrics = candidate_metrics(
            trades,
            candidate_ids=candidate_ids,
            period_start=period_start,
            period_end=period_end,
            round_trip_cost_usd=round_trip_cost,
        )
        metrics = metrics.loc[
            metrics["segment"] == DIRECTION_ALL
        ]
        for row in metrics.itertuples(index=False):
            rows.append(
                {
                    "candidate_id": row.candidate_id,
                    "slippage_ticks_per_side": int(
                        ticks
                    ),
                    "round_trip_cost_usd": float(
                        round_trip_cost
                    ),
                    "completed_trades": int(
                        row.completed_trades
                    ),
                    "net_profit_usd": float(
                        row.net_profit_usd
                    ),
                    "trade_profit_factor": float(
                        row.trade_profit_factor
                    ),
                    "maximum_drawdown_usd": float(
                        row.maximum_drawdown_usd
                    ),
                    "net_profit_to_drawdown": float(
                        row.net_profit_to_drawdown
                    ),
                }
            )
    return pd.DataFrame(rows)


def candidate_registry_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "candidate_id": item.candidate_id,
                "family_id": item.family_id,
                "candidate_role": item.candidate_role,
                "setup_kind": item.setup_kind,
                "threshold": item.threshold,
                "exit_mode": item.exit_mode,
                "selectable": item.selectable,
                "opening_range_minutes": (
                    item.opening_range_minutes
                ),
                "direction_mode": item.direction_mode,
                "last_signal_start_session_minute": (
                    item.last_signal_start_session_minute
                ),
                "forced_flat_session_minute": (
                    item.forced_flat_session_minute
                ),
            }
            for item in CANDIDATE_SPECS
        ]
    )


def _rankable_metric_frame(
    metrics: pd.DataFrame,
    *,
    candidate_ids: Iterable[str],
) -> pd.DataFrame:
    requested = tuple(str(value) for value in candidate_ids)
    current = metrics.loc[
        (metrics["segment"] == DIRECTION_ALL)
        & metrics["candidate_id"].isin(requested)
        & (metrics["candidate_role"] == "DEVELOPMENT")
        & (metrics["completed_trades"] > 0)
    ].copy()
    return current


def select_phase_a_survivors(
    metrics: pd.DataFrame,
    *,
    candidate_ids: Iterable[str] = DEVELOPMENT_CANDIDATE_IDS,
    maximum_per_family: int = 2,
) -> pd.DataFrame:
    current = _rankable_metric_frame(
        metrics,
        candidate_ids=candidate_ids,
    )
    rows: list[pd.DataFrame] = []
    for family_id in (
        "gap_fade",
        "premarket_momentum_continuation",
        "opening_drive_continuation",
    ):
        family = current.loc[
            current["family_id"] == family_id
        ].copy()
        family["_pf"] = family[
            "trade_profit_factor"
        ].replace(
            {np.nan: -np.inf}
        )
        family["_npdd"] = family[
            "net_profit_to_drawdown"
        ].replace(
            {np.nan: -np.inf}
        )
        family = family.sort_values(
            [
                "_pf",
                "_npdd",
                "net_profit_usd",
                "completed_trades",
                "candidate_id",
            ],
            ascending=[
                False,
                False,
                False,
                False,
                True,
            ],
            kind="stable",
        ).head(maximum_per_family)
        family["phase_a_family_rank"] = np.arange(
            1,
            len(family) + 1,
        )
        rows.append(family)

    if not rows:
        return pd.DataFrame(
            columns=(
                "candidate_id",
                "family_id",
                "phase_a_family_rank",
            )
        )
    result = pd.concat(
        rows,
        ignore_index=True,
    )
    return result.drop(
        columns=["_pf", "_npdd"],
        errors="ignore",
    ).sort_values(
        ["family_id", "phase_a_family_rank"],
        kind="stable",
    ).reset_index(drop=True)


def select_phase_b_finalists(
    development_metrics: pd.DataFrame,
    validation_metrics: pd.DataFrame,
    validation_annual: pd.DataFrame,
    *,
    phase_a_candidate_ids: Iterable[str],
    maximum_per_family: int = 1,
) -> pd.DataFrame:
    survivors = tuple(
        str(value)
        for value in phase_a_candidate_ids
    )
    development = development_metrics.loc[
        (development_metrics["segment"] == DIRECTION_ALL)
        & development_metrics["candidate_id"].isin(
            survivors
        )
    ].set_index("candidate_id")
    validation = validation_metrics.loc[
        (validation_metrics["segment"] == DIRECTION_ALL)
        & validation_metrics["candidate_id"].isin(
            survivors
        )
        & (validation_metrics["completed_trades"] > 0)
    ].copy()

    profitable_years = (
        validation_annual.loc[
            validation_annual["candidate_id"].isin(
                survivors
            )
            & (
                validation_annual["net_profit_usd"]
                > 0
            )
        ]
        .groupby("candidate_id")
        .size()
        .to_dict()
    )
    validation["profitable_internal_validation_years"] = (
        validation["candidate_id"].map(
            profitable_years
        ).fillna(0).astype(int)
    )
    validation["development_trade_profit_factor"] = (
        validation["candidate_id"].map(
            development["trade_profit_factor"]
        )
    )
    validation["_pf"] = validation[
        "trade_profit_factor"
    ].replace({np.nan: -np.inf})
    validation["_npdd"] = validation[
        "net_profit_to_drawdown"
    ].replace({np.nan: -np.inf})
    validation["_dev_pf"] = validation[
        "development_trade_profit_factor"
    ].replace({np.nan: -np.inf})

    rows: list[pd.DataFrame] = []
    for family_id in (
        "gap_fade",
        "premarket_momentum_continuation",
        "opening_drive_continuation",
    ):
        family = validation.loc[
            validation["family_id"] == family_id
        ].sort_values(
            [
                "profitable_internal_validation_years",
                "_pf",
                "_npdd",
                "net_profit_usd",
                "_dev_pf",
                "candidate_id",
            ],
            ascending=[
                False,
                False,
                False,
                False,
                False,
                True,
            ],
            kind="stable",
        ).head(maximum_per_family)
        family["phase_b_family_rank"] = np.arange(
            1,
            len(family) + 1,
        )
        rows.append(family)

    if not rows:
        return pd.DataFrame(
            columns=(
                "candidate_id",
                "family_id",
                "phase_b_family_rank",
            )
        )
    result = pd.concat(
        rows,
        ignore_index=True,
    )
    return result.drop(
        columns=[
            "_pf",
            "_npdd",
            "_dev_pf",
        ],
        errors="ignore",
    ).sort_values(
        ["family_id", "phase_b_family_rank"],
        kind="stable",
    ).reset_index(drop=True)


def parameter_stability(
    metrics: pd.DataFrame,
    *,
    candidate_ids: Iterable[str] = DEVELOPMENT_CANDIDATE_IDS,
) -> pd.DataFrame:
    current = metrics.loc[
        (metrics["segment"] == DIRECTION_ALL)
        & metrics["candidate_id"].isin(
            tuple(candidate_ids)
        )
    ].copy()
    registry = candidate_registry_frame().loc[
        lambda frame: frame["candidate_role"]
        == "DEVELOPMENT"
    ]
    current = current.merge(
        registry[
            [
                "candidate_id",
                "threshold",
                "exit_mode",
            ]
        ],
        on="candidate_id",
        how="left",
        validate="one_to_one",
    )
    rows: list[dict[str, Any]] = []
    for family_id, family in current.groupby(
        "family_id",
        sort=True,
    ):
        family = family.sort_values(
            ["exit_mode", "threshold"],
            kind="stable",
        )
        for row in family.itertuples(index=False):
            same_exit = family.loc[
                family["exit_mode"] == row.exit_mode
            ].sort_values(
                "threshold",
                kind="stable",
            )
            threshold_values = list(
                same_exit["threshold"]
            )
            position = threshold_values.index(
                row.threshold
            )
            lower = (
                same_exit.iloc[position - 1]
                if position > 0
                else None
            )
            upper = (
                same_exit.iloc[position + 1]
                if position + 1 < len(same_exit)
                else None
            )
            paired = family.loc[
                (family["threshold"] == row.threshold)
                & (
                    family["exit_mode"]
                    != row.exit_mode
                )
            ]
            rows.append(
                {
                    "candidate_id": row.candidate_id,
                    "family_id": family_id,
                    "threshold": row.threshold,
                    "exit_mode": row.exit_mode,
                    "trade_profit_factor": (
                        row.trade_profit_factor
                    ),
                    "net_profit_to_drawdown": (
                        row.net_profit_to_drawdown
                    ),
                    "lower_threshold_candidate": (
                        ""
                        if lower is None
                        else lower["candidate_id"]
                    ),
                    "lower_threshold_profit_factor": (
                        np.nan
                        if lower is None
                        else lower[
                            "trade_profit_factor"
                        ]
                    ),
                    "upper_threshold_candidate": (
                        ""
                        if upper is None
                        else upper["candidate_id"]
                    ),
                    "upper_threshold_profit_factor": (
                        np.nan
                        if upper is None
                        else upper[
                            "trade_profit_factor"
                        ]
                    ),
                    "paired_exit_candidate": (
                        ""
                        if paired.empty
                        else paired.iloc[0][
                            "candidate_id"
                        ]
                    ),
                    "paired_exit_profit_factor": (
                        np.nan
                        if paired.empty
                        else paired.iloc[0][
                            "trade_profit_factor"
                        ]
                    ),
                }
            )
    return pd.DataFrame(rows)


validate_candidate_specs()
