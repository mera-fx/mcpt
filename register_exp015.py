from __future__ import annotations

import ast
from pathlib import Path

from exp014_behaviour_result import verify_local_exp014_behaviour_result
from exp015_preregistration import validate_exp015_preregistration
from experiment_lifecycle import get_experiment_lifecycle


PROJECT_DIR = Path(__file__).resolve().parent
LIFECYCLE_FILE = PROJECT_DIR / "experiment_lifecycle.py"


EXP015_BLOCK = r'''

    "EXP-015": ExperimentLifecycle(
        experiment_id="EXP-015",
        experiment_name=(
            "London Strategic Edge NQ/MNQ Data-Source Qualification"
        ),
        hypothesis=(
            "London Strategic Edge may provide identifiable, structurally "
            "complete and sufficiently consistent one-minute NQ/MNQ history "
            "for new research when compared with the frozen Quantower reference."
        ),
        stage="PRE_REGISTERED",
        stage_reason=(
            "The catalog-first identity audit, fixed DST, holiday and roll "
            "sample windows, structural measurements, cross-source comparisons "
            "and exact frozen-strategy replay diagnostics were locked before "
            "accessing the vendor futures catalog or downloading history."
        ),
        next_action=(
            "Implement and commit a protected preflight and catalog-only audit. "
            "Do not download historical bars until NQ/MNQ identity, timestamp, "
            "contract and roll methodology are resolved. Keep all prior data "
            "and results frozen and never store the API key."
        ),
        market_name="NQ / MNQ futures",
        timeframe="One-minute historical data-source qualification",
        strategy_name="london_strategic_edge_data_qualification",
        preregistration_file=Path(
            "research/EXP-015_preregistration.md"
        ),
    ),
'''


def _atomic_write(path: Path, text: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def add_exp015_lifecycle(text: str) -> str:
    if '"EXP-015": ExperimentLifecycle(' in text:
        return text
    normalize_start = text.find("\ndef normalize_experiment_id")
    if normalize_start < 0:
        raise RuntimeError("Lifecycle normalize function was not found.")
    registry_end = text.rfind("\n}", 0, normalize_start)
    if registry_end < 0:
        raise RuntimeError("Lifecycle registry ending was not found.")
    updated = text[:registry_end] + EXP015_BLOCK + text[registry_end:]
    ast.parse(updated)
    return updated


def main() -> None:
    validate_exp015_preregistration()
    verify_local_exp014_behaviour_result()

    expected = {
        "EXP-005": "ACCEPTED_FOR_PAPER_TESTING",
        "EXP-006": "REJECTED",
        "EXP-007": "REJECTED",
        "EXP-008": "REJECTED",
        "EXP-009": "REVIEW",
        "EXP-010": "REVIEW",
        "EXP-011": "REVIEW",
        "EXP-012": "REVIEW",
        "EXP-013": "REVIEW",
        "EXP-014": "REVIEW",
    }
    for experiment_id, stage in expected.items():
        actual = get_experiment_lifecycle(experiment_id).stage
        if actual != stage:
            raise RuntimeError(
                f"{experiment_id} must remain {stage}; found {actual}."
            )

    original = LIFECYCLE_FILE.read_text(encoding="utf-8")
    updated = add_exp015_lifecycle(original)
    if updated == original:
        print("EXP-015 is already registered.")
    else:
        _atomic_write(LIFECYCLE_FILE, updated)
        print("Registered EXP-015 as PRE_REGISTERED.")

    print("London Strategic Edge catalog and history have not been accessed.")
    print("NQ/MNQ symbols, contract type and roll method remain unresolved.")
    print("Six fixed sample windows are locked.")
    print("Frozen EXP-005 through EXP-014 data and results remain unchanged.")
    print("No API key was read, printed or written.")
    print("No paper or live trading is authorized.")


if __name__ == "__main__":
    main()
