from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


REPORT_VERSION = (
    "exp008_vertical_exit_geometry_report_v1"
)


def _money(value: Any) -> str:
    if (
        value is None
        or not np.isfinite(float(value))
    ):
        return "—"
    number = float(value)
    sign = "−" if number < 0 else ""
    return (
        f"{sign}${abs(number):,.2f}"
    )


def _number(
    value: Any,
    digits: int = 3,
) -> str:
    if (
        value is None
        or not np.isfinite(float(value))
    ):
        return "—"
    return f"{float(value):,.{digits}f}"


def _percent(
    value: Any,
    digits: int = 2,
) -> str:
    if (
        value is None
        or not np.isfinite(float(value))
    ):
        return "—"
    return f"{float(value):,.{digits}f}%"


def _save_equity_chart(
    frame: pd.DataFrame,
    *,
    title: str,
    output: Path,
) -> None:
    dates = pd.to_datetime(
        frame["session_date"]
    )
    figure, axis = plt.subplots(
        figsize=(12, 5.2)
    )
    axis.plot(
        dates,
        frame[
            "cumulative_net_pnl_usd"
        ],
    )
    axis.axhline(
        0.0,
        linewidth=0.8,
    )
    axis.set_title(title)
    axis.set_xlabel("Session")
    axis.set_ylabel(
        "Cumulative net PnL (USD)"
    )
    axis.grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(
        output,
        dpi=150,
    )
    plt.close(figure)


def _save_drawdown_chart(
    frame: pd.DataFrame,
    *,
    title: str,
    reference_capital: float,
    output: Path,
) -> None:
    dates = pd.to_datetime(
        frame["session_date"]
    )
    drawdown_percent = (
        frame[
            "drawdown_usd"
        ].to_numpy(dtype=float)
        / float(reference_capital)
        * 100.0
    )
    figure, axis = plt.subplots(
        figsize=(12, 4.8)
    )
    axis.fill_between(
        dates,
        drawdown_percent,
        0.0,
        alpha=0.35,
    )
    axis.plot(
        dates,
        drawdown_percent,
    )
    axis.axhline(
        0.0,
        linewidth=0.8,
    )
    axis.set_title(title)
    axis.set_xlabel("Session")
    axis.set_ylabel(
        "Drawdown (% of reference capital)"
    )
    axis.grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(
        output,
        dpi=150,
    )
    plt.close(figure)


def _save_annual_chart(
    frame: pd.DataFrame,
    output: Path,
) -> None:
    pivot = frame.pivot(
        index="year",
        columns="symbol",
        values="net_profit_usd",
    ).sort_index()
    figure, axis = plt.subplots(
        figsize=(12, 5.0)
    )
    pivot.plot(
        kind="bar",
        ax=axis,
    )
    axis.axhline(
        0.0,
        linewidth=0.8,
    )
    axis.set_title(
        "Selected candidate annual net profit"
    )
    axis.set_xlabel("Year")
    axis.set_ylabel(
        "Net PnL (USD)"
    )
    axis.grid(
        axis="y",
        alpha=0.25,
    )
    figure.tight_layout()
    figure.savefig(
        output,
        dpi=150,
    )
    plt.close(figure)


def _save_walk_forward_chart(
    frame: pd.DataFrame,
    output: Path,
) -> None:
    figure, axis = plt.subplots(
        figsize=(12, 5.0)
    )
    axis.bar(
        frame["fold"].astype(str),
        frame[
            "test_net_profit_usd"
        ],
    )
    axis.axhline(
        0.0,
        linewidth=0.8,
    )
    axis.set_title(
        "Anchored walk-forward test-fold net profit"
    )
    axis.set_xlabel("Fold")
    axis.set_ylabel(
        "NQ net PnL (USD)"
    )
    axis.grid(
        axis="y",
        alpha=0.25,
    )
    figure.tight_layout()
    figure.savefig(
        output,
        dpi=150,
    )
    plt.close(figure)


def _save_cost_chart(
    frame: pd.DataFrame,
    output: Path,
) -> None:
    pivot = frame.pivot(
        index="slippage_ticks_per_side",
        columns="symbol",
        values="net_profit_usd",
    ).sort_index()
    figure, axis = plt.subplots(
        figsize=(12, 5.0)
    )
    pivot.plot(
        marker="o",
        ax=axis,
    )
    axis.axhline(
        0.0,
        linewidth=0.8,
    )
    axis.set_title(
        "Selected candidate cost sensitivity"
    )
    axis.set_xlabel(
        "Slippage ticks per side"
    )
    axis.set_ylabel(
        "Net PnL (USD)"
    )
    axis.grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(
        output,
        dpi=150,
    )
    plt.close(figure)


def _save_mcpt_chart(
    frame: pd.DataFrame,
    *,
    real_pf: float,
    output: Path,
) -> None:
    values = frame[
        "selected_trade_profit_factor"
    ].replace(
        [np.inf, -np.inf],
        np.nan,
    ).dropna()
    figure, axis = plt.subplots(
        figsize=(12, 5.0)
    )
    axis.hist(
        values,
        bins=40,
        alpha=0.75,
    )
    axis.axvline(
        real_pf,
        linewidth=2.0,
        label="Real selected PF",
    )
    axis.set_title(
        "Selection-aware MCPT selected-PF distribution"
    )
    axis.set_xlabel(
        "Permuted selected Profit Factor"
    )
    axis.set_ylabel("Frequency")
    axis.legend()
    axis.grid(
        axis="y",
        alpha=0.25,
    )
    figure.tight_layout()
    figure.savefig(
        output,
        dpi=150,
    )
    plt.close(figure)


def _save_parameter_heatmaps(
    grid: pd.DataFrame,
    assets: Path,
) -> list[Path]:
    output_files: list[Path] = []

    for flat in (
        "12:00",
        "14:00",
        "15:55",
    ):
        subset = grid.loc[
            grid[
                "forced_flat_time_new_york"
            ].eq(flat)
        ]
        pivot = subset.pivot(
            index="opening_range_minutes",
            columns="reward_to_risk",
            values="nq_trade_profit_factor",
        ).sort_index()

        figure, axis = plt.subplots(
            figsize=(8.5, 5.2)
        )
        image = axis.imshow(
            pivot.to_numpy(dtype=float),
            aspect="auto",
        )
        axis.set_xticks(
            range(len(pivot.columns))
        )
        axis.set_xticklabels(
            [
                f"{value:g}R"
                for value in pivot.columns
            ]
        )
        axis.set_yticks(
            range(len(pivot.index))
        )
        axis.set_yticklabels(
            [
                f"{value} min"
                for value in pivot.index
            ]
        )
        axis.set_xlabel(
            "Profit target"
        )
        axis.set_ylabel(
            "Opening range"
        )
        axis.set_title(
            "NQ Profit Factor surface · "
            f"flat {flat}"
        )

        for row in range(
            len(pivot.index)
        ):
            for column in range(
                len(pivot.columns)
            ):
                value = float(
                    pivot.iloc[
                        row,
                        column,
                    ]
                )
                axis.text(
                    column,
                    row,
                    _number(
                        value,
                        3,
                    ),
                    ha="center",
                    va="center",
                )

        figure.colorbar(
            image,
            ax=axis,
            label="NQ Profit Factor",
        )
        figure.tight_layout()
        output = (
            assets
            / (
                "pf_surface_flat_"
                + flat.replace(
                    ":",
                    "",
                )
                + ".png"
            )
        )
        figure.savefig(
            output,
            dpi=150,
        )
        plt.close(figure)
        output_files.append(output)

    return output_files


def _table(
    frame: pd.DataFrame,
    *,
    columns: list[str] | None = None,
) -> str:
    local = (
        frame.copy()
        if columns is None
        else frame.loc[
            :,
            [
                column
                for column in columns
                if column in frame.columns
            ],
        ].copy()
    )
    return local.to_html(
        index=False,
        border=0,
        classes="data-table",
        float_format=(
            lambda value: (
                f"{value:,.4f}"
            )
        ),
    )



def build_exp008_no_candidate_report(
    *,
    decision: dict[str, Any],
    grid: pd.DataFrame,
    walk_forward: pd.DataFrame,
    mcpt: pd.DataFrame,
    output_dir: Path,
) -> Path:
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )
    assets = output_dir / "assets"
    assets.mkdir(
        parents=True,
        exist_ok=True,
    )

    evaluation = decision["evaluation"]
    if evaluation["selected_candidate_exists"] is not False:
        raise ValueError(
            "EXP-008 no-candidate report requires "
            "a no-candidate decision."
        )

    _save_walk_forward_chart(
        walk_forward,
        assets / "walk_forward_net_profit.png",
    )
    _save_mcpt_chart(
        mcpt,
        real_pf=0.0,
        output=(
            assets / "mcpt_selected_pf.png"
        ),
    )
    heatmap_files = _save_parameter_heatmaps(
        grid,
        assets,
    )

    grid_html = _table(
        grid.sort_values(
            [
                "opening_range_minutes",
                "reward_to_risk",
                "forced_flat_time_new_york",
            ]
        ),
        columns=[
            "parameter_key",
            "opening_range_minutes",
            "reward_to_risk",
            "forced_flat_time_new_york",
            "nq_completed_trades",
            "nq_trade_profit_factor",
            "nq_net_profit_usd",
            "nq_maximum_drawdown_usd",
            "nq_net_profit_to_drawdown",
            "profitable_neighbor_fraction",
            "neighbor_median_nq_trade_profit_factor",
            "neighbor_stable",
            "eligible",
            "selected",
        ],
    )
    walk_html = _table(
        walk_forward.sort_values("fold")
    )

    failed = evaluation["failed_gates"]
    failed_text = (
        "None"
        if not failed
        else ", ".join(failed)
    )
    decision_label = (
        evaluation["decision"]
        .replace("_", " ")
        .title()
    )

    gate_rows = "".join(
        "<tr>"
        f"<th>{html.escape(name)}</th>"
        f"<td>{html.escape(str(gate['actual']))}</td>"
        f"<td>{html.escape(str(gate['operator']))}</td>"
        f"<td>{html.escape(str(gate['threshold']))}</td>"
        f"<td class={'pass' if gate['passed'] else 'fail'}>"
        f"{'PASS' if gate['passed'] else 'FAIL'}</td>"
        "</tr>"
        for name, gate in evaluation["gates"].items()
    )

    baseline = decision["baseline_comparison"]
    heatmaps_html = "".join(
        (
            '<img src="assets/'
            + path.name
            + '" alt="Parameter surface">'
        )
        for path in heatmap_files
    )

    document = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>EXP-008 ORB Exit Geometry</title>
<style>
:root {{ color-scheme: light dark; --panel:#151922; --line:#343b49; --muted:#9da7b8; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:Segoe UI,Arial,sans-serif; line-height:1.5; background:#0d1016; color:#edf1f7; }}
nav {{ position:fixed; inset:0 auto 0 0; width:260px; padding:28px 20px; background:#11151d; border-right:1px solid var(--line); overflow:auto; }}
nav h1 {{ font-size:18px; margin:0 0 22px; }}
nav a {{ display:block; color:#cbd4e2; text-decoration:none; padding:8px 0; }}
main {{ margin-left:260px; max-width:1320px; padding:36px 42px 80px; }}
section {{ width:100%; margin:0 0 34px; padding:26px; background:var(--panel); border:1px solid var(--line); border-radius:12px; overflow:auto; }}
h1,h2,h3 {{ line-height:1.2; }}
.hero {{ padding:34px; }}
.kicker {{ color:var(--muted); text-transform:uppercase; letter-spacing:.12em; font-size:12px; }}
.status {{ font-size:24px; font-weight:700; margin:10px 0; }}
table {{ width:100%; border-collapse:collapse; white-space:nowrap; }}
th,td {{ text-align:right; padding:10px 12px; border-bottom:1px solid var(--line); vertical-align:top; }}
th:first-child,td:first-child {{ text-align:left; }}
img {{ width:100%; height:auto; display:block; background:white; border-radius:8px; margin:14px 0 26px; }}
.note {{ color:var(--muted); }}
.pass {{ color:#7ee2a8; }} .fail {{ color:#ff9b9b; }}
@media (max-width:900px) {{ nav {{ position:static; width:auto; }} main {{ margin:0; padding:20px; }} }}
</style>
</head>
<body>
<nav>
<h1>EXP-008</h1>
<a href="#decision">Decision</a>
<a href="#selection">Selection outcome</a>
<a href="#grid">Complete grid</a>
<a href="#surfaces">Parameter surfaces</a>
<a href="#walkforward">Anchored walk-forward</a>
<a href="#mcpt">Selection-aware MCPT</a>
<a href="#baseline">EXP-007 comparison</a>
<a href="#gates">Decision gates</a>
</nav>
<main>
<section class="hero" id="decision">
<div class="kicker">Structured exit-geometry optimization · {REPORT_VERSION}</div>
<h1>Long-Only NQ/MNQ Opening Range Breakout</h1>
<div class="status fail">{html.escape(decision_label)}</div>
<p>Failed gates: {html.escape(failed_text)}</p>
<p class="note">No candidate satisfied the locked eligibility and immediate-neighbour stability procedure. This is a completed negative result, not a software failure. No live trading is authorized.</p>
</section>
<section id="selection"><h2>Selection outcome</h2>
<p><strong>Selected candidate:</strong> None</p>
<p><strong>Eligible candidates:</strong> {decision['grid']['eligible_candidates']}</p>
<p><strong>Stable eligible candidates:</strong> {decision['grid']['stable_eligible_candidates']}</p>
<p class="note">The preregistered no-eligible-candidate statistic is 0.0. Candidate-specific MNQ, cost, bootstrap, annual-equity and drawdown analyses are not applicable because no final geometry was selected.</p>
</section>
<section id="grid"><h2>Complete 27-candidate grid</h2>{grid_html}</section>
<section id="surfaces"><h2>Parameter surfaces</h2>{heatmaps_html}</section>
<section id="walkforward"><h2>Anchored walk-forward evaluation</h2><img src="assets/walk_forward_net_profit.png" alt="Walk-forward results">{walk_html}</section>
<section id="mcpt"><h2>Selection-aware MCPT</h2><p><strong>Real selected statistic:</strong> 0.000000</p><p><strong>Permutations:</strong> {decision['mcpt']['permutations']:,}</p><p><strong>p-value:</strong> {_number(decision['mcpt']['p_value'], 6)}</p><p><strong>Permutations at least real:</strong> {decision['mcpt']['permutations_at_least_real']}</p><p class="note">All 27 candidates and the complete neighbour-based selection procedure were rerun inside every permutation.</p><img src="assets/mcpt_selected_pf.png" alt="MCPT distribution"></section>
<section id="baseline"><h2>Frozen EXP-007 baseline comparison</h2><table><tbody>
<tr><th>EXP-007 parameter key</th><td>{html.escape(str(baseline['exp007_parameter_key']))}</td></tr>
<tr><th>EXP-007 NQ Profit Factor</th><td>{_number(baseline['exp007_nq_trade_profit_factor'], 6)}</td></tr>
<tr><th>EXP-008 selected NQ Profit Factor</th><td>Not applicable</td></tr>
<tr><th>Required comparison</th><td>A stable selected EXP-008 candidate would have needed Profit Factor strictly above EXP-007</td></tr>
</tbody></table></section>
<section id="gates"><h2>Locked decision gates</h2><table><thead><tr><th>Gate</th><th>Actual</th><th>Operator</th><th>Threshold</th><th>Result</th></tr></thead><tbody>{gate_rows}</tbody></table></section>
</main>
</body>
</html>"""

    report_file = output_dir / "report.html"
    report_file.write_text(
        document,
        encoding="utf-8",
    )

    metadata = {
        "schema_version": 1,
        "experiment_id": "EXP-008",
        "report_version": REPORT_VERSION,
        "report_type": (
            "structured_orb_exit_geometry_no_candidate_saved_results"
        ),
        "selected_parameter_key": None,
        "primary_metrics": {
            "primary_symbol": "NQ",
            "profit_factor": 0.0,
            "net_profit_usd": 0.0,
            "total_trades": 0,
            "mcpt_p_value": decision["mcpt"]["p_value"],
            "result_decision": evaluation["decision"],
        },
        "failed_gates": failed,
        "optimization_enabled": True,
        "parameter_combinations": 27,
        "selection_aware_mcpt": True,
        "selected_candidate_exists": False,
        "live_trading_authorized": False,
    }
    (output_dir / "report_metadata.json").write_text(
        json.dumps(
            metadata,
            indent=2,
            allow_nan=False,
        ),
        encoding="utf-8",
    )

    return report_file

def build_exp008_report(
    *,
    decision: dict[str, Any],
    grid: pd.DataFrame,
    nq_equity: pd.DataFrame,
    mnq_equity: pd.DataFrame,
    yearly: pd.DataFrame,
    walk_forward: pd.DataFrame,
    cost_sensitivity: pd.DataFrame,
    mcpt: pd.DataFrame,
    output_dir: Path,
) -> Path:
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )
    assets = output_dir / "assets"
    assets.mkdir(
        parents=True,
        exist_ok=True,
    )

    selected = decision[
        "selection"
    ]["selected_parameters"]
    if selected is None:
        raise ValueError(
            "EXP-008 report requires a selected "
            "candidate."
        )

    nq = decision["results"]["NQ"]
    mnq = decision["results"]["MNQ"]
    evaluation = decision[
        "evaluation"
    ]

    _save_equity_chart(
        nq_equity,
        title=(
            "Selected NQ total equity"
        ),
        output=(
            assets
            / "nq_total_equity.png"
        ),
    )
    _save_drawdown_chart(
        nq_equity,
        title=(
            "Selected NQ drawdown"
        ),
        reference_capital=100_000.0,
        output=(
            assets
            / "nq_drawdown_percent.png"
        ),
    )
    _save_equity_chart(
        mnq_equity,
        title=(
            "Selected MNQ total equity"
        ),
        output=(
            assets
            / "mnq_total_equity.png"
        ),
    )
    _save_drawdown_chart(
        mnq_equity,
        title=(
            "Selected MNQ drawdown"
        ),
        reference_capital=10_000.0,
        output=(
            assets
            / "mnq_drawdown_percent.png"
        ),
    )
    _save_annual_chart(
        yearly,
        assets
        / "annual_net_profit.png",
    )
    _save_walk_forward_chart(
        walk_forward,
        assets
        / "walk_forward_net_profit.png",
    )
    _save_cost_chart(
        cost_sensitivity,
        assets
        / "cost_sensitivity.png",
    )
    _save_mcpt_chart(
        mcpt,
        real_pf=float(
            nq[
                "trade_profit_factor"
            ]
        ),
        output=(
            assets
            / "mcpt_selected_pf.png"
        ),
    )
    heatmap_files = (
        _save_parameter_heatmaps(
            grid,
            assets,
        )
    )

    decision_label = (
        evaluation["decision"]
        .replace("_", " ")
        .title()
    )
    failed = evaluation[
        "failed_gates"
    ]
    failed_text = (
        "None"
        if not failed
        else ", ".join(failed)
    )

    metric_rows = [
        (
            "Completed trades",
            nq["completed_trades"],
            nq["long_trades"],
            0,
        ),
        (
            "Net profit",
            _money(
                nq["net_profit_usd"]
            ),
            _money(
                nq["net_profit_usd"]
            ),
            _money(0),
        ),
        (
            "Profit Factor",
            _number(
                nq[
                    "trade_profit_factor"
                ]
            ),
            _number(
                nq[
                    "trade_profit_factor"
                ]
            ),
            "—",
        ),
        (
            "Win rate",
            _percent(
                nq["win_rate_percent"]
            ),
            _percent(
                nq["win_rate_percent"]
            ),
            "—",
        ),
        (
            "Average trade",
            _money(
                nq["average_trade_usd"]
            ),
            _money(
                nq["average_trade_usd"]
            ),
            "—",
        ),
        (
            "Maximum drawdown",
            _money(
                nq[
                    "maximum_drawdown_usd"
                ]
            ),
            _money(
                nq[
                    "maximum_drawdown_usd"
                ]
            ),
            "—",
        ),
        (
            "Maximum drawdown %",
            _percent(
                nq[
                    "maximum_drawdown_percent"
                ]
            ),
            _percent(
                nq[
                    "maximum_drawdown_percent"
                ]
            ),
            "—",
        ),
    ]
    metrics_html = "".join(
        "<tr>"
        f"<th>{html.escape(str(name))}</th>"
        f"<td>{html.escape(str(all_value))}</td>"
        f"<td>{html.escape(str(long_value))}</td>"
        f"<td>{html.escape(str(short_value))}</td>"
        "</tr>"
        for (
            name,
            all_value,
            long_value,
            short_value,
        ) in metric_rows
    )

    gate_rows = "".join(
        "<tr>"
        f"<th>{html.escape(name.replace('_', ' ').title())}</th>"
        f"<td>{html.escape(str(gate['actual']))}</td>"
        f"<td>{html.escape(str(gate['operator']))}</td>"
        f"<td>{html.escape(str(gate['threshold']))}</td>"
        f"<td>{'Pass' if gate['passed'] else 'Fail'}</td>"
        "</tr>"
        for (
            name,
            gate,
        ) in evaluation[
            "gates"
        ].items()
    )

    selected_row = grid.loc[
        grid["selected"]
    ]
    neighbor_keys = set()
    if len(selected_row) == 1:
        value = str(
            selected_row.iloc[0].get(
                "neighbor_keys",
                "",
            )
        )
        neighbor_keys = {
            key
            for key in value.split("|")
            if key
        }
    neighbor_table = grid.loc[
        grid[
            "parameter_key"
        ].isin(
            neighbor_keys
            | {
                selected[
                    "parameter_key"
                ]
            }
        )
    ].copy()

    grid_html = _table(
        grid.sort_values(
            [
                "opening_range_minutes",
                "reward_to_risk",
                "forced_flat_time_new_york",
            ]
        )
    )
    neighbor_html = _table(
        neighbor_table,
        columns=[
            "parameter_key",
            "nq_trade_profit_factor",
            "nq_net_profit_usd",
            "nq_completed_trades",
            "profitable_neighbor_fraction",
            "neighbor_median_nq_trade_profit_factor",
            "neighbor_stable",
            "selected",
        ],
    )
    yearly_html = _table(
        yearly.sort_values(
            [
                "year",
                "symbol",
            ]
        )
    )
    walk_html = _table(
        walk_forward.sort_values(
            "fold"
        )
    )
    cost_html = _table(
        cost_sensitivity.sort_values(
            [
                "symbol",
                "slippage_ticks_per_side",
            ]
        )
    )

    baseline = decision[
        "baseline_comparison"
    ]
    bootstrap = decision[
        "bootstrap"
    ]

    heatmaps_html = "".join(
        (
            "<img src=\"assets/"
            + path.name
            + "\" alt=\"Parameter surface\">"
        )
        for path in heatmap_files
    )

    document = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>EXP-008 ORB Exit Geometry</title>
<style>
:root {{ color-scheme: light dark; --panel:#151922; --line:#343b49; --muted:#9da7b8; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:Segoe UI,Arial,sans-serif; line-height:1.5; background:#0d1016; color:#edf1f7; }}
nav {{ position:fixed; inset:0 auto 0 0; width:260px; padding:28px 20px; background:#11151d; border-right:1px solid var(--line); overflow:auto; }}
nav h1 {{ font-size:18px; margin:0 0 22px; }}
nav a {{ display:block; color:#cbd4e2; text-decoration:none; padding:8px 0; }}
main {{ margin-left:260px; max-width:1320px; padding:36px 42px 80px; }}
section {{ width:100%; margin:0 0 34px; padding:26px; background:var(--panel); border:1px solid var(--line); border-radius:12px; overflow:auto; }}
h1,h2,h3 {{ line-height:1.2; }}
.hero {{ padding:34px; }}
.kicker {{ color:var(--muted); text-transform:uppercase; letter-spacing:.12em; font-size:12px; }}
.status {{ font-size:24px; font-weight:700; margin:10px 0; }}
.summary {{ display:grid; grid-template-columns:1fr; gap:12px; }}
.summary div {{ padding:12px 0; border-bottom:1px solid var(--line); }}
table {{ width:100%; border-collapse:collapse; white-space:nowrap; }}
th,td {{ text-align:right; padding:10px 12px; border-bottom:1px solid var(--line); vertical-align:top; }}
th:first-child,td:first-child {{ text-align:left; }}
img {{ width:100%; height:auto; display:block; background:white; border-radius:8px; margin:14px 0 26px; }}
.note {{ color:var(--muted); }}
.pass {{ color:#7ee2a8; }} .fail {{ color:#ff9b9b; }}
@media (max-width:900px) {{ nav {{ position:static; width:auto; }} main {{ margin:0; padding:20px; }} }}
</style>
</head>
<body>
<nav>
<h1>EXP-008</h1>
<a href="#decision">Decision</a>
<a href="#selected">Selected geometry</a>
<a href="#performance">Performance</a>
<a href="#equity">Equity and drawdown</a>
<a href="#grid">Complete grid</a>
<a href="#surfaces">Parameter surfaces</a>
<a href="#neighbors">Neighbour stability</a>
<a href="#walkforward">Anchored walk-forward</a>
<a href="#annual">Annual results</a>
<a href="#costs">Cost sensitivity</a>
<a href="#mcpt">Selection-aware MCPT</a>
<a href="#bootstrap">Bootstrap</a>
<a href="#baseline">EXP-007 comparison</a>
<a href="#gates">Decision gates</a>
</nav>
<main>
<section class="hero" id="decision">
<div class="kicker">Structured exit-geometry optimization · {REPORT_VERSION}</div>
<h1>Long-Only NQ/MNQ Opening Range Breakout</h1>
<div class="status {'pass' if evaluation['passed'] else 'fail'}">{html.escape(decision_label)}</div>
<p>Failed gates: {html.escape(failed_text)}</p>
<p class="note">The complete 2019–2025 historical analysis is exploratory because the period had already been viewed. A passing result can only lock a candidate for new forward paper comparison. No live trading is authorized.</p>
</section>
<section id="selected"><h2>Selected geometry</h2>
<div class="summary">
<div><strong>Parameter key:</strong> {html.escape(selected['parameter_key'])}</div>
<div><strong>Opening range:</strong> {selected['opening_range_minutes']} minutes</div>
<div><strong>Profit target:</strong> {selected['reward_to_risk']}R</div>
<div><strong>Forced flat:</strong> {html.escape(selected['forced_flat_time_new_york'])} New York</div>
<div><strong>Direction:</strong> Long only</div>
<div><strong>Selection:</strong> Highest eligible NQ Profit Factor after locked neighbour-stability checks and tie-breaks</div>
</div></section>
<section id="performance"><h2>Selected NQ performance summary</h2>
<table><thead><tr><th>Metric</th><th>All trades</th><th>Long trades</th><th>Short trades</th></tr></thead><tbody>{metrics_html}</tbody></table>
<h3>MNQ implementation check</h3>
<table><tbody>
<tr><th>Completed trades</th><td>{mnq['completed_trades']}</td></tr>
<tr><th>Net profit</th><td>{_money(mnq['net_profit_usd'])}</td></tr>
<tr><th>Profit Factor</th><td>{_number(mnq['trade_profit_factor'])}</td></tr>
<tr><th>Maximum drawdown</th><td>{_money(mnq['maximum_drawdown_usd'])}</td></tr>
</tbody></table></section>
<section id="equity"><h2>NQ total equity</h2><img src="assets/nq_total_equity.png" alt="NQ total equity"><h3>NQ drawdown</h3><img src="assets/nq_drawdown_percent.png" alt="NQ drawdown"><h2>MNQ total equity</h2><img src="assets/mnq_total_equity.png" alt="MNQ total equity"><h3>MNQ drawdown</h3><img src="assets/mnq_drawdown_percent.png" alt="MNQ drawdown"></section>
<section id="grid"><h2>Complete 27-candidate grid</h2>{grid_html}</section>
<section id="surfaces"><h2>Parameter surfaces</h2>{heatmaps_html}</section>
<section id="neighbors"><h2>Selected candidate and immediate neighbours</h2>{neighbor_html}</section>
<section id="walkforward"><h2>Anchored walk-forward evaluation</h2><img src="assets/walk_forward_net_profit.png" alt="Walk-forward results">{walk_html}</section>
<section id="annual"><h2>Selected candidate annual results</h2><img src="assets/annual_net_profit.png" alt="Annual net profit">{yearly_html}</section>
<section id="costs"><h2>Selected candidate cost sensitivity</h2><img src="assets/cost_sensitivity.png" alt="Cost sensitivity">{cost_html}</section>
<section id="mcpt"><h2>Selection-aware MCPT</h2><p><strong>Permutations:</strong> {decision['mcpt']['permutations']:,}</p><p><strong>p-value:</strong> {_number(decision['mcpt']['p_value'], 6)}</p><p><strong>Permutations at least real:</strong> {decision['mcpt']['permutations_at_least_real']}</p><p class="note">All 27 candidates and the complete neighbour-based selection procedure were rerun inside every permutation.</p><img src="assets/mcpt_selected_pf.png" alt="MCPT distribution"></section>
<section id="bootstrap"><h2>Bootstrap diagnostics</h2><p>Average trade 95% interval: {_money(bootstrap['average_trade_usd_95_percentile_interval'][0])} to {_money(bootstrap['average_trade_usd_95_percentile_interval'][1])}</p><p>Profit Factor 95% interval: {_number(bootstrap['trade_profit_factor_95_percentile_interval'][0])} to {_number(bootstrap['trade_profit_factor_95_percentile_interval'][1])}</p><p class="note">Diagnostic only; not a decision gate.</p></section>
<section id="baseline"><h2>Frozen EXP-007 baseline comparison</h2><table><tbody>
<tr><th>EXP-007 parameter key</th><td>{html.escape(str(baseline['exp007_parameter_key']))}</td></tr>
<tr><th>EXP-007 NQ Profit Factor</th><td>{_number(baseline['exp007_nq_trade_profit_factor'], 6)}</td></tr>
<tr><th>EXP-008 selected NQ Profit Factor</th><td>{_number(baseline['exp008_selected_nq_trade_profit_factor'], 6)}</td></tr>
<tr><th>Absolute PF difference</th><td>{_number(baseline['absolute_profit_factor_difference'], 6)}</td></tr>
<tr><th>Required comparison</th><td>EXP-008 selected PF must be strictly greater than EXP-007 PF</td></tr>
</tbody></table></section>
<section id="gates"><h2>Locked decision gates</h2><table><thead><tr><th>Gate</th><th>Actual</th><th>Operator</th><th>Threshold</th><th>Result</th></tr></thead><tbody>{gate_rows}</tbody></table></section>
</main>
</body>
</html>"""

    report_file = (
        output_dir / "report.html"
    )
    report_file.write_text(
        document,
        encoding="utf-8",
    )

    metadata = {
        "schema_version": 1,
        "experiment_id": "EXP-008",
        "report_version": REPORT_VERSION,
        "report_type": (
            "structured_orb_exit_geometry_saved_results"
        ),
        "selected_parameter_key": (
            selected["parameter_key"]
        ),
        "primary_metrics": {
            "primary_symbol": "NQ",
            "profit_factor": (
                nq[
                    "trade_profit_factor"
                ]
            ),
            "net_profit_usd": (
                nq["net_profit_usd"]
            ),
            "total_return_percent": (
                nq["return_percent"]
            ),
            "win_rate_percent": (
                nq["win_rate_percent"]
            ),
            "max_drawdown_usd": (
                nq[
                    "maximum_drawdown_usd"
                ]
            ),
            "max_drawdown_percent": (
                nq[
                    "maximum_drawdown_percent"
                ]
            ),
            "total_trades": (
                nq["completed_trades"]
            ),
            "mcpt_p_value": (
                decision["mcpt"][
                    "p_value"
                ]
            ),
            "result_decision": (
                evaluation["decision"]
            ),
            "drawdown_percent_note": (
                "Uses the locked $100,000 analytical NQ "
                "reference capital; it is not a margin or "
                "account recommendation."
            ),
        },
        "failed_gates": failed,
        "optimization_enabled": True,
        "parameter_combinations": 27,
        "selection_aware_mcpt": True,
        "live_trading_authorized": False,
    }
    (
        output_dir
        / "report_metadata.json"
    ).write_text(
        json.dumps(
            metadata,
            indent=2,
            allow_nan=False,
        ),
        encoding="utf-8",
    )
    return report_file
