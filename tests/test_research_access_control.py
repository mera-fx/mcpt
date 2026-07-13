from __future__ import annotations

import unittest
from types import SimpleNamespace

from research_access_control import (
    assert_full_research_allowed,
)


class ResearchAccessControlTests(
    unittest.TestCase
):
    def test_legacy_experiments_are_not_blocked(
        self,
    ) -> None:
        config = SimpleNamespace(
            experiment_id="EXP-001"
        )
        lifecycle = SimpleNamespace(
            stage="REJECTED"
        )

        assert_full_research_allowed(
            config,
            lifecycle,
        )

    def test_review_exp003_is_frozen(
        self,
    ) -> None:
        config = SimpleNamespace(
            experiment_id="EXP-003"
        )
        lifecycle = SimpleNamespace(
            stage="REVIEW"
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "results are frozen",
        ):
            assert_full_research_allowed(
                config,
                lifecycle,
            )

    def test_accepted_exp003_is_still_frozen(
        self,
    ) -> None:
        config = SimpleNamespace(
            experiment_id="EXP-003"
        )
        lifecycle = SimpleNamespace(
            stage=(
                "ACCEPTED_FOR_PAPER_TESTING"
            )
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "results are frozen",
        ):
            assert_full_research_allowed(
                config,
                lifecycle,
            )

    def test_exp004_generic_runner_is_blocked(
        self,
    ) -> None:
        config = SimpleNamespace(
            experiment_id="EXP-004"
        )
        lifecycle = SimpleNamespace(
            stage="REJECTED"
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "frozen rejected",
        ):
            assert_full_research_allowed(
                config,
                lifecycle,
            )

    def test_exp005_generic_runner_is_blocked(
        self,
    ) -> None:
        config = SimpleNamespace(
            experiment_id="EXP-005"
        )
        lifecycle = SimpleNamespace(
            stage="PRE_REGISTERED"
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "no-optimization NQ/MNQ",
        ):
            assert_full_research_allowed(
                config,
                lifecycle,
            )


if __name__ == "__main__":
    unittest.main()
