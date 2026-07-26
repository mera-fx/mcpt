from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import hashlib
import json
import math
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd

from exp023_preregistration import FINALIST_IDS


REFERENCE_SESSION_COUNT = 1_331
ALLOWED_SESSION_DATE_START = "2020-01-03"
ALLOWED_SESSION_DATE_END = "2025-12-31"
ALLOWED_UTC_READ_START = pd.Timestamp(
    "2020-01-02T23:00:00+00:00"
)
ALLOWED_UTC_READ_END = pd.Timestamp(
    "2025-12-31T21:00:00+00:00"
)
RESEARCH_TIMEZONE = "America/New_York"

SESSION_START_MINUTE = 18 * 60
PREMARKET_START_SESSION_MINUTE = 840
CASH_START_SESSION_MINUTE = 930
CASH_END_SESSION_MINUTE = 1320
ENTRY_SESSION_MINUTE = 935
FORCED_FLAT_SESSION_MINUTE = 1315
PREMARKET_FIVE_MINUTE_BINS = tuple(range(168, 186))
CASH_FIVE_MINUTE_BINS = tuple(range(186, 264))

NQ_MULTIPLIER_USD_PER_POINT = 20.0
ROUND_TRIP_COST_USD = 15.0

REPRESENTATION_IDS = (
    "BACKWARD_ADJUSTED",
    "UNADJUSTED",
)


@dataclass(frozen=True)
class CandidateSpec:
    candidate_id: str
    family_id: str
    setup_kind: str
    threshold: float
    exit_mode: str


CANDIDATE_SPECS = (
    CandidateSpec(
        candidate_id="gap_fade_0p50_1r",
        family_id="gap_fade",
        setup_kind="gap_fade",
        threshold=0.50,
        exit_mode="one_r",
    ),
    CandidateSpec(
        candidate_id="premarket_continuation_0p50_time",
        family_id="premarket_momentum_continuation",
        setup_kind="premarket_continuation",
        threshold=0.50,
        exit_mode="time",
    ),
    CandidateSpec(
        candidate_id="premarket_continuation_0p75_time",
        family_id="premarket_momentum_continuation",
        setup_kind="premarket_continuation",
        threshold=0.75,
        exit_mode="time",
    ),
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

SESSION_ALIGNMENT_FIELDS = (
    "representation_id",
    "candidate_id",
    "session_date",
    "source_row_count",
    "cash_five_minute_bin_count",
    "premarket_five_minute_bin_count",
    "entry_minute_present",
    "forced_flat_minute_present",
    "previous_reference_session",
    "previous_cash_five_minute_bin_count",
    "eligible",
    "ineligibility_reason",
    "trade_flag",
    "direction",
    "entry_timestamp_utc",
    "context_value",
)

TRANSFER_TRADE_FIELDS = (
    "representation_id",
    "candidate_id",
    "family_id",
    "session_date",
    "direction",
    "entry_timestamp_utc",
    "exit_timestamp_utc",
    "entry_minute_slot",
    "exit_minute_slot",
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
)

TRADE_ALIGNMENT_FIELDS = (
    "representation_id",
    "candidate_id",
    "session_date",
    "eligible",
    "reference_trade_flag",
    "transfer_trade_flag",
    "reference_direction",
    "transfer_direction",
    "trade_indicator_and_direction_match",
    "common_trade",
    "reference_entry_timestamp_utc",
    "transfer_entry_timestamp_utc",
    "entry_timestamp_match",
    "reference_gross_pnl_usd",
    "transfer_gross_pnl_usd",
    "reference_net_pnl_usd",
    "transfer_net_pnl_usd",
    "gross_pnl_sign_match",
)

TRANSFER_METRIC_FIELDS = (
    "representation_id",
    "candidate_id",
    "reference_session_count",
    "eligible_session_count",
    "eligible_session_share",
    "trade_indicator_and_direction_agreement",
    "reference_trade_count",
    "transfer_trade_count",
    "trade_count_relative_difference",
    "common_trade_count",
    "common_trade_match_share",
    "matching_entry_timestamp_agreement",
    "common_trade_gross_pnl_correlation",
    "common_trade_gross_pnl_sign_agreement",
    "transfer_profit_factor",
    "transfer_net_profit_usd",
    "transfer_maximum_drawdown_usd",
    "gate_session_eligibility",
    "gate_trade_indicator_and_direction",
    "gate_trade_count",
    "gate_common_trade_match",
    "gate_entry_timestamp",
    "gate_gross_pnl_correlation",
    "gate_gross_pnl_sign",
    "all_transfer_gates_pass",
)

REPRESENTATION_SENSITIVITY_FIELDS = (
    "candidate_id",
    "common_eligible_session_count",
    "trade_indicator_and_direction_agreement",
    "backward_adjusted_trade_count",
    "unadjusted_trade_count",
    "common_trade_count",
    "common_trade_match_share",
    "matching_entry_timestamp_agreement",
    "common_trade_gross_pnl_correlation",
    "common_trade_gross_pnl_sign_agreement",
)


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


def validate_candidate_specs() -> None:
    candidate_ids = tuple(item.candidate_id for item in CANDIDATE_SPECS)
    if candidate_ids != FINALIST_IDS:
        raise ValueError("EXP-023 candidate specifications changed.")
    if len(set(candidate_ids)) != len(candidate_ids):
        raise ValueError("EXP-023 candidate identifiers are not unique.")
    expected = {
        "gap_fade_0p50_1r": (
            "gap_fade",
            "gap_fade",
            0.50,
            "one_r",
        ),
        "premarket_continuation_0p50_time": (
            "premarket_momentum_continuation",
            "premarket_continuation",
            0.50,
            "time",
        ),
        "premarket_continuation_0p75_time": (
            "premarket_momentum_continuation",
            "premarket_continuation",
            0.75,
            "time",
        ),
    }
    for item in CANDIDATE_SPECS:
        actual = (
            item.family_id,
            item.setup_kind,
            item.threshold,
            item.exit_mode,
        )
        if actual != expected[item.candidate_id]:
            raise ValueError(
                f"EXP-023 candidate rule changed: {item.candidate_id}."
            )


def validate_reference_session_dates(
    session_dates: Iterable[str],
    *,
    require_production_count: bool = False,
) -> tuple[str, ...]:
    values = tuple(str(value) for value in session_dates)
    if not values:
        raise ValueError("EXP-023 reference session axis is empty.")
    if values != tuple(sorted(set(values))):
        raise ValueError(
            "EXP-023 reference sessions must be sorted and unique."
        )
    if (
        values[0] < ALLOWED_SESSION_DATE_START
        or values[-1] > ALLOWED_SESSION_DATE_END
    ):
        raise ValueError("EXP-023 reference session axis left the lock.")
    if require_production_count and (
        len(values) != REFERENCE_SESSION_COUNT
        or values[0] != ALLOWED_SESSION_DATE_START
        or values[-1] != ALLOWED_SESSION_DATE_END
    ):
        raise ValueError(
            "EXP-023 production reference axis must contain exactly "
            "1,331 sessions from 2020-01-03 through 2025-12-31."
        )
    return values


def normalise_source_frame(
    frame: pd.DataFrame,
    *,
    representation_id: str,
) -> pd.DataFrame:
    if representation_id not in REPRESENTATION_IDS:
        raise ValueError(
            f"Unknown EXP-023 representation: {representation_id}."
        )
    missing = sorted(set(SOURCE_COLUMNS).difference(frame.columns))
    if missing:
        raise ValueError(
            "EXP-023 source frame is missing columns: "
            + ", ".join(missing)
        )

    local = frame.loc[:, SOURCE_COLUMNS].copy()
    local["ts_event"] = pd.to_datetime(
        local["ts_event"],
        utc=True,
        errors="raise",
    )
    if local.empty:
        raise ValueError("EXP-023 permitted source scan is empty.")
    if (
        local["ts_event"].min() < ALLOWED_UTC_READ_START
        or local["ts_event"].max() >= ALLOWED_UTC_READ_END
    ):
        raise ValueError(
            "EXP-023 source scan returned out-of-window timestamps."
        )
    if local["ts_event"].duplicated().any():
        raise ValueError("EXP-023 source timestamps are not unique.")
    if not local["ts_event"].is_monotonic_increasing:
        local = local.sort_values("ts_event", kind="stable").reset_index(
            drop=True
        )

    local["session_date"] = pd.to_datetime(
        local["trading_date"],
        errors="raise",
    ).dt.strftime("%Y-%m-%d")
    if (
        local["session_date"].min() < ALLOWED_SESSION_DATE_START
        or local["session_date"].max() > ALLOWED_SESSION_DATE_END
    ):
        raise ValueError(
            "EXP-023 source scan returned an out-of-window trading date."
        )

    numeric_columns = ("open", "high", "low", "close", "volume")
    for column in numeric_columns:
        local[column] = pd.to_numeric(local[column], errors="raise")
    if not np.isfinite(
        local.loc[:, numeric_columns].to_numpy(dtype=float)
    ).all():
        raise ValueError("EXP-023 source OHLCV contains nonfinite values.")
    if (local["volume"] < 0).any():
        raise ValueError("EXP-023 source volume is negative.")
    if (
        (local["high"] < local[["open", "close", "low"]].max(axis=1))
        | (local["low"] > local[["open", "close", "high"]].min(axis=1))
    ).any():
        raise ValueError("EXP-023 source OHLC geometry is invalid.")

    local_timestamp = local["ts_event"].dt.tz_convert(RESEARCH_TIMEZONE)
    if (
        (local_timestamp.dt.second != 0)
        | (local_timestamp.dt.microsecond != 0)
    ).any():
        raise ValueError(
            "EXP-023 timestamps must be exact UTC minute starts."
        )
    clock_minute = (
        local_timestamp.dt.hour.astype(int) * 60
        + local_timestamp.dt.minute.astype(int)
    )
    local["session_minute"] = np.where(
        clock_minute >= SESSION_START_MINUTE,
        clock_minute - SESSION_START_MINUTE,
        clock_minute + (24 * 60 - SESSION_START_MINUTE),
    ).astype(np.int16)

    local_dates = local_timestamp.dt.strftime("%Y-%m-%d")
    derived_trading_dates = pd.to_datetime(local_dates)
    evening = clock_minute >= SESSION_START_MINUTE
    derived_trading_dates = derived_trading_dates.where(
        ~evening,
        derived_trading_dates + pd.Timedelta(days=1),
    ).dt.strftime("%Y-%m-%d")
    if not derived_trading_dates.equals(local["session_date"]):
        raise ValueError(
            "EXP-023 trading-date and New York session semantics differ."
        )

    local = local.loc[
        local["session_minute"].between(
            0,
            CASH_END_SESSION_MINUTE - 1,
        )
    ].copy()
    if local.duplicated(["session_date", "session_minute"]).any():
        raise ValueError(
            "EXP-023 source contains duplicate session minutes."
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
            "EXP-023 five-minute input is missing: "
            + ", ".join(missing)
        )
    local = frame.loc[
        frame["session_minute"].between(
            PREMARKET_START_SESSION_MINUTE,
            CASH_END_SESSION_MINUTE - 1,
        )
    ].copy()
    if local.empty:
        return pd.DataFrame(
            columns=[
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
            ]
        )
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
    return result


def _sign(value: float) -> int:
    return 1 if value > 0 else -1 if value < 0 else 0


def _iso_timestamp(value: Any) -> str:
    return pd.Timestamp(value).isoformat()


def _empty_five_minute() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
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
        ]
    )


def _execute_trade(
    session_rows: pd.DataFrame,
    *,
    representation_id: str,
    candidate: CandidateSpec,
    session_date: str,
    direction: int,
    stop_price: float,
    target_price: float,
    context_value: float,
) -> dict[str, Any] | None:
    entry_rows = session_rows.loc[
        session_rows["session_minute"] == ENTRY_SESSION_MINUTE
    ]
    forced_rows = session_rows.loc[
        session_rows["session_minute"] == FORCED_FLAT_SESSION_MINUTE
    ]
    if len(entry_rows) != 1 or len(forced_rows) != 1:
        return None

    entry_row = entry_rows.iloc[0]
    forced_row = forced_rows.iloc[0]
    entry_price = float(entry_row["open"])
    risk_points = direction * (entry_price - stop_price)
    if not np.isfinite(risk_points) or risk_points <= 0:
        return None

    chosen_price = float(forced_row["open"])
    chosen_timestamp = forced_row["ts_event"]
    chosen_minute = FORCED_FLAT_SESSION_MINUTE
    chosen_reason = "forced_flat_1555"

    exit_rows = session_rows.loc[
        session_rows["session_minute"].between(
            ENTRY_SESSION_MINUTE,
            FORCED_FLAT_SESSION_MINUTE - 1,
        )
    ].sort_values("ts_event", kind="stable")
    for row in exit_rows.itertuples(index=False):
        bar_open = float(row.open)
        bar_high = float(row.high)
        bar_low = float(row.low)
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
            chosen_reason = "gap_through_stop"
            break
        if stop_touch:
            chosen_price = stop_price
            chosen_timestamp = row.ts_event
            chosen_minute = int(row.session_minute)
            chosen_reason = "protective_stop"
            break
        if target_touch:
            chosen_price = target_price
            chosen_timestamp = row.ts_event
            chosen_minute = int(row.session_minute)
            chosen_reason = "profit_target"
            break

    gross_pnl = (
        direction
        * (chosen_price - entry_price)
        * NQ_MULTIPLIER_USD_PER_POINT
    )
    return {
        "representation_id": representation_id,
        "candidate_id": candidate.candidate_id,
        "family_id": candidate.family_id,
        "session_date": session_date,
        "direction": "long" if direction == 1 else "short",
        "entry_timestamp_utc": _iso_timestamp(entry_row["ts_event"]),
        "exit_timestamp_utc": _iso_timestamp(chosen_timestamp),
        "entry_minute_slot": (
            ENTRY_SESSION_MINUTE - CASH_START_SESSION_MINUTE
        ),
        "exit_minute_slot": (
            chosen_minute - CASH_START_SESSION_MINUTE
        ),
        "entry_price": entry_price,
        "stop_price": float(stop_price),
        "target_price": (
            float(target_price)
            if np.isfinite(target_price)
            else np.nan
        ),
        "exit_price": float(chosen_price),
        "risk_points": float(risk_points),
        "gross_pnl_usd": float(gross_pnl),
        "transaction_cost_usd": ROUND_TRIP_COST_USD,
        "net_pnl_usd": float(gross_pnl - ROUND_TRIP_COST_USD),
        "exit_reason": chosen_reason,
        "context_value": float(context_value),
    }


def replay_representation(
    frame: pd.DataFrame,
    *,
    representation_id: str,
    reference_session_dates: Iterable[str],
    require_production_count: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    validate_candidate_specs()
    dates = validate_reference_session_dates(
        reference_session_dates,
        require_production_count=require_production_count,
    )
    source = normalise_source_frame(
        frame,
        representation_id=representation_id,
    )
    five_minute = aggregate_observed_five_minute(source)
    source_groups = {
        str(key): group.reset_index(drop=True)
        for key, group in source.groupby("session_date", sort=False)
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
        for index, session_date in enumerate(dates)
    }

    alignment_rows: list[dict[str, Any]] = []
    trade_rows: list[dict[str, Any]] = []
    for candidate in CANDIDATE_SPECS:
        for session_date in dates:
            session_rows = source_groups.get(
                session_date,
                pd.DataFrame(columns=source.columns),
            )
            five_rows = five_groups.get(
                session_date,
                _empty_five_minute(),
            )
            cash_rows = five_rows.loc[
                five_rows["five_minute_bin"].isin(
                    CASH_FIVE_MINUTE_BINS
                )
            ]
            premarket_rows = five_rows.loc[
                five_rows["five_minute_bin"].isin(
                    PREMARKET_FIVE_MINUTE_BINS
                )
            ]
            cash_count = int(
                cash_rows["five_minute_bin"].nunique()
            )
            premarket_count = int(
                premarket_rows["five_minute_bin"].nunique()
            )
            entry_present = int(
                (
                    session_rows["session_minute"]
                    == ENTRY_SESSION_MINUTE
                ).sum()
            ) == 1
            forced_present = int(
                (
                    session_rows["session_minute"]
                    == FORCED_FLAT_SESSION_MINUTE
                ).sum()
            ) == 1

            position = date_position[session_date]
            previous_date = (
                dates[position - 1]
                if position > 0
                else ""
            )
            previous_five = five_groups.get(
                previous_date,
                _empty_five_minute(),
            )
            previous_cash = previous_five.loc[
                previous_five["five_minute_bin"].isin(
                    CASH_FIVE_MINUTE_BINS
                )
            ]
            previous_cash_count = int(
                previous_cash["five_minute_bin"].nunique()
            )

            reasons: list[str] = []
            if session_rows.empty:
                reasons.append("SOURCE_SESSION_MISSING")
            if cash_count != len(CASH_FIVE_MINUTE_BINS):
                reasons.append("CASH_FIVE_MINUTE_BINS_INCOMPLETE")
            if not entry_present:
                reasons.append("ENTRY_MINUTE_0935_MISSING")
            if not forced_present:
                reasons.append("FORCED_FLAT_MINUTE_1555_MISSING")
            if (
                candidate.setup_kind == "premarket_continuation"
                and premarket_count
                != len(PREMARKET_FIVE_MINUTE_BINS)
            ):
                reasons.append(
                    "PREMARKET_FIVE_MINUTE_BINS_INCOMPLETE"
                )
            if candidate.setup_kind == "gap_fade":
                if not previous_date:
                    reasons.append(
                        "PREVIOUS_REFERENCE_SESSION_UNAVAILABLE"
                    )
                elif previous_cash_count != len(
                    CASH_FIVE_MINUTE_BINS
                ):
                    reasons.append(
                        "PREVIOUS_CASH_FIVE_MINUTE_BINS_INCOMPLETE"
                    )

            eligible = not reasons
            context_value = np.nan
            direction = 0
            stop_price = np.nan
            target_price = np.nan
            trade: dict[str, Any] | None = None

            if eligible:
                first_cash = cash_rows.loc[
                    cash_rows["five_minute_bin"]
                    == CASH_FIVE_MINUTE_BINS[0]
                ].iloc[0]
                first_bar_direction = _sign(
                    float(first_cash["close"])
                    - float(first_cash["open"])
                )
                if candidate.setup_kind == "gap_fade":
                    previous_close = float(
                        previous_cash.loc[
                            previous_cash["five_minute_bin"]
                            == CASH_FIVE_MINUTE_BINS[-1],
                            "close",
                        ].iloc[0]
                    )
                    previous_range = float(
                        previous_cash["high"].max()
                        - previous_cash["low"].min()
                    )
                    gap_move = (
                        float(first_cash["open"])
                        - previous_close
                    )
                    gap_direction = _sign(gap_move)
                    context_value = (
                        abs(gap_move) / previous_range
                        if previous_range > 0
                        else np.nan
                    )
                    direction = -gap_direction
                    setup_passes = (
                        np.isfinite(context_value)
                        and context_value >= candidate.threshold
                        and gap_direction != 0
                        and first_bar_direction == direction
                    )
                else:
                    premarket_range = float(
                        premarket_rows["high"].max()
                        - premarket_rows["low"].min()
                    )
                    premarket_move = (
                        float(
                            premarket_rows.loc[
                                premarket_rows[
                                    "five_minute_bin"
                                ]
                                == PREMARKET_FIVE_MINUTE_BINS[-1],
                                "close",
                            ].iloc[0]
                        )
                        - float(
                            premarket_rows.loc[
                                premarket_rows[
                                    "five_minute_bin"
                                ]
                                == PREMARKET_FIVE_MINUTE_BINS[0],
                                "open",
                            ].iloc[0]
                        )
                    )
                    direction = _sign(premarket_move)
                    context_value = (
                        abs(premarket_move) / premarket_range
                        if premarket_range > 0
                        else np.nan
                    )
                    setup_passes = (
                        np.isfinite(context_value)
                        and context_value >= candidate.threshold
                        and direction != 0
                        and first_bar_direction == direction
                    )

                if setup_passes:
                    stop_price = float(
                        first_cash["low"]
                        if direction == 1
                        else first_cash["high"]
                    )
                    entry_price = float(
                        session_rows.loc[
                            session_rows["session_minute"]
                            == ENTRY_SESSION_MINUTE,
                            "open",
                        ].iloc[0]
                    )
                    risk_points = direction * (
                        entry_price - stop_price
                    )
                    target_price = (
                        entry_price + direction * risk_points
                        if candidate.exit_mode == "one_r"
                        else np.nan
                    )
                    if risk_points > 0:
                        trade = _execute_trade(
                            session_rows,
                            representation_id=representation_id,
                            candidate=candidate,
                            session_date=session_date,
                            direction=direction,
                            stop_price=stop_price,
                            target_price=target_price,
                            context_value=float(context_value),
                        )

            trade_flag = trade is not None
            if trade is not None:
                trade_rows.append(trade)
            alignment_rows.append(
                {
                    "representation_id": representation_id,
                    "candidate_id": candidate.candidate_id,
                    "session_date": session_date,
                    "source_row_count": int(len(session_rows)),
                    "cash_five_minute_bin_count": cash_count,
                    "premarket_five_minute_bin_count": (
                        premarket_count
                    ),
                    "entry_minute_present": entry_present,
                    "forced_flat_minute_present": forced_present,
                    "previous_reference_session": previous_date,
                    "previous_cash_five_minute_bin_count": (
                        previous_cash_count
                    ),
                    "eligible": eligible,
                    "ineligibility_reason": "|".join(reasons),
                    "trade_flag": trade_flag,
                    "direction": (
                        trade["direction"]
                        if trade is not None
                        else ""
                    ),
                    "entry_timestamp_utc": (
                        trade["entry_timestamp_utc"]
                        if trade is not None
                        else ""
                    ),
                    "context_value": (
                        float(context_value)
                        if np.isfinite(context_value)
                        else np.nan
                    ),
                }
            )

    alignment = pd.DataFrame(
        alignment_rows,
        columns=SESSION_ALIGNMENT_FIELDS,
    )
    trades = pd.DataFrame(
        trade_rows,
        columns=TRANSFER_TRADE_FIELDS,
    )
    if alignment.duplicated(
        ["representation_id", "candidate_id", "session_date"]
    ).any():
        raise ValueError("EXP-023 session alignment keys are not unique.")
    if trades.duplicated(
        ["representation_id", "candidate_id", "session_date", "direction"]
    ).any():
        raise ValueError("EXP-023 transfer trade keys are not unique.")
    return alignment, trades


def build_reference_decisions(
    ledgers: Mapping[str, pd.DataFrame],
    *,
    reference_session_dates: Iterable[str],
) -> pd.DataFrame:
    dates = validate_reference_session_dates(reference_session_dates)
    rows: list[dict[str, Any]] = []
    for candidate_id in FINALIST_IDS:
        if candidate_id not in ledgers:
            raise ValueError(
                f"Missing EXP-014 reference ledger: {candidate_id}."
            )
        ledger = ledgers[candidate_id].copy()
        required = {
            "candidate_id",
            "session_date",
            "direction",
            "entry_time",
            "gross_pnl_usd",
            "net_pnl_usd",
        }
        missing = sorted(required.difference(ledger.columns))
        if missing:
            raise ValueError(
                f"Reference ledger {candidate_id} is missing: "
                + ", ".join(missing)
            )
        if (
            set(ledger["candidate_id"].astype(str))
            != {candidate_id}
        ):
            raise ValueError(
                f"Reference ledger identity changed: {candidate_id}."
            )
        ledger["session_date"] = ledger["session_date"].astype(str)
        if ledger["session_date"].duplicated().any():
            raise ValueError(
                f"Reference ledger sessions are not unique: {candidate_id}."
            )
        indexed = ledger.set_index("session_date", drop=False)
        for session_date in dates:
            if session_date not in indexed.index:
                rows.append(
                    {
                        "candidate_id": candidate_id,
                        "session_date": session_date,
                        "reference_trade_flag": False,
                        "reference_direction": "",
                        "reference_entry_timestamp_utc": "",
                        "reference_gross_pnl_usd": 0.0,
                        "reference_net_pnl_usd": 0.0,
                    }
                )
                continue
            current = indexed.loc[session_date]
            direction = str(current["direction"]).lower()
            if direction not in {"long", "short"}:
                raise ValueError(
                    f"Reference direction changed: {candidate_id}."
                )
            entry_time = str(current["entry_time"])
            entry_local = pd.Timestamp(
                f"{session_date} {entry_time}",
                tz=RESEARCH_TIMEZONE,
            )
            rows.append(
                {
                    "candidate_id": candidate_id,
                    "session_date": session_date,
                    "reference_trade_flag": True,
                    "reference_direction": direction,
                    "reference_entry_timestamp_utc": (
                        entry_local.tz_convert("UTC").isoformat()
                    ),
                    "reference_gross_pnl_usd": float(
                        current["gross_pnl_usd"]
                    ),
                    "reference_net_pnl_usd": float(
                        current["net_pnl_usd"]
                    ),
                }
            )
    result = pd.DataFrame(rows)
    if result.duplicated(["candidate_id", "session_date"]).any():
        raise ValueError("EXP-023 reference decision keys are not unique.")
    return result


def build_trade_alignment(
    session_alignment: pd.DataFrame,
    transfer_trades: pd.DataFrame,
    reference_decisions: pd.DataFrame,
) -> pd.DataFrame:
    transfer = transfer_trades.loc[
        :,
        [
            "representation_id",
            "candidate_id",
            "session_date",
            "gross_pnl_usd",
            "net_pnl_usd",
        ],
    ].rename(
        columns={
            "gross_pnl_usd": "transfer_gross_pnl_usd",
            "net_pnl_usd": "transfer_net_pnl_usd",
        }
    )
    decisions = session_alignment.loc[
        :,
        [
            "representation_id",
            "candidate_id",
            "session_date",
            "eligible",
            "trade_flag",
            "direction",
            "entry_timestamp_utc",
        ],
    ].rename(
        columns={
            "trade_flag": "transfer_trade_flag",
            "direction": "transfer_direction",
            "entry_timestamp_utc": "transfer_entry_timestamp_utc",
        }
    )
    result = decisions.merge(
        reference_decisions,
        on=["candidate_id", "session_date"],
        how="left",
        validate="many_to_one",
    ).merge(
        transfer,
        on=["representation_id", "candidate_id", "session_date"],
        how="left",
        validate="one_to_one",
    )
    result["transfer_gross_pnl_usd"] = result[
        "transfer_gross_pnl_usd"
    ].fillna(0.0)
    result["transfer_net_pnl_usd"] = result[
        "transfer_net_pnl_usd"
    ].fillna(0.0)
    result["trade_indicator_and_direction_match"] = (
        (
            result["reference_trade_flag"]
            == result["transfer_trade_flag"]
        )
        & (
            ~result["reference_trade_flag"]
            | (
                result["reference_direction"]
                == result["transfer_direction"]
            )
        )
    )
    result["common_trade"] = (
        result["reference_trade_flag"]
        & result["transfer_trade_flag"]
        & (
            result["reference_direction"]
            == result["transfer_direction"]
        )
    )
    result["entry_timestamp_match"] = (
        result["common_trade"]
        & (
            result["reference_entry_timestamp_utc"]
            == result["transfer_entry_timestamp_utc"]
        )
    )
    result["gross_pnl_sign_match"] = (
        result["common_trade"]
        & (
            np.sign(result["reference_gross_pnl_usd"])
            == np.sign(result["transfer_gross_pnl_usd"])
        )
    )
    result = result.loc[:, TRADE_ALIGNMENT_FIELDS].sort_values(
        ["representation_id", "candidate_id", "session_date"],
        kind="stable",
    ).reset_index(drop=True)
    if result.duplicated(
        ["representation_id", "candidate_id", "session_date"]
    ).any():
        raise ValueError("EXP-023 trade alignment keys are not unique.")
    return result


def safe_correlation(left: Iterable[float], right: Iterable[float]) -> float:
    x = np.asarray(tuple(left), dtype=float)
    y = np.asarray(tuple(right), dtype=float)
    valid = np.isfinite(x) & np.isfinite(y)
    x = x[valid]
    y = y[valid]
    if x.size < 2 or np.std(x) == 0 or np.std(y) == 0:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def profit_factor(values: Iterable[float]) -> float:
    local = np.asarray(tuple(values), dtype=float)
    gains = float(local[local > 0].sum())
    losses = float(-local[local < 0].sum())
    if losses == 0:
        return float("inf") if gains > 0 else 0.0
    return gains / losses


def maximum_drawdown(values: Iterable[float]) -> float:
    local = np.asarray(tuple(values), dtype=float)
    if local.size == 0:
        return 0.0
    equity = np.cumsum(local)
    peaks = np.maximum.accumulate(np.r_[0.0, equity])
    drawdown = np.r_[0.0, equity] - peaks
    return float(drawdown.min())


def _ratio(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator else 0.0


def candidate_transfer_metrics(
    trade_alignment: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (representation_id, candidate_id), group in (
        trade_alignment.groupby(
            ["representation_id", "candidate_id"],
            sort=True,
        )
    ):
        eligible = group.loc[group["eligible"]]
        reference_trade_count = int(
            group["reference_trade_flag"].sum()
        )
        transfer_trade_count = int(
            group["transfer_trade_flag"].sum()
        )
        agreement = _ratio(
            float(
                eligible[
                    "trade_indicator_and_direction_match"
                ].sum()
            ),
            float(len(eligible)),
        )
        reference_keys = {
            (str(row.session_date), str(row.reference_direction))
            for row in group.itertuples(index=False)
            if bool(row.reference_trade_flag)
        }
        transfer_keys = {
            (str(row.session_date), str(row.transfer_direction))
            for row in group.itertuples(index=False)
            if bool(row.transfer_trade_flag)
        }
        union = reference_keys | transfer_keys
        intersection = reference_keys & transfer_keys
        common = group.loc[group["common_trade"]]
        correlation = safe_correlation(
            common["reference_gross_pnl_usd"],
            common["transfer_gross_pnl_usd"],
        )
        sign_agreement = _ratio(
            float(common["gross_pnl_sign_match"].sum()),
            float(len(common)),
        )
        entry_agreement = _ratio(
            float(common["entry_timestamp_match"].sum()),
            float(len(common)),
        )
        transfer_pnl = group.loc[
            group["transfer_trade_flag"],
            "transfer_net_pnl_usd",
        ].to_numpy(dtype=float)
        eligibility_share = _ratio(
            float(len(eligible)),
            float(len(group)),
        )
        count_difference = _ratio(
            float(abs(transfer_trade_count - reference_trade_count)),
            float(reference_trade_count),
        )
        match_share = _ratio(
            float(len(intersection)),
            float(len(union)),
        )
        gates = {
            "gate_session_eligibility": eligibility_share >= 0.99,
            "gate_trade_indicator_and_direction": agreement >= 0.99,
            "gate_trade_count": count_difference <= 0.01,
            "gate_common_trade_match": match_share >= 0.98,
            "gate_entry_timestamp": entry_agreement >= 1.0,
            "gate_gross_pnl_correlation": (
                np.isfinite(correlation) and correlation >= 0.98
            ),
            "gate_gross_pnl_sign": sign_agreement >= 0.95,
        }
        rows.append(
            {
                "representation_id": representation_id,
                "candidate_id": candidate_id,
                "reference_session_count": int(len(group)),
                "eligible_session_count": int(len(eligible)),
                "eligible_session_share": eligibility_share,
                "trade_indicator_and_direction_agreement": agreement,
                "reference_trade_count": reference_trade_count,
                "transfer_trade_count": transfer_trade_count,
                "trade_count_relative_difference": count_difference,
                "common_trade_count": int(len(common)),
                "common_trade_match_share": match_share,
                "matching_entry_timestamp_agreement": entry_agreement,
                "common_trade_gross_pnl_correlation": correlation,
                "common_trade_gross_pnl_sign_agreement": sign_agreement,
                "transfer_profit_factor": profit_factor(transfer_pnl),
                "transfer_net_profit_usd": float(transfer_pnl.sum()),
                "transfer_maximum_drawdown_usd": maximum_drawdown(
                    transfer_pnl
                ),
                **gates,
                "all_transfer_gates_pass": all(gates.values()),
            }
        )
    return pd.DataFrame(rows, columns=TRANSFER_METRIC_FIELDS)


def representation_sensitivity(
    trade_alignment: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for candidate_id in FINALIST_IDS:
        local = trade_alignment.loc[
            trade_alignment["candidate_id"] == candidate_id
        ]
        left = local.loc[
            local["representation_id"] == "BACKWARD_ADJUSTED"
        ].set_index("session_date")
        right = local.loc[
            local["representation_id"] == "UNADJUSTED"
        ].set_index("session_date")
        common_dates = left.index.intersection(right.index)
        left = left.loc[common_dates]
        right = right.loc[common_dates]
        common_eligible = left["eligible"] & right["eligible"]
        decision_match = (
            (
                left["transfer_trade_flag"]
                == right["transfer_trade_flag"]
            )
            & (
                ~left["transfer_trade_flag"]
                | (
                    left["transfer_direction"]
                    == right["transfer_direction"]
                )
            )
        )
        left_keys = {
            (str(index), str(row["transfer_direction"]))
            for index, row in left.iterrows()
            if bool(row["transfer_trade_flag"])
        }
        right_keys = {
            (str(index), str(row["transfer_direction"]))
            for index, row in right.iterrows()
            if bool(row["transfer_trade_flag"])
        }
        common_keys = left_keys & right_keys
        union_keys = left_keys | right_keys
        common_rows = [
            (
                left.loc[session_date],
                right.loc[session_date],
            )
            for session_date, direction in sorted(common_keys)
            if (
                str(left.loc[session_date, "transfer_direction"])
                == direction
                and str(right.loc[session_date, "transfer_direction"])
                == direction
            )
        ]
        left_pnl = [
            float(item[0]["transfer_gross_pnl_usd"])
            for item in common_rows
        ]
        right_pnl = [
            float(item[1]["transfer_gross_pnl_usd"])
            for item in common_rows
        ]
        entry_matches = [
            (
                str(item[0]["transfer_entry_timestamp_utc"])
                == str(item[1]["transfer_entry_timestamp_utc"])
            )
            for item in common_rows
        ]
        sign_matches = [
            np.sign(left_value) == np.sign(right_value)
            for left_value, right_value in zip(left_pnl, right_pnl)
        ]
        rows.append(
            {
                "candidate_id": candidate_id,
                "common_eligible_session_count": int(
                    common_eligible.sum()
                ),
                "trade_indicator_and_direction_agreement": _ratio(
                    float(decision_match.loc[common_eligible].sum()),
                    float(common_eligible.sum()),
                ),
                "backward_adjusted_trade_count": int(
                    left["transfer_trade_flag"].sum()
                ),
                "unadjusted_trade_count": int(
                    right["transfer_trade_flag"].sum()
                ),
                "common_trade_count": int(len(common_keys)),
                "common_trade_match_share": _ratio(
                    float(len(common_keys)),
                    float(len(union_keys)),
                ),
                "matching_entry_timestamp_agreement": _ratio(
                    float(sum(entry_matches)),
                    float(len(entry_matches)),
                ),
                "common_trade_gross_pnl_correlation": safe_correlation(
                    left_pnl,
                    right_pnl,
                ),
                "common_trade_gross_pnl_sign_agreement": _ratio(
                    float(sum(sign_matches)),
                    float(len(sign_matches)),
                ),
            }
        )
    return pd.DataFrame(
        rows,
        columns=REPRESENTATION_SENSITIVITY_FIELDS,
    )


def period_comparison(
    trade_alignment: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for candidate_id in FINALIST_IDS:
        candidate = trade_alignment.loc[
            trade_alignment["candidate_id"] == candidate_id
        ]
        reference = candidate.loc[
            candidate["representation_id"] == "BACKWARD_ADJUSTED",
            [
                "session_date",
                "reference_trade_flag",
                "reference_net_pnl_usd",
            ],
        ].drop_duplicates("session_date")
        series = [
            (
                "REFERENCE_EXP014",
                reference.loc[reference["reference_trade_flag"]].rename(
                    columns={
                        "reference_net_pnl_usd": "net_pnl_usd"
                    }
                ),
            )
        ]
        for representation_id in REPRESENTATION_IDS:
            current = candidate.loc[
                (candidate["representation_id"] == representation_id)
                & candidate["transfer_trade_flag"],
                ["session_date", "transfer_net_pnl_usd"],
            ].rename(
                columns={
                    "transfer_net_pnl_usd": "net_pnl_usd"
                }
            )
            series.append((representation_id, current))
        for series_id, frame in series:
            local = frame.copy()
            if local.empty:
                continue
            timestamp = pd.to_datetime(local["session_date"])
            for period_type, labels in (
                ("YEAR", timestamp.dt.strftime("%Y")),
                ("MONTH", timestamp.dt.strftime("%Y-%m")),
            ):
                local["period"] = labels.to_numpy()
                for period, group in local.groupby("period", sort=True):
                    values = group["net_pnl_usd"].to_numpy(dtype=float)
                    rows.append(
                        {
                            "candidate_id": candidate_id,
                            "series_id": series_id,
                            "period_type": period_type,
                            "period": str(period),
                            "completed_trades": int(len(values)),
                            "net_profit_usd": float(values.sum()),
                            "profit_factor": profit_factor(values),
                        }
                    )
    return pd.DataFrame(rows).sort_values(
        ["candidate_id", "period_type", "period", "series_id"],
        kind="stable",
    ).reset_index(drop=True)


def roll_proximity_differences(
    trade_alignment: pd.DataFrame,
    *,
    reference_session_dates: Iterable[str],
    roll_session_dates: Iterable[str],
) -> pd.DataFrame:
    dates = validate_reference_session_dates(reference_session_dates)
    positions = {
        session_date: index
        for index, session_date in enumerate(dates)
    }
    roll_positions = sorted(
        {
            positions[str(value)]
            for value in roll_session_dates
            if str(value) in positions
        }
    )
    rows: list[dict[str, Any]] = []
    for row in trade_alignment.loc[
        trade_alignment["common_trade"]
    ].itertuples(index=False):
        position = positions[str(row.session_date)]
        distance = (
            min(abs(position - item) for item in roll_positions)
            if roll_positions
            else -1
        )
        band = (
            "0"
            if distance == 0
            else "1"
            if distance == 1
            else "2-3"
            if 2 <= distance <= 3
            else "OTHER"
        )
        rows.append(
            {
                "representation_id": row.representation_id,
                "candidate_id": row.candidate_id,
                "session_date": row.session_date,
                "distance_to_nearest_roll_session": distance,
                "roll_distance_band": band,
                "gross_pnl_difference_usd": float(
                    row.transfer_gross_pnl_usd
                    - row.reference_gross_pnl_usd
                ),
                "absolute_gross_pnl_difference_usd": float(
                    abs(
                        row.transfer_gross_pnl_usd
                        - row.reference_gross_pnl_usd
                    )
                ),
            }
        )
    return pd.DataFrame(rows)


def final_classification(
    metrics: pd.DataFrame,
    hard_checks: Mapping[str, bool],
) -> str:
    if len(hard_checks) != 20 or not all(hard_checks.values()):
        return "TRANSFER_DIAGNOSTIC_NOT_QUALIFIED"
    primary = metrics.loc[
        metrics["representation_id"] == "BACKWARD_ADJUSTED"
    ]
    if (
        len(primary) == len(FINALIST_IDS)
        and bool(primary["all_transfer_gates_pass"].all())
    ):
        return "QUALIFIED_FOR_SEPARATE_FIXED_RULE_HISTORY_VALIDATION"
    return "TRANSFER_DIAGNOSTIC_COMPLETE_WITH_MATERIAL_DIFFERENCES"
