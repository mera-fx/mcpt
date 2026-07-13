from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from exp004_orb_engine import (
    optimize_orb,
    run_orb_backtest,
)
from exp004_preregistration import (
    get_exp004_preregistration,
    validate_exp004_preregistration,
)
from exp004_quick_report import (
    build_exp004_quick_report,
)
from exp004_quick_screen import (
    evaluate_exp004_quick_screen,
    load_exp004_in_sample_data,
    validate_exp004_config_matches_preregistration,
)
from exp004_session_mcpt import (
    run_exp004_mcpt,
)
from experiment_config import (
    load_experiment,
)
from experiment_lifecycle import (
    get_experiment_lifecycle,
)
from run_provenance import (
    combined_code_fingerprint,
    git_state,
    json_ready,
    sha256_file,
    stable_json,
    utc_run_identity,
)


PROJECT_DIR = Path(__file__).resolve().parent

DATA_FILE = (
    PROJECT_DIR
    / "data"
    / "QQQ_5m_SIP.parquet"
)

DATA_AUDIT_FILE = (
    PROJECT_DIR
    / "results"
    / "EXP-004"
    / "data"
    / "in_sample_data_audit.json"
)

RESULTS_DIRECTORY = (
    PROJECT_DIR
    / "results"
    / "EXP-004"
    / "quick_screen"
)

REPORT_DIRECTORY = (
    PROJECT_DIR
    / "reports"
    / "EXP-004-quick-screen"
)

DECISION_FILE = (
    RESULTS_DIRECTORY
    / "quick_screen_decision.json"
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the protected EXP-004 "
            "in-sample-only quick screen."
        )
    )

    parser.add_argument(
        "--mcpt-workers",
        type=int,
        default=0,
        help=(
            "Session-aware MCPT workers. "
            "0 selects automatic mode."
        ),
    )

    return parser.parse_args()


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
            json_ready(payload),
            indent=2,
            allow_nan=True,
        ),
        encoding="utf-8",
    )

    temporary.replace(path)


def _atomic_csv(
    frame: pd.DataFrame,
    path: Path,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    frame.to_csv(
        temporary,
        index=False,
    )

    temporary.replace(path)


def main() -> None:
    arguments = parse_arguments()

    validate_exp004_preregistration()
    preregistration = (
        get_exp004_preregistration()
    )

    config = load_experiment(
        "EXP-004"
    )

    validate_exp004_config_matches_preregistration(
        config
    )

    lifecycle = get_experiment_lifecycle(
        "EXP-004"
    )

    if lifecycle.stage != "PRE_REGISTERED":
        raise RuntimeError(
            "EXP-004 quick screening is "
            "allowed only while the lifecycle "
            "is PRE_REGISTERED."
        )

    if DECISION_FILE.exists():
        raise RuntimeError(
            "The EXP-004 quick-screen decision "
            "already exists. Do not rerun it:\n"
            f"{DECISION_FILE}"
        )

    git = git_state(
        PROJECT_DIR
    )

    if git.get(
        "working_tree_dirty"
    ) is not False:
        raise RuntimeError(
            "Commit and push the EXP-004 "
            "implementation before running "
            "the protected quick screen. "
            "Git must be clean."
        )

    if not DATA_AUDIT_FILE.exists():
        raise FileNotFoundError(
            "The validated EXP-004 in-sample "
            "data audit is missing. Run:\n"
            r".\.venv\Scripts\python.exe "
            "download_exp004_qqq_is_data.py"
        )

    data_audit = json.loads(
        DATA_AUDIT_FILE.read_text(
            encoding="utf-8"
        )
    )

    if data_audit.get(
        "out_of_sample_rows"
    ) != 0:
        raise RuntimeError(
            "The EXP-004 data audit records "
            "out-of-sample rows. Quick screening "
            "is blocked."
        )

    if data_audit.get(
        "included_invalid_sessions"
    ) != 0:
        raise RuntimeError(
            "The EXP-004 data audit includes "
            "invalid sessions."
        )

    data = load_exp004_in_sample_data(
        DATA_FILE
    )

    data_hash = sha256_file(
        DATA_FILE
    )

    if (
        data_audit.get(
            "data_file_sha256"
        )
        != data_hash
    ):
        raise RuntimeError(
            "The EXP-004 data file does not "
            "match its validated audit."
        )

    code_fingerprint = (
        combined_code_fingerprint(
            PROJECT_DIR,
            (
                "exp004_preregistration.py",
                "exp004_orb_engine.py",
                "exp004_session_mcpt.py",
                "exp004_quick_screen.py",
                "exp004_quick_report.py",
                "run_exp004_quick_screen.py",
                "alpaca_historical_data.py",
                "intraday_market_foundation.py",
                "experiments/exp_004.py",
            ),
        )
    )

    preregistration_fingerprint = (
        sha256_file(
            PROJECT_DIR
            / "research"
            / "EXP-004_preregistration.md"
        )
    )

    run_id, run_started_at = (
        utc_run_identity()
    )

    print()
    print(
        "=============================================="
    )
    print(
        "EXP-004 PROTECTED QUICK SCREEN"
    )
    print(
        "Out-of-sample disclosure: BLOCKED"
    )
    print(
        f"Git commit: {git.get('short_commit')}"
    )
    print(
        "=============================================="
    )
    print(
        f"In-sample sessions: "
        f"{data['session_date'].nunique():,}"
    )
    print(
        f"In-sample rows:     {len(data):,}"
    )
    print()
    print(
        "Optimizing the nine locked "
        "parameter combinations..."
    )

    cost_model = preregistration[
        "cost_and_execution_model"
    ]

    total_cost = cost_model[
        "total_cost_bps_per_side"
    ]

    minimum_trades = preregistration[
        "optimization_plan"
    ][
        "minimum_valid_combination_trades"
    ]

    optimization, best_parameters, best_result = (
        optimize_orb(
            data,
            grid=preregistration[
                "optimized_parameters"
            ],
            starting_capital=cost_model[
                "starting_capital"
            ],
            total_cost_bps_per_side=(
                total_cost
            ),
            minimum_valid_trades=(
                minimum_trades
            ),
        )
    )

    fixed_result = run_orb_backtest(
        data,
        **preregistration[
            "fixed_parameters"
        ],
        starting_capital=cost_model[
            "starting_capital"
        ],
        total_cost_bps_per_side=(
            total_cost
        ),
    )

    best_pf = float(
        best_result.summary[
            "trade_profit_factor"
        ]
    )

    checkpoint_signature = {
        "schema_version": 1,
        "experiment_id": "EXP-004",
        "research_stage": (
            "IN_SAMPLE_QUICK_SCREEN"
        ),
        "data_file_sha256": data_hash,
        "code_fingerprint": (
            code_fingerprint
        ),
        "preregistration_fingerprint": (
            preregistration_fingerprint
        ),
        "grid": preregistration[
            "optimized_parameters"
        ],
        "random_seed": preregistration[
            "statistical_plan"
        ]["random_seed"],
        "objective": (
            "completed_trade_profit_factor"
        ),
        "minimum_valid_trades": (
            minimum_trades
        ),
    }

    (
        mcpt_results,
        mcpt_p_value,
        better_or_equal,
        mcpt_info,
    ) = run_exp004_mcpt(
        data=data,
        grid=preregistration[
            "optimized_parameters"
        ],
        starting_capital=cost_model[
            "starting_capital"
        ],
        total_cost_bps_per_side=(
            total_cost
        ),
        minimum_valid_trades=(
            minimum_trades
        ),
        random_seed=preregistration[
            "statistical_plan"
        ]["random_seed"],
        permutations=preregistration[
            "statistical_plan"
        ][
            "quick_mcpt_permutations"
        ],
        real_best_profit_factor=(
            best_pf
        ),
        requested_workers=(
            arguments.mcpt_workers
        ),
        checkpoint_directory=(
            RESULTS_DIRECTORY
            / "mcpt_checkpoint"
        ),
        checkpoint_signature=(
            checkpoint_signature
        ),
        checkpoint_every=1,
        resume=True,
    )

    combinations_pf_ge_one = int(
        (
            optimization[
                "trade_profit_factor"
            ]
            >= 1.0
        ).sum()
    )

    evaluation = (
        evaluate_exp004_quick_screen(
            best_in_sample_trade_pf=(
                best_pf
            ),
            fixed_in_sample_trade_pf=(
                fixed_result.summary[
                    "trade_profit_factor"
                ]
            ),
            parameter_combinations_pf_ge_1=(
                combinations_pf_ge_one
            ),
            quick_mcpt_p_value=(
                mcpt_p_value
            ),
            fixed_in_sample_completed_trades=(
                fixed_result.summary[
                    "completed_trades"
                ]
            ),
            fixed_in_sample_long_trades=(
                fixed_result.summary[
                    "long_trades"
                ]
            ),
            fixed_in_sample_short_trades=(
                fixed_result.summary[
                    "short_trades"
                ]
            ),
            included_invalid_sessions=(
                data_audit[
                    "included_invalid_sessions"
                ]
            ),
        )
    )

    RESULTS_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    _atomic_csv(
        optimization,
        RESULTS_DIRECTORY
        / "optimization.csv",
    )

    _atomic_csv(
        fixed_result.trades,
        RESULTS_DIRECTORY
        / "fixed_in_sample_trades.csv",
    )

    _atomic_csv(
        fixed_result.equity_curve,
        RESULTS_DIRECTORY
        / "fixed_in_sample_equity.csv",
    )

    _atomic_csv(
        mcpt_results,
        RESULTS_DIRECTORY
        / "mcpt_quick.csv",
    )

    run_metadata = {
        "run_id": run_id,
        "run_started_at_utc": (
            run_started_at
        ),
        "experiment_id": "EXP-004",
        "research_stage": (
            "IN_SAMPLE_QUICK_SCREEN"
        ),
        "oos_disclosure": "BLOCKED",
        "git": git,
        "data_file_sha256": data_hash,
        "code_fingerprint": (
            code_fingerprint
        ),
        "preregistration_fingerprint": (
            preregistration_fingerprint
        ),
        "best_parameters": (
            best_parameters
        ),
        "best_summary": (
            best_result.summary
        ),
        "fixed_parameters": (
            fixed_result.parameters
        ),
        "fixed_summary": (
            fixed_result.summary
        ),
        "mcpt_p_value": (
            mcpt_p_value
        ),
        "mcpt_better_or_equal": (
            better_or_equal
        ),
        "mcpt_execution": (
            mcpt_info.to_dict()
        ),
    }

    _atomic_json(
        run_metadata,
        RESULTS_DIRECTORY
        / "quick_screen_metadata.json",
    )

    report_file = (
        build_exp004_quick_report(
            report_directory=(
                REPORT_DIRECTORY
            ),
            optimization=optimization,
            best_parameters=(
                best_parameters
            ),
            fixed_result=fixed_result,
            mcpt_results=(
                mcpt_results
            ),
            mcpt_p_value=(
                mcpt_p_value
            ),
            evaluation=evaluation,
            data_audit=data_audit,
            run_metadata=(
                run_metadata
            ),
        )
    )

    decision_payload = {
        **evaluation.to_dict(),
        "experiment_id": "EXP-004",
        "decision_type": (
            "protected_in_sample_quick_screen"
        ),
        "out_of_sample_disclosure": (
            "BLOCKED"
        ),
        "best_parameters": (
            best_parameters
        ),
        "best_in_sample_summary": (
            best_result.summary
        ),
        "fixed_parameters": (
            fixed_result.parameters
        ),
        "fixed_in_sample_summary": (
            fixed_result.summary
        ),
        "parameter_combinations_pf_ge_1": (
            combinations_pf_ge_one
        ),
        "quick_mcpt_permutations": (
            len(mcpt_results)
        ),
        "quick_mcpt_p_value": (
            mcpt_p_value
        ),
        "data_file_sha256": (
            data_hash
        ),
        "git_commit": git.get(
            "commit"
        ),
        "created_at_utc": (
            datetime.now(
                timezone.utc
            ).isoformat(
                timespec="seconds"
            )
        ),
    }

    # Decision written last. If the process
    # stops before this point, the compatible
    # MCPT checkpoint may be resumed.
    _atomic_json(
        decision_payload,
        DECISION_FILE,
    )

    print()
    print(
        "============== QUICK-SCREEN GATES =============="
    )

    for name, gate in (
        evaluation.gates.items()
    ):
        status = (
            "PASS"
            if gate["passed"]
            else "FAIL"
        )

        print(
            f"{status:4} | {name}: "
            f"{gate['actual']} "
            f"{gate['operator']} "
            f"{gate['threshold']}"
        )

    print()
    print(
        "================ DECISION ================="
    )
    print(evaluation.decision)
    print(
        "Out-of-sample results remained locked."
    )
    print(
        f"Decision file: {DECISION_FILE}"
    )
    print(
        f"Visual report: {report_file}"
    )
    print(
        "==========================================="
    )


if __name__ == "__main__":
    main()
