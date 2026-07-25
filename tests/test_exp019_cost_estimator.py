from __future__ import annotations

import unittest

from exp019_cost_estimator import (
    CONTINUOUS_REFERENCE_COST_USD,
    ContractCost,
    build_summary,
    contract_plan_digest,
    estimate_contract_costs,
)


class FakeMetadata:
    def __init__(self):
        self.calls = []

    def get_cost(self, **kwargs):
        self.calls.append(kwargs)
        return len(self.calls) * 0.25


class FakeClient:
    def __init__(self):
        self.metadata = FakeMetadata()


class Exp019CostEstimatorTests(
    unittest.TestCase
):
    def test_estimates_each_contract_once(self):
        client = FakeClient()

        plan = (
            (
                "NQM10",
                "NQM0",
                "2010-06-06",
                "2010-06-19",
                "2010-06-18",
            ),
            (
                "NQU10",
                "NQU0",
                "2010-05-19",
                "2010-09-18",
                "2010-09-17",
            ),
        )

        rows = estimate_contract_costs(
            client,
            plan,
        )

        self.assertEqual(
            len(rows),
            2,
        )
        self.assertEqual(
            len(client.metadata.calls),
            2,
        )

        self.assertEqual(
            rows[0].estimated_cost_usd,
            0.25,
        )
        self.assertEqual(
            rows[1].estimated_cost_usd,
            0.50,
        )

        first_call = client.metadata.calls[0]

        self.assertEqual(
            first_call["dataset"],
            "GLBX.MDP3",
        )
        self.assertEqual(
            first_call["schema"],
            "ohlcv-1m",
        )
        self.assertEqual(
            first_call["stype_in"],
            "raw_symbol",
        )
        self.assertEqual(
            first_call["symbols"],
            "NQM0",
        )

    def test_summary_does_not_authorize_download(self):
        rows = [
            ContractCost(
                sequence=1,
                canonical_symbol="NQM10",
                raw_symbol="NQM0",
                start="2010-06-06",
                end_exclusive="2010-06-19",
                expiration="2010-06-18",
                estimated_cost_usd=10.0,
            )
        ]

        summary = build_summary(
            rows,
            {
                "branch": "main",
                "head": "abc",
                "origin_main": "abc",
                "locked_preregistration_commit": "def",
            },
        )

        self.assertFalse(
            summary["interpretation"][
                "download_authorized"
            ]
        )
        self.assertFalse(
            summary["interpretation"][
                "archive_qualified"
            ]
        )
        self.assertFalse(
            summary["interpretation"][
                "strategy_run"
            ]
        )
        self.assertFalse(
            summary["request"][
                "bar_records_requested"
            ]
        )
        self.assertFalse(
            summary["request"][
                "bar_records_downloaded"
            ]
        )

    def test_summary_cost_calculations(self):
        rows = [
            ContractCost(
                sequence=1,
                canonical_symbol="A",
                raw_symbol="A",
                start="2020-01-01",
                end_exclusive="2020-01-02",
                expiration="2020-01-01",
                estimated_cost_usd=10.0,
            ),
            ContractCost(
                sequence=2,
                canonical_symbol="B",
                raw_symbol="B",
                start="2020-01-01",
                end_exclusive="2020-01-02",
                expiration="2020-01-01",
                estimated_cost_usd=15.0,
            ),
        ]

        summary = build_summary(
            rows,
            {
                "branch": "main",
                "head": "abc",
                "origin_main": "abc",
                "locked_preregistration_commit": "def",
            },
        )

        costs = summary["costs"]

        self.assertEqual(
            costs["exact_contract_total_usd"],
            25.0,
        )
        self.assertAlmostEqual(
            costs["difference_usd"],
            25.0
            - CONTINUOUS_REFERENCE_COST_USD,
        )
        self.assertTrue(
            costs["within_locked_cap"]
        )

    def test_plan_digest_is_stable(self):
        plan = (
            (
                "NQM10",
                "NQM0",
                "2010-06-06",
                "2010-06-19",
                "2010-06-18",
            ),
        )

        self.assertEqual(
            contract_plan_digest(plan),
            contract_plan_digest(plan),
        )


if __name__ == "__main__":
    unittest.main()
