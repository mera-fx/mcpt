from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from exp003_review import evaluate_exp003_review
from experiment_lifecycle import get_experiment_lifecycle
from run_provenance import git_state


PROJECT_DIR = Path(__file__).resolve().parent


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"Required review file not found: {path}"
        )

    return json.loads(
        path.read_text(encoding="utf-8")
    )


def main() -> None:
    lifecycle = get_experiment_lifecycle(
        "EXP-003"
    )

    if lifecycle.stage != "REVIEW":
        raise RuntimeError(
            "EXP-003 must remain in REVIEW while the corrected "
            f"review runs. Current stage: {lifecycle.stage}"
        )

    results = (
        PROJECT_DIR
        / "results"
        / "EXP-003"
    )

    original_review_file = (
        results
        / "review"
        / "review_decision.json"
    )

    if not original_review_file.exists():
        raise RuntimeError(
            "The original review decision must remain preserved "
            "before review_v2 runs."
        )

    original_review = _load_json(
        original_review_file
    )

    if (
        original_review.get("decision") != "REJECT"
        or original_review.get("failed_checks")
        != ["broad_parameter_support"]
    ):
        raise RuntimeError(
            "review_v2 is authorized only for the documented "
            "parameter-schema parsing defect."
        )

    decision_dir = (
        results / "review_v2"
    )

    decision_file = (
        decision_dir
        / "review_v2_decision.json"
    )

    if decision_file.exists():
        raise RuntimeError(
            "EXP-003 corrected review decision already exists. "
            "Do not rerun review_v2:\n"
            f"{decision_file}"
        )

    git = git_state(PROJECT_DIR)

    if git.get("working_tree_dirty") is not False:
        raise RuntimeError(
            "Commit and push the review-v2 correction before "
            "running it. Git must report a clean working tree."
        )

    full_decision = _load_json(
        results
        / "full_validation"
        / "full_validation_decision.json"
    )

    stability_path = (
        results
        / "parameter_stability_summary.json"
    )

    stability = _load_json(
        stability_path
    )

    summary = pd.read_csv(
        results / "summary.csv",
        index_col="test",
    )

    diagnostics = pd.read_csv(
        results
        / "trade_diagnostics_summary.csv",
        index_col="test",
    )

    yearly = pd.read_csv(
        results
        / "full_validation"
        / "fixed_oos_calendar_years.csv"
    )

    profitable_years = int(
        yearly["profitable"]
        .astype(bool)
        .sum()
    )

    evaluation = evaluate_exp003_review(
        full_validation_decision=full_decision,
        summary=summary,
        diagnostics=diagnostics,
        parameter_stability=stability,
        profitable_calendar_years=profitable_years,
    )

    payload = {
        **evaluation.to_dict(),
        "experiment_id": "EXP-003",
        "review_type": (
            "read_only_post_validation_review_v2"
        ),
        "correction_reason": (
            "The original review used obsolete parameter-stability "
            "field names and defaulted the broad-support count to "
            "zero. The recorded schema uses break_even_count."
        ),
        "preserved_original_review": str(
            original_review_file
        ),
        "source_parameter_stability": str(
            stability_path
        ),
        "source_break_even_count": int(
            stability["break_even_count"]
        ),
        "review_git_commit": git.get(
            "commit"
        ),
    }

    decision_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    lines = [
        "# EXP-003 Corrected Formal Review (v2)",
        "",
        f"**Decision:** {evaluation.decision}",
        "",
        "The original review decision is preserved. This corrected "
        "review changes no research result or strategy rule. It only "
        "reads the actual `break_even_count` field from the existing "
        "parameter-stability summary.",
        "",
        "## Checks",
        "",
    ]

    for name, check in (
        evaluation.checks.items()
    ):
        status = (
            "PASS"
            if check["passed"]
            else "FAIL"
        )

        lines.append(
            f"- **{status} — {name}:** "
            f"actual `{check['actual']}` "
            f"{check['operator']} "
            f"`{check['threshold']}`"
        )

    lines.extend(
        [
            "",
            "## Audit trail",
            "",
            f"- Original review: `{original_review_file}`",
            f"- Stability source: `{stability_path}`",
            "- Corrected field: `break_even_count`",
            (
                "- Recorded value: "
                f"`{stability['break_even_count']}`"
            ),
            "",
            "No MCPT, optimization, walk-forward test or OOS "
            "backtest was rerun.",
        ]
    )

    report_file = (
        decision_dir
        / "review_v2_report.md"
    )

    report_file.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    # Write decision last so this correction remains one-time.
    decision_file.write_text(
        json.dumps(
            payload,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print(
        "========== EXP-003 CORRECTED REVIEW V2 =========="
    )
    print(
        f"Decision: {evaluation.decision}"
    )

    for name, check in (
        evaluation.checks.items()
    ):
        status = (
            "PASS"
            if check["passed"]
            else "FAIL"
        )

        print(
            f"{status} | {name}: "
            f"{check['actual']} "
            f"{check['operator']} "
            f"{check['threshold']}"
        )

    print()
    print(
        f"Decision file: {decision_file}"
    )
    print(
        f"Review report: {report_file}"
    )
    print(
        "Original review preserved: "
        f"{original_review_file}"
    )
    print(
        "================================================="
    )


if __name__ == "__main__":
    main()
