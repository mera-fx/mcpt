from __future__ import annotations

import html
import json
import math
import re
from typing import Any, Iterable, Mapping

from analytics_evidence_registry import (
    AnalyticsKind,
    ExperimentEvidenceSpec,
    MetricFamily,
    NOT_APPLICABLE_MESSAGE,
)
from analytics_metrics import FAMILY_LABELS


REPORT_STYLE = """
:root {
  color-scheme: light;
  --ink: #111827;
  --muted: #596273;
  --line: #d8dde6;
  --panel: #f6f7f9;
  --paper: #ffffff;
  --link: #1556a8;
  --bad: #a32121;
  --good: #166534;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font: 15px/1.55 Inter, ui-sans-serif, system-ui, sans-serif;
}
main { width: min(1700px, 96vw); margin: 0 auto; padding: 28px 0 64px; }
a { color: var(--link); text-decoration-thickness: 1px; }
.top-nav { margin-bottom: 24px; }
h1, h2, h3, h4 { line-height: 1.2; }
h1 { margin: 0 0 8px; font-size: clamp(28px, 4vw, 44px); }
h2 {
  margin-top: 38px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--ink);
}
h3 { margin-top: 26px; }
p { max-width: 1100px; }
.eyebrow {
  color: var(--muted);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: .09em;
  text-transform: uppercase;
}
.lede { color: var(--muted); font-size: 17px; }
.boundary, .notice {
  border: 1px solid var(--line);
  background: var(--panel);
  padding: 14px 16px;
  margin: 18px 0;
}
.notice.bad { color: var(--bad); border-color: #d9aaaa; }
.notice.good { color: var(--good); border-color: #a9c7b0; }
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px;
  margin: 18px 0;
}
.card { border: 1px solid var(--line); padding: 14px; min-width: 0; }
.card .label { color: var(--muted); font-size: 12px; font-weight: 700; }
.card .value { font-size: 22px; font-weight: 750; overflow-wrap: anywhere; }
.negative { color: var(--bad); }
.report-layout {
  display: grid;
  grid-template-columns: minmax(210px, 245px) minmax(0, 1fr);
  gap: 30px;
  align-items: start;
  margin-top: 14px;
}
.report-content { min-width: 0; }
.report-content section { scroll-margin-top: 18px; }
.side-nav {
  position: sticky;
  top: 18px;
  max-height: calc(100vh - 36px);
  overflow-y: auto;
  border: 1px solid var(--line);
  background: var(--panel);
  padding: 14px;
}
.side-nav strong {
  display: block;
  margin-bottom: 8px;
  font-size: 12px;
  letter-spacing: .07em;
  text-transform: uppercase;
}
.side-nav nav { margin: 0; }
.side-nav a {
  display: block;
  border-left: 3px solid transparent;
  padding: 6px 8px;
  color: var(--ink);
  font-size: 13px;
  line-height: 1.3;
  text-decoration: none;
}
.side-nav a:hover,
.side-nav a:focus {
  border-left-color: var(--link);
  background: var(--paper);
  color: var(--link);
}
.curve-comparison {
  margin: 24px 0 8px;
  scroll-margin-top: 18px;
}
.curve-comparison h3 { margin-bottom: 6px; }
.curve-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 12px;
}
.curve-panel {
  min-width: 0;
  border: 1px solid var(--line);
  background: var(--paper);
  padding: 12px;
}
.curve-panel-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: baseline;
  margin-bottom: 4px;
}
.curve-panel-header span {
  color: var(--muted);
  font-variant-numeric: tabular-nums;
  text-align: right;
}
.curve-panel svg {
  display: block;
  width: 100%;
  height: auto;
}
.curve-gridline { stroke: var(--line); stroke-width: 1; }
.curve-reference {
  stroke: #8b95a5;
  stroke-width: 1;
  stroke-dasharray: 5 4;
}
.curve-line {
  fill: none;
  stroke-width: 2.2;
  stroke-linejoin: round;
  stroke-linecap: round;
  vector-effect: non-scaling-stroke;
}
.curve-axis-label {
  fill: var(--muted);
  font: 11px/1.2 Inter, ui-sans-serif, system-ui, sans-serif;
}
.curve-empty {
  display: grid;
  min-height: 260px;
  place-items: center;
  padding: 24px;
  color: var(--muted);
  text-align: center;
}
.table-wrap { overflow-x: auto; border: 1px solid var(--line); margin: 12px 0; }
table { width: 100%; border-collapse: collapse; min-width: 680px; }
th, td {
  border-bottom: 1px solid var(--line);
  padding: 8px 10px;
  text-align: right;
  vertical-align: top;
}
th { background: var(--panel); font-size: 12px; letter-spacing: .02em; }
th:first-child, td:first-child { text-align: left; }
tr:last-child td { border-bottom: 0; }
code { overflow-wrap: anywhere; white-space: normal; }
details { border-top: 1px solid var(--line); padding: 8px 0; }
summary { cursor: pointer; font-weight: 700; }
.meta { color: var(--muted); font-size: 13px; }
.empty { color: var(--muted); font-style: italic; }
.status { font-weight: 800; }
.status.available { color: var(--good); }
.status.unavailable { color: var(--bad); }
footer { border-top: 1px solid var(--line); margin-top: 44px; padding-top: 16px; color: var(--muted); }
@media (max-width: 980px) {
  .report-layout { grid-template-columns: 1fr; }
  .side-nav {
    position: static;
    max-height: none;
  }
  .side-nav nav {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  }
}
@media (max-width: 760px) {
  main { width: 94vw; }
  .curve-grid { grid-template-columns: 1fr; }
  th, td { padding: 7px 8px; }
}
"""


LABEL_OVERRIDES = {
    "return_on_initial_capital_percent": (
        "Return on initial capital"
    ),
    "normalized_total_return_percent": (
        "Return on initial capital"
    ),
    "normalized_cagr_percent": "Annual rate of return",
    "annual_rate_of_return_percent": "Annual rate of return",
    "monthly_rate_of_return_percent": "Monthly rate of return",
    "maximum_strategy_drawdown_usd": (
        "Maximum strategy drawdown (USD)"
    ),
    "maximum_strategy_drawdown_percent": (
        "Maximum strategy drawdown (%)"
    ),
    "return_on_maximum_strategy_drawdown": (
        "Return on maximum strategy drawdown"
    ),
    "recovery_factor": (
        "Return on maximum strategy drawdown (recovery factor)"
    ),
    "maximum_contracts_held": "Maximum contracts held",
    "buy_and_hold_return_usd": "Buy-and-hold return (USD)",
    "buy_and_hold_return_percent": "Buy-and-hold return (%)",
    "benchmark_total_return_percent": "Buy-and-hold total return",
    "benchmark_cagr_percent": "Buy-and-hold annual rate",
    "excess_total_return_percent": (
        "Strategy minus buy-and-hold return"
    ),
    "excess_cagr_percent": (
        "Strategy minus buy-and-hold annual rate"
    ),
}


def series_slug(series_id: str) -> str:
    slug = re.sub(
        r"[^a-zA-Z0-9._-]+",
        "--",
        series_id,
    ).strip("-").lower()
    return slug or "series"


def _escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _humanize(value: str) -> str:
    text = value.replace("_", " ").strip()
    replacements = {
        "usd": "USD",
        "mae": "MAE",
        "mfe": "MFE",
        "sqn": "SQN",
        "hhi": "HHI",
        "cagr": "CAGR",
        "pnl": "P&L",
        "mcpt": "MCPT",
    }
    words = [
        replacements.get(word.lower(), word)
        for word in text.split()
    ]
    result = " ".join(words)
    return result[:1].upper() + result[1:]


def _display_label(key: str) -> str:
    return LABEL_OVERRIDES.get(key, _humanize(key))


def _is_adverse_value(key: str, value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(
        value,
        (int, float),
    ):
        return False
    number = float(value)
    if not math.isfinite(number):
        return False
    return number < 0 or (
        number > 0 and "gross_loss" in key.lower()
    )


def _format_value(key: str, value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        if not math.isfinite(value):
            return "—"
        lowered = key.lower()
        adverse = _is_adverse_value(key, value)
        display_value = abs(value) if adverse else value
        if "usd" in lowered or lowered.endswith("_dollars"):
            formatted = f"${display_value:,.2f}"
            return f"({formatted})" if adverse else formatted
        if "percent" in lowered:
            formatted = f"{display_value:,.2f}%"
            return f"({formatted})" if adverse else formatted
        if any(
            token in lowered
            for token in (
                "ratio",
                "factor",
                "correlation",
                "beta",
                "gini",
                "hhi",
                "autocorrelation",
                "fraction",
                "return_on_maximum",
            )
        ):
            formatted = f"{display_value:,.4f}"
        elif display_value.is_integer():
            formatted = f"{int(display_value):,}"
        else:
            formatted = f"{display_value:,.4f}"
        return f"({formatted})" if adverse else formatted
    if isinstance(value, (dict, list)):
        return _escape(
            json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    return _escape(value)


def _cell_html(key: str, value: Any) -> str:
    class_attribute = (
        ' class="negative"'
        if _is_adverse_value(key, value)
        else ""
    )
    return (
        f"<td{class_attribute}>"
        f"{_format_value(key, value)}</td>"
    )


def _chart_points(
    rows: Iterable[Mapping[str, Any]],
    value_key: str,
) -> list[tuple[int, float]]:
    points: list[tuple[int, float]] = []
    for index, row in enumerate(rows):
        value = row.get(value_key)
        if isinstance(value, bool) or not isinstance(
            value,
            (int, float),
        ):
            continue
        number = float(value)
        if math.isfinite(number):
            points.append((index, number))
    return points


def _axis_usd(value: float) -> str:
    magnitude = abs(value)
    if magnitude >= 1_000_000:
        return f"${value / 1_000_000:,.1f}m"
    if magnitude >= 1_000:
        return f"${value / 1_000:,.0f}k"
    return f"${value:,.0f}"


def _curve_svg(
    rows: list[Mapping[str, Any]],
    *,
    value_key: str,
    title: str,
    color: str,
    minimum: float,
    maximum: float,
    reference_capital_usd: float,
) -> str:
    points = _chart_points(rows, value_key)
    width = 640.0
    height = 270.0
    left = 66.0
    right = 16.0
    top = 14.0
    bottom = 34.0
    plot_width = width - left - right
    plot_height = height - top - bottom
    span = maximum - minimum

    def x_position(index: int) -> float:
        denominator = max(len(rows) - 1, 1)
        return left + index / denominator * plot_width

    def y_position(value: float) -> float:
        return top + (maximum - value) / span * plot_height

    path = " ".join(
        (
            f"{'M' if offset == 0 else 'L'}"
            f"{x_position(index):.2f},{y_position(value):.2f}"
        )
        for offset, (index, value) in enumerate(points)
    )
    grid = []
    for tick in range(5):
        fraction = tick / 4.0
        y = top + fraction * plot_height
        value = maximum - fraction * span
        grid.append(
            f'<line class="curve-gridline" x1="{left:.1f}" '
            f'y1="{y:.1f}" x2="{width - right:.1f}" '
            f'y2="{y:.1f}"></line>'
            f'<text class="curve-axis-label" x="{left - 8:.1f}" '
            f'y="{y + 4:.1f}" text-anchor="end">'
            f"{_escape(_axis_usd(value))}</text>"
        )
    reference_line = ""
    if minimum <= reference_capital_usd <= maximum:
        reference_y = y_position(reference_capital_usd)
        reference_line = (
            f'<line class="curve-reference" x1="{left:.1f}" '
            f'y1="{reference_y:.1f}" x2="{width - right:.1f}" '
            f'y2="{reference_y:.1f}"></line>'
        )
    start_date = (
        str(rows[0].get("analysis_date", ""))[:10]
        if rows
        else ""
    )
    end_date = (
        str(rows[-1].get("analysis_date", ""))[:10]
        if rows
        else ""
    )
    endpoint = ""
    if points:
        final_index, final_value = points[-1]
        endpoint = (
            f'<circle cx="{x_position(final_index):.2f}" '
            f'cy="{y_position(final_value):.2f}" r="3.2" '
            f'fill="{_escape(color)}"></circle>'
        )
    return (
        f'<svg viewBox="0 0 {width:.0f} {height:.0f}" '
        f'role="img" aria-label="{_escape(title)}">'
        f"<title>{_escape(title)}</title>"
        + "".join(grid)
        + reference_line
        + (
            f'<path class="curve-line" stroke="{_escape(color)}" '
            f'd="{path}"></path>'
            if path
            else ""
        )
        + endpoint
        + (
            f'<text class="curve-axis-label" x="{left:.1f}" '
            f'y="{height - 8:.1f}">{_escape(start_date)}</text>'
            f'<text class="curve-axis-label" '
            f'x="{width - right:.1f}" y="{height - 8:.1f}" '
            f'text-anchor="end">{_escape(end_date)}</text>'
        )
        + "</svg>"
    )


def _equity_comparison_chart(
    result: Mapping[str, Any],
) -> str:
    families = result["metric_families"]
    equity_family = families[
        MetricFamily.EQUITY_AND_DRAWDOWN.value
    ]
    benchmark_family = families[
        MetricFamily.BENCHMARK_AND_VALUE_ADDED.value
    ]
    benchmark_available = (
        benchmark_family["status"] == "AVAILABLE"
    )
    if benchmark_available:
        strategy_rows = list(
            benchmark_family.get("tables", {}).get(
                "aligned_periods",
                [],
            )
        )
        benchmark_rows = strategy_rows
    else:
        strategy_rows = list(
            equity_family.get("tables", {}).get(
                "equity_curve",
                [],
            )
        )
        benchmark_rows = []

    reference_capital = float(
        result["reference_model"]["reference_capital_usd"]
    )
    strategy_points = _chart_points(
        strategy_rows,
        "strategy_equity_usd",
    )
    benchmark_points = _chart_points(
        benchmark_rows,
        "benchmark_equity_usd",
    )
    values = [
        reference_capital,
        *[value for _, value in strategy_points],
        *[value for _, value in benchmark_points],
    ]
    raw_minimum = min(values)
    raw_maximum = max(values)
    raw_span = raw_maximum - raw_minimum
    padding = max(
        raw_span * 0.06,
        abs(reference_capital) * 0.01,
        1.0,
    )
    minimum = raw_minimum - padding
    maximum = raw_maximum + padding

    def panel(
        *,
        label: str,
        rows: list[Mapping[str, Any]],
        value_key: str,
        color: str,
    ) -> str:
        points = _chart_points(rows, value_key)
        if not points:
            return (
                '<div class="curve-panel">'
                f'<div class="curve-panel-header"><strong>'
                f"{_escape(label)}</strong></div>"
                '<div class="curve-empty">'
                "Buy-and-hold curve is not available from this "
                "experiment’s frozen evidence."
                "</div></div>"
            )
        ending = points[-1][1]
        total_return = (
            ending / reference_capital - 1.0
        ) * 100.0
        return_class = (
            ' class="negative"'
            if total_return < 0
            else ""
        )
        return (
            '<div class="curve-panel">'
            '<div class="curve-panel-header">'
            f"<strong>{_escape(label)}</strong>"
            f"<span>{_format_value('equity_usd', ending)} · "
            f"<b{return_class}>"
            f"{_format_value('return_percent', total_return)}"
            "</b></span></div>"
            + _curve_svg(
                rows,
                value_key=value_key,
                title=f"{label} over the aligned analysis period",
                color=color,
                minimum=minimum,
                maximum=maximum,
                reference_capital_usd=reference_capital,
            )
            + "</div>"
        )

    strategy_panel = panel(
        label="Strategy equity",
        rows=strategy_rows,
        value_key="strategy_equity_usd",
        color="#1556a8",
    )
    benchmark_panel = panel(
        label="Buy-and-hold equity",
        rows=benchmark_rows,
        value_key="benchmark_equity_usd",
        color="#6b7280",
    )
    comparison_note = (
        "Both panels use the same USD scale and the same aligned dates. "
        "The dashed line is registered reference capital. Buy-and-hold "
        "is the normalized underlying benchmark, not a literal "
        "one-contract futures portfolio."
        if benchmark_available
        else (
            "The dashed line is registered reference capital. The "
            "strategy curve is shown from frozen equity evidence; no "
            "buy-and-hold curve is estimated."
        )
    )
    return (
        '<div class="curve-comparison" '
        'id="equity-curve-comparison">'
        "<h3>Equity curve and buy-and-hold</h3>"
        f'<p class="meta">{_escape(comparison_note)}</p>'
        f'<div class="curve-grid">{strategy_panel}'
        f"{benchmark_panel}</div></div>"
    )


def _metric_table(metrics: Mapping[str, Any]) -> str:
    scalar = [
        (key, value)
        for key, value in metrics.items()
        if not isinstance(value, Mapping)
    ]
    nested = [
        (key, value)
        for key, value in metrics.items()
        if isinstance(value, Mapping)
    ]
    pieces: list[str] = []
    if scalar:
        rows = "".join(
            "<tr>"
            f"<td>{_escape(_display_label(key))}</td>"
            f"{_cell_html(key, value)}"
            "</tr>"
            for key, value in scalar
        )
        pieces.append(
            '<div class="table-wrap"><table>'
            "<thead><tr><th>Measurement</th><th>Value</th></tr></thead>"
            f"<tbody>{rows}</tbody></table></div>"
        )
    for key, value in nested:
        pieces.append(
            f"<h4>{_escape(_display_label(key))}</h4>"
            + _metric_table(value)
        )
    return "".join(pieces)


def _performance_matrix(metrics: Mapping[str, Any]) -> str:
    columns = ("all", "long", "short")
    preferred_fields = (
        "net_profit_usd",
        "gross_profit_usd",
        "gross_loss_usd",
        "return_on_initial_capital_percent",
        "maximum_strategy_drawdown_usd",
        "maximum_strategy_drawdown_percent",
        "return_on_maximum_strategy_drawdown",
        "profit_factor",
        "maximum_contracts_held",
        "total_transaction_cost_usd",
        "annual_rate_of_return_percent",
        "monthly_rate_of_return_percent",
        "buy_and_hold_return_usd",
        "buy_and_hold_return_percent",
        "completed_trades",
        "winning_trades",
        "losing_trades",
        "breakeven_trades",
        "win_rate_percent",
    )
    fields: list[str] = []
    for field in preferred_fields:
        if any(
            field in metrics.get(column, {})
            for column in columns
        ):
            fields.append(field)
    for column in columns:
        for field in metrics.get(column, {}):
            if field not in fields:
                fields.append(field)
    rows = []
    for field in fields:
        cells = [
            _cell_html(
                field,
                metrics.get(column, {}).get(field),
            )
            for column in columns
        ]
        rows.append(
            "<tr>"
            f"<td>{_escape(_display_label(field))}</td>"
            + "".join(cells)
            + "</tr>"
        )
    return (
        '<div class="table-wrap"><table>'
        "<thead><tr><th>Measurement</th>"
        "<th>All</th><th>Long</th><th>Short</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div>"
    )


def _table_html(
    rows: Iterable[Mapping[str, Any]],
    *,
    maximum_rows: int = 120,
) -> str:
    records = [dict(row) for row in rows]
    if not records:
        return '<p class="empty">No rows.</p>'
    truncated = len(records) > maximum_rows
    if truncated:
        half = maximum_rows // 2
        shown = records[:half] + records[-half:]
    else:
        shown = records
    columns: list[str] = []
    for row in shown:
        for column in row:
            if column not in columns:
                columns.append(column)
    header = "".join(
        f"<th>{_escape(_display_label(column))}</th>"
        for column in columns
    )
    body = []
    for row in shown:
        body.append(
            "<tr>"
            + "".join(
                _cell_html(column, row.get(column))
                for column in columns
            )
            + "</tr>"
        )
    note = (
        f'<p class="meta">Showing the first and last '
        f'{maximum_rows // 2:,} of {len(records):,} rows. '
        "The complete table is retained in analytics.json.</p>"
        if truncated
        else ""
    )
    return (
        note
        + '<div class="table-wrap"><table>'
        f"<thead><tr>{header}</tr></thead>"
        f"<tbody>{''.join(body)}</tbody></table></div>"
    )


def _assumptions_html(assumptions: Mapping[str, Any]) -> str:
    if not assumptions:
        return ""
    rows = "".join(
        "<tr>"
        f"<td>{_escape(_display_label(key))}</td>"
        f"{_cell_html(key, value)}"
        "</tr>"
        for key, value in assumptions.items()
    )
    return (
        "<details><summary>Conventions and assumptions</summary>"
        '<div class="table-wrap"><table><tbody>'
        f"{rows}</tbody></table></div></details>"
    )


def _family_html(
    family: Mapping[str, Any],
    *,
    after_metrics: str = "",
) -> str:
    status = str(family["status"])
    available = status == "AVAILABLE"
    status_class = "available" if available else "unavailable"
    pieces = [
        f'<section id="{_escape(family["family"])}">',
        f"<h2>{_escape(family['label'])}</h2>",
        (
            f'<p class="status {status_class}">'
            f"{_escape(status.replace('_', ' ').title())}</p>"
        ),
        f"<p>{_escape(family['message'])}</p>",
    ]
    if available:
        metrics = family.get("metrics", {})
        if family["family"] == MetricFamily.PERFORMANCE_SUMMARY.value:
            pieces.append(_performance_matrix(metrics))
        else:
            pieces.append(_metric_table(metrics))
        if after_metrics:
            pieces.append(after_metrics)
        for name, rows in family.get("tables", {}).items():
            if name == "equity_curve":
                continue
            pieces.append(f"<h3>{_escape(_display_label(name))}</h3>")
            pieces.append(_table_html(rows))
        pieces.append(
            _assumptions_html(family.get("assumptions", {}))
        )
        evidence_paths = family.get("evidence_paths", [])
        if evidence_paths:
            pieces.append(
                "<details><summary>Frozen evidence paths</summary><ul>"
                + "".join(
                    f"<li><code>{_escape(path)}</code></li>"
                    for path in evidence_paths
                )
                + "</ul></details>"
            )
    pieces.append("</section>")
    return "".join(pieces)


def _page(
    *,
    title: str,
    eyebrow: str,
    navigation: str,
    body: str,
) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_escape(title)}</title>
  <style>{REPORT_STYLE}</style>
</head>
<body>
<main>
  <nav class="top-nav">{navigation}</nav>
  <div class="eyebrow">{_escape(eyebrow)}</div>
  {body}
  <footer>
    Reporting-only analytics generated deterministically from registered
    frozen evidence. No strategy, selection, MCPT, bootstrap, market-data
    request, or lifecycle mutation is part of this build.
  </footer>
</main>
</body>
</html>
"""


def render_series_report(result: Mapping[str, Any]) -> str:
    series = result["series"]
    families = result["metric_families"]
    performance = families[
        MetricFamily.PERFORMANCE_SUMMARY.value
    ]["metrics"]["all"]
    ratios = families[
        MetricFamily.PERFORMANCE_RATIOS.value
    ]["metrics"]
    drawdown = families[
        MetricFamily.EQUITY_AND_DRAWDOWN.value
    ]["metrics"]
    integrity = result["integrity"]
    reconciliation_class = (
        "good"
        if integrity["trade_equity_reconciled"]
        else "bad"
    )
    cards = [
        ("Trades", performance["completed_trades"], "count"),
        ("Net profit", performance["net_profit_usd"], "usd"),
        (
            "Return on max drawdown",
            performance[
                "return_on_maximum_strategy_drawdown"
            ],
            "ratio",
        ),
        ("Profit Factor", performance["profit_factor"], "ratio"),
        ("Win rate", performance["win_rate_percent"], "percent"),
        (
            "Return on initial capital",
            ratios["normalized_total_return_percent"],
            "percent",
        ),
        (
            "Maximum drawdown",
            drawdown["maximum_drawdown_percent"],
            "percent",
        ),
    ]
    cards_html = "".join(
        '<div class="card">'
        f'<div class="label">{_escape(label)}</div>'
        f'<div class="value'
        f'{" negative" if _is_adverse_value(kind, value) else ""}">'
        f'{_format_value(kind, value)}</div>'
        "</div>"
        for label, value, kind in cards
    )
    family_html = "".join(
        _family_html(
            families[family.value],
            after_metrics=(
                _equity_comparison_chart(result)
                if family == MetricFamily.PERFORMANCE_SUMMARY
                else ""
            ),
        )
        for family in MetricFamily
    )
    evidence_html = _table_html(result.get("evidence", []))
    sidebar_links = [("overview", "Overview")]
    for family in MetricFamily:
        sidebar_links.append(
            (family.value, FAMILY_LABELS[family])
        )
        if family == MetricFamily.PERFORMANCE_SUMMARY:
            sidebar_links.append(
                (
                    "equity-curve-comparison",
                    "Equity curve and buy-and-hold",
                )
            )
    sidebar_links.append(
        ("evidence-manifest", "Series evidence manifest")
    )
    sidebar = (
        '<aside class="side-nav"><strong>On this page</strong>'
        '<nav aria-label="Report sections">'
        + "".join(
            f'<a href="#{_escape(section_id)}">'
            f"{_escape(label)}</a>"
            for section_id, label in sidebar_links
        )
        + "</nav></aside>"
    )
    content = f"""
<section id="overview">
<h1>{_escape(series['display_name'])}</h1>
<p class="lede">
  Complete frozen-evidence analytics for
  <code>{_escape(series['series_id'])}</code>.
</p>
<div class="boundary">
  This page measures the saved trade ledger, equity path, aligned benchmark,
  and existing robustness artifacts. It does not produce or alter a research
  result.
</div>
<div class="cards">{cards_html}</div>
<p class="meta">
  Return on max drawdown = net profit ÷ absolute maximum cash drawdown.
</p>
<div class="notice {reconciliation_class}">
  Trade/equity reconciliation:
  <strong>{_format_value('trade_equity_reconciled', integrity['trade_equity_reconciled'])}</strong>.
  Difference:
  {_format_value('reconciliation_difference_usd', integrity['reconciliation_difference_usd'])}.
</div>
</section>
{family_html}
<section id="evidence-manifest">
  <h2>Series evidence manifest</h2>
  {evidence_html}
</section>
"""
    body = (
        '<div class="report-layout">'
        f"{sidebar}"
        f'<div class="report-content">{content}</div>'
        "</div>"
    )
    return _page(
        title=f"{series['series_id']} analytics",
        eyebrow=(
            f"{series['experiment_id']} · {series['market']} · "
            "Frozen evidence"
        ),
        navigation=(
            '<a href="../report.html">Experiment analytics</a> · '
            '<a href="../../index.html">All experiments</a>'
        ),
        body=body,
    )


def render_experiment_report(
    experiment: ExperimentEvidenceSpec,
    results: Iterable[Mapping[str, Any]],
) -> str:
    result_rows = list(results)
    if experiment.analytics_kind == (
        AnalyticsKind.DATA_SOURCE_QUALIFICATION
    ):
        families = "".join(
            "<tr>"
            f"<td>{_escape(FAMILY_LABELS[family])}</td>"
            "<td class=\"status unavailable\">Not applicable</td>"
            f"<td>{_escape(NOT_APPLICABLE_MESSAGE)}</td>"
            "</tr>"
            for family in MetricFamily
        )
        body = f"""
<h1>{_escape(experiment.experiment_name)}</h1>
<p class="lede">{_escape(experiment.experiment_id)}</p>
<div class="notice">
  <strong>{_escape(NOT_APPLICABLE_MESSAGE)}</strong>
</div>
<p>
  This experiment qualifies a data source rather than a strategy. Strategy
  performance measurements are intentionally not estimated or reconstructed.
</p>
<div class="table-wrap"><table>
  <thead><tr><th>Metric family</th><th>Status</th><th>Explanation</th></tr></thead>
  <tbody>{families}</tbody>
</table></div>
"""
    else:
        rows = []
        for result in result_rows:
            series = result["series"]
            performance = result["metric_families"][
                MetricFamily.PERFORMANCE_SUMMARY.value
            ]["metrics"]["all"]
            ratios = result["metric_families"][
                MetricFamily.PERFORMANCE_RATIOS.value
            ]["metrics"]
            drawdown = result["metric_families"][
                MetricFamily.EQUITY_AND_DRAWDOWN.value
            ]["metrics"]
            benchmark = result["metric_families"][
                MetricFamily.BENCHMARK_AND_VALUE_ADDED.value
            ]
            rows.append(
                {
                    "series": (
                        f'<a href="{series_slug(series["series_id"])}/report.html">'
                        f'{_escape(series["display_name"])}</a>'
                    ),
                    "market": series["market"],
                    "completed_trades": performance[
                        "completed_trades"
                    ],
                    "net_profit_usd": performance[
                        "net_profit_usd"
                    ],
                    "profit_factor": performance[
                        "profit_factor"
                    ],
                    "win_rate_percent": performance[
                        "win_rate_percent"
                    ],
                    "normalized_total_return_percent": ratios[
                        "normalized_total_return_percent"
                    ],
                    "maximum_drawdown_percent": drawdown[
                        "maximum_drawdown_percent"
                    ],
                    "return_on_maximum_strategy_drawdown": (
                        performance[
                            "return_on_maximum_strategy_drawdown"
                        ]
                    ),
                }
            )
        columns = list(rows[0]) if rows else []
        header = "".join(
            f"<th>{_escape(_display_label(column))}</th>"
            for column in columns
        )
        body_rows = []
        for row in rows:
            body_rows.append(
                "<tr>"
                + "".join(
                    (
                        f"<td>{row[column]}</td>"
                        if column == "series"
                        else _cell_html(column, row[column])
                    )
                    for column in columns
                )
                + "</tr>"
            )
        body = f"""
<h1>{_escape(experiment.experiment_name)}</h1>
<p class="lede">
  {_escape(experiment.experiment_id)} · {len(result_rows):,} separately
  measured strategy series.
</p>
<div class="boundary">
  Candidate, finalist, sizing, NQ, and MNQ rows remain separate. The table
  does not manufacture an aggregate portfolio.
</div>
<div class="table-wrap"><table>
  <thead><tr>{header}</tr></thead>
  <tbody>{''.join(body_rows)}</tbody>
</table></div>
"""
    return _page(
        title=f"{experiment.experiment_id} analytics",
        eyebrow="Protected analytics expansion",
        navigation='<a href="../index.html">All experiments</a>',
        body=body,
    )


def render_root_index(
    experiments: Iterable[ExperimentEvidenceSpec],
    *,
    result_counts: Mapping[str, int],
    evidence_digest: str,
    evidence_file_count: int,
) -> str:
    rows = []
    for experiment in experiments:
        strategy = experiment.analytics_kind == AnalyticsKind.STRATEGY
        rows.append(
            "<tr>"
            f'<td><a href="{_escape(experiment.experiment_id)}/report.html">'
            f"{_escape(experiment.experiment_id)}</a></td>"
            f"<td>{_escape(experiment.experiment_name)}</td>"
            f"<td>{'Strategy' if strategy else 'Data-source qualification'}</td>"
            f"<td>{result_counts.get(experiment.experiment_id, 0):,}</td>"
            f"<td>{'Available' if strategy else 'Not applicable'}</td>"
            "</tr>"
        )
    total_series = sum(result_counts.values())
    body = f"""
<h1>Frozen-evidence analytics</h1>
<p class="lede">
  Complete reporting-only measurements for {total_series:,} separately
  registered strategy series across EXP-001 through EXP-014, with explicit
  not-applicable treatment for EXP-015 through EXP-018.
</p>
<div class="cards">
  <div class="card"><div class="label">Strategy series</div><div class="value">{total_series:,}</div></div>
  <div class="card"><div class="label">Frozen evidence files</div><div class="value">{evidence_file_count:,}</div></div>
  <div class="card"><div class="label">Evidence digest</div><div class="value"><code>{_escape(evidence_digest[:16])}…</code></div></div>
</div>
<div class="boundary">
  Every source file is hashed before calculation and after output generation.
  Rebuilds write only beneath <code>results/analytics_expansion</code>.
</div>
<div class="table-wrap"><table>
  <thead><tr><th>Experiment</th><th>Name</th><th>Kind</th><th>Series</th><th>Strategy analytics</th></tr></thead>
  <tbody>{''.join(rows)}</tbody>
</table></div>
"""
    return _page(
        title="Frozen-evidence analytics",
        eyebrow="Protected analytics expansion",
        navigation='<a href="../../reports/research_dashboard/index.html">Research dashboard</a>',
        body=body,
    )
