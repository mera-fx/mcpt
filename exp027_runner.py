from __future__ import annotations

import argparse
import csv
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
import hashlib
from html import escape
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd

from exp026_core import (
    SOURCE_COLUMNS,
    TRADE_COLUMNS,
    DECISION_COLUMNS,
    candidate_metrics,
    canonical_dataframe_sha256,
    canonical_object_sha256,
    cost_sensitivity,
    monthly_results,
    replay_candidates,
)
from exp026_runner import (
    REPRESENTATION_FILES,
    inspect_parquet_metadata,
    sha256_file,
    verify_frozen_series_bytes,
)
from exp027_core import (
    candidate_registry_exp027,
    candidate_series_metrics,
    canonical_trade_ledger,
    cohort_for,
    comparison_timeseries,
    dense_session_equity,
    drawdown_episodes,
    exp027_reported_ids,
    historical_context,
    primary_cohort_ids,
    representation_sensitivity,
    trade_distribution,
    validate_exp027_population,
    validate_result_frames,
)
from exp027_preregistration import (
    EXPECTED_EXP027_PREREGISTRATION_SHA256,
    get_exp027_preregistration,
    validate_exp027_preregistration,
)


PROJECT_DIR = Path(__file__).resolve().parent
LOCKED_PREREGISTRATION_COMMIT = (
    "21c182e119cde651e6c4fe22b1e4e8d6b99def5b"
)
LOCKED_EXP026_IMPLEMENTATION_COMMIT = (
    "13ee0683dfcbbb5d763f7254f3b245ecc8e6d9cd"
)

PREREGISTRATION_PATHS = (
    "build_research_dashboard_v2.py",
    "dashboard_experiment_profiles.py",
    "experiment_lifecycle.py",
    "exp027_preregistration.py",
    "research/EXP-027_preregistration.md",
    "tests/test_dashboard_experiment_profiles.py",
    "tests/test_dashboard_strategy_groups.py",
    "tests/test_experiment_lifecycle.py",
    "tests/test_exp027_preregistration.py",
)

IMPLEMENTATION_PATHS = (
    "exp027_core.py",
    "exp027_runner.py",
    "exp027_implementation_preflight.py",
    "research/EXP-027_implementation_report.md",
    "tests/test_exp027_core.py",
    "tests/test_exp027_implementation.py",
)

AUTHORIZATION_MODULE = "exp027_execution_authorization"
AUTHORIZATION_PATHS = (
    "exp027_execution_authorization.py",
    "research/EXP-027_execution_authorization.md",
    "tests/test_exp027_execution_authorization.py",
)

OUTPUT_DIR = (
    PROJECT_DIR
    / "results"
    / "EXP-027"
    / "protected_2026_measurement"
)
PARTIAL_DIR = OUTPUT_DIR.with_name(
    OUTPUT_DIR.name + ".partial"
)
PERIOD_START = "2026-01-01"
PERIOD_END = "2026-07-23"
MINIMUM_FREE_BYTES = 2_000_000_000


def run_git(
    *args: str,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=PROJECT_DIR,
        text=True,
        capture_output=True,
        check=check,
    )


def changed_paths(
    base: str,
    head: str,
) -> set[str]:
    return {
        line.strip().replace("\\", "/")
        for line in run_git(
            "diff",
            "--name-only",
            base,
            head,
        ).stdout.splitlines()
        if line.strip()
    }


def latest_commit(relative_path: str) -> str:
    value = run_git(
        "log",
        "-1",
        "--format=%H",
        "--",
        relative_path,
    ).stdout.strip()
    if not value:
        raise RuntimeError(
            f"No commit found for EXP-027 path: {relative_path}."
        )
    return value


def atomic_write_text(
    path: Path,
    value: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        raise RuntimeError(
            f"Temporary output already exists: {temporary}"
        )
    temporary.write_text(
        value,
        encoding="utf-8",
        newline="\n",
    )
    os.replace(temporary, path)


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _json_safe(current)
            for key, current in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_json_safe(current) for current in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer, int)) and not isinstance(
        value,
        bool,
    ):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if np.isfinite(number) else None
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()
    return value


def atomic_write_json(
    path: Path,
    value: Mapping[str, Any],
) -> None:
    atomic_write_text(
        path,
        json.dumps(
            _json_safe(value),
            indent=2,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
            default=str,
        )
        + "\n",
    )


def write_csv(
    path: Path,
    frame: pd.DataFrame,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        raise RuntimeError(
            f"Temporary CSV already exists: {temporary}"
        )
    frame.to_csv(
        temporary,
        index=False,
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\n",
    )
    os.replace(temporary, path)


def load_authorization() -> dict[str, Any]:
    module_path = PROJECT_DIR / (
        AUTHORIZATION_MODULE + ".py"
    )
    if not module_path.is_file():
        raise RuntimeError(
            "EXP-027 execution is not authorized. "
            "The separate authorization module is absent."
        )
    module = importlib.import_module(
        AUTHORIZATION_MODULE
    )
    validator = getattr(
        module,
        "validate_exp027_execution_authorization",
        None,
    )
    getter = getattr(
        module,
        "get_exp027_execution_authorization",
        None,
    )
    if validator is None or getter is None:
        raise RuntimeError(
            "EXP-027 authorization interface is incomplete."
        )
    validator()
    record = getter()
    if (
        record.get("experiment_id") != "EXP-027"
        or record.get("execution_authorized") is not True
        or record.get("one_time_run") is not True
        or record.get("maximum_runs") != 1
        or record.get("protected_2026_access_authorized")
        is not True
        or record.get("preregistration_sha256")
        != EXPECTED_EXP027_PREREGISTRATION_SHA256
        or record.get("new_databento_download_authorized")
        is not False
        or record.get("network_access_authorized")
        is not False
        or record.get("paper_trading_authorized")
        is not False
        or record.get("live_trading_authorized")
        is not False
    ):
        raise RuntimeError(
            "EXP-027 authorization boundary changed."
        )
    implementation_commit = record.get(
        "locked_implementation_commit"
    )
    if (
        not isinstance(implementation_commit, str)
        or len(implementation_commit) != 40
    ):
        raise RuntimeError(
            "EXP-027 locked implementation commit is invalid."
        )
    return record


def verify_repository_for_execution(
    authorization: Mapping[str, Any],
) -> dict[str, str]:
    if os.environ.get(
        "DATABENTO_API_KEY",
        "",
    ).strip():
        raise RuntimeError(
            "DATABENTO_API_KEY must be unset for EXP-027."
        )
    if run_git(
        "status",
        "--porcelain",
    ).stdout.strip():
        raise RuntimeError(
            "Repository must be clean for EXP-027 execution."
        )
    branch = run_git(
        "branch",
        "--show-current",
    ).stdout.strip()
    if branch != "main":
        raise RuntimeError(
            f"EXP-027 execution requires main, found {branch!r}."
        )
    head = run_git(
        "rev-parse",
        "HEAD",
    ).stdout.strip()
    origin = run_git(
        "rev-parse",
        "origin/main",
    ).stdout.strip()
    if head != origin:
        raise RuntimeError(
            "Local HEAD and origin/main must be aligned."
        )

    implementation_commit = str(
        authorization["locked_implementation_commit"]
    )
    implementation_commits = {
        latest_commit(path)
        for path in IMPLEMENTATION_PATHS
    }
    if implementation_commits != {
        implementation_commit
    }:
        raise RuntimeError(
            "EXP-027 implementation files do not share "
            "the authorized implementation commit."
        )
    authorization_commits = {
        latest_commit(path)
        for path in AUTHORIZATION_PATHS
    }
    if len(authorization_commits) != 1:
        raise RuntimeError(
            "EXP-027 authorization files lack one shared commit."
        )
    authorization_commit = next(
        iter(authorization_commits)
    )
    if authorization_commit != head:
        raise RuntimeError(
            "EXP-027 authorization commit must equal HEAD."
        )
    if changed_paths(
        implementation_commit,
        authorization_commit,
    ) != set(AUTHORIZATION_PATHS):
        raise RuntimeError(
            "EXP-027 authorization commit scope changed."
        )
    if run_git(
        "diff",
        "--quiet",
        LOCKED_PREREGISTRATION_COMMIT,
        implementation_commit,
        "--",
        *PREREGISTRATION_PATHS,
        check=False,
    ).returncode != 0:
        raise RuntimeError(
            "EXP-027 preregistration files changed after lock."
        )

    if OUTPUT_DIR.exists() or PARTIAL_DIR.exists():
        raise RuntimeError(
            "EXP-027 output or partial output already exists. "
            "The one-time run cannot be repeated."
        )
    free_bytes = shutil.disk_usage(
        PROJECT_DIR
    ).free
    if free_bytes < MINIMUM_FREE_BYTES:
        raise RuntimeError(
            "Insufficient free disk space for EXP-027."
        )
    return {
        "branch": branch,
        "head": head,
        "origin_main": origin,
        "implementation_commit": implementation_commit,
        "authorization_commit": authorization_commit,
    }


def load_protected_ohlcv(
    path: Path,
    *,
    representation_id: str,
) -> pd.DataFrame:
    """Deserialize only the locked protected 2026 trading dates."""

    import pyarrow as pa
    import pyarrow.dataset as ds

    record = get_exp027_preregistration()
    boundary = record["data_access_boundary"]
    if (
        boundary["allowed_strategy_session_start"]
        != PERIOD_START
        or boundary["allowed_strategy_session_end"]
        != PERIOD_END
    ):
        raise RuntimeError(
            "EXP-027 protected loader boundary changed."
        )

    source = ds.dataset(path, format="parquet")
    trading_date_type = source.schema.field(
        "trading_date"
    ).type
    if not pa.types.is_date32(trading_date_type):
        raise RuntimeError(
            "EXP-027 requires date32 trading_date "
            "for predicate pushdown."
        )

    predicate = (
        ds.field("trading_date")
        >= pa.scalar(
            date.fromisoformat(PERIOD_START),
            type=pa.date32(),
        )
    ) & (
        ds.field("trading_date")
        <= pa.scalar(
            date.fromisoformat(PERIOD_END),
            type=pa.date32(),
        )
    )
    table = source.scanner(
        columns=list(SOURCE_COLUMNS),
        filter=predicate,
        batch_size=65_536,
        batch_readahead=1,
        fragment_readahead=1,
        use_threads=True,
    ).to_table()
    frame = table.to_pandas(
        split_blocks=True,
        self_destruct=True,
    )
    dates = pd.to_datetime(
        frame["trading_date"],
        errors="raise",
    ).dt.strftime("%Y-%m-%d")
    if frame.empty:
        raise RuntimeError(
            "EXP-027 protected source scan is empty."
        )
    if dates.min() < PERIOD_START or dates.max() > PERIOD_END:
        raise RuntimeError(
            "EXP-027 loader returned an out-of-bound date."
        )
    return frame


def _parallel_replay(
    frame: pd.DataFrame,
    *,
    representation_id: str,
    workers: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    identifiers = exp027_reported_ids()
    worker_count = max(1, min(int(workers), len(identifiers)))
    chunks = [
        identifiers[index::worker_count]
        for index in range(worker_count)
    ]
    chunks = [chunk for chunk in chunks if chunk]

    def run_chunk(
        candidate_ids: tuple[str, ...],
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        return replay_candidates(
            frame,
            representation_id=representation_id,
            allowed_session_start=PERIOD_START,
            allowed_session_end=PERIOD_END,
            candidate_ids=candidate_ids,
        )

    with ThreadPoolExecutor(
        max_workers=worker_count
    ) as executor:
        results = list(executor.map(run_chunk, chunks))

    decisions = pd.concat(
        [item[0] for item in results],
        ignore_index=True,
    ).loc[:, DECISION_COLUMNS]
    decisions = decisions.sort_values(
        ["candidate_id", "session_date"],
        kind="stable",
    ).reset_index(drop=True)

    trade_parts = [
        item[1]
        for item in results
        if not item[1].empty
    ]
    trades = (
        pd.concat(
            trade_parts,
            ignore_index=True,
        ).loc[:, TRADE_COLUMNS]
        if trade_parts
        else pd.DataFrame(columns=TRADE_COLUMNS)
    )
    if not trades.empty:
        trades = trades.sort_values(
            [
                "candidate_id",
                "session_date",
                "entry_timestamp_utc",
            ],
            kind="stable",
        ).reset_index(drop=True)
    return decisions, trades


def replay_with_guards(
    *,
    representation_id: str,
    workers: int,
) -> dict[str, Any]:
    path = REPRESENTATION_FILES[
        representation_id
    ]

    first_source = load_protected_ohlcv(
        path,
        representation_id=representation_id,
    )
    first_decisions, first_trades = replay_candidates(
        first_source,
        representation_id=representation_id,
        allowed_session_start=PERIOD_START,
        allowed_session_end=PERIOD_END,
        candidate_ids=exp027_reported_ids(),
    )

    second_source = load_protected_ohlcv(
        path,
        representation_id=representation_id,
    )
    second_decisions, second_trades = replay_candidates(
        second_source,
        representation_id=representation_id,
        allowed_session_start=PERIOD_START,
        allowed_session_end=PERIOD_END,
        candidate_ids=exp027_reported_ids(),
    )

    parallel_decisions, parallel_trades = _parallel_replay(
        first_source,
        representation_id=representation_id,
        workers=workers,
    )

    hashes = {
        "first_decisions": canonical_dataframe_sha256(
            first_decisions
        ),
        "first_trades": canonical_dataframe_sha256(
            first_trades
        ),
        "second_decisions": canonical_dataframe_sha256(
            second_decisions
        ),
        "second_trades": canonical_dataframe_sha256(
            second_trades
        ),
        "parallel_decisions": canonical_dataframe_sha256(
            parallel_decisions
        ),
        "parallel_trades": canonical_dataframe_sha256(
            parallel_trades
        ),
    }
    if (
        hashes["first_decisions"]
        != hashes["second_decisions"]
        or hashes["first_trades"]
        != hashes["second_trades"]
        or hashes["first_decisions"]
        != hashes["parallel_decisions"]
        or hashes["first_trades"]
        != hashes["parallel_trades"]
    ):
        raise RuntimeError(
            "EXP-027 independent rebuild or serial/parallel "
            "parity failed."
        )

    return {
        "source_rows": int(len(first_source)),
        "source_first_trading_date": str(
            pd.to_datetime(
                first_source["trading_date"]
            ).min().date()
        ),
        "source_last_trading_date": str(
            pd.to_datetime(
                first_source["trading_date"]
            ).max().date()
        ),
        "decisions": first_decisions,
        "trades": first_trades,
        "hashes": hashes,
        "independent_rebuild": True,
        "serial_parallel_parity": True,
    }


def _load_csv(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise RuntimeError(
            f"Missing frozen EXP-026 context file: {path}"
        )
    return pd.read_csv(path)


def load_frozen_historical_context() -> pd.DataFrame:
    return historical_context(
        _load_csv(
            PROJECT_DIR
            / "results"
            / "EXP-026"
            / "phase_a_development"
            / "development_metrics.csv"
        ),
        _load_csv(
            PROJECT_DIR
            / "results"
            / "EXP-026"
            / "phase_b_internal_validation"
            / "internal_validation_metrics.csv"
        ),
        _load_csv(
            PROJECT_DIR
            / "results"
            / "EXP-026"
            / "phase_c_known_comparison"
            / "known_comparison_metrics.csv"
        ),
    )


def _render_charts(
    equity_by_candidate: dict[str, pd.DataFrame],
    output_dir: Path,
) -> None:
    import matplotlib.pyplot as plt

    output_dir.mkdir(parents=True, exist_ok=True)
    chart_ids = (
        *primary_cohort_ids(),
        "orb_control_exp005_15m_both_time",
        "orb_control_exp007_30m_long_1r",
    )

    figure, axis = plt.subplots(figsize=(15, 7))
    for candidate_id in chart_ids:
        frame = equity_by_candidate[candidate_id]
        axis.plot(
            pd.to_datetime(frame["session_date"]),
            frame["equity_usd"],
            label=candidate_id,
        )
    axis.set_title(
        "EXP-027 Protected 2026 Equity Curves "
        "— Primary Cohort and Controls"
    )
    axis.set_xlabel("Session date")
    axis.set_ylabel("Equity (USD)")
    axis.legend(loc="best", fontsize=8)
    figure.tight_layout()
    figure.savefig(
        output_dir / "equity_curves.png",
        dpi=150,
        facecolor="white",
    )
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(15, 7))
    for candidate_id in chart_ids:
        frame = equity_by_candidate[candidate_id]
        axis.plot(
            pd.to_datetime(frame["session_date"]),
            frame["drawdown_usd"],
            label=candidate_id,
        )
    axis.set_title(
        "EXP-027 Protected 2026 Drawdown Curves "
        "— Primary Cohort and Controls"
    )
    axis.set_xlabel("Session date")
    axis.set_ylabel("Drawdown (USD)")
    axis.legend(loc="best", fontsize=8)
    figure.tight_layout()
    figure.savefig(
        output_dir / "drawdown_curves.png",
        dpi=150,
        facecolor="white",
    )
    plt.close(figure)


def _format_number(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "—"
    if not np.isfinite(number):
        return "—"
    return f"{number:,.3f}"


def _render_report_markdown(
    metrics: pd.DataFrame,
    summary: Mapping[str, Any],
) -> str:
    all_trades = metrics.loc[
        metrics["segment"] == "ALL_TRADES"
    ].copy()
    lines = [
        "# EXP-027 Protected 2026 Measurement",
        "",
        "## Boundary",
        "",
        f"- Period: `{PERIOD_START}` through `{PERIOD_END}`",
        "- Candidate selection: `False`",
        "- Parameter optimisation: `False`",
        "- Winner declaration: `False`",
        "- Databento API calls: `0`",
        "- Paper/live trading authorised: `False`",
        "",
        "## All 24 evidence rows",
        "",
        "| Candidate | Cohort | Trades | Net profit | Profit Factor | Win rate | Maximum drawdown |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in all_trades.itertuples(index=False):
        lines.append(
            "| "
            + " | ".join(
                (
                    str(row.candidate_id),
                    cohort_for(str(row.candidate_id)),
                    str(int(row.completed_trades)),
                    _format_number(row.net_profit_usd),
                    _format_number(row.trade_profit_factor),
                    _format_number(
                        float(row.win_rate) * 100.0
                        if np.isfinite(float(row.win_rate))
                        else np.nan
                    )
                    + "%",
                    _format_number(row.maximum_drawdown_usd),
                )
            )
            + " |"
        )
    lines.extend(
        (
            "",
            "## Interpretation",
            "",
            "The three primary candidates were declared before protected "
            "2026 access. The remaining strategy variants are comparison "
            "evidence and cannot replace the primary cohort under EXP-027.",
            "",
            "This report describes measured behaviour. It does not "
            "automatically validate an edge, reject a strategy, choose one "
            "winner or authorise trading.",
            "",
            "## Reproducibility",
            "",
            f"- Independent rebuild: `{summary['independent_rebuild']}`",
            f"- Serial/parallel parity: `{summary['serial_parallel_parity']}`",
            f"- Protected source rows, primary: `{summary['primary_source_rows']:,}`",
            f"- Protected source rows, unadjusted: `{summary['secondary_source_rows']:,}`",
            "",
        )
    )
    return "\n".join(lines)


def _render_report_html(
    metrics: pd.DataFrame,
    summary: Mapping[str, Any],
) -> str:
    all_trades = metrics.loc[
        metrics["segment"] == "ALL_TRADES"
    ].copy()
    display = all_trades.loc[
        :,
        (
            "candidate_id",
            "completed_trades",
            "net_profit_usd",
            "trade_profit_factor",
            "win_rate",
            "maximum_drawdown_usd",
            "net_profit_to_drawdown",
        ),
    ].copy()
    display.insert(
        1,
        "cohort",
        display["candidate_id"].map(cohort_for),
    )
    display["win_rate"] = (
        pd.to_numeric(
            display["win_rate"],
            errors="coerce",
        )
        * 100.0
    )
    table = display.to_html(
        index=False,
        border=0,
        classes="metrics",
        na_rep="—",
        float_format=lambda value: f"{value:,.3f}",
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>EXP-027 Protected 2026 Measurement</title>
<style>
body {{
  background: #0b0b0c;
  color: #f0f0f0;
  font-family: Arial, sans-serif;
  margin: 0;
}}
main {{
  width: min(1500px, calc(100% - 32px));
  margin: 24px auto 70px;
}}
section {{
  background: #151517;
  border: 1px solid #333;
  border-radius: 14px;
  padding: 22px;
  margin: 18px 0;
}}
h1, h2 {{ margin-top: 0; }}
p, li {{ line-height: 1.55; }}
table {{
  width: 100%;
  border-collapse: collapse;
  overflow: auto;
}}
th, td {{
  border-bottom: 1px solid #333;
  padding: 9px 10px;
  text-align: right;
}}
th:first-child, td:first-child,
th:nth-child(2), td:nth-child(2) {{
  text-align: left;
}}
img {{
  width: 100%;
  background: white;
  border-radius: 10px;
}}
.warning {{
  border-left: 4px solid #c6a06a;
  padding-left: 14px;
}}
</style>
</head>
<body>
<main>
<section>
<h1>EXP-027 Protected 2026 Multi-Strategy Measurement</h1>
<p>
Protected period: <strong>{escape(PERIOD_START)}</strong> through
<strong>{escape(PERIOD_END)}</strong>. All 22 fixed strategy variants and
two fixed controls are reported.
</p>
<p class="warning">
No candidate selection, parameter optimisation, secondary-candidate promotion,
winner declaration, paper trading or live trading is authorised.
</p>
</section>
<section>
<h2>All / Long / Short measurements</h2>
{table}
</section>
<section>
<h2>Equity curves</h2>
<img src="assets/equity_curves.png" alt="Equity curves">
</section>
<section>
<h2>Drawdown curves</h2>
<img src="assets/drawdown_curves.png" alt="Drawdown curves">
</section>
<section>
<h2>Execution integrity</h2>
<ul>
<li>Independent rebuild: {summary['independent_rebuild']}</li>
<li>Serial/parallel parity: {summary['serial_parallel_parity']}</li>
<li>Databento API calls: 0</li>
<li>New market-data download: False</li>
<li>Paper/live trading authorised: False</li>
</ul>
</section>
</main>
</body>
</html>
"""


def _hash_outputs(
    root: Path,
) -> dict[str, Any]:
    files = {
        path.relative_to(root).as_posix(): {
            "size_bytes": int(path.stat().st_size),
            "sha256": sha256_file(path),
        }
        for path in sorted(root.rglob("*"))
        if path.is_file()
        and path.name not in {
            "output_hashes.json",
            "EXP027_COMPLETE.json",
        }
    }
    return {
        "file_count": len(files),
        "files": files,
        "manifest_sha256": canonical_object_sha256(files),
    }


def run_exp027(
    *,
    workers: int,
) -> dict[str, Any]:
    validate_exp027_preregistration()
    validate_exp027_population()
    authorization = load_authorization()
    repository = verify_repository_for_execution(
        authorization
    )
    frozen = verify_frozen_series_bytes()
    metadata = inspect_parquet_metadata()

    PARTIAL_DIR.mkdir(parents=True, exist_ok=False)
    try:
        primary = replay_with_guards(
            representation_id="BACKWARD_ADJUSTED",
            workers=workers,
        )
        secondary = replay_with_guards(
            representation_id="UNADJUSTED",
            workers=workers,
        )

        primary_metrics = candidate_metrics(
            primary["trades"],
            candidate_ids=exp027_reported_ids(),
            period_start=PERIOD_START,
            period_end=PERIOD_END,
        )
        secondary_metrics = candidate_metrics(
            secondary["trades"],
            candidate_ids=exp027_reported_ids(),
            period_start=PERIOD_START,
            period_end=PERIOD_END,
        )
        validate_result_frames(
            decisions=primary["decisions"],
            trades=primary["trades"],
            metrics=primary_metrics,
        )
        validate_result_frames(
            decisions=secondary["decisions"],
            trades=secondary["trades"],
            metrics=secondary_metrics,
        )

        registry = candidate_registry_exp027()
        monthly = monthly_results(
            primary["trades"],
            candidate_ids=exp027_reported_ids(),
            start_month="2026-01",
            end_month="2026-07",
        )
        costs = cost_sensitivity(
            primary["trades"],
            candidate_ids=exp027_reported_ids(),
            period_start=PERIOD_START,
            period_end=PERIOD_END,
        )
        sensitivity = representation_sensitivity(
            primary_metrics,
            secondary_metrics,
        )
        distributions = trade_distribution(
            primary["trades"]
        )
        context = load_frozen_historical_context()

        equity_by_candidate: dict[
            str,
            pd.DataFrame,
        ] = {}
        for candidate_id in exp027_reported_ids():
            ledger = canonical_trade_ledger(
                primary["trades"],
                candidate_id=candidate_id,
            )
            equity = dense_session_equity(
                primary["decisions"],
                primary["trades"],
                candidate_id=candidate_id,
            )
            equity_by_candidate[candidate_id] = equity
            comparison = comparison_timeseries(
                equity,
                candidate_id=candidate_id,
            )
            series_metrics = candidate_series_metrics(
                primary_metrics,
                candidate_id=candidate_id,
            )
            series_dir = (
                PARTIAL_DIR
                / "series"
                / candidate_id
            )
            write_csv(
                series_dir / "trades.csv",
                ledger,
            )
            write_csv(
                series_dir / "equity.csv",
                equity,
            )
            write_csv(
                series_dir
                / "comparison_timeseries.csv",
                comparison,
            )
            write_csv(
                series_dir / "metrics.csv",
                series_metrics,
            )

        episodes = drawdown_episodes(
            equity_by_candidate
        )
        _render_charts(
            equity_by_candidate,
            PARTIAL_DIR / "assets",
        )

        summary = {
            "experiment_id": "EXP-027",
            "classification": (
                "PROTECTED_2026_MEASUREMENT_COMPLETE"
            ),
            "period_start": PERIOD_START,
            "period_end": PERIOD_END,
            "partial_year": True,
            "strategy_candidate_count": 22,
            "control_candidate_count": 2,
            "reported_series_count": 24,
            "primary_confirmation_cohort": (
                primary_cohort_ids()
            ),
            "candidate_selection": False,
            "parameter_optimization": False,
            "winner_declaration": False,
            "secondary_candidate_promotion": False,
            "primary_source_rows": primary[
                "source_rows"
            ],
            "secondary_source_rows": secondary[
                "source_rows"
            ],
            "primary_decision_rows": int(
                len(primary["decisions"])
            ),
            "primary_trade_rows": int(
                len(primary["trades"])
            ),
            "secondary_decision_rows": int(
                len(secondary["decisions"])
            ),
            "secondary_trade_rows": int(
                len(secondary["trades"])
            ),
            "independent_rebuild": True,
            "serial_parallel_parity": True,
            "primary_rebuild_hashes": primary[
                "hashes"
            ],
            "secondary_rebuild_hashes": secondary[
                "hashes"
            ],
            "preregistration_sha256": (
                EXPECTED_EXP027_PREREGISTRATION_SHA256
            ),
            "implementation_commit": repository[
                "implementation_commit"
            ],
            "authorization_commit": repository[
                "authorization_commit"
            ],
            "exp022_series_snapshot": frozen[
                "series_snapshot"
            ],
            "parquet_metadata_rows": {
                key: int(value["row_count"])
                for key, value in metadata.items()
            },
            "protected_2026_accessed": True,
            "historical_2010_2025_market_rows_accessed": False,
            "databento_api_calls": 0,
            "network_access": False,
            "new_databento_download": False,
            "paper_trading_authorized": False,
            "live_trading_authorized": False,
        }

        write_csv(
            PARTIAL_DIR / "candidate_registry.csv",
            registry,
        )
        atomic_write_json(
            PARTIAL_DIR
            / "protected_measurement_summary.json",
            summary,
        )
        write_csv(
            PARTIAL_DIR
            / "protected_measurement_metrics.csv",
            primary_metrics,
        )
        write_csv(
            PARTIAL_DIR / "monthly_results.csv",
            monthly,
        )
        write_csv(
            PARTIAL_DIR / "cost_sensitivity.csv",
            costs,
        )
        write_csv(
            PARTIAL_DIR
            / "representation_sensitivity.csv",
            sensitivity,
        )
        write_csv(
            PARTIAL_DIR / "trade_distribution.csv",
            distributions,
        )
        write_csv(
            PARTIAL_DIR / "drawdown_episodes.csv",
            episodes,
        )
        write_csv(
            PARTIAL_DIR / "historical_context.csv",
            context,
        )

        markdown = _render_report_markdown(
            primary_metrics,
            summary,
        )
        html = _render_report_html(
            primary_metrics,
            summary,
        )
        atomic_write_text(
            PARTIAL_DIR / "report.md",
            markdown,
        )
        atomic_write_text(
            PARTIAL_DIR / "report.html",
            html,
        )

        hashes = _hash_outputs(PARTIAL_DIR)
        atomic_write_json(
            PARTIAL_DIR / "output_hashes.json",
            hashes,
        )
        completion = {
            "experiment_id": "EXP-027",
            "completed": True,
            "completed_at_utc": datetime.now(
                timezone.utc
            ).isoformat(),
            "output_manifest_sha256": hashes[
                "manifest_sha256"
            ],
            "output_file_count_before_completion": (
                hashes["file_count"] + 1
            ),
            "reported_series_count": 24,
            "candidate_selection": False,
            "parameter_optimization": False,
            "winner_declaration": False,
            "independent_rebuild": True,
            "serial_parallel_parity": True,
            "historical_2010_2025_market_rows_accessed": False,
            "protected_2026_accessed": True,
            "databento_api_calls": 0,
            "network_access": False,
            "paper_trading_authorized": False,
            "live_trading_authorized": False,
        }
        atomic_write_json(
            PARTIAL_DIR / "EXP027_COMPLETE.json",
            completion,
        )
        os.replace(PARTIAL_DIR, OUTPUT_DIR)
        return completion
    except Exception:
        raise


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the one-time authorized EXP-027 protected "
            "2026 measurement."
        )
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help=(
            "Worker count for the required serial/parallel "
            "parity rebuild."
        ),
    )
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    result = run_exp027(
        workers=arguments.workers,
    )
    print("EXP-027 PROTECTED MEASUREMENT COMPLETE")
    print(f"Completed:                 {result['completed']}")
    print("Reported series:           24")
    print("Candidate selection:       False")
    print("Parameter optimisation:    False")
    print("Winner declaration:        False")
    print("Independent rebuild:       True")
    print("Serial/parallel parity:    True")
    print("Protected 2026 accessed:   True")
    print("Historical rows accessed:  False")
    print("Databento API calls:       0")
    print("Paper/live trading:        False")
    print(f"Output:                    {OUTPUT_DIR}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(
            f"ERROR: {exc}",
            file=__import__("sys").stderr,
        )
        raise SystemExit(1)
