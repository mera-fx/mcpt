from __future__ import annotations

import numpy as np
import pandas as pd

from exp009_engine import Exp009Result, get_exp009_candidate
from exp011_sizing import (
    Exp011Calibration,
    Exp011SizedResult,
    apply_locked_sizing,
)


EVALUATION_SESSIONS = np.array(
    [
        "2021-01-04",
        "2021-01-05",
        "2021-01-06",
        "2021-01-07",
        "2021-01-08",
    ]
)


def make_base_result(
    *,
    signal_id: str = "opening_drive_0p5_time",
    symbol: str = "NQ",
    pnl_multiplier: float = 1.0,
) -> Exp009Result:
    if symbol == "NQ":
        cost = 15.0
        risk_points = [50.0, 100.0, 75.0, 25.0, 75.0, 150.0, 200.0]
        gross = [
            200.0,
            -100.0,
            300.0,
            1_000.0,
            -500.0,
            2_000.0,
            -1_000.0,
        ]
    else:
        cost = 3.0
        risk_points = [50.0, 100.0, 75.0, 25.0, 75.0, 150.0, 1_000.0]
        gross = [
            20.0,
            -10.0,
            30.0,
            100.0,
            -50.0,
            200.0,
            -100.0,
        ]
    dates = [
        "2020-01-02",
        "2020-06-01",
        "2020-12-15",
        "2021-01-04",
        "2021-01-05",
        "2021-01-06",
        "2021-01-07",
    ]
    gross_array = np.asarray(gross, dtype=float) * pnl_multiplier
    trades = pd.DataFrame(
        {
            "candidate_id": signal_id,
            "family_id": "opening_drive_continuation",
            "symbol": symbol,
            "session_date": dates,
            "year": pd.to_datetime(dates).year,
            "direction": ["long"] * len(dates),
            "signal_five_minute_slot": [5] * len(dates),
            "entry_minute_slot": [30] * len(dates),
            "exit_minute_slot": [100] * len(dates),
            "holding_minutes": [70] * len(dates),
            "entry_price": [100.0] * len(dates),
            "stop_price": (
                100.0 - np.asarray(risk_points, dtype=float)
            ),
            "target_price": [np.nan] * len(dates),
            "exit_price": [101.0] * len(dates),
            "risk_points": risk_points,
            "gross_pnl_usd": gross_array,
            "transaction_cost_usd": [cost] * len(dates),
            "net_pnl_usd": gross_array - cost,
            "exit_reason": ["time_exit"] * len(dates),
        }
    )
    return Exp009Result(
        candidate=get_exp009_candidate(signal_id),
        symbol=symbol,
        summary={},
        trades=trades,
        equity_curve=pd.DataFrame(),
        yearly_results=pd.DataFrame(),
    )


def make_calibration() -> Exp011Calibration:
    return Exp011Calibration(
        signal_candidate_id="opening_drive_0p5_time",
        market="NQ",
        calibration_start="2019-05-06",
        calibration_end="2020-12-31",
        trade_count=3,
        target_dollar_risk_usd=1515.0,
        median_one_contract_risk_usd=1515.0,
        minimum_one_contract_risk_usd=1015.0,
        maximum_one_contract_risk_usd=2015.0,
    )


def make_sized_results() -> dict[tuple[str, str], Exp011SizedResult]:
    target = make_calibration().target_dollar_risk_usd
    results: dict[tuple[str, str], Exp011SizedResult] = {}
    for signal_id, multiplier in (
        ("opening_drive_0p5_time", 1.0),
        ("opening_drive_0p5_1p5r", 0.8),
    ):
        nq = make_base_result(
            signal_id=signal_id,
            symbol="NQ",
            pnl_multiplier=multiplier,
        )
        mnq = make_base_result(
            signal_id=signal_id,
            symbol="MNQ",
            pnl_multiplier=multiplier,
        )
        for sizing_id, base in (
            ("fixed_one_nq", nq),
            ("fractional_nq_equal_risk", nq),
            ("integer_mnq_equal_risk", mnq),
        ):
            results[(signal_id, sizing_id)] = apply_locked_sizing(
                base,
                sizing_id=sizing_id,
                target_dollar_risk_usd=target,
                evaluation_session_dates=EVALUATION_SESSIONS,
            )
    return results
