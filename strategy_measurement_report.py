from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
import html
import json
import math
import shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from report_chart_style import save_report_figure
from strategy_explanations import (
    STRATEGY_EXPLANATION_CSS,
    strategy_explanation_html,
)


REPORT_VERSION = "strategy_measurement_report_v2"
REFERENCE_CAPITAL = {"NQ": 100_000.0, "MNQ": 10_000.0}


@dataclass(frozen=True)
class MeasurementSpec:
    experiment_id: str
    title: str
    subtitle: str
    result_directory: Path
    decision_file: Path
    nq_trades_file: Path
    mnq_trades_file: Path
    nq_equity_file: Path
    mnq_equity_file: Path
    yearly_file: Path | None = None
    cost_file: Path | None = None
    mcpt_file: Path | None = None
    walk_forward_file: Path | None = None
    grid_file: Path | None = None
    bootstrap_file: Path | None = None
    review_file: Path | None = None


def measurement_specs(project_dir: Path) -> tuple[MeasurementSpec, ...]:
    project_dir = Path(project_dir)
    return (
        MeasurementSpec(
            experiment_id="EXP-005",
            title="Fixed 15-Minute NQ/MNQ Opening Range Breakout",
            subtitle="Protected 2023–2025 confirmation validation",
            result_directory=project_dir / "results" / "EXP-005" / "full_validation",
            decision_file=project_dir / "results" / "EXP-005" / "full_validation" / "full_validation_decision.json",
            nq_trades_file=project_dir / "results" / "EXP-005" / "full_validation" / "nq_trades.csv",
            mnq_trades_file=project_dir / "results" / "EXP-005" / "full_validation" / "mnq_trades.csv",
            nq_equity_file=project_dir / "results" / "EXP-005" / "full_validation" / "nq_equity_curve.csv",
            mnq_equity_file=project_dir / "results" / "EXP-005" / "full_validation" / "mnq_equity_curve.csv",
            yearly_file=project_dir / "results" / "EXP-005" / "full_validation" / "yearly_results.csv",
            cost_file=project_dir / "results" / "EXP-005" / "full_validation" / "cost_sensitivity.csv",
            mcpt_file=project_dir / "results" / "EXP-005" / "full_validation" / "nq_mcpt_1000.csv",
            review_file=project_dir / "results" / "EXP-005" / "review" / "review_decision.json",
        ),
        MeasurementSpec(
            experiment_id="EXP-006",
            title="Structured NQ/MNQ ORB Entry-Window Optimization",
            subtitle="Twenty-seven opening-range, entry-time and direction combinations",
            result_directory=project_dir / "results" / "EXP-006" / "optimization",
            decision_file=project_dir / "results" / "EXP-006" / "optimization" / "optimization_decision.json",
            nq_trades_file=project_dir / "results" / "EXP-006" / "optimization" / "selected_nq_trades.csv",
            mnq_trades_file=project_dir / "results" / "EXP-006" / "optimization" / "selected_mnq_trades.csv",
            nq_equity_file=project_dir / "results" / "EXP-006" / "optimization" / "selected_nq_equity.csv",
            mnq_equity_file=project_dir / "results" / "EXP-006" / "optimization" / "selected_mnq_equity.csv",
            yearly_file=project_dir / "results" / "EXP-006" / "optimization" / "selected_nq_yearly.csv",
            cost_file=project_dir / "results" / "EXP-006" / "optimization" / "selected_cost_sensitivity.csv",
            mcpt_file=project_dir / "results" / "EXP-006" / "optimization" / "selection_mcpt.csv",
            walk_forward_file=project_dir / "results" / "EXP-006" / "optimization" / "walk_forward_folds.csv",
            grid_file=project_dir / "results" / "EXP-006" / "optimization" / "candidate_grid.csv",
        ),
        MeasurementSpec(
            experiment_id="EXP-007",
            title="Fixed 30-Minute Long-Only 1R ORB",
            subtitle="One fixed geometry with a 14:00 New York forced exit",
            result_directory=project_dir / "results" / "EXP-007" / "fixed_replication",
            decision_file=project_dir / "results" / "EXP-007" / "fixed_replication" / "replication_decision.json",
            nq_trades_file=project_dir / "results" / "EXP-007" / "fixed_replication" / "nq_trades.csv",
            mnq_trades_file=project_dir / "results" / "EXP-007" / "fixed_replication" / "mnq_trades.csv",
            nq_equity_file=project_dir / "results" / "EXP-007" / "fixed_replication" / "nq_equity_curve.csv",
            mnq_equity_file=project_dir / "results" / "EXP-007" / "fixed_replication" / "mnq_equity_curve.csv",
            yearly_file=project_dir / "results" / "EXP-007" / "fixed_replication" / "yearly_results.csv",
            cost_file=project_dir / "results" / "EXP-007" / "fixed_replication" / "cost_sensitivity.csv",
            mcpt_file=project_dir / "results" / "EXP-007" / "fixed_replication" / "mcpt_results.csv",
            bootstrap_file=project_dir / "results" / "EXP-007" / "fixed_replication" / "bootstrap_diagnostics.json",
        ),
        MeasurementSpec(
            experiment_id="EXP-008",
            title="Structured Long-Only ORB Exit-Geometry Optimization",
            subtitle="Twenty-seven opening-range, target and forced-exit combinations",
            result_directory=project_dir / "results" / "EXP-008" / "exit_geometry",
            decision_file=project_dir / "results" / "EXP-008" / "exit_geometry" / "optimization_decision.json",
            nq_trades_file=project_dir / "results" / "EXP-008" / "exit_geometry" / "nq_trades.csv",
            mnq_trades_file=project_dir / "results" / "EXP-008" / "exit_geometry" / "mnq_trades.csv",
            nq_equity_file=project_dir / "results" / "EXP-008" / "exit_geometry" / "nq_equity_curve.csv",
            mnq_equity_file=project_dir / "results" / "EXP-008" / "exit_geometry" / "mnq_equity_curve.csv",
            yearly_file=project_dir / "results" / "EXP-008" / "exit_geometry" / "yearly_results.csv",
            cost_file=project_dir / "results" / "EXP-008" / "exit_geometry" / "cost_sensitivity.csv",
            mcpt_file=project_dir / "results" / "EXP-008" / "exit_geometry" / "mcpt_results.csv",
            walk_forward_file=project_dir / "results" / "EXP-008" / "exit_geometry" / "anchored_walk_forward.csv",
            grid_file=project_dir / "results" / "EXP-008" / "exit_geometry" / "complete_candidate_grid.csv",
            bootstrap_file=project_dir / "results" / "EXP-008" / "exit_geometry" / "bootstrap_diagnostics.json",
        ),
    )


def _read_json(path: Path | None) -> dict[str, Any]:
    if path is None or not Path(path).exists():
        return {}
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def _read_csv(path: Path | None) -> pd.DataFrame:
    if path is None or not Path(path).exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def validate_measurement_inputs(spec: MeasurementSpec) -> None:
    required = (
        spec.decision_file,
        spec.nq_trades_file,
        spec.mnq_trades_file,
        spec.nq_equity_file,
        spec.mnq_equity_file,
    )
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing measurement inputs: " + ", ".join(missing))


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    return value


def _safe_float(value: Any, default: float = float("nan")) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def _money(value: Any) -> str:
    number = _safe_float(value)
    if not math.isfinite(number):
        return "—"
    sign = "−" if number < 0 else ""
    return f"{sign}${abs(number):,.2f}"


def _number(value: Any, digits: int = 3) -> str:
    number = _safe_float(value)
    if not math.isfinite(number):
        return "—"
    return f"{number:,.{digits}f}"


def _percent(value: Any, digits: int = 2) -> str:
    number = _safe_float(value)
    if not math.isfinite(number):
        return "—"
    return f"{number:,.{digits}f}%"


def _integer(value: Any) -> str:
    number = _safe_float(value)
    if not math.isfinite(number):
        return "—"
    return f"{int(round(number)):,}"


def _display_number(value: Any) -> float:
    if isinstance(value, (int, float, np.integer, np.floating)):
        number = float(value)
        return number if math.isfinite(number) else float("nan")

    text = str(value).strip()
    if not text or text in {"—", "nan", "None"}:
        return float("nan")

    negative_parentheses = text.startswith("(") and text.endswith(")")
    cleaned = (
        text.replace("−", "-")
        .replace("$", "")
        .replace("%", "")
        .replace(",", "")
        .replace("(", "")
        .replace(")", "")
        .replace("minutes", "")
        .replace("minute", "")
        .replace("min", "")
        .replace("sessions", "")
        .replace("session", "")
        .strip()
    )
    try:
        number = float(cleaned)
    except (TypeError, ValueError):
        return float("nan")
    return -abs(number) if negative_parentheses else number


def _cell_tone(
    row_label: Any,
    column_label: Any,
    value: Any,
) -> str:
    row = str(row_label).strip().lower().replace("_", " ")
    column = str(column_label).strip().lower().replace("_", " ")
    context = f"{row} {column}".strip()
    text = str(value).strip().lower()

    # Green is reserved for status words. Positive numeric values remain
    # in the normal text colour. Red still marks adverse numeric values,
    # failures and rejections.
    if text in {"pass", "passed", "true", "accepted"}:
        return "value-positive"
    if text in {"fail", "failed", "false"}:
        return "value-negative"
    if "accept" in text or text.startswith("lock_"):
        return "value-positive"
    if "reject" in text:
        return "value-negative"

    number = _display_number(value)
    if not math.isfinite(number):
        return ""

    if "p value" in context or "p-value" in context:
        return "value-negative" if number > 0.05 else ""

    if "profit factor" in context:
        return "value-negative" if number <= 1.0 else ""

    result_contexts = (
        "net profit",
        "gross profit",
        "average trade",
        "median trade",
        "average winner",
        "largest winner",
        "payoff ratio",
        "net profit / drawdown",
        "average trade / average cost",
        "average trade / costs",
        "strategy return",
        "benchmark return",
        "excess return",
        "combined test net profit",
    )
    if any(name in context for name in result_contexts):
        return "value-negative" if number < 0 else ""

    adverse_contexts = (
        "gross loss",
        "average loser",
        "largest loser",
        "maximum drawdown",
        "max drawdown",
        "total costs",
    )
    if any(name in context for name in adverse_contexts) and number != 0:
        return "value-negative"

    return ""

def _table(frame: pd.DataFrame, *, index: bool = False) -> str:
    if frame.empty:
        return '<p class="note">No saved rows were available for this section.</p>'

    local = frame.copy()
    if index:
        index_name = local.index.name or "Index"
        local = local.reset_index().rename(
            columns={local.reset_index().columns[0]: index_name}
        )

    columns = list(local.columns)
    header = "".join(
        f"<th>{html.escape(str(column))}</th>"
        for column in columns
    )
    body_rows: list[str] = []
    for _, record in local.iterrows():
        row_label = record.iloc[0] if len(record) else ""
        cells: list[str] = []
        for position, column in enumerate(columns):
            value = record[column]
            missing = value is None
            if isinstance(value, (float, np.floating)):
                missing = missing or math.isnan(float(value))
            display = "—" if missing else str(value)
            classes: list[str] = []
            if position == 0:
                classes.append("row-label")
            tone = _cell_tone(row_label, column, value)
            if tone:
                classes.append(tone)
            class_attribute = (
                f' class="{" ".join(classes)}"'
                if classes
                else ""
            )
            cells.append(
                f"<td{class_attribute}>{html.escape(display)}</td>"
            )
        body_rows.append("<tr>" + "".join(cells) + "</tr>")

    return (
        '<table class="data-table"><thead><tr>'
        + header
        + "</tr></thead><tbody>"
        + "".join(body_rows)
        + "</tbody></table>"
    )


def _profit_factor(values: Iterable[float]) -> float:
    array = np.asarray(list(values), dtype=float)
    positive = float(array[array > 0].sum())
    negative = float(-array[array < 0].sum())
    if negative <= 0:
        return float("inf") if positive > 0 else float("nan")
    return positive / negative


def _max_drawdown(values: Iterable[float]) -> float:
    array = np.asarray(list(values), dtype=float)
    if array.size == 0:
        return 0.0
    cumulative = np.cumsum(array)
    peaks = np.maximum.accumulate(np.r_[0.0, cumulative])[1:]
    return float(np.min(cumulative - peaks))


def _max_consecutive_losses(values: Iterable[float]) -> int:
    longest = current = 0
    for value in values:
        if float(value) < 0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def _repair_timestamp_series(series: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(series, errors="coerce", utc=True)
    if parsed.notna().sum() == 0:
        return parsed
    median_year = int(parsed.dropna().dt.year.median())
    if median_year >= 2000:
        return parsed.dt.tz_convert("America/New_York")
    repaired: list[pd.Timestamp | pd.NaT] = []
    for value in parsed:
        if pd.isna(value):
            repaired.append(pd.NaT)
        else:
            repaired.append(pd.Timestamp(int(value.value) * 1000, tz="UTC"))
    return pd.Series(repaired, index=series.index).dt.tz_convert("America/New_York")


def _holding_minutes(trades: pd.DataFrame) -> pd.Series:
    if "minutes_held" in trades:
        return pd.to_numeric(trades["minutes_held"], errors="coerce")
    if "bars_held" in trades:
        return pd.to_numeric(trades["bars_held"], errors="coerce") * 5.0
    if "entry_time" in trades and "exit_time" in trades:
        entry = _repair_timestamp_series(trades["entry_time"])
        exit_ = _repair_timestamp_series(trades["exit_time"])
        return (exit_ - entry).dt.total_seconds() / 60.0
    return pd.Series(np.nan, index=trades.index)


def _segment_metrics(trades: pd.DataFrame) -> dict[str, float]:
    if trades.empty:
        return {
            "completed_trades": 0,
            "net_profit_usd": 0.0,
            "gross_profit_usd": 0.0,
            "gross_loss_usd": 0.0,
            "profit_factor": float("nan"),
            "win_rate_percent": float("nan"),
            "average_trade_usd": float("nan"),
            "median_trade_usd": float("nan"),
            "average_winner_usd": float("nan"),
            "average_loser_usd": float("nan"),
            "payoff_ratio": float("nan"),
            "largest_winner_usd": float("nan"),
            "largest_loser_usd": float("nan"),
            "maximum_drawdown_usd": 0.0,
            "net_profit_to_drawdown": float("nan"),
            "total_costs_usd": 0.0,
            "average_trade_to_cost": float("nan"),
            "max_consecutive_losses": 0,
            "average_holding_minutes": float("nan"),
            "median_holding_minutes": float("nan"),
        }
    pnl = pd.to_numeric(trades["net_pnl_usd"], errors="coerce").fillna(0.0)
    winners = pnl[pnl > 0]
    losers = pnl[pnl < 0]
    gross_profit = float(winners.sum())
    gross_loss = float(-losers.sum())
    net = float(pnl.sum())
    drawdown = _max_drawdown(pnl)
    costs = (
        float(pd.to_numeric(trades["transaction_cost_usd"], errors="coerce").fillna(0.0).sum())
        if "transaction_cost_usd" in trades
        else 0.0
    )
    average_cost = costs / len(pnl) if len(pnl) else float("nan")
    holding = _holding_minutes(trades).dropna()
    return {
        "completed_trades": int(len(pnl)),
        "net_profit_usd": net,
        "gross_profit_usd": gross_profit,
        "gross_loss_usd": gross_loss,
        "profit_factor": gross_profit / gross_loss if gross_loss > 0 else float("inf"),
        "win_rate_percent": float((pnl > 0).mean() * 100.0),
        "average_trade_usd": float(pnl.mean()),
        "median_trade_usd": float(pnl.median()),
        "average_winner_usd": float(winners.mean()) if len(winners) else float("nan"),
        "average_loser_usd": float(losers.mean()) if len(losers) else float("nan"),
        "payoff_ratio": (
            float(winners.mean() / abs(losers.mean()))
            if len(winners) and len(losers) and losers.mean() != 0
            else float("nan")
        ),
        "largest_winner_usd": float(pnl.max()),
        "largest_loser_usd": float(pnl.min()),
        "maximum_drawdown_usd": drawdown,
        "net_profit_to_drawdown": net / abs(drawdown) if drawdown < 0 else float("nan"),
        "total_costs_usd": costs,
        "average_trade_to_cost": (
            float(pnl.mean() / average_cost)
            if average_cost and math.isfinite(average_cost)
            else float("nan")
        ),
        "max_consecutive_losses": _max_consecutive_losses(pnl),
        "average_holding_minutes": float(holding.mean()) if len(holding) else float("nan"),
        "median_holding_minutes": float(holding.median()) if len(holding) else float("nan"),
    }


def performance_table(trades: pd.DataFrame) -> pd.DataFrame:
    direction = trades.get("direction", pd.Series("", index=trades.index)).astype(str).str.lower()
    segments = {
        "All trades": trades,
        "Long trades": trades.loc[direction.eq("long")],
        "Short trades": trades.loc[direction.eq("short")],
    }
    metrics = {name: _segment_metrics(frame) for name, frame in segments.items()}
    rows = [
        ("Completed trades", "completed_trades", _integer),
        ("Net profit", "net_profit_usd", _money),
        ("Gross profit", "gross_profit_usd", _money),
        ("Gross loss", "gross_loss_usd", _money),
        ("Profit Factor", "profit_factor", lambda x: _number(x, 3)),
        ("Win rate", "win_rate_percent", _percent),
        ("Average trade", "average_trade_usd", _money),
        ("Median trade", "median_trade_usd", _money),
        ("Average winner", "average_winner_usd", _money),
        ("Average loser", "average_loser_usd", _money),
        ("Payoff ratio", "payoff_ratio", lambda x: _number(x, 3)),
        ("Largest winner", "largest_winner_usd", _money),
        ("Largest loser", "largest_loser_usd", _money),
        ("Maximum drawdown", "maximum_drawdown_usd", _money),
        ("Net profit / drawdown", "net_profit_to_drawdown", lambda x: _number(x, 3)),
        ("Total costs", "total_costs_usd", _money),
        ("Average trade / average cost", "average_trade_to_cost", lambda x: _number(x, 3)),
        ("Maximum consecutive losses", "max_consecutive_losses", _integer),
        ("Average holding time", "average_holding_minutes", lambda x: f"{_number(x, 1)} min" if math.isfinite(_safe_float(x)) else "—"),
        ("Median holding time", "median_holding_minutes", lambda x: f"{_number(x, 1)} min" if math.isfinite(_safe_float(x)) else "—"),
    ]
    return pd.DataFrame(
        {
            "Metric": [label for label, _, _ in rows],
            **{
                segment: [formatter(metrics[segment][field]) for _, field, formatter in rows]
                for segment in segments
            },
        }
    )


def normalized_benchmark(
    one_minute_data: pd.DataFrame,
    *,
    start_date: str,
    end_date: str,
    reference_capital: float,
) -> pd.DataFrame:
    required = {"session_date", "minute_slot", "close"}
    missing = required - set(one_minute_data.columns)
    if missing:
        raise ValueError(f"Benchmark data is missing columns: {sorted(missing)}")
    local = one_minute_data.loc[:, ["session_date", "minute_slot", "close"]].copy()
    local["session_date"] = pd.to_datetime(local["session_date"]).dt.normalize()
    local = local.loc[
        local["session_date"].between(pd.Timestamp(start_date), pd.Timestamp(end_date))
    ].sort_values(["session_date", "minute_slot"])
    closes = local.groupby("session_date", sort=True)["close"].last().astype(float)
    if len(closes) < 2:
        raise ValueError("Benchmark period must contain at least two session closes.")
    equity = float(reference_capital) * closes / float(closes.iloc[0])
    peak = equity.cummax()
    return pd.DataFrame(
        {
            "session_date": closes.index,
            "benchmark_close": closes.to_numpy(dtype=float),
            "benchmark_equity": equity.to_numpy(dtype=float),
            "benchmark_drawdown_percent": ((equity / peak - 1.0) * 100.0).to_numpy(dtype=float),
        }
    ).reset_index(drop=True)


def comparison_timeseries(
    equity: pd.DataFrame,
    benchmark: pd.DataFrame,
    *,
    reference_capital: float,
) -> pd.DataFrame:
    local = equity.copy()
    local["session_date"] = pd.to_datetime(local["session_date"]).dt.normalize()
    local["strategy_equity"] = float(reference_capital) + pd.to_numeric(
        local["cumulative_net_pnl_usd"], errors="coerce"
    ).fillna(0.0)
    strategy_peak = local["strategy_equity"].cummax()
    local["strategy_drawdown_percent"] = (local["strategy_equity"] / strategy_peak - 1.0) * 100.0
    merged = local.merge(benchmark, on="session_date", how="inner")
    merged["cash_equity"] = float(reference_capital)
    return merged


def _drawdown_episodes(timeseries: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    dates = pd.to_datetime(timeseries["session_date"]).reset_index(drop=True)
    equity = pd.to_numeric(timeseries["strategy_equity"], errors="coerce").reset_index(drop=True)
    peaks = equity.cummax()
    underwater = equity < peaks
    episodes: list[dict[str, Any]] = []
    start: int | None = None
    for i, flag in enumerate(underwater):
        if flag and start is None:
            start = max(0, i - 1)
        if start is not None and (not flag or i == len(underwater) - 1):
            end = i if not flag else i
            window = equity.iloc[start : end + 1]
            trough = int(window.idxmin())
            recovery = dates.iloc[end] if not flag else pd.NaT
            peak_value = float(equity.iloc[start])
            trough_value = float(equity.iloc[trough])
            episodes.append(
                {
                    "Peak date": dates.iloc[start].date().isoformat(),
                    "Trough date": dates.iloc[trough].date().isoformat(),
                    "Recovery date": "Not recovered" if pd.isna(recovery) else recovery.date().isoformat(),
                    "Drawdown": _money(trough_value - peak_value),
                    "Drawdown %": _percent((trough_value / peak_value - 1.0) * 100.0),
                    "Underwater sessions": int(end - start),
                }
            )
            start = None
    frame = pd.DataFrame(episodes)
    if frame.empty:
        return frame, 0
    numeric = frame["Drawdown %"].str.replace("%", "", regex=False).str.replace("−", "-", regex=False).astype(float)
    frame = frame.assign(_sort=numeric).sort_values("_sort").drop(columns="_sort").head(10)
    return frame, int(max(item["Underwater sessions"] for item in episodes))


def _monthly_matrix(trades: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    local = trades.copy()
    local["session_date"] = pd.to_datetime(local["session_date"])
    local["year"] = local["session_date"].dt.year
    local["month"] = local["session_date"].dt.month
    monthly = local.groupby(["year", "month"])["net_pnl_usd"].sum().unstack(fill_value=0.0)
    monthly = monthly.reindex(columns=range(1, 13), fill_value=0.0)
    month_series = local.set_index("session_date")["net_pnl_usd"].resample("ME").sum()
    return monthly, month_series


def _rolling_metrics(trades: pd.DataFrame, window: int = 100) -> pd.DataFrame:
    pnl = pd.to_numeric(trades["net_pnl_usd"], errors="coerce").fillna(0.0).reset_index(drop=True)
    dates = pd.to_datetime(trades["session_date"]).reset_index(drop=True)
    rows: list[dict[str, Any]] = []
    for end in range(window, len(pnl) + 1):
        values = pnl.iloc[end - window : end]
        rows.append(
            {
                "trade_number": end,
                "session_date": dates.iloc[end - 1],
                "rolling_profit_factor": _profit_factor(values),
                "rolling_average_trade_usd": float(values.mean()),
                "rolling_net_profit_usd": float(values.sum()),
            }
        )
    return pd.DataFrame(rows)


def _tail_table(trades: pd.DataFrame) -> pd.DataFrame:
    pnl = pd.to_numeric(trades["net_pnl_usd"], errors="coerce").dropna().sort_values(ascending=False)
    total = float(pnl.sum())
    rows: list[dict[str, Any]] = []
    for share in (0.01, 0.05, 0.10):
        count = max(1, int(math.ceil(len(pnl) * share)))
        contribution = float(pnl.head(count).sum())
        rows.append(
            {
                "Measurement": f"Top {int(share * 100)}% of trades",
                "Trades": count,
                "P&L contribution": _money(contribution),
                "Share of total net profit": _percent(contribution / total * 100.0) if total != 0 else "—",
            }
        )
    for count in (5, 10):
        remaining = float(pnl.iloc[count:].sum()) if len(pnl) > count else 0.0
        rows.append(
            {
                "Measurement": f"Result after removing best {count} trades",
                "Trades": max(0, len(pnl) - count),
                "P&L contribution": _money(remaining),
                "Share of total net profit": _percent(remaining / total * 100.0) if total != 0 else "—",
            }
        )
    return pd.DataFrame(rows)


def _annual_comparison(timeseries: pd.DataFrame) -> pd.DataFrame:
    local = timeseries.copy()
    local["year"] = pd.to_datetime(local["session_date"]).dt.year
    rows = []
    for year, frame in local.groupby("year", sort=True):
        strategy_net = float(frame["session_net_pnl_usd"].sum())
        benchmark_return = (float(frame["benchmark_equity"].iloc[-1]) / float(frame["benchmark_equity"].iloc[0]) - 1.0) * 100.0
        rows.append(
            {
                "Year": int(year),
                "Strategy net profit": strategy_net,
                "Benchmark return %": benchmark_return,
            }
        )
    return pd.DataFrame(rows)


def _decision_context(decision: dict[str, Any]) -> tuple[str, list[str], str]:
    evaluation = decision.get("evaluation", {})
    label = str(evaluation.get("decision", decision.get("stage", "MEASURED")))
    failed = [str(value) for value in evaluation.get("failed_gates", [])]
    if not failed:
        reason = "All locked decision gates passed. This describes the formal research status; the measurements below remain the primary evidence."
    else:
        reason = (
            "The formal status was determined by "
            + ", ".join(name.replace("_", " ") for name in failed)
            + ". Other measured strengths and weaknesses are still shown rather than hidden by the final label."
        )
    return label, failed, reason


def _parameter_description(experiment_id: str, decision: dict[str, Any]) -> str:
    if experiment_id == "EXP-005":
        return "15-minute opening range · long and short · fixed rules · no parameter optimization"
    if experiment_id == "EXP-006":
        selected = decision.get("grid", {}).get("selected_parameters", {})
        return (
            f"{selected.get('opening_range_minutes', '—')}-minute opening range · "
            f"final entry {selected.get('final_entry_time_new_york', '—')} · "
            f"{selected.get('direction_mode', '—')} direction"
        )
    if experiment_id == "EXP-007":
        return "30-minute opening range · long only · 1R target · 14:00 forced exit"
    selected = decision.get("grid", {}).get("selected_parameters", {})
    return (
        f"{selected.get('opening_range_minutes', '—')}-minute opening range · "
        f"{selected.get('reward_to_risk', '—')}R target · "
        f"{selected.get('forced_flat_time_new_york', '—')} forced exit · long only"
    )


def _test_design(experiment_id: str, decision: dict[str, Any]) -> list[tuple[str, str]]:
    data = decision.get("data", {})
    mcpt = decision.get("mcpt", {})
    common = [
        ("Market", "NQ primary measurement with MNQ implementation comparison"),
        ("Execution resolution", "Five-minute signals with one-minute execution and saved post-cost trades"),
        ("Historical sessions", f"{int(data.get('included_sessions', 0)):,}" if data.get("included_sessions") else "Saved result period"),
        ("Costs", "Exchange/commission model plus one tick of slippage per side in the base result"),
    ]
    if experiment_id == "EXP-005":
        return common + [
            ("What was tested", "One unchanged 15-minute opening-range breakout transferred to NQ and MNQ; both long and short trades were allowed."),
            ("Optimization", "Disabled. One fixed parameter combination was evaluated on the protected 2023–2025 confirmation period."),
            ("MCPT", f"{int(mcpt.get('permutations', 0)):,} session-aware permutations tested the fixed rules."),
        ]
    if experiment_id == "EXP-006":
        return common + [
            ("What was tested", "Twenty-seven combinations varied opening-range duration, final entry time and direction mode."),
            ("Selection", "Candidates were ranked after eligibility and immediate-neighbour stability checks."),
            ("Walk-forward", "Five expanding training windows selected a candidate before each annual test fold."),
            ("MCPT", f"{int(mcpt.get('permutations', 0)):,} selection-aware permutations repeated the full 27-candidate search."),
        ]
    if experiment_id == "EXP-007":
        rules = decision.get("fixed_rules", {})
        return common + [
            ("What was tested", "One fixed long-only ORB geometry: first completed five-minute close above the opening range, followed by next-bar-open entry."),
            ("Risk and exit", f"Stop at the opening-range low, {rules.get('reward_to_risk', 1.0)}R target and {rules.get('forced_flat_time_new_york', '14:00')} forced exit."),
            ("Optimization", "Disabled. The strategy had one fixed combination."),
            ("MCPT", f"{int(mcpt.get('permutations', 0)):,} session-aware fixed-strategy permutations."),
        ]
    return common + [
        ("What was tested", "Twenty-seven long-only geometries varied opening-range duration, reward-to-risk target and forced-flat time."),
        ("Selection", "The highest eligible NQ Profit Factor was selected only after immediate-neighbour profitability and median-PF checks."),
        ("Walk-forward", "Five expanding training windows repeated the same selection procedure before each annual test fold."),
        ("MCPT", f"{int(mcpt.get('permutations', 0)):,} selection-aware permutations reran all 27 candidates and the complete selection procedure."),
    ]


def _save_figure(figure: plt.Figure, output: Path) -> None:
    figure.tight_layout()
    save_report_figure(
        figure,
        output,
        dpi=150,
        bbox_inches="tight",
    )
    plt.close(figure)


def _write_charts(
    *,
    assets: Path,
    experiment_id: str,
    trades: pd.DataFrame,
    timeseries: pd.DataFrame,
    monthly: pd.DataFrame,
    rolling: pd.DataFrame,
    annual: pd.DataFrame,
    mcpt: pd.DataFrame,
    decision: dict[str, Any],
    cost: pd.DataFrame,
    walk_forward: pd.DataFrame,
    grid: pd.DataFrame,
) -> list[str]:
    assets.mkdir(parents=True, exist_ok=True)
    written: list[str] = []

    dates = pd.to_datetime(timeseries["session_date"])
    figure, axis = plt.subplots(figsize=(13, 5.6))
    axis.plot(dates, timeseries["strategy_equity"], label="Strategy equity")
    axis.plot(dates, timeseries["benchmark_equity"], label="NQ close benchmark")
    axis.plot(dates, timeseries["cash_equity"], label="Cash")
    axis.set_title("Strategy versus normalized NQ market benchmark")
    axis.set_ylabel("Normalized equity (USD)")
    axis.legend()
    axis.grid(alpha=0.25)
    path = assets / "strategy_vs_benchmark.png"
    _save_figure(figure, path); written.append(path.name)

    figure, axis = plt.subplots(figsize=(13, 4.8))
    axis.plot(dates, timeseries["strategy_drawdown_percent"], label="Strategy")
    axis.plot(dates, timeseries["benchmark_drawdown_percent"], label="NQ benchmark")
    axis.axhline(0.0, linewidth=0.8)
    axis.set_title("Strategy and benchmark drawdown")
    axis.set_ylabel("Drawdown (%)")
    axis.legend()
    axis.grid(alpha=0.25)
    path = assets / "drawdown_vs_benchmark.png"
    _save_figure(figure, path); written.append(path.name)

    figure, axis = plt.subplots(figsize=(12, 5.0))
    positions = np.arange(len(annual))
    width = 0.38
    axis.bar(positions - width / 2, annual["Strategy net profit"], width=width, label="Strategy net profit (USD)")
    second = axis.twinx()
    second.bar(positions + width / 2, annual["Benchmark return %"], width=width, alpha=0.55, label="Benchmark return %")
    axis.set_xticks(positions)
    axis.set_xticklabels(annual["Year"].astype(str))
    axis.set_title("Annual strategy result and NQ benchmark return")
    axis.set_ylabel("Strategy net profit (USD)")
    second.set_ylabel("Benchmark return (%)")
    lines, labels = axis.get_legend_handles_labels()
    lines2, labels2 = second.get_legend_handles_labels()
    axis.legend(lines + lines2, labels + labels2, loc="best")
    axis.grid(axis="y", alpha=0.25)
    path = assets / "annual_strategy_vs_benchmark.png"
    _save_figure(figure, path); written.append(path.name)

    figure, axis = plt.subplots(figsize=(13, max(3.8, 0.55 * len(monthly))))
    image = axis.imshow(monthly.to_numpy(dtype=float), aspect="auto")
    axis.set_title("Monthly net-profit heatmap")
    axis.set_xlabel("Month")
    axis.set_ylabel("Year")
    axis.set_xticks(range(12))
    axis.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    axis.set_yticks(range(len(monthly.index)))
    axis.set_yticklabels(monthly.index.astype(str))
    for row in range(len(monthly.index)):
        for column in range(12):
            axis.text(column, row, f"{monthly.iloc[row, column] / 1000:.1f}k", ha="center", va="center", fontsize=8)
    figure.colorbar(image, ax=axis, label="Net profit (USD)")
    path = assets / "monthly_heatmap.png"
    _save_figure(figure, path); written.append(path.name)

    if not rolling.empty:
        figure, axis = plt.subplots(figsize=(13, 5.0))
        axis.plot(rolling["trade_number"], rolling["rolling_profit_factor"], label="Rolling 100-trade PF")
        axis.axhline(1.0, linewidth=0.8, linestyle="--")
        second = axis.twinx()
        second.plot(rolling["trade_number"], rolling["rolling_average_trade_usd"], alpha=0.65, label="Rolling average trade")
        second.axhline(0.0, linewidth=0.8)
        axis.set_title("Rolling 100-trade quality")
        axis.set_xlabel("Completed trade number")
        axis.set_ylabel("Profit Factor")
        second.set_ylabel("Average trade (USD)")
        lines, labels = axis.get_legend_handles_labels()
        lines2, labels2 = second.get_legend_handles_labels()
        axis.legend(lines + lines2, labels + labels2, loc="best")
        axis.grid(alpha=0.25)
        path = assets / "rolling_quality.png"
        _save_figure(figure, path); written.append(path.name)

    pnl = pd.to_numeric(trades["net_pnl_usd"], errors="coerce").dropna()
    figure, axis = plt.subplots(figsize=(12, 5.0))
    axis.hist(pnl, bins=45)
    axis.axvline(0.0, linewidth=0.8)
    axis.axvline(float(pnl.mean()), linewidth=1.8, label="Average trade")
    axis.set_title("Trade P&L distribution")
    axis.set_xlabel("Net P&L per trade (USD)")
    axis.set_ylabel("Trades")
    axis.legend()
    axis.grid(axis="y", alpha=0.25)
    path = assets / "trade_pnl_distribution.png"
    _save_figure(figure, path); written.append(path.name)

    exit_counts = trades.get("exit_reason", pd.Series("Unknown", index=trades.index)).fillna("Unknown").astype(str).value_counts()
    figure, axis = plt.subplots(figsize=(12, 4.8))
    exit_counts.sort_values().plot(kind="barh", ax=axis)
    axis.set_title("How trades exited")
    axis.set_xlabel("Completed trades")
    axis.grid(axis="x", alpha=0.25)
    path = assets / "exit_reason_counts.png"
    _save_figure(figure, path); written.append(path.name)

    holding = _holding_minutes(trades).dropna()
    if not holding.empty:
        figure, axis = plt.subplots(figsize=(12, 4.8))
        axis.hist(holding, bins=35)
        axis.axvline(float(holding.median()), linewidth=1.8, label="Median")
        axis.set_title("Trade holding-time distribution")
        axis.set_xlabel("Minutes held")
        axis.set_ylabel("Trades")
        axis.legend()
        axis.grid(axis="y", alpha=0.25)
        path = assets / "holding_time_distribution.png"
        _save_figure(figure, path); written.append(path.name)

    if "entry_time" in trades:
        entry = _repair_timestamp_series(trades["entry_time"])
        hours = entry.dropna().dt.strftime("%H:%M").value_counts().sort_index()
        if not hours.empty:
            figure, axis = plt.subplots(figsize=(13, 4.8))
            hours.plot(kind="bar", ax=axis)
            axis.set_title("Entry-time distribution")
            axis.set_xlabel("New York entry time")
            axis.set_ylabel("Trades")
            axis.tick_params(axis="x", labelrotation=70)
            axis.grid(axis="y", alpha=0.25)
            path = assets / "entry_time_distribution.png"
            _save_figure(figure, path); written.append(path.name)

    direction = trades.get("direction", pd.Series("", index=trades.index)).astype(str).str.lower()
    figure, axis = plt.subplots(figsize=(13, 5.0))
    for name in ("long", "short"):
        local = trades.loc[direction.eq(name)]
        if local.empty:
            continue
        local = local.copy()
        local["session_date"] = pd.to_datetime(local["session_date"])
        daily = local.groupby("session_date")["net_pnl_usd"].sum().cumsum()
        axis.plot(daily.index, daily.values, label=name.title())
    axis.axhline(0.0, linewidth=0.8)
    axis.set_title("Long and short cumulative P&L")
    axis.set_ylabel("Cumulative net P&L (USD)")
    axis.legend()
    axis.grid(alpha=0.25)
    path = assets / "direction_equity.png"
    _save_figure(figure, path); written.append(path.name)

    if not cost.empty and {"slippage_ticks_per_side", "net_profit_usd"}.issubset(cost.columns):
        figure, axis = plt.subplots(figsize=(12, 4.8))
        if "symbol" in cost:
            for symbol, frame in cost.groupby("symbol"):
                axis.plot(frame["slippage_ticks_per_side"], frame["net_profit_usd"], marker="o", label=str(symbol))
            axis.legend()
        else:
            axis.plot(cost["slippage_ticks_per_side"], cost["net_profit_usd"], marker="o")
        axis.axhline(0.0, linewidth=0.8)
        axis.set_title("Cost sensitivity")
        axis.set_xlabel("Slippage ticks per side")
        axis.set_ylabel("Net profit (USD)")
        axis.grid(alpha=0.25)
        path = assets / "cost_sensitivity.png"
        _save_figure(figure, path); written.append(path.name)

    if not walk_forward.empty:
        net_column = next((name for name in ("test_net_profit_usd", "nq_test_net_profit_usd", "net_profit_usd") if name in walk_forward), None)
        fold_column = "fold" if "fold" in walk_forward else None
        if net_column and fold_column:
            figure, axis = plt.subplots(figsize=(12, 4.8))
            axis.bar(walk_forward[fold_column].astype(str), walk_forward[net_column])
            axis.axhline(0.0, linewidth=0.8)
            axis.set_title("Anchored walk-forward test-fold net profit")
            axis.set_xlabel("Fold")
            axis.set_ylabel("NQ net profit (USD)")
            axis.grid(axis="y", alpha=0.25)
            path = assets / "walk_forward.png"
            _save_figure(figure, path); written.append(path.name)

    if not mcpt.empty:
        possible = (
            "selected_trade_profit_factor",
            "trade_profit_factor",
            "best_selection_statistic",
            "best_trade_profit_factor",
        )
        value_column = next((name for name in possible if name in mcpt), None)
        if value_column:
            values = pd.to_numeric(mcpt[value_column], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
            if not values.empty:
                real = decision.get("mcpt", {}).get("real_selected_trade_profit_factor")
                if real is None:
                    real = decision.get("mcpt", {}).get("real_selection_statistic")
                if real is None:
                    real = decision.get("results", {}).get("NQ", {}).get("trade_profit_factor")
                figure, axis = plt.subplots(figsize=(12, 4.8))
                axis.hist(values, bins=40)
                if real is not None:
                    axis.axvline(float(real), linewidth=2.0, label="Real result")
                    axis.legend()
                axis.set_title("MCPT null distribution")
                axis.set_xlabel(value_column.replace("_", " ").title())
                axis.set_ylabel("Permutations")
                axis.grid(axis="y", alpha=0.25)
                path = assets / "mcpt_distribution.png"
                _save_figure(figure, path); written.append(path.name)

    if not grid.empty and experiment_id in {"EXP-006", "EXP-008"}:
        if experiment_id == "EXP-008" and {"forced_flat_time_new_york", "opening_range_minutes", "reward_to_risk", "nq_trade_profit_factor"}.issubset(grid.columns):
            for flat, frame in grid.groupby("forced_flat_time_new_york"):
                pivot = frame.pivot(index="opening_range_minutes", columns="reward_to_risk", values="nq_trade_profit_factor").sort_index()
                figure, axis = plt.subplots(figsize=(8.5, 5.0))
                image = axis.imshow(pivot.to_numpy(dtype=float), aspect="auto")
                axis.set_xticks(range(len(pivot.columns))); axis.set_xticklabels([f"{v:g}R" for v in pivot.columns])
                axis.set_yticks(range(len(pivot.index))); axis.set_yticklabels([f"{v} min" for v in pivot.index])
                for row in range(len(pivot.index)):
                    for column in range(len(pivot.columns)):
                        axis.text(column, row, f"{pivot.iloc[row, column]:.3f}", ha="center", va="center")
                axis.set_title(f"NQ Profit Factor surface · forced flat {flat}")
                figure.colorbar(image, ax=axis)
                path = assets / f"parameter_surface_{str(flat).replace(':', '')}.png"
                _save_figure(figure, path); written.append(path.name)
        elif experiment_id == "EXP-006" and {"direction_mode", "opening_range_minutes", "final_entry_time_new_york", "nq_trade_profit_factor"}.issubset(grid.columns):
            for mode, frame in grid.groupby("direction_mode"):
                pivot = frame.pivot(index="opening_range_minutes", columns="final_entry_time_new_york", values="nq_trade_profit_factor").sort_index()
                figure, axis = plt.subplots(figsize=(8.5, 5.0))
                image = axis.imshow(pivot.to_numpy(dtype=float), aspect="auto")
                axis.set_xticks(range(len(pivot.columns))); axis.set_xticklabels(pivot.columns)
                axis.set_yticks(range(len(pivot.index))); axis.set_yticklabels([f"{v} min" for v in pivot.index])
                for row in range(len(pivot.index)):
                    for column in range(len(pivot.columns)):
                        axis.text(column, row, f"{pivot.iloc[row, column]:.3f}", ha="center", va="center")
                axis.set_title(f"NQ Profit Factor surface · {mode}")
                figure.colorbar(image, ax=axis)
                path = assets / f"parameter_surface_{mode}.png"
                _save_figure(figure, path); written.append(path.name)

    return written


def _robustness_tables(
    decision: dict[str, Any],
    cost: pd.DataFrame,
    walk_forward: pd.DataFrame,
    grid: pd.DataFrame,
    bootstrap: dict[str, Any],
) -> str:
    pieces: list[str] = []
    if not cost.empty:
        pieces.append("<h3>Cost sensitivity</h3>" + _table(cost))
    if not walk_forward.empty:
        pieces.append("<h3>Anchored walk-forward folds</h3>" + _table(walk_forward))
    if not grid.empty:
        selected_column = "selected" if "selected" in grid else None
        if selected_column:
            selected = grid.loc[grid[selected_column].astype(bool)]
            pieces.append("<h3>Selected row</h3>" + _table(selected))
        pieces.append("<h3>Complete parameter grid</h3>" + _table(grid))
    if bootstrap:
        rows = pd.DataFrame(
            [{"Field": key.replace("_", " ").title(), "Value": value} for key, value in bootstrap.items()]
        )
        pieces.append("<h3>Bootstrap diagnostics</h3>" + _table(rows))
    mcpt = decision.get("mcpt", {})
    if mcpt:
        rows = []
        for key in (
            "permutations",
            "base_seed",
            "p_value",
            "permutations_at_least_real",
            "real_selected_trade_profit_factor",
            "real_selection_statistic",
            "permutation_selected_pf_median",
            "permutation_selected_pf_maximum",
        ):
            if key in mcpt:
                rows.append({"Measurement": key.replace("_", " ").title(), "Value": mcpt[key]})
        pieces.append("<h3>MCPT measurements</h3>" + _table(pd.DataFrame(rows)))
    return "".join(pieces)


def build_strategy_measurement_report(
    *,
    spec: MeasurementSpec,
    benchmark_one_minute: pd.DataFrame,
    output_dir: Path,
    measurement_results_dir: Path,
) -> dict[str, Any]:
    validate_measurement_inputs(spec)
    decision = _read_json(spec.decision_file)
    nq_trades = _read_csv(spec.nq_trades_file)
    mnq_trades = _read_csv(spec.mnq_trades_file)
    nq_equity = _read_csv(spec.nq_equity_file)
    mnq_equity = _read_csv(spec.mnq_equity_file)
    yearly = _read_csv(spec.yearly_file)
    cost = _read_csv(spec.cost_file)
    mcpt = _read_csv(spec.mcpt_file)
    walk_forward = _read_csv(spec.walk_forward_file)
    grid = _read_csv(spec.grid_file)
    bootstrap = _read_json(spec.bootstrap_file)
    review = _read_json(spec.review_file)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    legacy = output_dir / "report_legacy.html"
    current = output_dir / "report.html"
    if current.exists() and not legacy.exists():
        shutil.copy2(current, legacy)

    nq_equity = nq_equity.copy()
    nq_equity["session_date"] = pd.to_datetime(nq_equity["session_date"])
    start_date = nq_equity["session_date"].min().date().isoformat()
    end_date = nq_equity["session_date"].max().date().isoformat()
    benchmark = normalized_benchmark(
        benchmark_one_minute,
        start_date=start_date,
        end_date=end_date,
        reference_capital=REFERENCE_CAPITAL["NQ"],
    )
    timeseries = comparison_timeseries(
        nq_equity,
        benchmark,
        reference_capital=REFERENCE_CAPITAL["NQ"],
    )
    monthly, month_series = _monthly_matrix(nq_trades)
    rolling = _rolling_metrics(nq_trades)
    annual = _annual_comparison(timeseries)
    drawdowns, longest_drawdown = _drawdown_episodes(timeseries)
    tail = _tail_table(nq_trades)
    performance = performance_table(nq_trades)
    all_metrics = _segment_metrics(nq_trades)
    mnq_metrics = _segment_metrics(mnq_trades)

    strategy_return = (float(timeseries["strategy_equity"].iloc[-1]) / REFERENCE_CAPITAL["NQ"] - 1.0) * 100.0
    benchmark_return = (float(timeseries["benchmark_equity"].iloc[-1]) / REFERENCE_CAPITAL["NQ"] - 1.0) * 100.0
    strategy_dd = float(timeseries["strategy_drawdown_percent"].min())
    benchmark_dd = float(timeseries["benchmark_drawdown_percent"].min())
    profitable_months = float((month_series > 0).mean() * 100.0) if len(month_series) else float("nan")
    session_count = int(len(timeseries))
    trades_per_year = float(len(nq_trades) / max(1.0, session_count / 252.0))
    sessions_traded = int(pd.to_datetime(nq_trades["session_date"]).nunique())
    participation = sessions_traded / session_count * 100.0 if session_count else float("nan")

    label, failed, decision_reason = _decision_context(decision)
    parameter_description = _parameter_description(spec.experiment_id, decision)
    mcpt_p = _safe_float(decision.get("mcpt", {}).get("p_value"))
    mcpt_permutations = int(decision.get("mcpt", {}).get("permutations", 0) or 0)
    mcpt_exceedances = int(decision.get("mcpt", {}).get("permutations_at_least_real", 0) or 0)
    mcpt_percentile = (1.0 - mcpt_exceedances / mcpt_permutations) * 100.0 if mcpt_permutations else float("nan")

    what_happened = (
        f"The saved NQ result completed {len(nq_trades):,} trades from {start_date} through {end_date}. "
        f"It produced {_money(all_metrics['net_profit_usd'])}, a Profit Factor of {_number(all_metrics['profit_factor'], 3)}, "
        f"a {_percent(all_metrics['win_rate_percent'])} win rate and a maximum drawdown of {_money(all_metrics['maximum_drawdown_usd'])}. "
        f"Using the locked $100,000 reporting denominator, strategy return was {_percent(strategy_return)} versus "
        f"{_percent(benchmark_return)} for the normalized NQ close benchmark."
    )
    if failed:
        why = (
            decision_reason
            + (f" The saved MCPT p-value was {_number(mcpt_p, 6)}." if math.isfinite(mcpt_p) else "")
        )
    else:
        why = decision_reason
    context_note = (
        "The NQ benchmark is a normalized close-to-close price path from the same frozen session data. "
        "It is a descriptive buy-and-hold-style comparator, not a tradable one-contract futures backtest: "
        "contract-roll, financing, margin and position-sizing assumptions are not modeled."
    )

    assets = output_dir / "assets"
    written = _write_charts(
        assets=assets,
        experiment_id=spec.experiment_id,
        trades=nq_trades,
        timeseries=timeseries,
        monthly=monthly,
        rolling=rolling,
        annual=annual,
        mcpt=mcpt,
        decision=decision,
        cost=cost,
        walk_forward=walk_forward,
        grid=grid,
    )

    design_rows = pd.DataFrame(_test_design(spec.experiment_id, decision), columns=["Question", "Readable answer"])
    benchmark_table = pd.DataFrame(
        [
            {"Measurement": "Ending return", "Strategy": _percent(strategy_return), "NQ benchmark": _percent(benchmark_return)},
            {"Measurement": "Maximum drawdown", "Strategy": _percent(strategy_dd), "NQ benchmark": _percent(benchmark_dd)},
            {"Measurement": "Ending value from $100,000", "Strategy": _money(timeseries["strategy_equity"].iloc[-1]), "NQ benchmark": _money(timeseries["benchmark_equity"].iloc[-1])},
            {"Measurement": "Excess ending return", "Strategy": _percent(strategy_return - benchmark_return), "NQ benchmark": "0.00%"},
        ]
    )
    practical_table = pd.DataFrame(
        [
            {"Measurement": "Sessions in report", "Value": _integer(session_count)},
            {"Measurement": "Sessions with a trade", "Value": _integer(sessions_traded)},
            {"Measurement": "Session participation", "Value": _percent(participation)},
            {"Measurement": "Approximate trades per year", "Value": _number(trades_per_year, 1)},
            {"Measurement": "Average holding time", "Value": f"{_number(all_metrics['average_holding_minutes'], 1)} minutes"},
            {"Measurement": "Median holding time", "Value": f"{_number(all_metrics['median_holding_minutes'], 1)} minutes"},
            {"Measurement": "Maximum consecutive losses", "Value": _integer(all_metrics["max_consecutive_losses"])},
            {"Measurement": "Profitable months", "Value": _percent(profitable_months)},
            {"Measurement": "Longest drawdown", "Value": f"{longest_drawdown:,} sessions"},
        ]
    )
    mnq_table = pd.DataFrame(
        [
            {"Metric": "Completed trades", "MNQ": _integer(mnq_metrics["completed_trades"])},
            {"Metric": "Net profit", "MNQ": _money(mnq_metrics["net_profit_usd"])},
            {"Metric": "Profit Factor", "MNQ": _number(mnq_metrics["profit_factor"], 3)},
            {"Metric": "Win rate", "MNQ": _percent(mnq_metrics["win_rate_percent"])},
            {"Metric": "Average trade", "MNQ": _money(mnq_metrics["average_trade_usd"])},
            {"Metric": "Maximum drawdown", "MNQ": _money(mnq_metrics["maximum_drawdown_usd"])},
        ]
    )

    decision_rows = []
    for name, gate in decision.get("evaluation", {}).get("gates", {}).items():
        decision_rows.append(
            {
                "Gate": name.replace("_", " ").title(),
                "Actual": gate.get("actual"),
                "Rule": f"{gate.get('operator', '')} {gate.get('threshold', '')}",
                "Result": "Pass" if gate.get("passed") else "Fail",
            }
        )

    def tone(label_text: str, raw_value: Any) -> str:
        return _cell_tone(label_text, label_text, raw_value)

    upper_label = label.upper()
    status_tone = (
        "tone-negative"
        if "REJECT" in upper_label or "FAIL" in upper_label
        else (
            "tone-positive"
            if (
                "ACCEPT" in upper_label
                or "PASS" in upper_label
                or "LOCK" in upper_label
            )
            else ""
        )
    )

    chart = lambda name, alt: (
        f'<img class="chart" src="assets/{html.escape(name)}" alt="{html.escape(alt)}">'
        if name in written else ""
    )
    parameter_images = "".join(
        chart(name, "Parameter surface")
        for name in written
        if name.startswith("parameter_surface_")
    )

    document = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(spec.experiment_id)} Strategy Measurement Report</title>
<style>
:root {{ color-scheme:light dark; --bg:#07111f; --panel:#101d31; --panel2:#152641; --line:#2b3e5d; --text:#edf3fb; --muted:#a8b6c9; --accent:#7dd3fc; --good:#86efac; --bad:#fca5a5; }}
* {{ box-sizing:border-box; }}
html {{ scroll-behavior:smooth; }}
body {{ margin:0; background:var(--bg); color:var(--text); font-family:Inter,Segoe UI,Arial,sans-serif; line-height:1.55; }}
nav {{ position:fixed; inset:0 auto 0 0; width:260px; padding:24px 17px; background:#0b1728; border-right:1px solid var(--line); overflow:auto; }}
nav strong {{ display:block; margin-bottom:14px; }}
nav a {{ display:block; color:var(--muted); text-decoration:none; padding:7px 8px; border-radius:8px; }}
nav a:hover {{ color:var(--text); background:var(--panel); }}
.hub-link {{ color:var(--accent); font-weight:800; border:1px solid var(--line); margin-bottom:6px; }}
main {{ margin-left:260px; width:min(1380px,calc(100% - 300px)); padding:30px 0 70px; }}
header, section {{ background:var(--panel); border:1px solid var(--line); border-radius:16px; padding:24px; margin-bottom:18px; overflow:auto; }}
h1,h2,h3 {{ line-height:1.22; margin-top:0; }}
.kicker {{ color:var(--accent); text-transform:uppercase; letter-spacing:.1em; font-size:.76rem; font-weight:800; }}
.status {{ display:inline-block; border:1px solid var(--line); border-radius:999px; padding:7px 11px; color:var(--muted); font-weight:700; }}
.status.tone-positive {{ color:var(--good); }}
.status.tone-negative {{ color:var(--bad); }}
.lead {{ font-size:1.08rem; max-width:1100px; }}
.callout {{ background:var(--panel2); border-left:4px solid var(--accent); padding:16px 18px; border-radius:10px; margin:15px 0; }}
.note {{ color:var(--muted); }}
.data-table {{ width:100%; min-width:820px; border-collapse:collapse; }}
th,td {{ border-bottom:1px solid var(--line); padding:9px 10px; text-align:left; vertical-align:top; white-space:nowrap; }}
th {{ background:#1d3557; color:#dbeafe; }}
.data-table tbody tr:nth-child(even) {{ background:rgba(255,255,255,.02); }}
.data-table tbody tr:hover {{ background:rgba(125,211,252,.07); }}
.row-label {{ color:#bfdbfe; font-weight:750; }}
.value-positive {{ color:var(--good); font-weight:inherit; }}
.value-negative {{ color:var(--bad); font-weight:inherit; }}
.chart {{ display:block; width:100%; height:auto; margin:16px 0 26px; background:white; border:1px solid var(--line); border-radius:12px; }}
.metrics {{ display:grid; grid-template-columns:repeat(4,minmax(150px,1fr)); gap:10px; }}
.metric {{ background:var(--panel2); border:1px solid var(--line); border-radius:12px; padding:13px; }}
.metric span {{ display:block; color:var(--muted); font-size:.78rem; }}
.metric strong {{ display:block; margin-top:3px; font-size:1.2rem; }}
.metric.tone-positive strong {{ color:var(--good); }}
.metric.tone-negative strong {{ color:var(--bad); }}
@media(max-width:900px) {{ nav {{ position:static; width:auto; }} main {{ margin:0 auto; width:calc(100% - 24px); }} .metrics {{ grid-template-columns:1fr 1fr; }} }}
{STRATEGY_EXPLANATION_CSS}
</style>
</head>
<body>
<nav>
<strong>{html.escape(spec.experiment_id)} measurements</strong>
<a class="hub-link" href="../research_dashboard/index.html">← Research hub</a>
<a class="hub-link" href="../research_dashboard/strategy_comparison.html">Strategy comparison</a>
<a href="#overview">Overview</a>
<a href="#strategy-rules">How the strategy works</a>
<a href="#happened">What happened and why</a>
<a href="#design">What and how we tested</a>
<a href="#performance">Performance</a>
<a href="#benchmark">Strategy vs NQ</a>
<a href="#risk">Risk and drawdown</a>
<a href="#consistency">Consistency</a>
<a href="#behaviour">Trade behaviour</a>
<a href="#distribution">Distribution</a>
<a href="#robustness">Robustness</a>
<a href="#decision">Formal decision context</a>
</nav>
<main>
<header id="overview">
<div class="kicker">{html.escape(spec.subtitle)} · {REPORT_VERSION}</div>
<h1>{html.escape(spec.title)}</h1>
<p class="lead">{html.escape(parameter_description)}</p>
<p class="status {status_tone}">Formal status: {html.escape(label.replace('_', ' ').title())}</p>
<div class="metrics">
<div class="metric {tone('Profit Factor', all_metrics['profit_factor'])}"><span>Profit Factor</span><strong>{_number(all_metrics['profit_factor'], 3)}</strong></div>
<div class="metric {tone('Win rate', all_metrics['win_rate_percent'])}"><span>Win rate</span><strong>{_percent(all_metrics['win_rate_percent'])}</strong></div>
<div class="metric {tone('Net profit', all_metrics['net_profit_usd'])}"><span>Net profit</span><strong>{_money(all_metrics['net_profit_usd'])}</strong></div>
<div class="metric {tone('Maximum drawdown', all_metrics['maximum_drawdown_usd'])}"><span>Maximum drawdown</span><strong>{_money(all_metrics['maximum_drawdown_usd'])}</strong></div>
<div class="metric {tone('Average trade', all_metrics['average_trade_usd'])}"><span>Average trade</span><strong>{_money(all_metrics['average_trade_usd'])}</strong></div>
<div class="metric {tone('Net profit / drawdown', all_metrics['net_profit_to_drawdown'])}"><span>Net profit / drawdown</span><strong>{_number(all_metrics['net_profit_to_drawdown'], 3)}</strong></div>
<div class="metric"><span>Completed trades</span><strong>{len(nq_trades):,}</strong></div>
<div class="metric {tone('MCPT p-value', mcpt_p)}"><span>MCPT p-value</span><strong>{_number(mcpt_p, 4)}</strong></div>
</div>
</header>
{strategy_explanation_html(spec.experiment_id)}
<section id="happened"><h2>What happened and why</h2><div class="callout"><strong>What happened</strong><p>{html.escape(what_happened)}</p></div><div class="callout"><strong>Why the formal decision happened</strong><p>{html.escape(why)}</p></div><p class="note">A gate controls the claim made about a result. It does not erase the result's measured performance, risk, consistency or practical characteristics.</p></section>
<section id="design"><h2>What and how we tested</h2>{_table(design_rows)}<p class="note">This report is rebuilt only from saved frozen result files and frozen market data. It does not rerun a strategy, optimization, bootstrap or MCPT.</p></section>
<section id="performance"><h2>Complete NQ performance summary</h2>{_table(performance)}<h3>MNQ implementation comparison</h3>{_table(mnq_table)}</section>
<section id="benchmark"><h2>Strategy versus NQ market benchmark</h2><p>{html.escape(context_note)}</p>{chart('strategy_vs_benchmark.png','Strategy versus NQ benchmark')}{chart('drawdown_vs_benchmark.png','Strategy and benchmark drawdown')}{_table(benchmark_table)}</section>
<section id="risk"><h2>Risk, drawdown and recovery</h2>{chart('direction_equity.png','Long and short cumulative P&L')}<h3>Largest drawdown episodes</h3>{_table(drawdowns)}<h3>Practical risk measurements</h3>{_table(practical_table)}</section>
<section id="consistency"><h2>Consistency through time</h2>{chart('annual_strategy_vs_benchmark.png','Annual strategy and benchmark')}{chart('monthly_heatmap.png','Monthly heatmap')}{chart('rolling_quality.png','Rolling quality')}{_table(annual)}</section>
<section id="behaviour"><h2>How the strategy behaves</h2>{chart('entry_time_distribution.png','Entry time distribution')}{chart('holding_time_distribution.png','Holding time distribution')}{chart('exit_reason_counts.png','Exit reason counts')}</section>
<section id="distribution"><h2>Trade distribution and profit concentration</h2>{chart('trade_pnl_distribution.png','Trade P&L distribution')}{_table(tail)}</section>
<section id="robustness"><h2>Robustness and statistical uncertainty</h2>{chart('cost_sensitivity.png','Cost sensitivity')}{chart('walk_forward.png','Walk-forward')}{chart('mcpt_distribution.png','MCPT distribution')}{parameter_images}{_robustness_tables(decision,cost,walk_forward,grid,bootstrap)}</section>
<section id="decision"><h2>Formal decision context</h2><p>{html.escape(decision_reason)}</p>{_table(pd.DataFrame(decision_rows))}<p class="note">Review decision: {html.escape(str(review.get('evaluation', {}).get('decision', review.get('decision', 'Not applicable'))))}. Lifecycle status remains unchanged by this reporting upgrade.</p></section>
</main>
</body>
</html>"""
    current.write_text(document, encoding="utf-8")

    measurement_results_dir = Path(measurement_results_dir) / spec.experiment_id
    measurement_results_dir.mkdir(parents=True, exist_ok=True)
    timeseries.to_csv(measurement_results_dir / "comparison_timeseries.csv", index=False)
    rolling.to_csv(measurement_results_dir / "rolling_trade_quality.csv", index=False)
    monthly.to_csv(measurement_results_dir / "monthly_net_profit.csv")
    performance.to_csv(measurement_results_dir / "performance_summary.csv", index=False)
    drawdowns.to_csv(measurement_results_dir / "drawdown_episodes.csv", index=False)

    cost_two_tick = float("nan")
    if not cost.empty and {"slippage_ticks_per_side", "net_profit_usd"}.issubset(cost.columns):
        filtered = cost.loc[pd.to_numeric(cost["slippage_ticks_per_side"], errors="coerce").eq(2.0)]
        if "symbol" in filtered:
            filtered = filtered.loc[filtered["symbol"].astype(str).eq("NQ")]
        if not filtered.empty:
            cost_two_tick = float(filtered["net_profit_usd"].iloc[0])
    wf_profitable = float("nan")
    wf_count = float("nan")
    wf_net = float("nan")
    if not walk_forward.empty:
        profitability = next((name for name in ("test_profitable", "nq_test_profitable", "profitable") if name in walk_forward), None)
        net_column = next((name for name in ("test_net_profit_usd", "nq_test_net_profit_usd", "net_profit_usd") if name in walk_forward), None)
        if profitability:
            wf_profitable = int(walk_forward[profitability].astype(bool).sum())
            wf_count = int(len(walk_forward))
        if net_column:
            wf_net = float(pd.to_numeric(walk_forward[net_column], errors="coerce").sum())

    summary = {
        "experiment_id": spec.experiment_id,
        "title": spec.title,
        "parameters": parameter_description,
        "start_date": start_date,
        "end_date": end_date,
        "sessions": session_count,
        "completed_trades": len(nq_trades),
        "profit_factor": all_metrics["profit_factor"],
        "win_rate_percent": all_metrics["win_rate_percent"],
        "average_trade_usd": all_metrics["average_trade_usd"],
        "net_profit_usd": all_metrics["net_profit_usd"],
        "maximum_drawdown_usd": all_metrics["maximum_drawdown_usd"],
        "maximum_drawdown_percent": strategy_dd,
        "net_profit_to_drawdown": all_metrics["net_profit_to_drawdown"],
        "average_trade_to_cost": all_metrics["average_trade_to_cost"],
        "max_consecutive_losses": all_metrics["max_consecutive_losses"],
        "median_holding_minutes": all_metrics["median_holding_minutes"],
        "profitable_months_percent": profitable_months,
        "longest_drawdown_sessions": longest_drawdown,
        "session_participation_percent": participation,
        "trades_per_year": trades_per_year,
        "strategy_return_percent": strategy_return,
        "benchmark_return_percent": benchmark_return,
        "benchmark_max_drawdown_percent": benchmark_dd,
        "excess_return_percent": strategy_return - benchmark_return,
        "mnq_profit_factor": mnq_metrics["profit_factor"],
        "mnq_net_profit_usd": mnq_metrics["net_profit_usd"],
        "two_tick_nq_net_profit_usd": cost_two_tick,
        "walk_forward_profitable_folds": wf_profitable,
        "walk_forward_fold_count": wf_count,
        "walk_forward_net_profit_usd": wf_net,
        "mcpt_p_value": mcpt_p,
        "mcpt_percentile": mcpt_percentile,
        "formal_decision": label,
        "failed_gates": "|".join(failed),
        "report_file": str(current.relative_to(spec.result_directory.parents[2])) if False else str(current),
        "report_version": REPORT_VERSION,
    }
    (measurement_results_dir / "measurement_summary.json").write_text(
        json.dumps(_json_safe(summary), indent=2, allow_nan=False), encoding="utf-8"
    )
    return summary
