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

from exp005_confirmation_alignment_resolution import (
    validate_exp005_confirmation_alignment_resolution,
)
from exp005_confirmation_missing_session_resolution import (
    validate_exp005_confirmation_missing_session_resolution,
)
from exp005_confirmation_recheck_resolution import (
    validate_exp005_confirmation_recheck_resolution,
)
from exp005_full_session_mcpt import (
    FULL_PERMUTATIONS,
    run_exp005_full_mcpt,
)
from exp005_full_validation import (
    evaluate_exp005_full_validation,
)
from exp005_full_validation_implementation import (
    validate_exp005_full_validation_implementation,
)
from exp005_futures_orb import (
    FuturesOrbResult,
    run_cost_sensitivity,
    run_futures_orb,
)
from exp005_preregistration import (
    get_exp005_preregistration,
    validate_exp005_preregistration,
)
from exp005_quick_transfer_result import (
    verify_local_quick_transfer_decision,
)
from experiment_lifecycle import (
    get_experiment_lifecycle,
)
from import_exp005_quantower_confirmation_data import (
    AUDIT_FILE,
    OUTPUT_FILES,
    verify_existing_import,
)


PROJECT_DIR = Path(__file__).resolve().parent
RESULT_ROOT = (
    PROJECT_DIR
    / "results"
    / "EXP-005"
    / "full_validation"
)
REPORT_ROOT = (
    PROJECT_DIR
    / "reports"
    / "EXP-005-full-validation"
)
DECISION_FILE = (
    RESULT_ROOT
    / "full_validation_decision.json"
)
MCPT_CHECKPOINT = (
    RESULT_ROOT
    / "mcpt_checkpoint_1000.json"
)
EXPECTED_IMPORT_COMMIT = (
    "53a740aedb63e2a7508e3e010f5370be49cf816a"
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the protected EXP-005 2023–2025 "
            "NQ/MNQ full validation."
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
            "Verify the frozen confirmation data and "
            "workflow without calculating strategy results."
        ),
    )
    return parser.parse_args()


def git_state() -> dict[str, Any]:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=PROJECT_DIR,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    short_commit = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=PROJECT_DIR,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=PROJECT_DIR,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    return {
        "commit": commit,
        "short_commit": short_commit,
        "working_tree_clean": not bool(status),
    }


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]

    if isinstance(value, np.integer):
        return int(value)

    if isinstance(value, np.floating):
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

    if isinstance(value, pd.Timestamp):
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


def load_frozen_confirmation_data(
) -> tuple[
    dict[str, Any],
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    audit = verify_existing_import()

    required = {
        "included_sessions": 733,
        "included_nq_one_minute_rows": 285_870,
        "included_mnq_one_minute_rows": 285_870,
        "included_nq_five_minute_rows": 57_174,
        "included_mnq_five_minute_rows": 57_174,
        "provider_unavailable_sessions_excluded": 2,
        "provider_complete_sessions_restored": 1,
        "potential_front_month_mismatch_sessions_excluded": 9,
        "included_invalid_sessions": 0,
        "included_front_month_mismatch_sessions": 0,
        "strategy_results_calculated": False,
        "full_validation_results_calculated": False,
        "quick_transfer_rerun": False,
    }

    for field, expected in required.items():
        actual = audit.get(field)
        if actual != expected:
            raise RuntimeError(
                f"Confirmation audit field {field} changed: "
                f"expected {expected!r}, got {actual!r}."
            )

    import_git = audit.get("git", {})
    if import_git.get("commit") != EXPECTED_IMPORT_COMMIT:
        raise RuntimeError(
            "The confirmation data was imported under a "
            "different implementation commit."
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
            "Frozen confirmation NQ/MNQ one-minute "
            "timestamps are not aligned."
        )

    if not frames["NQ_5m"].index.equals(
        frames["MNQ_5m"].index
    ):
        raise RuntimeError(
            "Frozen confirmation NQ/MNQ five-minute "
            "timestamps are not aligned."
        )

    for name, frame in frames.items():
        sessions = pd.to_datetime(
            frame["session_date"]
        )
        if (
            sessions.min()
            < pd.Timestamp("2023-01-03")
            or sessions.max()
            > pd.Timestamp("2025-12-31")
            or sessions.nunique() != 733
        ):
            raise RuntimeError(
                f"{name} confirmation period or session "
                "count changed."
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
                    result.contract.tick_value_usd
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
        local = result.yearly_results.copy()
        local.insert(0, "symbol", result.symbol)
        frames.append(local)

    return pd.concat(
        frames,
        ignore_index=True,
    )


def profitable_nq_calendar_years(
    nq: FuturesOrbResult,
) -> int:
    yearly = nq.yearly_results
    if yearly.empty:
        return 0

    return int(
        yearly["net_profit_usd"]
        .astype(float)
        .gt(0.0)
        .sum()
    )


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
        frame["session_date"] = pd.to_datetime(
            frame["session_date"]
        )

        figure, axis = plt.subplots(
            figsize=(10, 4.5)
        )
        axis.plot(
            frame["session_date"],
            frame["cumulative_net_pnl_usd"],
        )
        axis.axhline(0.0, linewidth=0.8)
        axis.set_title(
            f"{result.symbol} confirmation cumulative net P&L"
        )
        axis.set_xlabel("Session")
        axis.set_ylabel("USD per contract")
        figure.tight_layout()
        path = assets / (
            f"{result.symbol.lower()}_equity.png"
        )
        figure.savefig(path, dpi=140)
        plt.close(figure)
        outputs.append(path)

    finite = mcpt[
        "trade_profit_factor"
    ].replace(
        [np.inf, -np.inf],
        np.nan,
    ).dropna()

    figure, axis = plt.subplots(
        figsize=(10, 4.5)
    )
    if not finite.empty:
        axis.hist(
            finite,
            bins=min(
                40,
                max(10, int(np.sqrt(len(finite)))),
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
        "NQ full MCPT permutation Profit Factors"
    )
    axis.set_xlabel("Trade Profit Factor")
    axis.set_ylabel("Permutations")
    figure.tight_layout()
    path = assets / "nq_mcpt_1000.png"
    figure.savefig(path, dpi=140)
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
    pivot.plot(kind="bar", ax=axis)
    axis.axhline(0.0, linewidth=0.8)
    axis.set_title(
        "Confirmation calendar-year net P&L"
    )
    axis.set_xlabel("Year")
    axis.set_ylabel("USD per contract")
    figure.tight_layout()
    path = assets / "yearly_pnl.png"
    figure.savefig(path, dpi=140)
    plt.close(figure)
    outputs.append(path)

    return outputs


def _table_html(frame: pd.DataFrame) -> str:
    return frame.to_html(
        index=False,
        border=0,
        classes="data-table",
        float_format=lambda value: f"{value:,.4f}",
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
            decision["evaluation"]["decision"]
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
<title>EXP-005 Full Validation</title>
<style>
:root {{ color-scheme: light dark; --bg:#101216; --panel:#181c22; --text:#eef1f5; --muted:#aeb7c4; --border:#303744; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:Inter,Segoe UI,Arial,sans-serif; background:var(--bg); color:var(--text); line-height:1.5; }}
main {{ width:min(1180px,calc(100% - 32px)); margin:30px auto 60px; }}
header,.card {{ background:var(--panel); border:1px solid var(--border); border-radius:14px; padding:22px; margin-bottom:18px; overflow-x:auto; }}
h1,h2 {{ margin-top:0; }}
.muted {{ color:var(--muted); }}
.decision {{ font-size:clamp(1.6rem,5vw,3rem); font-weight:750; margin:10px 0; }}
.data-table {{ width:100%; border-collapse:collapse; min-width:680px; }}
.data-table th,.data-table td {{ padding:9px 11px; border-bottom:1px solid var(--border); text-align:right; }}
.data-table th:first-child,.data-table td:first-child {{ text-align:left; }}
.chart-card img {{ display:block; width:100%; height:auto; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:18px; }}
.grid .card {{ margin:0; }}
</style>
</head>
<body>
<main>
<header>
<p class="muted">EXP-005 · NQ/MNQ 5-Minute ORB · 2023–2025 confirmation</p>
<h1>Protected Full Validation</h1>
<div class="decision">{decision_name}</div>
<p>Failed gates: {failed_text}</p>
<p class="muted">One fixed rule set, no optimization, 1,000 NQ session-aware permutations.</p>
</header>
<section class="card"><h2>Locked gates</h2>{_table_html(gates)}</section>
<section class="card"><h2>Decision-model summary</h2>{_table_html(summary)}</section>
<section class="card"><h2>Calendar-year results</h2>{_table_html(yearly)}</section>
<section class="card"><h2>Cost sensitivity</h2>{_table_html(cost_sensitivity)}</section>
<div class="grid">{chart_html}</div>
<section class="card">
<h2>Interpretation boundary</h2>
<p>NQ is the primary transfer evidence. MNQ is a contract-size and cost implementation check, not independent market evidence. A pass advances only to operational review; it does not authorize parameter changes or paper trading.</p>
</section>
</main>
</body>
</html>"""

    path = REPORT_ROOT / "report.html"
    temporary = path.with_suffix(".html.tmp")
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
    verify_local_quick_transfer_decision()
    validate_exp005_confirmation_recheck_resolution()
    validate_exp005_confirmation_missing_session_resolution()
    validate_exp005_confirmation_alignment_resolution()
    validate_exp005_full_validation_implementation()

    lifecycle = get_experiment_lifecycle("EXP-005")
    if lifecycle.stage != "FULL_VALIDATION":
        raise RuntimeError(
            "EXP-005 full validation may run only while "
            "the lifecycle stage is FULL_VALIDATION."
        )

    prereg = get_exp005_preregistration()
    if (
        prereg["optimization"]["enabled"]
        is not False
    ):
        raise RuntimeError(
            "EXP-005 optimization must remain disabled."
        )

    if DECISION_FILE.exists():
        raise RuntimeError(
            "The EXP-005 full-validation decision already "
            "exists. This protected result cannot be "
            "repeated or overwritten."
        )

    git = git_state()
    if not git["working_tree_clean"]:
        raise RuntimeError(
            "Commit and push the full-validation "
            "implementation before running research. "
            "Git must be clean."
        )

    (
        audit,
        nq_1m,
        mnq_1m,
        nq_5m,
        mnq_5m,
    ) = load_frozen_confirmation_data()

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
        "========== EXP-005 FULL VALIDATION =========="
    )
    print("Rules:        locked 15-minute ORB")
    print("Optimization: DISABLED")
    print("Period:       2023-01-03 through 2025-12-31")
    print(
        f"Sessions:     {audit['included_sessions']:,}"
    )
    print("NQ MCPT:      1,000 permutations")
    print(f"Git commit:   {git['short_commit']}")
    print()

    if arguments.preflight:
        print(
            "Preflight passed. No full-validation "
            "strategy results were calculated."
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
        run_exp005_full_mcpt(
            nq_1m,
            real_trade_profit_factor=float(
                nq.summary["trade_profit_factor"]
            ),
            permutations=FULL_PERMUTATIONS,
            base_seed=45,
            requested_workers=arguments.workers,
            checkpoint_file=MCPT_CHECKPOINT,
            one_minute_fingerprint=(
                audit["fingerprints"]["NQ_1m"]
            ),
        )
    )

    profitable_years = (
        profitable_nq_calendar_years(nq)
    )
    evaluation = evaluate_exp005_full_validation(
        nq_trade_profit_factor=float(
            nq.summary["trade_profit_factor"]
        ),
        mnq_trade_profit_factor=float(
            mnq.summary["trade_profit_factor"]
        ),
        nq_net_profit_usd=float(
            nq.summary["net_profit_usd"]
        ),
        mnq_net_profit_usd=float(
            mnq.summary["net_profit_usd"]
        ),
        nq_mcpt_p_value=float(p_value),
        nq_completed_trades=int(
            nq.summary["completed_trades"]
        ),
        profitable_nq_calendar_years=(
            profitable_years
        ),
        included_invalid_sessions=int(
            audit["included_invalid_sessions"]
        ),
        included_roll_switch_sessions=int(
            audit[
                "included_front_month_mismatch_sessions"
            ]
        ),
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
    summary = _summary_frame(nq, mnq)
    yearly = _yearly_frame(nq, mnq)
    permutations_at_least_real = int(
        mcpt["permutation_ge_real"].sum()
    )

    decision = {
        "schema_version": 1,
        "experiment_id": "EXP-005",
        "stage": "FULL_VALIDATION",
        "calculated_at_utc": (
            datetime.now(timezone.utc).isoformat(
                timespec="seconds"
            )
        ),
        "git": git,
        "data": {
            "confirmation_import_audit": str(
                AUDIT_FILE.resolve()
            ),
            "confirmation_import_commit": (
                audit["git"]["commit"]
            ),
            "included_sessions": int(
                audit["included_sessions"]
            ),
            "included_invalid_sessions": int(
                audit["included_invalid_sessions"]
            ),
            "included_roll_switch_sessions": int(
                audit[
                    "included_front_month_mismatch_sessions"
                ]
            ),
            "provider_unavailable_sessions_excluded": int(
                audit[
                    "provider_unavailable_sessions_excluded"
                ]
            ),
            "provider_complete_sessions_restored": int(
                audit[
                    "provider_complete_sessions_restored"
                ]
            ),
            "potential_front_month_mismatch_sessions_excluded": int(
                audit[
                    "potential_front_month_mismatch_sessions_excluded"
                ]
            ),
            "fingerprints": audit["fingerprints"],
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
            "profitable_nq_calendar_years": (
                profitable_years
            ),
        },
        "mcpt": {
            "market": "NQ",
            "permutations": FULL_PERMUTATIONS,
            "p_value": float(p_value),
            "permutations_at_least_real": (
                permutations_at_least_real
            ),
            "run_info": mcpt_info.to_dict(),
        },
        "evaluation": evaluation.to_dict(),
        "confirmation_period_accessed": True,
        "confirmation_results_calculated": True,
        "quick_transfer_rerun": False,
        "source_experiment_reopened": False,
        "automatic_lifecycle_source_edit": False,
        "next_stage_if_passed": "REVIEW",
    }

    RESULT_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )
    _atomic_csv(
        summary,
        RESULT_ROOT / "decision_model_summary.csv",
    )
    _atomic_csv(
        nq.trades,
        RESULT_ROOT / "nq_trades.csv",
    )
    _atomic_csv(
        mnq.trades,
        RESULT_ROOT / "mnq_trades.csv",
    )
    _atomic_csv(
        nq.equity_curve,
        RESULT_ROOT / "nq_equity_curve.csv",
    )
    _atomic_csv(
        mnq.equity_curve,
        RESULT_ROOT / "mnq_equity_curve.csv",
    )
    _atomic_csv(
        mcpt,
        RESULT_ROOT / "nq_mcpt_1000.csv",
    )
    _atomic_csv(
        cost_sensitivity,
        RESULT_ROOT / "cost_sensitivity.csv",
    )
    _atomic_csv(
        yearly,
        RESULT_ROOT / "yearly_results.csv",
    )

    report = write_report(
        decision=decision,
        nq=nq,
        mnq=mnq,
        mcpt=mcpt,
        summary=summary,
        cost_sensitivity=cost_sensitivity,
        yearly=yearly,
    )

    # The decision file is written last and is the immutable marker.
    _atomic_json(decision, DECISION_FILE)

    print()
    print("EXP-005 full validation completed.")
    print(f"Decision: {evaluation.decision}")
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
        "Profitable NQ calendar years: "
        f"{profitable_years}"
    )
    print(
        "NQ MCPT p-value: "
        f"{p_value:.6f}"
    )
    print(
        "Failed gates: "
        + (
            ", ".join(evaluation.failed_gates)
            if evaluation.failed_gates
            else "None"
        )
    )
    print("Quick transfer was not rerun.")
    print(f"Decision: {DECISION_FILE.resolve()}")
    print(f"Report:   {report.resolve()}")
    print(
        "=============================================="
    )


if __name__ == "__main__":
    main()
