from __future__ import annotations

import argparse
from datetime import (
    datetime,
    timezone,
)
import json
import math
from pathlib import Path
import subprocess
from typing import Any

import numpy as np
import pandas as pd

from exp006_data import (
    load_exp006_frozen_data,
)
from exp006_optimization_result import (
    verify_local_exp006_optimization_decision,
)
from exp007_replication_result import (
    verify_local_exp007_replication_decision,
)
from exp008_bootstrap import (
    bootstrap_exp008_trade_metrics,
)
from exp008_candidate_scoring import (
    BASELINE,
    evaluate_candidate_grid,
    select_candidate,
    selected_row,
)
from exp008_evaluation import (
    EXP007_BASELINE_NQ_PF,
    evaluate_exp008,
)
from exp008_implementation import (
    validate_exp008_implementation,
)
from exp008_orb import (
    Exp008Parameters,
    prepare_exp008_arrays,
    run_exp008_candidate_from_arrays,
)
from exp008_preregistration import (
    get_exp008_preregistration,
    validate_exp008_preregistration,
)
from exp008_report import (
    build_exp008_no_candidate_report,
    build_exp008_report,
)
from exp008_selection_mcpt import (
    run_exp008_selection_mcpt,
)
from exp008_walk_forward import (
    run_exp008_anchored_walk_forward,
)
from experiment_lifecycle import (
    get_experiment_lifecycle,
)


PROJECT_DIR = Path(__file__).resolve().parent
RESULT_DIR = (
    PROJECT_DIR
    / "results"
    / "EXP-008"
    / "exit_geometry"
)
REPORT_DIR = (
    PROJECT_DIR
    / "reports"
    / "EXP-008-research-lab"
)
DECISION_FILE = (
    RESULT_DIR
    / "optimization_decision.json"
)
CHECKPOINT_FILE = (
    RESULT_DIR
    / "mcpt_checkpoint.json"
)


def _run_git(
    *args: str,
) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=PROJECT_DIR,
        text=True,
        capture_output=True,
        check=True,
    )
    return completed.stdout.strip()


def git_provenance(
) -> dict[str, Any]:
    commit = _run_git(
        "rev-parse",
        "HEAD",
    )
    dirty = bool(
        _run_git(
            "status",
            "--porcelain",
        )
    )
    return {
        "commit": commit,
        "short_commit": commit[:7],
        "working_tree_clean": (
            not dirty
        ),
    }


def _json_safe(
    value: Any,
) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }
    if isinstance(
        value,
        (list, tuple),
    ):
        return [
            _json_safe(item)
            for item in value
        ]
    if isinstance(
        value,
        (np.integer,),
    ):
        return int(value)
    if isinstance(
        value,
        (
            np.floating,
            float,
        ),
    ):
        number = float(value)
        return (
            number
            if math.isfinite(number)
            else None
        )
    if isinstance(
        value,
        (
            np.bool_,
            bool,
        ),
    ):
        return bool(value)
    if isinstance(
        value,
        (
            pd.Timestamp,
            datetime,
        ),
    ):
        return value.isoformat()
    return value


def _atomic_json(
    payload: dict[str, Any],
    path: Path,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )
    temporary.write_text(
        json.dumps(
            _json_safe(payload),
            indent=2,
            allow_nan=False,
        ),
        encoding="utf-8",
    )
    temporary.replace(path)


def _verify_lifecycle() -> None:
    exp005 = get_experiment_lifecycle(
        "EXP-005"
    )
    exp006 = get_experiment_lifecycle(
        "EXP-006"
    )
    exp007 = get_experiment_lifecycle(
        "EXP-007"
    )
    exp008 = get_experiment_lifecycle(
        "EXP-008"
    )

    if (
        exp005.stage
        != "ACCEPTED_FOR_PAPER_TESTING"
    ):
        raise RuntimeError(
            "EXP-005 accepted control stage "
            "changed."
        )
    if exp006.stage != "REJECTED":
        raise RuntimeError(
            "EXP-006 rejection stage changed."
        )
    if exp007.stage != "REJECTED":
        raise RuntimeError(
            "EXP-007 rejection stage changed."
        )
    if exp008.stage != "PRE_REGISTERED":
        raise RuntimeError(
            "EXP-008 must remain PRE_REGISTERED "
            "before running."
        )

    frozen_exp006 = (
        verify_local_exp006_optimization_decision()
    )
    if (
        frozen_exp006[
            "evaluation"
        ]["decision"]
        != "REJECT_EXP006_KEEP_EXP005_CONTROL"
    ):
        raise RuntimeError(
            "The frozen EXP-006 decision changed."
        )

    frozen_exp007 = (
        verify_local_exp007_replication_decision()
    )
    if (
        frozen_exp007[
            "evaluation"
        ]["decision"]
        != "REJECT_EXP007_PRESERVE_AS_NEGATIVE_RESULT"
    ):
        raise RuntimeError(
            "The frozen EXP-007 decision changed."
        )


def protected_preflight(
) -> tuple[dict[str, Any], Any]:
    validate_exp008_preregistration()
    validate_exp008_implementation()
    _verify_lifecycle()

    git = git_provenance()
    if not git[
        "working_tree_clean"
    ]:
        raise RuntimeError(
            "Commit the EXP-008 implementation "
            "before preflight or results."
        )
    if DECISION_FILE.exists():
        raise RuntimeError(
            "EXP-008 already has a frozen decision. "
            "Do not rerun it."
        )

    frozen = load_exp006_frozen_data()
    if (
        int(
            frozen.audit[
                "included_sessions"
            ]
        )
        != 1639
    ):
        raise RuntimeError(
            "EXP-008 frozen session count changed."
        )

    print()
    print(
        "EXP-008 IMPLEMENTATION PREFLIGHT"
    )
    print(
        "================================"
    )
    print(
        "Lifecycle:       PRE_REGISTERED"
    )
    print(
        "Implementation:  IMPLEMENTED_NOT_RUN"
    )
    print(
        "Strategy:        long-only ORB exit geometry"
    )
    print(
        "Grid:            27 locked combinations"
    )
    print(
        "Opening ranges:  15, 30, 45 minutes"
    )
    print(
        "Targets:         0.5R, 1.0R, 1.5R"
    )
    print(
        "Forced flats:    12:00, 14:00, 15:55"
    )
    print(
        "Sessions:        1,639"
    )
    print(
        "Walk-forward:    5 anchored annual folds"
    )
    print(
        "NQ MCPT:         1,000 selection-aware permutations"
    )
    print(
        "Selection inside every permutation: True"
    )
    print(
        f"Git commit:      {git['short_commit']}"
    )
    print(
        "Git clean:       True"
    )
    print(
        "EXP-005/006/007 changed: False"
    )
    print(
        "Results:         not calculated"
    )
    print(
        "================================"
    )

    return git, frozen


def _combined_yearly(
    nq_yearly: pd.DataFrame,
    mnq_yearly: pd.DataFrame,
) -> pd.DataFrame:
    nq = nq_yearly.copy()
    nq.insert(
        0,
        "symbol",
        "NQ",
    )
    mnq = mnq_yearly.copy()
    mnq.insert(
        0,
        "symbol",
        "MNQ",
    )
    return pd.concat(
        [
            nq,
            mnq,
        ],
        ignore_index=True,
    )


def _cost_sensitivity(
    *,
    parameters: Exp008Parameters,
    nq_arrays: Any,
    mnq_arrays: Any,
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
]:
    rows: list[dict[str, Any]] = []
    two_tick_nq: (
        dict[str, Any] | None
    ) = None

    for ticks in (
        0.0,
        1.0,
        2.0,
    ):
        for (
            symbol,
            arrays,
        ) in (
            (
                "NQ",
                nq_arrays,
            ),
            (
                "MNQ",
                mnq_arrays,
            ),
        ):
            result = (
                run_exp008_candidate_from_arrays(
                    arrays,
                    parameters=parameters,
                    symbol=symbol,
                    slippage_ticks_per_side=(
                        ticks
                    ),
                )
            )
            summary = result.summary
            row = {
                "parameter_key": (
                    parameters.key
                ),
                "symbol": symbol,
                "slippage_ticks_per_side": (
                    float(ticks)
                ),
                "round_trip_cost_usd": (
                    float(
                        summary[
                            "round_trip_cost_usd"
                        ]
                    )
                ),
                "completed_trades": int(
                    summary[
                        "completed_trades"
                    ]
                ),
                "trade_profit_factor": (
                    float(
                        summary[
                            "trade_profit_factor"
                        ]
                    )
                ),
                "net_profit_usd": float(
                    summary[
                        "net_profit_usd"
                    ]
                ),
                "average_trade_usd": (
                    float(
                        summary[
                            "average_trade_usd"
                        ]
                    )
                ),
                "maximum_drawdown_usd": (
                    float(
                        summary[
                            "maximum_drawdown_usd"
                        ]
                    )
                ),
            }
            rows.append(row)

            if (
                symbol == "NQ"
                and ticks == 2.0
            ):
                two_tick_nq = row

    if two_tick_nq is None:
        raise RuntimeError(
            "EXP-008 two-tick NQ stress "
            "result is missing."
        )

    return (
        pd.DataFrame(rows),
        two_tick_nq,
    )



def _zero_final_candidate_yearly() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "year": [
                2021,
                2022,
                2023,
                2024,
                2025,
            ],
            "completed_trades": [0] * 5,
            "net_profit_usd": [0.0] * 5,
            "trade_profit_factor": [0.0] * 5,
            "average_trade_usd": [0.0] * 5,
            "profitable": [False] * 5,
        }
    )


def _complete_no_candidate_outcome(
    *,
    git: dict[str, Any],
    frozen: Any,
    nq_arrays: Any,
    scored_grid: pd.DataFrame,
    selection: Any,
    workers: int,
) -> None:
    print(
        "No stable eligible full-sample candidate was selected."
    )
    print(
        "Continuing the locked walk-forward and MCPT procedures "
        "to record a formal rejection."
    )

    print(
        "Running five anchored walk-forward folds..."
    )
    walk_forward_result = (
        run_exp008_anchored_walk_forward(
            nq_arrays
        )
    )

    print(
        "Running locked selection-aware MCPT with the "
        "preregistered no-candidate statistic of 0.0..."
    )
    (
        mcpt_frame,
        mcpt_p_value,
        mcpt_info,
    ) = run_exp008_selection_mcpt(
        frozen.nq_1m,
        real_selected_trade_profit_factor=0.0,
        requested_workers=workers,
        checkpoint_file=CHECKPOINT_FILE,
        one_minute_fingerprint=(
            frozen.audit["fingerprints"]["NQ_1m"]
        ),
    )

    zero_yearly = _zero_final_candidate_yearly()
    evaluation = evaluate_exp008(
        selected_row=None,
        nq_summary=None,
        mnq_summary=None,
        nq_yearly_results=zero_yearly,
        walk_forward_results=(
            walk_forward_result.folds
        ),
        nq_two_tick_summary=None,
        mcpt_p_value=mcpt_p_value,
    )

    exceedances = int(
        mcpt_frame[
            "permutation_ge_real"
        ].sum()
    )
    finite_pf = mcpt_frame[
        "selected_trade_profit_factor"
    ].replace(
        [np.inf, -np.inf],
        np.nan,
    ).dropna()
    selection_counts = (
        mcpt_frame[
            "selected_parameter_key"
        ]
        .replace("", "NO_ELIGIBLE_CANDIDATE")
        .value_counts()
        .sort_index()
        .to_dict()
    )

    baseline_rows = scored_grid.loc[
        scored_grid[
            "parameter_key"
        ].eq(BASELINE.key)
    ]
    if len(baseline_rows) != 1:
        raise RuntimeError(
            "EXP-008 frozen EXP-007 baseline row "
            "is not unique."
        )
    baseline_row = baseline_rows.iloc[0]
    preregistration = get_exp008_preregistration()

    decision = {
        "schema_version": 1,
        "experiment_id": "EXP-008",
        "stage": (
            "STRUCTURED_EXIT_GEOMETRY_OPTIMIZATION"
        ),
        "calculated_at_utc": datetime.now(
            timezone.utc
        ).isoformat(timespec="seconds"),
        "git": git,
        "data": {
            "source_experiment": "EXP-005",
            "included_sessions": 1639,
            "one_minute_rows_per_symbol": 639210,
            "five_minute_rows_per_symbol": 127842,
            "fingerprints": frozen.audit[
                "fingerprints"
            ],
            "new_data_cleaning_decisions": 0,
        },
        "grid": {
            "dimensions": preregistration[
                "parameter_grid"
            ]["dimensions"],
            "combination_count": 27,
            "exp007_baseline_parameter_key": BASELINE.key,
            "eligible_candidates": selection.eligible_count,
            "stable_eligible_candidates": (
                selection.stable_eligible_count
            ),
            "selected_parameter_key": None,
            "selected_parameters": None,
            "selected_grid_row": None,
        },
        "selection": {
            "market": "NQ",
            "procedure": preregistration[
                "candidate_selection"
            ],
            "selected_parameters": None,
            "selected_candidate_neighbor_keys": [],
            "selected_candidate_neighbors": [],
            "no_eligible_candidate_statistic": 0.0,
        },
        "results": {
            "NQ": None,
            "MNQ": None,
        },
        "walk_forward": {
            "fold_count": 5,
            "profitable_test_folds": (
                walk_forward_result.profitable_test_folds
            ),
            "combined_test_net_profit_usd": (
                walk_forward_result.combined_test_net_profit_usd
            ),
            "folds": walk_forward_result.folds.to_dict(
                orient="records"
            ),
        },
        "final_candidate_annual_evaluation": {
            "years": [2021, 2022, 2023, 2024, 2025],
            "profitable_nq_years": 0,
            "combined_2021_2025_nq_net_profit_usd": 0.0,
            "status": "NOT_APPLICABLE_NO_SELECTED_CANDIDATE",
        },
        "cost_sensitivity": [],
        "bootstrap": {
            "status": "NOT_RUN_NO_SELECTED_CANDIDATE",
            "resamples": 10000,
            "random_seed": 4801,
            "decision_gate": False,
        },
        "mcpt": {
            "market": "NQ",
            "permutations": 1000,
            "base_seed": 48,
            "test_statistic": (
                "selected_candidate_trade_profit_factor"
            ),
            "real_selected_trade_profit_factor": 0.0,
            "permutations_at_least_real": exceedances,
            "p_value": mcpt_p_value,
            "permutation_selected_pf_median": (
                float(finite_pf.median())
                if len(finite_pf)
                else None
            ),
            "permutation_selected_pf_maximum": (
                float(finite_pf.max())
                if len(finite_pf)
                else None
            ),
            "selected_parameter_counts": selection_counts,
            "run_info": mcpt_info.to_dict(),
            "all_27_candidates_inside_each_permutation": True,
            "selection_inside_each_permutation": True,
        },
        "baseline_comparison": {
            "exp007_parameter_key": BASELINE.key,
            "exp007_frozen_nq_trade_profit_factor": (
                EXP007_BASELINE_NQ_PF
            ),
            "exp007_nq_trade_profit_factor": float(
                baseline_row["nq_trade_profit_factor"]
            ),
            "exp007_nq_net_profit_usd": float(
                baseline_row["nq_net_profit_usd"]
            ),
            "exp008_selected_parameter_key": None,
            "exp008_selected_nq_trade_profit_factor": None,
            "absolute_profit_factor_difference": None,
            "strict_improvement_required": True,
            "fixed_minimum_improvement_amount": None,
        },
        "evaluation": evaluation,
        "historical_status": (
            "EXPLORATORY_BECAUSE_2019_2025_WAS_ALREADY_VIEWED"
        ),
        "best_possible_pass_action": (
            "LOCK_EXP008_EXIT_GEOMETRY_CANDIDATE_FOR_"
            "NEW_FORWARD_PAPER_COMPARISON"
        ),
        "exp005_control_changed": False,
        "exp006_result_changed": False,
        "exp007_result_changed": False,
        "live_trading_authorized": False,
        "automatic_lifecycle_source_edit": False,
    }

    scored_grid.to_csv(
        RESULT_DIR / "complete_candidate_grid.csv",
        index=False,
    )
    pd.DataFrame().to_csv(
        RESULT_DIR / "selected_neighbor_evidence.csv",
        index=False,
    )
    walk_forward_result.folds.to_csv(
        RESULT_DIR / "anchored_walk_forward.csv",
        index=False,
    )
    mcpt_frame.to_csv(
        RESULT_DIR / "mcpt_results.csv",
        index=False,
    )
    _atomic_json(
        decision,
        DECISION_FILE,
    )

    report = build_exp008_no_candidate_report(
        decision=_json_safe(decision),
        grid=scored_grid,
        walk_forward=walk_forward_result.folds,
        mcpt=mcpt_frame,
        output_dir=REPORT_DIR,
    )

    print()
    print(
        "EXP-008 exit-geometry optimization completed."
    )
    print(
        f"Decision: {evaluation['decision']}"
    )
    print(
        "Selected parameters: none"
    )
    print(
        "Stable eligible candidates: 0"
    )
    print(
        "Selection-aware MCPT p-value: "
        f"{mcpt_p_value:.6f}"
    )
    print(
        "Failed gates: "
        + ", ".join(
            evaluation["failed_gates"]
        )
    )
    print(
        f"Decision file: {DECISION_FILE}"
    )
    print(
        f"Report: {report}"
    )
    print(
        "No live trading is authorized."
    )

def run_optimization(
    *,
    workers: int,
) -> None:
    git, frozen = protected_preflight()
    RESULT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print(
        "========== EXP-008 EXIT-GEOMETRY OPTIMIZATION =========="
    )
    print(
        "Grid:          27 locked long-only ORB combinations"
    )
    print(
        "Data:          frozen EXP-005 2019-2025 sessions"
    )
    print(
        "Selection:     NQ PF rank after locked neighbor checks"
    )
    print(
        "Walk-forward:  5 anchored annual folds"
    )
    print(
        "NQ MCPT:       1,000 selection-aware permutations"
    )
    print(
        "Sessions:      1,639"
    )
    print(
        f"Git commit:    {git['short_commit']}"
    )
    print(
        "EXP-005/006/007: frozen, unchanged"
    )
    print()

    print(
        "Preparing frozen NQ and MNQ arrays..."
    )
    nq_arrays = prepare_exp008_arrays(
        frozen.nq_1m
    )
    mnq_arrays = prepare_exp008_arrays(
        frozen.mnq_1m
    )

    print(
        "Running all 27 NQ and MNQ candidates..."
    )
    complete_grid = evaluate_candidate_grid(
        nq_arrays,
        mnq_arrays,
    )
    selection = select_candidate(
        complete_grid
    )
    scored_grid = selection.scored_grid

    if (
        selection.selected_parameters
        is None
    ):
        _complete_no_candidate_outcome(
            git=git,
            frozen=frozen,
            nq_arrays=nq_arrays,
            scored_grid=scored_grid,
            selection=selection,
            workers=workers,
        )
        return

    parameters = (
        selection.selected_parameters
    )
    selected_grid_row = selected_row(
        selection
    )
    if selected_grid_row is None:
        raise RuntimeError(
            "EXP-008 selected row is missing."
        )

    print(
        "Selected candidate: "
        f"{parameters.key}"
    )
    print(
        "Running detailed selected NQ result..."
    )
    nq_result = (
        run_exp008_candidate_from_arrays(
            nq_arrays,
            parameters=parameters,
            symbol="NQ",
        )
    )
    print(
        "Running selected MNQ implementation check..."
    )
    mnq_result = (
        run_exp008_candidate_from_arrays(
            mnq_arrays,
            parameters=parameters,
            symbol="MNQ",
        )
    )

    print(
        "Running five anchored walk-forward folds..."
    )
    walk_forward_result = (
        run_exp008_anchored_walk_forward(
            nq_arrays
        )
    )

    print(
        "Running locked cost sensitivity..."
    )
    (
        cost_sensitivity,
        nq_two_tick,
    ) = _cost_sensitivity(
        parameters=parameters,
        nq_arrays=nq_arrays,
        mnq_arrays=mnq_arrays,
    )

    print(
        "Running diagnostic 10,000-resample bootstrap..."
    )
    bootstrap = (
        bootstrap_exp008_trade_metrics(
            nq_result.trades
        )
    )

    print(
        "Running locked selection-aware MCPT..."
    )
    (
        mcpt_frame,
        mcpt_p_value,
        mcpt_info,
    ) = run_exp008_selection_mcpt(
        frozen.nq_1m,
        real_selected_trade_profit_factor=float(
            nq_result.summary[
                "trade_profit_factor"
            ]
        ),
        requested_workers=workers,
        checkpoint_file=(
            CHECKPOINT_FILE
        ),
        one_minute_fingerprint=(
            frozen.audit[
                "fingerprints"
            ]["NQ_1m"]
        ),
    )

    evaluation = evaluate_exp008(
        selected_row=selected_grid_row,
        nq_summary=nq_result.summary,
        mnq_summary=mnq_result.summary,
        nq_yearly_results=(
            nq_result.yearly_results
        ),
        walk_forward_results=(
            walk_forward_result.folds
        ),
        nq_two_tick_summary=(
            nq_two_tick
        ),
        mcpt_p_value=mcpt_p_value,
    )

    yearly = _combined_yearly(
        nq_result.yearly_results,
        mnq_result.yearly_results,
    )
    exceedances = int(
        mcpt_frame[
            "permutation_ge_real"
        ].sum()
    )
    finite_pf = mcpt_frame[
        "selected_trade_profit_factor"
    ].replace(
        [np.inf, -np.inf],
        np.nan,
    ).dropna()

    selection_counts = (
        mcpt_frame[
            "selected_parameter_key"
        ]
        .replace("", "NO_ELIGIBLE_CANDIDATE")
        .value_counts()
        .sort_index()
        .to_dict()
    )

    baseline_rows = scored_grid.loc[
        scored_grid[
            "parameter_key"
        ].eq(BASELINE.key)
    ]
    if len(baseline_rows) != 1:
        raise RuntimeError(
            "EXP-008 frozen EXP-007 baseline "
            "row is not unique."
        )
    baseline_row = (
        baseline_rows.iloc[0]
    )

    neighbor_keys = [
        key
        for key in str(
            selected_grid_row.get(
                "neighbor_keys",
                "",
            )
        ).split("|")
        if key
    ]
    neighbor_rows = scored_grid.loc[
        scored_grid[
            "parameter_key"
        ].isin(neighbor_keys)
    ]

    preregistration = (
        get_exp008_preregistration()
    )
    decision = {
        "schema_version": 1,
        "experiment_id": "EXP-008",
        "stage": (
            "STRUCTURED_EXIT_GEOMETRY_OPTIMIZATION"
        ),
        "calculated_at_utc": (
            datetime.now(
                timezone.utc
            ).isoformat(
                timespec="seconds"
            )
        ),
        "git": git,
        "data": {
            "source_experiment": (
                "EXP-005"
            ),
            "included_sessions": 1639,
            "one_minute_rows_per_symbol": (
                639210
            ),
            "five_minute_rows_per_symbol": (
                127842
            ),
            "fingerprints": frozen.audit[
                "fingerprints"
            ],
            "new_data_cleaning_decisions": (
                0
            ),
        },
        "grid": {
            "dimensions": (
                preregistration[
                    "parameter_grid"
                ]["dimensions"]
            ),
            "combination_count": 27,
            "exp007_baseline_parameter_key": (
                BASELINE.key
            ),
            "eligible_candidates": (
                selection.eligible_count
            ),
            "stable_eligible_candidates": (
                selection.stable_eligible_count
            ),
            "selected_parameter_key": (
                parameters.key
            ),
            "selected_parameters": (
                parameters.to_dict()
            ),
            "selected_grid_row": (
                selected_grid_row
            ),
        },
        "selection": {
            "market": "NQ",
            "procedure": (
                preregistration[
                    "candidate_selection"
                ]
            ),
            "selected_parameters": (
                parameters.to_dict()
            ),
            "selected_candidate_neighbor_keys": (
                neighbor_keys
            ),
            "selected_candidate_neighbors": (
                neighbor_rows.to_dict(
                    orient="records"
                )
            ),
        },
        "results": {
            "NQ": nq_result.summary,
            "MNQ": mnq_result.summary,
        },
        "walk_forward": {
            "fold_count": 5,
            "profitable_test_folds": (
                walk_forward_result[
                    "profitable_test_folds"
                ]
                if isinstance(
                    walk_forward_result,
                    dict,
                )
                else walk_forward_result.profitable_test_folds
            ),
            "combined_test_net_profit_usd": (
                walk_forward_result[
                    "combined_test_net_profit_usd"
                ]
                if isinstance(
                    walk_forward_result,
                    dict,
                )
                else walk_forward_result.combined_test_net_profit_usd
            ),
            "folds": (
                walk_forward_result.folds.to_dict(
                    orient="records"
                )
            ),
        },
        "final_candidate_annual_evaluation": {
            "years": [
                2021,
                2022,
                2023,
                2024,
                2025,
            ],
            "profitable_nq_years": (
                evaluation[
                    "profitable_final_candidate_nq_years"
                ]
            ),
            "combined_2021_2025_nq_net_profit_usd": (
                evaluation[
                    "combined_2021_2025_final_candidate_nq_net_profit_usd"
                ]
            ),
        },
        "cost_sensitivity": (
            cost_sensitivity.to_dict(
                orient="records"
            )
        ),
        "bootstrap": bootstrap,
        "mcpt": {
            "market": "NQ",
            "permutations": 1000,
            "base_seed": 48,
            "test_statistic": (
                "selected_candidate_trade_profit_factor"
            ),
            "real_selected_trade_profit_factor": (
                nq_result.summary[
                    "trade_profit_factor"
                ]
            ),
            "permutations_at_least_real": (
                exceedances
            ),
            "p_value": mcpt_p_value,
            "permutation_selected_pf_median": (
                float(
                    finite_pf.median()
                )
                if len(finite_pf)
                else None
            ),
            "permutation_selected_pf_maximum": (
                float(
                    finite_pf.max()
                )
                if len(finite_pf)
                else None
            ),
            "selected_parameter_counts": (
                selection_counts
            ),
            "run_info": (
                mcpt_info.to_dict()
            ),
            "all_27_candidates_inside_each_permutation": (
                True
            ),
            "selection_inside_each_permutation": (
                True
            ),
        },
        "baseline_comparison": {
            "exp007_parameter_key": (
                BASELINE.key
            ),
            "exp007_frozen_nq_trade_profit_factor": (
                EXP007_BASELINE_NQ_PF
            ),
            "exp007_nq_trade_profit_factor": (
                float(
                    baseline_row[
                        "nq_trade_profit_factor"
                    ]
                )
            ),
            "exp007_nq_net_profit_usd": (
                float(
                    baseline_row[
                        "nq_net_profit_usd"
                    ]
                )
            ),
            "exp008_selected_parameter_key": (
                parameters.key
            ),
            "exp008_selected_nq_trade_profit_factor": (
                float(
                    nq_result.summary[
                        "trade_profit_factor"
                    ]
                )
            ),
            "absolute_profit_factor_difference": (
                float(
                    nq_result.summary[
                        "trade_profit_factor"
                    ]
                )
                - EXP007_BASELINE_NQ_PF
            ),
            "strict_improvement_required": (
                True
            ),
            "fixed_minimum_improvement_amount": (
                None
            ),
        },
        "evaluation": evaluation,
        "historical_status": (
            "EXPLORATORY_BECAUSE_2019_2025_WAS_ALREADY_VIEWED"
        ),
        "best_possible_pass_action": (
            "LOCK_EXP008_EXIT_GEOMETRY_CANDIDATE_FOR_"
            "NEW_FORWARD_PAPER_COMPARISON"
        ),
        "exp005_control_changed": False,
        "exp006_result_changed": False,
        "exp007_result_changed": False,
        "live_trading_authorized": False,
        "automatic_lifecycle_source_edit": (
            False
        ),
    }

    scored_grid.to_csv(
        RESULT_DIR
        / "complete_candidate_grid.csv",
        index=False,
    )
    neighbor_rows.to_csv(
        RESULT_DIR
        / "selected_neighbor_evidence.csv",
        index=False,
    )
    nq_result.trades.to_csv(
        RESULT_DIR / "nq_trades.csv",
        index=False,
    )
    mnq_result.trades.to_csv(
        RESULT_DIR / "mnq_trades.csv",
        index=False,
    )
    nq_result.equity_curve.to_csv(
        RESULT_DIR
        / "nq_equity_curve.csv",
        index=False,
    )
    mnq_result.equity_curve.to_csv(
        RESULT_DIR
        / "mnq_equity_curve.csv",
        index=False,
    )
    yearly.to_csv(
        RESULT_DIR
        / "yearly_results.csv",
        index=False,
    )
    walk_forward_result.folds.to_csv(
        RESULT_DIR
        / "anchored_walk_forward.csv",
        index=False,
    )
    cost_sensitivity.to_csv(
        RESULT_DIR
        / "cost_sensitivity.csv",
        index=False,
    )
    mcpt_frame.to_csv(
        RESULT_DIR
        / "mcpt_results.csv",
        index=False,
    )
    _atomic_json(
        bootstrap,
        RESULT_DIR
        / "bootstrap_diagnostics.json",
    )
    _atomic_json(
        decision,
        DECISION_FILE,
    )

    report = build_exp008_report(
        decision=_json_safe(
            decision
        ),
        grid=scored_grid,
        nq_equity=(
            nq_result.equity_curve
        ),
        mnq_equity=(
            mnq_result.equity_curve
        ),
        yearly=yearly,
        walk_forward=(
            walk_forward_result.folds
        ),
        cost_sensitivity=(
            cost_sensitivity
        ),
        mcpt=mcpt_frame,
        output_dir=REPORT_DIR,
    )

    print()
    print(
        "EXP-008 exit-geometry optimization completed."
    )
    print(
        f"Decision: {evaluation['decision']}"
    )
    print(
        "Selected parameters: "
        f"{parameters.key}"
    )
    print(
        "Selected NQ Profit Factor: "
        f"{float(nq_result.summary['trade_profit_factor']):.6f}"
    )
    print(
        "Selected NQ net profit: "
        f"${float(nq_result.summary['net_profit_usd']):,.2f}"
    )
    print(
        "Selected NQ completed trades: "
        f"{nq_result.summary['completed_trades']}"
    )
    print(
        "Walk-forward profitable folds: "
        f"{walk_forward_result.profitable_test_folds}/5"
    )
    print(
        f"Selection-aware MCPT p-value: {mcpt_p_value:.6f}"
    )
    print(
        "Failed gates: "
        + (
            ", ".join(
                evaluation[
                    "failed_gates"
                ]
            )
            if evaluation[
                "failed_gates"
            ]
            else "none"
        )
    )
    print(
        f"Decision file: {DECISION_FILE}"
    )
    print(
        f"Report: {report}"
    )
    print(
        "No live trading is authorized."
    )


def parse_args(
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Protected EXP-008 structured "
            "ORB exit-geometry optimization."
        )
    )
    parser.add_argument(
        "--preflight",
        action="store_true",
        help=(
            "Verify the committed implementation "
            "without calculating results."
        ),
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=0,
        help=(
            "0 selects up to eight logical-worker "
            "processes."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.preflight:
        protected_preflight()
        print()
        print(
            "Preflight passed. No EXP-008 grid, "
            "selection, walk-forward, cost, bootstrap "
            "or MCPT result was calculated."
        )
        return

    run_optimization(
        workers=int(
            args.workers
        )
    )


if __name__ == "__main__":
    main()
