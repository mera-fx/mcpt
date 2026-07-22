from __future__ import annotations

import html
import math
import os
from pathlib import Path
from typing import Any, Iterable

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from dashboard_experiment_profiles import DashboardProfile


SOURCE_FILES: dict[str, tuple[str, ...]] = {
    "EXP-015": (
        "results/EXP-015/source_qualification/catalog_result.json",
        "results/EXP-015/source_qualification/catalog_rows.csv",
        "research/EXP-015_catalog_result.md",
    ),
    "EXP-016": (
        "results/EXP-016/source_qualification/audit_result.json",
        "results/EXP-016/source_qualification/structural_measurements.csv",
        "results/EXP-016/source_qualification/cross_source_measurements.csv",
        "results/EXP-016/source_qualification/largest_discrepancies.csv",
        "research/EXP-016_audit_result.md",
    ),
    "EXP-017": (
        "research/EXP-017_closure.md",
        "research/EXP-017_source_lock.md",
        "research/EXP-017_preregistration.md",
    ),
    "EXP-018": (
        "results/EXP-018/source_qualification/audit_result.json",
        "results/EXP-018/source_qualification/window_measurements.csv",
        "results/EXP-018/source_qualification/session_measurements.csv",
        "results/EXP-018/source_qualification/missing_minute_runs.csv",
        "results/EXP-018/source_qualification/repeatability_measurements.csv",
        "research/EXP-018_preregistration.md",
    ),
}


def _safe(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return number if math.isfinite(number) else float("nan")


def _format_value(key: str, value: Any) -> str:
    if value is None or value == "":
        return "—"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    number = _safe(value)
    if not math.isnan(number):
        lowered = key.lower()
        if "coverage" in lowered or "share" in lowered:
            if abs(number) <= 1.0:
                number *= 100.0
            return f"{number:,.6f}%"
        if "cost" in lowered or key.endswith("_usd"):
            sign = "−" if number < 0 else ""
            return f"{sign}${abs(number):,.2f}"
        if number.is_integer():
            return f"{int(number):,}"
        return f"{number:,.6f}"
    return str(value)


def _humanize(value: str) -> str:
    return value.replace("_", " ").strip().title()


def _relative_link(source_dir: Path, target: Path) -> str:
    return Path(
        os.path.relpath(
            target.resolve(),
            source_dir.resolve(),
        )
    ).as_posix()


def _measurement_table(profile: DashboardProfile) -> str:
    rows = [
        (
            "Classification",
            profile.result_state,
        ),
        (
            "Result source",
            profile.result_state_source,
        ),
    ]
    rows.extend(
        (
            _humanize(key),
            _format_value(key, value),
        )
        for key, value in profile.data_measurements.items()
        if key != "classification"
    )
    return (
        '<table class="measurements"><tbody>'
        + "".join(
            "<tr>"
            f"<th>{html.escape(label)}</th>"
            f"<td>{html.escape(str(value))}</td>"
            "</tr>"
            for label, value in rows
        )
        + "</tbody></table>"
    )


def _source_links(
    project_dir: Path,
    output_dir: Path,
    experiment_id: str,
) -> str:
    links = []
    for relative in SOURCE_FILES.get(experiment_id, ()):
        path = project_dir / relative
        if not path.exists():
            continue
        href = _relative_link(output_dir, path)
        links.append(
            "<li>"
            f'<a href="{html.escape(href)}">{html.escape(relative)}</a>'
            "</li>"
        )
    if not links:
        return '<p class="muted">No dedicated source file was found.</p>'
    return "<ul>" + "".join(links) + "</ul>"


def _csv_table(
    path: Path,
    *,
    columns: Iterable[str] | None = None,
    max_rows: int = 100,
) -> str:
    if not path.exists() or path.stat().st_size == 0:
        return '<p class="muted">No rows available yet.</p>'
    try:
        frame = pd.read_csv(path)
    except Exception as error:
        return (
            '<p class="muted">Table could not be read: '
            + html.escape(str(error))
            + "</p>"
        )
    if frame.empty:
        return '<p class="muted">No rows available yet.</p>'
    if columns is not None:
        selected = [
            column
            for column in columns
            if column in frame.columns
        ]
        if selected:
            frame = frame[selected]
    frame = frame.head(max_rows)
    return (
        '<div class="table-wrap">'
        + frame.to_html(
            index=False,
            escape=True,
            border=0,
            classes="detail-table",
        )
        + "</div>"
    )


def _save_figure(figure: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.tight_layout()
    figure.savefig(
        path,
        dpi=150,
        bbox_inches="tight",
    )
    plt.close(figure)


def _exp016_chart(project_dir: Path, output_dir: Path) -> str:
    path = (
        project_dir
        / "results"
        / "EXP-016"
        / "source_qualification"
        / "cross_source_measurements.csv"
    )
    if not path.exists():
        return ""
    try:
        frame = pd.read_csv(path)
    except Exception:
        return ""
    required = {
        "window_id",
        "expected_minute_completeness",
        "close_within_one_tick_share",
    }
    if frame.empty or not required.issubset(frame.columns):
        return ""

    labels = frame["window_id"].astype(str).tolist()
    completeness = (
        pd.to_numeric(
            frame["expected_minute_completeness"],
            errors="coerce",
        )
        * 100.0
    )
    within_tick = (
        pd.to_numeric(
            frame["close_within_one_tick_share"],
            errors="coerce",
        )
        * 100.0
    )
    x = np.arange(len(labels), dtype=float)
    width = 0.36

    figure, axis = plt.subplots(figsize=(14, 6.2))
    axis.bar(
        x - width / 2,
        completeness,
        width,
        label="Expected-minute completeness",
    )
    axis.bar(
        x + width / 2,
        within_tick,
        width,
        label="Close within one tick",
    )
    axis.axhline(
        99.9,
        linestyle="--",
        linewidth=1.0,
        label="99.9% completeness gate",
    )
    axis.axhline(
        99.5,
        linestyle=":",
        linewidth=1.0,
        label="99.5% price gate",
    )
    axis.set_title("EXP-016 cross-source sample measurements")
    axis.set_ylabel("Percent")
    axis.set_xticks(x)
    axis.set_xticklabels(labels, rotation=30, ha="right")
    axis.grid(axis="y", alpha=0.25)
    axis.legend()

    chart = output_dir / "assets" / "cross_source_quality.png"
    _save_figure(figure, chart)
    return (
        '<img class="chart" '
        'src="assets/cross_source_quality.png" '
        'alt="EXP-016 completeness and price agreement chart">'
    )


def _exp018_chart(project_dir: Path, output_dir: Path) -> str:
    path = (
        project_dir
        / "results"
        / "EXP-018"
        / "source_qualification"
        / "session_measurements.csv"
    )
    if not path.exists():
        return ""
    try:
        frame = pd.read_csv(path)
    except Exception:
        return ""
    required = {
        "window_id",
        "session_type",
        "trade_minute_coverage",
    }
    if frame.empty or not required.issubset(frame.columns):
        return ""

    pivot = frame.pivot_table(
        index="window_id",
        columns="session_type",
        values="trade_minute_coverage",
        aggfunc="first",
    )
    if pivot.empty:
        return ""

    labels = pivot.index.astype(str).tolist()
    x = np.arange(len(labels), dtype=float)
    columns = list(pivot.columns)
    width = 0.8 / max(len(columns), 1)

    figure, axis = plt.subplots(figsize=(14, 6.2))
    for position, column in enumerate(columns):
        values = (
            pd.to_numeric(
                pivot[column],
                errors="coerce",
            )
            * 100.0
        )
        offset = (
            position - (len(columns) - 1) / 2
        ) * width
        axis.bar(
            x + offset,
            values,
            width,
            label=str(column),
        )
    axis.axhline(
        99.9,
        linestyle="--",
        linewidth=1.0,
        label="Regular coverage gate",
    )
    axis.axhline(
        99.5,
        linestyle=":",
        linewidth=1.0,
        label="Extended coverage gate",
    )
    axis.set_title("EXP-018 trade-minute coverage by locked window")
    axis.set_ylabel("Coverage (%)")
    axis.set_xticks(x)
    axis.set_xticklabels(labels, rotation=30, ha="right")
    axis.grid(axis="y", alpha=0.25)
    axis.legend()

    chart = output_dir / "assets" / "trade_minute_coverage.png"
    _save_figure(figure, chart)
    return (
        '<img class="chart" '
        'src="assets/trade_minute_coverage.png" '
        'alt="EXP-018 regular and extended trade-minute coverage chart">'
    )


def _detail_sections(
    project_dir: Path,
    output_dir: Path,
    profile: DashboardProfile,
) -> str:
    experiment_id = profile.experiment_id
    if experiment_id == "EXP-015":
        catalog = (
            project_dir
            / "results"
            / "EXP-015"
            / "source_qualification"
            / "catalog_rows.csv"
        )
        return (
            "<h2>Catalog sample</h2>"
            "<p class=\"muted\">Catalog discovery does not resolve contract "
            "construction or qualify history.</p>"
            + _csv_table(
                catalog,
                columns=(
                    "symbol",
                    "name",
                    "dataset",
                    "ticks",
                    "first",
                    "last",
                    "country",
                ),
                max_rows=100,
            )
        )

    if experiment_id == "EXP-016":
        structural = (
            project_dir
            / "results"
            / "EXP-016"
            / "source_qualification"
            / "structural_measurements.csv"
        )
        cross = (
            project_dir
            / "results"
            / "EXP-016"
            / "source_qualification"
            / "cross_source_measurements.csv"
        )
        return (
            _exp016_chart(project_dir, output_dir)
            + "<h2>Structural measurements</h2>"
            + _csv_table(
                structural,
                columns=(
                    "window_id",
                    "raw_rows",
                    "timestamp_source",
                    "timestamp_timezone_aware",
                    "duplicate_timestamp_count",
                    "invalid_ohlc_rows",
                    "negative_volume_rows",
                    "nonfinite_ohlcv_rows",
                ),
            )
            + "<h2>Cross-source measurements</h2>"
            + _csv_table(
                cross,
                columns=(
                    "window_id",
                    "expected_minute_completeness",
                    "matched_timestamp_share",
                    "close_within_one_tick_share",
                    "mean_open_abs_diff",
                    "mean_high_abs_diff",
                    "mean_low_abs_diff",
                    "mean_close_abs_diff",
                    "mean_volume_abs_diff",
                ),
            )
        )

    if experiment_id == "EXP-017":
        return """
<h2>Closure interpretation</h2>
<p>
  EXP-017 required two accessible exact-contract historical sources. Only one
  accessible candidate was available under the locked source set, so the
  benchmark closed as ACCESS_INCOMPLETE without viewing exact-contract OHLCV
  under this experiment.
</p>
<p class="muted">
  The closure is an access result, not a market-data accuracy ranking and not
  a strategy or trading authorization.
</p>
"""

    if experiment_id == "EXP-018":
        windows = (
            project_dir
            / "results"
            / "EXP-018"
            / "source_qualification"
            / "window_measurements.csv"
        )
        sessions = (
            project_dir
            / "results"
            / "EXP-018"
            / "source_qualification"
            / "session_measurements.csv"
        )
        repeats = (
            project_dir
            / "results"
            / "EXP-018"
            / "source_qualification"
            / "repeatability_measurements.csv"
        )
        return (
            _exp018_chart(project_dir, output_dir)
            + "<h2>Locked exact-contract windows</h2>"
            + _csv_table(
                windows,
                columns=(
                    "window_id",
                    "canonical_contract",
                    "raw_symbol",
                    "expected_instrument_id",
                    "row_count",
                    "duplicate_timestamp_rows",
                    "identity_mismatch_rows",
                    "invalid_ohlc_rows",
                    "negative_volume_rows",
                    "nonfinite_ohlcv_rows",
                    "off_tick_ohlc_values",
                    "regular_trade_minute_coverage",
                    "extended_trade_minute_coverage",
                ),
            )
            + "<h2>Session coverage</h2>"
            + _csv_table(sessions)
            + "<h2>Delayed repeatability</h2>"
            + _csv_table(repeats)
        )

    return ""


def _report_html(
    project_dir: Path,
    output_dir: Path,
    profile: DashboardProfile,
) -> str:
    dashboard = (
        project_dir
        / "reports"
        / "research_dashboard"
        / "index.html"
    )
    dashboard_link = _relative_link(output_dir, dashboard)
    detail = _detail_sections(
        project_dir,
        output_dir,
        profile,
    )
    sources = _source_links(
        project_dir,
        output_dir,
        profile.experiment_id,
    )
    missing = (
        "<ul>"
        + "".join(
            f"<li>{html.escape(item)}</li>"
            for item in profile.missing_items
            if item != "No dedicated visual data-quality report"
        )
        + "</ul>"
        if any(
            item != "No dedicated visual data-quality report"
            for item in profile.missing_items
        )
        else '<p class="muted">No unresolved dashboard parser gap.</p>'
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(profile.experiment_id)} data-source report</title>
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
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: Inter, "Segoe UI", Arial, sans-serif;
  line-height: 1.5;
}}
main {{
  width: min(1500px, calc(100% - 32px));
  margin: 28px auto 80px;
}}
.hero, section {{
  border: 1px solid var(--line);
  background: var(--panel);
  border-radius: 16px;
  padding: 22px;
  margin-bottom: 18px;
}}
h1 {{ margin: 0 0 8px; }}
h2 {{ margin-top: 28px; border-bottom: 1px solid var(--line); padding-bottom: 8px; }}
a {{ color: var(--accent); text-decoration: none; }}
.muted {{ color: var(--muted); }}
.measurements {{
  width: 100%;
  border-collapse: collapse;
}}
.measurements th, .measurements td {{
  padding: 10px 12px;
  border-bottom: 1px solid var(--line);
  text-align: left;
}}
.measurements th {{ width: 42%; color: var(--muted); }}
.table-wrap {{
  overflow: auto;
  border: 1px solid var(--line);
  border-radius: 12px;
}}
.detail-table {{
  width: 100%;
  border-collapse: collapse;
  background: var(--panel2);
}}
.detail-table th, .detail-table td {{
  padding: 8px 10px;
  border-bottom: 1px solid var(--line);
  text-align: left;
  white-space: nowrap;
}}
.chart {{
  display: block;
  width: 100%;
  height: auto;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: white;
  margin: 18px 0;
}}
</style>
</head>
<body>
<main>
  <p><a href="{html.escape(dashboard_link)}">← Research dashboard</a></p>
  <div class="hero">
    <div class="muted">{html.escape(profile.research_type_label)}</div>
    <h1>{html.escape(profile.experiment_id)} · {html.escape(profile.experiment_name)}</h1>
    <p>{html.escape(profile.hypothesis)}</p>
  </div>

  <section>
    <h2>Current qualification state</h2>
    {_measurement_table(profile)}
  </section>

  <section>
    <h2>Evidence and boundary</h2>
    <p>{html.escape(profile.stage_reason)}</p>
    <h3>Next action</h3>
    <p>{html.escape(profile.next_action)}</p>
  </section>

  <section>
    {detail}
  </section>

  <section>
    <h2>Source files</h2>
    {sources}
  </section>

  <section>
    <h2>Dashboard parser status</h2>
    {missing}
  </section>

  <p class="muted">
    Generated from saved files only. No market-data request, strategy run,
    optimization, MCPT, bootstrap, paper simulator or trading action was run.
  </p>
</main>
</body>
</html>
"""


def build_data_source_reports(
    project_dir: Path,
    profiles: Iterable[DashboardProfile],
) -> dict[str, Path]:
    project_dir = Path(project_dir)
    written: dict[str, Path] = {}
    for profile in profiles:
        if profile.research_type != "data_source":
            continue
        output_dir = (
            project_dir
            / "reports"
            / f"{profile.experiment_id}-data-quality"
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        report = output_dir / "report.html"
        report.write_text(
            _report_html(
                project_dir,
                output_dir,
                profile,
            ),
            encoding="utf-8",
        )
        written[profile.experiment_id] = report
    return written
