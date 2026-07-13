from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from alpaca_historical_data import (
    validate_exp004_clean_data,
)
from exp004_preregistration import (
    get_exp004_preregistration,
)
from experiment_config import ResearchConfig


@dataclass(frozen=True)
class Exp004QuickEvaluation:
    decision: str
    passed: bool
    gates: dict[str, dict[str, Any]]
    failed_gates: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "passed": self.passed,
            "gates": self.gates,
            "failed_gates": list(
                self.failed_gates
            ),
        }


def validate_exp004_config_matches_preregistration(
    config: ResearchConfig,
) -> None:
    record = get_exp004_preregistration()

    expected = {
        "experiment_id": "EXP-004",
        "market_name": "QQQ ETF",
        "timeframe": "5 minutes",
        "data_file": Path(
            "data/QQQ_5m_SIP.parquet"
        ),
        "strategy_name": (
            "opening_range_breakout"
        ),
        "fixed_parameters": record[
            "fixed_parameters"
        ],
        "optimization_grid": record[
            "optimized_parameters"
        ],
        "in_sample_start": pd.Timestamp(
            record[
                "research_split"
            ]["in_sample_start"]
        ),
        "in_sample_end": (
            pd.Timestamp(
                record[
                    "research_split"
                ]["in_sample_end"]
            )
            + pd.Timedelta(days=1)
        ),
        "out_of_sample_start": pd.Timestamp(
            record[
                "research_split"
            ]["out_of_sample_start"]
        ),
        "out_of_sample_end": (
            pd.Timestamp(
                record[
                    "research_split"
                ]["out_of_sample_end"]
            )
            + pd.Timedelta(days=1)
        ),
        "starting_capital": record[
            "cost_and_execution_model"
        ]["starting_capital"],
        "commission_bps_per_side": record[
            "cost_and_execution_model"
        ][
            "commission_and_fees_bps_per_side"
        ],
        "slippage_bps_per_side": record[
            "cost_and_execution_model"
        ]["slippage_bps_per_side"],
        "execution_lag_bars": record[
            "cost_and_execution_model"
        ]["execution_lag_bars"],
        "mcpt_permutations": record[
            "statistical_plan"
        ]["full_mcpt_permutations"],
        "random_seed": record[
            "statistical_plan"
        ]["random_seed"],
        "walkforward_training_bars": (
            record[
                "research_split"
            ][
                "walkforward_training_sessions"
            ]
            * 78
        ),
        "walkforward_retrain_bars": (
            record[
                "research_split"
            ][
                "walkforward_retrain_sessions"
            ]
            * 78
        ),
    }

    mismatches: list[str] = []

    date_fields = {
        "in_sample_start",
        "in_sample_end",
        "out_of_sample_start",
        "out_of_sample_end",
    }

    for field_name, expected_value in (
        expected.items()
    ):
        actual_value = getattr(
            config,
            field_name,
        )

        if field_name in date_fields:
            matches = (
                pd.Timestamp(actual_value)
                == pd.Timestamp(
                    expected_value
                )
            )
        elif field_name == "data_file":
            matches = (
                Path(actual_value)
                == expected_value
            )
        else:
            matches = (
                actual_value
                == expected_value
            )

        if not matches:
            mismatches.append(
                f"{field_name}: expected "
                f"{expected_value!r}, got "
                f"{actual_value!r}"
            )

    if mismatches:
        raise ValueError(
            "EXP-004 configuration does not "
            "match the locked preregistration:"
            "\n- "
            + "\n- ".join(
                mismatches
            )
        )


def load_exp004_in_sample_data(
    path: Path,
) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"EXP-004 data was not found: "
            f"{path}"
        )

    data = pd.read_parquet(
        path
    )

    data.index = pd.to_datetime(
        data.index,
        utc=True,
    )

    validate_exp004_clean_data(
        data,
        maximum_session_date=(
            "2022-12-30"
        ),
    )

    first = min(
        pd.to_datetime(
            data["session_date"]
        ).dt.date
    )

    last = max(
        pd.to_datetime(
            data["session_date"]
        ).dt.date
    )

    if first < pd.Timestamp(
        "2019-01-02"
    ).date():
        raise ValueError(
            "EXP-004 data begins before "
            "the locked in-sample period."
        )

    if last > pd.Timestamp(
        "2022-12-30"
    ).date():
        raise ValueError(
            "EXP-004 quick-screen loader "
            "detected out-of-sample rows."
        )

    return data


def evaluate_exp004_quick_screen(
    *,
    best_in_sample_trade_pf: float,
    fixed_in_sample_trade_pf: float,
    parameter_combinations_pf_ge_1: int,
    quick_mcpt_p_value: float,
    fixed_in_sample_completed_trades: int,
    fixed_in_sample_long_trades: int,
    fixed_in_sample_short_trades: int,
    included_invalid_sessions: int,
) -> Exp004QuickEvaluation:
    thresholds = (
        get_exp004_preregistration()[
            "quick_screen"
        ]["gates"]
    )

    gates: dict[
        str,
        dict[str, Any],
    ] = {}

    def add(
        name: str,
        actual: Any,
        operator: str,
        threshold: Any,
        passed: bool,
    ) -> None:
        gates[name] = {
            "actual": actual,
            "operator": operator,
            "threshold": threshold,
            "passed": bool(passed),
        }

    add(
        "best_in_sample_trade_pf",
        float(best_in_sample_trade_pf),
        ">",
        thresholds[
            "best_in_sample_trade_pf_strictly_above"
        ],
        float(
            best_in_sample_trade_pf
        )
        > thresholds[
            "best_in_sample_trade_pf_strictly_above"
        ],
    )

    add(
        "fixed_in_sample_trade_pf",
        float(fixed_in_sample_trade_pf),
        ">",
        thresholds[
            "fixed_in_sample_trade_pf_strictly_above"
        ],
        float(
            fixed_in_sample_trade_pf
        )
        > thresholds[
            "fixed_in_sample_trade_pf_strictly_above"
        ],
    )

    add(
        "parameter_combinations_pf_ge_1",
        int(
            parameter_combinations_pf_ge_1
        ),
        ">=",
        thresholds[
            "minimum_parameter_combinations_pf_ge_1"
        ],
        int(
            parameter_combinations_pf_ge_1
        )
        >= thresholds[
            "minimum_parameter_combinations_pf_ge_1"
        ],
    )

    add(
        "quick_mcpt_p_value",
        float(
            quick_mcpt_p_value
        ),
        "<=",
        thresholds[
            "maximum_quick_mcpt_p_value"
        ],
        float(
            quick_mcpt_p_value
        )
        <= thresholds[
            "maximum_quick_mcpt_p_value"
        ],
    )

    add(
        "fixed_in_sample_completed_trades",
        int(
            fixed_in_sample_completed_trades
        ),
        ">=",
        thresholds[
            "minimum_fixed_in_sample_completed_trades"
        ],
        int(
            fixed_in_sample_completed_trades
        )
        >= thresholds[
            "minimum_fixed_in_sample_completed_trades"
        ],
    )

    add(
        "fixed_in_sample_long_trades",
        int(
            fixed_in_sample_long_trades
        ),
        ">=",
        thresholds[
            "minimum_fixed_long_trades"
        ],
        int(
            fixed_in_sample_long_trades
        )
        >= thresholds[
            "minimum_fixed_long_trades"
        ],
    )

    add(
        "fixed_in_sample_short_trades",
        int(
            fixed_in_sample_short_trades
        ),
        ">=",
        thresholds[
            "minimum_fixed_short_trades"
        ],
        int(
            fixed_in_sample_short_trades
        )
        >= thresholds[
            "minimum_fixed_short_trades"
        ],
    )

    add(
        "included_invalid_sessions",
        int(
            included_invalid_sessions
        ),
        "<=",
        thresholds[
            "maximum_included_invalid_sessions"
        ],
        int(
            included_invalid_sessions
        )
        <= thresholds[
            "maximum_included_invalid_sessions"
        ],
    )

    failed = tuple(
        name
        for name, gate in (
            gates.items()
        )
        if not gate["passed"]
    )

    passed = not failed

    return Exp004QuickEvaluation(
        decision=(
            "PASS_TO_FULL_VALIDATION"
            if passed
            else "REJECT"
        ),
        passed=passed,
        gates=gates,
        failed_gates=failed,
    )
