from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ResearchConfig:
    """Settings for one complete research experiment."""

    experiment_id: str
    experiment_name: str
    hypothesis: str

    market_name: str
    timeframe: str
    data_file: Path

    strategy_name: str
    fixed_parameters: dict[str, Any] = field(default_factory=dict)
    optimization_grid: dict[str, list[Any]] = field(default_factory=dict)

    in_sample_start: str = "2018-01-01"
    in_sample_end: str = "2022-01-01"
    out_of_sample_start: str = "2022-01-01"
    out_of_sample_end: str = "2026-01-01"

    starting_capital: float = 100_000.0
    commission_bps_per_side: float = 5.0
    slippage_bps_per_side: float = 2.0
    execution_lag_bars: int = 1

    run_mcpt: bool = True
    mcpt_permutations: int = 1_000
    random_seed: int = 10_000

    run_walkforward: bool = True
    walkforward_training_bars: int = 24 * 365 * 4
    walkforward_retrain_bars: int = 24 * 30

    cost_levels_bps_per_side: tuple[float, ...] = (
        0.0,
        1.0,
        2.0,
        3.0,
        5.0,
        7.0,
        10.0,
        15.0,
        20.0,
    )
    rolling_trade_window: int = 50

    results_folder: Path = Path("results")
    reports_folder: Path = Path("reports")

    def validate(self) -> None:
        if not self.experiment_id.strip():
            raise ValueError("experiment_id cannot be empty.")

        if not self.experiment_name.strip():
            raise ValueError("experiment_name cannot be empty.")

        if not self.strategy_name.strip():
            raise ValueError("strategy_name cannot be empty.")

        if self.starting_capital <= 0:
            raise ValueError("starting_capital must be positive.")

        if self.commission_bps_per_side < 0:
            raise ValueError(
                "commission_bps_per_side cannot be negative."
            )

        if self.slippage_bps_per_side < 0:
            raise ValueError(
                "slippage_bps_per_side cannot be negative."
            )

        if self.execution_lag_bars < 0:
            raise ValueError(
                "execution_lag_bars cannot be negative."
            )

        if self.run_mcpt and self.mcpt_permutations < 1:
            raise ValueError(
                "mcpt_permutations must be at least 1."
            )

        if self.run_walkforward:
            if self.walkforward_training_bars < 1:
                raise ValueError(
                    "walkforward_training_bars must be positive."
                )

            if self.walkforward_retrain_bars < 1:
                raise ValueError(
                    "walkforward_retrain_bars must be positive."
                )

        if not self.fixed_parameters:
            raise ValueError(
                "fixed_parameters cannot be empty."
            )

        if not self.optimization_grid:
            raise ValueError(
                "optimization_grid cannot be empty."
            )


def normalize_experiment_module(value: str) -> str:
    """Convert EXP-001, exp_001, exp001 or 001 into exp_001."""

    cleaned = value.strip().lower().replace("-", "_")

    if cleaned.endswith(".py"):
        cleaned = cleaned[:-3]

    if cleaned.startswith("experiments."):
        cleaned = cleaned.split(".", maxsplit=1)[1]

    if cleaned.startswith("exp_"):
        suffix = cleaned[4:]
    elif cleaned.startswith("exp"):
        suffix = cleaned[3:].lstrip("_")
    else:
        suffix = cleaned

    if not suffix.isdigit():
        raise ValueError(
            "Experiment must look like EXP-001, exp_001 or 001."
        )

    return f"exp_{int(suffix):03d}"


def load_experiment(value: str) -> ResearchConfig:
    module_name = normalize_experiment_module(value)

    try:
        module = import_module(
            f"experiments.{module_name}"
        )
    except ModuleNotFoundError as error:
        if error.name == f"experiments.{module_name}":
            raise FileNotFoundError(
                "Experiment configuration not found: "
                f"experiments/{module_name}.py"
            ) from error

        raise

    config = getattr(module, "EXPERIMENT", None)

    if not isinstance(config, ResearchConfig):
        raise TypeError(
            f"experiments/{module_name}.py must define "
            "EXPERIMENT = ResearchConfig(...)."
        )

    config.validate()
    return config


def list_experiments() -> list[ResearchConfig]:
    experiments_directory = (
        Path(__file__).resolve().parent
        / "experiments"
    )

    if not experiments_directory.exists():
        return []

    configs: list[ResearchConfig] = []

    for path in sorted(
        experiments_directory.glob("exp_[0-9][0-9][0-9].py")
    ):
        configs.append(load_experiment(path.stem))

    return configs


if __name__ == "__main__":
    configs = list_experiments()

    if not configs:
        print("No experiment configuration files found.")
    else:
        print("Available experiments")
        print("---------------------")

        for config in configs:
            print(
                f"{config.experiment_id}: "
                f"{config.experiment_name}"
            )
