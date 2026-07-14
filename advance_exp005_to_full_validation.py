from __future__ import annotations

from pathlib import Path
import re

from exp005_quick_transfer_result import (
    verify_local_quick_transfer_decision,
)


PROJECT_DIR = Path(__file__).resolve().parent
LIFECYCLE_FILE = PROJECT_DIR / "experiment_lifecycle.py"
LIFECYCLE_TEST_FILE = (
    PROJECT_DIR
    / "tests"
    / "test_experiment_lifecycle.py"
)
PLAN_FILE = PROJECT_DIR / "show_research_plan.py"


FULL_VALIDATION_BLOCK = '''    "EXP-005": ExperimentLifecycle(
        experiment_id="EXP-005",
        experiment_name=(
            "NQ/MNQ 5-Minute ORB Locked Transfer"
        ),
        hypothesis=(
            "The unchanged fixed EXP-004 opening-range rules may "
            "transfer from QQQ to Nasdaq-100 futures and remain "
            "profitable after contract-specific futures costs."
        ),
        stage="FULL_VALIDATION",
        stage_reason=(
            "The protected 2019–2022 quick transfer passed all ten "
            "locked gates. NQ Profit Factor was 1.1340, MNQ Profit "
            "Factor was 1.1202, NQ net profit was $94,660.00, MNQ "
            "net profit was $8,549.50, and the 25-permutation NQ "
            "MCPT p-value was 0.076923. No optimization was performed, "
            "zero invalid or roll-switch sessions were included, and "
            "the 2023–2025 confirmation period was not accessed."
        ),
        next_action=(
            "Freeze the quick-transfer result, export NQ and MNQ "
            "provider-front-month one-minute data once for 2023-01-03 "
            "through 2025-12-31, run the protected confirmation "
            "importer, then execute the preregistered full validation "
            "with 1,000 NQ permutations. Do not rerun the quick transfer."
        ),
        market_name="NQ / MNQ futures",
        timeframe="5 minutes",
        strategy_name=(
            "opening_range_breakout_locked_transfer"
        ),
        preregistration_file=Path(
            "research/EXP-005_preregistration.md"
        ),
    ),'''


def replace_exp005_lifecycle_block(
    text: str,
) -> str:
    start_marker = (
        '    "EXP-005": ExperimentLifecycle('
    )
    start = text.find(start_marker)

    if start < 0:
        raise ValueError(
            "EXP-005 lifecycle block was not found."
        )

    next_function = text.find(
        "\n\ndef normalize_experiment_id(",
        start,
    )

    if next_function < 0:
        raise ValueError(
            "Lifecycle function boundary was not found."
        )

    block_region = text[start:next_function]
    closing = block_region.rfind("\n    ),")

    if closing < 0:
        raise ValueError(
            "EXP-005 lifecycle block closing was not found."
        )

    end = start + closing + len("\n    ),")

    old_block = text[start:end]

    if 'stage="FULL_VALIDATION"' in old_block:
        return text

    required = (
        'stage="PRE_REGISTERED"',
        "Lucid/Rithmic",
        "2019-05-06 through 2022-12-30",
        "Keep 2023–2025 unexported",
    )

    for phrase in required:
        if phrase not in old_block:
            raise ValueError(
                "Existing EXP-005 lifecycle block does not "
                f"match the expected pre-result state: {phrase}"
            )

    return (
        text[:start]
        + FULL_VALIDATION_BLOCK
        + text[end:]
    )


def _replace_test_method(
    text: str,
    *,
    old_name: str,
    new_name: str,
    new_method: str,
) -> str:
    if new_name in text:
        return text

    pattern = re.compile(
        rf"(?ms)^    def {re.escape(old_name)}\("
        rf".*?(?=^    def |^class |\Z)"
    )
    match = pattern.search(text)

    if match is None:
        raise ValueError(
            f"Lifecycle test method '{old_name}' "
            "was not found."
        )

    return (
        text[:match.start()]
        + new_method.rstrip()
        + "\n\n"
        + text[match.end():]
    )


def replace_lifecycle_tests(
    text: str,
) -> str:
    new_quick_pass = """    def test_exp005_lifecycle_records_quick_pass(
        self,
    ) -> None:
        record = get_experiment_lifecycle(
            "EXP-005"
        )

        self.assertIn(
            "quick transfer passed",
            record.stage_reason,
        )

        self.assertIn(
            "2023-01-03",
            record.next_action,
        )

        self.assertIn(
            "1,000 NQ permutations",
            record.next_action,
        )
"""

    new_stage = """    def test_exp005_is_in_full_validation(
        self,
    ) -> None:
        record = get_experiment_lifecycle(
            "EXP-005"
        )

        self.assertEqual(
            record.stage,
            "FULL_VALIDATION",
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

    updated = _replace_test_method(
        text,
        old_name=(
            "test_exp005_lifecycle_mentions_free_source"
        ),
        new_name=(
            "test_exp005_lifecycle_records_quick_pass"
        ),
        new_method=new_quick_pass,
    )

    updated = _replace_test_method(
        updated,
        old_name="test_exp005_is_preregistered",
        new_name="test_exp005_is_in_full_validation",
        new_method=new_stage,
    )

    required = (
        "test_exp005_lifecycle_records_quick_pass",
        "test_exp005_is_in_full_validation",
    )

    for name in required:
        if name not in updated:
            raise ValueError(
                f"Updated lifecycle test '{name}' "
                "is missing."
            )

    return updated


def replace_research_plan(
    text: str,
) -> str:
    new = """    print(
        "EXP-003 continues automatic paper testing. "
        "EXP-004 remains a rejected QQQ basic-ORB result. "
        "EXP-005 passed its protected 2019–2022 NQ/MNQ "
        "quick transfer with no optimization and has advanced "
        "to full validation. The 2023–2025 confirmation data "
        "may now be exported once and imported through the "
        "protected confirmation workflow. Structured ORB "
        "optimization remains a separate future path."
    )
"""

    if "EXP-005 passed its protected" in text:
        return text

    milestone = text.find(
        '    print("Current project milestone")'
    )

    if milestone < 0:
        raise ValueError(
            "Research-plan milestone heading was not found."
        )

    paragraph_start = text.find(
        "    print(",
        milestone
        + len(
            '    print("Current project milestone")'
        ),
    )

    if paragraph_start < 0:
        raise ValueError(
            "Research-plan milestone paragraph was not found."
        )

    pattern = re.compile(
        r"(?ms)^    print\(\n"
        r"        \"EXP-003 continues automatic paper testing\."
        r".*?^    \)\n"
    )
    match = pattern.search(
        text,
        paragraph_start,
    )

    if match is None:
        raise ValueError(
            "Expected pre-full-validation milestone "
            "paragraph was not found."
        )

    return (
        text[:match.start()]
        + new
        + text[match.end():]
    )


def _atomic_write(
    path: Path,
    text: str,
) -> None:
    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )
    temporary.write_text(
        text,
        encoding="utf-8",
    )
    temporary.replace(path)


def main() -> None:
    verify_local_quick_transfer_decision()

    updates = (
        (
            LIFECYCLE_FILE,
            replace_exp005_lifecycle_block,
        ),
        (
            LIFECYCLE_TEST_FILE,
            replace_lifecycle_tests,
        ),
        (
            PLAN_FILE,
            replace_research_plan,
        ),
    )

    prepared: list[
        tuple[Path, str, str]
    ] = []

    for path, transform in updates:
        if not path.exists():
            raise FileNotFoundError(path)

        current = path.read_text(
            encoding="utf-8"
        )
        updated = transform(current)
        prepared.append(
            (path, current, updated)
        )

    # Write only after every transformation succeeds. This prevents
    # a future formatting mismatch from leaving a partial update.
    for path, current, updated in prepared:
        if updated != current:
            _atomic_write(
                path,
                updated,
            )
            print(f"Updated: {path.name}")
        else:
            print(f"Already updated: {path.name}")

    print()
    print(
        "EXP-005 is formally advanced to FULL_VALIDATION."
    )
    print(
        "The quick-transfer result remains frozen."
    )


if __name__ == "__main__":
    main()
