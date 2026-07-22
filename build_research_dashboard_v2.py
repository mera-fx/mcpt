from __future__ import annotations

import argparse
import html
import json
import math
import os
from pathlib import Path
from typing import Any

import pandas as pd

from dashboard_data_source_reports import build_data_source_reports
from dashboard_experiment_profiles import (
    DashboardProfile,
    STRATEGY_METRIC_FIELDS,
    build_dashboard_profile,
    populated_strategy_metric_count,
)
from experiment_lifecycle import list_experiment_lifecycles
from research_dashboard_library import (
    ResearchArtifact,
    build_artifact_preview,
    choose_primary_report,
    discover_artifacts,
    load_experiment_metrics,
    relative_link,
)


PROJECT_DIR = Path(__file__).resolve().parent
DASHBOARD_DIR = PROJECT_DIR / "reports" / "research_dashboard"
DASHBOARD_FILE = DASHBOARD_DIR / "index.html"
PROFILE_CSV = PROJECT_DIR / "results" / "research_dashboard_profiles.csv"
PROFILE_JSON = PROJECT_DIR / "results" / "research_dashboard_profiles.json"


STRATEGY_RESEARCH_GROUPS = (
    {
        "group_id": "btc-hourly-strategies",
        "title": "BTCUSDT Hourly Strategy Ideas",
        "description": (
            "Three separate BTCUSDT hourly strategy hypotheses tested in the "
            "same research environment. They share market and timeframe, but "
            "they are not one optimization lineage."
        ),
        "relationship": (
            "EXP-001 Donchian breakout · EXP-002 z-score mean reversion · "
            "EXP-003 volatility-compression breakout"
        ),
        "experiment_ids": ("EXP-001", "EXP-002", "EXP-003"),
    },
    {
        "group_id": "orb-transfer-lineage",
        "title": "ORB Locked-Transfer Lineage",
        "description": (
            "The original QQQ opening-range idea, its unchanged transfer to "
            "NQ/MNQ, and the later structured optimization measured against "
            "the accepted transfer control."
        ),
        "relationship": (
            "EXP-004 QQQ quick screen → EXP-005 locked NQ/MNQ transfer → "
            "EXP-006 structured optimization"
        ),
        "experiment_ids": ("EXP-004", "EXP-005", "EXP-006"),
    },
    {
        "group_id": "long-only-orb-lineage",
        "title": "Long-Only ORB Exit-Geometry Lineage",
        "description": (
            "A separate long-only opening-range branch. EXP-007 is the fixed "
            "30-minute 1R baseline and EXP-008 is its locked exit-geometry search."
        ),
        "relationship": (
            "EXP-007 fixed long-only baseline → EXP-008 exit-geometry optimization"
        ),
        "experiment_ids": ("EXP-007", "EXP-008"),
    },
    {
        "group_id": "opening-drive-lineage",
        "title": "Multi-Strategy Discovery and Opening-Drive Lineage",
        "description": (
            "The broad intraday discovery tournament, the deep validation of "
            "its opening-drive family, and the sizing study performed without "
            "changing the validated signals."
        ),
        "relationship": (
            "EXP-009 discovery tournament → EXP-010 opening-drive validation → "
            "EXP-011 position sizing"
        ),
        "experiment_ids": ("EXP-009", "EXP-010", "EXP-011"),
    },
    {
        "group_id": "extended-context-lineage",
        "title": "Extended-Hours Context Lineage",
        "description": (
            "The extended-hours discovery tournament, validation of the three "
            "locked finalists, and the descriptive behaviour and complementarity study."
        ),
        "relationship": (
            "EXP-012 context discovery → EXP-013 finalist validation → "
            "EXP-014 behaviour and complementarity"
        ),
        "experiment_ids": ("EXP-012", "EXP-013", "EXP-014"),
    },
)


def _strategy_group_for(experiment_id: str) -> dict[str, Any] | None:
    for group in STRATEGY_RESEARCH_GROUPS:
        if experiment_id in group["experiment_ids"]:
            return group
    return None


def _strategy_group_label(experiment_id: str) -> str:
    group = _strategy_group_for(experiment_id)
    if group is None:
        return "Data-source qualification"
    return str(group["title"])


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a heterogeneous research dashboard with separate strategy "
            "and data-source qualification views from saved files only."
        )
    )
    parser.add_argument("--open", action="store_true")
    return parser.parse_args()


def _safe_float(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return number if math.isfinite(number) else float("nan")


def _number(value: Any, digits: int = 3) -> str:
    number = _safe_float(value)
    return "—" if math.isnan(number) else f"{number:,.{digits}f}"


def _integer(value: Any) -> str:
    number = _safe_float(value)
    return "—" if math.isnan(number) else f"{int(round(number)):,}"


def _percent(value: Any, digits: int = 2, fraction: bool = False) -> str:
    number = _safe_float(value)
    if math.isnan(number):
        return "—"
    if fraction:
        number *= 100.0
    return f"{number:,.{digits}f}%"


def _money(value: Any) -> str:
    number = _safe_float(value)
    if math.isnan(number):
        return "—"
    sign = "−" if number < 0 else ""
    return f"{sign}${abs(number):,.2f}"


def _bool(value: Any) -> str:
    if value is True:
        return "Yes"
    if value is False:
        return "No"
    return "—"


def _status_class(value: str) -> str:
    normalized = value.upper()
    if "ACCEPTED" in normalized or "QUALIFIED" in normalized:
        return "good"
    if "REJECTED" in normalized or "FAILED" in normalized or "NOT_QUALIFIED" in normalized:
        return "bad"
    if "PENDING" in normalized or "PRE_REGISTERED" in normalized:
        return "pending"
    return "review"


def _artifact_href(artifact: ResearchArtifact) -> str:
    return relative_link(DASHBOARD_DIR, artifact.path)


def _path_href(path: str) -> str:
    if not path:
        return ""
    return relative_link(DASHBOARD_DIR, PROJECT_DIR / path)


def _metric_row(label: str, value: str, note: str = "") -> str:
    note_html = f'<span class="note">{html.escape(note)}</span>' if note else ""
    return (
        "<tr>"
        f"<th>{html.escape(label)}{note_html}</th>"
        f"<td>{html.escape(value)}</td>"
        "</tr>"
    )



def _strategy_summary_table(context: dict[str, Any]) -> str:
    rows = context.get("summary_rows")
    if not isinstance(rows, list) or not rows:
        return ""

    body = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        label = str(row.get("label", ""))
        value = str(row.get("value", "—"))
        body.append(
            "<tr>"
            f"<th>{html.escape(label)}</th>"
            f"<td>{html.escape(value)}</td>"
            "</tr>"
        )
    if not body:
        return ""
    return (
        '<h4 class="subsection-title">Experiment-specific context</h4>'
        '<table class="metric-table context-table"><tbody>'
        + "".join(body)
        + "</tbody></table>"
    )


def _strategy_comparison_table(context: dict[str, Any]) -> str:
    rows = context.get("comparison_rows")
    if not isinstance(rows, list) or not rows:
        return ""

    title = str(
        context.get(
            "comparison_title",
            "Measured comparison",
        )
    )
    note = str(context.get("comparison_note", ""))
    body = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        selected = bool(row.get("selected", False))
        row_class = ' class="selected-row"' if selected else ""
        years = "—"
        profitable_years = _safe_float(row.get("profitable_years"))
        trading_years = _safe_float(row.get("trading_years"))
        if math.isfinite(profitable_years) and math.isfinite(trading_years):
            years = f"{int(profitable_years)}/{int(trading_years)}"

        role_parts = [
            str(row.get("role", "")).strip(),
            str(row.get("note", "")).strip(),
        ]
        role = " · ".join(
            part
            for part in role_parts
            if part
        )
        family = str(row.get("family", "")).strip()
        if family and role:
            role = f"{family} · {role}"
        elif family:
            role = family

        body.append(
            f"<tr{row_class}>"
            f"<td><strong>{html.escape(str(row.get('name', '')))}</strong>"
            f"<span class=\"note\">{html.escape(role)}</span></td>"
            f"<td>{_integer(row.get('completed_trades'))}</td>"
            f"<td>{_number(row.get('profit_factor'), 3)}</td>"
            f"<td>{_percent(row.get('win_rate_percent'))}</td>"
            f"<td>{_money(row.get('average_trade_usd'))}</td>"
            f"<td>{_money(row.get('net_profit_usd'))}</td>"
            f"<td>{_money(row.get('maximum_drawdown_usd'))}</td>"
            f"<td>{_number(row.get('net_profit_to_drawdown'), 3)}</td>"
            f"<td>{years}</td>"
            f"<td>{_money(row.get('two_tick_net_profit_usd'))}</td>"
            "</tr>"
        )

    if not body:
        return ""

    note_html = (
        f'<p class="muted">{html.escape(note)}</p>'
        if note
        else ""
    )
    return (
        f'<h4 class="subsection-title">{html.escape(title)}</h4>'
        + note_html
        + '<div class="table-wrap"><table class="comparison-table">'
        "<thead><tr>"
        "<th>Candidate / method</th>"
        "<th>Trades</th>"
        "<th>PF</th>"
        "<th>Win rate</th>"
        "<th>Average trade</th>"
        "<th>Net profit</th>"
        "<th>Max DD</th>"
        "<th>Net/DD</th>"
        "<th>Profitable years</th>"
        "<th>Two-tick net</th>"
        "</tr></thead><tbody>"
        + "".join(body)
        + "</tbody></table></div>"
    )


def _strategy_pair_table(context: dict[str, Any]) -> str:
    rows = context.get("pair_rows")
    if not isinstance(rows, list) or not rows:
        return ""

    title = str(
        context.get(
            "pair_title",
            "Pair diagnostics",
        )
    )
    note = str(context.get("pair_note", ""))
    body = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        years = "—"
        profitable = _safe_float(row.get("profitable_years"))
        total = _safe_float(row.get("total_years"))
        if math.isfinite(profitable) and math.isfinite(total):
            years = f"{int(profitable)}/{int(total)}"
        body.append(
            "<tr>"
            f"<td><strong>{html.escape(str(row.get('name', '')))}</strong>"
            f"<span class=\"note\">"
            f"{html.escape(str(row.get('components', '')))}</span></td>"
            f"<td>{_money(row.get('net_profit_usd'))}</td>"
            f"<td>{_money(row.get('maximum_drawdown_usd'))}</td>"
            f"<td>{_number(row.get('net_profit_to_drawdown'), 3)}</td>"
            f"<td>{years}</td>"
            f"<td>{_money(row.get('worst_year_usd'))}</td>"
            f"<td>{_bool(row.get('diagnostic_not_executable_portfolio'))}</td>"
            "</tr>"
        )

    note_html = (
        f'<p class="muted">{html.escape(note)}</p>'
        if note
        else ""
    )
    return (
        f'<h4 class="subsection-title">{html.escape(title)}</h4>'
        + note_html
        + '<div class="table-wrap"><table class="comparison-table">'
        "<thead><tr>"
        "<th>Diagnostic pair</th>"
        "<th>Net profit</th>"
        "<th>Max DD</th>"
        "<th>Net/DD</th>"
        "<th>Profitable years</th>"
        "<th>Worst year</th>"
        "<th>Not executable</th>"
        "</tr></thead><tbody>"
        + "".join(body)
        + "</tbody></table></div>"
    )


def _strategy_context_html(profile: DashboardProfile) -> str:
    context = profile.strategy_context
    if not context:
        return ""
    return (
        _strategy_summary_table(context)
        + _strategy_comparison_table(context)
        + _strategy_pair_table(context)
    )


def _strategy_table(profile: DashboardProfile) -> str:
    metrics = profile.metrics
    rows = [
        _metric_row(
            "Dashboard headline",
            str(metrics.get("headline_name") or "Saved strategy result"),
            str(
                metrics.get("metric_scope")
                or (
                    "Single saved-result headline. Open the primary report "
                    "for full experiment context."
                )
            ),
        ),
        _metric_row("Profit Factor", _number(metrics.get("profit_factor"))),
        _metric_row("Net profit", _money(metrics.get("net_profit_usd"))),
        _metric_row("Win rate", _percent(metrics.get("win_rate_percent"))),
        _metric_row("Average trade", _money(metrics.get("average_trade_usd"))),
        _metric_row("Maximum drawdown", _money(metrics.get("max_drawdown_usd"))),
        _metric_row(
            "Maximum drawdown %",
            _percent(metrics.get("max_drawdown_percent")),
        ),
        _metric_row(
            "Net profit / drawdown",
            _number(metrics.get("net_profit_to_drawdown"), 3),
        ),
        _metric_row("Total return", _percent(metrics.get("total_return_percent"))),
        _metric_row("Completed trades", _integer(metrics.get("total_trades"))),
        _metric_row("MCPT p-value", _number(metrics.get("mcpt_p_value"), 4)),
        _metric_row(
            "Metric coverage",
            f"{populated_strategy_metric_count(metrics)}/{len(STRATEGY_METRIC_FIELDS)}",
            (
                "Blank values are displayed honestly rather than inferred "
                "from unrelated files."
            ),
        ),
        _metric_row(
            "Metric source",
            str(metrics.get("metric_source") or "No adapter yet"),
        ),
    ]
    headline = (
        '<table class="metric-table"><tbody>'
        + "".join(rows)
        + "</tbody></table>"
    )
    return headline + _strategy_context_html(profile)


def _data_table(profile: DashboardProfile) -> str:
    values = profile.data_measurements
    rows = [
        _metric_row("Classification", profile.result_state),
        _metric_row(
            "Result source",
            profile.result_state_source or "Lifecycle registry",
        ),
        _metric_row("Result phase", str(values.get("result_phase") or "—")),
        _metric_row(
            "Classification scope",
            str(values.get("classification_scope") or "—"),
        ),
        _metric_row("Client version", str(values.get("client_version") or "—")),
        _metric_row("Dataset", str(values.get("dataset") or "—")),
        _metric_row("Schema", str(values.get("schema") or "—")),
        _metric_row("Contract type", str(values.get("contract_type") or "—")),
        _metric_row(
            "Continuous-series method",
            str(values.get("continuous_series_method") or "—"),
        ),
        _metric_row("Roll method", str(values.get("roll_method") or "—")),
        _metric_row(
            "Price adjustment",
            str(values.get("price_adjustment") or "—"),
        ),
        _metric_row(
            "Volume semantics",
            str(values.get("volume_semantics") or "—"),
        ),
        _metric_row("Sample windows", _integer(values.get("sample_windows"))),
        _metric_row(
            "Structural windows",
            _integer(values.get("structural_windows")),
        ),
        _metric_row(
            "Initial windows measured",
            _integer(values.get("initial_windows_measured")),
        ),
        _metric_row(
            "Repeatability windows measured",
            _integer(values.get("repeatability_windows_measured")),
        ),
        _metric_row(
            "Total vendor rows",
            _integer(values.get("total_vendor_rows")),
        ),
        _metric_row(
            "Minimum regular trade-minute coverage",
            _percent(
                values.get("regular_trade_minute_coverage"),
                6,
                fraction=True,
            ),
        ),
        _metric_row(
            "Minimum extended trade-minute coverage",
            _percent(
                values.get("extended_trade_minute_coverage"),
                6,
                fraction=True,
            ),
        ),
        _metric_row(
            "Minimum expected-minute completeness",
            _percent(
                values.get("minimum_expected_minute_completeness"),
                6,
                fraction=True,
            ),
        ),
        _metric_row(
            "Minimum matched-timestamp share",
            _percent(
                values.get("minimum_matched_timestamp_share"),
                6,
                fraction=True,
            ),
        ),
        _metric_row(
            "Minimum close within one tick",
            _percent(
                values.get("minimum_close_within_one_tick_share"),
                6,
                fraction=True,
            ),
        ),
        _metric_row("Estimated cost", _money(values.get("estimated_cost_usd"))),
        _metric_row(
            "Identity mismatches",
            _integer(values.get("identity_mismatch_rows")),
        ),
        _metric_row(
            "Duplicate timestamps",
            _integer(values.get("duplicate_timestamp_rows")),
        ),
        _metric_row(
            "Invalid OHLC rows",
            _integer(values.get("invalid_ohlc_rows")),
        ),
        _metric_row(
            "Negative-volume rows",
            _integer(values.get("negative_volume_rows")),
        ),
        _metric_row(
            "Nonfinite OHLCV rows",
            _integer(values.get("nonfinite_ohlcv_rows")),
        ),
        _metric_row(
            "Off-tick OHLC values",
            _integer(values.get("off_tick_ohlc_values")),
        ),
        _metric_row(
            "Futures rows catalogued",
            _integer(values.get("futures_rows")),
        ),
        _metric_row("NQ candidates", _integer(values.get("nq_candidates"))),
        _metric_row("MNQ candidates", _integer(values.get("mnq_candidates"))),
        _metric_row("NQ identified", _bool(values.get("nq_identified"))),
        _metric_row("MNQ identified", _bool(values.get("mnq_identified"))),
        _metric_row(
            "Contract method resolved",
            _bool(values.get("contract_method_resolved")),
        ),
        _metric_row(
            "Roll method resolved",
            _bool(values.get("roll_method_resolved")),
        ),
        _metric_row(
            "Price adjustment resolved",
            _bool(values.get("price_adjustment_resolved")),
        ),
        _metric_row(
            "History download authorized",
            _bool(values.get("history_download_authorized")),
        ),
        _metric_row(
            "Full history downloaded",
            _bool(values.get("history_downloaded")),
        ),
        _metric_row(
            "Primary source qualified",
            _bool(values.get("primary_source_qualified")),
        ),
        _metric_row(
            "Quantower replaced",
            _bool(values.get("quantower_replaced")),
        ),
        _metric_row(
            "Exchange-accuracy claim",
            _bool(values.get("exchange_accuracy_claim")),
        ),
        _metric_row("Strategy run", _bool(values.get("strategy_run"))),
        _metric_row("Optimization run", _bool(values.get("optimization_run"))),
        _metric_row(
            "Paper trading authorized",
            _bool(values.get("paper_trading_authorized")),
        ),
        _metric_row(
            "Live trading authorized",
            _bool(values.get("live_trading_authorized")),
        ),
    ]
    return (
        '<table class="metric-table"><tbody>'
        + "".join(rows)
        + "</tbody></table>"
    )


def _artifact_list(
    experiment_id: str,
    artifacts: list[ResearchArtifact],
    previews: dict[str, Path | None],
) -> str:
    experiment_artifacts = [
        artifact for artifact in artifacts
        if artifact.experiment_id == experiment_id
    ]
    if not experiment_artifacts:
        return '<p class="muted">No linked artifacts.</p>'

    rows: list[str] = []
    for artifact in experiment_artifacts:
        href = _artifact_href(artifact)
        preview = previews.get(artifact.project_relative_path)
        preview_link = ""
        if preview is not None:
            preview_href = relative_link(DASHBOARD_DIR, preview)
            preview_link = (
                f' · <a href="{html.escape(preview_href)}">Preview</a>'
            )
        rows.append(
            "<tr>"
            f"<td>{html.escape(artifact.category)}</td>"
            f"<td>{html.escape(artifact.label)}</td>"
            f"<td><code>{html.escape(artifact.project_relative_path)}</code></td>"
            f'<td><a href="{html.escape(href)}">Open</a>{preview_link}</td>'
            "</tr>"
        )
    return (
        '<div class="table-wrap"><table class="artifact-table">'
        "<thead><tr><th>Type</th><th>Name</th><th>Location</th><th>Open</th></tr></thead>"
        "<tbody>" + "".join(rows) + "</tbody></table></div>"
    )


def _experiment_block(
    profile: DashboardProfile,
    artifacts: list[ResearchArtifact],
    previews: dict[str, Path | None],
) -> str:
    state_class = _status_class(profile.result_state)
    missing = ""
    if profile.missing_items:
        missing = (
            '<div class="warning"><strong>Dashboard coverage gaps</strong><ul>'
            + "".join(f"<li>{html.escape(item)}</li>" for item in profile.missing_items)
            + "</ul></div>"
        )

    report_link = (
        f'<a class="button" href="{html.escape(_path_href(profile.primary_report_path))}">'
        "Open primary report</a>"
        if profile.primary_report_path
        else '<span class="button disabled">No primary report</span>'
    )
    prereg_link = (
        f'<a class="button" href="{html.escape(_path_href(profile.preregistration_file))}">'
        "Open preregistration</a>"
        if profile.preregistration_file
        else ""
    )

    metric_html = (
        _strategy_table(profile)
        if profile.research_type == "strategy"
        else _data_table(profile)
    )

    searchable = " ".join(
        (
            profile.experiment_id,
            profile.experiment_name,
            profile.research_type_label,
            profile.stage,
            profile.result_state,
            profile.market_name,
            profile.strategy_name,
            profile.stage_reason,
        )
    ).lower()

    open_attribute = ""
    metric_title = (
        "Strategy measurements"
        if profile.research_type == "strategy"
        else "Data-source measurements"
    )
    return f'''
<details class="experiment" id="{html.escape(profile.experiment_id.lower())}"
  data-search="{html.escape(searchable)}"{open_attribute}>
  <summary>
    <span class="exp-id">{html.escape(profile.experiment_id)}</span>
    <span class="exp-title">{html.escape(profile.experiment_name)}</span>
    <span class="pill type">{html.escape(profile.research_type_label)}</span>
    <span class="pill {state_class}">{html.escape(profile.result_state)}</span>
    <span class="artifact-count">{profile.artifact_count:,} files</span>
  </summary>
  <div class="experiment-body">
    <div class="metadata">
      <div><span>Lifecycle</span><strong>{html.escape(profile.stage)}</strong></div>
      <div><span>Market</span><strong>{html.escape(profile.market_name)}</strong></div>
      <div><span>Timeframe</span><strong>{html.escape(profile.timeframe)}</strong></div>
      <div><span>Strategy / subject</span><strong>{html.escape(profile.strategy_name)}</strong></div>
    </div>

    <section class="narrative">
      <h3>Research question</h3>
      <p>{html.escape(profile.hypothesis)}</p>
      <h3>Current evidence and decision</h3>
      <p>{html.escape(profile.stage_reason)}</p>
      <h3>Next action</h3>
      <p>{html.escape(profile.next_action)}</p>
    </section>

    <div class="actions">{report_link}{prereg_link}</div>
    {missing}

    <section>
      <h3>{metric_title}</h3>
      {metric_html}
    </section>

    <details class="artifacts">
      <summary>Research files ({profile.artifact_count:,})</summary>
      {_artifact_list(profile.experiment_id, artifacts, previews)}
    </details>
  </div>
</details>
'''


def _strategy_group_block(
    group: dict[str, Any],
    profiles: list[DashboardProfile],
    artifacts: list[ResearchArtifact],
    previews: dict[str, Path | None],
) -> str:
    experiment_ids = tuple(group["experiment_ids"])
    profile_by_id = {profile.experiment_id: profile for profile in profiles}
    members = [
        profile_by_id[experiment_id]
        for experiment_id in experiment_ids
        if experiment_id in profile_by_id
    ]
    if not members:
        return ""

    blocks = "".join(
        _experiment_block(profile, artifacts, previews)
        for profile in members
    )
    searchable = " ".join(
        [
            str(group["title"]),
            str(group["description"]),
            str(group["relationship"]),
        ]
        + [profile.experiment_id for profile in members]
        + [profile.experiment_name for profile in members]
    ).lower()
    range_label = " · ".join(profile.experiment_id for profile in members)

    return f'''
<details class="research-group" id="group-{html.escape(str(group['group_id']))}"
  data-search="{html.escape(searchable)}">
  <summary>
    <span class="group-heading">
      <strong>{html.escape(str(group['title']))}</strong>
      <span>{html.escape(range_label)}</span>
    </span>
    <span class="group-count">{len(members)} experiments</span>
  </summary>
  <div class="research-group-body">
    <p class="group-description">{html.escape(str(group['description']))}</p>
    <p class="lineage-flow">{html.escape(str(group['relationship']))}</p>
    {blocks}
  </div>
</details>
'''


def _overview_row(profile: DashboardProfile) -> str:
    report = "Yes" if profile.primary_report_path else "No"
    if profile.research_type == "strategy":
        results = f"{populated_strategy_metric_count(profile.metrics)}/{len(STRATEGY_METRIC_FIELDS)} metrics"
    else:
        results = profile.result_state
    group_label = _strategy_group_label(profile.experiment_id)
    gap = "Complete" if not profile.missing_items else f"{len(profile.missing_items)} gap(s)"
    searchable = (
        profile.experiment_id
        + " "
        + profile.experiment_name
        + " "
        + profile.result_state
        + " "
        + group_label
    ).lower()
    return (
        f'<tr data-search="{html.escape(searchable)}">'
        f'<td><a href="#{html.escape(profile.experiment_id.lower())}">{html.escape(profile.experiment_id)}</a></td>'
        f"<td>{html.escape(profile.experiment_name)}</td>"
        f"<td>{html.escape(group_label)}</td>"
        f"<td>{html.escape(profile.research_type_label)}</td>"
        f"<td>{html.escape(profile.stage)}</td>"
        f"<td>{html.escape(results)}</td>"
        f"<td>{report}</td>"
        f"<td>{profile.artifact_count:,}</td>"
        f"<td>{html.escape(gap)}</td>"
        "</tr>"
    )


def build_html(
    profiles: list[DashboardProfile],
    artifacts: list[ResearchArtifact],
    previews: dict[str, Path | None],
) -> str:
    strategy_profiles = [item for item in profiles if item.research_type == "strategy"]
    data_profiles = [item for item in profiles if item.research_type == "data_source"]
    accepted = sum(item.stage == "ACCEPTED_FOR_PAPER_TESTING" for item in profiles)
    review = sum(item.stage in {"REVIEW", "PRE_REGISTERED"} for item in profiles)
    missing_reports = sum(not item.primary_report_path for item in profiles)
    adapter_gaps = sum(bool(item.missing_items) for item in profiles)

    overview = "".join(_overview_row(item) for item in profiles)
    strategy = "".join(
        _strategy_group_block(
            group,
            strategy_profiles,
            artifacts,
            previews,
        )
        for group in STRATEGY_RESEARCH_GROUPS
    )
    data = "".join(_experiment_block(item, artifacts, previews) for item in data_profiles)

    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Quantitative Research Dashboard</title>
<style>
:root {{
  color-scheme: dark;
  --bg: #0a1020;
  --panel: #111a2e;
  --panel2: #15213a;
  --text: #e8eef8;
  --muted: #9eacc2;
  --line: #2b3a58;
  --accent: #86d7ff;
  --good: #72d89a;
  --bad: #ff8d8d;
  --pending: #ffd37a;
  --review: #b7b8ff;
}}
* {{ box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}
body {{
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: Inter, "Segoe UI", Arial, sans-serif;
  line-height: 1.5;
}}
header {{
  position: sticky;
  top: 0;
  z-index: 10;
  background: rgba(10, 16, 32, 0.96);
  border-bottom: 1px solid var(--line);
  backdrop-filter: blur(10px);
}}
.header-inner {{
  width: min(1600px, calc(100% - 32px));
  margin: 0 auto;
  padding: 14px 0;
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: center;
  flex-wrap: wrap;
}}
.brand {{ font-weight: 800; }}
nav {{ display: flex; gap: 14px; flex-wrap: wrap; }}
a {{ color: var(--accent); text-decoration: none; }}
main {{
  width: min(1600px, calc(100% - 32px));
  margin: 28px auto 80px;
}}
.hero {{
  border: 1px solid var(--line);
  background: linear-gradient(135deg, var(--panel), #0d2840);
  border-radius: 18px;
  padding: 28px;
}}
.hero h1 {{ margin: 0 0 8px; font-size: clamp(2rem, 4vw, 3.4rem); }}
.hero p {{ color: var(--muted); max-width: 1000px; }}
.stats {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 12px;
  margin-top: 22px;
}}
.stat {{
  border: 1px solid var(--line);
  background: rgba(17, 26, 46, 0.75);
  padding: 16px;
  border-radius: 14px;
}}
.stat strong {{ display: block; font-size: 1.8rem; }}
.stat span {{ color: var(--muted); }}
.toolbar {{
  display: flex;
  gap: 10px;
  margin: 18px 0;
  flex-wrap: wrap;
}}
input, button, .button {{
  border: 1px solid var(--line);
  background: var(--panel);
  color: var(--text);
  border-radius: 10px;
  padding: 10px 13px;
  font: inherit;
}}
input {{ min-width: min(520px, 100%); flex: 1; }}
button, .button {{ cursor: pointer; }}
.button.disabled {{ color: var(--muted); cursor: default; }}
.section-title {{
  margin: 38px 0 14px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--line);
}}
.table-wrap {{
  overflow: auto;
  border: 1px solid var(--line);
  border-radius: 14px;
}}
table {{
  width: 100%;
  border-collapse: collapse;
  background: var(--panel);
}}
th, td {{
  padding: 10px 12px;
  border-bottom: 1px solid var(--line);
  text-align: left;
  vertical-align: top;
}}
thead th {{
  position: sticky;
  top: 61px;
  background: var(--panel2);
  z-index: 2;
}}
.metric-table th {{ width: 42%; color: var(--muted); font-weight: 600; }}
.metric-table td {{ font-weight: 700; }}
.context-table {{ margin-top: 10px; }}
.subsection-title {{
  margin: 24px 0 8px;
  color: var(--muted);
  font-size: 0.95rem;
}}
.comparison-table th, .comparison-table td {{
  white-space: nowrap;
}}
.comparison-table td:first-child {{
  min-width: 260px;
  white-space: normal;
}}
.selected-row {{
  background: rgba(134, 215, 255, 0.08);
}}
.note {{ display: block; font-size: 0.78rem; font-weight: 400; margin-top: 4px; }}
.research-group {{
  border: 1px solid var(--line);
  border-radius: 18px;
  background: rgba(13, 40, 64, 0.34);
  margin: 18px 0;
  overflow: hidden;
}}
.research-group > summary {{
  display: grid;
  grid-template-columns: minmax(260px, 1fr) auto;
  gap: 16px;
  align-items: center;
  padding: 18px 20px;
  cursor: pointer;
  list-style: none;
}}
.research-group > summary::-webkit-details-marker {{ display: none; }}
.group-heading strong {{ display: block; font-size: 1.08rem; }}
.group-heading span {{ display: block; color: var(--accent); margin-top: 3px; font-size: 0.82rem; }}
.group-count {{ color: var(--muted); white-space: nowrap; }}
.research-group-body {{
  border-top: 1px solid var(--line);
  padding: 18px;
}}
.group-description {{ margin: 0 0 8px; color: var(--muted); max-width: 1100px; }}
.lineage-flow {{
  margin: 0 0 18px;
  border-left: 3px solid var(--accent);
  background: rgba(134, 215, 255, 0.06);
  padding: 10px 12px;
  font-weight: 700;
}}
.research-group .experiment:first-of-type {{ margin-top: 0; }}
.research-group .experiment:last-child {{ margin-bottom: 0; }}
.experiment {{
  border: 1px solid var(--line);
  border-radius: 16px;
  background: var(--panel);
  margin: 14px 0;
  overflow: hidden;
}}
.experiment > summary {{
  display: grid;
  grid-template-columns: 90px minmax(260px, 1fr) auto auto auto;
  gap: 12px;
  align-items: center;
  padding: 16px 18px;
  cursor: pointer;
  list-style: none;
}}
.experiment > summary::-webkit-details-marker {{ display: none; }}
.exp-id {{ font-weight: 800; color: var(--accent); }}
.exp-title {{ font-weight: 700; }}
.artifact-count {{ color: var(--muted); white-space: nowrap; }}
.pill {{
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 5px 9px;
  font-size: 0.78rem;
  white-space: nowrap;
}}
.pill.good {{ color: var(--good); }}
.pill.bad {{ color: var(--bad); }}
.pill.pending {{ color: var(--pending); }}
.pill.review {{ color: var(--review); }}
.pill.type {{ color: var(--accent); }}
.experiment-body {{
  padding: 20px;
  border-top: 1px solid var(--line);
}}
.metadata {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: 10px;
  margin-bottom: 20px;
}}
.metadata div {{
  background: var(--panel2);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 12px;
}}
.metadata span {{ display: block; color: var(--muted); font-size: 0.8rem; }}
.narrative {{
  display: grid;
  grid-template-columns: 210px minmax(0, 1fr);
  gap: 8px 18px;
}}
.narrative h3 {{ margin: 0; font-size: 0.95rem; color: var(--muted); }}
.narrative p {{ margin: 0 0 14px; }}
.actions {{ display: flex; gap: 10px; flex-wrap: wrap; margin: 12px 0 18px; }}
.warning {{
  border: 1px solid #7a5d24;
  background: #2a2212;
  border-radius: 12px;
  padding: 12px 16px;
  margin: 14px 0;
}}
.warning ul {{ margin-bottom: 0; }}
.artifacts {{ margin-top: 18px; }}
.artifacts > summary {{ cursor: pointer; font-weight: 700; padding: 10px 0; }}
.muted {{ color: var(--muted); }}
.hidden {{ display: none !important; }}
.footer {{ color: var(--muted); margin-top: 28px; }}
@media (max-width: 980px) {{
  .experiment > summary {{ grid-template-columns: 80px 1fr; }}
  .pill, .artifact-count {{ justify-self: start; }}
  .narrative {{ grid-template-columns: 1fr; }}
  thead th {{ top: 100px; }}
}}
</style>
</head>
<body>
<header>
  <div class="header-inner">
    <div class="brand">Quantitative Research Dashboard</div>
    <nav>
      <a href="#overview">Overview</a>
      <a href="#strategy-research">Strategy research</a>
      <a href="#data-research">Data-source research</a>
      <a href="strategy_comparison.html">Existing strategy comparison</a>
    </nav>
  </div>
</header>
<main>
<section class="hero">
  <h1>Different experiments, appropriate evidence</h1>
  <p>
    Strategy experiments and data-source qualification experiments are displayed
    separately. Missing metric adapters and missing visual reports are shown
    explicitly. This page reads saved research files only and does not rerun
    strategies, optimization, MCPT, downloads or qualification requests.
  </p>
  <div class="stats">
    <div class="stat"><strong>{len(profiles)}</strong><span>Total experiments</span></div>
    <div class="stat"><strong>{len(strategy_profiles)}</strong><span>Strategy experiments</span></div>
    <div class="stat"><strong>{len(data_profiles)}</strong><span>Data-source experiments</span></div>
    <div class="stat"><strong>{accepted}</strong><span>Accepted for paper testing</span></div>
    <div class="stat"><strong>{review}</strong><span>Review or preregistered</span></div>
    <div class="stat"><strong>{missing_reports}</strong><span>Without dedicated report</span></div>
    <div class="stat"><strong>{adapter_gaps}</strong><span>With dashboard coverage gaps</span></div>
    <div class="stat"><strong>{len(artifacts):,}</strong><span>Linked artifacts</span></div>
  </div>
</section>

<div class="toolbar">
  <input id="search" type="search"
    placeholder="Search experiment ID, name, stage, classification, market or strategy...">
  <button id="expand" type="button">Expand all</button>
  <button id="collapse" type="button">Collapse all</button>
</div>

<section id="overview">
  <h2 class="section-title">Research coverage overview</h2>
  <div class="table-wrap">
    <table id="overview-table">
      <thead>
        <tr>
          <th>Experiment</th><th>Name</th><th>Research group</th><th>Research type</th>
          <th>Lifecycle</th><th>Parsed result</th><th>Primary report</th><th>Files</th><th>Coverage</th>
        </tr>
      </thead>
      <tbody>{overview}</tbody>
    </table>
  </div>
</section>

<section id="strategy-research">
  <h2 class="section-title">Strategy research</h2>
  <p class="muted">
    Experiments are grouped by research lineage so related work is kept together
    and separate branches remain visibly separate. Every group and experiment
    starts collapsed. Arrows show research dependency, not an automatic winner
    or trading authorization.
  </p>
  {strategy}
</section>

<section id="data-research">
  <h2 class="section-title">Data-source research · EXP-015 through EXP-018</h2>
  <p class="muted">
    Data-source records use identity, structural quality, completeness,
    repeatability, access cost and claim boundaries rather than trading metrics.
  </p>
  {data}
</section>

<p class="footer">
  Generated from lifecycle records and saved files. No market-data request,
  strategy execution, optimization, MCPT, bootstrap or paper simulator was run.
</p>
</main>

<script>
const search = document.getElementById("search");
const experiments = Array.from(document.querySelectorAll(".experiment"));
const researchGroups = Array.from(document.querySelectorAll(".research-group"));
const overviewRows = Array.from(document.querySelectorAll("#overview-table tbody tr"));
const overviewLinks = Array.from(document.querySelectorAll('#overview-table a[href^="#exp-"]'));

document.getElementById("expand").addEventListener("click", () => {{
  researchGroups.forEach(item => item.open = true);
  experiments.forEach(item => item.open = true);
}});
document.getElementById("collapse").addEventListener("click", () => {{
  experiments.forEach(item => item.open = false);
  researchGroups.forEach(item => item.open = false);
}});

overviewLinks.forEach(link => {{
  link.addEventListener("click", () => {{
    const target = document.querySelector(link.getAttribute("href"));
    if (!target) return;
    const group = target.closest(".research-group");
    if (group) group.open = true;
    target.open = true;
  }});
}});

search.addEventListener("input", () => {{
  const query = search.value.trim().toLowerCase();
  experiments.forEach(item => {{
    const visible = !query || (item.dataset.search || "").includes(query);
    item.classList.toggle("hidden", !visible);
    if (query && visible) item.open = true;
  }});
  researchGroups.forEach(group => {{
    const groupMatches = Boolean(
      query && (group.dataset.search || "").includes(query)
    );
    const members = Array.from(group.querySelectorAll(".experiment"));
    if (groupMatches) {{
      members.forEach(item => item.classList.remove("hidden"));
    }}
    const hasVisibleMember = members.some(
      item => !item.classList.contains("hidden")
    );
    const visible = !query || groupMatches || hasVisibleMember;
    group.classList.toggle("hidden", !visible);
    if (query && visible) group.open = true;
  }});
  overviewRows.forEach(item => {{
    const visible = !query || (item.dataset.search || "").includes(query);
    item.classList.toggle("hidden", !visible);
  }});
}});
</script>
</body>
</html>
'''



def _build_profiles(
    lifecycles: list[Any],
    artifacts: list[ResearchArtifact],
) -> list[DashboardProfile]:
    profiles: list[DashboardProfile] = []
    for lifecycle in lifecycles:
        experiment_artifacts = [
            artifact
            for artifact in artifacts
            if artifact.experiment_id == lifecycle.experiment_id
        ]
        primary = choose_primary_report(
            experiment_artifacts,
            lifecycle.experiment_id,
        )
        metrics = load_experiment_metrics(
            PROJECT_DIR,
            lifecycle.experiment_id,
        )
        profiles.append(
            build_dashboard_profile(
                project_dir=PROJECT_DIR,
                lifecycle=lifecycle,
                artifacts=artifacts,
                primary_report=primary,
                metrics=metrics,
            )
        )
    return sorted(
        profiles,
        key=lambda item: int(
            item.experiment_id.split("-")[1]
        ),
    )


def main() -> None:
    arguments = parse_arguments()
    lifecycles = list_experiment_lifecycles()
    experiment_ids = [
        item.experiment_id
        for item in lifecycles
    ]

    DASHBOARD_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )
    PROFILE_CSV.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    initial_artifacts = discover_artifacts(
        PROJECT_DIR,
        experiment_ids,
    )
    provisional_profiles = _build_profiles(
        lifecycles,
        initial_artifacts,
    )
    generated_reports = build_data_source_reports(
        PROJECT_DIR,
        provisional_profiles,
    )

    artifacts = discover_artifacts(
        PROJECT_DIR,
        experiment_ids,
    )

    previews: dict[str, Path | None] = {}
    for artifact in artifacts:
        previews[
            artifact.project_relative_path
        ] = build_artifact_preview(
            artifact,
            DASHBOARD_DIR,
        )

    profiles = _build_profiles(
        lifecycles,
        artifacts,
    )

    DASHBOARD_FILE.write_text(
        build_html(
            profiles,
            artifacts,
            previews,
        ),
        encoding="utf-8",
    )

    serializable = [
        profile.to_dict()
        for profile in profiles
    ]
    PROFILE_JSON.write_text(
        json.dumps(
            serializable,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    rows = []
    for profile in profiles:
        rows.append(
            {
                "experiment_id": profile.experiment_id,
                "experiment_name": profile.experiment_name,
                "research_type": profile.research_type,
                "lifecycle_stage": profile.stage,
                "result_state": profile.result_state,
                "result_state_source": profile.result_state_source,
                "artifact_count": profile.artifact_count,
                "primary_report_path": profile.primary_report_path,
                "strategy_metric_count": (
                    populated_strategy_metric_count(
                        profile.metrics
                    )
                ),
                "strategy_adapter": (
                    profile.strategy_context.get(
                        "adapter_id",
                        "",
                    )
                ),
                "dashboard_gap_count": len(
                    profile.missing_items
                ),
                "dashboard_gaps": " | ".join(
                    profile.missing_items
                ),
            }
        )
    pd.DataFrame(rows).to_csv(
        PROFILE_CSV,
        index=False,
    )

    strategy_count = sum(
        item.research_type == "strategy"
        for item in profiles
    )
    data_count = sum(
        item.research_type == "data_source"
        for item in profiles
    )
    adapter_count = sum(
        bool(item.strategy_context)
        for item in profiles
    )
    gap_count = sum(
        bool(item.missing_items)
        for item in profiles
    )

    print()
    print("Research dashboard v2 phase 2 created.")
    print(
        f"Experiments:              {len(profiles)}"
    )
    print(
        f"Strategy experiments:     {strategy_count}"
    )
    print(
        f"Data-source experiments:  {data_count}"
    )
    print(
        f"Specific strategy adapters: {adapter_count}"
    )
    print(
        f"Generated data reports:   {len(generated_reports)}"
    )
    print(
        f"Linked artifacts:         {len(artifacts)}"
    )
    print(
        f"Experiments with gaps:    {gap_count}"
    )
    print(
        f"Dashboard:                {DASHBOARD_FILE}"
    )
    print(
        f"Coverage CSV:             {PROFILE_CSV}"
    )
    print(
        f"Profile JSON:             {PROFILE_JSON}"
    )
    print("Research rerun:           False")
    print("Market-data request:      False")

    if arguments.open:
        if hasattr(os, "startfile"):
            os.startfile(DASHBOARD_FILE)
        else:
            print(
                "--open is automatically "
                "supported on Windows only."
            )


if __name__ == "__main__":
    main()
