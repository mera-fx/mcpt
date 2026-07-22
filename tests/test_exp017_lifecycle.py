import unittest
from experiment_lifecycle import get_experiment_lifecycle

class Exp017LifecycleTests(unittest.TestCase):
    def test_exp017_review(self):
        r = get_experiment_lifecycle("EXP-017")
        self.assertEqual(r.stage, "REVIEW")
        self.assertIn("access_incomplete", r.stage_reason.lower())
        self.assertIn("exp-018", r.next_action.lower())
    def test_exp018_preregistered(self):
        r = get_experiment_lifecycle("EXP-018")
        self.assertEqual(r.stage, "PRE_REGISTERED")
        self.assertEqual(
            r.strategy_name,
            "databento_exact_contract_qualification",
        )
        self.assertIn("implementation", r.next_action.lower())
    def test_exp016_review(self):
        self.assertEqual(
            get_experiment_lifecycle("EXP-016").stage,
            "REVIEW",
        )

if __name__ == "__main__":
    unittest.main()
