from __future__ import annotations

from copy import deepcopy
from typing import Any


EXP003_PREREGISTRATION: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-003",
    "title": (
        "BTCUSDT Hourly Long-Only "
        "Volatility-Compression Breakout"
    ),
    "locked_date": "2026-07-11",
    "research_status": "PRE_REGISTERED",
    "hypothesis": (
        "After an unusually quiet realized-volatility regime, "
        "an upside price-range breakout may be followed by "
        "positive continuation strong enough to overcome "
        "realistic trading costs."
    ),
    "null_hypothesis": (
        "Conditioning an upside breakout on prior volatility "
        "compression does not produce returns distinguishable "
        "from chance and does not remain profitable out of "
        "sample after costs."
    ),
    "market_and_data": {
        "market": "BTCUSDT spot",
        "timeframe": "1 hour",
        "data_file": "data/BTCUSDT_1h.parquet",
        "price_fields": [
            "open",
            "high",
            "low",
            "close",
        ],
        "position_direction": "long_only",
        "maximum_position": 1.0,
        "leverage": 1.0,
        "pyramiding": False,
    },
    "research_split": {
        "in_sample_start": "2018-01-01 00:00:00",
        "in_sample_end": "2021-12-31 23:00:00",
        "out_of_sample_start": "2022-01-01 00:00:00",
        "out_of_sample_end": "2025-12-31 23:00:00",
        "walkforward_training_bars": 35040,
        "walkforward_retrain_bars": 720,
        "effective_oos_rule": (
            "The out-of-sample start may move forward only by "
            "the minimum number of bars required to supply the "
            "locked walk-forward training window. No other date "
            "changes are permitted."
        ),
    },
    "signal_definition": {
        "return_series": (
            "log_return[t] = log(close[t] / close[t-1])"
        ),
        "realized_volatility": (
            "rv[t] = rolling population standard deviation of "
            "log_return over vol_lookback bars, using data "
            "available through close[t]"
        ),
        "compression_reference_window_bars": 2160,
        "compression_threshold": (
            "threshold[t] = trailing compression_quantile of "
            "rv over the previous 2160 bars, shifted by one bar"
        ),
        "compression_state": (
            "compressed[t] = rv[t] <= threshold[t]"
        ),
        "compression_recency_bars": 24,
        "recent_compression": (
            "recent_compression[t] is true when at least one "
            "compressed state occurred during bars t-23 through t"
        ),
        "breakout_level": (
            "breakout_level[t] = maximum high over the previous "
            "breakout_lookback bars, excluding bar t"
        ),
        "entry_signal": (
            "When flat, enter long when recent_compression[t] is "
            "true and close[t] > breakout_level[t]"
        ),
        "exit_lookback_bars": 24,
        "exit_level": (
            "exit_level[t] = minimum low over the previous "
            "24 bars, excluding bar t"
        ),
        "maximum_holding_bars": 168,
        "exit_signal": (
            "When long, exit when close[t] < exit_level[t] or "
            "the position has been held for 168 bars"
        ),
        "same_bar_rule": (
            "An exit takes precedence over a new entry. The "
            "strategy cannot exit and re-enter on the same signal bar."
        ),
        "execution": (
            "Signals are calculated after the hourly close and "
            "executed at the next hourly open"
        ),
        "final_bar_rule": (
            "Any remaining position is closed at the final "
            "available close and labelled end_of_data"
        ),
    },
    "optimized_parameters": {
        "vol_lookback": [24, 48, 72],
        "compression_quantile": [0.10, 0.20, 0.30],
        "breakout_lookback": [24, 48, 72],
    },
    "fixed_parameters": {
        "vol_lookback": 48,
        "compression_quantile": 0.20,
        "breakout_lookback": 48,
    },
    "parameter_count": 27,
    "cost_and_execution_model": {
        "starting_capital": 100000.0,
        "commission_bps_per_side": 5.0,
        "slippage_bps_per_side": 2.0,
        "execution_lag_bars": 1,
        "position_sizing": (
            "Full notional while long and zero while flat"
        ),
    },
    "statistical_plan": {
        "optimization_objective": (
            "In-sample next-bar log-return Profit Factor"
        ),
        "random_seed": 42,
        "quick_mcpt_permutations": 25,
        "full_mcpt_permutations": 1000,
        "parameter_surface_rule": (
            "All 27 locked combinations must be retained and "
            "reported. The best point alone is insufficient."
        ),
        "benchmark_context": [
            "Cash",
            "Buy and Hold",
        ],
    },
    "quick_screen": {
        "data_access_rule": (
            "The quick screen may use only the in-sample period. "
            "Out-of-sample strategy results must not be calculated "
            "or displayed before the quick-screen decision is locked."
        ),
        "all_gates_required": True,
        "gates": {
            "best_in_sample_bar_pf_strictly_above": 1.0,
            "minimum_parameter_combinations_pf_ge_1": 6,
            "minimum_neighbour_median_ratio_to_best": 0.95,
            "maximum_quick_mcpt_p_value": 0.20,
            "minimum_in_sample_completed_trades_fixed": 50,
        },
        "failure_action": (
            "Set EXP-003 to REJECTED and stop. Do not inspect "
            "out-of-sample strategy results."
        ),
        "pass_action": (
            "Advance to FULL_VALIDATION and reveal the locked "
            "out-of-sample period once."
        ),
    },
    "full_validation": {
        "all_gates_required": True,
        "gates": {
            "maximum_full_mcpt_p_value": 0.05,
            "minimum_fixed_oos_total_return_percent": 0.0,
            "minimum_fixed_oos_trade_profit_factor": 1.0,
            "minimum_fixed_oos_completed_trades": 30,
            "minimum_walkforward_total_return_percent": 0.0,
            "minimum_walkforward_trade_profit_factor": 1.0,
            "minimum_walkforward_completed_trades": 30,
            "maximum_absolute_fixed_oos_drawdown_percent": 50.0,
            "minimum_profitable_oos_calendar_years": 2,
        },
        "benchmark_rule": (
            "Cash and Buy and Hold must be reported over the same "
            "period, but Buy-and-Hold outperformance is not a "
            "mandatory gate because strategy exposure may differ."
        ),
        "failure_action": (
            "Set EXP-003 to REJECTED. Preserve the result as a "
            "completed negative experiment."
        ),
        "pass_action": (
            "Advance to REVIEW. Acceptance for paper testing "
            "requires a documented review confirming every gate."
        ),
    },
    "prohibited_post_result_changes": [
        (
            "Do not change signal definitions, parameter values, "
            "research dates, costs, or pass/fail gates under EXP-003."
        ),
        (
            "Do not add a trend filter, stop-loss, profit target, "
            "alternative exit, or different compression measure "
            "after viewing EXP-003 results."
        ),
        (
            "Any altered hypothesis or rule set must receive a new "
            "experiment ID and a fresh preregistration."
        ),
    ],
}


def get_exp003_preregistration() -> dict[str, Any]:
    return deepcopy(EXP003_PREREGISTRATION)


def validate_exp003_preregistration(
    preregistration: dict[str, Any] | None = None,
) -> None:
    record = (
        EXP003_PREREGISTRATION
        if preregistration is None
        else preregistration
    )

    if record.get("experiment_id") != "EXP-003":
        raise ValueError(
            "EXP-003 preregistration must use experiment_id EXP-003."
        )

    if record.get("research_status") != "PRE_REGISTERED":
        raise ValueError(
            "EXP-003 research_status must be PRE_REGISTERED."
        )

    optimized = record["optimized_parameters"]

    required_parameters = {
        "vol_lookback",
        "compression_quantile",
        "breakout_lookback",
    }

    if set(optimized) != required_parameters:
        raise ValueError(
            "EXP-003 optimized parameter names do not match "
            "the locked three-parameter design."
        )

    expected_count = 1

    for values in optimized.values():
        if not values:
            raise ValueError(
                "Optimized parameter lists cannot be empty."
            )

        expected_count *= len(values)

    if expected_count != record["parameter_count"]:
        raise ValueError(
            "parameter_count does not match the locked grid."
        )

    fixed = record["fixed_parameters"]

    for parameter_name, value in fixed.items():
        if value not in optimized[parameter_name]:
            raise ValueError(
                f"Fixed value for {parameter_name} is outside "
                "the preregistered grid."
            )

    quick_screen = record["quick_screen"]

    if (
        "out-of-sample"
        not in quick_screen[
            "data_access_rule"
        ].lower()
    ):
        raise ValueError(
            "Quick-screen data-access restrictions are missing."
        )

    if not quick_screen["all_gates_required"]:
        raise ValueError(
            "Every quick-screen gate must be mandatory."
        )

    full_validation = record[
        "full_validation"
    ]

    if not full_validation["all_gates_required"]:
        raise ValueError(
            "Every full-validation gate must be mandatory."
        )

    if not record[
        "prohibited_post_result_changes"
    ]:
        raise ValueError(
            "Post-result change restrictions cannot be empty."
        )


if __name__ == "__main__":
    validate_exp003_preregistration()

    print(
        "EXP-003 preregistration is valid and locked."
    )
