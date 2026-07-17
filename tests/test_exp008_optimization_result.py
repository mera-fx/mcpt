from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from exp008_optimization_result import (
    EXPECTED_CANONICAL_SHA256,
    canonical_record_sha256,
    get_exp008_optimization_result,
    load_json_object,
    load_tracked_exp008_optimization_result,
    validate_exp008_result,
    verify_local_exp008_optimization_decision,
)


class Exp008OptimizationResultTests(
    unittest.TestCase
):
    def test_tracked_result_is_valid(
        self,
    ) -> None:
        result = (
            load_tracked_exp008_optimization_result()
        )
        self.assertEqual(
            result["evaluation"]["decision"],
            "REJECT_EXP008_PRESERVE_AS_NEGATIVE_RESULT",
        )

    def test_result_hash_is_frozen(
        self,
    ) -> None:
        result = (
            load_tracked_exp008_optimization_result()
        )
        self.assertEqual(
            canonical_record_sha256(result),
            EXPECTED_CANONICAL_SHA256,
        )

    def test_local_matches_tracked(
        self,
    ) -> None:
        self.assertEqual(
            verify_local_exp008_optimization_decision(),
            load_tracked_exp008_optimization_result(),
        )

    def test_only_mcpt_gate_failed(
        self,
    ) -> None:
        result = (
            get_exp008_optimization_result()
        )
        self.assertEqual(
            result["evaluation"]["failed_gates"],
            ["selection_aware_nq_mcpt_p_value"],
        )

    def test_mcpt_exceedance_and_p_value_are_exact(
        self,
    ) -> None:
        mcpt = (
            get_exp008_optimization_result()[
                "mcpt"
            ]
        )
        self.assertEqual(
            mcpt["permutations_at_least_real"],
            138,
        )
        self.assertAlmostEqual(
            mcpt["p_value"],
            139 / 1001,
            places=15,
        )

    def test_crlf_and_lf_have_same_canonical_hash(
        self,
    ) -> None:
        result = (
            load_tracked_exp008_optimization_result()
        )
        serialized = json.dumps(
            result,
            indent=2,
            allow_nan=False,
        )

        with tempfile.TemporaryDirectory() as directory:
            lf_path = Path(directory) / "lf.json"
            crlf_path = Path(directory) / "crlf.json"

            lf_path.write_bytes(
                serialized.encode("utf-8")
            )
            crlf_path.write_bytes(
                serialized.replace(
                    "\n",
                    "\r\n",
                ).encode("utf-8")
            )

            lf_record = load_json_object(
                lf_path
            )
            crlf_record = load_json_object(
                crlf_path
            )

        self.assertEqual(
            lf_record,
            crlf_record,
        )
        self.assertEqual(
            canonical_record_sha256(
                lf_record
            ),
            canonical_record_sha256(
                crlf_record
            ),
        )

    def test_changed_decision_is_rejected(
        self,
    ) -> None:
        changed = deepcopy(
            get_exp008_optimization_result()
        )
        changed["evaluation"]["decision"] = "PASS"

        with self.assertRaisesRegex(
            ValueError,
            "rejection decision changed",
        ):
            validate_exp008_result(
                changed
            )


if __name__ == "__main__":
    unittest.main()
