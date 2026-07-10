from __future__ import annotations

import argparse
import html
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from experiment_config import load_experiment
from trade_diagnostics import calculate_trade_diagnostics


PROJECT_DIR = Path(__file__).resolve().parent


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build loss-size and trade-quality diagnostics "
            "from an existing research-lab result."
        )
    )

    parser.add_argument(
        "--experiment",
        default="EXP-002",
        help="Experiment ID, for example EXP-001 or EXP-002.",
    )

    parser.add_argument(
        "--rolling-window",
        type=int,
        default=30,
        help="Number of trades used in rolling trade-quality charts.",
    )

    return parser.parse_args()


def resolve(path: Path) -> Path:
    if path.is_absolute():
        return path

    return PROJECT_DIR / path


def load_trade_file(
    path: Path,
) -> pd.DataFrame | None:
    if not path.exists():
        return None

    trades = pd.read_csv(path)

    for column in ["entry_time", "exit_time"]:
        if column in trades.columns:
            trades[column] = pd.to_datetime(
                trades[column]
            )

    return trades


def rolling_profit_factor(
    trades: pd.DataFrame,
    window: int,
) -> pd.Series:
    pnl = trades["pnl_cash"].astype(float)

    gains = (
        pnl.clip(lower=0)
        .rolling(window, min_periods=window)
        .sum()
    )

    losses = (
        (-pnl.clip(upper=0))
        .rolling(window, min_periods=window)
        .sum()
    )

    return gains / losses.replace(0, np.nan)


def save_figure(
    report_directory: Path,
    filename: str,
) -> None:
    plt.tight_layout()
    plt.savefig(
        report_directory / filename,
        dpi=140,
        bbox_inches="tight",
    )
    plt.close()


def main() -> None:
    arguments = parse_arguments()

    if arguments.rolling_window < 2:
        raise ValueError(
            "--rolling-window must be at least 2."
        )

    config = load_experiment(
        arguments.experiment
    )

    results_directory = (
        resolve(config.results_folder)
        / config.experiment_id
    )

    report_directory = (
        resolve(config.reports_folder)
        / f"{config.experiment_id}-trade-diagnostics"
    )

    report_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    test_files = {
        "Fixed parameters": (
            results_directory
            / "fixed_trades.csv"
        ),
        "Walk-forward": (
            results_directory
            / "walkforward_trades.csv"
        ),
    }

    ledgers: dict[str, pd.DataFrame] = {}

    for test_name, path in test_files.items():
        trades = load_trade_file(path)

        if trades is not None:
            ledgers[test_name] = trades

    if not ledgers:
        raise FileNotFoundError(
            "No completed-trade files were found in "
            f"{results_directory}. Run the research experiment first."
        )

    summary_rows = []
    side_frames = []
    streak_frames = []

    diagnostics_by_test = {}

    for test_name, trades in ledgers.items():
        diagnostics = calculate_trade_diagnostics(
            trades
        )

        diagnostics_by_test[test_name] = diagnostics

        summary_rows.append(
            {
                "test": test_name,
                **diagnostics.summary,
            }
        )

        side_table = diagnostics.by_side.copy()
        side_table.insert(
            0,
            "test",
            test_name,
        )
        side_frames.append(side_table)

        streak_table = diagnostics.streaks.copy()
        streak_table.insert(
            0,
            "test",
            test_name,
        )
        streak_frames.append(streak_table)

    summary = pd.DataFrame(
        summary_rows
    ).set_index("test")

    by_side = (
        pd.concat(side_frames, ignore_index=True)
        if side_frames
        else pd.DataFrame()
    )

    streaks = (
        pd.concat(streak_frames, ignore_index=True)
        if streak_frames
        else pd.DataFrame()
    )

    summary.to_csv(
        results_directory
        / "trade_diagnostics_summary.csv"
    )

    by_side.to_csv(
        results_directory
        / "trade_diagnostics_by_side.csv",
        index=False,
    )

    streaks.to_csv(
        results_directory
        / "trade_streaks.csv",
        index=False,
    )

    plt.style.use("dark_background")

    # --------------------------------------------------------
    # Chart 1: trade-return distributions
    # --------------------------------------------------------

    plt.figure(figsize=(14, 7))

    for test_name, trades in ledgers.items():
        plt.hist(
            trades["net_return_percent"],
            bins=45,
            alpha=0.55,
            label=test_name,
        )

    plt.axvline(0, linewidth=1)
    plt.title(
        f"{config.experiment_id} — Completed-Trade Returns"
    )
    plt.xlabel("Net Return per Trade (%)")
    plt.ylabel("Trades")
    plt.grid(alpha=0.2)
    plt.legend()

    save_figure(
        report_directory,
        "01_trade_return_distribution.png",
    )

    # --------------------------------------------------------
    # Chart 2: cumulative PnL by completed trade
    # --------------------------------------------------------

    plt.figure(figsize=(14, 7))

    for test_name, trades in ledgers.items():
        ordered = trades.sort_values(
            ["exit_time", "trade_id"]
        ).reset_index(drop=True)

        cumulative_pnl = (
            ordered["pnl_cash"].cumsum()
        )

        trade_number = np.arange(
            1,
            len(ordered) + 1,
        )

        plt.plot(
            trade_number,
            cumulative_pnl,
            linewidth=1.8,
            label=test_name,
        )

    plt.axhline(0, linewidth=1, linestyle="--")
    plt.title(
        f"{config.experiment_id} — Cumulative PnL by Trade"
    )
    plt.xlabel("Completed Trade Number")
    plt.ylabel("Cumulative PnL")
    plt.grid(alpha=0.2)
    plt.legend()

    save_figure(
        report_directory,
        "02_cumulative_trade_pnl.png",
    )

    # --------------------------------------------------------
    # Chart 3: rolling average trade return
    # --------------------------------------------------------

    plt.figure(figsize=(14, 7))

    for test_name, trades in ledgers.items():
        ordered = trades.sort_values(
            ["exit_time", "trade_id"]
        ).reset_index(drop=True)

        rolling_average = (
            ordered["net_return_percent"]
            .rolling(
                arguments.rolling_window,
                min_periods=arguments.rolling_window,
            )
            .mean()
        )

        plt.plot(
            ordered["exit_time"],
            rolling_average,
            linewidth=1.7,
            label=test_name,
        )

    plt.axhline(0, linewidth=1, linestyle="--")
    plt.title(
        f"{config.experiment_id} — Rolling "
        f"{arguments.rolling_window}-Trade Average Return"
    )
    plt.xlabel("Trade Exit Date")
    plt.ylabel("Average Net Trade Return (%)")
    plt.grid(alpha=0.2)
    plt.legend()

    save_figure(
        report_directory,
        "03_rolling_average_trade.png",
    )

    # --------------------------------------------------------
    # Chart 4: rolling trade profit factor
    # --------------------------------------------------------

    plt.figure(figsize=(14, 7))

    for test_name, trades in ledgers.items():
        ordered = trades.sort_values(
            ["exit_time", "trade_id"]
        ).reset_index(drop=True)

        rolling_pf = rolling_profit_factor(
            ordered,
            arguments.rolling_window,
        )

        plt.plot(
            ordered["exit_time"],
            rolling_pf,
            linewidth=1.7,
            label=test_name,
        )

    plt.axhline(
        1.0,
        linewidth=1,
        linestyle="--",
        label="PF = 1.0",
    )
    plt.title(
        f"{config.experiment_id} — Rolling "
        f"{arguments.rolling_window}-Trade Profit Factor"
    )
    plt.xlabel("Trade Exit Date")
    plt.ylabel("Rolling Trade Profit Factor")
    plt.ylim(bottom=0)
    plt.grid(alpha=0.2)
    plt.legend()

    save_figure(
        report_directory,
        "04_rolling_trade_pf.png",
    )

    # --------------------------------------------------------
    # Chart 5: largest losses
    # --------------------------------------------------------

    plt.figure(figsize=(14, 7))

    x_offset = 0

    for test_name, trades in ledgers.items():
        worst = (
            trades.nsmallest(
                20,
                "net_return_percent",
            )
            .sort_values(
                "net_return_percent"
            )
            .reset_index(drop=True)
        )

        positions = (
            np.arange(len(worst))
            + x_offset
        )

        plt.scatter(
            positions,
            worst["net_return_percent"],
            s=55,
            label=test_name,
        )

        x_offset += len(worst) + 2

    plt.axhline(0, linewidth=1)
    plt.title(
        f"{config.experiment_id} — Twenty Largest "
        "Completed-Trade Losses"
    )
    plt.xlabel("Loss Rank, Grouped by Test")
    plt.ylabel("Net Trade Return (%)")
    plt.grid(alpha=0.2)
    plt.legend()

    save_figure(
        report_directory,
        "05_largest_losses.png",
    )

    # --------------------------------------------------------
    # HTML report
    # --------------------------------------------------------

    display_columns = [
        "total_trades",
        "win_rate_percent",
        "trade_profit_factor",
        "average_trade_percent",
        "median_trade_percent",
        "average_winner_percent",
        "average_loser_percent",
        "payoff_ratio",
        "largest_win_percent",
        "largest_loss_percent",
        "fifth_percentile_trade_percent",
        "top_1_loss_share_percent",
        "top_5_loss_share_percent",
        "max_consecutive_wins",
        "max_consecutive_losses",
        "average_winner_holding_hours",
        "average_loser_holding_hours",
    ]

    display_summary = summary[
        display_columns
    ].copy().round(3)

    summary_html = display_summary.to_html(
        classes="metrics",
        border=0,
    )

    side_html = (
        by_side.round(3).to_html(
            index=False,
            classes="metrics",
            border=0,
        )
        if not by_side.empty
        else "<p>No side-level results.</p>"
    )

    fixed = summary.loc[
        "Fixed parameters"
    ] if "Fixed parameters" in summary.index else None

    if fixed is not None:
        interpretation = (
            f"The fixed strategy won "
            f"{fixed['win_rate_percent']:.1f}% of trades. "
            f"Its average winner was "
            f"{fixed['average_winner_percent']:.3f}%, while "
            f"its average loser was "
            f"{fixed['average_loser_percent']:.3f}%. "
            f"The payoff ratio was "
            f"{fixed['payoff_ratio']:.3f}."
        )
    else:
        interpretation = (
            "Review average winners, average losers, payoff ratio "
            "and loss concentration together."
        )

    report_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{html.escape(config.experiment_id)} Trade Diagnostics</title>

<style>
body {{
    background: #090909;
    color: #eeeeee;
    font-family: Arial, Helvetica, sans-serif;
    margin: 0;
}}

.page {{
    max-width: 1450px;
    margin: auto;
    padding: 35px;
}}

h1 {{
    font-size: 38px;
    margin-bottom: 5px;
}}

h2 {{
    margin-top: 45px;
    border-bottom: 1px solid #333333;
    padding-bottom: 8px;
}}

.subtitle {{
    color: #aaaaaa;
    margin-bottom: 25px;
}}

.note {{
    background: #151515;
    border-left: 5px solid #888888;
    padding: 18px;
    margin: 20px 0;
}}

.chart {{
    width: 100%;
    border: 1px solid #333333;
    border-radius: 8px;
    margin: 15px 0 35px;
}}

.metrics {{
    width: 100%;
    border-collapse: collapse;
    background: #151515;
}}

.metrics th,
.metrics td {{
    border: 1px solid #333333;
    padding: 10px;
    text-align: center;
}}

.metrics th {{
    background: #222222;
}}
</style>
</head>

<body>
<div class="page">

<h1>
{html.escape(config.experiment_id)} —
Trade Diagnostics
</h1>

<div class="subtitle">
{html.escape(config.experiment_name)}
</div>

<div class="note">
<strong>Why this report exists</strong>

<p>
Win rate alone does not measure strategy quality. A strategy can
win often and still lose money when its average loss is much larger
than its average win.
</p>

<p>{html.escape(interpretation)}</p>
</div>

<h2>Trade-Quality Summary</h2>
{summary_html}

<h2>Trade Returns</h2>
<img class="chart"
     src="01_trade_return_distribution.png"
     alt="Trade-return distribution">

<h2>Cumulative PnL by Trade</h2>
<img class="chart"
     src="02_cumulative_trade_pnl.png"
     alt="Cumulative trade PnL">

<h2>Rolling Average Trade</h2>
<img class="chart"
     src="03_rolling_average_trade.png"
     alt="Rolling average trade">

<h2>Rolling Trade Profit Factor</h2>
<img class="chart"
     src="04_rolling_trade_pf.png"
     alt="Rolling trade Profit Factor">

<h2>Largest Losses</h2>
<img class="chart"
     src="05_largest_losses.png"
     alt="Largest completed-trade losses">

<h2>Breakdown by Side</h2>
{side_html}

<h2>How to Read the Main Fields</h2>

<p>
<strong>Payoff ratio:</strong>
average winner divided by the absolute average loser.
A value below 1 means the typical loss is larger than the
typical win.
</p>

<p>
<strong>Top-five loss share:</strong>
the percentage of all gross losses caused by the five largest
losing trades. A high value indicates tail-loss concentration.
</p>

<p>
<strong>Fifth percentile:</strong>
a threshold for the worst 5% of completed trades.
</p>

<p>
<strong>Maximum losing streak:</strong>
the greatest number of consecutive completed losing trades.
</p>

</div>
</body>
</html>
"""

    report_file = (
        report_directory / "report.html"
    )

    report_file.write_text(
        report_html,
        encoding="utf-8",
    )

    print()
    print("Trade diagnostics created.")
    print()
    print(
        summary[
            [
                "total_trades",
                "win_rate_percent",
                "trade_profit_factor",
                "average_winner_percent",
                "average_loser_percent",
                "payoff_ratio",
                "largest_loss_percent",
                "top_5_loss_share_percent",
                "max_consecutive_losses",
            ]
        ]
        .round(3)
        .to_string()
    )

    print()
    print(
        "Summary CSV: "
        f"{results_directory / 'trade_diagnostics_summary.csv'}"
    )
    print(
        "Side CSV:    "
        f"{results_directory / 'trade_diagnostics_by_side.csv'}"
    )
    print(
        "Streak CSV:  "
        f"{results_directory / 'trade_streaks.csv'}"
    )
    print(f"Report:      {report_file}")


if __name__ == "__main__":
    main()
