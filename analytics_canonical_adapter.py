from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from analytics_evidence_registry import (
    AnalyticsSeriesSpec,
    BenchmarkSchema,
    EquitySchema,
    TradeSchema,
)


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
    "period_end",
    "net_pnl_usd",
    "cumulative_net_pnl_usd",
    "equity_usd",
    "drawdown_usd",
    "drawdown_percent",
    "had_trade",
)

CANONICAL_BENCHMARK_COLUMNS = (
    "series_id",
    "period_end",
    "benchmark_equity_usd",
    "benchmark_return",
    "benchmark_drawdown_percent",
)


class AnalyticsEvidenceUnavailable(ValueError):
    pass


def _numeric(
    frame: pd.DataFrame,
    column: str,
    *,
    default: float = np.nan,
) -> pd.Series:
    if column not in frame:
        return pd.Series(default, index=frame.index, dtype=float)
    return pd.to_numeric(frame[column], errors="coerce")


def _text(
    frame: pd.DataFrame,
    column: str,
    *,
    default: str = "",
) -> pd.Series:
    if column not in frame:
        return pd.Series(default, index=frame.index, dtype=object)
    return frame[column].fillna(default).astype(str)


def _normalize_direction(series: pd.Series) -> pd.Series:
    def normalize(value: object) -> str:
        text = str(value).strip().lower()
        if text in {"1", "1.0", "long", "buy"}:
            return "long"
        if text in {"-1", "-1.0", "short", "sell"}:
            return "short"
        raise ValueError(f"Unsupported trade direction: {value!r}.")

    return series.map(normalize)


def _repair_timestamp_series(series: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(series, errors="coerce", utc=True)
    if parsed.notna().sum() == 0:
        return parsed
    median_year = int(parsed.dropna().dt.year.median())
    if median_year >= 2000:
        return parsed
    repaired: list[pd.Timestamp | pd.NaT] = []
    for value in parsed:
        if pd.isna(value):
            repaired.append(pd.NaT)
        else:
            repaired.append(
                pd.Timestamp(int(value.value) * 1000, tz="UTC")
            )
    return pd.Series(repaired, index=series.index)


def _time_only_timestamps(
    session_dates: pd.Series,
    clock_values: pd.Series,
    timezone: str,
) -> pd.Series:
    combined = (
        session_dates.astype(str).str.slice(0, 10)
        + " "
        + clock_values.astype(str)
    )
    local = pd.to_datetime(combined, errors="coerce")
    return local.dt.tz_localize(
        timezone,
        nonexistent="shift_forward",
        ambiguous="NaT",
    ).dt.tz_convert("UTC")


def _slot_timestamps(
    session_dates: pd.Series,
    slots: pd.Series,
    timezone: str,
) -> pd.Series:
    local_midnight = pd.to_datetime(
        session_dates,
        errors="coerce",
    ).dt.tz_localize(
        timezone,
        nonexistent="shift_forward",
        ambiguous="NaT",
    )
    return (
        local_midnight
        + pd.Timedelta(hours=9, minutes=30)
        + pd.to_timedelta(slots, unit="m")
    ).dt.tz_convert("UTC")


def _trade_timestamps(
    frame: pd.DataFrame,
    spec: AnalyticsSeriesSpec,
) -> tuple[pd.Series, pd.Series]:
    session_dates = _text(frame, "session_date")
    if (
        spec.trade_schema == TradeSchema.FUTURES_ENRICHED
        and "entry_time" in frame
        and frame["entry_time"].astype(str).str.fullmatch(
            r"\d{1,2}:\d{2}(:\d{2})?"
        ).all()
    ):
        return (
            _time_only_timestamps(
                session_dates,
                frame["entry_time"],
                spec.timezone,
            ),
            _time_only_timestamps(
                session_dates,
                frame["exit_time"],
                spec.timezone,
            ),
        )
    if (
        "entry_minute_slot" in frame
        and "exit_minute_slot" in frame
    ):
        return (
            _slot_timestamps(
                session_dates,
                _numeric(frame, "entry_minute_slot"),
                spec.timezone,
            ),
            _slot_timestamps(
                session_dates,
                _numeric(frame, "exit_minute_slot"),
                spec.timezone,
            ),
        )
    if "entry_time" in frame and "exit_time" in frame:
        return (
            _repair_timestamp_series(frame["entry_time"]),
            _repair_timestamp_series(frame["exit_time"]),
        )
    empty = pd.Series(pd.NaT, index=frame.index, dtype="datetime64[ns, UTC]")
    return empty.copy(), empty.copy()


def _holding_minutes(
    frame: pd.DataFrame,
    spec: AnalyticsSeriesSpec,
    entry_time: pd.Series,
    exit_time: pd.Series,
) -> pd.Series:
    if "holding_minutes" in frame:
        return _numeric(frame, "holding_minutes")
    if "minutes_held" in frame:
        return _numeric(frame, "minutes_held")
    if "hours_held" in frame:
        return _numeric(frame, "hours_held") * 60.0
    if "bars_held" in frame:
        bar_minutes = (
            60.0
            if spec.trade_schema == TradeSchema.BTC_HOURLY
            else 5.0
        )
        return _numeric(frame, "bars_held") * bar_minutes
    return (exit_time - entry_time).dt.total_seconds() / 60.0


def _trade_cash_values(
    frame: pd.DataFrame,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    if "net_pnl_usd" in frame:
        net = _numeric(frame, "net_pnl_usd")
    elif "pnl_cash" in frame:
        net = _numeric(frame, "pnl_cash")
    elif {
        "equity_before",
        "net_return_percent",
    }.issubset(frame.columns):
        net = (
            _numeric(frame, "equity_before")
            * _numeric(frame, "net_return_percent")
            / 100.0
        )
    else:
        raise ValueError("Trade ledger has no supported net P&L field.")

    if "gross_pnl_usd" in frame:
        gross = _numeric(frame, "gross_pnl_usd")
    elif {
        "equity_before",
        "gross_return_percent",
    }.issubset(frame.columns):
        gross = (
            _numeric(frame, "equity_before")
            * _numeric(frame, "gross_return_percent")
            / 100.0
        )
    else:
        gross = net.copy()

    if "transaction_cost_usd" in frame:
        costs = _numeric(frame, "transaction_cost_usd")
    else:
        costs = gross - net
    return gross, costs, net


def canonicalize_trades(
    frame: pd.DataFrame,
    spec: AnalyticsSeriesSpec,
) -> pd.DataFrame:
    working = frame.copy().reset_index(drop=True)
    entry_time, exit_time = _trade_timestamps(working, spec)
    holding = _holding_minutes(
        working,
        spec,
        entry_time,
        exit_time,
    )
    gross, costs, net = _trade_cash_values(working)

    direction_source = (
        working["side"]
        if "side" in working
        else working["direction"]
    )
    direction = _normalize_direction(direction_source)
    if "session_date" in working:
        session_date = pd.to_datetime(
            working["session_date"],
            errors="coerce",
        ).dt.normalize()
    else:
        session_date = entry_time.dt.tz_convert("UTC").dt.tz_localize(
            None
        ).dt.normalize()

    trade_ids = (
        _numeric(working, "trade_id")
        if "trade_id" in working
        else pd.Series(
            np.arange(1, len(working) + 1),
            index=working.index,
            dtype=float,
        )
    )
    result = pd.DataFrame(
        {
            "series_id": spec.series_id,
            "experiment_id": spec.experiment_id,
            "candidate_id": spec.candidate_id or "",
            "family_id": spec.family_id or "",
            "market": spec.market,
            "trade_id": trade_ids.astype("Int64"),
            "session_date": session_date,
            "direction": direction,
            "entry_time": entry_time,
            "exit_time": exit_time,
            "holding_minutes": holding,
            "entry_price": _numeric(working, "entry_price"),
            "exit_price": _numeric(working, "exit_price"),
            "gross_pnl_usd": gross,
            "transaction_cost_usd": costs,
            "net_pnl_usd": net,
            "risk_points": _numeric(working, "risk_points"),
            "initial_risk_usd": _numeric(
                working,
                "initial_risk_usd",
            ),
            "contracts": _numeric(working, "contracts", default=1.0),
            "exit_reason": _text(working, "exit_reason"),
            "mae_usd": _numeric(
                working,
                "pre_exit_mae_usd",
            ),
            "mfe_usd": _numeric(
                working,
                "pre_exit_mfe_usd",
            ),
            "captured_fraction_of_mfe": _numeric(
                working,
                "captured_fraction_of_mfe",
            ),
            "source_row_number": np.arange(
                1,
                len(working) + 1,
            ),
        }
    )
    if result["net_pnl_usd"].isna().any():
        raise ValueError("Canonical trade P&L contains missing values.")
    if (result["holding_minutes"].dropna() < 0).any():
        raise ValueError("Canonical holding time cannot be negative.")
    if not spec.supports_mae_mfe and (
        result["mae_usd"].notna().any()
        or result["mfe_usd"].notna().any()
    ):
        raise ValueError(
            "MAE/MFE appeared for a series that does not support it."
        )
    return result.loc[:, CANONICAL_TRADE_COLUMNS]


def load_canonical_trades(
    project_dir: Path,
    spec: AnalyticsSeriesSpec,
) -> pd.DataFrame:
    return canonicalize_trades(
        pd.read_csv(project_dir / spec.trades_path),
        spec,
    )


def _period_end(frame: pd.DataFrame) -> pd.Series:
    if "timestamp" in frame:
        return pd.to_datetime(
            frame["timestamp"],
            errors="coerce",
            utc=True,
        )
    if "session_date" in frame:
        return pd.to_datetime(
            frame["session_date"],
            errors="coerce",
            utc=True,
        )
    raise ValueError("Equity evidence has no date field.")


def canonicalize_equity(
    frame: pd.DataFrame,
    spec: AnalyticsSeriesSpec,
) -> pd.DataFrame:
    working = frame.copy().reset_index(drop=True)
    period_end = _period_end(working)

    if spec.equity_schema == EquitySchema.SESSION_PNL_MATRIX:
        if not spec.equity_value_column:
            raise ValueError(
                "Session P&L matrix requires equity_value_column."
            )
        pnl = _numeric(working, spec.equity_value_column)
        equity = spec.reference_capital_usd + pnl.cumsum()
    elif "equity_usd" in working:
        equity = _numeric(working, "equity_usd")
        pnl = equity.diff()
        if len(pnl):
            pnl.iloc[0] = (
                equity.iloc[0] - spec.reference_capital_usd
            )
    elif "equity" in working:
        equity = _numeric(working, "equity")
        pnl = equity.diff()
        if len(pnl):
            pnl.iloc[0] = (
                equity.iloc[0] - spec.reference_capital_usd
            )
    else:
        cumulative_name = next(
            (
                column
                for column in (
                    "cumulative_net_pnl_usd",
                    "cumulative_net_profit_usd",
                )
                if column in working
            ),
            None,
        )
        if cumulative_name is None:
            raise ValueError(
                "Equity evidence has no supported equity or "
                "cumulative P&L field."
            )
        cumulative = _numeric(working, cumulative_name)
        equity = spec.reference_capital_usd + cumulative
        pnl = cumulative.diff()
        if len(pnl):
            pnl.iloc[0] = cumulative.iloc[0]

    cumulative_pnl = equity - spec.reference_capital_usd
    peak = equity.cummax()
    drawdown_usd = equity - peak
    drawdown_percent = np.where(
        peak != 0,
        drawdown_usd / peak * 100.0,
        np.nan,
    )
    if "had_trade" in working:
        had_trade = (
            working["had_trade"]
            .astype(str)
            .str.lower()
            .map({"true": True, "false": False})
            .fillna(False)
        )
    else:
        had_trade = pnl.fillna(0.0).ne(0.0)

    result = pd.DataFrame(
        {
            "series_id": spec.series_id,
            "experiment_id": spec.experiment_id,
            "market": spec.market,
            "period_end": period_end,
            "net_pnl_usd": pnl,
            "cumulative_net_pnl_usd": cumulative_pnl,
            "equity_usd": equity,
            "drawdown_usd": drawdown_usd,
            "drawdown_percent": drawdown_percent,
            "had_trade": had_trade.astype(bool),
        }
    )
    result = result.sort_values("period_end").reset_index(drop=True)
    if result["period_end"].isna().any():
        raise ValueError("Canonical equity contains invalid dates.")
    if result["equity_usd"].isna().any():
        raise ValueError("Canonical equity contains missing values.")
    return result.loc[:, CANONICAL_EQUITY_COLUMNS]


def load_canonical_equity(
    project_dir: Path,
    spec: AnalyticsSeriesSpec,
) -> pd.DataFrame:
    result = canonicalize_equity(
        pd.read_csv(project_dir / spec.equity_path),
        spec,
    )
    if not spec.dense_session_equity:
        return result

    benchmark = load_canonical_benchmark(
        project_dir,
        spec,
    )
    session_index = benchmark["period_end"].drop_duplicates()
    dense = (
        result.set_index("period_end")
        .reindex(session_index)
        .rename_axis("period_end")
        .reset_index()
    )
    dense["series_id"] = spec.series_id
    dense["experiment_id"] = spec.experiment_id
    dense["market"] = spec.market
    dense["equity_usd"] = dense["equity_usd"].ffill().fillna(
        spec.reference_capital_usd
    )
    dense["net_pnl_usd"] = (
        dense["equity_usd"].diff().fillna(
            dense["equity_usd"] - spec.reference_capital_usd
        )
    )
    dense["cumulative_net_pnl_usd"] = (
        dense["equity_usd"] - spec.reference_capital_usd
    )
    peak = dense["equity_usd"].cummax()
    dense["drawdown_usd"] = dense["equity_usd"] - peak
    dense["drawdown_percent"] = np.where(
        peak != 0,
        dense["drawdown_usd"] / peak * 100.0,
        np.nan,
    )
    dense["had_trade"] = dense["net_pnl_usd"].ne(0.0)
    return dense.loc[:, CANONICAL_EQUITY_COLUMNS]


def _normalized_benchmark(
    period_end: pd.Series,
    values: pd.Series,
    reference_capital_usd: float,
) -> pd.DataFrame:
    working = pd.DataFrame(
        {
            "period_end": pd.to_datetime(
                period_end,
                errors="coerce",
                utc=True,
            ),
            "value": pd.to_numeric(values, errors="coerce"),
        }
    ).dropna()
    working = (
        working.sort_values("period_end")
        .drop_duplicates("period_end", keep="last")
        .reset_index(drop=True)
    )
    if working.empty or float(working["value"].iloc[0]) == 0.0:
        raise ValueError("Benchmark evidence cannot be normalized.")
    equity = (
        working["value"]
        / float(working["value"].iloc[0])
        * reference_capital_usd
    )
    returns = equity.pct_change().fillna(0.0)
    peak = equity.cummax()
    return pd.DataFrame(
        {
            "period_end": working["period_end"],
            "benchmark_equity_usd": equity,
            "benchmark_return": returns,
            "benchmark_drawdown_percent": (
                (equity / peak - 1.0) * 100.0
            ),
        }
    )


def _market_parquet_benchmark(
    project_dir: Path,
    paths: Iterable[Path],
    reference_capital_usd: float,
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for path in paths:
        market = pd.read_parquet(project_dir / path)
        if "session_date" not in market or "close" not in market:
            raise ValueError(
                f"Market benchmark source lacks required columns: {path}."
            )
        frames.append(
            market.loc[:, ["session_date", "close"]].reset_index(
                drop=True
            )
        )
    combined = pd.concat(frames, ignore_index=True)
    session_close = (
        combined.assign(
            session_date=pd.to_datetime(
                combined["session_date"],
                errors="coerce",
                utc=True,
            )
        )
        .dropna(subset=["session_date", "close"])
        .groupby("session_date", as_index=False)["close"]
        .last()
    )
    return _normalized_benchmark(
        session_close["session_date"],
        session_close["close"],
        reference_capital_usd,
    )


def load_canonical_benchmark(
    project_dir: Path,
    spec: AnalyticsSeriesSpec,
    *,
    clip_to_analysis_period: bool = True,
) -> pd.DataFrame:
    if spec.benchmark_schema == BenchmarkSchema.NONE:
        raise AnalyticsEvidenceUnavailable(
            "Benchmark is not available from this experiment’s "
            "frozen evidence."
        )
    if spec.benchmark_schema == BenchmarkSchema.INLINE_CLOSE:
        frame = pd.read_csv(project_dir / spec.benchmark_paths[0])
        benchmark = _normalized_benchmark(
            frame["timestamp"],
            frame["close"],
            spec.reference_capital_usd,
        )
    elif spec.benchmark_schema == (
        BenchmarkSchema.NORMALIZED_COMPARISON
    ):
        frame = pd.read_csv(project_dir / spec.benchmark_paths[0])
        if not spec.benchmark_column:
            raise ValueError(
                "Normalized comparison requires benchmark_column."
            )
        benchmark = _normalized_benchmark(
            frame["session_date"],
            frame[spec.benchmark_column],
            spec.reference_capital_usd,
        )
    elif spec.benchmark_schema == BenchmarkSchema.MARKET_PARQUET:
        benchmark = _market_parquet_benchmark(
            project_dir,
            spec.benchmark_paths,
            spec.reference_capital_usd,
        )
    else:
        raise ValueError(
            f"Unsupported benchmark schema: {spec.benchmark_schema}."
        )

    if clip_to_analysis_period:
        if spec.analysis_start:
            start = pd.Timestamp(spec.analysis_start, tz="UTC")
            benchmark = benchmark.loc[
                benchmark["period_end"] >= start
            ]
        if spec.analysis_end:
            end = (
                pd.Timestamp(spec.analysis_end, tz="UTC")
                + pd.Timedelta(days=1)
                - pd.Timedelta(nanoseconds=1)
            )
            benchmark = benchmark.loc[
                benchmark["period_end"] <= end
            ]
        benchmark = benchmark.reset_index(drop=True)
        if not benchmark.empty:
            benchmark = _normalized_benchmark(
                benchmark["period_end"],
                benchmark["benchmark_equity_usd"],
                spec.reference_capital_usd,
            )
    benchmark = benchmark.reset_index(drop=True)
    benchmark.insert(0, "series_id", spec.series_id)
    return benchmark.loc[:, CANONICAL_BENCHMARK_COLUMNS]
