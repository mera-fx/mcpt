from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def _format(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, (bool, np.bool_)):
        return "Yes" if value else "No"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return html.escape(str(value))
    if np.isnan(number):
        return "—"
    if np.isposinf(number):
        return "∞"
    if np.isneginf(number):
        return "−∞"
    return f"{number:,.4f}"


def _table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "<p>No rows.</p>"
    return frame.to_html(
        index=False,
        escape=True,
        border=0,
        classes="data-table",
        na_rep="—",
    )


def _vertical_comparison(
    selected: pd.Series | None,
    baseline: pd.Series,
) -> pd.DataFrame:
    rows = []
    metrics = [
        (
            "Opening range",
            "opening_range_minutes",
            " minutes",
        ),
        (
            "Final entry",
            "final_entry_time_new_york",
            "",
        ),
        (
            "Direction",
            "direction_mode",
            "",
        ),
        (
            "NQ Profit Factor",
            "nq_trade_profit_factor",
            "",
        ),
        (
            "NQ net profit",
            "nq_net_profit_usd",
            " USD",
        ),
        (
            "NQ maximum drawdown",
            "nq_maximum_drawdown_usd",
            " USD",
        ),
        (
            "NQ maximum drawdown",
            "nq_maximum_drawdown_percent",
            "%",
        ),
        (
            "NQ completed trades",
            "nq_completed_trades",
            "",
        ),
        (
            "NQ profitable years",
            "nq_profitable_calendar_years",
            "",
        ),
        (
            "MNQ Profit Factor",
            "mnq_trade_profit_factor",
            "",
        ),
        (
            "MNQ net profit",
            "mnq_net_profit_usd",
            " USD",
        ),
        (
            "Neighbour profitability",
            "profitable_neighbor_share",
            "",
        ),
        (
            "Median component rank",
            "median_component_rank",
            "",
        ),
    ]
    for label, field, suffix in metrics:
        baseline_value = baseline.get(field)
        selected_value = (
            selected.get(field)
            if selected is not None
            else None
        )
        if field == "profitable_neighbor_share":
            baseline_text = (
                f"{float(baseline_value) * 100:.2f}%"
                if baseline_value is not None
                else "—"
            )
            selected_text = (
                f"{float(selected_value) * 100:.2f}%"
                if selected_value is not None
                else "—"
            )
        elif field in {
            "nq_net_profit_usd",
            "nq_maximum_drawdown_usd",
            "mnq_net_profit_usd",
        }:
            baseline_text = (
                f"${float(baseline_value):,.2f}"
                if baseline_value is not None
                else "—"
            )
            selected_text = (
                f"${float(selected_value):,.2f}"
                if selected_value is not None
                else "—"
            )
        elif field == "nq_maximum_drawdown_percent":
            baseline_text = (
                f"{float(baseline_value):,.2f}%"
                if baseline_value is not None
                else "—"
            )
            selected_text = (
                f"{float(selected_value):,.2f}%"
                if selected_value is not None
                else "—"
            )
        elif suffix == " minutes":
            baseline_text = f"{int(baseline_value)} minutes"
            selected_text = (
                f"{int(selected_value)} minutes"
                if selected_value is not None
                else "—"
            )
        elif isinstance(
            baseline_value,
            (int, float, np.integer, np.floating),
        ):
            baseline_text = _format(baseline_value)
            selected_text = _format(selected_value)
        else:
            baseline_text = str(baseline_value)
            selected_text = (
                str(selected_value)
                if selected_value is not None
                else "—"
            )
        rows.append(
            {
                "Metric": label,
                "EXP-005 control": baseline_text,
                "EXP-006 selected": selected_text,
            }
        )
    return pd.DataFrame(rows)


def write_exp006_charts(
    *,
    report_root: Path,
    grid: pd.DataFrame,
    walk_forward: pd.DataFrame,
    mcpt: pd.DataFrame,
    real_statistic: float,
    selected_nq_equity: pd.DataFrame | None,
    selected_mnq_equity: pd.DataFrame | None,
) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    chart_root = report_root / "charts"
    chart_root.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    for direction in (
        "long",
        "short",
        "both",
    ):
        local = grid.loc[
            grid["direction_mode"].eq(direction)
        ]
        pivot = local.pivot(
            index="opening_range_minutes",
            columns="final_entry_time_new_york",
            values="nq_trade_profit_factor",
        ).reindex(
            index=[5, 15, 30],
            columns=["10:30", "11:15", "12:00"],
        )
        figure, axis = plt.subplots(
            figsize=(10, 5)
        )
        image = axis.imshow(
            pivot.to_numpy(dtype=float),
            aspect="auto",
        )
        axis.set_title(
            f"NQ Profit Factor — {direction.title()}"
        )
        axis.set_xlabel("Final entry time (New York)")
        axis.set_ylabel("Opening range minutes")
        axis.set_xticks(range(len(pivot.columns)))
        axis.set_xticklabels(pivot.columns)
        axis.set_yticks(range(len(pivot.index)))
        axis.set_yticklabels(pivot.index)
        for row in range(len(pivot.index)):
            for column in range(len(pivot.columns)):
                value = pivot.iloc[row, column]
                axis.text(
                    column,
                    row,
                    f"{value:.3f}",
                    ha="center",
                    va="center",
                )
        figure.colorbar(image, ax=axis)
        figure.tight_layout()
        path = chart_root / (
            f"nq_pf_heatmap_{direction}.png"
        )
        figure.savefig(path, dpi=150)
        plt.close(figure)
        paths.append(path)

    if selected_nq_equity is not None:
        figure, axis = plt.subplots(
            figsize=(13, 5)
        )
        dates = pd.to_datetime(
            selected_nq_equity["session_date"]
        )
        axis.plot(
            dates,
            100_000.0
            + selected_nq_equity[
                "cumulative_net_pnl_usd"
            ],
        )
        axis.set_title(
            "Selected candidate NQ total equity"
        )
        axis.set_ylabel("Equity (USD)")
        axis.grid(True, alpha=0.25)
        figure.tight_layout()
        path = chart_root / "selected_nq_equity.png"
        figure.savefig(path, dpi=150)
        plt.close(figure)
        paths.append(path)

        figure, axis = plt.subplots(
            figsize=(13, 4)
        )
        axis.plot(
            dates,
            selected_nq_equity["drawdown_usd"]
            / 100_000.0
            * 100.0,
        )
        axis.set_title(
            "Selected candidate NQ drawdown"
        )
        axis.set_ylabel("Drawdown (%)")
        axis.grid(True, alpha=0.25)
        figure.tight_layout()
        path = chart_root / "selected_nq_drawdown.png"
        figure.savefig(path, dpi=150)
        plt.close(figure)
        paths.append(path)

    if selected_mnq_equity is not None:
        figure, axis = plt.subplots(
            figsize=(13, 5)
        )
        dates = pd.to_datetime(
            selected_mnq_equity["session_date"]
        )
        axis.plot(
            dates,
            10_000.0
            + selected_mnq_equity[
                "cumulative_net_pnl_usd"
            ],
        )
        axis.set_title(
            "Selected candidate MNQ total equity"
        )
        axis.set_ylabel("Equity (USD)")
        axis.grid(True, alpha=0.25)
        figure.tight_layout()
        path = chart_root / "selected_mnq_equity.png"
        figure.savefig(path, dpi=150)
        plt.close(figure)
        paths.append(path)

    if not walk_forward.empty:
        figure, axis = plt.subplots(
            figsize=(12, 5)
        )
        axis.bar(
            walk_forward["fold"].astype(str),
            walk_forward[
                "nq_test_net_profit_usd"
            ],
        )
        axis.set_title(
            "Anchored walk-forward NQ net profit"
        )
        axis.set_xlabel("Test fold")
        axis.set_ylabel("Net profit (USD)")
        axis.grid(True, axis="y", alpha=0.25)
        figure.tight_layout()
        path = chart_root / "walk_forward_nq.png"
        figure.savefig(path, dpi=150)
        plt.close(figure)
        paths.append(path)

    if not mcpt.empty:
        figure, axis = plt.subplots(
            figsize=(12, 5)
        )
        axis.hist(
            mcpt[
                "best_selection_statistic"
            ].astype(float),
            bins=35,
        )
        axis.axvline(
            real_statistic,
            linestyle="--",
            linewidth=2,
            label="Real selection statistic",
        )
        axis.set_title(
            "Selection-aware MCPT null distribution"
        )
        axis.set_xlabel("Best 27-candidate statistic")
        axis.set_ylabel("Permutations")
        axis.legend()
        axis.grid(True, axis="y", alpha=0.25)
        figure.tight_layout()
        path = chart_root / "selection_mcpt.png"
        figure.savefig(path, dpi=150)
        plt.close(figure)
        paths.append(path)

    return paths


def build_exp006_report(
    *,
    report_root: Path,
    decision: dict[str, Any],
    grid: pd.DataFrame,
    walk_forward: pd.DataFrame,
    mcpt: pd.DataFrame,
    selected_nq_equity: pd.DataFrame | None,
    selected_mnq_equity: pd.DataFrame | None,
) -> Path:
    report_root.mkdir(parents=True, exist_ok=True)
    selected_rows = grid.loc[grid["selected"]]
    selected = (
        selected_rows.iloc[0]
        if len(selected_rows) == 1
        else None
    )
    baseline = grid.loc[
        grid["parameter_key"].eq(
            "or15_entry1200_both"
        )
    ].iloc[0]
    charts = write_exp006_charts(
        report_root=report_root,
        grid=grid,
        walk_forward=walk_forward,
        mcpt=mcpt,
        real_statistic=float(
            decision["mcpt"][
                "real_selection_statistic"
            ]
        ),
        selected_nq_equity=(
            selected_nq_equity
        ),
        selected_mnq_equity=(
            selected_mnq_equity
        ),
    )
    def chart_markup(paths: list[Path]) -> str:
        return "".join(
            f'<img class="chart" src="{html.escape(path.relative_to(report_root).as_posix())}">'
            for path in paths
        )

    equity_chart_html = chart_markup(
        [
            path
            for path in charts
            if "equity" in path.stem
            or "drawdown" in path.stem
        ]
    )
    surface_chart_html = chart_markup(
        [path for path in charts if "heatmap" in path.stem]
    )
    walk_forward_chart_html = chart_markup(
        [path for path in charts if "walk_forward" in path.stem]
    )
    mcpt_chart_html = chart_markup(
        [path for path in charts if "mcpt" in path.stem]
    )
    comparison = _vertical_comparison(
        selected,
        baseline,
    )
    gates = pd.DataFrame(
        [
            {
                "Gate": name,
                "Actual": json.dumps(
                    value["actual"],
                    default=str,
                ),
                "Rule": (
                    f"{value['operator']} "
                    f"{value['threshold']}"
                ),
                "Passed": value["passed"],
            }
            for name, value in decision[
                "evaluation"
            ]["gates"].items()
        ]
    )
    ranked = grid.sort_values(
        [
            "median_component_rank",
            "parameter_key",
        ]
    ).reset_index(drop=True)

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>EXP-006 Structured ORB Optimization</title>
<style>
:root {{ color-scheme: light dark; --bg:#07111f; --panel:#101d31; --line:#2b3e5d; --text:#edf3fb; --muted:#9eb0c7; --accent:#7dd3fc; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--text); font-family:Inter,Segoe UI,Arial,sans-serif; line-height:1.5; }}
nav {{ position:fixed; top:0; left:0; bottom:0; width:230px; padding:24px 16px; background:#0b1728; border-right:1px solid var(--line); overflow:auto; }}
nav strong {{ display:block; margin-bottom:16px; }}
nav a {{ display:block; color:var(--muted); text-decoration:none; padding:7px 8px; border-radius:8px; }}
nav a:hover {{ color:var(--text); background:var(--panel); }}
main {{ margin-left:230px; width:min(1350px,calc(100% - 262px)); padding:30px 0 70px; }}
header, section {{ background:var(--panel); border:1px solid var(--line); border-radius:16px; padding:22px; margin-bottom:18px; overflow:auto; }}
h1,h2 {{ margin-top:0; }}
.status {{ display:inline-block; padding:7px 11px; border:1px solid var(--line); border-radius:999px; color:var(--accent); font-weight:700; }}
.data-table {{ width:100%; border-collapse:collapse; min-width:780px; }}
th,td {{ border-bottom:1px solid var(--line); padding:9px 10px; text-align:left; white-space:nowrap; }}
th {{ background:#172741; position:sticky; top:0; }}
.chart {{ display:block; width:100%; height:auto; margin:18px 0; border:1px solid var(--line); border-radius:12px; background:white; }}
.note {{ color:var(--muted); }}
code {{ color:var(--accent); }}
@media(max-width:850px) {{ nav {{ position:static; width:auto; }} main {{ margin-left:0; width:calc(100% - 24px); margin:auto; }} }}
</style>
</head>
<body>
<nav>
<strong>EXP-006</strong>
<a href="#overview">Overview</a>
<a href="#comparison">Control vs selected</a>
<a href="#equity">Equity and drawdown</a>
<a href="#surface">Parameter surface</a>
<a href="#walkforward">Walk-forward</a>
<a href="#mcpt">Selection-aware MCPT</a>
<a href="#gates">Decision gates</a>
<a href="#grid">Complete grid</a>
</nav>
<main>
<header id="overview">
<h1>EXP-006 Structured NQ/MNQ ORB Optimization</h1>
<p class="status">{html.escape(str(decision['evaluation']['decision']))}</p>
<p>This is an exploratory structured optimization because 2019–2025 was already viewed during EXP-005. A historical pass can nominate one candidate for forward paper comparison only.</p>
<p class="note">EXP-005 remains frozen and unchanged. All summaries run vertically from top to bottom.</p>
</header>
<section id="comparison"><h2>EXP-005 control versus EXP-006 selection</h2>{_table(comparison)}</section>
<section id="equity"><h2>Total equity and drawdown</h2><p>Equity uses analytical reference capital of $100,000 for NQ and $10,000 for MNQ. These are reporting denominators, not margin recommendations.</p>{equity_chart_html}</section>
<section id="surface"><h2>Parameter surface and neighbour stability</h2><p>Heatmaps are separated by direction and displayed full width.</p>{surface_chart_html}</section>
<section id="walkforward"><h2>Anchored annual walk-forward</h2>{walk_forward_chart_html}{_table(walk_forward)}</section>
<section id="mcpt"><h2>Selection-aware MCPT</h2><p>All 27 candidates were evaluated inside each permutation. P-value: <strong>{decision['mcpt']['p_value']:.6f}</strong>.</p>{mcpt_chart_html}{_table(mcpt.head(100))}<p class="note">Showing the first 100 permutation rows; the complete CSV is retained in results.</p></section>
<section id="gates"><h2>Historical decision gates</h2>{_table(gates)}</section>
<section id="grid"><h2>Complete ranked 27-candidate grid</h2>{_table(ranked)}</section>
</main>
</body>
</html>"""
    path = report_root / "report.html"
    path.write_text(page, encoding="utf-8")
    return path
