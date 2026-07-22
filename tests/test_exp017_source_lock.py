from __future__ import annotations

import unittest

from exp017_source_lock import (
    LOCKED_CONTRACTS,
    get_exp017_source_set_lock,
    validate_exp017_source_set_lock,
)


class Exp017SourceSetLockTests(unittest.TestCase):
    def test_source_set_lock_is_valid(self) -> None:
        validate_exp017_source_set_lock()

    def test_locked_contracts(self) -> None:
        self.assertEqual(
            LOCKED_CONTRACTS,
            ("NQH24", "NQM24", "NQU24", "NQZ24", "NQH25", "NQM25"),
        )

    def test_lucid_rithmic_is_context_only(self) -> None:
        role = get_exp017_source_set_lock()["source_roles"]["execution_feed_context"]
        self.assertFalse(role["locked_expired_contracts_found"])
        self.assertFalse(role["exact_contract_benchmark_eligible"])
        self.assertTrue(role["execution_feed_alignment_context"])

    def test_candidate_sources_are_pending(self) -> None:
        roles = get_exp017_source_set_lock()["source_roles"]
        self.assertEqual(
            roles["historical_exact_contract_candidate"]["eligibility"],
            "PENDING_METADATA_CONFIRMATION",
        )
        self.assertEqual(
            roles["exchange_native_reference_candidate"]["eligibility"],
            "PENDING_COMMERCIAL_AND_METADATA_CONFIRMATION",
        )

    def test_london_is_excluded(self) -> None:
        excluded = get_exp017_source_set_lock()["excluded_sources"]["london_strategic_edge_nq_f"]
        self.assertFalse(excluded["included_in_exp017_benchmark"])
        self.assertFalse(excluded["reentry_after_this_lock"])

    def test_no_bar_access(self) -> None:
        record = get_exp017_source_set_lock()
        self.assertFalse(record["benchmark_bar_access_authorized"])
        self.assertFalse(record["next_metadata_only_stage"]["databento_ohlcv_request_authorized"])
        self.assertFalse(record["next_metadata_only_stage"]["cme_datamine_file_download_authorized"])

    def test_mutation_rejected(self) -> None:
        changed = get_exp017_source_set_lock()
        changed["benchmark_bar_access_authorized"] = True
        with self.assertRaisesRegex(ValueError, "identity"):
            validate_exp017_source_set_lock(changed)


if __name__ == "__main__":
    unittest.main()
