from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd


CORE_SUMMARY_COLUMNS = (
    "total_return_percent",
    "max_drawdown_percent",
    "trade_profit_factor",
    "total_trades",
    "win_rate_percent",
    "average_trade_percent",
    "exposure_percent",
)

ADVANCED_SUMMARY_COLUMNS = (
    "ending_capital",
    "average_holding_hours",
    "long_trades",
    "short_trades",
    "long_net_profit",
    "short_net_profit",
)

CORE_DIAGNOSTIC_COLUMNS = (
    "total_trades",
    "win_rate_percent",
    "trade_profit_factor",
    "average_winner_percent",
    "average_loser_percent",
    "payoff_ratio",
    "largest_loss_percent",
    "max_consecutive_losses",
)

ADVANCED_DIAGNOSTIC_COLUMNS = (
    "largest_win_percent",
    "fifth_percentile_trade_percent",
    "top_1_loss_share_percent",
    "top_5_loss_share_percent",
    "max_consecutive_wins",
    "average_winner_holding_hours",
    "average_loser_holding_hours",
)

COLUMN_LABELS = {
    "ending_capital": "Ending capital",
    "total_return_percent": "Return",
    "max_drawdown_percent": "Max drawdown",
    "total_trades": "Trades",
    "win_rate_percent": "Win rate",
    "trade_profit_factor": "Trade PF",
    "average_trade_percent": "Avg trade",
    "average_holding_hours": "Avg hold",
    "exposure_percent": "Exposure",
    "long_trades": "Long trades",
    "short_trades": "Short trades",
    "long_net_profit": "Long net P&L",
    "short_net_profit": "Short net P&L",
    "average_winner_percent": "Avg winner",
    "average_loser_percent": "Avg loser",
    "payoff_ratio": "Payoff ratio",
    "largest_win_percent": "Largest win",
    "largest_loss_percent": "Largest loss",
    "fifth_percentile_trade_percent": "5th percentile",
    "top_1_loss_share_percent": "Top loss share",
    "top_5_loss_share_percent": "Top 5 loss share",
    "max_consecutive_wins": "Max wins in row",
    "max_consecutive_losses": "Max losses in row",
    "average_winner_holding_hours": "Winner avg hold",
    "average_loser_holding_hours": "Loser avg hold",
    "test": "Test",
    "side": "Side",
    "net_profit_cash": "Net P&L",
}

PERCENT_COLUMNS = {
    "total_return_percent",
    "max_drawdown_percent",
    "win_rate_percent",
    "average_trade_percent",
    "exposure_percent",
    "average_winner_percent",
    "average_loser_percent",
    "largest_win_percent",
    "largest_loss_percent",
    "fifth_percentile_trade_percent",
    "top_1_loss_share_percent",
    "top_5_loss_share_percent",
}

CURRENCY_COLUMNS = {
    "ending_capital",
    "long_net_profit",
    "short_net_profit",
    "net_profit_cash",
}

INTEGER_COLUMNS = {
    "total_trades",
    "long_trades",
    "short_trades",
    "max_consecutive_wins",
    "max_consecutive_losses",
}

HOURS_COLUMNS = {
    "average_holding_hours",
    "average_winner_holding_hours",
    "average_loser_holding_hours",
}


def safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def format_number(value: Any, decimals: int = 3) -> str:
    number = safe_float(value)

    if np.isnan(number):
        return "—"
    if np.isposinf(number):
        return "∞"
    if np.isneginf(number):
        return "−∞"

    return f"{number:,.{decimals}f}"


def format_percent(value: Any, decimals: int = 2) -> str:
    number = safe_float(value)

    if np.isnan(number):
        return "—"

    return f"{number:,.{decimals}f}%"


def format_integer(value: Any) -> str:
    number = safe_float(value)

    if np.isnan(number):
        return "—"

    return f"{int(round(number)):,}"


def format_currency(value: Any) -> str:
    number = safe_float(value)

    if np.isnan(number):
        return "—"

    sign = "−" if number < 0 else ""
    return f"{sign}{abs(number):,.0f}"


def format_hours(value: Any) -> str:
    number = safe_float(value)

    if np.isnan(number):
        return "—"

    return f"{number:,.1f}h"


def format_cell(column: str, value: Any) -> str:
    if column in PERCENT_COLUMNS:
        return format_percent(value)
    if column in CURRENCY_COLUMNS:
        return format_currency(value)
    if column in INTEGER_COLUMNS:
        return format_integer(value)
    if column in HOURS_COLUMNS:
        return format_hours(value)
    if column in {"trade_profit_factor", "payoff_ratio"}:
        return format_number(value, 3)
    if pd.isna(value):
        return "—"

    return str(value)


def _available_columns(
    frame: pd.DataFrame,
    requested: Iterable[str],
) -> list[str]:
    return [
        column
        for column in requested
        if column in frame.columns
    ]


def dataframe_table_html(
    frame: pd.DataFrame,
    *,
    columns: Iterable[str],
    include_index: bool = True,
    compact: bool = False,
    table_class: str = "data-table",
) -> str:
    selected_columns = _available_columns(
        frame,
        columns,
    )

    if frame.empty or not selected_columns:
        return '<p class="muted">No data available.</p>'

    table = frame[selected_columns].copy()

    header_cells: list[str] = []

    if include_index:
        index_label = frame.index.name or "Test"
        header_cells.append(
            f"<th>{html.escape(str(index_label).title())}</th>"
        )

    for column in selected_columns:
        header_cells.append(
            f"<th>{html.escape(COLUMN_LABELS.get(column, column.replace('_', ' ').title()))}</th>"
        )

    body_rows: list[str] = []

    for index_value, row in table.iterrows():
        cells: list[str] = []

        if include_index:
            cells.append(
                f'<th scope="row">{html.escape(str(index_value))}</th>'
            )

        for column in selected_columns:
            formatted = format_cell(
                column,
                row[column],
            )
            cells.append(
                f"<td>{html.escape(formatted)}</td>"
            )

        body_rows.append(
            "<tr>" + "".join(cells) + "</tr>"
        )

    compact_class = " compact" if compact else ""

    return (
        f'<table class="{table_class}{compact_class}">'
        "<thead><tr>"
        + "".join(header_cells)
        + "</tr></thead><tbody>"
        + "".join(body_rows)
        + "</tbody></table>"
    )


def parameter_list_html(
    parameters: dict[str, Any],
) -> str:
    if not parameters:
        return '<p class="muted">No parameters recorded.</p>'

    rows = []

    for key, value in parameters.items():
        readable_key = key.replace("_", " ").title()
        rows.append(
            '<div class="parameter-row">'
            f'<span class="parameter-name">{html.escape(readable_key)}</span>'
            f'<span class="parameter-value">{html.escape(str(value))}</span>'
            "</div>"
        )

    return '<div class="parameter-list">' + "".join(rows) + "</div>"


def metric_card(
    label: str,
    value: str,
    *,
    tone: str = "neutral",
    detail: str | None = None,
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


def _tone_for_return(value: Any) -> str:
    number = safe_float(value)

    if np.isnan(number) or number == 0:
        return "neutral"

    return "positive" if number > 0 else "negative"


def _tone_for_pf(value: Any) -> str:
    number = safe_float(value)

    if np.isnan(number):
        return "neutral"

    return "positive" if number > 1 else "negative"


def _summary_value(
    summary: pd.DataFrame,
    row: str,
    column: str,
) -> Any:
    if row not in summary.index:
        return np.nan
    if column not in summary.columns:
        return np.nan

    return summary.loc[row, column]


def comparison_strategy_card(
    summary: pd.DataFrame,
    row_name: str,
    display_name: str,
) -> str:
    if row_name not in summary.index:
        return ""

    return_value = _summary_value(
        summary,
        row_name,
        "total_return_percent",
    )
    drawdown = _summary_value(
        summary,
        row_name,
        "max_drawdown_percent",
    )
    profit_factor = _summary_value(
        summary,
        row_name,
        "trade_profit_factor",
    )
    trades = _summary_value(
        summary,
        row_name,
        "total_trades",
    )

    tone = _tone_for_return(return_value)

    return f"""
    <article class="comparison-card tone-border-{tone}">
        <div class="comparison-heading">{html.escape(display_name)}</div>
        <div class="comparison-return">{html.escape(format_percent(return_value))}</div>
        <div class="comparison-grid">
            <div><span>Drawdown</span><strong>{html.escape(format_percent(drawdown))}</strong></div>
            <div><span>Trade PF</span><strong>{html.escape(format_number(profit_factor, 3))}</strong></div>
            <div><span>Trades</span><strong>{html.escape(format_integer(trades))}</strong></div>
        </div>
    </article>
    """


def stability_cards_html(
    stability: dict[str, Any],
) -> str:
    if not stability:
        return '<p class="muted">Parameter-stability data unavailable.</p>'

    total = int(stability.get("valid_combinations", 0) or 0)
    break_even = int(stability.get("break_even_count", 0) or 0)
    near_best = int(stability.get("near_best_count", 0) or 0)

    cards = [
        metric_card(
            "Edge assessment",
            str(stability.get("edge_assessment", "N/A"))
            .replace("_", " ")
            .title(),
        ),
        metric_card(
            "Local surface",
            str(stability.get("local_surface_assessment", "N/A"))
            .replace("_", " ")
            .title(),
        ),
        metric_card(
            "PF ≥ 1 combinations",
            f"{break_even}/{total}" if total else str(break_even),
            tone=("positive" if total and break_even == total else "neutral"),
        ),
        metric_card(
            "Within 95% of best",
            f"{near_best}/{total}" if total else str(near_best),
        ),
        metric_card(
            "Neighbour retention",
            format_percent(
                safe_float(stability.get("neighbor_retention_ratio")) * 100,
                1,
            ),
        ),
        metric_card(
            "Best vs second gap",
            format_number(stability.get("best_vs_second_gap"), 4),
        ),
    ]

    return '<div class="metric-grid small">' + "".join(cards) + "</div>"


def chart_grid_html(
    chart_sections: Iterable[tuple[str, str]],
) -> str:
    cards = []

    for title, filename in chart_sections:
        cards.append(
            f"""
            <figure class="chart-card">
                <figcaption>{html.escape(title)}</figcaption>
                <a href="{html.escape(filename)}" target="_blank" rel="noopener">
                    <img src="{html.escape(filename)}" alt="{html.escape(title)}" loading="lazy">
                </a>
            </figure>
            """
        )

    if not cards:
        return '<p class="muted">No chart files were found.</p>'

    return '<div class="chart-grid">' + "".join(cards) + "</div>"


def write_research_report(
    *,
    report_file: Path,
    experiment_id: str,
    experiment_name: str,
    market_name: str,
    timeframe: str,
    hypothesis: str,
    effective_oos_start: Any,
    oos_end: Any,
    lifecycle_stage: str,
    lifecycle_reason: str,
    lifecycle_next_action: str,
    best_parameters: dict[str, Any],
    fixed_parameters: dict[str, Any],
    best_score: Any,
    mcpt_p_value: Any,
    mcpt_source: str,
    summary: pd.DataFrame,
    parameter_stability: dict[str, Any],
    diagnostic_summary: pd.DataFrame,
    diagnostic_by_side: pd.DataFrame,
    chart_sections: Iterable[tuple[str, str]],
    generated_from_saved_results: bool = False,
) -> Path:
    report_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fixed_return = _summary_value(
        summary,
        "Fixed parameters",
        "total_return_percent",
    )
    fixed_pf = _summary_value(
        summary,
        "Fixed parameters",
        "trade_profit_factor",
    )
    fixed_drawdown = _summary_value(
        summary,
        "Fixed parameters",
        "max_drawdown_percent",
    )
    walkforward_return = _summary_value(
        summary,
        "Walk-forward",
        "total_return_percent",
    )
    walkforward_pf = _summary_value(
        summary,
        "Walk-forward",
        "trade_profit_factor",
    )
    buy_hold_return = _summary_value(
        summary,
        "Buy and Hold",
        "total_return_percent",
    )

    fixed_excess = (
        safe_float(fixed_return)
        - safe_float(buy_hold_return)
    )

    overview_cards = [
        metric_card(
            "Fixed OOS return",
            format_percent(fixed_return),
            tone=_tone_for_return(fixed_return),
        ),
        metric_card(
            "Walk-forward return",
            format_percent(walkforward_return),
            tone=_tone_for_return(walkforward_return),
        ),
        metric_card(
            "Fixed trade PF",
            format_number(fixed_pf, 3),
            tone=_tone_for_pf(fixed_pf),
        ),
        metric_card(
            "Walk-forward trade PF",
            format_number(walkforward_pf, 3),
            tone=_tone_for_pf(walkforward_pf),
        ),
        metric_card(
            "MCPT p-value",
            format_number(mcpt_p_value, 4),
            tone=(
                "positive"
                if not np.isnan(safe_float(mcpt_p_value))
                and safe_float(mcpt_p_value) <= 0.05
                else "neutral"
            ),
            detail=str(mcpt_source).replace("_", " ").title(),
        ),
        metric_card(
            "Fixed max drawdown",
            format_percent(fixed_drawdown),
            tone="neutral",
        ),
    ]

    comparison_cards = "".join(
        [
            comparison_strategy_card(
                summary,
                "Fixed parameters",
                "Fixed parameters",
            ),
            comparison_strategy_card(
                summary,
                "Walk-forward",
                "Walk-forward",
            ),
            comparison_strategy_card(
                summary,
                "Buy and Hold",
                "Buy & Hold",
            ),
            comparison_strategy_card(
                summary,
                "Cash",
                "Cash",
            ),
        ]
    )

    core_summary_html = dataframe_table_html(
        summary,
        columns=CORE_SUMMARY_COLUMNS,
        include_index=True,
        compact=True,
    )

    advanced_summary_html = dataframe_table_html(
        summary,
        columns=ADVANCED_SUMMARY_COLUMNS,
        include_index=True,
    )

    core_diagnostics_html = dataframe_table_html(
        diagnostic_summary,
        columns=CORE_DIAGNOSTIC_COLUMNS,
        include_index=True,
        compact=True,
    )

    advanced_diagnostics_html = dataframe_table_html(
        diagnostic_summary,
        columns=ADVANCED_DIAGNOSTIC_COLUMNS,
        include_index=True,
    )

    side_columns = (
        "test",
        "side",
        "total_trades",
        "win_rate_percent",
        "trade_profit_factor",
        "average_winner_percent",
        "average_loser_percent",
        "payoff_ratio",
        "largest_loss_percent",
        "net_profit_cash",
    )

    side_html = dataframe_table_html(
        diagnostic_by_side,
        columns=side_columns,
        include_index=False,
    )

    saved_note = (
        "This layout was rebuilt from the existing saved result files. "
        "No optimization, MCPT, walk-forward test or OOS backtest was rerun."
        if generated_from_saved_results
        else (
            "This report was generated as part of the recorded research run."
        )
    )

    lifecycle_tone = (
        "accepted"
        if "ACCEPT" in lifecycle_stage.upper()
        else "rejected"
        if "REJECT" in lifecycle_stage.upper()
        else "active"
    )

    report_html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(experiment_id)} Research Report</title>
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
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    line-height: 1.5;
    overflow-x: hidden;
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
    scrollbar-width: thin;
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
.hero h1 {{
    margin: 0;
    font-size: clamp(28px, 4vw, 44px);
    line-height: 1.08;
}}
.subtitle {{ color: var(--muted); margin-top: 10px; }}
.stage-badge {{
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 9px 14px;
    font-weight: 700;
    white-space: nowrap;
}}
.stage-accepted {{ border-color: rgba(97, 208, 149, .6); color: var(--positive); }}
.stage-rejected {{ border-color: rgba(255, 122, 133, .6); color: var(--negative); }}
.stage-active {{ border-color: rgba(116, 167, 255, .6); color: var(--accent); }}

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

.notice {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-left: 4px solid var(--accent);
    border-radius: 10px;
    padding: 16px 18px;
    margin: 16px 0;
}}
.notice p {{ margin: 8px 0 0; }}
.notice.compact {{ font-size: 14px; color: var(--muted); }}

.metric-grid {{
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
}}
.metric-grid.small {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
.metric-card {{
    min-width: 0;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px;
}}
.metric-label {{ color: var(--muted); font-size: 13px; }}
.metric-value {{
    margin-top: 5px;
    font-size: clamp(22px, 2.4vw, 30px);
    font-weight: 760;
    overflow-wrap: anywhere;
}}
.metric-detail {{ margin-top: 6px; color: var(--muted); font-size: 12px; }}
.tone-positive .metric-value {{ color: var(--positive); }}
.tone-negative .metric-value {{ color: var(--negative); }}

.two-column {{
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
}}
.panel {{
    min-width: 0;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 18px;
}}
.panel h3 {{ margin: 0 0 12px; font-size: 17px; }}
.panel p {{ margin: 8px 0; }}
.muted {{ color: var(--muted); }}

.parameter-list {{ display: grid; gap: 8px; }}
.parameter-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    background: var(--panel-2);
    border-radius: 8px;
    padding: 9px 11px;
}}
.parameter-name {{ color: var(--muted); font-size: 13px; }}
.parameter-value {{ font-weight: 700; text-align: right; overflow-wrap: anywhere; }}

.comparison-cards {{
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
    margin-bottom: 16px;
}}
.comparison-card {{
    min-width: 0;
    background: var(--panel);
    border: 1px solid var(--border);
    border-top-width: 3px;
    border-radius: 12px;
    padding: 15px;
}}
.tone-border-positive {{ border-top-color: var(--positive); }}
.tone-border-negative {{ border-top-color: var(--negative); }}
.tone-border-neutral {{ border-top-color: var(--muted); }}
.comparison-heading {{ color: var(--muted); font-size: 13px; }}
.comparison-return {{ font-size: 27px; font-weight: 760; margin: 5px 0 12px; }}
.comparison-grid {{ display: grid; gap: 7px; }}
.comparison-grid div {{ display: flex; justify-content: space-between; gap: 8px; font-size: 13px; }}
.comparison-grid span {{ color: var(--muted); }}

.table-shell {{
    width: 100%;
    max-width: 100%;
    overflow-x: auto;
    border: 1px solid var(--border);
    border-radius: 10px;
    background: var(--panel);
    scrollbar-width: thin;
}}
.data-table {{
    width: 100%;
    min-width: 760px;
    border-collapse: collapse;
    font-size: 13px;
}}
.data-table.compact {{ min-width: 700px; table-layout: fixed; }}
.data-table th,
.data-table td {{
    border-bottom: 1px solid var(--border);
    padding: 10px 11px;
    text-align: right;
    white-space: nowrap;
}}
.data-table th:first-child,
.data-table td:first-child {{ text-align: left; }}
.data-table thead th {{
    position: sticky;
    top: 0;
    background: #1a2027;
    color: #dce2e8;
    font-weight: 650;
}}
.data-table tbody tr:last-child th,
.data-table tbody tr:last-child td {{ border-bottom: 0; }}
.data-table tbody tr:hover {{ background: rgba(116, 167, 255, .06); }}

.details-card {{
    margin-top: 13px;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
}}
.details-card summary {{
    cursor: pointer;
    padding: 13px 15px;
    font-weight: 650;
}}
.details-content {{ padding: 0 14px 14px; }}

.chart-grid {{
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
}}
.chart-card {{
    min-width: 0;
    margin: 0;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
}}
.chart-card figcaption {{
    padding: 12px 14px;
    font-weight: 700;
    border-bottom: 1px solid var(--border);
}}
.chart-card img {{
    display: block;
    width: 100%;
    height: auto;
    background: #090909;
}}

footer {{
    margin: 40px 0 10px;
    padding-top: 18px;
    border-top: 1px solid var(--border);
    color: var(--muted);
    font-size: 13px;
}}

@media (max-width: 960px) {{
    .hero {{ grid-template-columns: 1fr; }}
    .stage-badge {{ justify-self: start; }}
    .metric-grid,
    .metric-grid.small {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    .comparison-cards {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    .chart-grid {{ grid-template-columns: 1fr; }}
}}

@media (max-width: 640px) {{
    .page {{ padding: 16px; }}
    .metric-grid,
    .metric-grid.small,
    .two-column,
    .comparison-cards {{ grid-template-columns: 1fr; }}
    .data-table.compact {{ table-layout: auto; }}
}}
</style>
</head>
<body>
<div class="page">
<nav class="report-nav" aria-label="Report sections">
    <a href="#overview">Overview</a>
    <a href="#comparison">Comparison</a>
    <a href="#parameters">Parameters</a>
    <a href="#diagnostics">Diagnostics</a>
    <a href="#charts">Charts</a>
    <a href="#notes">Notes</a>
</nav>

<header class="hero">
    <div>
        <h1>{html.escape(experiment_id)} — {html.escape(experiment_name)}</h1>
        <div class="subtitle">
            {html.escape(market_name)} · {html.escape(timeframe)} ·
            OOS {html.escape(str(effective_oos_start))} through {html.escape(str(oos_end))}
        </div>
    </div>
    <div class="stage-badge stage-{lifecycle_tone}">{html.escape(lifecycle_stage)}</div>
</header>

<div class="notice compact">
    {html.escape(saved_note)}
</div>

<section class="section" id="overview">
    <div class="section-header">
        <h2>Overview</h2>
        <div class="section-kicker">Key evidence in one place</div>
    </div>
    <div class="metric-grid">{''.join(overview_cards)}</div>

    <div class="two-column" style="margin-top:14px">
        <div class="panel">
            <h3>Hypothesis</h3>
            <p>{html.escape(hypothesis)}</p>
        </div>
        <div class="panel">
            <h3>Lifecycle</h3>
            <p><strong>{html.escape(lifecycle_stage)}</strong></p>
            <p class="muted">{html.escape(lifecycle_reason)}</p>
            <p><strong>Next:</strong> {html.escape(lifecycle_next_action)}</p>
        </div>
    </div>
</section>

<section class="section" id="comparison">
    <div class="section-header">
        <h2>Out-of-sample comparison</h2>
        <div class="section-kicker">Fixed, walk-forward and benchmarks</div>
    </div>

    <div class="comparison-cards">{comparison_cards}</div>

    <div class="notice compact">
        Fixed excess return versus Buy & Hold: <strong>{html.escape(format_percent(fixed_excess))}</strong>.
        Benchmark return is context; lower exposure or drawdown can still be relevant even when raw return is lower.
    </div>

    <div class="table-shell">{core_summary_html}</div>

    <details class="details-card">
        <summary>Additional account and position metrics</summary>
        <div class="details-content">
            <div class="table-shell">{advanced_summary_html}</div>
        </div>
    </details>
</section>

<section class="section" id="parameters">
    <div class="section-header">
        <h2>Parameters and statistical evidence</h2>
        <div class="section-kicker">Best in-sample is not the same as fixed OOS</div>
    </div>

    <div class="two-column">
        <div class="panel">
            <h3>Best in-sample parameters</h3>
            {parameter_list_html(best_parameters)}
            <p class="muted">Best in-sample bar PF: <strong>{html.escape(format_number(best_score, 4))}</strong></p>
        </div>
        <div class="panel">
            <h3>Fixed out-of-sample parameters</h3>
            {parameter_list_html(fixed_parameters)}
            <p class="muted">These are the locked parameters used for the fixed OOS comparison.</p>
        </div>
    </div>

    <div style="margin-top:14px">{stability_cards_html(parameter_stability)}</div>

    <div class="notice compact">
        {html.escape(str(parameter_stability.get('interpretation', 'Parameter stability is descriptive and does not replace MCPT or out-of-sample validation.')))}
    </div>
</section>

<section class="section" id="diagnostics">
    <div class="section-header">
        <h2>Trade-quality diagnostics</h2>
        <div class="section-kicker">Expectancy, payoff and tail risk</div>
    </div>

    <div class="table-shell">{core_diagnostics_html}</div>

    <details class="details-card">
        <summary>Advanced tail and holding-period diagnostics</summary>
        <div class="details-content">
            <div class="table-shell">{advanced_diagnostics_html}</div>
        </div>
    </details>

    <details class="details-card">
        <summary>Diagnostics by position side</summary>
        <div class="details-content">
            <div class="table-shell">{side_html}</div>
        </div>
    </details>
</section>

<section class="section" id="charts">
    <div class="section-header">
        <h2>Charts</h2>
        <div class="section-kicker">Click any chart to open it full size</div>
    </div>
    {chart_grid_html(chart_sections)}
</section>

<section class="section" id="notes">
    <div class="section-header"><h2>Research notes</h2></div>
    <div class="notice">
        <strong>Interpretation rule:</strong>
        <p>
            Statistical significance, economic significance, out-of-sample consistency,
            transaction costs, exposure and market rationale should be considered together.
            A single headline number is not enough to establish a robust edge.
        </p>
    </div>
</section>

<footer>
    Responsive research report layout · Wide tables are contained within their own scroll area rather than expanding the whole page.
</footer>
</div>
</body>
</html>
"""

    report_file.write_text(
        report_html,
        encoding="utf-8",
    )

    return report_file
