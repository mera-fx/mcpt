from __future__ import annotations

import argparse
import html
import json
import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from experiment_config import list_experiments
from experiment_lifecycle import (
    format_stage_label,
    get_experiment_lifecycle,
    list_experiment_lifecycles,
)
from research_dashboard_library import (
    ResearchArtifact,
    build_artifact_preview,
    choose_primary_report,
    discover_artifacts,
    load_experiment_metrics,
    relative_link,
)


PROJECT_DIR = Path(__file__).resolve().parent


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build one local research hub containing "
            "every experiment report, decision, audit "
            "and saved result file."
        )
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help=(
            "Open the dashboard after building it. "
            "Supported on Windows through os.startfile."
        ),
    )
    return parser.parse_args()


def resolve(path: Path) -> Path:
    if path.is_absolute():
        return path
    return PROJECT_DIR / path


def read_csv_optional(
    path: Path,
    *,
    index_col: int | None = None,
) -> pd.DataFrame | None:
    if not path.exists():
        return None
    return pd.read_csv(
        path,
        index_col=index_col,
    )


def read_json_optional(
    path: Path,
) -> dict[str, Any]:
    if not path.exists():
        return {}

    value = json.loads(
        path.read_text(encoding="utf-8")
    )
    return value if isinstance(value, dict) else {}


def get_row(
    table: pd.DataFrame | None,
    row_name: str,
) -> pd.Series | None:
    if table is None or table.empty:
        return None
    if row_name not in table.index:
        return None
    return table.loc[row_name]


def value_from_row(
    row: pd.Series | None,
    column: str,
) -> float:
    if row is None or column not in row:
        return float("nan")

    try:
        return float(row[column])
    except (TypeError, ValueError):
        return float("nan")


def safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def format_number(
    value: Any,
    decimals: int = 3,
) -> str:
    number = safe_float(value)
    if np.isnan(number):
        return "—"
    if np.isposinf(number):
        return "∞"
    if np.isneginf(number):
        return "−∞"
    return f"{number:,.{decimals}f}"


def format_percent(
    value: Any,
    decimals: int = 2,
) -> str:
    number = safe_float(value)
    if np.isnan(number):
        return "—"
    return f"{number:,.{decimals}f}%"


def format_currency(
    value: Any,
) -> str:
    number = safe_float(value)
    if np.isnan(number):
        return "—"
    sign = "−" if number < 0 else ""
    return f"{sign}${abs(number):,.2f}"


def format_integer(
    value: Any,
) -> str:
    number = safe_float(value)
    if np.isnan(number):
        return "—"
    return f"{int(round(number)):,}"


def status_class(status: str) -> str:
    return status.lower().replace("_", "-")


def _base_record(
    *,
    lifecycle,
    configured: bool,
) -> dict[str, Any]:
    return {
        "experiment_id": lifecycle.experiment_id,
        "experiment_name": lifecycle.experiment_name,
        "hypothesis": lifecycle.hypothesis,
        "market_name": lifecycle.market_name,
        "timeframe": lifecycle.timeframe,
        "strategy_name": lifecycle.strategy_name,
        "status": lifecycle.stage,
        "status_label": format_stage_label(
            lifecycle.stage
        ),
        "stage_reason": lifecycle.stage_reason,
        "next_action": lifecycle.next_action,
        "preregistration_file": (
            str(lifecycle.preregistration_file)
            if lifecycle.preregistration_file is not None
            else ""
        ),
        "configured": configured,
        "has_results": False,
        "report_exists": False,
        "report_file": Path(),
        "fixed_return_percent": np.nan,
        "fixed_max_drawdown_percent": np.nan,
        "fixed_trade_profit_factor": np.nan,
        "fixed_trades": np.nan,
        "walkforward_return_percent": np.nan,
        "walkforward_max_drawdown_percent": np.nan,
        "walkforward_trade_profit_factor": np.nan,
        "walkforward_trades": np.nan,
        "mcpt_p_value": np.nan,
        "best_in_sample_bar_profit_factor": np.nan,
        "best_in_sample_parameters": {},
        "average_winner_percent": np.nan,
        "average_loser_percent": np.nan,
        "payoff_ratio": np.nan,
        "largest_loss_percent": np.nan,
        "artifacts": [],
        "primary_report": None,
        "metrics": {},
    }


def build_experiment_record(
    config,
) -> dict[str, Any]:
    lifecycle = get_experiment_lifecycle(
        config.experiment_id,
        experiment_name=config.experiment_name,
        hypothesis=config.hypothesis,
        market_name=config.market_name,
        timeframe=config.timeframe,
        strategy_name=config.strategy_name,
    )
    record = _base_record(
        lifecycle=lifecycle,
        configured=True,
    )

    results_directory = (
        resolve(config.results_folder)
        / config.experiment_id
    )
    summary = read_csv_optional(
        results_directory / "summary.csv",
        index_col=0,
    )
    diagnostics = read_csv_optional(
        results_directory
        / "trade_diagnostics_summary.csv",
        index_col=0,
    )
    metadata = read_json_optional(
        results_directory / "run_metadata.json"
    )

    fixed = get_row(
        summary,
        "Fixed parameters",
    )
    walkforward = get_row(
        summary,
        "Walk-forward",
    )
    fixed_diagnostics = get_row(
        diagnostics,
        "Fixed parameters",
    )

    record.update(
        {
            "has_results": fixed is not None,
            "fixed_return_percent": value_from_row(
                fixed,
                "total_return_percent",
            ),
            "fixed_max_drawdown_percent": value_from_row(
                fixed,
                "max_drawdown_percent",
            ),
            "fixed_trade_profit_factor": value_from_row(
                fixed,
                "trade_profit_factor",
            ),
            "fixed_trades": value_from_row(
                fixed,
                "total_trades",
            ),
            "walkforward_return_percent": value_from_row(
                walkforward,
                "total_return_percent",
            ),
            "walkforward_max_drawdown_percent": value_from_row(
                walkforward,
                "max_drawdown_percent",
            ),
            "walkforward_trade_profit_factor": value_from_row(
                walkforward,
                "trade_profit_factor",
            ),
            "walkforward_trades": value_from_row(
                walkforward,
                "total_trades",
            ),
            "mcpt_p_value": metadata.get(
                "mcpt_p_value",
                np.nan,
            ),
            "best_in_sample_bar_profit_factor": metadata.get(
                "best_in_sample_bar_profit_factor",
                np.nan,
            ),
            "best_in_sample_parameters": metadata.get(
                "best_in_sample_parameters",
                {},
            ),
            "average_winner_percent": value_from_row(
                fixed_diagnostics,
                "average_winner_percent",
            ),
            "average_loser_percent": value_from_row(
                fixed_diagnostics,
                "average_loser_percent",
            ),
            "payoff_ratio": value_from_row(
                fixed_diagnostics,
                "payoff_ratio",
            ),
            "largest_loss_percent": value_from_row(
                fixed_diagnostics,
                "largest_loss_percent",
            ),
        }
    )
    return record


def build_lifecycle_only_record(
    lifecycle,
) -> dict[str, Any]:
    return _base_record(
        lifecycle=lifecycle,
        configured=False,
    )


def _metric_card(
    label: str,
    value: str,
    *,
    note: str = "",
) -> str:
    note_html = (
        f'<div class="metric-note">{html.escape(note)}</div>'
        if note
        else ""
    )
    return (
        '<div class="metric-card">'
        f'<div class="metric-label">{html.escape(label)}</div>'
        f'<div class="metric-value">{html.escape(value)}</div>'
        f"{note_html}"
        "</div>"
    )


def _artifact_links(
    artifact: ResearchArtifact,
    *,
    dashboard_directory: Path,
    preview_file: Path | None,
) -> str:
    source_href = relative_link(
        dashboard_directory,
        artifact.path,
    )
    links = [
        (
            f'<a href="{html.escape(source_href)}">'
            "Open original</a>"
        )
    ]

    if preview_file is not None:
        preview_href = relative_link(
            dashboard_directory,
            preview_file,
        )
        links.insert(
            0,
            (
                f'<a href="{html.escape(preview_href)}">'
                "Preview</a>"
            ),
        )

    return " · ".join(links)


def _artifact_card(
    artifact: ResearchArtifact,
    *,
    dashboard_directory: Path,
    preview_file: Path | None,
) -> str:
    size_kb = artifact.size_bytes / 1024
    searchable = " ".join(
        (
            artifact.experiment_id,
            artifact.label,
            artifact.category,
            artifact.project_relative_path,
        )
    ).lower()

    return f"""
<article class="artifact-card" data-search="{html.escape(searchable)}">
  <div class="artifact-topline">
    <span class="artifact-category">{html.escape(artifact.category)}</span>
    <span class="artifact-size">{size_kb:,.1f} KB</span>
  </div>
  <h4>{html.escape(artifact.label)}</h4>
  <code>{html.escape(artifact.project_relative_path)}</code>
  <div class="artifact-links">
    {_artifact_links(
        artifact,
        dashboard_directory=dashboard_directory,
        preview_file=preview_file,
    )}
  </div>
</article>
"""


def _record_metrics_html(
    record: dict[str, Any],
) -> str:
    metrics = record["metrics"]
    drawdown_percent = metrics.get(
        "max_drawdown_percent",
        np.nan,
    )
    drawdown_note = metrics.get(
        "drawdown_percent_note",
        "",
    )

    cards = [
        _metric_card(
            "Profit factor",
            format_number(
                metrics.get("profit_factor"),
                3,
            ),
        ),
        _metric_card(
            "Net profit",
            format_currency(
                metrics.get("net_profit_usd")
            ),
        ),
        _metric_card(
            "Win rate",
            format_percent(
                metrics.get("win_rate_percent")
            ),
        ),
        _metric_card(
            "Max drawdown",
            format_currency(
                metrics.get("max_drawdown_usd")
            ),
        ),
        _metric_card(
            "Max drawdown %",
            format_percent(drawdown_percent),
            note=drawdown_note,
        ),
        _metric_card(
            "Trades",
            format_integer(
                metrics.get("total_trades")
            ),
        ),
        _metric_card(
            "MCPT p-value",
            format_number(
                metrics.get("mcpt_p_value"),
                4,
            ),
        ),
    ]

    return "".join(cards)


def _experiment_section(
    record: dict[str, Any],
    *,
    dashboard_directory: Path,
    previews: dict[str, Path | None],
) -> str:
    experiment_id = record["experiment_id"]
    artifacts: list[ResearchArtifact] = record[
        "artifacts"
    ]
    primary = record["primary_report"]

    if primary is not None:
        primary_href = relative_link(
            dashboard_directory,
            primary.path,
        )
        primary_button = (
            f'<a class="primary-button" '
            f'href="{html.escape(primary_href)}">'
            "Open primary visual report</a>"
        )
    else:
        primary_button = (
            '<span class="disabled-button">'
            "No visual report found</span>"
        )

    review_decision = record["metrics"].get(
        "review_decision",
        "",
    )
    result_decision = record["metrics"].get(
        "result_decision",
        "",
    )
    decision_badges = "".join(
        (
            f'<span class="decision-badge">'
            f'{html.escape(label)}: '
            f'{html.escape(str(value))}</span>'
        )
        for label, value in (
            ("Result", result_decision),
            ("Review", review_decision),
        )
        if value
    )

    artifact_cards = "".join(
        _artifact_card(
            artifact,
            dashboard_directory=dashboard_directory,
            preview_file=previews.get(
                artifact.project_relative_path
            ),
        )
        for artifact in artifacts
    )

    return f"""
<section class="experiment-section" id="{html.escape(experiment_id.lower())}">
  <div class="experiment-header">
    <div>
      <div class="experiment-id">{html.escape(experiment_id)}</div>
      <h2>{html.escape(record["experiment_name"])}</h2>
      <p class="market-line">
        {html.escape(record["market_name"])}
        · {html.escape(record["timeframe"])}
        · {html.escape(record["strategy_name"])}
      </p>
    </div>
    <span class="stage {status_class(record["status"])}">
      {html.escape(record["status_label"])}
    </span>
  </div>

  <p>{html.escape(record["hypothesis"])}</p>

  <div class="decision-row">{decision_badges}</div>
  <div class="metrics-grid">{_record_metrics_html(record)}</div>

  <div class="lifecycle-grid">
    <div>
      <h3>Why it is at this stage</h3>
      <p>{html.escape(record["stage_reason"])}</p>
    </div>
    <div>
      <h3>Next action</h3>
      <p>{html.escape(record["next_action"])}</p>
    </div>
  </div>

  <div class="section-actions">
    {primary_button}
    <span>{len(artifacts):,} linked artifacts</span>
  </div>

  <details open>
    <summary>Reports, decisions, audits and saved files</summary>
    <div class="artifact-grid">{artifact_cards}</div>
  </details>
</section>
"""


def build_dashboard_html(
    records: list[dict[str, Any]],
    dashboard_directory: Path,
    previews: dict[str, Path | None] | None = None,
) -> str:
    previews = previews or {}
    total_artifacts = sum(
        len(record["artifacts"])
        for record in records
    )
    accepted = sum(
        record["status"]
        == "ACCEPTED_FOR_PAPER_TESTING"
        for record in records
    )
    rejected = sum(
        record["status"] == "REJECTED"
        for record in records
    )
    active = len(records) - accepted - rejected

    nav = "".join(
        (
            f'<a href="#{html.escape(record["experiment_id"].lower())}">'
            f'{html.escape(record["experiment_id"])}</a>'
        )
        for record in records
    )

    sections = "".join(
        _experiment_section(
            record,
            dashboard_directory=dashboard_directory,
            previews=previews,
        )
        for record in records
    )

    artifact_rows = []
    for record in records:
        for artifact in record["artifacts"]:
            preview = previews.get(
                artifact.project_relative_path
            )
            searchable = " ".join(
                (
                    artifact.experiment_id,
                    artifact.label,
                    artifact.category,
                    artifact.project_relative_path,
                )
            ).lower()
            artifact_rows.append(
                f"""
<tr data-search="{html.escape(searchable)}">
  <td>{html.escape(artifact.experiment_id)}</td>
  <td>{html.escape(artifact.category)}</td>
  <td>{html.escape(artifact.label)}</td>
  <td><code>{html.escape(artifact.project_relative_path)}</code></td>
  <td>{_artifact_links(
      artifact,
      dashboard_directory=dashboard_directory,
      preview_file=preview,
  )}</td>
</tr>
"""
            )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Quantitative Research Hub</title>
<style>
:root {{
  color-scheme: light dark;
  --bg: #081120;
  --panel: #101b2e;
  --panel-2: #15243b;
  --text: #e8eef8;
  --muted: #9cacbf;
  --line: #2a3b56;
  --accent: #7dd3fc;
  --positive: #86efac;
  --negative: #fca5a5;
  --warning: #fde68a;
}}
* {{ box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}
body {{
  margin: 0;
  background:
    radial-gradient(circle at top right, #123155 0, transparent 28%),
    var(--bg);
  color: var(--text);
  font-family: Inter, Segoe UI, Arial, sans-serif;
  line-height: 1.5;
}}
a {{
  color: var(--accent);
  text-decoration: none;
}}
a:hover {{ text-decoration: underline; }}
header {{
  position: sticky;
  top: 0;
  z-index: 20;
  backdrop-filter: blur(14px);
  background: rgba(8, 17, 32, 0.91);
  border-bottom: 1px solid var(--line);
}}
.header-inner {{
  width: min(1550px, calc(100% - 32px));
  margin: 0 auto;
  display: flex;
  gap: 22px;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
}}
.brand {{ font-weight: 800; }}
nav {{
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
}}
main {{
  width: min(1550px, calc(100% - 32px));
  margin: 32px auto 72px;
}}
.hero {{
  border: 1px solid var(--line);
  border-radius: 24px;
  padding: 28px;
  background: linear-gradient(135deg, #132642, #0d182a);
  margin-bottom: 24px;
}}
.hero h1 {{
  margin: 0 0 8px;
  font-size: clamp(2rem, 5vw, 3.7rem);
}}
.hero p {{
  color: var(--muted);
  max-width: 900px;
}}
.stats {{
  display: grid;
  grid-template-columns: repeat(4, minmax(130px, 1fr));
  gap: 12px;
  margin-top: 20px;
}}
.stat {{
  background: rgba(255,255,255,0.035);
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 14px;
}}
.stat strong {{
  display: block;
  font-size: 1.5rem;
}}
.stat span {{ color: var(--muted); }}
.search-panel {{
  display: flex;
  gap: 12px;
  align-items: center;
  margin: 22px 0;
}}
.search-panel input {{
  width: 100%;
  border: 1px solid var(--line);
  background: var(--panel);
  color: var(--text);
  padding: 13px 15px;
  border-radius: 12px;
  font: inherit;
}}
.experiment-section {{
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 22px;
  padding: 24px;
  margin: 22px 0;
  scroll-margin-top: 82px;
}}
.experiment-header {{
  display: flex;
  gap: 20px;
  justify-content: space-between;
  align-items: flex-start;
}}
.experiment-id {{
  color: var(--accent);
  font-weight: 800;
  letter-spacing: 0.08em;
  font-size: 0.8rem;
}}
.experiment-header h2 {{
  margin: 3px 0;
  font-size: clamp(1.45rem, 3vw, 2.15rem);
}}
.market-line {{ color: var(--muted); }}
.stage, .decision-badge {{
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 7px 11px;
  font-weight: 700;
  white-space: nowrap;
}}
.stage.accepted-for-paper-testing {{
  color: var(--positive);
}}
.stage.rejected {{ color: var(--negative); }}
.stage.review, .stage.full-validation {{
  color: var(--warning);
}}
.decision-row {{
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 13px 0;
}}
.decision-badge {{
  font-size: 0.82rem;
  color: var(--positive);
}}
.metrics-grid {{
  display: grid;
  grid-template-columns: repeat(7, minmax(125px, 1fr));
  gap: 10px;
  margin: 20px 0;
}}
.metric-card {{
  background: var(--panel-2);
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 12px;
  min-width: 0;
}}
.metric-label {{
  color: var(--muted);
  font-size: 0.78rem;
}}
.metric-value {{
  font-weight: 800;
  font-size: 1.1rem;
  margin-top: 3px;
}}
.metric-note {{
  color: var(--muted);
  font-size: 0.68rem;
  margin-top: 5px;
}}
.lifecycle-grid {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}}
.lifecycle-grid > div {{
  background: rgba(255,255,255,0.025);
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 14px;
}}
.lifecycle-grid h3 {{
  margin-top: 0;
  font-size: 0.95rem;
}}
.section-actions {{
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  margin: 18px 0;
  color: var(--muted);
}}
.primary-button, .disabled-button {{
  display: inline-block;
  border-radius: 11px;
  padding: 10px 14px;
  font-weight: 800;
}}
.primary-button {{
  background: var(--accent);
  color: #06233a;
}}
.disabled-button {{
  border: 1px solid var(--line);
  color: var(--muted);
}}
details {{
  border-top: 1px solid var(--line);
  padding-top: 16px;
}}
summary {{
  cursor: pointer;
  font-weight: 800;
  margin-bottom: 14px;
}}
.artifact-grid {{
  display: grid;
  grid-template-columns: repeat(3, minmax(250px, 1fr));
  gap: 12px;
}}
.artifact-card {{
  background: var(--panel-2);
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 14px;
  min-width: 0;
}}
.artifact-card h4 {{
  margin: 9px 0;
}}
.artifact-card code {{
  display: block;
  color: var(--muted);
  white-space: normal;
  overflow-wrap: anywhere;
  font-size: 0.75rem;
}}
.artifact-topline {{
  display: flex;
  justify-content: space-between;
  gap: 8px;
  color: var(--muted);
  font-size: 0.75rem;
}}
.artifact-category {{
  color: var(--accent);
  font-weight: 700;
}}
.artifact-links {{
  margin-top: 12px;
}}
.library {{
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 22px;
  padding: 22px;
  overflow: auto;
}}
table {{
  width: 100%;
  border-collapse: collapse;
  min-width: 950px;
}}
th, td {{
  border-bottom: 1px solid var(--line);
  padding: 10px;
  text-align: left;
  vertical-align: top;
}}
th {{
  position: sticky;
  top: 58px;
  background: var(--panel);
}}
td code {{
  font-size: 0.78rem;
  overflow-wrap: anywhere;
}}
.hidden {{ display: none !important; }}
.footer-note {{
  color: var(--muted);
  margin-top: 24px;
}}
@media (max-width: 1200px) {{
  .metrics-grid {{
    grid-template-columns: repeat(4, 1fr);
  }}
  .artifact-grid {{
    grid-template-columns: repeat(2, 1fr);
  }}
}}
@media (max-width: 760px) {{
  .header-inner {{
    align-items: flex-start;
    flex-direction: column;
  }}
  .stats,
  .metrics-grid,
  .lifecycle-grid,
  .artifact-grid {{
    grid-template-columns: 1fr;
  }}
  .experiment-header {{
    flex-direction: column;
  }}
}}
</style>
</head>
<body>
<header>
  <div class="header-inner">
    <div class="brand">Quantitative Research Hub</div>
    <nav>
      <a href="#top">Overview</a>
      {nav}
      <a href="#all-files">All files</a>
    </nav>
  </div>
</header>

<main id="top">
<section class="hero">
  <h1>Everything in one place</h1>
  <p>
    Open visual reports, review decisions, audits, trade ledgers,
    cost tables, preregistrations and research notes from one local page.
    This dashboard reads saved files only; it does not rerun research.
  </p>
  <div class="stats">
    <div class="stat"><strong>{len(records)}</strong><span>Experiments</span></div>
    <div class="stat"><strong>{total_artifacts}</strong><span>Linked artifacts</span></div>
    <div class="stat"><strong>{accepted}</strong><span>Accepted for paper testing</span></div>
    <div class="stat"><strong>{active}</strong><span>Active or under review</span></div>
  </div>
</section>

<div class="search-panel">
  <input id="artifact-search" type="search"
    placeholder="Search reports, decisions, audits, trades, experiment IDs...">
</div>

{sections}

<section class="library" id="all-files">
  <h2>Complete report and research library</h2>
  <p class="footer-note">
    The dashboard scans the reports, results and research folders.
    Raw market-data folders are intentionally excluded.
  </p>
  <table>
    <thead>
      <tr>
        <th>Experiment</th>
        <th>Type</th>
        <th>Name</th>
        <th>Location</th>
        <th>Open</th>
      </tr>
    </thead>
    <tbody>
      {''.join(artifact_rows)}
    </tbody>
  </table>
</section>

<p class="footer-note">
  Generated from saved local files. No strategy, MCPT, optimization,
  confirmation import or paper simulator was rerun.
</p>
</main>

<script>
const input = document.getElementById("artifact-search");
input.addEventListener("input", () => {{
  const query = input.value.trim().toLowerCase();
  document.querySelectorAll("[data-search]").forEach((element) => {{
    const visible = !query || element.dataset.search.includes(query);
    element.classList.toggle("hidden", !visible);
  }});
}});
</script>
</body>
</html>
"""


def main() -> None:
    arguments = parse_arguments()
    configs = list_experiments()
    configured_records = [
        build_experiment_record(config)
        for config in configs
    ]
    configured_ids = {
        record["experiment_id"]
        for record in configured_records
    }
    lifecycle_only_records = [
        build_lifecycle_only_record(lifecycle)
        for lifecycle in list_experiment_lifecycles()
        if lifecycle.experiment_id not in configured_ids
    ]
    records = sorted(
        configured_records
        + lifecycle_only_records,
        key=lambda record: int(
            record["experiment_id"].split("-")[1]
        ),
    )

    if not records:
        raise RuntimeError(
            "No experiment records were found."
        )

    experiment_ids = [
        record["experiment_id"]
        for record in records
    ]
    artifacts = discover_artifacts(
        PROJECT_DIR,
        experiment_ids,
    )

    reports_root = PROJECT_DIR / "reports"
    results_root = PROJECT_DIR / "results"
    dashboard_directory = (
        reports_root / "research_dashboard"
    )
    dashboard_directory.mkdir(
        parents=True,
        exist_ok=True,
    )
    results_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    previews: dict[str, Path | None] = {}
    for artifact in artifacts:
        previews[
            artifact.project_relative_path
        ] = build_artifact_preview(
            artifact,
            dashboard_directory,
        )

    for record in records:
        experiment_artifacts = [
            artifact
            for artifact in artifacts
            if artifact.experiment_id
            == record["experiment_id"]
        ]
        primary = choose_primary_report(
            experiment_artifacts,
            record["experiment_id"],
        )
        metrics = load_experiment_metrics(
            PROJECT_DIR,
            record["experiment_id"],
        )

        record["artifacts"] = experiment_artifacts
        record["primary_report"] = primary
        record["metrics"] = metrics
        record["report_exists"] = (
            primary is not None
        )
        record["report_file"] = (
            primary.path
            if primary is not None
            else Path()
        )
        record["has_results"] = (
            record["has_results"]
            or bool(metrics.get("metric_source"))
            or any(
                artifact.category
                in {
                    "Visual report",
                    "Decision record",
                    "Summary table",
                }
                for artifact in experiment_artifacts
            )
        )

        if not np.isnan(
            safe_float(
                metrics.get("mcpt_p_value")
            )
        ):
            record["mcpt_p_value"] = metrics[
                "mcpt_p_value"
            ]

    dashboard_file = (
        dashboard_directory / "index.html"
    )
    dashboard_file.write_text(
        build_dashboard_html(
            records,
            dashboard_directory,
            previews,
        ),
        encoding="utf-8",
    )

    dashboard_rows = []
    for record in records:
        metrics = record["metrics"]
        dashboard_rows.append(
            {
                "experiment_id": record[
                    "experiment_id"
                ],
                "experiment_name": record[
                    "experiment_name"
                ],
                "status": record["status"],
                "status_label": record[
                    "status_label"
                ],
                "market_name": record[
                    "market_name"
                ],
                "timeframe": record["timeframe"],
                "strategy_name": record[
                    "strategy_name"
                ],
                "artifact_count": len(
                    record["artifacts"]
                ),
                "primary_report": (
                    record["primary_report"]
                    .project_relative_path
                    if record[
                        "primary_report"
                    ] is not None
                    else ""
                ),
                "profit_factor": metrics.get(
                    "profit_factor"
                ),
                "net_profit_usd": metrics.get(
                    "net_profit_usd"
                ),
                "win_rate_percent": metrics.get(
                    "win_rate_percent"
                ),
                "max_drawdown_usd": metrics.get(
                    "max_drawdown_usd"
                ),
                "max_drawdown_percent": metrics.get(
                    "max_drawdown_percent"
                ),
                "total_trades": metrics.get(
                    "total_trades"
                ),
                "mcpt_p_value": metrics.get(
                    "mcpt_p_value"
                ),
                "result_decision": metrics.get(
                    "result_decision"
                ),
                "review_decision": metrics.get(
                    "review_decision"
                ),
                "stage_reason": record[
                    "stage_reason"
                ],
                "next_action": record[
                    "next_action"
                ],
            }
        )

    pd.DataFrame(
        dashboard_rows
    ).to_csv(
        results_root
        / "research_dashboard.csv",
        index=False,
    )

    pd.DataFrame(
        [
            artifact.to_dict()
            for artifact in artifacts
        ]
    ).to_csv(
        results_root
        / "research_dashboard_artifacts.csv",
        index=False,
    )

    print()
    print("Research hub dashboard created.")
    print(f"Experiments: {len(records)}")
    print(f"Linked artifacts: {len(artifacts)}")
    print(f"Dashboard: {dashboard_file}")
    print(
        "Experiment summary: "
        f"{results_root / 'research_dashboard.csv'}"
    )
    print(
        "Artifact library: "
        f"{results_root / 'research_dashboard_artifacts.csv'}"
    )

    if arguments.open:
        if hasattr(os, "startfile"):
            os.startfile(dashboard_file)
        else:
            print(
                "--open is automatically supported "
                "on Windows only."
            )


if __name__ == "__main__":
    main()
