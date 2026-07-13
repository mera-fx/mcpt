from __future__ import annotations

import os

from experiment_config import ResearchConfig
from experiment_lifecycle import ExperimentLifecycle


EXP003_FULL_VALIDATION_ENVIRONMENT_KEY = (
    "EXP003_FULL_VALIDATION_AUTHORIZED"
)

EXP003_POST_VALIDATION_LOCKED_STAGES = {
    "REVIEW",
    "REJECTED",
    "ACCEPTED_FOR_PAPER_TESTING",
}


def assert_full_research_allowed(
    config: ResearchConfig,
    lifecycle: ExperimentLifecycle,
) -> None:
    """Protect experiment-specific research disclosure rules."""

    if config.experiment_id == "EXP-004":
        raise RuntimeError(
            "EXP-004 uses a session-aware intraday research engine. "
            "Direct use of run_research_lab.py is blocked while its "
            f"lifecycle stage is {lifecycle.stage}. Download only "
            "the locked in-sample data with "
            "download_exp004_qqq_is_data.py, then run "
            "run_exp004_quick_screen.py. OOS access requires a "
            "separate protected full-validation workflow."
        )

    if config.experiment_id != "EXP-003":
        return

    if lifecycle.stage == "FULL_VALIDATION":
        if (
            os.environ.get(
                EXP003_FULL_VALIDATION_ENVIRONMENT_KEY
            )
            == "1"
        ):
            return

        raise RuntimeError(
            "EXP-003 is ready for full validation, but direct use "
            "of run_research_lab.py is blocked. Run "
            "run_exp003_full_validation.py exactly once so the "
            "locked gates are evaluated and a decision is recorded."
        )

    if lifecycle.stage in (
        EXP003_POST_VALIDATION_LOCKED_STAGES
    ):
        raise RuntimeError(
            "EXP-003 research results are frozen while its "
            f"lifecycle stage is {lifecycle.stage}. Do not rerun "
            "the research engine. Use the recorded result files "
            "and the protected review workflow instead."
        )

    raise RuntimeError(
        "EXP-003 out-of-sample research is locked while its "
        f"lifecycle stage is {lifecycle.stage}. Run "
        "run_exp003_quick_screen.py instead. Full validation "
        "becomes available only after every quick-screen gate passes."
    )
