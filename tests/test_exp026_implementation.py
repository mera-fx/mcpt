from __future__ import annotations

import inspect
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from exp026_core import (
    CONTROL_CANDIDATE_IDS,
    DEVELOPMENT_CANDIDATE_IDS,
)
from exp026_implementation_preflight import (
    implementation_preflight,
)
from exp026_runner import (
    IMPLEMENTATION_PATHS,
    LOCKED_PREREGISTRATION_COMMIT,
    PHASE_AUTHORIZATION_MODULES,
    PHASE_COMPLETION_MODULES,
    PHASE_OUTPUT_DIRS,
    PHASE_PARTIAL_DIRS,
    PHASE_REQUIRED_OUTPUTS,
    PREREGISTRATION_PATHS,
    _locked_phase_a_survivors,
    _locked_phase_b_finalists,
    _write_output_manifest,
    load_permitted_ohlcv,
    load_phase_authorization,
    repository_state_preflight,
    run_phase,
)
from exp026_statistics import (
    bootstrap_session_blocks,
    selection_aware_market_mcpt,
)


class Exp026ImplementationTests(unittest.TestCase):
    def test_01_locked_preregistration_commit_is_exact(
        self,
    ) -> None:
        self.assertEqual(
            LOCKED_PREREGISTRATION_COMMIT,
            "ce661c7785fa6d8d409378ee2ad63a00f0e0a9b9",
        )

    def test_02_preregistration_paths_are_protected(
        self,
    ) -> None:
        self.assertEqual(
            set(PREREGISTRATION_PATHS),
            {
                "exp026_preregistration.py",
                "research/EXP-026_preregistration.md",
                "tests/test_exp026_preregistration.py",
                "experiment_lifecycle.py",
                "tests/test_experiment_lifecycle.py",
            },
        )

    def test_03_implementation_scope_is_exact(
        self,
    ) -> None:
        self.assertEqual(
            set(IMPLEMENTATION_PATHS),
            {
                "exp026_core.py",
                "exp026_statistics.py",
                "exp026_runner.py",
                "exp026_implementation_preflight.py",
                "research/EXP-026_implementation_report.md",
                "tests/test_exp026_core.py",
                "tests/test_exp026_implementation.py",
            },
        )

    def test_04_phase_output_names_match_preregistration(
        self,
    ) -> None:
        self.assertEqual(
            PHASE_REQUIRED_OUTPUTS["A"],
            (
                "development_summary.json",
                "candidate_registry.csv",
                "development_metrics.csv",
                "development_annual_results.csv",
                "phase_a_survivors.json",
                "output_hashes.json",
                "report.md",
                "PHASE_A_COMPLETE.json",
            ),
        )
        self.assertEqual(
            PHASE_REQUIRED_OUTPUTS["B"],
            (
                "internal_validation_summary.json",
                "internal_validation_metrics.csv",
                "selected_finalists.json",
                "walk_forward_results.csv",
                "bootstrap_summary.csv",
                "mcpt_summary.json",
                "parameter_stability.csv",
                "output_hashes.json",
                "report.md",
                "report.html",
                "PHASE_B_COMPLETE.json",
            ),
        )
        self.assertEqual(
            PHASE_REQUIRED_OUTPUTS["C"],
            (
                "known_comparison_summary.json",
                "known_comparison_metrics.csv",
                "annual_results.csv",
                "monthly_results.csv",
                "cost_sensitivity.csv",
                "representation_sensitivity.csv",
                "trade_distribution.csv",
                "drawdown_episodes.csv",
                "output_hashes.json",
                "report.md",
                "report.html",
                "PHASE_C_COMPLETE.json",
            ),
        )

    def test_05_authorization_modules_are_separate(
        self,
    ) -> None:
        self.assertEqual(
            PHASE_AUTHORIZATION_MODULES,
            {
                "A": "exp026_phase_a_authorization",
                "B": "exp026_phase_b_authorization",
                "C": "exp026_phase_c_authorization",
            },
        )
        self.assertEqual(
            PHASE_COMPLETION_MODULES,
            {
                "A": "exp026_phase_a_completion",
                "B": "exp026_phase_b_completion",
            },
        )

    def test_06_missing_phase_authorization_is_rejected(
        self,
    ) -> None:
        for phase in ("A", "B", "C"):
            with self.assertRaisesRegex(
                RuntimeError,
                "not authorized",
            ):
                load_phase_authorization(phase)

    def test_07_import_does_not_create_outputs(
        self,
    ) -> None:
        for path in (
            *PHASE_OUTPUT_DIRS.values(),
            *PHASE_PARTIAL_DIRS.values(),
        ):
            self.assertFalse(path.exists())

    def test_08_protected_loader_uses_arrow_filter_before_table(
        self,
    ) -> None:
        source = inspect.getsource(
            load_permitted_ohlcv
        )
        self.assertIn(
            'ds.field("trading_date")',
            source,
        )
        self.assertIn(
            "filter=predicate",
            source,
        )
        self.assertLess(
            source.index("filter=predicate"),
            source.index("to_pandas"),
        )
        self.assertIn(
            'allowed_session_end > "2025-12-31"',
            source,
        )

    def test_09_preflight_does_not_call_market_loader(
        self,
    ) -> None:
        source = inspect.getsource(
            implementation_preflight
        )
        self.assertNotIn(
            "load_permitted_ohlcv",
            source,
        )
        self.assertIn(
            "inspect_parquet_metadata",
            source,
        )
        self.assertIn(
            "verify_frozen_series_bytes",
            source,
        )

    def test_10_repository_preflight_rejects_unknown_phase(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "Unknown EXP-026 phase",
        ):
            repository_state_preflight("D")

    def test_11_runner_rejects_unknown_phase(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "Unknown EXP-026 phase",
        ):
            run_phase("D")

    def test_12_phase_a_survivor_boundary_is_enforced(
        self,
    ) -> None:
        valid = _locked_phase_a_survivors(
            {
                "survivor_candidate_ids": (
                    "gap_fade_0p50_1r",
                    "premarket_continuation_0p50_time",
                    "opening_drive_0p50_time",
                )
            }
        )
        self.assertEqual(len(valid), 3)
        with self.assertRaisesRegex(
            RuntimeError,
            "exceed two per family",
        ):
            _locked_phase_a_survivors(
                {
                    "survivor_candidate_ids": (
                        "gap_fade_0p25_1r",
                        "gap_fade_0p50_1r",
                        "gap_fade_0p75_1r",
                    )
                }
            )

    def test_13_phase_b_finalist_boundary_is_enforced(
        self,
    ) -> None:
        valid = _locked_phase_b_finalists(
            {
                "finalist_candidate_ids": (
                    "gap_fade_0p50_1r",
                    "premarket_continuation_0p50_time",
                    "opening_drive_0p50_time",
                )
            }
        )
        self.assertEqual(len(valid), 3)
        with self.assertRaisesRegex(
            RuntimeError,
            "exceed one per family",
        ):
            _locked_phase_b_finalists(
                {
                    "finalist_candidate_ids": (
                        "gap_fade_0p25_1r",
                        "gap_fade_0p50_1r",
                    )
                }
            )

    def test_14_controls_cannot_enter_selection_population(
        self,
    ) -> None:
        self.assertTrue(
            set(CONTROL_CANDIDATE_IDS).isdisjoint(
                DEVELOPMENT_CANDIDATE_IDS
            )
        )

    def test_15_mcpt_and_bootstrap_defaults_are_locked(
        self,
    ) -> None:
        mcpt = inspect.signature(
            selection_aware_market_mcpt
        )
        bootstrap = inspect.signature(
            bootstrap_session_blocks
        )
        self.assertEqual(
            mcpt.parameters[
                "permutations"
            ].default,
            1_000,
        )
        self.assertEqual(
            mcpt.parameters[
                "random_seed"
            ].default,
            26_026,
        )
        self.assertEqual(
            bootstrap.parameters[
                "resamples"
            ].default,
            10_000,
        )
        self.assertEqual(
            bootstrap.parameters[
                "random_seed"
            ].default,
            26_027,
        )

    def test_16_output_manifest_records_no_trading_authority(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            (output / "example.txt").write_text(
                "example\n",
                encoding="utf-8",
            )
            with mock.patch.dict(
                PHASE_REQUIRED_OUTPUTS,
                {
                    **PHASE_REQUIRED_OUTPUTS,
                    "A": (
                        "output_hashes.json",
                        "PHASE_A_COMPLETE.json",
                    ),
                },
                clear=True,
            ):
                _write_output_manifest(
                    output,
                    marker_name=(
                        "PHASE_A_COMPLETE.json"
                    ),
                    phase="A",
                    summary={"test": True},
                )
            marker = (
                output / "PHASE_A_COMPLETE.json"
            ).read_text(encoding="utf-8")
            self.assertIn(
                '"protected_2026_accessed": false',
                marker,
            )
            self.assertIn(
                '"paper_trading_authorized": false',
                marker,
            )
            self.assertIn(
                '"live_trading_authorized": false',
                marker,
            )


if __name__ == "__main__":
    unittest.main()
