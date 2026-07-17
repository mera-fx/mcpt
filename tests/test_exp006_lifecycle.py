from __future__ import annotations

import unittest

from experiment_lifecycle import (
    get_experiment_lifecycle,
)


class Exp006LifecycleTests(
    unittest.TestCase
):
    def test_exp006_is_rejected(
        self,
    ) -> None:
        record = get_experiment_lifecycle(
            "EXP-006"
        )
        self.assertEqual(
            record.stage,
            "REJECTED",
        )
        self.assertIn(
            "0.017995",
            record.stage_reason,
        )
        self.assertIn(
            "0.020000",
            record.stage_reason,
        )

    def test_exp005_remains_accepted_control(
        self,
    ) -> None:
        record = get_experiment_lifecycle(
            "EXP-005"
        )
        self.assertEqual(
            record.stage,
            "ACCEPTED_FOR_PAPER_TESTING",
        )


if __name__ == "__main__":
    unittest.main()
