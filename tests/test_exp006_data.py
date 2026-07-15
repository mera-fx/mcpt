from __future__ import annotations

import inspect
import unittest
from unittest.mock import patch

import pandas as pd

import exp006_data


def frozen_result() -> dict:
    return {
        "data": {
            "confirmation_import_commit": (
                "53a740aedb63e2a7508e3e010f"
                "5370be49cf816a"
            ),
            "fingerprints": {
                "NQ_1m": "a",
                "MNQ_1m": "b",
                "NQ_5m": "c",
                "MNQ_5m": "d",
            },
        }
    }


def valid_audit() -> dict:
    return {
        **exp006_data
        .EXPECTED_CONFIRMATION_IMPORT_FIELDS,
        "git": {
            "commit": (
                "53a740aedb63e2a7508e3e010f"
                "5370be49cf816a"
            )
        },
        "fingerprints": {
            "NQ_1m": "a",
            "MNQ_1m": "b",
            "NQ_5m": "c",
            "MNQ_5m": "d",
        },
    }


class Exp006FrozenConfirmationLoaderTests(
    unittest.TestCase
):
    def test_stage_gated_exp005_loader_is_not_imported(
        self,
    ) -> None:
        source = inspect.getsource(
            exp006_data
        )

        self.assertNotIn(
            "run_exp005_full_validation",
            source,
        )
        self.assertNotIn(
            "verify_existing_import",
            source,
        )
        self.assertIn(
            "verify_local_full_validation_decision",
            source,
        )

    def test_exact_frozen_audit_is_accepted(
        self,
    ) -> None:
        exp006_data.verify_confirmation_audit_for_exp006(
            audit=valid_audit(),
            full_validation_result=(
                frozen_result()
            ),
        )

    def test_changed_audit_field_is_rejected(
        self,
    ) -> None:
        audit = valid_audit()
        audit["included_sessions"] = 734

        with self.assertRaisesRegex(
            RuntimeError,
            "included_sessions changed",
        ):
            exp006_data.verify_confirmation_audit_for_exp006(
                audit=audit,
                full_validation_result=(
                    frozen_result()
                ),
            )

    def test_loader_uses_frozen_result_without_lifecycle(
        self,
    ) -> None:
        empty = pd.DataFrame()

        with (
            patch.object(
                exp006_data,
                "verify_local_full_validation_decision",
                return_value=frozen_result(),
            ) as verify_result,
            patch.object(
                exp006_data,
                "_read_confirmation_audit",
                return_value=valid_audit(),
            ),
            patch.object(
                exp006_data,
                "_load_verified_confirmation_frames",
                return_value={
                    "NQ_1m": empty,
                    "MNQ_1m": empty,
                    "NQ_5m": empty,
                    "MNQ_5m": empty,
                },
            ),
        ):
            result = (
                exp006_data
                .load_frozen_confirmation_data_for_exp006()
            )

        verify_result.assert_called_once_with()
        self.assertEqual(
            result[0]["included_sessions"],
            733,
        )


if __name__ == "__main__":
    unittest.main()
