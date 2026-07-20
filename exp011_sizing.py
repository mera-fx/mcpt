from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np
import pandas as pd

from exp005_futures_orb import get_contract_spec
from exp009_engine import Exp009Result, maximum_drawdown, profit_factor


CALIBRATION_START = "2019-05-06"
CALIBRATION_END = "2020-12-31"
EVALUATION_START = "2021-01-04"
EVALUATION_END = "2025-12-31"
REFERENCE_CAPITAL_USD = 100_000.0
FRACTIONAL_NQ_CAP = 2.0
INTEGER_MNQ_CAP = 20

SIZING_IDS = (
    "fixed_one_nq",
    "fractional_nq_equal_risk",
    "integer_mnq_equal_risk",
)


@dataclass(frozen=True)
class Exp011Calibration:
    signal_candidate_id: str
    market: str
    calibration_start: str
    calibration_end: str
    trade_count: int
    target_dollar_risk_usd: float
    median_one_contract_risk_usd: float
    minimum_one_contract_risk_usd: float
    maximum_one_contract_risk_usd: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_candidate_id": self.signal_candidate_id,
            "market": self.market,
            "calibration_start": self.calibration_start,
            "calibration_end": self.calibration_end,
            "trade_count": self.trade_count,
            "target_dollar_risk_usd": self.target_dollar_risk_usd,
            "median_one_contract_risk_usd": (
                self.median_one_contract_risk_usd
            ),
            "minimum_one_contract_risk_usd": (
                self.minimum_one_contract_risk_usd
            ),
            "maximum_one_contract_risk_usd": (
                self.maximum_one_contract_risk_usd
            ),
        }


@dataclass(frozen=True)
class Exp011SizedResult:
    signal_candidate_id: str
    sizing_id: str
    symbol: str
    target_dollar_risk_usd: float
    summary: dict[str, Any]
    signals: pd.DataFrame
    trades: pd.DataFrame
    equity_curve: pd.DataFrame
    yearly_results: pd.DataFrame
    monthly_results: pd.DataFrame


def _date_mask(
    values: pd.Series | Iterable[Any],
    *,
    start: str,
    end: str,
) -> np.ndarray:
    dates = pd.to_datetime(pd.Series(values), errors="raise")
    return dates.between(pd.Timestamp(start), pd.Timestamp(end)).to_numpy()


def _one_contract_initial_risk(
    trades: pd.DataFrame,
    *,
    symbol: str,
) -> np.ndarray:
    required = {"risk_points", "transaction_cost_usd"}
    missing = sorted(required.difference(trades.columns))
    if missing:
        raise ValueError(
            "Trade ledger is missing initial-risk inputs: "
            + ", ".join(missing)
        )
    multiplier = get_contract_spec(symbol).multiplier_usd_per_point
    risk = (
        trades["risk_points"].to_numpy(dtype=float) * multiplier
        + trades["transaction_cost_usd"].to_numpy(dtype=float)
    )
    if risk.size and (
        not np.all(np.isfinite(risk)) or not np.all(risk > 0)
    ):
        raise ValueError(
            "Every sized trade must have finite positive initial risk."
        )
    return risk


def calibrate_target_dollar_risk(
    primary_nq_result: Exp009Result,
    *,
    start: str = CALIBRATION_START,
    end: str = CALIBRATION_END,
) -> Exp011Calibration:
    if primary_nq_result.symbol != "NQ":
        raise ValueError("EXP-011 calibration must use NQ.")
    if (
        primary_nq_result.candidate.candidate_id
        != "opening_drive_0p5_time"
    ):
        raise ValueError(
            "EXP-011 calibration must use opening_drive_0p5_time."
        )
    if pd.Timestamp(end) >= pd.Timestamp(EVALUATION_START):
        raise ValueError(
            "EXP-011 calibration cannot use evaluation-period data."
        )

    mask = _date_mask(
        primary_nq_result.trades["session_date"],
        start=start,
        end=end,
    )
    calibration_trades = primary_nq_result.trades.loc[mask].copy()
    risk = _one_contract_initial_risk(
        calibration_trades,
        symbol="NQ",
    )
    if risk.size == 0:
        raise ValueError("EXP-011 calibration has no valid NQ trades.")

    target = float(np.median(risk))
    return Exp011Calibration(
        signal_candidate_id=primary_nq_result.candidate.candidate_id,
        market="NQ",
        calibration_start=start,
        calibration_end=end,
        trade_count=int(risk.size),
        target_dollar_risk_usd=target,
        median_one_contract_risk_usd=target,
        minimum_one_contract_risk_usd=float(risk.min()),
        maximum_one_contract_risk_usd=float(risk.max()),
    )


def _maximum_consecutive_losses(values: np.ndarray) -> int:
    maximum = 0
    current = 0
    for value in values:
        if value < 0:
            current += 1
            maximum = max(maximum, current)
        else:
            current = 0
    return maximum


def _worst_rolling_sum(values: np.ndarray, window: int) -> float:
    if len(values) < window:
        return float("nan")
    return float(
        pd.Series(values).rolling(window).sum().dropna().min()
    )


def _summary(
    *,
    signal_candidate_id: str,
    sizing_id: str,
    symbol: str,
    target_dollar_risk_usd: float,
    signals: pd.DataFrame,
    trades: pd.DataFrame,
    evaluation_session_count: int,
) -> dict[str, Any]:
    pnl = trades["net_pnl_usd"].to_numpy(dtype=float)
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    risk = trades["initial_risk_usd"].to_numpy(dtype=float)
    contracts = trades["contracts"].to_numpy(dtype=float)
    maximum_dd = maximum_drawdown(pnl)
    average_risk = float(risk.mean()) if risk.size else 0.0
    risk_std = float(risk.std(ddof=0)) if risk.size else 0.0
    signal_count = int(len(signals))
    skipped = int(signals["skipped_zero_size"].sum())
    completed = int(len(trades))

    return {
        "signal_candidate_id": signal_candidate_id,
        "sizing_id": sizing_id,
        "symbol": symbol,
        "implementation_status": (
            "THEORETICAL_FRACTIONAL_ONLY"
            if sizing_id == "fractional_nq_equal_risk"
            else "IMPLEMENTABLE"
        ),
        "target_dollar_risk_usd": target_dollar_risk_usd,
        "evaluation_session_count": evaluation_session_count,
        "signal_count": signal_count,
        "completed_trades": completed,
        "skipped_zero_size_trades": skipped,
        "zero_contract_skip_rate": (
            float(skipped / signal_count) if signal_count else 0.0
        ),
        "gross_profit_usd": float(wins.sum()),
        "gross_loss_usd": float(losses.sum()),
        "net_profit_usd": float(pnl.sum()),
        "trade_profit_factor": float(profit_factor(pnl)),
        "win_rate": float(np.mean(pnl > 0)) if pnl.size else 0.0,
        "average_trade_usd": float(pnl.mean()) if pnl.size else 0.0,
        "median_trade_usd": (
            float(np.median(pnl)) if pnl.size else 0.0
        ),
        "average_winner_usd": (
            float(wins.mean()) if wins.size else 0.0
        ),
        "average_loser_usd": (
            float(losses.mean()) if losses.size else 0.0
        ),
        "maximum_drawdown_usd": float(maximum_dd),
        "net_profit_to_maximum_drawdown": (
            float(pnl.sum() / abs(maximum_dd))
            if maximum_dd < 0
            else 0.0
        ),
        "average_initial_risk_usd": average_risk,
        "initial_risk_standard_deviation_usd": risk_std,
        "initial_risk_coefficient_of_variation": (
            float(risk_std / average_risk) if average_risk else 0.0
        ),
        "95th_percentile_initial_risk_usd": (
            float(np.percentile(risk, 95)) if risk.size else 0.0
        ),
        "maximum_initial_risk_usd": (
            float(risk.max()) if risk.size else 0.0
        ),
        "maximum_consecutive_losses": _maximum_consecutive_losses(pnl),
        "worst_20_trade_result_usd": _worst_rolling_sum(pnl, 20),
        "worst_50_trade_result_usd": _worst_rolling_sum(pnl, 50),
        "average_contracts": (
            float(contracts.mean()) if contracts.size else 0.0
        ),
        "median_contracts": (
            float(np.median(contracts)) if contracts.size else 0.0
        ),
        "maximum_contracts": (
            float(contracts.max()) if contracts.size else 0.0
        ),
        "average_holding_minutes": (
            float(trades["holding_minutes"].mean())
            if completed
            else 0.0
        ),
        "cost_total_usd": (
            float(trades["transaction_cost_usd"].sum())
            if completed
            else 0.0
        ),
        "session_participation_rate": (
            float(completed / evaluation_session_count)
            if evaluation_session_count
            else 0.0
        ),
        "automatic_winner": False,
        "pass_fail_gate": False,
    }


def apply_locked_sizing(
    base_result: Exp009Result,
    *,
    sizing_id: str,
    target_dollar_risk_usd: float,
    evaluation_session_dates: Iterable[Any],
    start: str = EVALUATION_START,
    end: str = EVALUATION_END,
) -> Exp011SizedResult:
    if sizing_id not in SIZING_IDS:
        raise KeyError(f"Unknown EXP-011 sizing method: {sizing_id}")
    expected_symbol = (
        "MNQ" if sizing_id == "integer_mnq_equal_risk" else "NQ"
    )
    if base_result.symbol != expected_symbol:
        raise ValueError(
            f"{sizing_id} requires {expected_symbol}, "
            f"not {base_result.symbol}."
        )
    if (
        not np.isfinite(target_dollar_risk_usd)
        or target_dollar_risk_usd <= 0
    ):
        raise ValueError("Target dollar risk must be finite and positive.")

    session_dates = pd.Series(evaluation_session_dates).astype(str)
    session_mask = _date_mask(session_dates, start=start, end=end)
    sessions = session_dates.loc[session_mask].reset_index(drop=True)
    if sessions.empty:
        raise ValueError("EXP-011 evaluation period has no sessions.")
    if sessions.duplicated().any():
        raise ValueError("EXP-011 evaluation sessions must be unique.")

    mask = _date_mask(
        base_result.trades["session_date"],
        start=start,
        end=end,
    )
    signals = base_result.trades.loc[mask].copy().reset_index(drop=True)
    unknown_signal_dates = sorted(
        set(signals["session_date"].astype(str)).difference(set(sessions))
    )
    if unknown_signal_dates:
        raise ValueError(
            "EXP-011 signal dates are absent from the evaluation sessions: "
            + ", ".join(unknown_signal_dates[:5])
        )
    one_contract_risk = _one_contract_initial_risk(
        signals,
        symbol=expected_symbol,
    )

    if sizing_id == "fixed_one_nq":
        contracts = np.ones(len(signals), dtype=float)
    elif sizing_id == "fractional_nq_equal_risk":
        contracts = np.minimum(
            target_dollar_risk_usd / one_contract_risk,
            FRACTIONAL_NQ_CAP,
        )
    else:
        contracts = np.floor(
            target_dollar_risk_usd / one_contract_risk
        )
        contracts = np.clip(contracts, 0, INTEGER_MNQ_CAP)

    signals.insert(0, "sizing_id", sizing_id)
    signals.insert(
        0,
        "signal_candidate_id",
        base_result.candidate.candidate_id,
    )
    signals["target_dollar_risk_usd"] = target_dollar_risk_usd
    signals["one_contract_initial_risk_usd"] = one_contract_risk
    signals["contracts"] = contracts
    signals["skipped_zero_size"] = contracts <= 0
    signals["skip_reason"] = np.where(
        signals["skipped_zero_size"],
        "TARGET_RISK_BELOW_ONE_MNQ_CONTRACT",
        "",
    )
    signals["initial_risk_usd"] = one_contract_risk * contracts
    signals["gross_pnl_usd"] = (
        signals["gross_pnl_usd"].to_numpy(dtype=float) * contracts
    )
    signals["transaction_cost_usd"] = (
        signals["transaction_cost_usd"].to_numpy(dtype=float) * contracts
    )
    signals["net_pnl_usd"] = (
        signals["gross_pnl_usd"] - signals["transaction_cost_usd"]
    )

    trades = (
        signals.loc[~signals["skipped_zero_size"]]
        .copy()
        .reset_index(drop=True)
    )
    session_pnl = (
        trades.groupby("session_date")["net_pnl_usd"].sum()
        if not trades.empty
        else pd.Series(dtype=float)
    )
    pnl = sessions.map(session_pnl).fillna(0.0).to_numpy(dtype=float)
    cumulative = np.cumsum(pnl)
    peaks = np.maximum.accumulate(np.r_[0.0, cumulative])[1:]
    equity_curve = pd.DataFrame(
        {
            "session_date": sessions,
            "session_net_pnl_usd": pnl,
            "cumulative_net_profit_usd": cumulative,
            "equity_usd": REFERENCE_CAPITAL_USD + cumulative,
            "drawdown_usd": cumulative - peaks,
        }
    )

    if trades.empty:
        yearly = pd.DataFrame(
            columns=[
                "year",
                "completed_trades",
                "net_profit_usd",
                "profit_factor",
            ]
        )
        monthly = pd.DataFrame(
            columns=["month", "completed_trades", "net_profit_usd"]
        )
    else:
        local = trades.assign(
            year=pd.to_datetime(trades["session_date"]).dt.year,
            month=pd.to_datetime(trades["session_date"])
            .dt.to_period("M")
            .astype(str),
        )
        yearly = (
            local.groupby("year", as_index=False)
            .agg(
                completed_trades=("net_pnl_usd", "size"),
                net_profit_usd=("net_pnl_usd", "sum"),
            )
            .sort_values("year")
        )
        yearly["profit_factor"] = yearly["year"].map(
            {
                int(year): profit_factor(
                    local.loc[
                        local["year"].eq(year), "net_pnl_usd"
                    ].to_numpy(dtype=float)
                )
                for year in yearly["year"]
            }
        )
        monthly = (
            local.groupby("month", as_index=False)
            .agg(
                completed_trades=("net_pnl_usd", "size"),
                net_profit_usd=("net_pnl_usd", "sum"),
            )
            .sort_values("month")
        )

    summary = _summary(
        signal_candidate_id=base_result.candidate.candidate_id,
        sizing_id=sizing_id,
        symbol=expected_symbol,
        target_dollar_risk_usd=float(target_dollar_risk_usd),
        signals=signals,
        trades=trades,
        evaluation_session_count=len(sessions),
    )
    return Exp011SizedResult(
        signal_candidate_id=base_result.candidate.candidate_id,
        sizing_id=sizing_id,
        symbol=expected_symbol,
        target_dollar_risk_usd=float(target_dollar_risk_usd),
        summary=summary,
        signals=signals,
        trades=trades,
        equity_curve=equity_curve,
        yearly_results=yearly.reset_index(drop=True),
        monthly_results=monthly.reset_index(drop=True),
    )
