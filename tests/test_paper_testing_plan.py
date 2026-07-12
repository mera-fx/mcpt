from __future__ import annotations

from copy import deepcopy
import unittest

from paper_testing_plan import (
    get_exp003_paper_testing_plan,
    validate_exp003_paper_testing_plan,
)


class PaperTestingPlanSafetyTests(
    unittest.TestCase
):
    def test_live_mode_is_rejected(
        self,
    ) -> None:
        plan = get_exp003_paper_testing_plan()
        plan["mode"] = "live"

        with self.assertRaises(ValueError):
            validate_exp003_paper_testing_plan(
                plan
            )

    def test_parameter_change_is_rejected(
        self,
    ) -> None:
        plan = get_exp003_paper_testing_plan()
        plan["fixed_parameters"][
            "compression_quantile"
        ] = 0.10

        with self.assertRaises(ValueError):
            validate_exp003_paper_testing_plan(
                plan
            )

    def test_short_observation_is_rejected(
        self,
    ) -> None:
        plan = get_exp003_paper_testing_plan()
        plan["minimum_observation"][
            "calendar_weeks"
        ] = 4

        with self.assertRaises(ValueError):
            validate_exp003_paper_testing_plan(
                plan
            )

    def test_reconciliation_must_be_exact(
        self,
    ) -> None:
        plan = get_exp003_paper_testing_plan()
        plan["operational_gates"][
            "signal_state_match_percent"
        ] = 99.0

        with self.assertRaises(ValueError):
            validate_exp003_paper_testing_plan(
                plan
            )


if __name__ == "__main__":
    unittest.main()
