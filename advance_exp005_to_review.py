from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

from exp005_full_validation_result import verify_local_full_validation_decision

PROJECT_DIR = Path(__file__).resolve().parent


def _atomic_write(path: Path, text: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def _exp005_block(text: str) -> tuple[int, int, str]:
    start = text.find('"EXP-005": ExperimentLifecycle(')
    if start < 0:
        raise ValueError("EXP-005 lifecycle block was not found.")
    marker = 'preregistration_file=Path('
    marker_position = text.find(marker, start)
    if marker_position < 0:
        raise ValueError("EXP-005 lifecycle preregistration field was not found.")

    closing_marker = "\n    ),\n}"
    closing = text.find(closing_marker, marker_position)

    if closing < 0:
        # Compact-format fallback for a one-line registry.
        closing_marker = "), ), }"
        closing = text.find(closing_marker, marker_position)

    if closing < 0:
        raise ValueError("EXP-005 lifecycle block ending was not found.")

    end = closing + len(closing_marker) - 2
    return start, end, text[start:end]


def replace_lifecycle(text: str) -> str:
    start, end, block = _exp005_block(text)
    if 'stage="REVIEW"' in block and "1,000-permutation NQ MCPT" in block:
        return text

    block, stage_count = re.subn(
        r'stage="FULL_VALIDATION"',
        'stage="REVIEW"',
        block,
        count=1,
    )
    if stage_count != 1:
        raise ValueError("EXP-005 lifecycle stage could not be updated.")

    reason = """stage_reason=(
            "The protected 2023–2025 confirmation full validation "
            "passed every locked gate. NQ Profit Factor was 1.1811, "
            "MNQ Profit Factor was 1.1629, NQ net profit was "
            "$116,715.00, MNQ net profit was $10,607.50, and the "
            "1,000-permutation NQ MCPT p-value was 0.037962. All "
            "three NQ calendar years were profitable, no optimization "
            "was performed, and zero invalid or front-month-mismatch "
            "sessions were included."
        )"""
    block, reason_count = re.subn(
        r'stage_reason=\(.*?\),\s*next_action=\(',
        reason + ",\n        next_action=(",
        block,
        count=1,
        flags=re.DOTALL,
    )
    if reason_count != 1:
        raise ValueError("EXP-005 lifecycle reason could not be updated.")

    next_action = """next_action=(
            "Freeze the full-validation result and run the separate "
            "read-only operational-quality review. Do not rerun the "
            "strategy, MCPT, quick transfer or confirmation import. "
            "A passing review may advance only to paper testing under "
            "the unchanged fixed rules."
        )"""
    block, action_count = re.subn(
        r'next_action=\(.*?\),\s*market_name=',
        next_action + ",\n        market_name=",
        block,
        count=1,
        flags=re.DOTALL,
    )
    if action_count != 1:
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
        raise ValueError(f"Lifecycle test method {old_name!r} was not found.")
    return text[:match.start()] + new_method.rstrip() + "\n\n" + text[match.end():]


def replace_lifecycle_tests(text: str) -> str:
    review_method = """    def test_exp005_is_in_review(
            self,
        ) -> None:
            record = get_experiment_lifecycle(
                "EXP-005"
            )
            self.assertEqual(
                record.stage,
                "REVIEW",
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
    """
    full_pass_method = """    def test_exp005_lifecycle_records_full_pass(
            self,
        ) -> None:
            record = get_experiment_lifecycle(
                "EXP-005"
            )
            self.assertIn(
                "full validation",
                record.stage_reason.lower(),
            )
            self.assertIn(
                "0.037962",
                record.stage_reason,
            )
            self.assertIn(
                "read-only",
                record.next_action.lower(),
            )
    """
    updated = _replace_test_method(
        text,
        old_name="test_exp005_is_in_full_validation",
        new_name="test_exp005_is_in_review",
        new_method=review_method,
    )
    return _replace_test_method(
        updated,
        old_name="test_exp005_lifecycle_records_quick_pass",
        new_name="test_exp005_lifecycle_records_full_pass",
        new_method=full_pass_method,
    )


def replace_research_plan(text: str) -> str:
    unique_phrase = "EXP-005 passed its protected 2023–2025 full"
    if unique_phrase in text:
        return text
    marker_index = text.find('    print("Current project milestone")')
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
    replacement = """    print(
        "EXP-003 continues automatic paper testing. "
        "EXP-004 remains a rejected QQQ basic-ORB result. "
        "EXP-005 passed its protected 2023–2025 full "
        "validation with no optimization and has advanced "
        "to a separate read-only operational review. "
        "No strategy, MCPT or data workflow may be rerun. "
        "Structured ORB optimization remains a separate "
        "future path."
    )
"""
    return text[:match.start()] + replacement + text[match.end():]


def main() -> None:
    result = verify_local_full_validation_decision()
    if result["evaluation"]["decision"] != "PASS_TO_REVIEW":
        raise RuntimeError("EXP-005 did not pass to review.")

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
        prepared.append((path, current, transform(current)))

    # Transactional: write only after every transform succeeds.
    for path, current, updated in prepared:
        if updated != current:
            _atomic_write(path, updated)
            print(f"Updated: {path.name}")
        else:
            print(f"Already updated: {path.name}")

    print()
    print("EXP-005 is formally advanced to REVIEW.")
    print("The quick-transfer and full-validation results remain frozen.")


if __name__ == "__main__":
    main()
