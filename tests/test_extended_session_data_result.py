from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from extended_session_data import AUDIT_FILE, OUTPUT_FILES
from extended_session_data_result import (
    EXPECTED_OUTPUTS,
    TRACKED_RESULT_FILE,
    verify_extended_session_data_result,
)


class ExtendedSessionDataResultTests(unittest.TestCase):
    def test_local_result_is_frozen_and_valid(self) -> None:
        result = verify_extended_session_data_result()
        self.assertEqual(result["status"], "DATA_READY")
        self.assertEqual(
            result["complete_aligned_sessions"],
            1344,
        )

    def test_all_four_output_hashes_are_frozen(self) -> None:
        result = verify_extended_session_data_result()
        self.assertEqual(result["outputs"], EXPECTED_OUTPUTS)
        self.assertEqual(set(OUTPUT_FILES), set(EXPECTED_OUTPUTS))

    def test_research_boundary_forbids_strategy_claim(self) -> None:
        result = verify_extended_session_data_result()
        boundary = result["research_boundary"]
        self.assertFalse(
            boundary["strategy_results_calculated"]
        )
        self.assertFalse(boundary["missing_bars_filled"])
        self.assertFalse(boundary["trading_authorized"])

    def test_changed_audit_is_rejected(self) -> None:
        value = json.loads(
            AUDIT_FILE.read_text(encoding="utf-8")
        )
        value["complete_aligned_sessions"] = 1345
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.json"
            path.write_text(
                json.dumps(value),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                verify_extended_session_data_result(
                    audit_path=path,
                )

    def test_changed_tracked_output_is_rejected(self) -> None:
        value = json.loads(
            TRACKED_RESULT_FILE.read_text(
                encoding="utf-8"
            )
        )
        value["outputs"]["NQ_1m"]["rows"] += 1
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            path.write_text(
                json.dumps(value),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                verify_extended_session_data_result(
                    tracked_result_path=path,
                )


if __name__ == "__main__":
    unittest.main()
