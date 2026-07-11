from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Any, Callable

import numpy as np
import pandas as pd

from donchian import donchian_breakout


SignalFunction = Callable[..., pd.Series]


@dataclass(frozen=True)
class StrategyDefinition:
    """
    Describes one strategy that the research runner can call by name.
    """

    name: str
    signal_function: SignalFunction
    parameter_names: tuple[str, ...]
    description: str


def _ensure_signal(
    signal: pd.Series | np.ndarray,
    index: pd.Index,
    name: str,
) -> pd.Series:
    """
    Convert any supported signal output into a clean pandas Series.
    """

    if isinstance(signal, pd.Series):
        clean_signal = signal.reindex(index)
    else:
        clean_signal = pd.Series(
            signal,
            index=index,
        )

    clean_signal = clean_signal.astype(float)
    clean_signal.name = name

    return clean_signal


def donchian_signal(
    data: pd.DataFrame,
    *,
    lookback: int,
) -> pd.Series:
    """
    Long when close breaks above the recent upper boundary.
    Short when close breaks below the recent lower boundary.
    """

    lookback = int(lookback)

    if lookback < 2:
        raise ValueError(
            "Donchian lookback must be at least 2."
        )

    signal = donchian_breakout(
        data,
        lookback,
    )

    return _ensure_signal(
        signal,
        data.index,
        "donchian_signal",
    )


def zscore_mean_reversion_long_signal(
    data: pd.DataFrame,
    *,
    lookback: int,
    entry_z: float,
) -> pd.Series:
    """
    Long-only mean reversion.

    Enter long when the close is entry_z standard deviations below
    its rolling mean. Hold the position until price recovers to the
    rolling mean. Otherwise remain flat.
    """

    lookback = int(lookback)
    entry_z = float(entry_z)

    if lookback < 2:
        raise ValueError(
            "Mean-reversion lookback must be at least 2."
        )

    if entry_z <= 0:
        raise ValueError(
            "entry_z must be positive."
        )

    close = data["close"].astype(float)

    rolling_mean = close.rolling(
        lookback,
        min_periods=lookback,
    ).mean()

    rolling_std = close.rolling(
        lookback,
        min_periods=lookback,
    ).std(ddof=0)

    z_score = (
        close - rolling_mean
    ) / rolling_std.replace(0, np.nan)

    events = pd.Series(
        np.nan,
        index=data.index,
        dtype=float,
    )

    # Enter after an unusually large downside deviation.
    events.loc[z_score <= -entry_z] = 1.0

    # Exit once price has recovered to its rolling mean.
    events.loc[z_score >= 0.0] = 0.0

    signal = events.ffill().fillna(0.0)

    return _ensure_signal(
        signal,
        data.index,
        "zscore_mean_reversion_long_signal",
    )


def calculate_volatility_compression_components(
    data: pd.DataFrame,
    *,
    vol_lookback: int,
    compression_quantile: float,
    breakout_lookback: int,
    compression_reference_window_bars: int = 2160,
    compression_recency_bars: int = 24,
    exit_lookback_bars: int = 24,
) -> pd.DataFrame:
    """Calculate the locked, causal EXP-003 indicator components."""

    vol_lookback = int(vol_lookback)
    breakout_lookback = int(breakout_lookback)
    compression_quantile = float(compression_quantile)

    if vol_lookback < 2:
        raise ValueError(
            "vol_lookback must be at least 2."
        )

    if breakout_lookback < 2:
        raise ValueError(
            "breakout_lookback must be at least 2."
        )

    if not 0.0 < compression_quantile < 1.0:
        raise ValueError(
            "compression_quantile must be between 0 and 1."
        )

    if compression_reference_window_bars < 2:
        raise ValueError(
            "compression_reference_window_bars must be at least 2."
        )

    close = data["close"].astype(float)
    high = data["high"].astype(float)
    low = data["low"].astype(float)

    log_return = np.log(close).diff()

    realized_volatility = log_return.rolling(
        vol_lookback,
        min_periods=vol_lookback,
    ).std(ddof=0)

    compression_threshold = realized_volatility.rolling(
        compression_reference_window_bars,
        min_periods=compression_reference_window_bars,
    ).quantile(
        compression_quantile
    ).shift(1)

    compressed = (
        realized_volatility
        <= compression_threshold
    ).fillna(False)

    recent_compression = compressed.astype(float).rolling(
        compression_recency_bars,
        min_periods=1,
    ).max().astype(bool)

    breakout_level = high.shift(1).rolling(
        breakout_lookback,
        min_periods=breakout_lookback,
    ).max()

    exit_level = low.shift(1).rolling(
        exit_lookback_bars,
        min_periods=exit_lookback_bars,
    ).min()

    return pd.DataFrame(
        {
            "log_return": log_return,
            "realized_volatility": realized_volatility,
            "compression_threshold": compression_threshold,
            "compressed": compressed,
            "recent_compression": recent_compression,
            "breakout_level": breakout_level,
            "exit_level": exit_level,
        },
        index=data.index,
    )


def build_volatility_breakout_position_signal(
    *,
    close: pd.Series,
    recent_compression: pd.Series,
    breakout_level: pd.Series,
    exit_level: pd.Series,
    maximum_holding_bars: int = 168,
) -> pd.Series:
    """Apply the locked EXP-003 long/flat state machine."""

    maximum_holding_bars = int(
        maximum_holding_bars
    )

    if maximum_holding_bars < 1:
        raise ValueError(
            "maximum_holding_bars must be positive."
        )

    index = close.index

    recent = recent_compression.reindex(
        index
    ).fillna(False).astype(bool)

    breakout = breakout_level.reindex(index)
    exit_boundary = exit_level.reindex(index)

    signal = pd.Series(
        0.0,
        index=index,
        dtype=float,
        name=(
            "volatility_compression_breakout_long_signal"
        ),
    )

    is_long = False
    entry_signal_position: int | None = None

    for position in range(len(index)):
        current_close = float(
            close.iloc[position]
        )

        current_breakout = breakout.iloc[
            position
        ]

        current_exit = exit_boundary.iloc[
            position
        ]

        if is_long:
            bars_since_entry_signal = (
                position
                - int(entry_signal_position)
            )

            price_exit = (
                pd.notna(current_exit)
                and current_close
                < float(current_exit)
            )

            time_exit = (
                bars_since_entry_signal
                >= maximum_holding_bars
            )

            if price_exit or time_exit:
                is_long = False
                entry_signal_position = None
                signal.iloc[position] = 0.0
            else:
                signal.iloc[position] = 1.0

            # Exit takes priority. No same-bar re-entry.
            continue

        entry = (
            bool(recent.iloc[position])
            and pd.notna(current_breakout)
            and current_close
            > float(current_breakout)
        )

        if entry:
            is_long = True
            entry_signal_position = position
            signal.iloc[position] = 1.0

    return signal


def volatility_compression_breakout_long_signal(
    data: pd.DataFrame,
    *,
    vol_lookback: int,
    compression_quantile: float,
    breakout_lookback: int,
) -> pd.Series:
    """Locked EXP-003 volatility-compression breakout signal."""

    components = (
        calculate_volatility_compression_components(
            data,
            vol_lookback=vol_lookback,
            compression_quantile=(
                compression_quantile
            ),
            breakout_lookback=breakout_lookback,
        )
    )

    return build_volatility_breakout_position_signal(
        close=data["close"].astype(float),
        recent_compression=components[
            "recent_compression"
        ],
        breakout_level=components[
            "breakout_level"
        ],
        exit_level=components[
            "exit_level"
        ],
        maximum_holding_bars=168,
    )


STRATEGIES: dict[str, StrategyDefinition] = {
    "donchian_breakout": StrategyDefinition(
        name="donchian_breakout",
        signal_function=donchian_signal,
        parameter_names=("lookback",),
        description=(
            "Long/short closing-price Donchian breakout."
        ),
    ),

    "zscore_mean_reversion_long": StrategyDefinition(
        name="zscore_mean_reversion_long",
        signal_function=zscore_mean_reversion_long_signal,
        parameter_names=("lookback", "entry_z"),
        description=(
            "Long-only z-score mean reversion with exit at "
            "the rolling mean."
        ),
    ),

    "volatility_compression_breakout_long": StrategyDefinition(
        name="volatility_compression_breakout_long",
        signal_function=(
            volatility_compression_breakout_long_signal
        ),
        parameter_names=(
            "vol_lookback",
            "compression_quantile",
            "breakout_lookback",
        ),
        description=(
            "Long-only upside breakout after a recent "
            "realized-volatility compression regime."
        ),
    ),
}


def list_strategies() -> pd.DataFrame:
    """
    Return a readable table of all registered strategies.
    """

    rows = []

    for strategy in STRATEGIES.values():
        rows.append(
            {
                "strategy_name": strategy.name,
                "parameters": ", ".join(
                    strategy.parameter_names
                ),
                "description": strategy.description,
            }
        )

    return pd.DataFrame(rows)


def get_strategy(
    strategy_name: str,
) -> StrategyDefinition:
    """
    Find a strategy by its configuration name.
    """

    try:
        return STRATEGIES[strategy_name]
    except KeyError as error:
        available = ", ".join(
            sorted(STRATEGIES)
        )

        raise KeyError(
            f"Unknown strategy '{strategy_name}'. "
            f"Available strategies: {available}"
        ) from error


def validate_parameters(
    strategy_name: str,
    parameters: dict[str, Any],
) -> None:
    """
    Confirm that the supplied parameter names match the strategy.
    """

    strategy = get_strategy(strategy_name)

    expected = set(strategy.parameter_names)
    supplied = set(parameters)

    missing = expected.difference(supplied)
    extra = supplied.difference(expected)

    if missing:
        raise ValueError(
            f"Missing parameters for {strategy_name}: "
            f"{sorted(missing)}"
        )

    if extra:
        raise ValueError(
            f"Unexpected parameters for {strategy_name}: "
            f"{sorted(extra)}"
        )


def generate_signal(
    strategy_name: str,
    data: pd.DataFrame,
    parameters: dict[str, Any],
) -> pd.Series:
    """
    Generate one strategy signal from a configuration dictionary.
    """

    validate_parameters(
        strategy_name,
        parameters,
    )

    strategy = get_strategy(strategy_name)

    signal = strategy.signal_function(
        data,
        **parameters,
    )

    return _ensure_signal(
        signal,
        data.index,
        f"{strategy_name}_signal",
    )


def expand_parameter_grid(
    strategy_name: str,
    optimization_grid: dict[str, list[Any]],
) -> list[dict[str, Any]]:
    """
    Convert a parameter grid into every possible combination.

    Example:
    {
        "lookback": [12, 13, 14]
    }

    becomes:
    [
        {"lookback": 12},
        {"lookback": 13},
        {"lookback": 14},
    ]
    """

    strategy = get_strategy(strategy_name)

    expected = set(strategy.parameter_names)
    supplied = set(optimization_grid)

    if supplied != expected:
        missing = expected.difference(supplied)
        extra = supplied.difference(expected)

        messages = []

        if missing:
            messages.append(
                f"missing {sorted(missing)}"
            )

        if extra:
            messages.append(
                f"unexpected {sorted(extra)}"
            )

        raise ValueError(
            "Invalid optimization grid: "
            + ", ".join(messages)
        )

    for parameter_name, values in optimization_grid.items():
        if not values:
            raise ValueError(
                f"Optimization values for "
                f"'{parameter_name}' cannot be empty."
            )

    ordered_names = strategy.parameter_names
    ordered_values = [
        optimization_grid[name]
        for name in ordered_names
    ]

    combinations = []

    for values in product(*ordered_values):
        combinations.append(
            dict(zip(ordered_names, values))
        )

    return combinations


if __name__ == "__main__":
    print("Registered strategies")
    print("---------------------")
    print(list_strategies().to_string(index=False))
    print()

    example_parameters = {
        "lookback": 49,
    }

    validate_parameters(
        "donchian_breakout",
        example_parameters,
    )

    example_grid = expand_parameter_grid(
        "donchian_breakout",
        {
            "lookback": [12, 24, 49],
        },
    )

    print("Parameter validation passed.")
    print()
    print("Example optimization combinations:")
    print(example_grid)
