from __future__ import annotations

import unittest

from experiment_lifecycle import (
    get_experiment_lifecycle,
)


class Exp007LifecycleTests(
    unittest.TestCase
):
    def test_exp007_is_preregistered(
        self,
    ) -> None:
        record = get_experiment_lifecycle(
            "EXP-007"
        )
        self.assertEqual(
            record.stage,
            "PRE_REGISTERED",
        )
        self.assertEqual(
            record.strategy_name,
            "fixed_30m_long_only_1r_orb",
        )
        self.assertIn(
            "Do not optimize",
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
        self.assertEqual(
            exp005.stage,
            "ACCEPTED_FOR_PAPER_TESTING",
        )
        self.assertEqual(
            exp006.stage,
            "REJECTED",
        )


if __name__ == "__main__":
    unittest.main()
