from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
from html import escape
import importlib
import json
import os
from pathlib import Path
import subprocess
from typing import Any, Iterable, Mapping, Sequence


PROJECT_DIR = Path(__file__).resolve().parent
LOCKED_ATTEMPT_002_FAILURE_COMMIT = (
    "7acf180c9640079c560c992a00c4fd413f3b13b7"
)
LOCKED_ATTEMPT_002_FAILURE_SHA256 = (
    "d58e747db36ae3c5e80a034e3b6de127d9771184805470a16f0d3adbbab77359"
)
ATTEMPT_002_MODULE = "exp024_attempt_002_failure"
ATTEMPT_002_PATH = PROJECT_DIR / "exp024_attempt_002_failure.py"

PARTIAL_DIR = (
    PROJECT_DIR
    / "results"
    / "EXP-024"
    / "source_disagreement_attribution.partial"
)
FINAL_DIR = (
    PROJECT_DIR
    / "results"
    / "EXP-024"
    / "source_disagreement_attribution"
)

RECOVERY_AUTHORIZATION_MODULE = (
    "exp024_evidence_recovery_authorization"
)
RECOVERY_AUTHORIZATION_PATH = (
    PROJECT_DIR / "exp024_evidence_recovery_authorization.py"
)
RECOVERY_AUTHORIZATION_PATHS = (
    "exp024_evidence_recovery_authorization.py",
    "research/EXP-024_evidence_recovery_authorization.md",
    "tests/test_exp024_evidence_recovery_authorization.py",
)
RECOVERY_IMPLEMENTATION_PATHS = (
    "exp024_evidence_recovery.py",
    "research/EXP-024_evidence_recovery_implementation.md",
    "tests/test_exp024_evidence_recovery.py",
)
ATTEMPT_002_PATHS = (
    "exp024_attempt_002_failure.py",
    "research/EXP-024_attempt_002_failure.md",
    "tests/test_exp024_attempt_002_failure.py",
)

PRESERVED_ARTIFACTS: dict[str, dict[str, Any]] = {'aggregation_check.csv': {'size_bytes': 641094, 'sha256': 'c2c693c142a076db404739047f8e683cb63e1c218f057e1c3d46b9c20f63a7fa'}, 'assets/attribution_categories.png': {'size_bytes': 74003, 'sha256': '9c88dc6b2c68fd36eb471b0c8298e8e3d455de80fbef0a29d511ba4e8d4d5f85'}, 'assets/raw_component_differences.png': {'size_bytes': 79515, 'sha256': '8e81cf3d629653841c90abac421e37b7f994ced81490eb1420ee7fb3e58f3214'}, 'assets/roll_context.png': {'size_bytes': 57825, 'sha256': 'f8b9fd976c18ce3e227dacb5317adf96f73ee4c769548e5ca892a5ccaf13e0bf'}, 'assets/threshold_margins.png': {'size_bytes': 89786, 'sha256': 'f7489bb363b51e9a6250a53ca262d545c3dbf6cac93fa09b31132cd056dde7a6'}, 'feature_comparison.csv': {'size_bytes': 38064, 'sha256': 'd10a5ffb4e01ee0b7ab65d65f721ab5beca0a4b9cfac6eca4fdacc82c9bd595c'}, 'mismatch_attribution.csv': {'size_bytes': 6797, 'sha256': '1f762b2cbb2d53c0cd979171a584a42fb3e8742040b2c3bb9494155e7d55dbae'}, 'raw_component_differences.csv': {'size_bytes': 163741, 'sha256': 'de13b28fb809ce5b267816b126b71ecbe3ae4d2d396b7cab9bbf9860e417c457'}, 'roll_context.csv': {'size_bytes': 8791, 'sha256': '35ec1eba30a6eeea59ab369b89a575b0cad44cf23b6b3ca89d494a8ef6428ffc'}}

CANDIDATE_IDS = (
    "gap_fade_0p50_1r",
    "premarket_continuation_0p50_time",
    "premarket_continuation_0p75_time",
)
EXPECTED_CANDIDATE_COUNTS = {
    "gap_fade_0p50_1r": 48,
    "premarket_continuation_0p50_time": 2,
    "premarket_continuation_0p75_time": 1,
}
EXPECTED_CATEGORY_COUNTS = {
    "ELIGIBILITY_DIFFERENCE": 1,
    "NORMALIZED_CONTEXT_THRESHOLD_CROSSING": 5,
    "CONTEXT_DIRECTION_DIFFERENCE": 0,
    "FIRST_CASH_BAR_CONFIRMATION_DIFFERENCE": 0,
    "ENTRY_RISK_VALIDITY_DIFFERENCE": 0,
    "MULTIPLE_DECISION_COMPONENT_DIFFERENCES": 2,
    "UNRESOLVED_WITH_LOCKED_FEATURES": 43,
}
EXPECTED_SOURCE_IDS = {
    "QUANTOWER_REFERENCE",
    "BACKWARD_ADJUSTED",
    "UNADJUSTED",
}
CLASSIFICATION = "ATTRIBUTION_DIAGNOSTIC_NOT_QUALIFIED"

GENERATED_OUTPUTS = (
    "attribution_summary.json",
    "report.md",
    "report.html",
    "output_hashes.json",
    "ATTRIBUTION_DIAGNOSTIC_COMPLETE.json",
)
FINAL_OUTPUTS = tuple(PRESERVED_ARTIFACTS) + GENERATED_OUTPUTS


def run_git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=PROJECT_DIR,
        text=True,
        capture_output=True,
        check=check,
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def changed_paths(base: str, head: str) -> set[str]:
    return {
        line.strip().replace("\\", "/")
        for line in run_git(
            "diff", "--name-only", base, head
        ).stdout.splitlines()
        if line.strip()
    }


def commit_that_added(relative_path: str) -> str:
    commits = run_git(
        "log",
        "--diff-filter=A",
        "--reverse",
        "--format=%H",
        "--",
        relative_path,
    ).stdout.strip().splitlines()
    if len(commits) != 1:
        raise RuntimeError(
            "Expected exactly one creation commit for "
            f"{relative_path}."
        )
    return commits[0]


def dirty_paths() -> set[str]:
    output = run_git(
        "status", "--porcelain=v1", "--untracked-files=all"
    ).stdout
    result: set[str] = set()
    for line in output.splitlines():
        if len(line) < 4:
            continue
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        result.add(path.replace("\\", "/"))
    return result


def _strict_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    normalised = str(value).strip().lower()
    if normalised not in {"true", "false"}:
        raise ValueError(f"Expected a strict boolean, found {value!r}.")
    return normalised == "true"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise RuntimeError(f"CSV has no header: {path.name}")
        return [dict(row) for row in reader]


def _count(rows: Iterable[Mapping[str, Any]], column: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for row in rows:
        key = str(row[column])
        result[key] = result.get(key, 0) + 1
    return result


def snapshot_preserved_artifacts(
    directory: Path = PARTIAL_DIR,
) -> dict[str, dict[str, Any]]:
    if not directory.is_dir():
        raise RuntimeError(
            f"EXP-024 partial evidence directory is missing: {directory}"
        )
    actual = {
        path.relative_to(directory).as_posix()
        for path in directory.rglob("*")
        if path.is_file()
    }
    allowed = set(PRESERVED_ARTIFACTS) | set(GENERATED_OUTPUTS)
    unexpected = actual.difference(allowed)
    if unexpected:
        raise RuntimeError(
            "Unexpected EXP-024 partial artifact(s): "
            + ", ".join(sorted(unexpected))
        )
    result: dict[str, dict[str, Any]] = {}
    for relative, expected in PRESERVED_ARTIFACTS.items():
        path = directory / relative
        if not path.is_file():
            raise RuntimeError(f"Missing preserved EXP-024 artifact: {relative}")
        current = {
            "size_bytes": int(path.stat().st_size),
            "sha256": sha256_file(path),
        }
        if current != expected:
            raise RuntimeError(
                f"Preserved EXP-024 artifact changed: {relative}"
            )
        result[relative] = current
    return result


def verify_attempt_002_record() -> dict[str, Any]:
    if not ATTEMPT_002_PATH.is_file():
        raise RuntimeError("EXP-024 attempt-002 failure record is absent.")
    module = importlib.import_module(ATTEMPT_002_MODULE)
    validator = getattr(
        module, "validate_exp024_attempt_002_failure", None
    )
    getter = getattr(
        module, "get_exp024_attempt_002_failure", None
    )
    expected_hash = getattr(
        module, "EXPECTED_EXP024_ATTEMPT_002_FAILURE_SHA256", None
    )
    if validator is None or getter is None:
        raise RuntimeError("EXP-024 attempt-002 interface is incomplete.")
    validator()
    record = getter()
    if (
        expected_hash != LOCKED_ATTEMPT_002_FAILURE_SHA256
        or record.get("attempt_id") != "EXP-024-ATTEMPT-002"
        or record.get("evidence_only_recovery_authorized") is not True
        or record.get("market_data_rerun_authorized") is not False
        or record.get("partial_artifact_count") != 9
        or record.get("reconstructed_classification") != CLASSIFICATION
    ):
        raise RuntimeError("EXP-024 attempt-002 recovery boundary changed.")
    if record.get("partial_artifacts") != PRESERVED_ARTIFACTS:
        raise RuntimeError("EXP-024 preserved-artifact lock changed.")
    return record


def inspect_preserved_evidence(
    directory: Path = PARTIAL_DIR,
) -> dict[str, Any]:
    snapshot_preserved_artifacts(directory)
    mismatch = _read_csv(directory / "mismatch_attribution.csv")
    features = _read_csv(directory / "feature_comparison.csv")
    raw = _read_csv(directory / "raw_component_differences.csv")
    roll = _read_csv(directory / "roll_context.csv")
    aggregation = _read_csv(directory / "aggregation_check.csv")

    if len(mismatch) != 51:
        raise RuntimeError("EXP-024 mismatch row count changed.")
    candidate_counts = _count(mismatch, "candidate_id")
    if candidate_counts != EXPECTED_CANDIDATE_COUNTS:
        raise RuntimeError("EXP-024 candidate mismatch counts changed.")
    category_counts = {
        category: 0 for category in EXPECTED_CATEGORY_COUNTS
    }
    for row in mismatch:
        category = str(row["primary_attribution_category"])
        if category not in category_counts:
            raise RuntimeError(
                f"Unexpected EXP-024 attribution category: {category}"
            )
        category_counts[category] += 1
    if category_counts != EXPECTED_CATEGORY_COUNTS:
        raise RuntimeError("EXP-024 attribution category counts changed.")

    reference_matches = sum(
        _strict_bool(row["reference_rebuild_matches_frozen"])
        for row in mismatch
    )
    transfer_matches = sum(
        _strict_bool(row["transfer_rebuild_matches_frozen"])
        for row in mismatch
    )
    unresolved = sum(
        row["primary_attribution_category"]
        == "UNRESOLVED_WITH_LOCKED_FEATURES"
        for row in mismatch
    )
    failed_reference = [
        row
        for row in mismatch
        if not _strict_bool(row["reference_rebuild_matches_frozen"])
    ]
    if (
        reference_matches != 8
        or transfer_matches != 51
        or unresolved != 43
        or len(failed_reference) != 43
        or {
            row["candidate_id"] for row in failed_reference
        } != {"gap_fade_0p50_1r"}
    ):
        raise RuntimeError("EXP-024 rebuild evidence changed.")

    mismatch_keys = {
        (row["candidate_id"], row["session_date"])
        for row in mismatch
    }
    feature_keys = {
        (row["candidate_id"], row["session_date"])
        for row in features
    }
    if (
        len(features) != 153
        or feature_keys != mismatch_keys
        or {row["source_id"] for row in features} != EXPECTED_SOURCE_IDS
    ):
        raise RuntimeError("EXP-024 source-feature evidence changed.")
    feature_per_key = _count(
        (
            {"key": f"{row['candidate_id']}|{row['session_date']}"}
            for row in features
        ),
        "key",
    )
    if set(feature_per_key.values()) != {3}:
        raise RuntimeError("EXP-024 feature source multiplicity changed.")

    if len(raw) != 1530 or len(roll) != 51:
        raise RuntimeError("EXP-024 supporting evidence row counts changed.")
    if {
        (row["candidate_id"], row["session_date"]) for row in roll
    } != mismatch_keys:
        raise RuntimeError("EXP-024 roll-context keys changed.")
    if not all(
        _strict_bool(row["roll_context_is_descriptive_not_causal"])
        for row in roll
    ):
        raise RuntimeError("EXP-024 roll-context boundary changed.")

    if len(aggregation) != 4709 or not all(
        _strict_bool(row["all_ohlc_match"])
        for row in aggregation
    ):
        raise RuntimeError("EXP-024 aggregation evidence changed.")

    diagnostic_hard_checks = {
        "exactly_51_candidate_session_rows_are_retained": True,
        "candidate_mismatch_counts_match_preregistration": True,
        "quantower_one_minute_aggregation_matches_frozen_five_minute_rows": True,
        "transfer_decision_rebuild_matches_frozen_alignment": True,
        "reference_decision_rebuild_matches_frozen_alignment": False,
        "attribution_categories_are_exhaustive_and_mutually_exclusive": True,
        "roll_context_is_not_used_as_automatic_causal_attribution": True,
        "no_exit_pnl_return_equity_or_performance_metric_is_computed": True,
    }
    return {
        "mismatch_rows": mismatch,
        "feature_rows": features,
        "raw_rows": raw,
        "roll_rows": roll,
        "aggregation_rows": aggregation,
        "candidate_counts": candidate_counts,
        "category_counts": category_counts,
        "reference_rebuild_match_rows": reference_matches,
        "reference_rebuild_failure_rows": 51 - reference_matches,
        "transfer_rebuild_match_rows": transfer_matches,
        "unresolved_rows": unresolved,
        "diagnostic_hard_checks": diagnostic_hard_checks,
        "diagnostic_hard_failure_count": sum(
            not value for value in diagnostic_hard_checks.values()
        ),
    }


def _base_repository_state() -> dict[str, Any]:
    if os.environ.get("DATABENTO_API_KEY"):
        raise RuntimeError("DATABENTO_API_KEY must not be present.")
    if run_git("branch", "--show-current").stdout.strip() != "main":
        raise RuntimeError("EXP-024 recovery requires branch main.")
    head = run_git("rev-parse", "HEAD").stdout.strip()
    origin_main = run_git("rev-parse", "origin/main").stdout.strip()
    if head != origin_main:
        raise RuntimeError("Local HEAD and origin/main are not aligned.")
    if dirty_paths():
        raise RuntimeError("Repository must be clean for EXP-024 recovery.")
    if FINAL_DIR.exists():
        raise RuntimeError("EXP-024 final output already exists.")
    if not PARTIAL_DIR.is_dir():
        raise RuntimeError("EXP-024 partial output is absent.")
    return {"head": head, "origin_main": origin_main}


def implementation_preflight() -> dict[str, Any]:
    state = _base_repository_state()
    record = verify_attempt_002_record()
    failure_commit = commit_that_added("exp024_attempt_002_failure.py")
    if failure_commit != LOCKED_ATTEMPT_002_FAILURE_COMMIT:
        raise RuntimeError("EXP-024 attempt-002 failure commit changed.")
    if changed_paths(
        "da7bbe843361fd9d08cf64cc1e772c9eabf82fb5",
        failure_commit,
    ) != set(ATTEMPT_002_PATHS):
        raise RuntimeError("EXP-024 attempt-002 commit scope changed.")
    implementation_commit = commit_that_added(
        "exp024_evidence_recovery.py"
    )
    if changed_paths(
        LOCKED_ATTEMPT_002_FAILURE_COMMIT,
        implementation_commit,
    ) != set(RECOVERY_IMPLEMENTATION_PATHS):
        raise RuntimeError("EXP-024 recovery implementation scope changed.")
    if run_git(
        "merge-base",
        "--is-ancestor",
        implementation_commit,
        "HEAD",
        check=False,
    ).returncode != 0:
        raise RuntimeError("EXP-024 recovery implementation ancestry is invalid.")
    if RECOVERY_AUTHORIZATION_PATH.exists():
        raise RuntimeError(
            "EXP-024 recovery authorization must be absent at the implementation gate."
        )
    preserved = snapshot_preserved_artifacts()
    evidence = inspect_preserved_evidence()
    return {
        **state,
        "attempt_002_failure": record,
        "implementation_commit": implementation_commit,
        "authorization_present": False,
        "preserved_artifacts": preserved,
        "evidence": evidence,
        "market_parquet_accessed": False,
        "attribution_recalculated": False,
        "charts_rebuilt": False,
        "recovery_run": False,
    }


def load_recovery_authorization() -> dict[str, Any]:
    if not RECOVERY_AUTHORIZATION_PATH.is_file():
        raise RuntimeError("EXP-024 evidence recovery is not authorized.")
    module = importlib.import_module(RECOVERY_AUTHORIZATION_MODULE)
    validator = getattr(
        module, "validate_exp024_evidence_recovery_authorization", None
    )
    getter = getattr(
        module, "get_exp024_evidence_recovery_authorization", None
    )
    if validator is None or getter is None:
        raise RuntimeError("EXP-024 recovery authorization interface is incomplete.")
    validator()
    record = getter()
    required_false = (
        "market_parquet_access_authorized",
        "attribution_recalculation_authorized",
        "feature_reconstruction_authorized",
        "chart_rebuild_authorized",
        "network_access_authorized",
        "strategy_replay_authorized",
        "performance_evaluation_authorized",
        "optimization_authorized",
        "mcpt_authorized",
        "bootstrap_authorized",
        "walk_forward_authorized",
        "paper_trading_authorized",
        "live_trading_authorized",
    )
    if (
        record.get("experiment_id") != "EXP-024"
        or record.get("authorization_id")
        != "EXP-024-EVIDENCE-RECOVERY-AUTH-001"
        or record.get("evidence_recovery_authorized") is not True
        or record.get("one_time_recovery") is not True
        or record.get("maximum_recovery_runs") != 1
        or record.get("attempt_002_failure_commit")
        != LOCKED_ATTEMPT_002_FAILURE_COMMIT
        or record.get("attempt_002_failure_record_sha256")
        != LOCKED_ATTEMPT_002_FAILURE_SHA256
        or record.get("partial_artifact_count") != 9
        or any(record.get(name) is not False for name in required_false)
    ):
        raise RuntimeError("EXP-024 recovery authorization boundary changed.")
    implementation_commit = record.get("locked_recovery_implementation_commit")
    if not isinstance(implementation_commit, str) or len(implementation_commit) != 40:
        raise RuntimeError("EXP-024 locked recovery implementation commit is invalid.")
    return record


def authorized_preflight() -> dict[str, Any]:
    state = _base_repository_state()
    record = verify_attempt_002_record()
    authorization = load_recovery_authorization()
    implementation_commit = authorization[
        "locked_recovery_implementation_commit"
    ]
    if changed_paths(
        LOCKED_ATTEMPT_002_FAILURE_COMMIT,
        implementation_commit,
    ) != set(RECOVERY_IMPLEMENTATION_PATHS):
        raise RuntimeError("EXP-024 recovery implementation scope changed.")
    authorization_commit = commit_that_added(
        "exp024_evidence_recovery_authorization.py"
    )
    if changed_paths(
        implementation_commit,
        authorization_commit,
    ) != set(RECOVERY_AUTHORIZATION_PATHS):
        raise RuntimeError("EXP-024 recovery authorization scope changed.")
    if (
        run_git(
            "merge-base", "--is-ancestor", implementation_commit,
            authorization_commit, check=False,
        ).returncode != 0
        or run_git(
            "merge-base", "--is-ancestor", authorization_commit,
            "HEAD", check=False,
        ).returncode != 0
    ):
        raise RuntimeError("EXP-024 recovery authorization ancestry is invalid.")
    protected_paths = (
        *ATTEMPT_002_PATHS,
        *RECOVERY_IMPLEMENTATION_PATHS,
        *RECOVERY_AUTHORIZATION_PATHS,
    )
    if run_git(
        "diff", "--quiet", authorization_commit, "HEAD", "--",
        *protected_paths, check=False,
    ).returncode != 0:
        raise RuntimeError("Protected EXP-024 recovery files changed after authorization.")
    preserved = snapshot_preserved_artifacts()
    evidence = inspect_preserved_evidence()
    return {
        **state,
        "attempt_002_failure": record,
        "authorization": authorization,
        "implementation_commit": implementation_commit,
        "authorization_commit": authorization_commit,
        "authorization_present": True,
        "preserved_artifacts": preserved,
        "evidence": evidence,
        "market_parquet_accessed": False,
        "attribution_recalculated": False,
        "charts_rebuilt": False,
        "recovery_run": False,
    }


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _markdown_table(columns: Sequence[str], rows: Iterable[Sequence[Any]]) -> str:
    def clean(value: Any) -> str:
        if value is None:
            return ""
        return str(value).replace("|", "\\|").replace("\n", " ")
    lines = [
        "| " + " | ".join(columns) + " |",
        "|" + "|".join("---" for _ in columns) + "|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(clean(value) for value in row) + " |")
    return "\n".join(lines)


def build_recovery_documents(
    evidence: Mapping[str, Any],
    *,
    repository: Mapping[str, str],
    recovered_at_utc: str,
    preserved: Mapping[str, Mapping[str, Any]],
) -> dict[str, bytes]:
    category_rows = [
        (category, evidence["category_counts"][category])
        for category in EXPECTED_CATEGORY_COUNTS
    ]
    diagnostic_checks = evidence["diagnostic_hard_checks"]
    check_rows = [
        (name, bool(value))
        for name, value in diagnostic_checks.items()
    ]
    visible_rows = [
        (
            row["candidate_id"],
            row["session_date"],
            row["frozen_reference_trade_flag"],
            row["frozen_transfer_trade_flag"],
            row["differing_decision_components"],
            row["primary_attribution_category"],
        )
        for row in evidence["mismatch_rows"]
    ]
    recovery_checks = {
        "attempt_002_failure_record_matches": True,
        "exactly_nine_preserved_artifacts_match": True,
        "only_preserved_csv_and_image_evidence_was_read": True,
        "candidate_session_row_count_is_51": True,
        "feature_row_count_is_153": True,
        "raw_component_difference_row_count_is_1530": True,
        "roll_context_row_count_is_51": True,
        "aggregation_row_count_is_4709": True,
        "classification_matches_failure_record": True,
        "no_market_parquet_access": True,
        "no_feature_reconstruction": True,
        "no_attribution_recalculation": True,
        "no_chart_rebuild": True,
        "no_network_or_api_access": True,
        "no_strategy_or_performance_evaluation": True,
        "no_optimization_mcpt_bootstrap_or_walk_forward": True,
        "no_paper_or_live_trading_authorization": True,
        "original_nine_artifacts_remain_unchanged": True,
    }
    summary = {
        "schema_version": 1,
        "experiment_id": "EXP-024",
        "publication_mode": "EVIDENCE_ONLY_RECOVERY",
        "classification": CLASSIFICATION,
        "classification_reason": (
            "The Quantower reference-decision reconstruction hard check "
            "fails on 43 gap-fade mismatch rows. The transfer reconstruction "
            "and Quantower one-to-five-minute aggregation checks pass."
        ),
        "recovered_at_utc": recovered_at_utc,
        "candidate_ids": list(CANDIDATE_IDS),
        "candidate_session_row_count": 51,
        "feature_row_count": 153,
        "raw_component_difference_row_count": 1530,
        "roll_context_row_count": 51,
        "aggregation_check_row_count": 4709,
        "aggregation_all_ohlc_match": True,
        "reference_rebuild_match_rows": 8,
        "reference_rebuild_failure_rows": 43,
        "transfer_rebuild_match_rows": 51,
        "unresolved_count": 43,
        "candidate_counts": evidence["candidate_counts"],
        "category_counts": evidence["category_counts"],
        "diagnostic_hard_checks": diagnostic_checks,
        "diagnostic_hard_failure_count": evidence[
            "diagnostic_hard_failure_count"
        ],
        "recovery_hard_checks": recovery_checks,
        "recovery_hard_failure_count": 0,
        "preserved_artifacts": preserved,
        "repository": dict(repository),
        "market_parquet_accessed": False,
        "feature_reconstruction": False,
        "attribution_recalculation": False,
        "chart_rebuild": False,
        "databento_api_calls": 0,
        "network_access": False,
        "strategy_replay": False,
        "exit_evaluation": False,
        "performance_evaluation": False,
        "optimization": False,
        "mcpt": False,
        "bootstrap": False,
        "walk_forward": False,
        "source_winner_selected": False,
        "candidate_winner_selected": False,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
        "rerun_authorized": False,
    }

    markdown = f"""# EXP-024 Source-Disagreement Attribution

**Publication mode:** `EVIDENCE_ONLY_RECOVERY`

**Classification:** `{CLASSIFICATION}`

This report publishes the nine hash-locked artifacts preserved after attempt
002. It does not scan market Parquet files, reconstruct features, recalculate
attribution, rebuild charts, evaluate exits or returns, or select a preferred
data source.

## Headline result

| Measurement | Result |
|---|---:|
| Frozen mismatch rows | 51 |
| Quantower aggregation rows matching | 4,709 / 4,709 |
| Transfer decision rebuild matching | 51 / 51 |
| Quantower reference decision rebuild matching | 8 / 51 |
| Failed reference rebuild rows | 43 |
| Unresolved rows | 43 |

The diagnostic is not qualified because the locked Quantower reference
reconstruction fails on 43 gap-fade rows. The transfer reconstruction and the
one-minute-to-five-minute Quantower aggregation check both pass.

## Attribution categories

{_markdown_table(("Category", "Count"), category_rows)}

## Visual evidence

![Attribution categories](assets/attribution_categories.png)

![Paired threshold margins](assets/threshold_margins.png)

![Raw component differences](assets/raw_component_differences.png)

![Roll context](assets/roll_context.png)

## Diagnostic hard checks

{_markdown_table(("Hard check", "Passed"), check_rows)}

## All 51 frozen mismatch rows

{_markdown_table(
    (
        "Candidate",
        "Session",
        "Reference trade",
        "Transfer trade",
        "Differing components",
        "Attribution",
    ),
    visible_rows,
)}

## Interpretation boundary

The 43 unresolved rows mean this diagnostic cannot fully explain the frozen
source disagreement under the locked feature reconstruction. That does not
prove either source is wrong or superior. Quantower contract identity, roll
trigger and adjustment method remain unexposed. No strategy edge, P&L,
position sizing, paper trading or live trading conclusion is authorized.
"""

    category_html = "".join(
        f"<tr><td>{escape(str(category))}</td><td>{count}</td></tr>"
        for category, count in category_rows
    )
    check_html = "".join(
        f"<tr><td>{escape(str(name))}</td><td>{str(bool(value))}</td></tr>"
        for name, value in check_rows
    )
    visible_html = "".join(
        "<tr>" + "".join(
            f"<td>{escape(str(value))}</td>" for value in row
        ) + "</tr>"
        for row in visible_rows
    )
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>EXP-024 source-disagreement attribution</title>
<style>
body {{ font-family: Arial, sans-serif; color: #20242a; background: #fff;
       max-width: 1320px; margin: 0 auto; padding: 28px; line-height: 1.45; }}
section {{ margin: 0 0 34px; }}
.warning {{ color: #a33a2b; font-weight: 700; }}
img {{ display: block; width: 100%; height: auto; margin: 16px 0 28px;
       border: 1px solid #d8dde5; }}
table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
th, td {{ border: 1px solid #d8dde5; padding: 6px 8px; text-align: left; }}
th {{ background: #f3f5f8; position: sticky; top: 0; }}
.scroll {{ overflow-x: auto; max-height: 760px; overflow-y: auto; }}
code {{ background: #f3f5f8; padding: 2px 5px; border-radius: 4px; }}
</style>
</head>
<body>
<h1>EXP-024 Source-Disagreement Attribution</h1>
<p>Publication mode: <code>EVIDENCE_ONLY_RECOVERY</code></p>
<p>Classification: <span class="warning">{CLASSIFICATION}</span></p>
<section>
<h2>Headline result</h2>
<table><tbody>
<tr><th>Frozen mismatch rows</th><td>51</td></tr>
<tr><th>Quantower aggregation rows matching</th><td>4,709 / 4,709</td></tr>
<tr><th>Transfer decision rebuild matching</th><td>51 / 51</td></tr>
<tr><th>Quantower reference decision rebuild matching</th><td>8 / 51</td></tr>
<tr><th>Failed reference rebuild rows</th><td>43</td></tr>
<tr><th>Unresolved rows</th><td>43</td></tr>
</tbody></table>
<p class="warning">The diagnostic is not qualified because the locked
Quantower reference reconstruction fails on 43 gap-fade rows.</p>
</section>
<section><h2>Attribution categories</h2><table><thead><tr><th>Category</th>
<th>Count</th></tr></thead><tbody>{category_html}</tbody></table></section>
<section><h2>Visual evidence</h2>
<img src="assets/attribution_categories.png" alt="Attribution categories">
<img src="assets/threshold_margins.png" alt="Paired threshold margins">
<img src="assets/raw_component_differences.png" alt="Raw component differences">
<img src="assets/roll_context.png" alt="Roll context"></section>
<section><h2>Diagnostic hard checks</h2><table><thead><tr><th>Hard check</th>
<th>Passed</th></tr></thead><tbody>{check_html}</tbody></table></section>
<section><h2>All 51 frozen mismatch rows</h2><div class="scroll"><table>
<thead><tr><th>Candidate</th><th>Session</th><th>Reference trade</th>
<th>Transfer trade</th><th>Differing components</th><th>Attribution</th></tr></thead>
<tbody>{visible_html}</tbody></table></div></section>
<section><h2>Interpretation boundary</h2><p>The 43 unresolved rows mean this
locked diagnostic cannot fully explain the source disagreement. Neither source
is treated as ground truth or selected as superior. No strategy edge, P&amp;L,
paper trading or live trading conclusion is authorized.</p></section>
</body></html>
"""
    return {
        "attribution_summary.json": _json_bytes(summary),
        "report.md": markdown.encode("utf-8"),
        "report.html": html.encode("utf-8"),
    }


def _atomic_write_bytes(path: Path, content: bytes) -> None:
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        raise RuntimeError(f"Temporary recovery output exists: {temporary}")
    with temporary.open("xb") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _hash_outputs(
    directory: Path,
    names: Iterable[str],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for relative in names:
        path = directory / relative
        if not path.is_file():
            raise RuntimeError(f"Missing EXP-024 recovery output: {relative}")
        result[relative] = {
            "size_bytes": int(path.stat().st_size),
            "sha256": sha256_file(path),
        }
    return result


def run_evidence_recovery() -> dict[str, Any]:
    preflight = authorized_preflight()
    before = snapshot_preserved_artifacts()
    evidence = preflight["evidence"]
    recovered_at = datetime.now(timezone.utc).isoformat()
    repository = {
        "attempt_002_failure_commit": LOCKED_ATTEMPT_002_FAILURE_COMMIT,
        "recovery_implementation_commit": preflight[
            "implementation_commit"
        ],
        "recovery_authorization_commit": preflight[
            "authorization_commit"
        ],
        "recovery_execution_head": preflight["head"],
    }
    documents = build_recovery_documents(
        evidence,
        repository=repository,
        recovered_at_utc=recovered_at,
        preserved=before,
    )
    for relative in GENERATED_OUTPUTS:
        if (PARTIAL_DIR / relative).exists():
            raise RuntimeError(
                f"EXP-024 generated recovery output already exists: {relative}"
            )
    for relative, content in documents.items():
        _atomic_write_bytes(PARTIAL_DIR / relative, content)

    core_names = tuple(PRESERVED_ARTIFACTS) + tuple(documents)
    output_hashes = _hash_outputs(PARTIAL_DIR, core_names)
    _atomic_write_bytes(
        PARTIAL_DIR / "output_hashes.json",
        _json_bytes({"files": output_hashes}),
    )
    marker = {
        "schema_version": 1,
        "experiment_id": "EXP-024",
        "publication_mode": "EVIDENCE_ONLY_RECOVERY",
        "classification": CLASSIFICATION,
        "completed_at_utc": recovered_at,
        "recovery_complete": True,
        "diagnostic_qualified": False,
        "all_recovery_hard_checks_pass": True,
        "diagnostic_hard_failure_count": evidence[
            "diagnostic_hard_failure_count"
        ],
        "preserved_artifact_count": 9,
        "required_output_count": 14,
        "market_parquet_accessed": False,
        "attribution_recalculated": False,
        "charts_rebuilt": False,
        "databento_api_calls": 0,
        "network_access": False,
        "strategy_replay": False,
        "performance_evaluation": False,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
        "rerun_authorized": False,
        "output_hashes_sha256": sha256_file(
            PARTIAL_DIR / "output_hashes.json"
        ),
    }
    _atomic_write_bytes(
        PARTIAL_DIR / "ATTRIBUTION_DIAGNOSTIC_COMPLETE.json",
        _json_bytes(marker),
    )

    after = snapshot_preserved_artifacts()
    if after != before:
        raise RuntimeError(
            "Preserved EXP-024 artifacts changed during evidence recovery."
        )
    actual = {
        path.relative_to(PARTIAL_DIR).as_posix()
        for path in PARTIAL_DIR.rglob("*")
        if path.is_file()
    }
    if actual != set(FINAL_OUTPUTS):
        raise RuntimeError(
            "EXP-024 recovery output set is incomplete: "
            + str(sorted(actual))
        )
    os.replace(PARTIAL_DIR, FINAL_DIR)
    return {
        "classification": CLASSIFICATION,
        "output": str(FINAL_DIR),
        "candidate_session_rows": 51,
        "reference_rebuild_match_rows": 8,
        "reference_rebuild_failure_rows": 43,
        "transfer_rebuild_match_rows": 51,
        "unresolved_rows": 43,
        "required_output_count": 14,
        "databento_api_calls": 0,
        "market_parquet_accessed": False,
        "attribution_recalculated": False,
        "strategy_replay": False,
        "rerun_authorized": False,
    }


def print_implementation_preflight(state: Mapping[str, Any]) -> None:
    print("EXP-024 evidence-recovery implementation preflight passed.")
    print(f"Repository HEAD:             {state['head']}")
    print(f"Attempt-002 failure commit:  {LOCKED_ATTEMPT_002_FAILURE_COMMIT}")
    print(f"Implementation commit:       {state['implementation_commit']}")
    print("Preserved artifacts:         9 / 9")
    print("Candidate-session rows:      51")
    print("Classification:              ATTRIBUTION_DIAGNOSTIC_NOT_QUALIFIED")
    print("Authorization present:       False")
    print("Market Parquet access:       False")
    print("Attribution recalculation:   False")
    print("Recovery run:                False")


def print_authorized_preflight(state: Mapping[str, Any]) -> None:
    print("EXP-024 authorized evidence-recovery preflight passed.")
    print(f"Repository HEAD:             {state['head']}")
    print(f"Implementation commit:       {state['implementation_commit']}")
    print(f"Authorization commit:        {state['authorization_commit']}")
    print("Preserved artifacts:         9 / 9")
    print("Candidate-session rows:      51")
    print("Classification:              ATTRIBUTION_DIAGNOSTIC_NOT_QUALIFIED")
    print("Market Parquet access:       False")
    print("Attribution recalculation:   False")
    print("Recovery run:                False")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Protected EXP-024 evidence-only publication recovery."
    )
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--preflight", action="store_true")
    action.add_argument("--authorized-preflight", action="store_true")
    action.add_argument("--recover", action="store_true")
    parser.add_argument(
        "--confirm-evidence-only-recovery",
        action="store_true",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.preflight:
        if args.confirm_evidence_only_recovery:
            raise SystemExit(
                "Confirmation flag is valid only with --recover."
            )
        print_implementation_preflight(implementation_preflight())
        return
    if args.authorized_preflight:
        if args.confirm_evidence_only_recovery:
            raise SystemExit(
                "Confirmation flag is valid only with --recover."
            )
        print_authorized_preflight(authorized_preflight())
        return
    if not args.confirm_evidence_only_recovery:
        raise SystemExit(
            "--recover requires --confirm-evidence-only-recovery."
        )
    result = run_evidence_recovery()
    print("EXP-024 evidence-only recovery complete.")
    print(f"Classification:              {result['classification']}")
    print("Candidate-session rows:      51")
    print("Reference rebuild matches:   8 / 51")
    print("Transfer rebuild matches:    51 / 51")
    print("Unresolved rows:             43")
    print("Published outputs:           14")
    print("Market Parquet access:       False")
    print("Attribution recalculation:   False")
    print("Databento API calls:         0")
    print("Strategy run:                False")
    print("Recovery rerun:              Prohibited")


if __name__ == "__main__":
    main()
