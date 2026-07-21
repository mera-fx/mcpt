from __future__ import annotations

import os
from pathlib import Path
import subprocess


PROJECT_DIR = Path(__file__).resolve().parent
MEASUREMENT_PATH = PROJECT_DIR / "exp016_measurements.py"
TEST_PATH = PROJECT_DIR / "tests" / "test_exp016_measurements.py"
RESULT_PATH = (
    PROJECT_DIR
    / "results"
    / "EXP-016"
    / "source_qualification"
    / "audit_result.json"
)
EXPECTED_HEAD = "a76e4ee00b07b03b6f1c6e61ed32cc1db1b16f37"


def _run_git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=PROJECT_DIR,
        text=True,
        capture_output=True,
        check=True,
    )


def _replace_exact(
    source: str,
    old: str,
    new: str,
    *,
    expected_count: int = 1,
    label: str,
) -> str:
    count = source.count(old)
    if count != expected_count:
        raise RuntimeError(
            f"{label}: expected {expected_count} exact match(es), found {count}."
        )
    return source.replace(old, new)


def _verify_preconditions() -> None:
    if os.environ.get("LSE_API_KEY"):
        raise RuntimeError(
            "Remove LSE_API_KEY before applying the local measurement correction."
        )
    if RESULT_PATH.exists():
        raise RuntimeError(
            "EXP-016 audit results already exist. Stop for reviewed handling."
        )

    head = _run_git("rev-parse", "HEAD").stdout.strip()
    if head != EXPECTED_HEAD:
        raise RuntimeError(
            f"Expected HEAD {EXPECTED_HEAD}; found {head}."
        )

    for path in (MEASUREMENT_PATH, TEST_PATH):
        if not path.is_file():
            raise RuntimeError(f"Missing expected file: {path}")
        relative = str(path.relative_to(PROJECT_DIR))
        changed = subprocess.run(
            ["git", "diff", "--quiet", "--", relative],
            cwd=PROJECT_DIR,
            check=False,
        )
        if changed.returncode != 0:
            raise RuntimeError(
                f"Tracked target already has local changes: {relative}"
            )


def _correct_measurements(source: str) -> str:
    if "OUTSIDE_ROLL_WINDOW_IDS" in source:
        raise RuntimeError(
            "The EXP-016 measurement-alignment correction already appears applied."
        )

    source = _replace_exact(
        source,
        '''    "time left",
)


class Exp016MeasurementError''',
        '''    "time left",
)

ALL_WINDOW_IDS = (
    "2020_march_dst_roll_volatility",
    "2021_thanksgiving",
    "2022_june_roll",
    "2023_march_dst_roll",
    "2024_thanksgiving",
    "2025_march_dst_roll",
)
ROLL_WINDOW_IDS = frozenset(
    {
        "2020_march_dst_roll_volatility",
        "2022_june_roll",
        "2023_march_dst_roll",
        "2025_march_dst_roll",
    }
)
OUTSIDE_ROLL_WINDOW_IDS = frozenset(
    {
        "2021_thanksgiving",
        "2024_thanksgiving",
    }
)


class Exp016MeasurementError''',
        label="window classification insertion",
    )

    source = _replace_exact(
        source,
        '''                "matched_timestamp_share": None,
                "close_within_one_tick_share": None,
''',
        '''                "expected_minute_completeness": None,
                "matched_timestamp_share": None,
                "close_within_one_tick_share": None,
''',
        expected_count=2,
        label="unresolved comparison schema",
    )

    source = _replace_exact(
        source,
        '''def utc_window_bounds(start: str, end: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    lower = pd.Timestamp(start, tz="UTC")
    upper = pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)
    return lower, upper


def compare_with_reference(
''',
        '''def utc_window_bounds(start: str, end: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    lower = pd.Timestamp(start, tz="UTC")
    upper = pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)
    return lower, upper


def _difference_bucket_counts(
    values: pd.Series,
    prefix: str,
) -> dict[str, int]:
    return {
        f"{prefix}_diff_exact_rows": int(values.eq(0.0).sum()),
        f"{prefix}_diff_gt_0_to_0p25_rows": int(
            values.gt(0.0).where(values.le(0.25), False).sum()
        ),
        f"{prefix}_diff_gt_0p25_to_1_rows": int(
            values.gt(0.25).where(values.le(1.0), False).sum()
        ),
        f"{prefix}_diff_gt_1_rows": int(values.gt(1.0).sum()),
    }


def compare_with_reference(
''',
        label="difference bucket helper",
    )

    source = _replace_exact(
        source,
        '''    close_diff = matched["close_abs_diff"]
    exact = int(close_diff.eq(0.0).sum())
    quarter = int(close_diff.gt(0.0).where(close_diff.le(0.25), False).sum())
    one_point = int(close_diff.gt(0.25).where(close_diff.le(1.0), False).sum())
    over_one = int(close_diff.gt(1.0).sum())

''',
        '''    close_diff = matched["close_abs_diff"]
    difference_buckets: dict[str, int] = {}
    for column in ("open", "high", "low", "close"):
        difference_buckets.update(
            _difference_bucket_counts(
                matched[f"{column}_abs_diff"],
                column,
            )
        )

''',
        label="OHLC bucket calculation",
    )

    source = _replace_exact(
        source,
        '''        "quantower_only_rows": int(len(reference_only)),
        "matched_timestamp_share": matched_share,
        "close_within_one_tick_share": within_tick,
        "close_diff_exact_rows": exact,
        "close_diff_gt_0_to_0p25_rows": quarter,
        "close_diff_gt_0p25_to_1_rows": one_point,
        "close_diff_gt_1_rows": over_one,
''',
        '''        "quantower_only_rows": int(len(reference_only)),
        "expected_minute_completeness": matched_share,
        "matched_timestamp_share": matched_share,
        "close_within_one_tick_share": within_tick,
        **difference_buckets,
''',
        label="measured comparison schema",
    )

    source = _replace_exact(
        source,
        '''    if (
        cross_source["matched_timestamp_share"].min() < 0.999
        or cross_source["close_within_one_tick_share"].min() < 0.995
    ):
        return "NOT_QUALIFIED"

''',
        '''    if "window_id" not in cross_source.columns:
        return "STRUCTURE_UNRESOLVED"
    window_ids = set(cross_source["window_id"].astype(str))
    if window_ids != set(ALL_WINDOW_IDS):
        return "STRUCTURE_UNRESOLVED"

    required_overlap = cross_source[
        [
            "expected_minute_completeness",
            "matched_timestamp_share",
        ]
    ].apply(pd.to_numeric, errors="coerce")
    if not np.isfinite(required_overlap.to_numpy(dtype=float)).all():
        return "STRUCTURE_UNRESOLVED"
    if (
        required_overlap["expected_minute_completeness"].min() < 0.999
        or required_overlap["matched_timestamp_share"].min() < 0.999
    ):
        return "NOT_QUALIFIED"

    outside_roll = cross_source[
        cross_source["window_id"].isin(OUTSIDE_ROLL_WINDOW_IDS)
    ]
    if len(outside_roll) != len(OUTSIDE_ROLL_WINDOW_IDS):
        return "STRUCTURE_UNRESOLVED"
    outside_roll_close_share = pd.to_numeric(
        outside_roll["close_within_one_tick_share"],
        errors="coerce",
    )
    if not np.isfinite(outside_roll_close_share.to_numpy(dtype=float)).all():
        return "STRUCTURE_UNRESOLVED"
    if outside_roll_close_share.min() < 0.995:
        return "NOT_QUALIFIED"

''',
        label="preregistered classification thresholds",
    )

    compile(source, str(MEASUREMENT_PATH), "exec")
    return source


def _correct_existing_tests(source: str) -> str:
    if "ALL_WINDOW_IDS" in source:
        raise RuntimeError(
            "The existing EXP-016 measurement tests already appear corrected."
        )

    source = _replace_exact(
        source,
        '''from exp016_measurements import (
    canonicalize_vendor_frame,
''',
        '''from exp016_measurements import (
    ALL_WINDOW_IDS,
    canonicalize_vendor_frame,
''',
        label="test import",
    )

    source = _replace_exact(
        source,
        '''        self.assertEqual(metrics["matched_timestamp_share"], 1.0)
        self.assertEqual(metrics["close_within_one_tick_share"], 1.0)
        self.assertEqual(len(detail), 3)
''',
        '''        self.assertEqual(metrics["expected_minute_completeness"], 1.0)
        self.assertEqual(metrics["matched_timestamp_share"], 1.0)
        self.assertEqual(metrics["close_within_one_tick_share"], 1.0)
        for column in ("open", "high", "low", "close"):
            self.assertEqual(metrics[f"{column}_diff_exact_rows"], 3)
            self.assertEqual(
                metrics[f"{column}_diff_gt_0_to_0p25_rows"],
                0,
            )
            self.assertEqual(
                metrics[f"{column}_diff_gt_0p25_to_1_rows"],
                0,
            )
            self.assertEqual(metrics[f"{column}_diff_gt_1_rows"], 0)
        self.assertEqual(len(detail), 3)
''',
        label="exact comparison assertions",
    )

    source = _replace_exact(
        source,
        '''        cross = pd.DataFrame(
            [
                {
                    "comparison_status": "MEASURED",
                    "matched_timestamp_share": 1.0,
                    "close_within_one_tick_share": 1.0,
                }
                for _ in range(6)
            ]
        )
''',
        '''        cross = pd.DataFrame(
            [
                {
                    "window_id": window_id,
                    "comparison_status": "MEASURED",
                    "expected_minute_completeness": 1.0,
                    "matched_timestamp_share": 1.0,
                    "close_within_one_tick_share": 1.0,
                }
                for window_id in ALL_WINDOW_IDS
            ]
        )
''',
        label="classification fixture",
    )

    compile(source, str(TEST_PATH), "exec")
    return source


def main() -> None:
    _verify_preconditions()

    measurement_source = MEASUREMENT_PATH.read_text(encoding="utf-8")
    test_source = TEST_PATH.read_text(encoding="utf-8")

    corrected_measurement = _correct_measurements(measurement_source)
    corrected_test = _correct_existing_tests(test_source)

    MEASUREMENT_PATH.write_text(
        corrected_measurement,
        encoding="utf-8",
        newline="\n",
    )
    TEST_PATH.write_text(
        corrected_test,
        encoding="utf-8",
        newline="\n",
    )

    print("Applied EXP-016 preregistered measurement alignment.")
    print("Sample contents inspected: False")
    print("Audit results viewed: False")
    print("Remote request performed: False")
    print("API key accessed: False")
    print("Sample windows changed: False")
    print("Qualification thresholds changed: False")
    print("Outside-roll threshold scope corrected: True")
    print("Expected-minute completeness exposed: True")
    print("OHLC difference buckets exposed: True")


if __name__ == "__main__":
    main()
