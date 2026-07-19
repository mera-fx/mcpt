from __future__ import annotations

from copy import deepcopy
import unittest

from exp009_tournament_result import (
    EXPECTED_CANDIDATE_CANONICAL_SHA256,
    EXPECTED_FAMILY_CANONICAL_SHA256,
    EXPECTED_MANIFEST_CANONICAL_SHA256,
    canonical_dataframe_sha256,
    canonical_object_sha256,
    load_candidate_measurements,
    load_family_measurements,
    load_manifest,
    validate_exp009_tournament_result,
    verify_local_exp009_tournament_result,
)


class Exp009TournamentResultTests(unittest.TestCase):
    def test_local_result_is_valid(self) -> None:
        result = verify_local_exp009_tournament_result()
        self.assertEqual(
            result["manifest"]["result_status"],
            "MEASURED_AWAITING_USER_REVIEW",
        )

    def test_result_hashes_are_frozen(self) -> None:
        self.assertEqual(
            canonical_dataframe_sha256(load_candidate_measurements()),
            EXPECTED_CANDIDATE_CANONICAL_SHA256,
        )
        self.assertEqual(
            canonical_dataframe_sha256(load_family_measurements()),
            EXPECTED_FAMILY_CANONICAL_SHA256,
        )
        self.assertEqual(
            canonical_object_sha256(load_manifest()),
            EXPECTED_MANIFEST_CANONICAL_SHA256,
        )

    def test_complete_tournament_remains_visible(self) -> None:
        candidates = load_candidate_measurements()
        families = load_family_measurements()
        self.assertEqual(len(candidates), 24)
        self.assertEqual(candidates["candidate_id"].nunique(), 24)
        self.assertEqual(len(families), 6)
        self.assertEqual(families["family_id"].nunique(), 6)

    def test_opening_drive_family_is_preserved_without_winner_claim(
        self,
    ) -> None:
        result = verify_local_exp009_tournament_result()
        opening_drive = result["candidates"].loc[
            result["candidates"]["family_id"]
            == "opening_drive_continuation"
        ]
        self.assertEqual(len(opening_drive), 4)
        self.assertTrue(opening_drive["pareto_nondominated"].all())
        self.assertTrue(
            (opening_drive["reliability_flag_count"] == 0).all()
        )
        self.assertFalse(result["manifest"]["automatic_winner"])

    def test_user_reference_candidate_exact_measurements(self) -> None:
        candidates = load_candidate_measurements().set_index(
            "candidate_id"
        )
        reference = candidates.loc["opening_drive_0p5_1p5r"]
        self.assertEqual(int(reference["completed_trades"]), 775)
        self.assertAlmostEqual(
            float(reference["trade_profit_factor"]),
            1.3158469945355191,
            places=12,
        )
        self.assertAlmostEqual(float(reference["win_rate"]), 0.52)
        self.assertAlmostEqual(
            float(reference["net_profit_usd"]),
            187850.0,
        )
        self.assertAlmostEqual(
            float(reference["maximum_drawdown_usd"]),
            -24930.0,
        )
        self.assertAlmostEqual(
            float(reference["profitable_year_fraction"]),
            1.0,
        )

    def test_manifest_mutation_is_rejected(self) -> None:
        changed = deepcopy(load_manifest())
        changed["automatic_winner"] = True
        with self.assertRaisesRegex(ValueError, "safety field changed"):
            validate_exp009_tournament_result(
                manifest=changed,
                candidates=load_candidate_measurements(),
                families=load_family_measurements(),
                verify_hashes=False,
            )

    def test_candidate_mutation_is_rejected(self) -> None:
        changed = load_candidate_measurements()
        changed.loc[
            changed["candidate_id"] == "opening_drive_0p5_1p5r",
            "net_profit_usd",
        ] += 1.0
        with self.assertRaisesRegex(ValueError, "net_profit_usd changed"):
            validate_exp009_tournament_result(
                manifest=load_manifest(),
                candidates=changed,
                families=load_family_measurements(),
                verify_hashes=False,
            )


if __name__ == "__main__":
    unittest.main()
