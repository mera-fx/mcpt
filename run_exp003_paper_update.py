from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import pandas as pd

from experiment_lifecycle import (
    get_experiment_lifecycle,
)
from paper_market_data import (
    update_public_hourly_data,
)
from paper_simulator import (
    candle_fingerprints,
    run_paper_simulation,
    validate_fingerprint_history,
    write_paper_report,
)
from paper_testing_plan import (
    get_exp003_paper_testing_plan,
    validate_exp003_paper_testing_plan,
)
from run_provenance import (
    combined_code_fingerprint,
    git_state,
)
from strategy_registry import generate_signal


PROJECT_DIR = Path(__file__).resolve().parent

DATA_FILE = (
    PROJECT_DIR
    / "paper_data"
    / "BTCUSDT_1h.parquet"
)

STATE_DIRECTORY = (
    PROJECT_DIR
    / "paper_state"
    / "EXP-003"
)

RESULTS_DIRECTORY = (
    PROJECT_DIR
    / "paper_results"
    / "EXP-003"
)

REPORT_DIRECTORY = (
    PROJECT_DIR
    / "paper_reports"
    / "EXP-003"
)

ACTIVATION_FILE = (
    STATE_DIRECTORY
    / "activation.json"
)

FINGERPRINT_FILE = (
    STATE_DIRECTORY
    / "candle_fingerprints.csv"
)


def _atomic_text_write(
    path: Path,
    text: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    temporary.write_text(
        text,
        encoding="utf-8",
    )

    temporary.replace(path)


def _atomic_csv_write(
    frame: pd.DataFrame,
    path: Path,
    *,
    index: bool = False,
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
        index=index,
    )

    temporary.replace(path)


def _json_ready(
    value: Any,
) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _json_ready(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            _json_ready(item)
            for item in value
        ]

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    if hasattr(value, "item"):
        try:
            return value.item()
        except ValueError:
            return value

    return value


def main() -> None:
    lifecycle = get_experiment_lifecycle(
        "EXP-003"
    )

    if (
        lifecycle.stage
        != "ACCEPTED_FOR_PAPER_TESTING"
    ):
        raise RuntimeError(
            "EXP-003 is not accepted for paper testing. "
            f"Current stage: {lifecycle.stage}"
        )

    validate_exp003_paper_testing_plan()
    plan = get_exp003_paper_testing_plan()

    git = git_state(PROJECT_DIR)

    if git.get("working_tree_dirty") is not False:
        raise RuntimeError(
            "Commit and push the paper simulator before "
            "running it. Git must report a clean working tree."
        )

    strategy_fingerprint = (
        combined_code_fingerprint(
            PROJECT_DIR,
            (
                "strategy_registry.py",
                "experiments/exp_003.py",
                "paper_testing_plan.py",
            ),
        )
    )

    print()
    print(
        "========== EXP-003 PAPER UPDATE =========="
    )
    print("Mode:       PAPER ONLY")
    print("Live orders: DISABLED")
    print(
        f"Git commit: {git.get('short_commit')}"
    )
    print(
        "Fetching public closed hourly candles..."
    )

    update = update_public_hourly_data(
        destination=DATA_FILE,
        symbol="BTCUSDT",
        initial_history_bars=3000,
        overlap_bars=72,
    )

    data = update.data

    STATE_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    RESULTS_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    initialized_now = False

    if ACTIVATION_FILE.exists():
        activation = json.loads(
            ACTIVATION_FILE.read_text(
                encoding="utf-8"
            )
        )

        if (
            activation[
                "strategy_fingerprint"
            ]
            != strategy_fingerprint
        ):
            raise RuntimeError(
                "The locked strategy fingerprint changed "
                "after paper activation. Stop paper testing "
                "and document the change before proceeding."
            )
    else:
        initialized_now = True

        activation = {
            "schema_version": 1,
            "experiment_id": "EXP-003",
            "mode": "paper_only",
            "activated_at_utc": (
                datetime.now(
                    timezone.utc
                ).isoformat(
                    timespec="seconds"
                )
            ),
            "activation_cutoff": (
                data.index[-1].isoformat()
            ),
            "activation_git_commit": (
                git.get("commit")
            ),
            "strategy_fingerprint": (
                strategy_fingerprint
            ),
            "starting_capital": (
                plan[
                    "cost_model"
                ]["starting_capital"]
            ),
            "source": (
                update.source_base_url
            ),
            "note": (
                "No pre-activation position is inherited. "
                "The first eligible signal must occur after "
                "the activation cutoff."
            ),
        }

        _atomic_text_write(
            ACTIVATION_FILE,
            json.dumps(
                activation,
                indent=2,
            ),
        )

    current_fingerprints = (
        candle_fingerprints(data)
    )

    if FINGERPRINT_FILE.exists():
        previous_fingerprints = (
            pd.read_csv(
                FINGERPRINT_FILE,
                dtype=str,
            )
        )

        validate_fingerprint_history(
            previous=previous_fingerprints,
            current=current_fingerprints,
        )

    parameters = plan[
        "fixed_parameters"
    ]

    raw_signal = generate_signal(
        "volatility_compression_breakout_long",
        data,
        parameters,
    )

    result = run_paper_simulation(
        data=data,
        raw_signal=raw_signal,
        activation_cutoff=pd.Timestamp(
            activation[
                "activation_cutoff"
            ]
        ),
        starting_capital=plan[
            "cost_model"
        ]["starting_capital"],
        commission_bps_per_side=plan[
            "cost_model"
        ]["commission_bps_per_side"],
        slippage_bps_per_side=plan[
            "cost_model"
        ]["slippage_bps_per_side"],
    )

    _atomic_csv_write(
        current_fingerprints,
        FINGERPRINT_FILE,
        index=False,
    )

    _atomic_csv_write(
        result.equity_curve.reset_index(),
        RESULTS_DIRECTORY
        / "paper_equity.csv",
        index=False,
    )

    _atomic_csv_write(
        result.completed_trades,
        RESULTS_DIRECTORY
        / "paper_trades.csv",
        index=False,
    )

    _atomic_csv_write(
        result.audit_log,
        RESULTS_DIRECTORY
        / "paper_audit_log.csv",
        index=False,
    )

    signal_frame = pd.DataFrame(
        {
            "raw_signal": (
                raw_signal.astype(float)
            ),
            "paper_signal": (
                result.isolated_signal
            ),
            "target_position": (
                result.target_position
            ),
        }
    )

    _atomic_csv_write(
        signal_frame.reset_index(),
        RESULTS_DIRECTORY
        / "paper_signals.csv",
        index=False,
    )

    _atomic_text_write(
        RESULTS_DIRECTORY
        / "paper_summary.json",
        json.dumps(
            _json_ready(
                {
                    **result.summary,
                    "reconciliation": (
                        result.reconciliation
                    ),
                    "open_position": (
                        result.open_position
                    ),
                    "git_commit": (
                        git.get("commit")
                    ),
                    "strategy_fingerprint": (
                        strategy_fingerprint
                    ),
                    "market_data_source": (
                        update.source_base_url
                    ),
                    "market_server_time_utc": (
                        update.server_time_utc
                    ),
                    "new_candles_this_run": (
                        update.new_rows
                    ),
                }
            ),
            indent=2,
            allow_nan=True,
        ),
    )

    activation_cutoff = pd.Timestamp(
        activation["activation_cutoff"]
    )

    latest_candle = data.index[-1]

    observation_weeks = max(
        0.0,
        (
            latest_candle
            - activation_cutoff
        ).total_seconds()
        / (7 * 24 * 3600),
    )

    report_file = write_paper_report(
        result=result,
        activation=activation,
        report_directory=REPORT_DIRECTORY,
        observation_weeks=(
            observation_weeks
        ),
        required_weeks=plan[
            "minimum_observation"
        ]["calendar_weeks"],
        required_trades=plan[
            "minimum_observation"
        ]["completed_trades"],
    )

    history_file = (
        RESULTS_DIRECTORY
        / "paper_run_history.csv"
    )

    history_row = pd.DataFrame(
        [
            {
                "run_time_utc": (
                    datetime.now(
                        timezone.utc
                    ).isoformat(
                        timespec="seconds"
                    )
                ),
                "git_commit": (
                    git.get("commit")
                ),
                "latest_closed_candle": (
                    latest_candle.isoformat()
                ),
                "new_candles": (
                    update.new_rows
                ),
                "observation_weeks": (
                    observation_weeks
                ),
                "completed_trades": (
                    result.summary[
                        "completed_trades"
                    ]
                ),
                "current_position": (
                    result.summary[
                        "current_position"
                    ]
                ),
                "total_return_percent": (
                    result.summary[
                        "total_return_percent"
                    ]
                ),
                "reconciliation_passed": (
                    result.reconciliation[
                        "passed"
                    ]
                ),
            }
        ]
    )

    if history_file.exists():
        history = pd.read_csv(
            history_file
        )

        history = pd.concat(
            [history, history_row],
            ignore_index=True,
        )
    else:
        history = history_row

    _atomic_csv_write(
        history,
        history_file,
        index=False,
    )

    print()
    if initialized_now:
        print(
            "Paper observation initialized."
        )
        print(
            "No historical position was inherited."
        )
    else:
        print(
            "Paper observation updated."
        )

    print(
        f"New closed candles: {update.new_rows}"
    )
    print(
        f"Latest candle:      {latest_candle}"
    )
    print(
        f"Observation weeks:  {observation_weeks:.3f}"
    )
    print(
        "Completed trades:   "
        f"{result.summary['completed_trades']}"
    )
    print(
        "Current position:   "
        + (
            "LONG"
            if result.summary[
                "current_position"
            ] == 1
            else "FLAT"
        )
    )
    print(
        "Pending next open:  "
        + (
            "LONG"
            if result.summary[
                "pending_next_open_target"
            ] == 1
            else "FLAT"
        )
    )
    print(
        "Reconciliation:     PASS"
    )
    print(
        f"Status report:      {report_file}"
    )
    print(
        "=========================================="
    )


if __name__ == "__main__":
    main()
