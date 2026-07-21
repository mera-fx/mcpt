from __future__ import annotations

import unittest

from exp015_catalog import (
    assess_catalog,
    build_catalog_result,
    canonicalize_catalog_rows,
    find_nq_mnq_candidates,
)


SAMPLE_ROWS = [
    {
        "symbol": "NQ",
        "name": "NASDAQ-100 futures",
        "category": "Futures",
        "dataset": "eurex",
        "ticks": 1000,
        "first": "2020-01-01T00:00:00Z",
        "last": "2026-01-01T00:00:00Z",
        "country": "US",
    },
    {
        "symbol": "MNQ",
        "name": "Micro E-mini NASDAQ-100 futures",
        "category": "Futures",
        "dataset": "eurex",
        "ticks": "2,000",
        "first": "2020-01-01T00:00:00Z",
        "last": "2026-01-01T00:00:00Z",
        "country": "US",
    },
]


class Exp015CatalogTests(unittest.TestCase):
    def test_catalog_rows_are_canonical_and_sorted(self) -> None:
        rows = canonicalize_catalog_rows(reversed(SAMPLE_ROWS))
        self.assertEqual([row["symbol"] for row in rows], ["MNQ", "NQ"])
        self.assertEqual(rows[0]["ticks"], 2000)
        self.assertEqual(
            set(rows[0]),
            {
                "symbol",
                "name",
                "category",
                "dataset",
                "ticks",
                "first",
                "last",
                "country",
            },
        )

    def test_candidate_discovery_keeps_nq_and_mnq_distinct(self) -> None:
        candidates = find_nq_mnq_candidates(SAMPLE_ROWS)
        self.assertEqual(
            [row["symbol"] for row in candidates["NQ"]],
            ["NQ"],
        )
        self.assertEqual(
            [row["symbol"] for row in candidates["MNQ"]],
            ["MNQ"],
        )

    def test_catalog_only_never_authorizes_history(self) -> None:
        assessment = assess_catalog(SAMPLE_ROWS)
        self.assertEqual(
            assessment["classification"],
            "IDENTITY_UNRESOLVED",
        )
        self.assertFalse(assessment["nq_identified"])
        self.assertFalse(assessment["mnq_identified"])
        self.assertFalse(assessment["history_download_authorized"])
        self.assertFalse(assessment["all_vendor_data_qualified"])

    def test_empty_catalog_is_unavailable(self) -> None:
        assessment = assess_catalog([])
        self.assertEqual(
            assessment["classification"],
            "CATALOG_UNAVAILABLE",
        )
        self.assertEqual(assessment["futures_catalog_rows"], 0)

    def test_result_preserves_research_boundaries(self) -> None:
        result = build_catalog_result(
            SAMPLE_ROWS,
            git={
                "commit": "abc",
                "short_commit": "abc",
                "working_tree_clean": True,
            },
            client_probe={
                "status": "PASS",
                "distribution": "lse-data",
                "version": "0.14.0",
                "python_version": "3.14.6",
                "wheel_sha256": "hash",
            },
        )
        self.assertEqual(result["result_phase"], "CATALOG_ONLY")
        self.assertTrue(
            result["interpretation"][
                "candidate_discovery_is_not_identity_resolution"
            ]
        )
        self.assertTrue(
            result["interpretation"]["catalog_does_not_start_history_phase"]
        )
        self.assertFalse(
            result["interpretation"]["automatic_all_data_claim"]
        )
        self.assertFalse(
            result["interpretation"]["paper_trading_authorized"]
        )

    def test_credential_material_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "credential"):
            canonicalize_catalog_rows(
                [
                    {
                        "symbol": "NQ",
                        "authorization": "secret",
                    }
                ]
            )

    def test_boolean_tick_count_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Boolean"):
            canonicalize_catalog_rows(
                [{"symbol": "NQ", "ticks": True}]
            )
