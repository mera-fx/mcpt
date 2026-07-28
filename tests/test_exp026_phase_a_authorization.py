from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import hashlib
import unittest

from exp026_phase_a_authorization import (
    EXPECTED_EXP026_PHASE_A_AUTHORIZATION_SHA256,
    canonical_record_hash,
    get_exp026_phase_a_authorization,
    validate_exp026_phase_a_authorization,
)
from exp026_preregistration import (
    EXPECTED_EXP026_PREREGISTRATION_SHA256,
    get_exp026_preregistration,
)
from exp026_runner import (
    IMPLEMENTATION_PATHS,
    PHASE_REQUIRED_OUTPUTS,
    load_phase_authorization,
)


PROJECT_DIR = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for block in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


class Exp026PhaseAAuthorizationTests(unittest.TestCase):
    def test_01_authorization_is_valid(self) -> None:
        validate_exp026_phase_a_authorization()

    def test_02_identity_is_locked(self) -> None:
        record = get_exp026_phase_a_authorization()

        self.assertEqual(
            record["experiment_id"],
            "EXP-026",
        )
        self.assertEqual(record["phase"], "A")
        self.assertEqual(
            record["authorization_status"],
            "AUTHORIZED",
        )
        self.assertTrue(
            record["execution_authorized"]
        )

    def test_03_preregistration_and_implementation_are_locked(
        self,
    ) -> None:
        record = get_exp026_phase_a_authorization()

        self.assertEqual(
            record["preregistration_sha256"],
            EXPECTED_EXP026_PREREGISTRATION_SHA256,
        )
        self.assertEqual(
            record["locked_implementation_commit"],
            "13ee0683dfcbbb5d763f7254f3b245ecc8e6d9cd",
        )

    def test_04_implementation_file_hashes_match(
        self,
    ) -> None:
        record = get_exp026_phase_a_authorization()
        files = record["implementation_files"]

        self.assertEqual(
            set(files),
            set(IMPLEMENTATION_PATHS),
        )

        for relative_path, expected in files.items():
            path = PROJECT_DIR / relative_path

            self.assertTrue(path.is_file())
            self.assertEqual(
                int(path.stat().st_size),
                int(expected["size_bytes"]),
            )
            self.assertEqual(
                sha256_file(path),
                expected["sha256"],
            )

    def test_05_phase_a_period_is_exact(self) -> None:
        scope = get_exp026_phase_a_authorization()[
            "phase_scope"
        ]

        self.assertEqual(
            scope["allowed_session_start"],
            "2010-06-07",
        )
        self.assertEqual(
            scope["allowed_session_end"],
            "2017-12-31",
        )

    def test_06_candidate_scope_matches_preregistration(
        self,
    ) -> None:
        authorization = (
            get_exp026_phase_a_authorization()
        )
        preregistration = (
            get_exp026_preregistration()
        )
        scope = authorization["phase_scope"]
        grid = preregistration["candidate_grid"]

        expected_development = tuple(
            item["candidate_id"]
            for item in grid[
                "development_candidates"
            ]
        )
        expected_controls = tuple(
            item["candidate_id"]
            for item in grid[
                "control_candidates"
            ]
        )

        self.assertEqual(
            tuple(scope["development_candidate_ids"]),
            expected_development,
        )
        self.assertEqual(
            tuple(scope["control_candidate_ids"]),
            expected_controls,
        )

    def test_07_run_is_one_time_only(self) -> None:
        record = get_exp026_phase_a_authorization()

        self.assertTrue(record["one_time_run"])
        self.assertEqual(record["maximum_runs"], 1)
        self.assertFalse(
            record["execution_boundary"][
                "rerun_after_completion_authorized"
            ]
        )

    def test_08_only_backward_adjusted_is_authorized(
        self,
    ) -> None:
        scope = get_exp026_phase_a_authorization()[
            "phase_scope"
        ]

        self.assertEqual(
            scope["primary_representation"],
            "BACKWARD_ADJUSTED",
        )
        self.assertFalse(
            scope[
                "unadjusted_representation_authorized"
            ]
        )

    def test_09_required_outputs_match_runner(
        self,
    ) -> None:
        record = get_exp026_phase_a_authorization()

        self.assertEqual(
            tuple(record["required_outputs"]),
            PHASE_REQUIRED_OUTPUTS["A"],
        )

    def test_10_phase_b_and_c_are_not_authorized(
        self,
    ) -> None:
        protected = get_exp026_phase_a_authorization()[
            "protected_actions"
        ]

        self.assertFalse(
            protected[
                "phase_b_execution_authorized"
            ]
        )
        self.assertFalse(
            protected[
                "phase_c_execution_authorized"
            ]
        )

    def test_11_runner_required_top_level_fields_are_locked(
        self,
    ) -> None:
        record = get_exp026_phase_a_authorization()

        for field in (
            "protected_2026_access_authorized",
            "new_databento_download_authorized",
            "network_access_authorized",
            "paper_trading_authorized",
            "live_trading_authorized",
        ):
            self.assertIn(field, record)
            self.assertFalse(record[field])

    def test_12_no_download_network_or_trading(
        self,
    ) -> None:
        boundary = get_exp026_phase_a_authorization()[
            "data_access_boundary"
        ]

        self.assertEqual(
            boundary[
                "databento_api_calls_authorized"
            ],
            0,
        )
        self.assertFalse(
            boundary[
                "new_databento_download_authorized"
            ]
        )
        self.assertFalse(
            boundary["network_access_authorized"]
        )
        self.assertFalse(
            boundary["order_api_access_authorized"]
        )

    def test_13_runner_accepts_authorization_interface(
        self,
    ) -> None:
        record = load_phase_authorization("A")

        self.assertEqual(record["phase"], "A")
        self.assertTrue(
            record["execution_authorized"]
        )
        self.assertFalse(
            record[
                "protected_2026_access_authorized"
            ]
        )

    def test_14_hash_rejects_mutation(self) -> None:
        record = get_exp026_phase_a_authorization()

        self.assertEqual(
            canonical_record_hash(record),
            EXPECTED_EXP026_PHASE_A_AUTHORIZATION_SHA256,
        )

        changed = deepcopy(record)
        changed["maximum_runs"] = 2

        with self.assertRaisesRegex(
            ValueError,
            "authorization identity changed",
        ):
            validate_exp026_phase_a_authorization(
                changed
            )


if __name__ == "__main__":
    unittest.main()
