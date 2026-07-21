from __future__ import annotations

import unittest

from exp015_implementation import (
    EXPECTED_CLIENT_VERSION,
    EXPECTED_CLIENT_WHEEL_SHA256,
    EXPECTED_PREREGISTRATION_COMMIT,
    get_exp015_implementation,
    validate_exp015_implementation,
)


class Exp015ImplementationTests(unittest.TestCase):
    def test_implementation_is_valid_and_not_run(self) -> None:
        validate_exp015_implementation()
        record = get_exp015_implementation()
        self.assertEqual(
            record["implementation_status"],
            "IMPLEMENTED_NOT_RUN",
        )
        self.assertEqual(
            record["expected_preregistration_commit"],
            EXPECTED_PREREGISTRATION_COMMIT,
        )

    def test_exact_client_version_and_hash_are_locked(self) -> None:
        client = get_exp015_implementation()["client_lock"]
        self.assertEqual(client["version"], EXPECTED_CLIENT_VERSION)
        self.assertEqual(
            client["wheel_sha256"],
            EXPECTED_CLIENT_WHEEL_SHA256,
        )
        self.assertTrue(client["main_environment_install_prohibited"])

    def test_only_preflight_probe_and_catalog_modes_exist(self) -> None:
        modes = get_exp015_implementation()["runner_modes"]
        self.assertTrue(modes["preflight"])
        self.assertTrue(modes["probe_client"])
        self.assertTrue(modes["catalog"])
        self.assertFalse(modes["history"])
        self.assertFalse(modes["strategy_replay"])
        self.assertTrue(modes["modes_mutually_exclusive"])

    def test_probe_cannot_use_real_key_or_market_data(self) -> None:
        probe = get_exp015_implementation()["probe_boundary"]
        self.assertTrue(probe["real_api_key_removed_from_probe_environment"])
        self.assertTrue(
            probe["client_constructed_with_non_secret_dummy_key"]
        )
        self.assertFalse(probe["network_market_data_call"])

    def test_catalog_is_catalog_only(self) -> None:
        catalog = get_exp015_implementation()["catalog_boundary"]
        self.assertEqual(
            catalog["only_allowed_remote_method"],
            "catalog('futures')",
        )
        self.assertTrue(catalog["candles_call_prohibited"])
        self.assertTrue(catalog["history_call_prohibited"])
        self.assertTrue(catalog["dataset_call_prohibited"])
        self.assertTrue(catalog["stream_call_prohibited"])
        self.assertFalse(catalog["history_phase_automatically_starts"])

    def test_client_mutation_is_rejected(self) -> None:
        changed = get_exp015_implementation()
        changed["client_lock"]["version"] = "999.0.0"
        with self.assertRaisesRegex(ValueError, "client lock"):
            validate_exp015_implementation(changed)

    def test_history_mode_mutation_is_rejected(self) -> None:
        changed = get_exp015_implementation()
        changed["runner_modes"]["history"] = True
        with self.assertRaisesRegex(ValueError, "runner modes"):
            validate_exp015_implementation(changed)

    def test_trading_authorization_is_prohibited(self) -> None:
        protection = get_exp015_implementation()[
            "prior_research_protection"
        ]
        self.assertFalse(protection["paper_trading_authorized"])
        self.assertFalse(protection["live_trading_authorized"])
