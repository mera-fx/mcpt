from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

from donchian import donchian_breakout


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent

DATA_FILE = PROJECT_DIR / "data" / "BTCUSDT_1h.parquet"

COMPARISON_SUMMARY_FILE = (
    PROJECT_DIR / "results" / "EXP-001_comparison.csv"
)

COMPARISON_DETAIL_FILE = (
    PROJECT_DIR / "results" / "EXP-001_comparison_detail.csv"
)

MCPT_FILE = (
    PROJECT_DIR / "results" / "EXP-001_mcpt.csv"
)

REPORT_DIR = (
    PROJECT_DIR / "reports" / "EXP-001"
)

TRAIN_START_YEAR = 2018
TRAIN_END_YEAR = 2022  # Exclusive

LOOKBACK_MIN = 12
LOOKBACK_MAX = 168

# The position charts show one year so signals remain readable.
POSITION_CHART_START = "2025-01-01"
POSITION_CHART_END = "2025-12-31 23:59:59"


# ============================================================
# VISUAL SETTINGS
# ============================================================

plt.style.use("dark_background")

plt.rcParams.update(
    {
        "figure.figsize": (14, 7),
        "figure.dpi": 120,
        "font.size": 11,
        "axes.titleweight": "bold",
        "axes.titlesize": 17,
        "axes.labelsize": 12,
        "legend.fontsize": 10,
    }
)

COLORS = {
    "fixed": "#00d9ff",
    "walkforward": "#ff3cac",
    "buy_hold": "#ffb000",
    "real": "#ff3333",
    "long": "#00d26a",
    "short": "#ff4d4d",
    "neutral": "#888888",
    "grid": "#333333",
}


# ============================================================
# VALIDATION AND LOADING
# ============================================================

def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(
            f"Required file was not found:\n{path}"
        )


for required_path in [
    DATA_FILE,
    COMPARISON_SUMMARY_FILE,
    COMPARISON_DETAIL_FILE,
    MCPT_FILE,
]:
    require_file(required_path)

REPORT_DIR.mkdir(parents=True, exist_ok=True)

summary = pd.read_csv(
    COMPARISON_SUMMARY_FILE,
    index_col=0,
)

detail = pd.read_csv(
    COMPARISON_DETAIL_FILE,
    index_col=0,
    parse_dates=True,
)

detail.index = pd.to_datetime(detail.index)
detail = detail.sort_index()

mcpt_results = pd.read_csv(MCPT_FILE)

if "best_permuted_pf" not in mcpt_results.columns:
    raise RuntimeError(
        "EXP-001_mcpt.csv does not contain "
        "'best_permuted_pf'."
    )

permuted_pfs = (
    mcpt_results["best_permuted_pf"]
    .dropna()
    .astype(float)
)


# ============================================================
# HELPERS
# ============================================================

def save_figure(
    figure: plt.Figure,
    filename: str,
) -> None:
    output_path = REPORT_DIR / filename

    figure.tight_layout()
    figure.savefig(
        output_path,
        bbox_inches="tight",
        facecolor=figure.get_facecolor(),
    )

    plt.close(figure)


def equity_from_returns(
    returns: pd.Series,
) -> pd.Series:
    clean_returns = returns.fillna(0)
    return np.exp(clean_returns.cumsum())


def drawdown_from_equity(
    equity: pd.Series,
) -> pd.Series:
    return equity / equity.cummax() - 1


def calculate_bar_profit_factor(
    returns: pd.Series,
) -> float:
    returns = returns.dropna()

    gains = returns[returns > 0].sum()
    losses = returns[returns < 0].abs().sum()

    if losses == 0:
        return float("inf")

    return float(gains / losses)


def format_summary_table(
    results: pd.DataFrame,
) -> str:
    display = results.copy()

    if "profit_factor" in display.columns:
        display["profit_factor"] = display[
            "profit_factor"
        ].map(lambda value: f"{value:.4f}")

    if "total_return_percent" in display.columns:
        display["total_return_percent"] = display[
            "total_return_percent"
        ].map(lambda value: f"{value:.2f}%")

    if "max_drawdown_percent" in display.columns:
        display["max_drawdown_percent"] = display[
            "max_drawdown_percent"
        ].map(lambda value: f"{value:.2f}%")

    if "position_changes" in display.columns:
        display["position_changes"] = display[
            "position_changes"
        ].map(lambda value: f"{int(value):,}")

    display = display.rename(
        columns={
            "profit_factor": "Bar PF",
            "total_return_percent": "Return",
            "max_drawdown_percent": "Max Drawdown",
            "position_changes": "Position Changes",
        }
    )

    return display.to_html(
        classes="metrics-table",
        border=0,
        justify="center",
    )


# ============================================================
# EQUITY COMPARISON
# ============================================================

fixed_equity = equity_from_returns(
    detail["fixed_return"]
)

walkforward_equity = equity_from_returns(
    detail["walkforward_return"]
)

buy_hold_equity = equity_from_returns(
    detail["buy_hold_return"]
)

figure, axis = plt.subplots()

axis.plot(
    fixed_equity.index,
    fixed_equity,
    label="Fixed Donchian 49",
    color=COLORS["fixed"],
    linewidth=1.8,
)

axis.plot(
    walkforward_equity.index,
    walkforward_equity,
    label="Walk-Forward Donchian",
    color=COLORS["walkforward"],
    linewidth=1.8,
)

axis.plot(
    buy_hold_equity.index,
    buy_hold_equity,
    label="Buy and Hold",
    color=COLORS["buy_hold"],
    linewidth=1.8,
)

axis.axhline(
    1.0,
    color="white",
    linewidth=0.8,
    alpha=0.5,
)

axis.set_title(
    "EXP-001 — Out-of-Sample Equity Comparison"
)

axis.set_xlabel("Date")
axis.set_ylabel("Growth of 1.00")
axis.grid(alpha=0.2)
axis.legend()

save_figure(
    figure,
    "01_equity_comparison.png",
)


# ============================================================
# DRAWDOWN COMPARISON
# ============================================================

fixed_drawdown = drawdown_from_equity(
    fixed_equity
) * 100

walkforward_drawdown = drawdown_from_equity(
    walkforward_equity
) * 100

buy_hold_drawdown = drawdown_from_equity(
    buy_hold_equity
) * 100

figure, axis = plt.subplots()

axis.plot(
    fixed_drawdown.index,
    fixed_drawdown,
    label="Fixed Donchian 49",
    color=COLORS["fixed"],
    linewidth=1.5,
)

axis.plot(
    walkforward_drawdown.index,
    walkforward_drawdown,
    label="Walk-Forward Donchian",
    color=COLORS["walkforward"],
    linewidth=1.5,
)

axis.plot(
    buy_hold_drawdown.index,
    buy_hold_drawdown,
    label="Buy and Hold",
    color=COLORS["buy_hold"],
    linewidth=1.5,
)

axis.axhline(
    0,
    color="white",
    linewidth=0.8,
    alpha=0.5,
)

axis.set_title(
    "EXP-001 — Drawdown Comparison"
)

axis.set_xlabel("Date")
axis.set_ylabel("Drawdown (%)")
axis.grid(alpha=0.2)
axis.legend()

save_figure(
    figure,
    "02_drawdown_comparison.png",
)


# ============================================================
# MONTE CARLO PERMUTATION DISTRIBUTION
# ============================================================

raw_data = pd.read_parquet(DATA_FILE)
raw_data.index = pd.to_datetime(raw_data.index)
raw_data = raw_data.sort_index()

training_data = raw_data[
    (raw_data.index.year >= TRAIN_START_YEAR)
    & (raw_data.index.year < TRAIN_END_YEAR)
].copy()

training_returns = (
    np.log(training_data["close"])
    .diff()
    .shift(-1)
)

sensitivity_rows = []

for lookback in range(
    LOOKBACK_MIN,
    LOOKBACK_MAX + 1,
):
    signal = donchian_breakout(
        training_data,
        lookback,
    )

    strategy_returns = (
        signal * training_returns
    )

    profit_factor = (
        calculate_bar_profit_factor(
            strategy_returns
        )
    )

    sensitivity_rows.append(
        {
            "lookback": lookback,
            "profit_factor": profit_factor,
        }
    )

sensitivity = pd.DataFrame(
    sensitivity_rows
)

finite_sensitivity = sensitivity.replace(
    [np.inf, -np.inf],
    np.nan,
).dropna()

best_row = finite_sensitivity.loc[
    finite_sensitivity["profit_factor"].idxmax()
]

best_real_lookback = int(
    best_row["lookback"]
)

best_real_pf = float(
    best_row["profit_factor"]
)

better_or_equal = int(
    (permuted_pfs >= best_real_pf).sum()
)

mcpt_p_value = (
    better_or_equal + 1
) / (
    len(permuted_pfs) + 1
)

real_percentile = (
    100
    * (
        permuted_pfs < best_real_pf
    ).mean()
)

figure, axis = plt.subplots()

axis.hist(
    permuted_pfs,
    bins=40,
    color="#d9d9d9",
    alpha=0.85,
    edgecolor="#555555",
    label="Optimized Permutations",
)

axis.axvline(
    best_real_pf,
    color=COLORS["real"],
    linewidth=3,
    label=(
        f"Real Optimized PF "
        f"({best_real_pf:.4f})"
    ),
)

axis.set_title(
    "EXP-001 — In-Sample Permutation Test"
)

axis.set_xlabel(
    "Best Bar-Return Profit Factor"
)

axis.set_ylabel(
    "Number of Permutations"
)

axis.grid(alpha=0.15)

axis.text(
    0.98,
    0.95,
    (
        f"Permutations: {len(permuted_pfs):,}\n"
        f"Real percentile: {real_percentile:.1f}%\n"
        f"MCPT p-value: {mcpt_p_value:.4f}"
    ),
    transform=axis.transAxes,
    horizontalalignment="right",
    verticalalignment="top",
    bbox={
        "facecolor": "#151515",
        "edgecolor": "#777777",
        "alpha": 0.9,
        "boxstyle": "round,pad=0.6",
    },
)

axis.legend()

save_figure(
    figure,
    "03_mcpt_distribution.png",
)


# ============================================================
# PARAMETER SENSITIVITY
# ============================================================

figure, axis = plt.subplots()

axis.plot(
    finite_sensitivity["lookback"],
    finite_sensitivity["profit_factor"],
    color=COLORS["fixed"],
    linewidth=1.7,
)

axis.axhline(
    1.0,
    color="white",
    linestyle="--",
    linewidth=1,
    alpha=0.6,
    label="PF = 1.0",
)

axis.scatter(
    [best_real_lookback],
    [best_real_pf],
    color=COLORS["real"],
    s=90,
    zorder=5,
    label=(
        f"Best: {best_real_lookback} hours, "
        f"PF {best_real_pf:.4f}"
    ),
)

axis.set_title(
    "EXP-001 — In-Sample Parameter Sensitivity"
)

axis.set_xlabel(
    "Donchian Lookback (Hours)"
)

axis.set_ylabel(
    "Bar-Return Profit Factor"
)

axis.grid(alpha=0.2)
axis.legend()

save_figure(
    figure,
    "04_parameter_sensitivity.png",
)


# ============================================================
# PRICE AND POSITION VISUALS
# ============================================================

def create_position_chart(
    signal_column: str,
    title: str,
    filename: str,
) -> None:
    view = detail.loc[
        POSITION_CHART_START:
        POSITION_CHART_END
    ].copy()

    if view.empty:
        view = detail.tail(24 * 365).copy()

    signal = view[signal_column].ffill()

    figure, axis = plt.subplots()

    axis.plot(
        view.index,
        view["close"],
        color="white",
        linewidth=1.2,
        label="BTCUSDT Close",
    )

    change_mask = signal.ne(
        signal.shift()
    )

    segment_starts = list(
        signal.index[change_mask]
    )

    for segment_number, start in enumerate(
        segment_starts
    ):
        if segment_number + 1 < len(
            segment_starts
        ):
            end = segment_starts[
                segment_number + 1
            ]
        else:
            end = view.index[-1]

        value = signal.loc[start]

        if value > 0:
            background_color = COLORS["long"]
        elif value < 0:
            background_color = COLORS["short"]
        else:
            background_color = COLORS["neutral"]

        axis.axvspan(
            start,
            end,
            color=background_color,
            alpha=0.09,
        )

    legend_items = [
        Patch(
            facecolor=COLORS["long"],
            alpha=0.25,
            label="Long",
        ),
        Patch(
            facecolor=COLORS["short"],
            alpha=0.25,
            label="Short",
        ),
    ]

    axis.set_title(title)
    axis.set_xlabel("Date")
    axis.set_ylabel("BTCUSDT Price")
    axis.grid(alpha=0.18)

    axis.legend(
        handles=legend_items,
        loc="best",
    )

    save_figure(
        figure,
        filename,
    )


create_position_chart(
    signal_column="fixed_signal",
    title=(
        "EXP-001 — Fixed Donchian 49 "
        "Positions During 2025"
    ),
    filename="05_fixed_positions.png",
)

create_position_chart(
    signal_column="walkforward_signal",
    title=(
        "EXP-001 — Walk-Forward Donchian "
        "Positions During 2025"
    ),
    filename="06_walkforward_positions.png",
)


# ============================================================
# HTML REPORT
# ============================================================

fixed_return = float(
    summary.loc[
        "Fixed Donchian 49",
        "total_return_percent",
    ]
)

walkforward_return = float(
    summary.loc[
        "Walk-Forward Donchian",
        "total_return_percent",
    ]
)

buy_hold_return = float(
    summary.loc[
        "Buy and Hold",
        "total_return_percent",
    ]
)

fixed_drawdown_value = float(
    summary.loc[
        "Fixed Donchian 49",
        "max_drawdown_percent",
    ]
)

walkforward_drawdown_value = float(
    summary.loc[
        "Walk-Forward Donchian",
        "max_drawdown_percent",
    ]
)

summary_table_html = format_summary_table(
    summary
)

decision = "REJECTED"

decision_reason = (
    "The fixed and walk-forward Donchian variants both "
    "lost money out of sample. Monthly re-optimization "
    "performed worse than keeping the original parameter."
)

report_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>EXP-001 Research Report</title>

<style>
    body {{
        background: #090909;
        color: #eeeeee;
        font-family: Arial, Helvetica, sans-serif;
        margin: 0;
        padding: 0;
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
        border-bottom: 1px solid #333333;
        padding-bottom: 8px;
        margin-top: 45px;
    }}

    .subtitle {{
        color: #aaaaaa;
        margin-bottom: 30px;
    }}

    .cards {{
        display: grid;
        grid-template-columns:
            repeat(auto-fit, minmax(220px, 1fr));
        gap: 18px;
        margin: 25px 0;
    }}

    .card {{
        background: #151515;
        border: 1px solid #2d2d2d;
        border-radius: 10px;
        padding: 20px;
    }}

    .card-label {{
        color: #aaaaaa;
        font-size: 14px;
    }}

    .card-value {{
        font-size: 28px;
        font-weight: bold;
        margin-top: 8px;
    }}

    .decision {{
        border-left: 6px solid #ff4d4d;
        background: #1b1111;
        padding: 22px;
        border-radius: 8px;
        margin: 25px 0;
    }}

    .decision-title {{
        color: #ff6666;
        font-size: 27px;
        font-weight: bold;
    }}

    .chart {{
        width: 100%;
        margin: 16px 0 35px 0;
        border: 1px solid #303030;
        border-radius: 8px;
    }}

    .metrics-table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 20px;
        background: #141414;
    }}

    .metrics-table th,
    .metrics-table td {{
        border: 1px solid #333333;
        padding: 13px;
        text-align: center;
    }}

    .metrics-table th {{
        background: #202020;
    }}

    .warning {{
        background: #241d0c;
        border-left: 5px solid #ffb000;
        padding: 18px;
        margin: 25px 0;
    }}

    code {{
        color: #00d9ff;
    }}
</style>
</head>

<body>
<div class="page">

    <h1>EXP-001 — Donchian Breakout</h1>

    <div class="subtitle">
        BTCUSDT spot price data · 1-hour bars ·
        Out-of-sample period 2022–2025
    </div>

    <div class="decision">
        <div class="decision-title">
            Final Decision: {decision}
        </div>

        <p>{decision_reason}</p>
    </div>

    <div class="cards">
        <div class="card">
            <div class="card-label">
                In-Sample Best Lookback
            </div>

            <div class="card-value">
                {best_real_lookback} hours
            </div>
        </div>

        <div class="card">
            <div class="card-label">
                In-Sample Bar PF
            </div>

            <div class="card-value">
                {best_real_pf:.4f}
            </div>
        </div>

        <div class="card">
            <div class="card-label">
                MCPT p-value
            </div>

            <div class="card-value">
                {mcpt_p_value:.4f}
            </div>
        </div>

        <div class="card">
            <div class="card-label">
                Fixed OOS Return
            </div>

            <div class="card-value">
                {fixed_return:.2f}%
            </div>
        </div>

        <div class="card">
            <div class="card-label">
                Walk-Forward OOS Return
            </div>

            <div class="card-value">
                {walkforward_return:.2f}%
            </div>
        </div>

        <div class="card">
            <div class="card-label">
                Buy-and-Hold Return
            </div>

            <div class="card-value">
                {buy_hold_return:.2f}%
            </div>
        </div>
    </div>

    <div class="warning">
        Current Profit Factor calculations use hourly strategy
        returns, not completed trades. Fees, spread, slippage,
        financing and execution constraints are not yet included.
    </div>

    <h2>Performance Summary</h2>

    {summary_table_html}

    <h2>Equity Comparison</h2>
    <img
        class="chart"
        src="01_equity_comparison.png"
        alt="Equity comparison"
    >

    <h2>Drawdown Comparison</h2>
    <img
        class="chart"
        src="02_drawdown_comparison.png"
        alt="Drawdown comparison"
    >

    <h2>Monte Carlo Permutation Test</h2>

    <p>
        The real optimized result exceeded
        approximately {real_percentile:.1f}% of randomized
        optimized markets. Its p-value was
        <strong>{mcpt_p_value:.4f}</strong>.
    </p>

    <img
        class="chart"
        src="03_mcpt_distribution.png"
        alt="MCPT distribution"
    >

    <h2>Parameter Sensitivity</h2>

    <p>
        This chart shows whether nearby Donchian lookbacks
        behaved similarly or whether the selected parameter
        was an isolated result.
    </p>

    <img
        class="chart"
        src="04_parameter_sensitivity.png"
        alt="Parameter sensitivity"
    >

    <h2>Fixed Donchian Positions</h2>

    <p>
        Green backgrounds represent long exposure.
        Red backgrounds represent short exposure.
    </p>

    <img
        class="chart"
        src="05_fixed_positions.png"
        alt="Fixed Donchian positions"
    >

    <h2>Walk-Forward Positions</h2>

    <img
        class="chart"
        src="06_walkforward_positions.png"
        alt="Walk-forward positions"
    >

    <h2>Research Conclusion</h2>

    <p>
        The in-sample result was economically weak and the
        permutation-test result was borderline. Neither the
        fixed parameter nor monthly walk-forward optimization
        produced profitable unseen performance.
    </p>

    <p>
        Fixed Donchian maximum drawdown:
        <strong>{fixed_drawdown_value:.2f}%</strong>.
        Walk-forward maximum drawdown:
        <strong>{walkforward_drawdown_value:.2f}%</strong>.
    </p>

    <p>
        EXP-001 should not be modified repeatedly in an attempt
        to force a passing result. New rules must be recorded
        as a separate experiment.
    </p>

</div>
</body>
</html>
"""

report_file = REPORT_DIR / "report.html"

report_file.write_text(
    report_html,
    encoding="utf-8",
)

print()
print("EXP-001 visual report created successfully.")
print()
print(f"Report folder: {REPORT_DIR}")
print(f"Open this file: {report_file}")
print()
print("Charts created:")
print("  01_equity_comparison.png")
print("  02_drawdown_comparison.png")
print("  03_mcpt_distribution.png")
print("  04_parameter_sensitivity.png")
print("  05_fixed_positions.png")
print("  06_walkforward_positions.png")