from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ALLOWED_STAGES = (
    "IDEA",
    "PRE_REGISTERED",
    "QUICK_SCREEN",
    "FULL_VALIDATION",
    "REVIEW",
    "REJECTED",
    "ACCEPTED_FOR_PAPER_TESTING",
)

STAGE_ORDER = {
    stage: position
    for position, stage in enumerate(
        ALLOWED_STAGES
    )
}


@dataclass(frozen=True)
class ExperimentLifecycle:
    experiment_id: str
    experiment_name: str
    hypothesis: str
    stage: str
    stage_reason: str
    next_action: str
    market_name: str = "BTCUSDT spot"
    timeframe: str = "1 hour"
    strategy_name: str = "Not implemented"
    preregistration_file: Path | None = None

    def validate(self) -> None:
        if self.stage not in ALLOWED_STAGES:
            raise ValueError(
                f"Invalid stage '{self.stage}' for "
                f"{self.experiment_id}. Allowed values: "
                f"{list(ALLOWED_STAGES)}"
            )

        if not self.experiment_id.strip():
            raise ValueError(
                "experiment_id cannot be empty."
            )

        if not self.experiment_name.strip():
            raise ValueError(
                "experiment_name cannot be empty."
            )

        if not self.hypothesis.strip():
            raise ValueError(
                "hypothesis cannot be empty."
            )

        if not self.stage_reason.strip():
            raise ValueError(
                "stage_reason cannot be empty."
            )

        if not self.next_action.strip():
            raise ValueError(
                "next_action cannot be empty."
            )

    def to_dict(self) -> dict[str, Any]:
        self.validate()

        record = asdict(self)

        if self.preregistration_file is not None:
            record["preregistration_file"] = str(
                self.preregistration_file
            )

        return record


EXPERIMENT_LIFECYCLE: dict[
    str,
    ExperimentLifecycle,
] = {
    "EXP-001": ExperimentLifecycle(
        experiment_id="EXP-001",
        experiment_name=(
            "BTCUSDT Hourly Donchian Breakout"
        ),
        hypothesis=(
            "BTCUSDT may exhibit trend persistence that can be "
            "captured by a closing-price Donchian breakout."
        ),
        stage="REJECTED",
        stage_reason=(
            "Weak and borderline in-sample evidence, MCPT "
            "p-value 0.0529, negative fixed out-of-sample "
            "performance and worse walk-forward results."
        ),
        next_action=(
            "Keep as a completed negative result. Do not rescue "
            "the strategy through additional tuning."
        ),
        strategy_name="donchian_breakout",
    ),
    "EXP-002": ExperimentLifecycle(
        experiment_id="EXP-002",
        experiment_name=(
            "BTCUSDT Hourly Long-Only Z-Score Mean Reversion"
        ),
        hypothesis=(
            "Large negative hourly deviations from a rolling "
            "mean may revert upward strongly enough to support "
            "a long-only strategy."
        ),
        stage="REJECTED",
        stage_reason=(
            "The best in-sample Profit Factor was below 1.0. "
            "Fixed and walk-forward versions lost money and "
            "displayed adverse payoff and tail-loss behaviour."
        ),
        next_action=(
            "Keep as a completed negative result. Do not alter "
            "parameters or exits to rehabilitate it."
        ),
        strategy_name="zscore_mean_reversion_long",
    ),
    "EXP-003": ExperimentLifecycle(
        experiment_id="EXP-003",
        experiment_name=(
            "BTCUSDT Hourly Volatility-Compression Breakout"
        ),
        hypothesis=(
            "After an unusually quiet realized-volatility "
            "regime, an upside range breakout may be followed "
            "by continuation strong enough to overcome costs."
        ),
        stage="ACCEPTED_FOR_PAPER_TESTING",
        stage_reason=(
            "The protected full validation passed every locked "
            "gate, and the corrected read-only review v2 passed "
            "all ten operational-quality checks. The original "
            "review defect was a documented field-name mismatch; "
            "no research result was rerun or changed."
        ),
        next_action=(
            "Build and operate a paper-only simulator using the "
            "fixed preregistered parameters. Keep all EXP-003 "
            "research outputs frozen and do not alter the strategy "
            "under this experiment ID."
        ),
        strategy_name=(
            "volatility_compression_breakout_long"
        ),
        preregistration_file=Path(
            "research/EXP-003_preregistration.md"
        ),
    ),
    "EXP-004": ExperimentLifecycle(
        experiment_id="EXP-004",
        experiment_name=(
            "QQQ 5-Minute Opening Range Breakout"
        ),
        hypothesis=(
            "After QQQ establishes its opening range, the first "
            "confirmed break outside that range may continue far "
            "enough during the same regular session to overcome "
            "realistic intraday trading costs."
        ),
        stage="REJECTED",
        stage_reason=(
            "The protected in-sample quick screen failed three "
            "locked gates. Best trade Profit Factor was 1.0463 "
            "versus the required 1.10, fixed-parameter Profit "
            "Factor was 1.0211 versus 1.05, and the session-aware "
            "25-permutation MCPT p-value was 0.3077 versus 0.20. "
            "The test contained 973 completed trades and zero "
            "included invalid sessions, so the negative result "
            "was not caused by an undersized or invalid sample."
        ),
        next_action=(
            "Preserve EXP-004 as a completed negative result. "
            "Keep 2023–2025 QQQ OOS results locked and do not "
            "change its rules or gates. More structured ORB "
            "variants require new experiment IDs. EXP-005 may "
            "test only the unchanged fixed ORB rules on NQ/MNQ."
        ),
        market_name="QQQ ETF",
        timeframe="5 minutes",
        strategy_name="opening_range_breakout",
        preregistration_file=Path(
            "research/EXP-004_preregistration.md"
        ),
    ),
    "EXP-005": ExperimentLifecycle(
        experiment_id="EXP-005",
        experiment_name=(
            "NQ/MNQ 5-Minute ORB Locked Transfer"
        ),
        hypothesis=(
            "The unchanged fixed EXP-004 opening-range rules may "
            "transfer from QQQ to Nasdaq-100 futures and remain "
            "profitable after contract-specific futures costs."
        ),
        stage="PRE_REGISTERED",
        stage_reason=(
            "EXP-005 is a no-optimization cross-market transfer "
            "test. Source amendment EXP-005-A1 replaced the paid "
            "source with zero-additional-cost Lucid/Rithmic "
            "front-month CSV exports before the complete quick "
            "period was exported or strategy results were viewed. "
            "Signal rules, periods, costs, MCPT and gates remain "
            "unchanged."
        ),
        next_action=(
            "Implement the protected Quantower CSV importer and "
            "then export only NQ and MNQ front-month history for "
            "2019-05-06 through 2022-12-30. Keep 2023–2025 "
            "unexported and locked unless every quick-transfer "
            "gate passes."
        ),
        market_name="NQ / MNQ futures",
        timeframe="5 minutes",
        strategy_name=(
            "opening_range_breakout_locked_transfer"
        ),
        preregistration_file=Path(
            "research/EXP-005_preregistration.md"
        ),
    ),
}


def normalize_experiment_id(
    value: str,
) -> str:
    cleaned = (
        value.strip()
        .upper()
        .replace("_", "-")
    )

    if cleaned.startswith("EXP-"):
        suffix = cleaned[4:]
    elif cleaned.startswith("EXP"):
        suffix = cleaned[3:].lstrip("-")
    else:
        suffix = cleaned

    if not suffix.isdigit():
        raise ValueError(
            "Experiment ID must look like EXP-003 or 003."
        )

    return f"EXP-{int(suffix):03d}"


def get_experiment_lifecycle(
    experiment_id: str,
    *,
    experiment_name: str | None = None,
    hypothesis: str | None = None,
    market_name: str = "Unknown market",
    timeframe: str = "Unknown timeframe",
    strategy_name: str = "Unknown strategy",
) -> ExperimentLifecycle:
    normalized = normalize_experiment_id(
        experiment_id
    )

    if normalized in EXPERIMENT_LIFECYCLE:
        record = EXPERIMENT_LIFECYCLE[
            normalized
        ]
        record.validate()
        return record

    fallback = ExperimentLifecycle(
        experiment_id=normalized,
        experiment_name=(
            experiment_name
            or f"Unregistered {normalized}"
        ),
        hypothesis=(
            hypothesis
            or "No lifecycle hypothesis has been recorded."
        ),
        stage="IDEA",
        stage_reason=(
            "This experiment has a configuration but no explicit "
            "lifecycle record."
        ),
        next_action=(
            "Add the experiment to experiment_lifecycle.py and "
            "complete preregistration before treating results as "
            "confirmatory."
        ),
        market_name=market_name,
        timeframe=timeframe,
        strategy_name=strategy_name,
    )

    fallback.validate()
    return fallback


def list_experiment_lifecycles(
) -> list[ExperimentLifecycle]:
    records = list(
        EXPERIMENT_LIFECYCLE.values()
    )

    for record in records:
        record.validate()

    return sorted(
        records,
        key=lambda record: (
            int(record.experiment_id.split("-")[1]),
            STAGE_ORDER[record.stage],
        ),
    )


def format_stage_label(
    stage: str,
) -> str:
    if stage not in ALLOWED_STAGES:
        raise ValueError(
            f"Unknown research stage: {stage}"
        )

    return stage.replace("_", " ").title()


def validate_lifecycle_registry() -> None:
    seen_ids: set[str] = set()

    for key, record in (
        EXPERIMENT_LIFECYCLE.items()
    ):
        record.validate()

        if key != record.experiment_id:
            raise ValueError(
                f"Lifecycle key '{key}' does not match "
                f"record ID '{record.experiment_id}'."
            )

        if key in seen_ids:
            raise ValueError(
                f"Duplicate lifecycle ID: {key}"
            )

        seen_ids.add(key)


if __name__ == "__main__":
    validate_lifecycle_registry()

    print("Research lifecycle")
    print("------------------")

    for record in list_experiment_lifecycles():
        print(
            f"{record.experiment_id}: "
            f"{format_stage_label(record.stage)}"
        )
        print(
            f"  {record.experiment_name}"
        )
        print(
            f"  Next: {record.next_action}"
        )
