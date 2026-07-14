from __future__ import annotations

from dataclasses import dataclass
import html
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


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


def _write_charts(
    saved: Exp005SavedResults,
    capital: dict[str, float],
) -> dict[str, str]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ASSET_ROOT.mkdir(parents=True, exist_ok=True)
    charts: dict[str, str] = {}

    for symbol, frame in (
        ("NQ", saved.nq_equity),
        ("MNQ", saved.mnq_equity),
    ):
        local = frame.copy()
        local["session_date"] = pd.to_datetime(local["session_date"])
        local["return_percent"] = (
            local["cumulative_net_pnl_usd"].astype(float)
            / capital[symbol]
            * 100.0
        )
        local["drawdown_percent"] = (
            local["drawdown_usd"].astype(float)
            / capital[symbol]
            * 100.0
        )

        figure = plt.figure(figsize=(10, 4.5))
        axis = figure.add_subplot(111)
        axis.plot(local["session_date"], local["return_percent"])
        axis.axhline(0.0, linewidth=0.8)
        axis.set_title(f"{symbol} cumulative return on analytical capital")
        axis.set_xlabel("Session")
        axis.set_ylabel("Return %")
        figure.tight_layout()
        path = ASSET_ROOT / f"{symbol.lower()}_return_percent.png"
        figure.savefig(path, dpi=150)
        plt.close(figure)
        charts[f"{symbol.lower()}_return"] = f"assets/{path.name}"

        figure = plt.figure(figsize=(10, 4.5))
        axis = figure.add_subplot(111)
        axis.plot(local["session_date"], local["drawdown_percent"])
        axis.axhline(0.0, linewidth=0.8)
        axis.set_title(f"{symbol} drawdown on analytical capital")
        axis.set_xlabel("Session")
        axis.set_ylabel("Drawdown %")
        figure.tight_layout()
        path = ASSET_ROOT / f"{symbol.lower()}_drawdown_percent.png"
        figure.savefig(path, dpi=150)
        plt.close(figure)
        charts[f"{symbol.lower()}_drawdown"] = f"assets/{path.name}"

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
    figure = plt.figure(figsize=(10, 4.5))
    axis = figure.add_subplot(111)
    pivot.plot(kind="bar", ax=axis)
    axis.axhline(0.0, linewidth=0.8)
    axis.set_title("Calendar-year return on analytical capital")
    axis.set_xlabel("Year")
    axis.set_ylabel("Return %")
    figure.tight_layout()
    path = ASSET_ROOT / "yearly_return_percent.png"
    figure.savefig(path, dpi=150)
    plt.close(figure)
    charts["yearly"] = f"assets/{path.name}"

    cost = saved.cost_sensitivity.copy()
    figure = plt.figure(figsize=(10, 4.5))
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
    figure.savefig(path, dpi=150)
    plt.close(figure)
    charts["cost"] = f"assets/{path.name}"

    finite = saved.mcpt["trade_profit_factor"].replace(
        [np.inf, -np.inf], np.nan
    ).dropna()
    real_pf = float(
        saved.decision["results"]["NQ"]["trade_profit_factor"]
    )
    figure = plt.figure(figsize=(10, 4.5))
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
    figure.savefig(path, dpi=150)
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

    overview_cards = "".join(
        [
            _metric_card(
                "NQ net profit",
                format_currency(nq["net_profit_usd"]),
                detail=format_percent(nq["total_return_percent"]),
                tone="positive",
            ),
            _metric_card(
                "NQ max drawdown",
                format_currency(nq["maximum_drawdown_usd"]),
                detail=format_percent(nq["maximum_drawdown_percent"]),
                tone="negative",
            ),
            _metric_card(
                "NQ Profit Factor",
                format_number(nq["trade_profit_factor"], 3),
                detail="Primary transfer evidence",
                tone="positive",
            ),
            _metric_card(
                "NQ win rate",
                format_percent(nq["win_rate_percent"]),
                detail=f"{format_integer(nq['completed_trades'])} completed trades",
            ),
            _metric_card(
                "MCPT p-value",
                format_number(saved.decision["mcpt"]["p_value"], 4),
                detail="1,000 session-aware permutations",
                tone="positive",
            ),
            _metric_card(
                "Profitable NQ years",
                format_integer(
                    saved.decision["results"]["profitable_nq_calendar_years"]
                ),
                detail="2023, 2024 and 2025",
                tone="positive",
            ),
        ]
    )

    contract_cards = "".join(
        [
            _metric_card(
                "MNQ net profit",
                format_currency(mnq["net_profit_usd"]),
                detail=format_percent(mnq["total_return_percent"]),
                tone="positive",
            ),
            _metric_card(
                "MNQ max drawdown",
                format_currency(mnq["maximum_drawdown_usd"]),
                detail=format_percent(mnq["maximum_drawdown_percent"]),
                tone="negative",
            ),
            _metric_card(
                "MNQ Profit Factor",
                format_number(mnq["trade_profit_factor"], 3),
                detail="Contract-size implementation check",
                tone="positive",
            ),
            _metric_card(
                "MNQ win rate",
                format_percent(mnq["win_rate_percent"]),
                detail=f"{format_integer(mnq['completed_trades'])} completed trades",
            ),
        ]
    )

    summary_table = _dataframe_html(
        summary,
        columns=[
            "symbol",
            "reference_capital_usd",
            "net_profit_usd",
            "total_return_percent",
            "maximum_drawdown_usd",
            "maximum_drawdown_percent",
            "trade_profit_factor",
            "win_rate_percent",
            "completed_trades",
            "average_trade_usd",
            "round_trip_cost_usd",
            "net_profit_to_drawdown",
        ],
        rename={
            "symbol": "Symbol",
            "reference_capital_usd": "Analytical capital USD",
            "net_profit_usd": "Net profit USD",
            "total_return_percent": "Return %",
            "maximum_drawdown_usd": "Max drawdown USD",
            "maximum_drawdown_percent": "Max drawdown %",
            "trade_profit_factor": "Profit Factor",
            "win_rate_percent": "Win rate %",
            "completed_trades": "Trades",
            "average_trade_usd": "Average trade USD",
            "round_trip_cost_usd": "Round-trip cost USD",
            "net_profit_to_drawdown": "Net / drawdown",
        },
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
    data_cards = "".join(
        [
            _metric_card(
                "Included sessions",
                format_integer(data["included_sessions"]),
                detail="Complete paired NQ/MNQ sessions",
            ),
            _metric_card(
                "Invalid included",
                format_integer(data["included_invalid_sessions"]),
                tone="positive",
            ),
            _metric_card(
                "Provider gaps excluded",
                format_integer(data["provider_unavailable_sessions_excluded"]),
            ),
            _metric_card(
                "Alignment days excluded",
                format_integer(
                    data["potential_front_month_mismatch_sessions_excluded"]
                ),
            ),
        ]
    )

    chart_html = "".join(
        [
            _chart_card(
                "NQ cumulative return",
                charts["nq_return"],
                "Cumulative NQ net P&L divided by the fixed $100,000 analytical capital basis.",
            ),
            _chart_card(
                "NQ drawdown percentage",
                charts["nq_drawdown"],
                "Peak-to-trough drawdown as a percentage of the same analytical capital basis.",
            ),
            _chart_card(
                "MNQ cumulative return",
                charts["mnq_return"],
                "Cumulative MNQ net P&L divided by the fixed $10,000 analytical capital basis.",
            ),
            _chart_card(
                "MNQ drawdown percentage",
                charts["mnq_drawdown"],
                "Peak-to-trough drawdown as a percentage of the same analytical capital basis.",
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
<title>EXP-005 Research Report</title>
<style>
:root {{
  color-scheme: dark;
  --bg: #080a0d;
  --panel: #11151a;
  --panel-2: #151a20;
  --border: #2a313a;
  --text: #f4f6f8;
  --muted: #9da7b3;
  --accent: #74a7ff;
  --positive: #61d095;
  --negative: #ff7a85;
  --warning: #f3c969;
}}
* {{ box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}
body {{
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system,
    BlinkMacSystemFont, "Segoe UI", sans-serif;
  line-height: 1.5;
}}
a {{ color: inherit; }}
.page {{
  width: min(1240px, 100%);
  margin: 0 auto;
  padding: clamp(18px, 3vw, 38px);
}}
.report-nav {{
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding: 10px 0;
  margin-bottom: 20px;
  background: rgba(8, 10, 13, 0.94);
  backdrop-filter: blur(12px);
}}
.report-nav a {{
  flex: 0 0 auto;
  text-decoration: none;
  color: var(--muted);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 7px 12px;
  font-size: 13px;
}}
.report-nav a:hover {{ color: var(--text); border-color: var(--accent); }}
.hero {{
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 20px;
  align-items: start;
  margin-bottom: 22px;
}}
.hero h1 {{ margin: 0; font-size: clamp(28px, 4vw, 44px); line-height: 1.08; }}
.subtitle {{ color: var(--muted); margin-top: 10px; max-width: 820px; }}
.stage-badge {{
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 9px 14px;
  font-weight: 700;
  white-space: nowrap;
}}
.stage-accepted {{ border-color: rgba(97, 208, 149, .6); color: var(--positive); }}
.stage-active {{ border-color: rgba(116, 167, 255, .6); color: var(--accent); }}
.notice {{
  background: var(--panel);
  border: 1px solid var(--border);
  border-left: 4px solid var(--accent);
  border-radius: 10px;
  padding: 16px 18px;
  margin: 16px 0;
}}
.notice p {{ margin: 6px 0; }}
.section {{ margin-top: 34px; scroll-margin-top: 72px; }}
.section-header {{
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: end;
  border-bottom: 1px solid var(--border);
  padding-bottom: 10px;
  margin-bottom: 16px;
}}
.section-header h2 {{ margin: 0; font-size: clamp(21px, 2.5vw, 29px); }}
.section-kicker {{ color: var(--muted); font-size: 13px; }}
.metric-grid {{
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}}
.metric-grid.four {{ grid-template-columns: repeat(4, minmax(0, 1fr)); }}
.metric-card {{
  min-width: 0;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px;
}}
.metric-label {{ color: var(--muted); font-size: 13px; }}
.metric-value {{ margin-top: 5px; font-size: clamp(22px, 2.4vw, 30px); font-weight: 760; }}
.metric-detail {{ margin-top: 6px; color: var(--muted); font-size: 12px; }}
.tone-positive .metric-value {{ color: var(--positive); }}
.tone-negative .metric-value {{ color: var(--negative); }}
.chart-grid {{
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}}
.chart-card, .panel {{
  min-width: 0;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 18px;
}}
.chart-card h3, .panel h3 {{ margin: 0 0 8px; }}
.chart-card p {{ color: var(--muted); margin: 0 0 12px; }}
.chart-card img {{ display: block; width: 100%; height: auto; border-radius: 8px; }}
.table-wrap {{ overflow-x: auto; }}
.data-table {{ width: 100%; border-collapse: collapse; min-width: 780px; font-size: 13px; }}
.data-table th, .data-table td {{ padding: 9px 10px; border-bottom: 1px solid var(--border); text-align: right; }}
.data-table th:first-child, .data-table td:first-child {{ text-align: left; }}
.data-table th {{ color: var(--muted); }}
details.panel {{ padding: 0; overflow: hidden; }}
details.panel > summary {{ cursor: pointer; padding: 16px 18px; font-weight: 750; }}
details.panel > .table-wrap, details.panel > .detail-body {{ border-top: 1px solid var(--border); padding: 14px 18px 18px; }}
.two-column {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }}
.muted {{ color: var(--muted); }}
code {{ color: var(--accent); overflow-wrap: anywhere; }}
@media (max-width: 850px) {{
  .hero {{ grid-template-columns: 1fr; }}
  .metric-grid, .metric-grid.four, .chart-grid, .two-column {{ grid-template-columns: 1fr; }}
}}
</style>
</head>
<body>
<div class="page">
<nav class="report-nav">
  <a href="../research_dashboard/index.html">Research hub</a>
  <a href="#overview">Overview</a>
  <a href="#replication">Replication</a>
  <a href="#performance">Performance</a>
  <a href="#risk">Risk</a>
  <a href="#robustness">Robustness</a>
  <a href="#quality">Data quality</a>
  <a href="#review">Review</a>
  <a href="../EXP-005-full-validation/report.html">Original validation report</a>
</nav>

<header class="hero" id="overview">
  <div>
    <div class="section-kicker">EXP-005 · NQ/MNQ 5-minute opening-range breakout</div>
    <h1>Locked Transfer Research Report</h1>
    <p class="subtitle">
      A polished report rebuilt entirely from frozen saved results. The strategy,
      confirmation import, quick transfer, MCPT and formal review were not rerun.
    </p>
  </div>
  <div class="stage-badge stage-{stage_tone}">{html.escape(review_decision)}</div>
</header>

<div class="notice">
  <p><strong>Full-validation decision:</strong> {html.escape(full_decision)}</p>
  <p><strong>Formal review decision:</strong> {html.escape(review_decision)}</p>
  <p><strong>Percentage basis:</strong> NQ {format_currency(capital['NQ'])}; MNQ {format_currency(capital['MNQ'])}. These are analytical reporting denominators, not margin requirements or live-account recommendations.</p>
</div>

<section class="section">
  <div class="section-header"><h2>NQ confirmation overview</h2><span class="section-kicker">Primary evidence market</span></div>
  <div class="metric-grid">{overview_cards}</div>
</section>

<section class="section">
  <div class="section-header"><h2>MNQ implementation overview</h2><span class="section-kicker">Contract-size and cost consistency check</span></div>
  <div class="metric-grid four">{contract_cards}</div>
</section>

<section class="section" id="replication">
  <div class="section-header"><h2>Cross-period replication</h2><span class="section-kicker">Unchanged rules across two protected periods</span></div>
  <div class="panel table-wrap">{replication_table}</div>
</section>

<section class="section" id="performance">
  <div class="section-header"><h2>Performance and percentage context</h2><span class="section-kicker">USD and analytical-capital percentages shown together</span></div>
  <div class="panel table-wrap">{summary_table}</div>
  <div class="chart-grid" style="margin-top:14px;">{chart_html}</div>
</section>

<section class="section" id="risk">
  <div class="section-header"><h2>Trade and calendar-year profile</h2><span class="section-kicker">Payoff, direction and yearly consistency</span></div>
  <div class="two-column">
    <div class="panel table-wrap">{trade_profile_table}</div>
    <div class="panel table-wrap">{yearly_table}</div>
  </div>
</section>

<section class="section" id="robustness">
  <div class="section-header"><h2>Robustness evidence</h2><span class="section-kicker">Costs, locked gates and randomized markets</span></div>
  <details class="panel" open><summary>Cost sensitivity</summary><div class="table-wrap">{cost_table}</div></details>
  <details class="panel"><summary>Full-validation gates</summary><div class="table-wrap">{gate_table}</div></details>
</section>

<section class="section" id="quality">
  <div class="section-header"><h2>Data integrity</h2><span class="section-kicker">Only complete, aligned sessions were included</span></div>
  <div class="metric-grid four">{data_cards}</div>
  <div class="notice">
    <p>733 paired sessions were included. Two provider-unavailable sessions and nine NQ/MNQ alignment-mismatch sessions were excluded from both symbols. No missing bars were invented.</p>
  </div>
</section>

<section class="section" id="review">
  <div class="section-header"><h2>Formal operational review</h2><span class="section-kicker">Read-only checks performed after validation</span></div>
  <details class="panel" open><summary>Review checks</summary><div class="table-wrap">{review_table}</div></details>
  <div class="notice">
    <p>NQ is the primary evidence market. MNQ is a contract-size and cost implementation check, not independent market evidence.</p>
    <p>Historical acceptance does not guarantee future profitability and does not authorize live orders, leverage or post-result rule changes.</p>
  </div>
</section>

<p class="muted">Generated from saved files under <code>results/EXP-005</code>. No protected research workflow was rerun.</p>
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
        "schema_version": 1,
        "experiment_id": "EXP-005",
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
    }
    metadata_path = REPORT_ROOT / "report_metadata.json"
    metadata_temporary = metadata_path.with_suffix(".json.tmp")
    metadata_temporary.write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )
    metadata_temporary.replace(metadata_path)
    return report_path, metadata_path
