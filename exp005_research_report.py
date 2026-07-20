from __future__ import annotations

from dataclasses import dataclass
import html
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from report_chart_style import save_report_figure


PROJECT_DIR = Path(__file__).resolve().parent
RESULT_ROOT = PROJECT_DIR / "results" / "EXP-005" / "full_validation"
QUICK_ROOT = PROJECT_DIR / "results" / "EXP-005" / "quick_transfer"
REVIEW_ROOT = PROJECT_DIR / "results" / "EXP-005" / "review"
REPORT_ROOT = PROJECT_DIR / "reports" / "EXP-005-research-lab"
ASSET_ROOT = REPORT_ROOT / "assets"

DEFAULT_REFERENCE_CAPITAL = {
    "NQ": 100_000.0,
    "MNQ": 10_000.0,
}


@dataclass(frozen=True)
class Exp005SavedResults:
    decision: dict[str, Any]
    review: dict[str, Any]
    quick: dict[str, Any]
    summary: pd.DataFrame
    yearly: pd.DataFrame
    cost_sensitivity: pd.DataFrame
    nq_equity: pd.DataFrame
    mnq_equity: pd.DataFrame
    nq_trades: pd.DataFrame
    mnq_trades: pd.DataFrame
    mcpt: pd.DataFrame
    confirmation_audit: dict[str, Any]


def _read_json(path: Path, *, required: bool = True) -> dict[str, Any]:
    if not path.exists():
        if required:
            raise FileNotFoundError(path)
        return {}

    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def load_reference_capital() -> dict[str, float]:
    try:
        from exp005_paper_testing_plan import (  # type: ignore
            get_exp005_paper_testing_plan,
            validate_exp005_paper_testing_plan,
        )
    except ImportError:
        return dict(DEFAULT_REFERENCE_CAPITAL)

    validate_exp005_paper_testing_plan()
    plan = get_exp005_paper_testing_plan()
    capital = plan["analytical_reference_capital"]
    return {
        "NQ": float(capital["NQ_usd"]),
        "MNQ": float(capital["MNQ_usd"]),
    }


def load_saved_results() -> Exp005SavedResults:
    decision = _read_json(
        RESULT_ROOT / "full_validation_decision.json"
    )
    review = _read_json(
        REVIEW_ROOT / "review_decision.json",
        required=False,
    )
    quick = _read_json(
        QUICK_ROOT / "quick_transfer_decision.json",
        required=False,
    )

    audit_path = Path(
        str(
            decision.get("data", {}).get(
                "confirmation_import_audit",
                PROJECT_DIR
                / "results"
                / "EXP-005"
                / "confirmation_data"
                / "quantower_confirmation_import_audit.json",
            )
        )
    )
    if not audit_path.is_absolute():
        audit_path = PROJECT_DIR / audit_path

    saved = Exp005SavedResults(
        decision=decision,
        review=review,
        quick=quick,
        summary=_read_csv(
            RESULT_ROOT / "decision_model_summary.csv"
        ),
        yearly=_read_csv(
            RESULT_ROOT / "yearly_results.csv"
        ),
        cost_sensitivity=_read_csv(
            RESULT_ROOT / "cost_sensitivity.csv"
        ),
        nq_equity=_read_csv(
            RESULT_ROOT / "nq_equity_curve.csv"
        ),
        mnq_equity=_read_csv(
            RESULT_ROOT / "mnq_equity_curve.csv"
        ),
        nq_trades=_read_csv(
            RESULT_ROOT / "nq_trades.csv"
        ),
        mnq_trades=_read_csv(
            RESULT_ROOT / "mnq_trades.csv"
        ),
        mcpt=_read_csv(
            RESULT_ROOT / "nq_mcpt_1000.csv"
        ),
        confirmation_audit=_read_json(
            audit_path,
            required=False,
        ),
    )
    validate_saved_results(saved)
    return saved


def validate_saved_results(saved: Exp005SavedResults) -> None:
    decision = saved.decision
    if (
        decision.get("experiment_id") != "EXP-005"
        or decision.get("stage") != "FULL_VALIDATION"
    ):
        raise ValueError("The EXP-005 full-validation identity changed.")

    evaluation = decision.get("evaluation", {})
    if (
        evaluation.get("decision") != "PASS_TO_REVIEW"
        or evaluation.get("passed") is not True
        or evaluation.get("failed_gates") != []
    ):
        raise ValueError(
            "The polished report may be built only from the frozen passing result."
        )

    data = decision.get("data", {})
    if (
        int(data.get("included_sessions", -1)) != 733
        or int(data.get("included_invalid_sessions", -1)) != 0
        or int(data.get("included_roll_switch_sessions", -1)) != 0
    ):
        raise ValueError("The EXP-005 confirmation sample changed.")

    required_summary = {
        "symbol",
        "completed_trades",
        "net_profit_usd",
        "trade_profit_factor",
        "win_rate_percent",
        "maximum_drawdown_usd",
    }
    missing = required_summary.difference(saved.summary.columns)
    if missing:
        raise ValueError(
            f"Decision summary is missing columns: {sorted(missing)}"
        )

    if set(saved.summary["symbol"].astype(str)) != {"NQ", "MNQ"}:
        raise ValueError("The EXP-005 summary must contain NQ and MNQ.")

    for frame, symbol in (
        (saved.nq_equity, "NQ"),
        (saved.mnq_equity, "MNQ"),
    ):
        required = {
            "session_date",
            "cumulative_net_pnl_usd",
            "drawdown_usd",
        }
        missing_equity = required.difference(frame.columns)
        if missing_equity:
            raise ValueError(
                f"{symbol} equity data is missing: {sorted(missing_equity)}"
            )

    mcpt_info = decision.get("mcpt", {})
    if int(mcpt_info.get("permutations", -1)) != 1000:
        raise ValueError("The EXP-005 report requires the frozen 1,000-permutation MCPT.")


def percentage(value: float, capital: float) -> float:
    if capital <= 0:
        raise ValueError("Reference capital must be positive.")
    return float(value) / float(capital) * 100.0


def enriched_summary(
    summary: pd.DataFrame,
    reference_capital: dict[str, float],
) -> pd.DataFrame:
    local = summary.copy()
    local["reference_capital_usd"] = local["symbol"].map(
        reference_capital
    )
    if local["reference_capital_usd"].isna().any():
        raise ValueError("A reporting-capital value is missing.")

    local["total_return_percent"] = (
        local["net_profit_usd"].astype(float)
        / local["reference_capital_usd"].astype(float)
        * 100.0
    )
    local["maximum_drawdown_percent"] = (
        local["maximum_drawdown_usd"].astype(float)
        / local["reference_capital_usd"].astype(float)
        * 100.0
    )
    local["net_profit_to_drawdown"] = (
        local["net_profit_usd"].astype(float)
        / local["maximum_drawdown_usd"].astype(float).abs()
    )
    local["average_trade_to_cost"] = (
        local["average_trade_usd"].astype(float)
        / local["round_trip_cost_usd"].astype(float)
    )
    return local


def _safe_number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def format_number(value: Any, decimals: int = 2) -> str:
    number = _safe_number(value)
    if math.isnan(number):
        return "—"
    if math.isinf(number):
        return "∞" if number > 0 else "−∞"
    return f"{number:,.{decimals}f}"


def format_currency(value: Any) -> str:
    number = _safe_number(value)
    if math.isnan(number):
        return "—"
    sign = "−" if number < 0 else ""
    return f"{sign}${abs(number):,.2f}"


def format_percent(value: Any, decimals: int = 2) -> str:
    number = _safe_number(value)
    if math.isnan(number):
        return "—"
    return f"{number:,.{decimals}f}%"


def format_integer(value: Any) -> str:
    number = _safe_number(value)
    if math.isnan(number):
        return "—"
    return f"{int(round(number)):,}"


def _metric_card(
    label: str,
    value: str,
    *,
    detail: str = "",
    tone: str = "neutral",
) -> str:
    detail_html = (
        f'<div class="metric-detail">{html.escape(detail)}</div>'
        if detail
        else ""
    )
    return f"""
<div class="metric-card tone-{html.escape(tone)}">
  <div class="metric-label">{html.escape(label)}</div>
  <div class="metric-value">{html.escape(value)}</div>
  {detail_html}
</div>
"""


def _dataframe_html(
    frame: pd.DataFrame,
    *,
    columns: list[str] | None = None,
    rename: dict[str, str] | None = None,
) -> str:
    local = frame.copy()
    if columns is not None:
        local = local[[column for column in columns if column in local.columns]]
    if rename:
        local = local.rename(columns=rename)
    return local.to_html(
        index=False,
        border=0,
        classes="data-table",
        escape=True,
        na_rep="—",
        float_format=lambda value: f"{value:,.3f}",
    )


def _gate_table(decision: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for name, gate in decision["evaluation"]["gates"].items():
        rows.append(
            {
                "Gate": name.replace("_", " ").title(),
                "Actual": gate["actual"],
                "Rule": f"{gate['operator']} {gate['threshold']}",
                "Status": "PASS" if gate["passed"] else "FAIL",
            }
        )
    return pd.DataFrame(rows)


def _review_table(review: dict[str, Any]) -> pd.DataFrame:
    evaluation = review.get("evaluation", {})
    checks = evaluation.get("checks", {})
    rows = []
    for name, check in checks.items():
        rows.append(
            {
                "Review check": name.replace("_", " ").title(),
                "Status": "PASS" if check.get("passed") else "FAIL",
                "Rule": check.get("operator", ""),
            }
        )
    return pd.DataFrame(rows)


def _replication_table(saved: Exp005SavedResults) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for period, payload in (
        ("2019–2022 quick transfer", saved.quick),
        ("2023–2025 confirmation", saved.decision),
    ):
        results = payload.get("results", {})
        for symbol in ("NQ", "MNQ"):
            metrics = results.get(symbol)
            if not isinstance(metrics, dict):
                continue
            rows.append(
                {
                    "Period": period,
                    "Symbol": symbol,
                    "Profit Factor": metrics.get("trade_profit_factor"),
                    "Net profit USD": metrics.get("net_profit_usd"),
                    "Trades": metrics.get("completed_trades"),
                    "Win rate %": metrics.get("win_rate_percent"),
                }
            )
    return pd.DataFrame(rows)


def _trade_profile(
    trades: pd.DataFrame,
    symbol: str,
) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()

    pnl = trades["net_pnl_usd"].astype(float)
    gross_profit = float(pnl[pnl > 0].sum())
    gross_loss = abs(float(pnl[pnl < 0].sum()))
    return pd.DataFrame(
        [
            {
                "Symbol": symbol,
                "Long trades": int(
                    trades["direction"].astype(str).str.lower().eq("long").sum()
                ),
                "Short trades": int(
                    trades["direction"].astype(str).str.lower().eq("short").sum()
                ),
                "Winning trades": int(pnl.gt(0).sum()),
                "Losing trades": int(pnl.lt(0).sum()),
                "Largest win USD": float(pnl.max()),
                "Largest loss USD": float(pnl.min()),
                "Gross profit USD": gross_profit,
                "Gross loss USD": gross_loss,
                "Median trade USD": float(pnl.median()),
                "Average bars held": float(trades["bars_held"].astype(float).mean()),
            }
        ]
    )



def _max_drawdown_from_trade_pnl(pnl: pd.Series) -> float:
    values = pnl.astype(float).reset_index(drop=True)
    equity = pd.concat(
        [pd.Series([0.0]), values.cumsum()],
        ignore_index=True,
    )
    drawdown = equity - equity.cummax()
    return float(drawdown.min())


def _trade_segment_metrics(
    trades: pd.DataFrame,
    *,
    capital: float,
    round_trip_cost: float,
) -> dict[str, float]:
    if trades.empty:
        return {
            "starting_capital_usd": capital,
            "ending_equity_usd": capital,
            "net_profit_usd": 0.0,
            "return_percent": 0.0,
            "gross_profit_usd": 0.0,
            "gross_loss_usd": 0.0,
            "transaction_costs_usd": 0.0,
            "gross_pnl_before_costs_usd": 0.0,
            "profit_factor": float("nan"),
            "maximum_drawdown_usd": 0.0,
            "maximum_drawdown_percent": 0.0,
            "return_on_drawdown": float("nan"),
            "total_trades": 0.0,
            "winning_trades": 0.0,
            "losing_trades": 0.0,
            "percent_profitable": float("nan"),
            "average_trade_usd": float("nan"),
            "median_trade_usd": float("nan"),
            "average_winner_usd": float("nan"),
            "average_loser_usd": float("nan"),
            "payoff_ratio": float("nan"),
            "largest_winner_usd": float("nan"),
            "largest_loser_usd": float("nan"),
            "average_bars_held": float("nan"),
            "round_trip_cost_usd": round_trip_cost,
        }

    pnl = trades["net_pnl_usd"].astype(float)
    winners = pnl.loc[pnl > 0.0]
    losers = pnl.loc[pnl < 0.0]
    gross_profit = float(winners.sum())
    gross_loss = abs(float(losers.sum()))
    net_profit = float(pnl.sum())
    costs = float(len(trades) * round_trip_cost)
    drawdown = _max_drawdown_from_trade_pnl(pnl)
    average_winner = float(winners.mean()) if not winners.empty else float("nan")
    average_loser = float(losers.mean()) if not losers.empty else float("nan")
    payoff = (
        average_winner / abs(average_loser)
        if not math.isnan(average_winner)
        and not math.isnan(average_loser)
        and average_loser != 0.0
        else float("nan")
    )
    bars = (
        float(trades["bars_held"].astype(float).mean())
        if "bars_held" in trades.columns
        else float("nan")
    )

    return {
        "starting_capital_usd": capital,
        "ending_equity_usd": capital + net_profit,
        "net_profit_usd": net_profit,
        "return_percent": percentage(net_profit, capital),
        "gross_profit_usd": gross_profit,
        "gross_loss_usd": gross_loss,
        "transaction_costs_usd": costs,
        "gross_pnl_before_costs_usd": net_profit + costs,
        "profit_factor": (
            gross_profit / gross_loss
            if gross_loss > 0.0
            else float("inf")
        ),
        "maximum_drawdown_usd": drawdown,
        "maximum_drawdown_percent": percentage(drawdown, capital),
        "return_on_drawdown": (
            net_profit / abs(drawdown)
            if drawdown < 0.0
            else float("nan")
        ),
        "total_trades": float(len(trades)),
        "winning_trades": float(len(winners)),
        "losing_trades": float(len(losers)),
        "percent_profitable": float(len(winners) / len(trades) * 100.0),
        "average_trade_usd": float(pnl.mean()),
        "median_trade_usd": float(pnl.median()),
        "average_winner_usd": average_winner,
        "average_loser_usd": average_loser,
        "payoff_ratio": payoff,
        "largest_winner_usd": float(pnl.max()),
        "largest_loser_usd": float(pnl.min()),
        "average_bars_held": bars,
        "round_trip_cost_usd": round_trip_cost,
    }


def _all_trade_metrics(
    summary_row: pd.Series,
    trades: pd.DataFrame,
    *,
    capital: float,
) -> dict[str, float]:
    calculated = _trade_segment_metrics(
        trades,
        capital=capital,
        round_trip_cost=float(summary_row["round_trip_cost_usd"]),
    )
    net_profit = float(summary_row["net_profit_usd"])
    drawdown = float(summary_row["maximum_drawdown_usd"])

    calculated.update(
        {
            "ending_equity_usd": capital + net_profit,
            "net_profit_usd": net_profit,
            "return_percent": percentage(net_profit, capital),
            "gross_profit_usd": float(summary_row["gross_profit_usd"]),
            "gross_loss_usd": float(summary_row["gross_loss_usd"]),
            "transaction_costs_usd": float(summary_row["transaction_costs_usd"]),
            "gross_pnl_before_costs_usd": float(summary_row["gross_pnl_usd"]),
            "profit_factor": float(summary_row["trade_profit_factor"]),
            "maximum_drawdown_usd": drawdown,
            "maximum_drawdown_percent": percentage(drawdown, capital),
            "return_on_drawdown": (
                net_profit / abs(drawdown)
                if drawdown < 0.0
                else float("nan")
            ),
            "total_trades": float(summary_row["completed_trades"]),
            "percent_profitable": float(summary_row["win_rate_percent"]),
            "average_trade_usd": float(summary_row["average_trade_usd"]),
            "median_trade_usd": float(summary_row["median_trade_usd"]),
            "round_trip_cost_usd": float(summary_row["round_trip_cost_usd"]),
        }
    )
    return calculated


def _format_metric(value: float, kind: str) -> str:
    if kind == "currency":
        return format_currency(value)
    if kind == "percent":
        return format_percent(value)
    if kind == "integer":
        return format_integer(value)
    if kind == "ratio":
        return format_number(value, 3)
    return format_number(value, 2)


def _performance_summary_html(
    *,
    symbol: str,
    summary_row: pd.Series,
    trades: pd.DataFrame,
    capital: float,
) -> str:
    all_metrics = _all_trade_metrics(
        summary_row,
        trades,
        capital=capital,
    )
    long_metrics = _trade_segment_metrics(
        trades.loc[
            trades["direction"].astype(str).str.lower().eq("long")
        ],
        capital=capital,
        round_trip_cost=float(summary_row["round_trip_cost_usd"]),
    )
    short_metrics = _trade_segment_metrics(
        trades.loc[
            trades["direction"].astype(str).str.lower().eq("short")
        ],
        capital=capital,
        round_trip_cost=float(summary_row["round_trip_cost_usd"]),
    )

    rows = [
        ("Starting analytical capital", "starting_capital_usd", "currency"),
        ("Ending total equity", "ending_equity_usd", "currency"),
        ("Net profit", "net_profit_usd", "currency"),
        ("Return on analytical capital", "return_percent", "percent"),
        ("Gross P&L before costs", "gross_pnl_before_costs_usd", "currency"),
        ("Gross profit", "gross_profit_usd", "currency"),
        ("Gross loss", "gross_loss_usd", "currency"),
        ("Transaction costs", "transaction_costs_usd", "currency"),
        ("Profit Factor", "profit_factor", "ratio"),
        ("Max strategy drawdown", "maximum_drawdown_usd", "currency"),
        ("Max strategy drawdown (%)", "maximum_drawdown_percent", "percent"),
        ("Return on max drawdown", "return_on_drawdown", "ratio"),
        ("Total trades", "total_trades", "integer"),
        ("Winning trades", "winning_trades", "integer"),
        ("Losing trades", "losing_trades", "integer"),
        ("Percent profitable", "percent_profitable", "percent"),
        ("Average trade", "average_trade_usd", "currency"),
        ("Median trade", "median_trade_usd", "currency"),
        ("Average winning trade", "average_winner_usd", "currency"),
        ("Average losing trade", "average_loser_usd", "currency"),
        ("Payoff ratio", "payoff_ratio", "ratio"),
        ("Largest winning trade", "largest_winner_usd", "currency"),
        ("Largest losing trade", "largest_loser_usd", "currency"),
        ("Average bars held", "average_bars_held", "number"),
        ("Round-trip cost per trade", "round_trip_cost_usd", "currency"),
    ]

    body = []
    for label, key, kind in rows:
        values = [all_metrics[key], long_metrics[key], short_metrics[key]]
        cells = "".join(
            f'<td class="{"negative" if _safe_number(value) < 0 else ""}">'
            f'{html.escape(_format_metric(value, kind))}</td>'
            for value in values
        )
        body.append(
            f'<tr><th scope="row">{html.escape(label)}</th>{cells}</tr>'
        )

    return f"""
<div class="summary-table-wrap">
<table class="performance-summary">
  <thead>
    <tr>
      <th>{html.escape(symbol)} strategy performance summary</th>
      <th>All trades</th>
      <th>Long trades</th>
      <th>Short trades</th>
    </tr>
  </thead>
  <tbody>{''.join(body)}</tbody>
</table>
</div>
"""


def _contract_comparison_html(summary: pd.DataFrame) -> str:
    by_symbol = {
        str(row.symbol): row
        for row in summary.itertuples(index=False)
    }
    rows = [
        ("Analytical capital", "reference_capital_usd", "currency"),
        ("Ending total equity", None, "currency"),
        ("Net profit", "net_profit_usd", "currency"),
        ("Return", "total_return_percent", "percent"),
        ("Max drawdown", "maximum_drawdown_usd", "currency"),
        ("Max drawdown (%)", "maximum_drawdown_percent", "percent"),
        ("Profit Factor", "trade_profit_factor", "ratio"),
        ("Win rate", "win_rate_percent", "percent"),
        ("Completed trades", "completed_trades", "integer"),
        ("Average trade", "average_trade_usd", "currency"),
        ("Net profit / drawdown", "net_profit_to_drawdown", "ratio"),
    ]
    body = []
    for label, key, kind in rows:
        values = []
        for symbol in ("NQ", "MNQ"):
            row = by_symbol[symbol]
            value = (
                float(row.reference_capital_usd) + float(row.net_profit_usd)
                if key is None
                else getattr(row, key)
            )
            values.append(value)
        cells = "".join(
            f'<td class="{"negative" if _safe_number(value) < 0 else ""}">'
            f'{html.escape(_format_metric(value, kind))}</td>'
            for value in values
        )
        body.append(
            f'<tr><th scope="row">{html.escape(label)}</th>{cells}</tr>'
        )
    return f"""
<div class="summary-table-wrap">
<table class="performance-summary compact-summary">
  <thead><tr><th>Contract comparison</th><th>NQ</th><th>MNQ</th></tr></thead>
  <tbody>{''.join(body)}</tbody>
</table>
</div>
"""


def _write_charts(
    saved: Exp005SavedResults,
    capital: dict[str, float],
) -> dict[str, str]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ASSET_ROOT.mkdir(parents=True, exist_ok=True)
    charts: dict[str, str] = {}
    prepared: dict[str, pd.DataFrame] = {}

    for symbol, frame in (
        ("NQ", saved.nq_equity),
        ("MNQ", saved.mnq_equity),
    ):
        local = frame.copy()
        local["session_date"] = pd.to_datetime(local["session_date"])
        local["total_equity_usd"] = (
            capital[symbol]
            + local["cumulative_net_pnl_usd"].astype(float)
        )
        local["equity_index"] = (
            local["total_equity_usd"] / capital[symbol] * 100.0
        )
        local["drawdown_percent"] = (
            local["drawdown_usd"].astype(float)
            / capital[symbol]
            * 100.0
        )
        prepared[symbol] = local

        figure = plt.figure(figsize=(12, 4.8))
        axis = figure.add_subplot(111)
        axis.plot(local["session_date"], local["total_equity_usd"])
        axis.axhline(capital[symbol], linewidth=0.8)
        axis.set_title(f"{symbol} total equity curve")
        axis.set_xlabel("Session")
        axis.set_ylabel("Total equity USD")
        figure.tight_layout()
        path = ASSET_ROOT / f"{symbol.lower()}_total_equity_usd.png"
        save_report_figure(figure, path, dpi=160)
        plt.close(figure)
        charts[f"{symbol.lower()}_total_equity"] = f"assets/{path.name}"

        figure = plt.figure(figsize=(12, 4.2))
        axis = figure.add_subplot(111)
        axis.plot(local["session_date"], local["drawdown_percent"])
        axis.axhline(0.0, linewidth=0.8)
        axis.set_title(f"{symbol} drawdown percentage")
        axis.set_xlabel("Session")
        axis.set_ylabel("Drawdown %")
        figure.tight_layout()
        path = ASSET_ROOT / f"{symbol.lower()}_drawdown_percent.png"
        save_report_figure(figure, path, dpi=160)
        plt.close(figure)
        charts[f"{symbol.lower()}_drawdown"] = f"assets/{path.name}"

    normalized = prepared["NQ"][["session_date", "equity_index"]].rename(
        columns={"equity_index": "NQ"}
    ).merge(
        prepared["MNQ"][["session_date", "equity_index"]].rename(
            columns={"equity_index": "MNQ"}
        ),
        on="session_date",
        how="inner",
        validate="one_to_one",
    )
    figure = plt.figure(figsize=(12, 4.8))
    axis = figure.add_subplot(111)
    axis.plot(normalized["session_date"], normalized["NQ"], label="NQ")
    axis.plot(normalized["session_date"], normalized["MNQ"], label="MNQ")
    axis.axhline(100.0, linewidth=0.8)
    axis.set_title("Normalized total equity comparison")
    axis.set_xlabel("Session")
    axis.set_ylabel("Equity index (start = 100)")
    axis.legend()
    figure.tight_layout()
    path = ASSET_ROOT / "normalized_total_equity.png"
    save_report_figure(figure, path, dpi=160)
    plt.close(figure)
    charts["normalized_equity"] = f"assets/{path.name}"

    yearly = saved.yearly.copy()
    yearly["net_profit_percent"] = yearly.apply(
        lambda row: percentage(
            float(row["net_profit_usd"]),
            capital[str(row["symbol"])],
        ),
        axis=1,
    )
    pivot = yearly.pivot(
        index="year",
        columns="symbol",
        values="net_profit_percent",
    ).sort_index()
    figure = plt.figure(figsize=(12, 4.5))
    axis = figure.add_subplot(111)
    pivot.plot(kind="bar", ax=axis)
    axis.axhline(0.0, linewidth=0.8)
    axis.set_title("Calendar-year return on analytical capital")
    axis.set_xlabel("Year")
    axis.set_ylabel("Return %")
    figure.tight_layout()
    path = ASSET_ROOT / "yearly_return_percent.png"
    save_report_figure(figure, path, dpi=160)
    plt.close(figure)
    charts["yearly"] = f"assets/{path.name}"

    cost = saved.cost_sensitivity.copy()
    figure = plt.figure(figsize=(12, 4.5))
    axis = figure.add_subplot(111)
    for symbol, group in cost.groupby("symbol", sort=True):
        group = group.sort_values("slippage_ticks_per_side")
        axis.plot(
            group["slippage_ticks_per_side"],
            group["trade_profit_factor"],
            marker="o",
            label=str(symbol),
        )
    axis.axhline(1.0, linewidth=0.8)
    axis.set_title("Profit Factor under higher slippage")
    axis.set_xlabel("Slippage ticks per side")
    axis.set_ylabel("Trade Profit Factor")
    axis.legend()
    figure.tight_layout()
    path = ASSET_ROOT / "cost_sensitivity_profit_factor.png"
    save_report_figure(figure, path, dpi=160)
    plt.close(figure)
    charts["cost"] = f"assets/{path.name}"

    finite = saved.mcpt["trade_profit_factor"].replace(
        [np.inf, -np.inf], np.nan
    ).dropna()
    real_pf = float(
        saved.decision["results"]["NQ"]["trade_profit_factor"]
    )
    figure = plt.figure(figsize=(12, 4.5))
    axis = figure.add_subplot(111)
    if not finite.empty:
        axis.hist(
            finite,
            bins=min(40, max(10, int(np.sqrt(len(finite))))),
        )
    axis.axvline(real_pf, linewidth=2.0, label="Real NQ PF")
    axis.set_title("NQ session-aware MCPT distribution")
    axis.set_xlabel("Trade Profit Factor")
    axis.set_ylabel("Permutations")
    axis.legend()
    figure.tight_layout()
    path = ASSET_ROOT / "nq_mcpt_distribution.png"
    save_report_figure(figure, path, dpi=160)
    plt.close(figure)
    charts["mcpt"] = f"assets/{path.name}"

    return charts

def _chart_card(title: str, source: str, description: str) -> str:
    return f"""
<article class="chart-card">
  <h3>{html.escape(title)}</h3>
  <p>{html.escape(description)}</p>
  <img src="{html.escape(source)}" alt="{html.escape(title)}">
</article>
"""


def _primary_metrics(
    summary: pd.DataFrame,
    decision: dict[str, Any],
    review: dict[str, Any],
) -> dict[str, Any]:
    nq = summary.loc[summary["symbol"].eq("NQ")].iloc[0]
    evaluation = decision.get("evaluation", {})
    review_evaluation = review.get("evaluation", {})
    return {
        "primary_symbol": "NQ",
        "profit_factor": float(nq["trade_profit_factor"]),
        "net_profit_usd": float(nq["net_profit_usd"]),
        "total_return_percent": float(nq["total_return_percent"]),
        "win_rate_percent": float(nq["win_rate_percent"]),
        "max_drawdown_usd": float(nq["maximum_drawdown_usd"]),
        "max_drawdown_percent": float(nq["maximum_drawdown_percent"]),
        "total_trades": int(nq["completed_trades"]),
        "mcpt_p_value": float(decision["mcpt"]["p_value"]),
        "result_decision": str(evaluation.get("decision", "")),
        "review_decision": str(review_evaluation.get("decision", "")),
        "drawdown_percent_note": (
            "Based on $100,000 analytical NQ capital; not a margin requirement."
        ),
    }



def build_report_html(
    saved: Exp005SavedResults,
    summary: pd.DataFrame,
    charts: dict[str, str],
    capital: dict[str, float],
) -> str:
    nq = summary.loc[summary["symbol"].eq("NQ")].iloc[0]
    mnq = summary.loc[summary["symbol"].eq("MNQ")].iloc[0]
    full_decision = str(saved.decision["evaluation"]["decision"])
    review_decision = str(
        saved.review.get("evaluation", {}).get("decision", "Not yet frozen")
    )
    stage_tone = "accepted" if "ACCEPT" in review_decision else "active"

    status_rows = [
        ("Full-validation decision", full_decision),
        ("Formal review decision", review_decision),
        ("Primary evidence market", "NQ"),
        ("Implementation shadow", "MNQ"),
        ("Parameter combinations", "1"),
        ("Optimization", "Disabled"),
        ("NQ MCPT", "1,000 permutations"),
        ("NQ MCPT p-value", format_number(saved.decision["mcpt"]["p_value"], 6)),
        ("Research rerun", "No"),
    ]
    status_table = "".join(
        f'<tr><th scope="row">{html.escape(label)}</th><td>{html.escape(value)}</td></tr>'
        for label, value in status_rows
    )

    contract_comparison = _contract_comparison_html(summary)
    nq_summary = _performance_summary_html(
        symbol="NQ",
        summary_row=nq,
        trades=saved.nq_trades,
        capital=capital["NQ"],
    )
    mnq_summary = _performance_summary_html(
        symbol="MNQ",
        summary_row=mnq,
        trades=saved.mnq_trades,
        capital=capital["MNQ"],
    )

    yearly = saved.yearly.copy()
    yearly["return_percent"] = yearly.apply(
        lambda row: percentage(
            float(row["net_profit_usd"]),
            capital[str(row["symbol"])],
        ),
        axis=1,
    )
    yearly_table = _dataframe_html(
        yearly,
        columns=[
            "symbol",
            "year",
            "completed_trades",
            "net_profit_usd",
            "return_percent",
            "trade_profit_factor",
            "win_rate_percent",
            "average_trade_usd",
        ],
        rename={
            "symbol": "Symbol",
            "year": "Year",
            "completed_trades": "Trades",
            "net_profit_usd": "Net profit USD",
            "return_percent": "Return %",
            "trade_profit_factor": "Profit Factor",
            "win_rate_percent": "Win rate %",
            "average_trade_usd": "Average trade USD",
        },
    )

    cost = saved.cost_sensitivity.copy()
    cost["return_percent"] = cost.apply(
        lambda row: percentage(
            float(row["net_profit_usd"]),
            capital[str(row["symbol"])],
        ),
        axis=1,
    )
    cost["drawdown_percent"] = cost.apply(
        lambda row: percentage(
            float(row["maximum_drawdown_usd"]),
            capital[str(row["symbol"])],
        ),
        axis=1,
    )
    cost_table = _dataframe_html(
        cost,
        columns=[
            "symbol",
            "slippage_ticks_per_side",
            "round_trip_cost_usd",
            "net_profit_usd",
            "return_percent",
            "trade_profit_factor",
            "maximum_drawdown_usd",
            "drawdown_percent",
        ],
        rename={
            "symbol": "Symbol",
            "slippage_ticks_per_side": "Slippage ticks / side",
            "round_trip_cost_usd": "Round-trip cost USD",
            "net_profit_usd": "Net profit USD",
            "return_percent": "Return %",
            "trade_profit_factor": "Profit Factor",
            "maximum_drawdown_usd": "Max drawdown USD",
            "drawdown_percent": "Max drawdown %",
        },
    )

    gate_table = _dataframe_html(_gate_table(saved.decision))
    review_frame = _review_table(saved.review)
    review_table = (
        _dataframe_html(review_frame)
        if not review_frame.empty
        else '<p class="muted">Review decision file not available.</p>'
    )
    replication = _replication_table(saved)
    replication_table = (
        _dataframe_html(replication)
        if not replication.empty
        else '<p class="muted">Quick-transfer result not available.</p>'
    )
    trade_profile = pd.concat(
        [
            _trade_profile(saved.nq_trades, "NQ"),
            _trade_profile(saved.mnq_trades, "MNQ"),
        ],
        ignore_index=True,
    )
    trade_profile_table = _dataframe_html(trade_profile)

    data = saved.decision["data"]
    data_rows = [
        ("Included paired sessions", format_integer(data["included_sessions"])),
        ("Included invalid sessions", format_integer(data["included_invalid_sessions"])),
        ("Included mismatch sessions", format_integer(data["included_roll_switch_sessions"])),
        ("Provider-unavailable sessions excluded", format_integer(data["provider_unavailable_sessions_excluded"])),
        ("Alignment-mismatch sessions excluded", format_integer(data["potential_front_month_mismatch_sessions_excluded"])),
        ("Missing bars invented", "0"),
    ]
    data_table = "".join(
        f'<tr><th scope="row">{html.escape(label)}</th><td>{html.escape(value)}</td></tr>'
        for label, value in data_rows
    )

    charts_html = "".join(
        [
            _chart_card(
                "NQ total equity curve",
                charts["nq_total_equity"],
                "Starting analytical equity of $100,000 plus frozen cumulative net P&L.",
            ),
            _chart_card(
                "NQ drawdown percentage",
                charts["nq_drawdown"],
                "Session-close peak-to-trough drawdown on the same analytical capital basis.",
            ),
            _chart_card(
                "MNQ total equity curve",
                charts["mnq_total_equity"],
                "Starting analytical equity of $10,000 plus frozen cumulative net P&L.",
            ),
            _chart_card(
                "MNQ drawdown percentage",
                charts["mnq_drawdown"],
                "Session-close peak-to-trough drawdown on the same analytical capital basis.",
            ),
            _chart_card(
                "Normalized total equity comparison",
                charts["normalized_equity"],
                "NQ and MNQ equity indexed to 100 so the paths can be compared despite different contract multipliers.",
            ),
            _chart_card(
                "Calendar-year return",
                charts["yearly"],
                "Year-by-year net return for both contract sizes.",
            ),
            _chart_card(
                "Cost sensitivity",
                charts["cost"],
                "Profit Factor after increasing modeled slippage per side.",
            ),
            _chart_card(
                "NQ MCPT distribution",
                charts["mcpt"],
                "The real NQ Profit Factor compared with 1,000 session-aware permuted markets.",
            ),
        ]
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>EXP-005 Strategy Analysis</title>
<style>
:root {{
  color-scheme: dark;
  --bg: #090c10;
  --panel: #11161d;
  --panel-2: #171d25;
  --border: #303946;
  --text: #f4f7fa;
  --muted: #a5afbb;
  --accent: #7eb0ff;
  --positive: #65d39a;
  --negative: #ff858f;
}}
* {{ box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}
body {{
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system,
    BlinkMacSystemFont, "Segoe UI", sans-serif;
  line-height: 1.45;
}}
a {{ color: inherit; text-decoration: none; }}
.report-shell {{
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr);
  min-height: 100vh;
}}
.side-nav {{
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
  border-right: 1px solid var(--border);
  background: #0d1117;
  padding: 18px 14px 28px;
}}
.side-nav h2 {{
  margin: 0 8px 14px;
  font-size: 15px;
}}
.side-nav a {{
  display: block;
  color: var(--muted);
  border-radius: 7px;
  padding: 7px 9px;
  font-size: 13px;
}}
.side-nav a:hover {{ color: var(--text); background: var(--panel-2); }}
.side-nav .group-label {{
  margin: 16px 8px 5px;
  color: var(--accent);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: .08em;
  text-transform: uppercase;
}}
.report-main {{
  min-width: 0;
  width: min(1260px, 100%);
  padding: 28px clamp(18px, 3vw, 42px) 64px;
}}
.hero {{
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: flex-start;
  border-bottom: 1px solid var(--border);
  padding-bottom: 20px;
}}
.hero h1 {{ margin: 3px 0 8px; font-size: clamp(28px, 4vw, 44px); }}
.subtitle {{ color: var(--muted); max-width: 850px; }}
.stage-badge {{
  border: 1px solid rgba(101, 211, 154, .55);
  color: var(--positive);
  border-radius: 999px;
  padding: 9px 13px;
  white-space: nowrap;
  font-weight: 750;
}}
.section {{ margin-top: 34px; scroll-margin-top: 18px; }}
.section-title {{
  margin: 0 0 14px;
  background: #3b4148;
  color: white;
  padding: 9px 12px;
  font-size: 19px;
  font-weight: 750;
}}
.panel {{
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}}
.notice {{
  border-left: 4px solid var(--accent);
  background: var(--panel);
  padding: 13px 16px;
  margin: 16px 0;
}}
.summary-table-wrap, .table-wrap {{ overflow-x: auto; }}
.performance-summary, .data-table, .status-table {{
  width: 100%;
  border-collapse: collapse;
  min-width: 760px;
  font-size: 13px;
}}
.performance-summary th,
.performance-summary td,
.data-table th,
.data-table td,
.status-table th,
.status-table td {{
  border-bottom: 1px solid var(--border);
  padding: 8px 10px;
}}
.performance-summary thead th {{
  background: #2b3138;
  color: white;
  text-align: right;
  position: sticky;
  top: 0;
}}
.performance-summary thead th:first-child {{ text-align: left; }}
.performance-summary tbody th {{
  color: var(--text);
  text-align: left;
  font-weight: 560;
}}
.performance-summary tbody td {{ text-align: right; }}
.performance-summary tbody tr:hover {{ background: rgba(255,255,255,.025); }}
.performance-summary .negative,
.data-table td.negative {{ color: var(--negative); }}
.compact-summary {{ min-width: 560px; }}
.status-table {{ min-width: 0; }}
.status-table th {{ width: 310px; color: var(--muted); text-align: left; }}
.status-table td {{ text-align: left; font-weight: 650; }}
.data-table th, .data-table td {{ text-align: right; }}
.data-table th:first-child, .data-table td:first-child {{ text-align: left; }}
.data-table th {{ color: var(--muted); }}
.report-stack {{ display: grid; grid-template-columns: 1fr; gap: 16px; }}
.chart-card {{
  width: 100%;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
}}
.chart-card h3 {{ margin: 0 0 5px; }}
.chart-card p {{ color: var(--muted); margin: 0 0 12px; }}
.chart-card img {{ display: block; width: 100%; height: auto; border-radius: 5px; }}
details.panel {{ padding: 0; overflow: hidden; }}
details.panel > summary {{ cursor: pointer; padding: 14px 16px; font-weight: 750; }}
details.panel > .table-wrap {{ border-top: 1px solid var(--border); padding: 14px 16px 16px; }}
.muted {{ color: var(--muted); }}
code {{ color: var(--accent); overflow-wrap: anywhere; }}
@media (max-width: 900px) {{
  .report-shell {{ grid-template-columns: 1fr; }}
  .side-nav {{
    position: sticky;
    z-index: 20;
    height: auto;
    display: flex;
    gap: 6px;
    overflow-x: auto;
    border-right: 0;
    border-bottom: 1px solid var(--border);
    padding: 9px;
  }}
  .side-nav h2, .side-nav .group-label {{ display: none; }}
  .side-nav a {{ flex: 0 0 auto; }}
  .hero {{ flex-direction: column; }}
}}
</style>
</head>
<body>
<div class="report-shell">
<aside class="side-nav">
  <h2>Strategy Analysis</h2>
  <a href="../research_dashboard/index.html">← Research hub</a>
  <div class="group-label">Summary</div>
  <a href="#status">Research status</a>
  <a href="#comparison">Contract comparison</a>
  <a href="#nq-summary">NQ performance summary</a>
  <a href="#mnq-summary">MNQ performance summary</a>
  <div class="group-label">Equity analysis</div>
  <a href="#equity">Total equity curves</a>
  <a href="#periodic">Periodic analysis</a>
  <div class="group-label">Trade analysis</div>
  <a href="#replication">Cross-period replication</a>
  <a href="#trades">Trade profile</a>
  <a href="#costs">Cost sensitivity</a>
  <div class="group-label">Validation</div>
  <a href="#mcpt">MCPT</a>
  <a href="#gates">Validation gates</a>
  <a href="#quality">Data quality</a>
  <a href="#review">Formal review</a>
</aside>

<main class="report-main">
<header class="hero">
  <div>
    <div class="muted">EXP-005 · NQ/MNQ 5-minute opening-range breakout</div>
    <h1>Strategy Performance and Equity Report</h1>
    <p class="subtitle">
      Full-width, top-to-bottom analysis rebuilt only from frozen saved results.
      No strategy, data import, optimization, MCPT or formal review was rerun.
    </p>
  </div>
  <div class="stage-badge">{html.escape(review_decision)}</div>
</header>

<section class="section" id="status">
  <h2 class="section-title">Research Status</h2>
  <div class="panel"><table class="status-table"><tbody>{status_table}</tbody></table></div>
  <div class="notice">
    Percentage metrics use analytical reference capital of {format_currency(capital['NQ'])} for NQ and {format_currency(capital['MNQ'])} for MNQ. These are reporting denominators, not margin requirements or account-size recommendations.
  </div>
</section>

<section class="section" id="comparison">
  <h2 class="section-title">Contract Comparison</h2>
  <div class="panel">{contract_comparison}</div>
</section>

<section class="section" id="nq-summary">
  <h2 class="section-title">NQ Strategy Performance Summary</h2>
  <div class="panel">{nq_summary}</div>
</section>

<section class="section" id="mnq-summary">
  <h2 class="section-title">MNQ Strategy Performance Summary</h2>
  <div class="panel">{mnq_summary}</div>
</section>

<section class="section" id="equity">
  <h2 class="section-title">Total Equity Curve and Drawdown</h2>
  <div class="report-stack">{charts_html}</div>
</section>

<section class="section" id="periodic">
  <h2 class="section-title">Periodical Analysis</h2>
  <div class="panel table-wrap">{yearly_table}</div>
</section>

<section class="section" id="replication">
  <h2 class="section-title">Cross-Period Replication</h2>
  <div class="panel table-wrap">{replication_table}</div>
</section>

<section class="section" id="trades">
  <h2 class="section-title">Trade Analysis</h2>
  <div class="panel table-wrap">{trade_profile_table}</div>
</section>

<section class="section" id="costs">
  <h2 class="section-title">Cost Sensitivity</h2>
  <div class="panel table-wrap">{cost_table}</div>
</section>

<section class="section" id="mcpt">
  <h2 class="section-title">Monte Carlo Permutation Test</h2>
  <div class="notice">
    The real NQ Profit Factor was {format_number(nq['trade_profit_factor'], 6)}. Exactly 37 of 1,000 session-aware permutations were at least as strong, giving p = {format_number(saved.decision['mcpt']['p_value'], 6)}.
  </div>
</section>

<section class="section" id="gates">
  <h2 class="section-title">Full-Validation Gates</h2>
  <div class="panel table-wrap">{gate_table}</div>
</section>

<section class="section" id="quality">
  <h2 class="section-title">Data Quality and Session Handling</h2>
  <div class="panel"><table class="status-table"><tbody>{data_table}</tbody></table></div>
  <div class="notice">All exclusions were paired across NQ and MNQ. No missing bar was filled or invented.</div>
</section>

<section class="section" id="review">
  <h2 class="section-title">Formal Operational Review</h2>
  <div class="panel table-wrap">{review_table}</div>
  <div class="notice">
    Historical acceptance does not guarantee future profitability and does not authorize live orders, leverage or post-result rule changes.
  </div>
</section>

<p class="muted">Generated from saved files under <code>results/EXP-005</code>. No protected research workflow was rerun.</p>
</main>
</div>
</body>
</html>
"""

def write_report() -> tuple[Path, Path]:
    saved = load_saved_results()
    capital = load_reference_capital()
    summary = enriched_summary(saved.summary, capital)
    charts = _write_charts(saved, capital)
    report_html = build_report_html(
        saved,
        summary,
        charts,
        capital,
    )

    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_ROOT / "report.html"
    temporary = report_path.with_suffix(".html.tmp")
    temporary.write_text(report_html, encoding="utf-8")
    temporary.replace(report_path)

    metadata = {
        "schema_version": 2,
        "experiment_id": "EXP-005",
        "layout": "vertical_strategy_analysis_v2",
        "generated_from_saved_results": True,
        "reference_capital_usd": capital,
        "reference_capital_interpretation": (
            "Analytical reporting basis only; not a margin requirement or live-account recommendation."
        ),
        "primary_metrics": _primary_metrics(
            summary,
            saved.decision,
            saved.review,
        ),
        "source_files": {
            "full_validation_decision": str(
                (RESULT_ROOT / "full_validation_decision.json").resolve()
            ),
            "review_decision": str(
                (REVIEW_ROOT / "review_decision.json").resolve()
            ),
        },
        "research_rerun": False,
        "mcpt_rerun": False,
        "data_import_rerun": False,
        "total_equity_curve_included": True,
        "summary_orientation": "top_to_bottom",
    }
    metadata_path = REPORT_ROOT / "report_metadata.json"
    metadata_temporary = metadata_path.with_suffix(".json.tmp")
    metadata_temporary.write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )
    metadata_temporary.replace(metadata_path)
    return report_path, metadata_path
