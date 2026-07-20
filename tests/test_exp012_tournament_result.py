from __future__ import annotations

from copy import deepcopy
import unittest

from exp012_tournament_result import (
    EXPECTED_CANDIDATE_CANONICAL_SHA256,
    EXPECTED_FAMILY_CANONICAL_SHA256,
    EXPECTED_MANIFEST_CANONICAL_SHA256,
    canonical_dataframe_sha256,
    canonical_object_sha256,
    load_candidate_measurements,
    load_family_measurements,
    load_manifest,
    validate_exp012_tournament_result,
    verify_local_exp012_tournament_result,
)


class Exp012TournamentResultTests(unittest.TestCase):
    def test_local_result_is_valid(self) -> None:
        result = verify_local_exp012_tournament_result()
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

    def test_three_review_candidates_remain_context_not_winners(
        self,
    ) -> None:
        result = verify_local_exp012_tournament_result()
        candidates = result["candidates"].set_index("candidate_id")
        expected = {
            "gap_fade_0p50_1r",
            "premarket_continuation_0p50_time",
            "premarket_continuation_0p75_time",
        }
        self.assertTrue(expected.issubset(set(candidates.index)))
        self.assertFalse(result["manifest"]["automatic_winner"])
        self.assertEqual(
            int(candidates.loc["premarket_continuation_0p75_time"][
                "reliability_flag_count"
            ]),
            1,
        )

    def test_manifest_mutation_is_rejected(self) -> None:
        changed = deepcopy(load_manifest())
        changed["automatic_winner"] = True
        with self.assertRaisesRegex(ValueError, "safety field changed"):
            validate_exp012_tournament_result(
                manifest=changed,
                candidates=load_candidate_measurements(),
                families=load_family_measurements(),
                verify_hashes=False,
            )

    def test_candidate_mutation_is_rejected(self) -> None:
        changed = load_candidate_measurements()
        changed.loc[
            changed["candidate_id"] == "gap_fade_0p50_1r",
            "net_profit_usd",
        ] += 1.0
        with self.assertRaisesRegex(ValueError, "net_profit_usd changed"):
            validate_exp012_tournament_result(
                manifest=load_manifest(),
                candidates=changed,
                families=load_family_measurements(),
                verify_hashes=False,
            )

    def test_missing_values_have_stable_canonical_hash(self) -> None:
        candidates = load_candidate_measurements()
        self.assertTrue(candidates["worst_100_trade_result_usd"].isna().any())
        self.assertEqual(
            canonical_dataframe_sha256(candidates),
            EXPECTED_CANDIDATE_CANONICAL_SHA256,
        )


if __name__ == "__main__":
    unittest.main()
