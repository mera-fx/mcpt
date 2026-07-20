from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from correct_exp011_mnq_bootstrap_units import (
    EXPECTED_RESULT_IMPLEMENTATION_COMMIT,
    validate_original_double_scaled_bootstrap,
)
from exp011_implementation import get_exp011_implementation


def original_fixture():
    diagnostics = [
        {
            "comparison_sizing_id": "fractional_nq_equal_risk",
            "comparison_scale_to_nq": 1.0,
        },
        {
            "comparison_sizing_id": "integer_mnq_equal_risk",
            "comparison_scale_to_nq": 10.0,
        },
        {
            "comparison_sizing_id": "fractional_nq_equal_risk",
            "comparison_scale_to_nq": 1.0,
        },
        {
            "comparison_sizing_id": "integer_mnq_equal_risk",
            "comparison_scale_to_nq": 10.0,
        },
    ]
    result = {
        "schema_version": 1,
        "experiment_id": "EXP-011",
        "result_status": "MEASURED_POSITION_SIZING_STUDY",
        "git": {"commit": EXPECTED_RESULT_IMPLEMENTATION_COMMIT},
        "calibration": {"target_dollar_risk_usd": 1005.0},
        "results": [{} for _ in range(6)],
        "paired_bootstrap": diagnostics,
    }
    return result, {"diagnostics": diagnostics}


class Exp011UnitCorrectionTests(unittest.TestCase):
    def test_original_double_scaled_record_is_recognized(self) -> None:
        result, bootstrap = original_fixture()
        validate_original_double_scaled_bootstrap(result, bootstrap)

    def test_changed_original_scale_is_rejected(self) -> None:
        result, bootstrap = original_fixture()
        changed = deepcopy(bootstrap)
        changed["diagnostics"][1]["comparison_scale_to_nq"] = 1.0
        result["paired_bootstrap"] = changed["diagnostics"]
        with self.assertRaisesRegex(ValueError, "double-scale"):
            validate_original_double_scaled_bootstrap(result, changed)

    def test_correct_implementation_prohibits_double_scaling(self) -> None:
        bootstrap = get_exp011_implementation()["bootstrap"]
        self.assertEqual(
            bootstrap["mnq_actual_usd_comparison_scale"], 1.0
        )
        self.assertTrue(bootstrap["mnq_double_scaling_prohibited"])

    def test_correction_does_not_import_strategy_runner(self) -> None:
        source = Path(
            "correct_exp011_mnq_bootstrap_units.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("run_exp009_candidate", source)
        self.assertNotIn("calibrate_target_dollar_risk", source)
        self.assertIn("measurement_summary_unchanged", source)


if __name__ == "__main__":
    unittest.main()
