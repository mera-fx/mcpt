from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from exp020_constructor import (
    ORIGINAL_AUTHORIZATION_COMMIT,
    PREFLIGHT_CORRECTION_AUTHORIZATION_PATH,
    archive_digest,
    load_preflight_correction_authorization,
)


class Exp020PreflightDigestCorrectionTests(
    unittest.TestCase
):
    def test_original_authorization_commit_is_locked(
        self,
    ) -> None:
        self.assertEqual(
            ORIGINAL_AUTHORIZATION_COMMIT,
            (
                "e497b1abf247ed83295caa9378c2a4e6"
                "869922b1"
            ),
        )

    def test_archive_digest_matches_exp019_protocol(
        self,
    ) -> None:
        rows = [
            {
                "sequence": "2",
                "canonical_symbol": "NQM24",
                "sha256": "b" * 64,
                "size_bytes": "22",
            },
            {
                "sequence": 1,
                "canonical_symbol": "NQH24",
                "sha256": "a" * 64,
                "size_bytes": 11,
            },
        ]

        self.assertEqual(
            archive_digest(rows),
            (
                "a122e3fb0f4fc3b67d043f12eb11fc2c"
                "18970d0bc152a3452b6e0189b74a76cc"
            ),
        )

    def test_digest_is_not_sorted_key_protocol(
        self,
    ) -> None:
        rows = [
            {
                "sequence": 1,
                "canonical_symbol": "NQH24",
                "sha256": "a" * 64,
                "size_bytes": 11,
            },
            {
                "sequence": 2,
                "canonical_symbol": "NQM24",
                "sha256": "b" * 64,
                "size_bytes": 22,
            },
        ]

        self.assertNotEqual(
            archive_digest(rows),
            (
                "67671b8173784fc561269c73f1ea736b2"
                "b7e33dae80d162b5d3e477a63441020"
            ),
        )

    def test_correction_requires_separate_authorization(
        self,
    ) -> None:
        missing = (
            Path(tempfile.gettempdir())
            / "missing_exp020_preflight_correction.py"
        )

        with patch(
            "exp020_constructor."
            "PREFLIGHT_CORRECTION_AUTHORIZATION_PATH",
            missing,
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "correction is not authorized",
            ):
                load_preflight_correction_authorization()

    def test_correction_authorization_path_is_locked(
        self,
    ) -> None:
        self.assertEqual(
            PREFLIGHT_CORRECTION_AUTHORIZATION_PATH.name,
            "exp020_preflight_correction_authorization.py",
        )


if __name__ == "__main__":
    unittest.main()
