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
        raise FileNotFoundError(f"Required review file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    lifecycle = get_experiment_lifecycle("EXP-003")

    if lifecycle.stage != "REVIEW":
        raise RuntimeError(
            "EXP-003 must be in REVIEW before formal review runs. "
            f"Current stage: {lifecycle.stage}"
        )

    results = PROJECT_DIR / "results" / "EXP-003"
    decision_dir = results / "review"
    decision_file = decision_dir / "review_decision.json"

    if decision_file.exists():
        raise RuntimeError(
            "EXP-003 review decision already exists. Do not rerun "
            f"the review:\n{decision_file}"
        )

    git = git_state(PROJECT_DIR)
    if git.get("working_tree_dirty") is not False:
        raise RuntimeError(
            "Commit and push the REVIEW stage update before running "
            "formal review. Git must report a clean working tree."
        )

    full_decision = _load_json(
        results / "full_validation" / "full_validation_decision.json"
    )
    stability = _load_json(results / "parameter_stability_summary.json")

    summary = pd.read_csv(results / "summary.csv", index_col="test")
    diagnostics = pd.read_csv(
        results / "trade_diagnostics_summary.csv", index_col="test"
    )
    yearly = pd.read_csv(
        results / "full_validation" / "fixed_oos_calendar_years.csv"
    )
    profitable_years = int(yearly["profitable"].astype(bool).sum())

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
        "review_type": "read_only_post_validation_review",
        "source_full_validation_decision": str(
            results / "full_validation" / "full_validation_decision.json"
        ),
        "review_git_commit": git.get("commit"),
    }

    decision_dir.mkdir(parents=True, exist_ok=True)

    review_markdown = [
        "# EXP-003 Formal Review",
        "",
        f"**Decision:** {evaluation.decision}",
        "",
        "This review used only recorded result files. No strategy "
        "research was rerun and no locked rule was changed.",
        "",
        "## Checks",
        "",
    ]

    for name, check in evaluation.checks.items():
        status = "PASS" if check["passed"] else "FAIL"
        review_markdown.append(
            f"- **{status} — {name}:** actual `{check['actual']}` "
            f"{check['operator']} `{check['threshold']}`"
        )

    review_markdown.extend([
        "",
        "## Interpretation",
        "",
        "Acceptance means the strategy may proceed to simulated paper "
        "testing. It does not authorize live capital, leverage or rule "
        "changes. Paper testing must preserve the registered signal, "
        "execution and cost assumptions.",
    ])

    (decision_dir / "review_report.md").write_text(
        "\n".join(review_markdown), encoding="utf-8"
    )

    # Decision is written last to make the workflow one-time.
    decision_file.write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )

    print()
    print("============== EXP-003 FORMAL REVIEW ==============")
    print(f"Decision: {evaluation.decision}")
    for name, check in evaluation.checks.items():
        status = "PASS" if check["passed"] else "FAIL"
        print(
            f"{status} | {name}: {check['actual']} "
            f"{check['operator']} {check['threshold']}"
        )
    print()
    print(f"Decision file: {decision_file}")
    print(f"Review report: {decision_dir / 'review_report.md'}")
    print("====================================================")


if __name__ == "__main__":
    main()
