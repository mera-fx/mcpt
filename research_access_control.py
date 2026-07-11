from __future__ import annotations

from experiment_config import ResearchConfig
from experiment_lifecycle import ExperimentLifecycle


EXP003_FULL_RESEARCH_ALLOWED_STAGES = {
    "FULL_VALIDATION",
    "REVIEW",
    "ACCEPTED_FOR_PAPER_TESTING",
}


def assert_full_research_allowed(
    config: ResearchConfig,
    lifecycle: ExperimentLifecycle,
) -> None:
    """Prevent premature EXP-003 out-of-sample disclosure."""

    if config.experiment_id != "EXP-003":
        return

    if lifecycle.stage in (
        EXP003_FULL_RESEARCH_ALLOWED_STAGES
    ):
        return

    raise RuntimeError(
        "EXP-003 out-of-sample research is locked while its "
        f"lifecycle stage is {lifecycle.stage}. Run "
        "run_exp003_quick_screen.py instead. The normal research "
        "runner becomes available only after every quick-screen "
        "gate passes and the lifecycle advances to FULL_VALIDATION."
    )
