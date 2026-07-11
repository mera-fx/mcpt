from __future__ import annotations

import os
import unittest
from dataclasses import replace
from unittest.mock import patch

from experiment_config import load_experiment
from experiment_lifecycle import (
    get_experiment_lifecycle,
)
from research_access_control import (
    EXP003_FULL_VALIDATION_ENVIRONMENT_KEY,
    assert_full_research_allowed,
)


class ResearchAccessControlTests(unittest.TestCase):
    def test_preregistered_exp003_is_blocked(
        self,
    ) -> None:
        config = load_experiment("EXP-003")
        lifecycle = replace(
            get_experiment_lifecycle(
                "EXP-003"
            ),
            stage="PRE_REGISTERED",
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "out-of-sample research is locked",
        ):
            assert_full_research_allowed(
                config,
                lifecycle,
            )

    def test_full_validation_direct_runner_is_blocked(
        self,
    ) -> None:
        config = load_experiment("EXP-003")
        lifecycle = get_experiment_lifecycle(
            "EXP-003"
        )

        with patch.dict(
            os.environ,
            {},
            clear=False,
        ):
            os.environ.pop(
                EXP003_FULL_VALIDATION_ENVIRONMENT_KEY,
                None,
            )

            with self.assertRaisesRegex(
                RuntimeError,
                "direct use",
            ):
                assert_full_research_allowed(
                    config,
                    lifecycle,
                )

    def test_full_validation_wrapper_is_allowed(
        self,
    ) -> None:
        config = load_experiment("EXP-003")
        lifecycle = get_experiment_lifecycle(
            "EXP-003"
        )

        with patch.dict(
            os.environ,
            {
                EXP003_FULL_VALIDATION_ENVIRONMENT_KEY: "1",
            },
        ):
            assert_full_research_allowed(
                config,
                lifecycle,
            )

    def test_review_stage_is_allowed(
        self,
    ) -> None:
        config = load_experiment("EXP-003")
        lifecycle = replace(
            get_experiment_lifecycle(
                "EXP-003"
            ),
            stage="REVIEW",
        )

        assert_full_research_allowed(
            config,
            lifecycle,
        )

    def test_legacy_experiments_are_not_blocked(
        self,
    ) -> None:
        config = load_experiment("EXP-002")
        lifecycle = get_experiment_lifecycle(
            "EXP-002"
        )

        assert_full_research_allowed(
            config,
            lifecycle,
        )


if __name__ == "__main__":
    unittest.main()
