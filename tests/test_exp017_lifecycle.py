from __future__ import annotations
import unittest
from experiment_lifecycle import get_experiment_lifecycle

class Exp017LifecycleTests(unittest.TestCase):
    def test_exp017_is_preregistered(self):
        r=get_experiment_lifecycle("EXP-017")
        self.assertEqual(r.stage,"PRE_REGISTERED")
        self.assertEqual(r.strategy_name,"exact_nq_contract_data_benchmark")
        self.assertIn("source-lock",r.next_action.lower())
        self.assertIn("before any bar",r.next_action.lower())
    def test_exp016_is_review(self): self.assertEqual(get_experiment_lifecycle("EXP-016").stage,"REVIEW")

if __name__=="__main__": unittest.main()
