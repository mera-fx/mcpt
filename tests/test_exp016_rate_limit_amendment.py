from __future__ import annotations

import unittest

from exp016_rate_limit_amendment import (
    COMPLETED_BEFORE_RATE_LIMIT,
    EXPECTED_IMPLEMENTATION_COMMIT,
    MINIMUM_RETRY_WAIT_SECONDS,
    OBSERVED_RATE_LIMIT_FAILURE,
    get_exp016_rate_limit_amendment,
    validate_exp016_rate_limit_amendment,
)


class Exp016RateLimitAmendmentTests(unittest.TestCase):
    def test_amendment_is_valid(self) -> None:
        validate_exp016_rate_limit_amendment()

    def test_base_implementation_commit_is_frozen(self) -> None:
        self.assertEqual(
            EXPECTED_IMPLEMENTATION_COMMIT,
            "a0f1c8c40d80b5a13f38604b2608c21528ad7bcd",
        )

    def test_five_completed_samples_are_frozen(self) -> None:
        self.assertEqual(len(COMPLETED_BEFORE_RATE_LIMIT), 5)
        self.assertEqual(
            [item["window_id"] for item in COMPLETED_BEFORE_RATE_LIMIT],
            [
                "2020_march_dst_roll_volatility",
                "2021_thanksgiving",
                "2022_june_roll",
                "2023_march_dst_roll",
                "2024_thanksgiving",
            ],
        )
        self.assertEqual(
            COMPLETED_BEFORE_RATE_LIMIT[0]["sha256"],
            "1f307ae35720423829e682d050a18f7e1fee87a2864ebc3f305e85209bcdc3a1",
        )

    def test_exact_429_failure_is_frozen(self) -> None:
        self.assertEqual(
            OBSERVED_RATE_LIMIT_FAILURE,
            {
                "window_id": "2025_march_dst_roll",
                "start": "2025-03-07",
                "end": "2025-03-21",
                "request_attempt": 1,
                "status": "FAILED",
                "safe_error": (
                    'LSEError: [429] {"detail":"too many export requests; '
                    'try again shortly"}'
                ),
            },
        )

    def test_only_one_delayed_retry_is_authorized(self) -> None:
        permission = get_exp016_rate_limit_amendment()["amended_permission"]
        self.assertEqual(permission["maximum_additional_requests"], 1)
        self.assertEqual(
            permission["minimum_wait_seconds_after_failure"],
            MINIMUM_RETRY_WAIT_SECONDS,
        )
        self.assertTrue(permission["original_failed_lock_must_remain_unchanged"])
        self.assertTrue(permission["other_window_requests_prohibited"])
        self.assertTrue(permission["additional_retry_after_failure_prohibited"])

    def test_request_accounting_is_seven_attempts_six_successes(self) -> None:
        accounting = get_exp016_rate_limit_amendment()["request_accounting"]
        self.assertEqual(accounting["maximum_total_attempts"], 7)
        self.assertEqual(accounting["maximum_successful_samples"], 6)

    def test_failed_retry_stops_remote_access(self) -> None:
        failure = get_exp016_rate_limit_amendment()[
            "failure_after_amended_retry"
        ]
        self.assertTrue(failure["no_further_remote_attempt"])
        self.assertEqual(
            failure["final_access_classification"],
            "ACCESS_UNAVAILABLE",
        )

    def test_retry_count_mutation_is_rejected(self) -> None:
        changed = get_exp016_rate_limit_amendment()
        changed["amended_permission"]["maximum_additional_requests"] = 2
        with self.assertRaisesRegex(ValueError, "retry permission"):
            validate_exp016_rate_limit_amendment(changed)

    def test_research_boundary_mutation_is_rejected(self) -> None:
        changed = get_exp016_rate_limit_amendment()
        changed["research_boundary"]["measurements_changed"] = True
        with self.assertRaisesRegex(ValueError, "research boundary"):
            validate_exp016_rate_limit_amendment(changed)
