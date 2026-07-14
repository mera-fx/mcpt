from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

from exp005_paper_testing_plan import validate_exp005_paper_testing_plan
from exp005_review_result import verify_local_exp005_review_decision

PROJECT_DIR = Path(__file__).resolve().parent


def _atomic_write(path: Path, text: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def _exp005_block(text: str) -> tuple[int, int, str]:
    start = text.find('"EXP-005": ExperimentLifecycle(')
    if start < 0:
        raise ValueError("EXP-005 lifecycle block was not found.")

    end_marker = (
        'preregistration_file=Path(\n'
        '            "research/EXP-005_preregistration.md"\n'
        '        ),\n'
        '    ),'
    )
    end = text.find(end_marker, start)

    if end < 0:
        compact_marker = (
            'preregistration_file=Path('
            '"research/EXP-005_preregistration.md"'
            '), ),'
        )
        end = text.find(compact_marker, start)
        if end < 0:
            raise ValueError("EXP-005 lifecycle block ending was not found.")
        end += len(compact_marker)
    else:
        end += len(end_marker)

    return start, end, text[start:end]


def replace_lifecycle(text: str) -> str:
    start, end, block = _exp005_block(text)

    if (
        'stage="ACCEPTED_FOR_PAPER_TESTING"' in block
        and "all 12 locked operational-quality" in block
    ):
        return text

    block, stage_count = re.subn(
        r'stage="REVIEW"',
        'stage="ACCEPTED_FOR_PAPER_TESTING"',
        block,
        count=1,
    )
    if stage_count != 1:
        raise ValueError("EXP-005 REVIEW stage was not found.")

    reason = (
        'stage_reason=(\n'
        '            "The protected quick transfer and independent 2023–2025 "\n'
        '            "full validation passed their locked gates. The separate "\n'
        '            "read-only review then passed all 12 locked operational-quality "\n'
        '            "checks, including two-tick cost resilience, all-year "\n'
        '            "profitability, NQ/MNQ consistency, direction balance and "\n'
        '            "loss-concentration controls. No strategy, MCPT, data import, "\n'
        '            "parameter, cost or gate was rerun or changed."\n'
        '        )'
    )
    next_action = (
        'next_action=(\n'
        '            "Operate the locked paper-only end-of-day NQ/MNQ replay for "\n'
        '            "at least 12 calendar weeks and 40 completed NQ paper trades. "\n'
        '            "Use completed Quantower one-minute exports, exact audit "\n'
        '            "reconciliation and the unchanged fixed ORB rules. Do not "\n'
        '            "connect an order API or use live capital."\n'
        '        )'
    )

    block, reason_count = re.subn(
        r'stage_reason=\(.*?\),\s*next_action=\(',
        reason + ",\n        next_action=(",
        block,
        count=1,
        flags=re.DOTALL,
    )
    if reason_count != 1:
        raise ValueError("EXP-005 lifecycle reason could not be updated.")

    block, next_count = re.subn(
        r'next_action=\(.*?\),\s*market_name=',
        next_action + ",\n        market_name=",
        block,
        count=1,
        flags=re.DOTALL,
    )
    if next_count != 1:
        raise ValueError("EXP-005 lifecycle next action could not be updated.")

    return text[:start] + block + text[end:]


def _replace_test_method(
    text: str,
    *,
    old_name: str,
    new_name: str,
    new_method: str,
) -> str:
    if f"def {new_name}(" in text:
        return text

    pattern = re.compile(
        rf"(?ms)^    def {re.escape(old_name)}\(.*?(?=^    def |^class |\Z)"
    )
    match = pattern.search(text)
    if match is None:
        raise ValueError(f"Lifecycle test method not found: {old_name}")

    return (
        text[:match.start()]
        + new_method.rstrip()
        + "\n\n"
        + text[match.end():]
    )


def replace_lifecycle_tests(text: str) -> str:
    accepted_method = '''    def test_exp005_is_accepted_for_paper_testing(
            self,
        ) -> None:
            record = get_experiment_lifecycle(
                "EXP-005"
            )
            self.assertEqual(
                record.stage,
                "ACCEPTED_FOR_PAPER_TESTING",
            )
            self.assertEqual(
                record.market_name,
                "NQ / MNQ futures",
            )
            self.assertEqual(
                record.timeframe,
                "5 minutes",
            )
            self.assertIsNotNone(
                record.preregistration_file
            )
    '''

    acceptance_method = '''    def test_exp005_lifecycle_records_review_acceptance(
            self,
        ) -> None:
            record = get_experiment_lifecycle(
                "EXP-005"
            )
            self.assertIn(
                "12 locked operational-quality",
                record.stage_reason,
            )
            self.assertIn(
                "12 calendar weeks",
                record.next_action,
            )
            self.assertIn(
                "40 completed NQ",
                record.next_action,
            )
            self.assertIn(
                "paper-only",
                record.next_action.lower(),
            )
    '''

    updated = _replace_test_method(
        text,
        old_name="test_exp005_is_in_review",
        new_name="test_exp005_is_accepted_for_paper_testing",
        new_method=accepted_method,
    )
    updated = _replace_test_method(
        updated,
        old_name="test_exp005_lifecycle_records_full_pass",
        new_name="test_exp005_lifecycle_records_review_acceptance",
        new_method=acceptance_method,
    )
    return updated


def replace_research_plan(text: str) -> str:
    if "accepted for a locked paper-only NQ/MNQ observation" in text:
        return text

    marker = '    print("Current project milestone")'
    marker_index = text.find(marker)
    if marker_index < 0:
        raise ValueError("Research-plan milestone heading was not found.")

    pattern = re.compile(
        r'(?ms)^    print\(\n'
        r'        "EXP-003 continues automatic paper testing\. "'
        r'.*?^    \)\n'
    )
    match = pattern.search(text, marker_index)
    if match is None:
        raise ValueError("Research-plan milestone paragraph was not found.")

    replacement = '''    print(
        "EXP-003 continues automatic paper testing. "
        "EXP-004 remains a rejected QQQ basic-ORB result. "
        "EXP-005 passed its protected quick transfer, full "
        "validation and all 12 read-only review checks, and is "
        "accepted for a locked paper-only NQ/MNQ observation. "
        "The next implementation uses completed daily Quantower "
        "exports and requires both 12 calendar weeks and 40 "
        "completed NQ paper trades. No live orders are authorized."
    )
'''
    return text[:match.start()] + replacement + text[match.end():]


def main() -> None:
    review = verify_local_exp005_review_decision()
    validate_exp005_paper_testing_plan()

    if review["evaluation"]["decision"] != "ACCEPT_FOR_PAPER_TESTING":
        raise RuntimeError("EXP-005 review did not authorize paper testing.")

    updates: list[tuple[Path, Callable[[str], str]]] = [
        (PROJECT_DIR / "experiment_lifecycle.py", replace_lifecycle),
        (
            PROJECT_DIR / "tests" / "test_experiment_lifecycle.py",
            replace_lifecycle_tests,
        ),
        (PROJECT_DIR / "show_research_plan.py", replace_research_plan),
    ]

    prepared: list[tuple[Path, str, str]] = []
    for path, transform in updates:
        if not path.exists():
            raise FileNotFoundError(path)
        current = path.read_text(encoding="utf-8")
        updated = transform(current)
        prepared.append((path, current, updated))

    for path, current, updated in prepared:
        if updated != current:
            _atomic_write(path, updated)
            print(f"Updated: {path.name}")
        else:
            print(f"Already updated: {path.name}")

    print()
    print("EXP-005 is formally accepted for paper testing.")
    print("Research, review and historical results remain frozen.")
    print("No paper trades have been generated yet.")


if __name__ == "__main__":
    main()
