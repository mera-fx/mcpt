from __future__ import annotations
from copy import deepcopy
import unittest
from exp016_audit_result import get_exp016_audit_freeze, validate_exp016_audit_freeze, verify_local_exp016_audit_outputs, verify_tracked_exp016_audit_freeze

class Exp016AuditResultTests(unittest.TestCase):
    def test_freeze_valid(self): validate_exp016_audit_freeze(); verify_tracked_exp016_audit_freeze()
    def test_local_outputs_match(self): self.assertEqual(verify_local_exp016_audit_outputs()["classification"],"NOT_QUALIFIED")
    def test_clean_structure_and_failed_equivalence_visible(self):
        i=get_exp016_audit_freeze()["interpretation"]
        self.assertTrue(i["vendor_files_structurally_clean"]); self.assertTrue(i["cross_source_coverage_below_locked_threshold"]); self.assertFalse(i["qualified_as_supplementary_source"])
    def test_no_ground_truth_overclaim(self):
        i=get_exp016_audit_freeze()["interpretation"]
        self.assertFalse(i["london_nq_f_inaccurate_claimed"]); self.assertFalse(i["quantower_proven_as_ground_truth"]); self.assertFalse(i["quantower_replaced"])
    def test_mutation_rejected(self):
        r=get_exp016_audit_freeze(); r["classification"]="SUPPLEMENTARY_ONLY"
        with self.assertRaisesRegex(ValueError,"identity"): validate_exp016_audit_freeze(r)
    def test_hash_mutation_rejected(self):
        r=deepcopy(get_exp016_audit_freeze()); r["interpretation"]["qualified_as_supplementary_source"]=True
        with self.assertRaisesRegex(ValueError,"canonical"): validate_exp016_audit_freeze(r)

if __name__=="__main__": unittest.main()
