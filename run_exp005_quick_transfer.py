from __future__ import annotations

import argparse
from datetime import datetime, timezone
import html
import json
import math
from pathlib import Path
import subprocess
from typing import Any

import numpy as np
import pandas as pd

from exp005_futures_orb import (
    FuturesOrbResult,
    run_cost_sensitivity,
    run_futures_orb,
)
from exp005_missing_session_resolution import (
    validate_exp005_missing_session_resolution,
)
from exp005_preregistration import (
    get_exp005_preregistration,
    validate_exp005_preregistration,
)
from exp005_quick_transfer import (
    evaluate_exp005_quick_transfer,
)
from exp005_quick_transfer_implementation import (
    validate_exp005_quick_transfer_implementation,
)
from exp005_recheck_resolution import (
    validate_exp005_recheck_resolution,
)
from exp005_session_mcpt import (
    run_exp005_mcpt,
)
from experiment_lifecycle import (
    get_experiment_lifecycle,
)
from import_exp005_quantower_quick_data import (
    AUDIT_FILE,
    OUTPUT_FILES,
    verify_existing_import,
)


PROJECT_DIR = Path(__file__).resolve().parent
RESULT_ROOT = (
    PROJECT_DIR
    / "results"
    / "EXP-005"
    / "quick_transfer"
)
REPORT_ROOT = (
    PROJECT_DIR
    / "reports"
    / "EXP-005-quick-transfer"
)
DECISION_FILE = (
    RESULT_ROOT
    / "quick_transfer_decision.json"
)
MCPT_CHECKPOINT = (
    RESULT_ROOT
    / "mcpt_checkpoint.json"
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the protected EXP-005 NQ/MNQ "
            "quick transfer using only frozen "
            "2019–2022 data."
        )
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=0,
        help=(
            "MCPT worker count. Use 0 for automatic "
            "selection."
        ),
    )
    parser.add_argument(
        "--preflight",
        action="store_true",
        help=(
            "Verify the protected workflow and frozen "
            "data without calculating strategy results."
        ),
    )
    return parser.parse_args()


def git_state() -> dict[str, Any]:
    commit = subprocess.run(
        [
            "git",
            "rev-parse",
            "HEAD",
        ],
        cwd=PROJECT_DIR,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    short_commit = subprocess.run(
        [
            "git",
            "rev-parse",
            "--short",
            "HEAD",
        ],
        cwd=PROJECT_DIR,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    status = subprocess.run(
        [
            "git",
            "status",
            "--porcelain",
        ],
        cwd=PROJECT_DIR,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    return {
        "commit": commit,
        "short_commit": short_commit,
        "working_tree_clean": not bool(
            status
        ),
    }


def _json_safe(
    value: Any,
) -> Any:
    if isinstance(
        value,
        dict,
    ):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }

    if isinstance(
        value,
        (list, tuple),
    ):
        return [
            _json_safe(item)
            for item in value
        ]

    if isinstance(
        value,
        (np.integer,),
    ):
        return int(value)

    if isinstance(
        value,
        (np.floating,),
    ):
        value = float(value)

    if isinstance(value, float):
        if math.isnan(value):
            return None
        if math.isinf(value):
            return (
                "Infinity"
                if value > 0
                else "-Infinity"
            )
        return value

    if isinstance(
        value,
        (pd.Timestamp,),
    ):
        return value.isoformat()

    return value


def _atomic_json(
    payload: dict[str, Any],
    path: Path,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )
    temporary.write_text(
        json.dumps(
            _json_safe(payload),
            indent=2,
            allow_nan=False,
        ),
        encoding="utf-8",
    )
    temporary.replace(path)


def _atomic_csv(
    frame: pd.DataFrame,
    path: Path,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )
    frame.to_csv(
        temporary,
        index=False,
    )
    temporary.replace(path)


def load_frozen_data(
) -> tuple[
    dict[str, Any],
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    verify_existing_import()

    audit = json.loads(
        AUDIT_FILE.read_text(
            encoding="utf-8"
        )
    )

    if (
        audit.get(
            "confirmation_period_requested"
        )
        is not False
        or audit.get(
            "confirmation_export_detected"
        )
        is not False
    ):
        raise RuntimeError(
            "EXP-005 confirmation-period data "
            "was detected before a quick pass."
        )

    if audit.get(
        "strategy_results_calculated"
    ) is not False:
        raise RuntimeError(
            "The frozen import audit already "
            "contains strategy results."
        )

    if audit.get(
        "quick_transfer_decision_calculated"
    ) is not False:
        raise RuntimeError(
            "The frozen import audit claims a "
            "quick decision already exists."
        )

    required_audit = {
        "included_sessions": 906,
        "included_nq_one_minute_rows": (
            353_340
        ),
        "included_mnq_one_minute_rows": (
            353_340
        ),
        "included_nq_five_minute_rows": (
            70_668
        ),
        "included_mnq_five_minute_rows": (
            70_668
        ),
        "included_invalid_sessions": 0,
        "included_front_month_mismatch_sessions": 0,
    }

    for field, expected in (
        required_audit.items()
    ):
        actual = audit.get(field)

        if actual != expected:
            raise RuntimeError(
                f"Frozen import audit field {field} "
                f"changed: expected {expected}, "
                f"got {actual}."
            )

    frames: dict[str, pd.DataFrame] = {}

    for name, path in OUTPUT_FILES.items():
        frame = pd.read_parquet(path)
        frame.index = pd.to_datetime(
            frame.index,
            utc=True,
        )
        frame = frame.sort_index()
        frames[name] = frame

    if not frames["NQ_1m"].index.equals(
        frames["MNQ_1m"].index
    ):
        raise RuntimeError(
            "Frozen NQ/MNQ one-minute "
            "timestamps are not aligned."
        )

    if not frames["NQ_5m"].index.equals(
        frames["MNQ_5m"].index
    ):
        raise RuntimeError(
            "Frozen NQ/MNQ five-minute "
            "timestamps are not aligned."
        )

    for name, frame in frames.items():
        last_session = pd.to_datetime(
            frame["session_date"]
        ).max()

        if last_session > pd.Timestamp(
            "2022-12-30"
        ):
            raise RuntimeError(
                f"{name} contains protected "
                "confirmation-period rows."
            )

    return (
        audit,
        frames["NQ_1m"],
        frames["MNQ_1m"],
        frames["NQ_5m"],
        frames["MNQ_5m"],
    )


def _summary_frame(
    nq: FuturesOrbResult,
    mnq: FuturesOrbResult,
) -> pd.DataFrame:
    rows = []

    for result in (nq, mnq):
        rows.append(
            {
                **result.summary,
                "contract_multiplier_usd_per_point": (
                    result.contract
                    .multiplier_usd_per_point
                ),
                "tick_value_usd": (
                    result.contract
                    .tick_value_usd
                ),
            }
        )

    return pd.DataFrame(rows)


def _yearly_frame(
    nq: FuturesOrbResult,
    mnq: FuturesOrbResult,
) -> pd.DataFrame:
    frames = []

    for result in (nq, mnq):
        local = (
            result.yearly_results
            .copy()
        )
        local.insert(
            0,
            "symbol",
            result.symbol,
        )
        frames.append(local)

    return pd.concat(
        frames,
        ignore_index=True,
    )


def _format_number(
    value: Any,
    *,
    digits: int = 3,
) -> str:
    if value is None:
        return "N/A"

    try:
        numeric = float(value)
    except (
        TypeError,
        ValueError,
    ):
        return html.escape(
            str(value)
        )

    if math.isnan(numeric):
        return "N/A"

    if math.isinf(numeric):
        return (
            "∞"
            if numeric > 0
            else "−∞"
        )

    return f"{numeric:,.{digits}f}"


def _write_charts(
    *,
    nq: FuturesOrbResult,
    mnq: FuturesOrbResult,
    mcpt: pd.DataFrame,
    yearly: pd.DataFrame,
) -> list[Path]:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return []

    assets = REPORT_ROOT / "assets"
    assets.mkdir(
        parents=True,
        exist_ok=True,
    )
    outputs: list[Path] = []

    for result in (nq, mnq):
        frame = result.equity_curve.copy()
        frame["session_date"] = (
            pd.to_datetime(
                frame["session_date"]
            )
        )

        figure, axis = plt.subplots(
            figsize=(10, 4.5)
        )
        axis.plot(
            frame["session_date"],
            frame[
                "cumulative_net_pnl_usd"
            ],
        )
        axis.axhline(
            0.0,
            linewidth=0.8,
        )
        axis.set_title(
            f"{result.symbol} cumulative net P&L"
        )
        axis.set_xlabel("Session")
        axis.set_ylabel("USD per contract")
        figure.tight_layout()

        path = assets / (
            f"{result.symbol.lower()}_equity.png"
        )
        figure.savefig(
            path,
            dpi=140,
        )
        plt.close(figure)
        outputs.append(path)

    figure, axis = plt.subplots(
        figsize=(10, 4.5)
    )
    finite = mcpt[
        "trade_profit_factor"
    ].replace(
        [np.inf, -np.inf],
        np.nan,
    ).dropna()

    if not finite.empty:
        axis.hist(
            finite,
            bins=min(
                12,
                max(
                    5,
                    int(
                        np.sqrt(
                            len(finite)
                        )
                    ),
                ),
            ),
        )

    real_pf = float(
        mcpt[
            "real_trade_profit_factor"
        ].iloc[0]
    )
    if np.isfinite(real_pf):
        axis.axvline(
            real_pf,
            linewidth=2.0,
            label="Real NQ PF",
        )
        axis.legend()

    axis.set_title(
        "NQ MCPT permutation Profit Factors"
    )
    axis.set_xlabel(
        "Trade Profit Factor"
    )
    axis.set_ylabel(
        "Permutations"
    )
    figure.tight_layout()
    path = assets / "nq_mcpt.png"
    figure.savefig(
        path,
        dpi=140,
    )
    plt.close(figure)
    outputs.append(path)

    pivot = yearly.pivot(
        index="year",
        columns="symbol",
        values="net_profit_usd",
    ).sort_index()

    figure, axis = plt.subplots(
        figsize=(10, 4.5)
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
        "Calendar-year net P&L"
    )
    axis.set_xlabel("Year")
    axis.set_ylabel("USD per contract")
    figure.tight_layout()
    path = assets / "yearly_pnl.png"
    figure.savefig(
        path,
        dpi=140,
    )
    plt.close(figure)
    outputs.append(path)

    return outputs


def _table_html(
    frame: pd.DataFrame,
) -> str:
    return frame.to_html(
        index=False,
        border=0,
        classes="data-table",
        float_format=lambda value: (
            f"{value:,.4f}"
        ),
        na_rep="N/A",
        escape=True,
    )


def write_report(
    *,
    decision: dict[str, Any],
    nq: FuturesOrbResult,
    mnq: FuturesOrbResult,
    mcpt: pd.DataFrame,
    summary: pd.DataFrame,
    cost_sensitivity: pd.DataFrame,
    yearly: pd.DataFrame,
) -> Path:
    REPORT_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )
    charts = _write_charts(
        nq=nq,
        mnq=mnq,
        mcpt=mcpt,
        yearly=yearly,
    )

    gates = pd.DataFrame(
        [
            {
                "Gate": name,
                "Actual": gate["actual"],
                "Rule": (
                    f"{gate['operator']} "
                    f"{gate['threshold']}"
                ),
                "Passed": (
                    "PASS"
                    if gate["passed"]
                    else "FAIL"
                ),
            }
            for name, gate in decision[
                "evaluation"
            ]["gates"].items()
        ]
    )

    chart_html = "\n".join(
        (
            '<section class="card chart-card">'
            f'<img src="assets/{html.escape(path.name)}" '
            f'alt="{html.escape(path.stem)}">'
            "</section>"
        )
        for path in charts
    )

    decision_name = html.escape(
        str(
            decision["evaluation"][
                "decision"
            ]
        )
    )
    failed = decision[
        "evaluation"
    ]["failed_gates"]
    failed_text = (
        ", ".join(
            html.escape(str(item))
            for item in failed
        )
        if failed
        else "None"
    )

    document = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>EXP-005 Quick Transfer</title>
<style>
:root {{
  color-scheme: light dark;
  --bg: #101216;
  --panel: #181c22;
  --text: #eef1f5;
  --muted: #aeb7c4;
  --border: #303744;
  --pass: #44c27d;
  --fail: #f06c75;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  font-family: Inter, Segoe UI, Arial, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.5;
}}
main {{
  width: min(1180px, calc(100% - 32px));
  margin: 30px auto 60px;
}}
header, .card {{
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 22px;
  margin-bottom: 18px;
  overflow-x: auto;
}}
h1, h2 {{ margin-top: 0; }}
.muted {{ color: var(--muted); }}
.decision {{
  font-size: clamp(1.6rem, 5vw, 3rem);
  font-weight: 750;
  margin: 10px 0;
}}
.data-table {{
  width: 100%;
  border-collapse: collapse;
  min-width: 680px;
}}
.data-table th, .data-table td {{
  padding: 9px 11px;
  border-bottom: 1px solid var(--border);
  text-align: right;
  white-space: nowrap;
}}
.data-table th:first-child,
.data-table td:first-child {{
  text-align: left;
}}
.chart-card img {{
  width: 100%;
  max-width: 1050px;
  display: block;
  margin: auto;
  background: white;
  border-radius: 8px;
}}
.grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(290px, 1fr));
  gap: 18px;
}}
.grid .card {{ margin-bottom: 0; }}
code {{
  overflow-wrap: anywhere;
}}
</style>
</head>
<body>
<main>
<header>
  <div class="muted">EXP-005 · NQ/MNQ 5-minute ORB locked transfer</div>
  <div class="decision">{decision_name}</div>
  <div>Failed gates: {failed_text}</div>
  <p class="muted">
    Fixed 15-minute opening range, both directions, one trade per
    session, next-open execution, opening-range stop, 15:55 ET flat.
    NQ is the primary evidence market. MNQ is a cost implementation
    check, not independent evidence.
  </p>
</header>

<section class="card">
  <h2>Decision gates</h2>
  {_table_html(gates)}
</section>

<section class="card">
  <h2>Decision-model results</h2>
  {_table_html(summary)}
</section>

<div class="grid">
  <section class="card">
    <h2>MCPT</h2>
    <p>NQ permutations: {len(mcpt)}</p>
    <p>p-value: {_format_number(decision["mcpt"]["p_value"], digits=6)}</p>
    <p>Permutations at least real: {decision["mcpt"]["permutations_at_least_real"]}</p>
  </section>
  <section class="card">
    <h2>Data controls</h2>
    <p>Included sessions: {decision["data"]["included_sessions"]}</p>
    <p>Invalid sessions included: {decision["data"]["included_invalid_sessions"]}</p>
    <p>Roll/mismatch sessions included: {decision["data"]["included_roll_switch_sessions"]}</p>
    <p>Confirmation accessed: {decision["confirmation_period_accessed"]}</p>
  </section>
</div>

<section class="card">
  <h2>Cost sensitivity</h2>
  {_table_html(cost_sensitivity)}
</section>

<section class="card">
  <h2>Calendar-year results</h2>
  {_table_html(yearly)}
</section>

{chart_html}

<section class="card">
  <h2>Reproducibility</h2>
  <p>Git commit: <code>{html.escape(str(decision["git"]["commit"]))}</code></p>
  <p>Import audit: <code>{html.escape(str(AUDIT_FILE.resolve()))}</code></p>
  <p>MCPT signature: <code>{html.escape(str(decision["mcpt"]["run_info"]["signature"]))}</code></p>
  <p class="muted">
    This report contains only the locked 2019–2022 quick-transfer
    period. The 2023–2025 confirmation period was not read or
    calculated.
  </p>
</section>
</main>
</body>
</html>
"""

    path = REPORT_ROOT / "report.html"
    temporary = path.with_suffix(
        ".html.tmp"
    )
    temporary.write_text(
        document,
        encoding="utf-8",
    )
    temporary.replace(path)
    return path


def preflight() -> tuple[
    dict[str, Any],
    dict[str, Any],
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    validate_exp005_preregistration()
    validate_exp005_recheck_resolution()
    validate_exp005_missing_session_resolution()
    validate_exp005_quick_transfer_implementation()

    lifecycle = get_experiment_lifecycle(
        "EXP-005"
    )

    if lifecycle.stage != "PRE_REGISTERED":
        raise RuntimeError(
            "EXP-005 quick transfer may run only "
            "while lifecycle stage is PRE_REGISTERED."
        )

    prereg = (
        get_exp005_preregistration()
    )

    if prereg["results_viewed"] != "NONE":
        raise RuntimeError(
            "EXP-005 results were already disclosed."
        )

    if (
        prereg["research_split"][
            "confirmation_access"
        ]
        != "LOCKED_UNTIL_QUICK_PASS"
    ):
        raise RuntimeError(
            "EXP-005 confirmation lock changed."
        )

    if DECISION_FILE.exists():
        raise RuntimeError(
            "The EXP-005 quick-transfer decision "
            "already exists. This protected run "
            "cannot be repeated or overwritten."
        )

    git = git_state()

    if not git["working_tree_clean"]:
        raise RuntimeError(
            "Commit and push the EXP-005 quick-transfer "
            "implementation before running research. "
            "Git must be clean."
        )

    (
        audit,
        nq_1m,
        mnq_1m,
        nq_5m,
        mnq_5m,
    ) = load_frozen_data()

    return (
        git,
        audit,
        nq_1m,
        mnq_1m,
        nq_5m,
        mnq_5m,
    )


def main() -> None:
    arguments = parse_arguments()

    (
        git,
        audit,
        nq_1m,
        mnq_1m,
        nq_5m,
        mnq_5m,
    ) = preflight()

    print()
    print(
        "========== EXP-005 QUICK TRANSFER =========="
    )
    print(
        "Rules:        locked 15-minute ORB"
    )
    print(
        "Optimization: DISABLED"
    )
    print(
        "Quick period: 2019-05-06 through 2022-12-30"
    )
    print(
        "Confirmation: BLOCKED"
    )
    print(
        f"Sessions:     {audit['included_sessions']:,}"
    )
    print(
        f"Git commit:   {git['short_commit']}"
    )
    print()

    if arguments.preflight:
        print(
            "Preflight passed. No strategy results "
            "were calculated."
        )
        return

    nq = run_futures_orb(
        nq_5m,
        symbol="NQ",
        slippage_ticks_per_side=1.0,
    )
    mnq = run_futures_orb(
        mnq_5m,
        symbol="MNQ",
        slippage_ticks_per_side=1.0,
    )

    mcpt, p_value, mcpt_info = (
        run_exp005_mcpt(
            nq_1m,
            real_trade_profit_factor=float(
                nq.summary[
                    "trade_profit_factor"
                ]
            ),
            permutations=25,
            base_seed=45,
            requested_workers=(
                arguments.workers
            ),
            checkpoint_file=(
                MCPT_CHECKPOINT
            ),
            one_minute_fingerprint=(
                audit["fingerprints"][
                    "NQ_1m"
                ]
            ),
        )
    )

    evaluation = (
        evaluate_exp005_quick_transfer(
            nq_trade_profit_factor=float(
                nq.summary[
                    "trade_profit_factor"
                ]
            ),
            mnq_trade_profit_factor=float(
                mnq.summary[
                    "trade_profit_factor"
                ]
            ),
            nq_net_profit_usd=float(
                nq.summary[
                    "net_profit_usd"
                ]
            ),
            mnq_net_profit_usd=float(
                mnq.summary[
                    "net_profit_usd"
                ]
            ),
            nq_mcpt_p_value=float(
                p_value
            ),
            nq_completed_trades=int(
                nq.summary[
                    "completed_trades"
                ]
            ),
            nq_long_trades=int(
                nq.summary[
                    "long_trades"
                ]
            ),
            nq_short_trades=int(
                nq.summary[
                    "short_trades"
                ]
            ),
            included_invalid_sessions=int(
                audit[
                    "included_invalid_sessions"
                ]
            ),
            included_roll_switch_sessions=int(
                audit[
                    "included_front_month_mismatch_sessions"
                ]
            ),
        )
    )

    cost_sensitivity = pd.concat(
        [
            run_cost_sensitivity(
                nq_5m,
                symbol="NQ",
            ),
            run_cost_sensitivity(
                mnq_5m,
                symbol="MNQ",
            ),
        ],
        ignore_index=True,
    )
    summary = _summary_frame(
        nq,
        mnq,
    )
    yearly = _yearly_frame(
        nq,
        mnq,
    )

    permutations_at_least_real = int(
        mcpt[
            "permutation_ge_real"
        ].sum()
    )

    decision = {
        "schema_version": 1,
        "experiment_id": "EXP-005",
        "stage": "QUICK_TRANSFER",
        "calculated_at_utc": (
            datetime.now(
                timezone.utc
            ).isoformat(
                timespec="seconds"
            )
        ),
        "git": git,
        "data": {
            "import_audit": str(
                AUDIT_FILE.resolve()
            ),
            "included_sessions": int(
                audit["included_sessions"]
            ),
            "included_invalid_sessions": int(
                audit[
                    "included_invalid_sessions"
                ]
            ),
            "included_roll_switch_sessions": int(
                audit[
                    "included_front_month_mismatch_sessions"
                ]
            ),
            "potential_mismatch_sessions_excluded": int(
                audit[
                    "potential_front_month_mismatch_sessions_excluded"
                ]
            ),
            "provider_unavailable_sessions_excluded": int(
                audit[
                    "locked_provider_unavailable_sessions_excluded"
                ]
            ),
            "fingerprints": audit[
                "fingerprints"
            ],
        },
        "fixed_rules": {
            "opening_range_minutes": 15,
            "direction_mode": "both",
            "parameter_combinations": 1,
            "optimization": False,
        },
        "results": {
            "NQ": nq.summary,
            "MNQ": mnq.summary,
        },
        "mcpt": {
            "market": "NQ",
            "permutations": 25,
            "p_value": float(
                p_value
            ),
            "permutations_at_least_real": (
                permutations_at_least_real
            ),
            "run_info": (
                mcpt_info.to_dict()
            ),
        },
        "evaluation": (
            evaluation.to_dict()
        ),
        "confirmation_period_accessed": False,
        "confirmation_results_calculated": False,
        "source_experiment_reopened": False,
        "automatic_lifecycle_source_edit": False,
    }

    RESULT_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    _atomic_csv(
        summary,
        RESULT_ROOT
        / "decision_model_summary.csv",
    )
    _atomic_csv(
        nq.trades,
        RESULT_ROOT
        / "nq_trades.csv",
    )
    _atomic_csv(
        mnq.trades,
        RESULT_ROOT
        / "mnq_trades.csv",
    )
    _atomic_csv(
        nq.equity_curve,
        RESULT_ROOT
        / "nq_equity_curve.csv",
    )
    _atomic_csv(
        mnq.equity_curve,
        RESULT_ROOT
        / "mnq_equity_curve.csv",
    )
    _atomic_csv(
        mcpt,
        RESULT_ROOT
        / "nq_mcpt_25.csv",
    )
    _atomic_csv(
        cost_sensitivity,
        RESULT_ROOT
        / "cost_sensitivity.csv",
    )
    _atomic_csv(
        yearly,
        RESULT_ROOT
        / "yearly_results.csv",
    )

    report = write_report(
        decision=decision,
        nq=nq,
        mnq=mnq,
        mcpt=mcpt,
        summary=summary,
        cost_sensitivity=(
            cost_sensitivity
        ),
        yearly=yearly,
    )

    # The decision file is the final immutable marker.
    _atomic_json(
        decision,
        DECISION_FILE,
    )

    print()
    print(
        "EXP-005 quick transfer completed."
    )
    print(
        "Decision: "
        f"{evaluation.decision}"
    )
    print(
        "NQ PF: "
        f"{nq.summary['trade_profit_factor']:.6f}"
    )
    print(
        "NQ net profit: "
        f"${nq.summary['net_profit_usd']:,.2f}"
    )
    print(
        "MNQ PF: "
        f"{mnq.summary['trade_profit_factor']:.6f}"
    )
    print(
        "MNQ net profit: "
        f"${mnq.summary['net_profit_usd']:,.2f}"
    )
    print(
        "NQ completed trades: "
        f"{nq.summary['completed_trades']}"
    )
    print(
        "NQ long / short: "
        f"{nq.summary['long_trades']} / "
        f"{nq.summary['short_trades']}"
    )
    print(
        "NQ MCPT p-value: "
        f"{p_value:.6f}"
    )
    print(
        "Failed gates: "
        + (
            ", ".join(
                evaluation.failed_gates
            )
            if evaluation.failed_gates
            else "None"
        )
    )
    print(
        "Confirmation period remained locked."
    )
    print(
        f"Decision: {DECISION_FILE.resolve()}"
    )
    print(
        f"Report:   {report.resolve()}"
    )
    print(
        "============================================"
    )


if __name__ == "__main__":
    main()
