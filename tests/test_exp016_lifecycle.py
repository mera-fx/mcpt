from __future__ import annotations
import unittest
from experiment_lifecycle import get_experiment_lifecycle
from register_exp016 import add_exp016_lifecycle

class Exp016LifecycleTests(unittest.TestCase):
    def test_exp016_is_preregistered(self):
        r=get_experiment_lifecycle('EXP-016')
        self.assertEqual(r.stage,'PRE_REGISTERED')
        self.assertEqual(r.strategy_name,'nq_f_data_sample_qualification')
        self.assertIn('six-request',r.next_action.lower())
        self.assertIn('do not rerun the catalog',r.next_action.lower())
    def test_exp015_and_prior_are_frozen(self):
        expected={"EXP-005":"ACCEPTED_FOR_PAPER_TESTING","EXP-006":"REJECTED","EXP-007":"REJECTED","EXP-008":"REJECTED",
                  "EXP-009":"REVIEW","EXP-010":"REVIEW","EXP-011":"REVIEW","EXP-012":"REVIEW","EXP-013":"REVIEW","EXP-014":"REVIEW","EXP-015":"REVIEW"}
        for experiment_id,stage in expected.items():
            self.assertEqual(get_experiment_lifecycle(experiment_id).stage,stage)
    def test_registration_is_idempotent(self):
        source='"EXP-016": ExperimentLifecycle(\n'
        self.assertEqual(add_exp016_lifecycle(source),source)

if __name__=='__main__':
    unittest.main()
