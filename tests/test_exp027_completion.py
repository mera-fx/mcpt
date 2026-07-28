from __future__ import annotations

from copy import deepcopy
import unittest

from exp027_completion import (
    EXPECTED_EXP027_COMPLETION_SHA256,
    EXPECTED_OUTPUT_FILES,
    canonical_record_hash,
    get_exp027_completion,
    resolve_exp027_completion_commit,
    validate_exp027_completion,
)


class Exp027CompletionTests(unittest.TestCase):
    def test_01_completion_is_valid(self) -> None:
        validate_exp027_completion()

    def test_02_identity_is_locked(self) -> None:
        record = get_exp027_completion()
        self.assertEqual(record["experiment_id"], "EXP-027")
        self.assertTrue(record["completed"])
        self.assertEqual(
            record["classification"],
            "PROTECTED_2026_MEASUREMENT_COMPLETE",
        )

    def test_03_ancestry_is_locked(self) -> None:
        record = get_exp027_completion()
        self.assertEqual(record["authorization_commit"], "88d6f4f7addad0e5ad9db6134987875ff1a7df10")
        self.assertEqual(record["implementation_commit"], "591cdf43b4c23abc312ae3d50b7d7948f88c90b2")
        self.assertEqual(record["preregistration_commit"], "21c182e119cde651e6c4fe22b1e4e8d6b99def5b")

    def test_04_counts_are_locked(self) -> None:
        record = get_exp027_completion()
        self.assertEqual(record["reported_series_count"], 24)
        self.assertEqual(record["primary_source_rows"], 198240)
        self.assertEqual(record["secondary_source_rows"], 198240)
        self.assertEqual(record["primary_trade_rows"], 925)
        self.assertEqual(record["secondary_trade_rows"], 927)

    def test_05_output_population_is_exact(self) -> None:
        record = get_exp027_completion()
        self.assertEqual(record["output_file_count"], 111)
        self.assertEqual(len(EXPECTED_OUTPUT_FILES), 111)
        self.assertEqual(set(record["all_output_paths"]), set(EXPECTED_OUTPUT_FILES))

    def test_06_integrity_is_locked(self) -> None:
        record = get_exp027_completion()
        self.assertTrue(record["independent_rebuild"])
        self.assertTrue(record["serial_parallel_parity"])
        self.assertEqual(
            record["output_manifest_sha256"],
            "fd8823bea6a04407da5f574552e4b17a79d8c21ec949a93c693421ef743e51d7",
        )

    def test_07_no_selection_or_optimization(self) -> None:
        record = get_exp027_completion()
        self.assertFalse(record["candidate_selection"])
        self.assertFalse(record["parameter_optimization"])
        self.assertFalse(record["winner_declaration"])
        self.assertFalse(record["secondary_candidate_promotion"])

    def test_08_protected_period_is_consumed(self) -> None:
        record = get_exp027_completion()
        self.assertTrue(record["protected_2026_accessed"])
        self.assertTrue(record["protected_period_consumed"])
        self.assertFalse(record["rerun_authorized"])

    def test_09_no_download_network_or_trading(self) -> None:
        record = get_exp027_completion()
        self.assertFalse(record["new_databento_download"])
        self.assertEqual(record["databento_api_calls"], 0)
        self.assertFalse(record["network_access"])
        self.assertFalse(record["paper_trading_authorized"])
        self.assertFalse(record["live_trading_authorized"])

    def test_10_completion_commit_resolves(self) -> None:
        self.assertEqual(len(resolve_exp027_completion_commit()), 40)

    def test_11_hash_rejects_mutation(self) -> None:
        record = get_exp027_completion()
        record.pop("completion_commit")
        self.assertEqual(
            canonical_record_hash(record),
            EXPECTED_EXP027_COMPLETION_SHA256,
        )
        changed = deepcopy(record)
        changed["rerun_authorized"] = True
        with self.assertRaisesRegex(ValueError, "access boundary|record changed"):
            validate_exp027_completion(changed)


if __name__ == "__main__":
    unittest.main()
