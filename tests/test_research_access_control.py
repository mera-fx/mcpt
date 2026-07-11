from __future__ import annotations

import unittest
from dataclasses import replace

from experiment_config import load_experiment
from experiment_lifecycle import (
    get_experiment_lifecycle,
)
from research_access_control import (
    assert_full_research_allowed,
)


class ResearchAccessControlTests(unittest.TestCase):
    def test_preregistered_exp003_is_blocked(
        self,
    ) -> None:
        config = load_experiment("EXP-003")
        lifecycle = get_experiment_lifecycle(
            "EXP-003"
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "out-of-sample research is locked",
        ):
            assert_full_research_allowed(
                config,
                lifecycle,
            )

    def test_full_validation_exp003_is_allowed(
        self,
    ) -> None:
        config = load_experiment("EXP-003")
        lifecycle = replace(
            get_experiment_lifecycle(
                "EXP-003"
            ),
            stage="FULL_VALIDATION",
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
