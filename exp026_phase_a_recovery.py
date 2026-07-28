from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import math
import os
from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence

import pandas as pd

from exp026_phase_a_authorization import (
    EXPECTED_EXP026_PHASE_A_AUTHORIZATION_SHA256,
    canonical_record_hash as authorization_record_hash,
    get_exp026_phase_a_authorization,
    validate_exp026_phase_a_authorization,
)
from exp026_runner import (
    PHASE_OUTPUT_DIRS,
    PHASE_PARTIAL_DIRS,
    PHASE_REQUIRED_OUTPUTS,
    _verify_required_outputs,
    _write_output_manifest,
    atomic_write_text,
    sha256_file,
)

PROJECT_DIR = Path(__file__).resolve().parent
AUTHORIZATION_COMMIT = "5fa417ed56c2d620c5d348e9ab43f3d7634518b8"
IMPLEMENTATION_COMMIT = "13ee0683dfcbbb5d763f7254f3b245ecc8e6d9cd"
AUTHORIZATION_SHA256 = "527fdbba75095d9b987e0e64dd6410e6fa79d1bff5916049c933e4f6aa8a9dcc"
RECOVERY_PATHS = (
    "exp026_phase_a_recovery.py",
    "research/EXP-026_phase_a_recovery.md",
    "tests/test_exp026_phase_a_recovery.py",
)
EXPECTED_PARTIAL_FILES = {
    "candidate_registry.csv": (2997, "325c043aecdbf498f994da07975cf09bb8b44f48812028014aef9998cfe4010f"),
    "development_annual_results.csv": (22801, "753cf86ccb3f6dd0eba9698edd36facdc5b416a035992bdd5cd7385883865146"),
    "development_metrics.csv": (24066, "5bd340778f3baa239298bc0f79e7cc9b184f820f9a852be6b081106a1a7df45f"),
    "development_summary.json": (567, "4a18a93c22eeefbf2d4cc028bdb8c36bc6e49dd1ab2a5dbf675a0b10b3910caf"),
    "phase_a_survivors.json": (502, "e9d940a3c247d885d1ea7537a7673ce67a15517ef79ba18ef5d243096a5f27cf"),
}
EXPECTED_SURVIVORS = (
    "gap_fade_0p75_1r",
    "gap_fade_0p25_1r",
    "opening_drive_0p75_1p5r",
    "opening_drive_0p75_time",
    "premarket_continuation_0p875_1p5r",
    "premarket_continuation_0p625_1p5r",
)
REPORT_COLUMNS = (
    "candidate_id",
    "segment",
    "completed_trades",
    "net_profit_usd",
    "trade_profit_factor",
    "win_rate",
    "maximum_drawdown_usd",
    "net_profit_to_drawdown",
    "maximum_consecutive_losses",
)


def run_git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=PROJECT_DIR,
        text=True,
        capture_output=True,
        check=check,
    )


def changed_paths(base: str, head: str) -> set[str]:
    return {
        line.strip().replace("\\", "/")
        for line in run_git("diff", "--name-only", base, head).stdout.splitlines()
        if line.strip()
    }


def latest_commit(path: str) -> str:
    value = run_git("log", "-1", "--format=%H", "--", path).stdout.strip()
    if not value:
        raise RuntimeError(f"No commit found for recovery path: {path}.")
    return value


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise RuntimeError(f"Expected JSON object: {path}")
    return value


def partial_snapshot(path: Path) -> dict[str, tuple[int, str]]:
    return {
        child.name: (int(child.stat().st_size), sha256_file(child))
        for child in sorted(path.iterdir())
        if child.is_file()
    }


def validate_partial_evidence(partial_dir: Path | None = None) -> dict[str, Any]:
    partial_dir = PHASE_PARTIAL_DIRS["A"] if partial_dir is None else partial_dir
    if not partial_dir.is_dir():
        raise RuntimeError("EXP-026 Phase A partial directory is missing.")
    if partial_dir == PHASE_PARTIAL_DIRS["A"] and PHASE_OUTPUT_DIRS["A"].exists():
        raise RuntimeError("Final EXP-026 Phase A directory already exists.")
    if partial_snapshot(partial_dir) != EXPECTED_PARTIAL_FILES:
        raise RuntimeError("EXP-026 Phase A partial evidence changed.")

    summary = load_json(partial_dir / "development_summary.json")
    survivors = load_json(partial_dir / "phase_a_survivors.json")
    if (
        summary.get("source_session_start") != "2010-06-07"
        or summary.get("source_session_end") != "2017-12-31"
        or summary.get("decision_rows") != 46584
        or summary.get("trade_rows") != 11502
        or summary.get("survivor_count") != 6
        or tuple(summary.get("survivor_ids", ())) != EXPECTED_SURVIVORS
        or summary.get("independent_rebuild") is not True
        or summary.get("protected_2026_accessed") is not False
        or summary.get("databento_api_calls") != 0
    ):
        raise RuntimeError("EXP-026 Phase A development summary changed.")
    if (
        survivors.get("experiment_id") != "EXP-026"
        or survivors.get("phase") != "A"
        or tuple(survivors.get("candidate_ids", ())) != EXPECTED_SURVIVORS
        or survivors.get("maximum_per_family") != 2
        or survivors.get("no_minimum_profit_gate") is not True
        or survivors.get("protected_2026_accessed") is not False
    ):
        raise RuntimeError("EXP-026 Phase A survivor record changed.")

    metrics = pd.read_csv(partial_dir / "development_metrics.csv")
    missing = sorted(set(REPORT_COLUMNS).difference(metrics.columns))
    if missing:
        raise RuntimeError("Missing Phase A report columns: " + ", ".join(missing))
    if (
        len(metrics) != 72
        or metrics["candidate_id"].nunique() != 24
        or set(metrics["segment"].astype(str)) != {"ALL_TRADES", "LONG_TRADES", "SHORT_TRADES"}
    ):
        raise RuntimeError("EXP-026 Phase A metrics population changed.")
    registry = pd.read_csv(partial_dir / "candidate_registry.csv")
    if len(registry) != 24:
        raise RuntimeError("EXP-026 Phase A candidate registry changed.")
    return {"summary": summary, "survivors": survivors, "metrics": metrics}


def repository_recovery_preflight() -> dict[str, Any]:
    if os.environ.get("DATABENTO_API_KEY", "").strip():
        raise RuntimeError("DATABENTO_API_KEY must not be set for Phase A recovery.")
    if run_git("status", "--porcelain").stdout.strip():
        raise RuntimeError("Repository must be clean before Phase A recovery.")
    branch = run_git("branch", "--show-current").stdout.strip()
    head = run_git("rev-parse", "HEAD").stdout.strip()
    origin = run_git("rev-parse", "origin/main").stdout.strip()
    if branch != "main" or head != origin:
        raise RuntimeError("EXP-026 recovery requires clean aligned main.")
    if run_git("merge-base", "--is-ancestor", AUTHORIZATION_COMMIT, head, check=False).returncode != 0:
        raise RuntimeError("Phase A authorization commit is not an ancestor.")
    if changed_paths(AUTHORIZATION_COMMIT, head) != set(RECOVERY_PATHS):
        raise RuntimeError("EXP-026 Phase A recovery commit scope changed.")
    if {latest_commit(path) for path in RECOVERY_PATHS} != {head}:
        raise RuntimeError("EXP-026 Phase A recovery files do not share HEAD.")

    validate_exp026_phase_a_authorization()
    authorization = get_exp026_phase_a_authorization()
    if (
        authorization_record_hash(authorization) != EXPECTED_EXP026_PHASE_A_AUTHORIZATION_SHA256
        or EXPECTED_EXP026_PHASE_A_AUTHORIZATION_SHA256 != AUTHORIZATION_SHA256
        or authorization.get("locked_implementation_commit") != IMPLEMENTATION_COMMIT
    ):
        raise RuntimeError("Frozen EXP-026 Phase A authorization changed.")
    evidence = validate_partial_evidence()
    return {
        "branch": branch,
        "head": head,
        "authorization_commit": AUTHORIZATION_COMMIT,
        "implementation_commit": IMPLEMENTATION_COMMIT,
        **evidence,
    }


def format_value(value: Any) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return f"{value:.6f}" if math.isfinite(value) else ""
    return str(value).replace("|", r"\|").replace("\n", " ")


def metrics_markdown(metrics: pd.DataFrame) -> str:
    frame = metrics.loc[:, list(REPORT_COLUMNS)]
    lines = [
        "| " + " | ".join(REPORT_COLUMNS) + " |",
        "|" + "|".join("---" for _ in REPORT_COLUMNS) + "|",
    ]
    for row in frame.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(format_value(value) for value in row) + " |")
    return "\n".join(lines)


def build_report(metrics: pd.DataFrame) -> str:
    selection = ", ".join(EXPECTED_SURVIVORS)
    return f"""# EXP-026 Phase A Development

**Phase:** A

**Recovery:** `EXP-026-A-R1`

**Protected 2026 market values materialised:** No

**Databento API calls:** 0

## Recovery disclosure

The authorised computation completed its independent deterministic rebuild and wrote the five hash-locked Phase A result files. Report generation then stopped because pandas could not import the optional `tabulate` package.

This recovery generated only the missing report, output-hash manifest and completion marker from the existing hash-locked results. It did not read market data, replay a strategy, change a candidate, change a parameter or repeat selection.

## Selection

{selection}

## All / Long / Short metrics

{metrics_markdown(metrics)}

## Interpretation notes

- Selection is exploratory and does not validate an edge.
- The two ORB controls were reported but were not eligible for selection.
- Phase B remains inaccessible until a separate completion record and Phase B authorisation are committed.
- Protected 2026 data remains inaccessible.
"""


def verify_manifest(output_dir: Path) -> None:
    manifest = load_json(output_dir / "output_hashes.json")
    files = manifest.get("files")
    expected = {
        name for name in PHASE_REQUIRED_OUTPUTS["A"]
        if name not in {"output_hashes.json", "PHASE_A_COMPLETE.json"}
    }
    if manifest.get("experiment_id") != "EXP-026" or manifest.get("phase") != "A" or set(files or {}) != expected:
        raise RuntimeError("EXP-026 Phase A output manifest changed.")
    for relative_path, record in files.items():
        path = output_dir / relative_path
        if (
            not path.is_file()
            or int(path.stat().st_size) != int(record["size_bytes"])
            or sha256_file(path) != str(record["sha256"])
        ):
            raise RuntimeError(f"Output manifest mismatch: {relative_path}.")


def recover_phase_a() -> dict[str, Any]:
    preflight = repository_recovery_preflight()
    partial_dir = PHASE_PARTIAL_DIRS["A"]
    final_dir = PHASE_OUTPUT_DIRS["A"]
    atomic_write_text(partial_dir / "report.md", build_report(preflight["metrics"]))
    _write_output_manifest(
        partial_dir,
        marker_name="PHASE_A_COMPLETE.json",
        phase="A",
        summary=preflight["summary"],
    )
    _verify_required_outputs(partial_dir, phase="A")
    verify_manifest(partial_dir)
    marker = load_json(partial_dir / "PHASE_A_COMPLETE.json")
    if (
        marker.get("completed") is not True
        or marker.get("protected_2026_accessed") is not False
        or marker.get("databento_api_calls") != 0
        or marker.get("network_access") is not False
        or marker.get("paper_trading_authorized") is not False
        or marker.get("live_trading_authorized") is not False
    ):
        raise RuntimeError("EXP-026 Phase A completion marker changed.")
    os.replace(partial_dir, final_dir)
    _verify_required_outputs(final_dir, phase="A")
    verify_manifest(final_dir)
    return {"head": preflight["head"], "output_dir": str(final_dir)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        result = repository_recovery_preflight()
        print("EXP-026 PHASE A RECOVERY PREFLIGHT PASSED")
        print(f"Branch:                      {result['branch']}")
        print(f"HEAD:                        {result['head']}")
        print("Partial files verified:      5")
        print("Independent rebuild:         True")
        print("Decision rows:               46,584")
        print("Trade rows:                  11,502")
        print("Survivors:                   6")
        print("Market values read:          False")
        print("Strategy recalculated:       False")
        print("Protected 2026 accessed:     False")
        print("Databento API calls:         0")
        return
    result = recover_phase_a()
    print("EXP-026 PHASE A RECOVERY COMPLETE")
    print(f"Recovery commit:             {result['head']}")
    print(f"Output directory:            {result['output_dir']}")
    print("Market values read:          False")
    print("Strategy recalculated:       False")
    print("Protected 2026 accessed:     False")
    print("Databento API calls:         0")
    print("Paper/live trading:          False")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=__import__("sys").stderr)
        raise SystemExit(1)
