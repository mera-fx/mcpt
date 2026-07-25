from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from exp019_acquisition import (
    DATASET,
    MAXIMUM_TOTAL_COST_USD,
    SCHEMA,
    STYPE_IN,
    STYPE_OUT,
    attempted_estimated_cost,
    contract_plan_digest,
    download_contract,
    new_manifest,
    output_filename,
    partial_filename,
)


class FakeTimeseries:
    def __init__(
        self,
        *,
        fail: bool = False,
    ):
        self.fail = fail
        self.calls = []

    def get_range(
        self,
        **kwargs,
    ):
        self.calls.append(
            kwargs
        )

        if self.fail:
            raise RuntimeError(
                "locked fake failure"
            )

        path = Path(
            kwargs["path"]
        )

        path.write_bytes(
            b"DBN TEST CONTENT"
        )

        return object()


class FakeClient:
    def __init__(
        self,
        *,
        fail: bool = False,
    ):
        self.timeseries = (
            FakeTimeseries(
                fail=fail
            )
        )


class Exp019AcquisitionTests(
    unittest.TestCase
):
    def test_contract_plan_digest_is_stable(
        self,
    ):
        self.assertEqual(
            contract_plan_digest(),
            contract_plan_digest(),
        )
        self.assertEqual(
            len(
                contract_plan_digest()
            ),
            64,
        )

    def test_output_and_partial_names(
        self,
    ):
        final_name = output_filename(
            1,
            "NQM10",
            "2010-06-06",
            "2010-06-19",
        )

        self.assertTrue(
            final_name.endswith(
                ".dbn.zst"
            )
        )

        partial = partial_filename(
            final_name
        )

        self.assertTrue(
            partial.endswith(
                ".partial.dbn.zst"
            )
        )
        self.assertNotEqual(
            partial,
            final_name,
        )

    def test_new_manifest_has_no_retries(
        self,
    ):
        manifest = new_manifest(
            {
                "branch": "main",
                "head": "abc",
                "origin_main": "abc",
            }
        )

        self.assertEqual(
            manifest["experiment_id"],
            "EXP-019",
        )
        self.assertEqual(
            manifest["status"],
            "IN_PROGRESS",
        )
        self.assertEqual(
            manifest["request"][
                "automatic_retries"
            ],
            0,
        )
        self.assertEqual(
            manifest["attempts"],
            [],
        )
        self.assertEqual(
            manifest["completed"],
            [],
        )

    def test_attempted_cost_counts_each_attempt(
        self,
    ):
        manifest = new_manifest(
            {
                "branch": "main",
                "head": "abc",
                "origin_main": "abc",
            }
        )

        manifest["attempts"] = [
            {
                "estimated_cost_usd": 1.25,
            },
            {
                "estimated_cost_usd": 2.50,
            },
        ]

        self.assertEqual(
            attempted_estimated_cost(
                manifest
            ),
            3.75,
        )

        self.assertLess(
            attempted_estimated_cost(
                manifest
            ),
            MAXIMUM_TOTAL_COST_USD,
        )

    def test_download_streams_one_locked_request(
        self,
    ):
        client = FakeClient()

        with tempfile.TemporaryDirectory() as directory:
            archive_root = (
                Path(directory)
                / "archive"
            )
            raw_dir = (
                archive_root
                / "raw"
            )

            entry = download_contract(
                client,
                sequence=1,
                canonical_symbol="NQM10",
                raw_symbol="NQM0",
                start="2010-06-06",
                end_exclusive="2010-06-19",
                expiration="2010-06-18",
                estimated_cost_usd=0.25,
                raw_dir=raw_dir,
                archive_root=archive_root,
            )

            self.assertEqual(
                len(
                    client.timeseries.calls
                ),
                1,
            )

            call = (
                client.timeseries.calls[0]
            )

            self.assertEqual(
                call["dataset"],
                DATASET,
            )
            self.assertEqual(
                call["schema"],
                SCHEMA,
            )
            self.assertEqual(
                call["stype_in"],
                STYPE_IN,
            )
            self.assertEqual(
                call["stype_out"],
                STYPE_OUT,
            )
            self.assertEqual(
                call["symbols"],
                "NQM0",
            )
            self.assertEqual(
                call["start"],
                "2010-06-06",
            )
            self.assertEqual(
                call["end"],
                "2010-06-19",
            )

            final_path = (
                archive_root
                / entry[
                    "relative_path"
                ]
            )

            self.assertEqual(
                Path(
                    entry[
                        "relative_path"
                    ]
                ).parts[0],
                "raw",
            )
            self.assertTrue(
                final_path.is_file()
            )
            self.assertGreater(
                entry["size_bytes"],
                0,
            )
            self.assertEqual(
                len(
                    entry["sha256"]
                ),
                64,
            )
            self.assertFalse(
                any(
                    raw_dir.glob(
                        "*.partial.dbn.zst"
                    )
                )
            )

    def test_failed_request_is_not_retried(
        self,
    ):
        client = FakeClient(
            fail=True
        )

        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(
                RuntimeError,
                "locked fake failure",
            ):
                download_contract(
                    client,
                    sequence=1,
                    canonical_symbol="NQM10",
                    raw_symbol="NQM0",
                    start="2010-06-06",
                    end_exclusive="2010-06-19",
                    expiration="2010-06-18",
                    estimated_cost_usd=0.25,
                    raw_dir=Path(
                        directory
                    ),
                )

        self.assertEqual(
            len(
                client.timeseries.calls
            ),
            1,
        )


if __name__ == "__main__":
    unittest.main()
