from __future__ import annotations

import unittest

from experiment_lifecycle import (
    get_experiment_lifecycle,
)


class Exp008LifecycleTests(
    unittest.TestCase
):
    def test_exp008_is_preregistered(
        self,
    ) -> None:
        record = get_experiment_lifecycle(
            "EXP-008"
        )
        self.assertEqual(
            record.stage,
            "PRE_REGISTERED",
        )
        self.assertEqual(
            record.strategy_name,
            "structured_long_only_orb_exit_geometry",
        )
        self.assertIn(
            "Commit the implementation",
            record.next_action,
        )

    def test_prior_experiments_remain_frozen(
        self,
    ) -> None:
        exp005 = get_experiment_lifecycle(
            "EXP-005"
        )
        exp006 = get_experiment_lifecycle(
            "EXP-006"
        )
        exp007 = get_experiment_lifecycle(
            "EXP-007"
        )

        self.assertEqual(
            exp005.stage,
            "ACCEPTED_FOR_PAPER_TESTING",
        )
        self.assertEqual(
            exp006.stage,
            "REJECTED",
        )
        self.assertEqual(
            exp007.stage,
            "REJECTED",
        )


if __name__ == "__main__":
    unittest.main()
