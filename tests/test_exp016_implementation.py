from __future__ import annotations

import unittest

from exp016_implementation import (
    EXPECTED_PREREGISTRATION_COMMIT,
    FIXED_SAMPLE_WINDOWS,
    get_exp016_implementation,
    validate_exp016_implementation,
)


class Exp016ImplementationTests(unittest.TestCase):
    def test_implementation_is_valid_and_not_run(self) -> None:
        validate_exp016_implementation()

    def test_preregistration_commit_is_locked(self) -> None:
        self.assertEqual(
            EXPECTED_PREREGISTRATION_COMMIT,
            "55577ca589fbc2b899c93a088592d32398121e49",
        )

    def test_only_three_safe_modes_exist(self) -> None:
        modes = get_exp016_implementation()["runner_modes"]
        self.assertTrue(modes["preflight"])
        self.assertTrue(modes["download_samples"])
        self.assertTrue(modes["audit_local"])
        self.assertFalse(modes["catalog"])
        self.assertFalse(modes["full_history"])
        self.assertFalse(modes["strategy_replay"])
        self.assertFalse(modes["optimization"])

    def test_remote_boundary_is_six_fixed_windows(self) -> None:
        remote = get_exp016_implementation()["remote_boundary"]
        self.assertEqual(tuple(remote["fixed_windows"]), FIXED_SAMPLE_WINDOWS)
        self.assertEqual(remote["maximum_requests"], 6)
        self.assertTrue(remote["one_request_attempt_per_window"])
        self.assertTrue(remote["catalog_call_prohibited"])
        self.assertTrue(remote["datasets_call_prohibited"])

    def test_no_primary_or_trading_authorization(self) -> None:
        result = get_exp016_implementation()["result_boundary"]
        self.assertTrue(result["primary_source_qualification_prohibited"])
        self.assertTrue(result["mnq_qualification_prohibited"])
        self.assertFalse(result["prior_data_replacement"])
        self.assertFalse(result["strategy_results"])
        self.assertFalse(result["paper_trading_authorized"])
        self.assertFalse(result["live_trading_authorized"])

    def test_mode_mutation_is_rejected(self) -> None:
        changed = get_exp016_implementation()
        changed["runner_modes"]["catalog"] = True
        with self.assertRaisesRegex(ValueError, "runner modes"):
            validate_exp016_implementation(changed)

    def test_reference_mutation_is_rejected(self) -> None:
        changed = get_exp016_implementation()
        changed["local_audit_boundary"]["automatic_price_offset"] = True
        with self.assertRaisesRegex(ValueError, "local audit"):
            validate_exp016_implementation(changed)
