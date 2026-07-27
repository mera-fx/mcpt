from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import hashlib
import unittest

from exp025_closure import (
    EXPECTED_EXP025_CLOSURE_SHA256,
    canonical_record_hash,
    get_exp025_closure,
    validate_exp025_closure,
)
from experiment_lifecycle import get_experiment_lifecycle


POLICY_PATH = Path(
    "research/HISTORICAL_DATA_POLICY.md"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(block)
    return digest.hexdigest()


class Exp025ClosureTests(unittest.TestCase):
    def test_01_closure_is_valid(self) -> None:
        validate_exp025_closure()

    def test_02_classification_is_locked(self) -> None:
        record = get_exp025_closure()
        self.assertEqual(
            record["research_status"],
            "REVIEW",
        )
        self.assertEqual(
            record["classification"],
            "BLOCKED_DATA_UNAVAILABLE",
        )

    def test_03_repository_chain_is_locked(self) -> None:
        repository = get_exp025_closure()["repository"]
        self.assertEqual(
            repository["preregistration_commit"],
            "1d736705a41d0208e353fb17710c8a16cc937710",
        )
        self.assertEqual(
            repository["corrected_implementation_commit"],
            "2011745145b9799a4a42b556d57780002d30e317",
        )
        self.assertEqual(
            repository[
                "quantower_export_authorization_commit"
            ],
            "6a76dba1702f87f7610b0d7346958478c6685ed4",
        )

    def test_04_no_exact_contract_evidence_was_accepted(
        self,
    ) -> None:
        evidence = get_exp025_closure()["evidence"]
        self.assertEqual(
            evidence["accepted_exact_contract_file_count"],
            0,
        )
        self.assertEqual(
            evidence["rejected_generic_nq_file_count"],
            2,
        )
        self.assertFalse(
            evidence[
                "generic_csv_explicit_contract_column_present"
            ]
        )
        self.assertFalse(
            evidence[
                "generic_nq_files_accepted_for_diagnostic"
            ]
        )

    def test_05_diagnostic_and_performance_were_not_run(
        self,
    ) -> None:
        execution = get_exp025_closure()["execution"]
        self.assertFalse(execution["diagnostic_executed"])
        self.assertFalse(
            execution["decision_engine_comparison_executed"]
        )
        self.assertFalse(
            execution["performance_evaluation_executed"]
        )
        self.assertFalse(execution["paper_trading_authorized"])
        self.assertFalse(execution["live_trading_authorized"])

    def test_06_no_strategy_conclusion_exists(self) -> None:
        interpretation = get_exp025_closure()[
            "interpretation"
        ]
        self.assertFalse(
            interpretation["strategy_edge_validated"]
        )
        self.assertFalse(
            interpretation["strategy_failure_established"]
        )
        self.assertFalse(
            interpretation["candidate_selected_or_rejected"]
        )
        self.assertTrue(
            interpretation["no_strategy_conclusion_permitted"]
        )

    def test_07_databento_first_policy_is_locked(
        self,
    ) -> None:
        record = get_exp025_closure()
        locked = record["locked_records"]

        self.assertTrue(POLICY_PATH.is_file())
        self.assertEqual(
            sha256_file(POLICY_PATH),
            locked["historical_data_policy_sha256"],
        )

        text = POLICY_PATH.read_text(encoding="utf-8")
        self.assertIn(
            "Databento is the primary historical market-data source",
            text,
        )
        self.assertIn("Exact quarterly contracts", text)
        self.assertIn("Continuous series", text)
        self.assertIn("Quantower and Lucid/Rithmic", text)

    def test_08_policy_does_not_authorize_download_or_trading(
        self,
    ) -> None:
        boundary = get_exp025_closure()[
            "next_research_boundary"
        ]
        self.assertTrue(
            boundary[
                "databento_primary_for_future_historical_testing"
            ]
        )
        self.assertFalse(
            boundary[
                "new_databento_download_authorized_by_closure"
            ]
        )
        self.assertTrue(
            boundary["paper_or_live_trading_not_authorized"]
        )

    def test_09_lifecycle_matches_closure(self) -> None:
        lifecycle = get_experiment_lifecycle("EXP-025")
        self.assertEqual(lifecycle.stage, "REVIEW")
        self.assertIn(
            "BLOCKED_DATA_UNAVAILABLE",
            lifecycle.stage_reason,
        )
        self.assertIn(
            "Databento as the primary historical",
            lifecycle.next_action,
        )

    def test_10_hash_rejects_mutation(self) -> None:
        record = get_exp025_closure()
        self.assertEqual(
            canonical_record_hash(record),
            EXPECTED_EXP025_CLOSURE_SHA256,
        )

        changed = deepcopy(record)
        changed["evidence"][
            "accepted_exact_contract_file_count"
        ] = 1

        with self.assertRaisesRegex(
            ValueError,
            "evidence boundary changed",
        ):
            validate_exp025_closure(changed)


if __name__ == "__main__":
    unittest.main()
