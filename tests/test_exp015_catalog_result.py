from __future__ import annotations

import unittest

from exp015_catalog_result import (
    EXPECTED_CATALOG_CANONICAL_SHA256,
    EXPECTED_CATALOG_CSV_SHA256,
    EXPECTED_CATALOG_JSON_SHA256,
    EXPECTED_IMPLEMENTATION_COMMIT,
    EXPECTED_NQ_CANDIDATE,
    get_exp015_catalog_freeze,
    validate_exp015_catalog_freeze,
    verify_local_exp015_catalog_result,
)


class Exp015CatalogResultTests(unittest.TestCase):
    def test_frozen_record_is_valid(self) -> None:
        validate_exp015_catalog_freeze()

    def test_local_catalog_result_is_frozen_and_valid(self) -> None:
        result = verify_local_exp015_catalog_result()
        self.assertEqual(
            result["assessment"]["classification"],
            "IDENTITY_UNRESOLVED",
        )

    def test_exact_result_hashes_are_frozen(self) -> None:
        hashes = get_exp015_catalog_freeze()["file_hashes"]
        self.assertEqual(
            hashes["catalog_result_json_sha256"],
            EXPECTED_CATALOG_JSON_SHA256,
        )
        self.assertEqual(
            hashes["catalog_rows_csv_sha256"],
            EXPECTED_CATALOG_CSV_SHA256,
        )
        self.assertEqual(
            hashes["catalog_canonical_sha256"],
            EXPECTED_CATALOG_CANONICAL_SHA256,
        )

    def test_implementation_provenance_is_frozen(self) -> None:
        record = get_exp015_catalog_freeze()
        self.assertEqual(
            record["git"]["commit"],
            EXPECTED_IMPLEMENTATION_COMMIT,
        )
        self.assertTrue(record["git"]["working_tree_clean"])

    def test_nq_candidate_and_mnq_absence_are_preserved(self) -> None:
        catalog = get_exp015_catalog_freeze()["catalog_measurement"]
        self.assertEqual(catalog["futures_catalog_rows"], 69)
        self.assertEqual(catalog["nq_candidate_count"], 1)
        self.assertEqual(catalog["nq_candidate"], EXPECTED_NQ_CANDIDATE)
        self.assertEqual(catalog["mnq_candidate_count"], 0)
        self.assertEqual(catalog["mnq_candidates"], [])

    def test_no_history_or_all_data_qualification(self) -> None:
        record = get_exp015_catalog_freeze()
        assessment = record["assessment"]
        interpretation = record["interpretation"]
        self.assertFalse(assessment["history_download_authorized"])
        self.assertFalse(assessment["all_vendor_data_qualified"])
        self.assertFalse(interpretation["history_downloaded"])
        self.assertFalse(interpretation["automatic_all_data_claim"])
        self.assertTrue(
            interpretation[
                "london_strategic_edge_not_qualified_as_primary_nq_mnq_source"
            ]
        )

    def test_no_trading_authorization(self) -> None:
        record = get_exp015_catalog_freeze()
        self.assertFalse(
            record["assessment"]["paper_trading_authorized"]
        )
        self.assertFalse(
            record["assessment"]["live_trading_authorized"]
        )
        self.assertFalse(
            record["interpretation"]["paper_trading_authorized"]
        )
        self.assertFalse(
            record["interpretation"]["live_trading_authorized"]
        )

    def test_classification_mutation_is_rejected(self) -> None:
        changed = get_exp015_catalog_freeze()
        changed["assessment"]["classification"] = (
            "QUALIFIED_FOR_NEW_NQ_MNQ_HISTORICAL_RESEARCH"
        )
        with self.assertRaisesRegex(ValueError, "assessment"):
            validate_exp015_catalog_freeze(changed)

    def test_mnq_mutation_is_rejected(self) -> None:
        changed = get_exp015_catalog_freeze()
        changed["catalog_measurement"]["mnq_candidate_count"] = 1
        with self.assertRaisesRegex(ValueError, "catalog measurement"):
            validate_exp015_catalog_freeze(changed)

    def test_hash_mutation_is_rejected(self) -> None:
        changed = get_exp015_catalog_freeze()
        changed["file_hashes"]["catalog_result_json_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "hashes"):
            validate_exp015_catalog_freeze(changed)


if __name__ == "__main__":
    unittest.main()
