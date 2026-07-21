from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from exp014_preregistration import (
    FINALIST_IDS,
    PAIR_DEFINITIONS,
    validate_exp014_preregistration,
)


PROJECT_DIR = Path(__file__).resolve().parent
RESULT_DIR = (
    PROJECT_DIR / "results" / "EXP-014" / "finalist_behaviour"
)
REPORT_DIR = PROJECT_DIR / "reports" / "EXP-014-research-lab"

STUDY_FILE = RESULT_DIR / "study_result.json"
STANDALONE_FILE = RESULT_DIR / "standalone_measurements.csv"
PERIOD_FILE = RESULT_DIR / "period_comparison.csv"
BEHAVIOUR_FILE = RESULT_DIR / "behaviour_breakdowns.csv"
CONCENTRATION_FILE = RESULT_DIR / "concentration_measurements.csv"
DRAWDOWN_FILE = RESULT_DIR / "drawdown_diagnostics.csv"
MONTHLY_FILE = RESULT_DIR / "monthly_measurements.csv"
OVERLAP_FILE = RESULT_DIR / "overlap_measurements.csv"
PAIR_SESSION_FILE = RESULT_DIR / "pair_session_pnl.csv"
REGIME_FILE = RESULT_DIR / "regime_context.csv"
ROLLING_FILE = RESULT_DIR / "rolling_measurements.csv"
SESSION_FILE = RESULT_DIR / "session_pnl.csv"
PAIR_FILE = RESULT_DIR / "sleeve_pair_measurements.csv"
REPORT_FILE = REPORT_DIR / "report.html"

LEDGER_FILES: dict[str, Path] = {
    "gap_fade_0p50_1r": (
        RESULT_DIR
        / "candidates"
        / "gap_fade_0p50_1r"
        / "nq_enriched_trades.csv"
    ),
    "premarket_continuation_0p50_time": (
        RESULT_DIR
        / "candidates"
        / "premarket_continuation_0p50_time"
        / "nq_enriched_trades.csv"
    ),
    "premarket_continuation_0p75_time": (
        RESULT_DIR
        / "candidates"
        / "premarket_continuation_0p75_time"
        / "nq_enriched_trades.csv"
    ),
}

EXPECTED_IMPLEMENTATION_COMMIT = (
    "f56c1e0137b3c902cc0c25d8c29e7a01a13b62b2"
)

EXPECTED_CANONICAL_SHA256: dict[str, str] = {
    "study_result": (
        "7c888e5a9f9ede8640702700dabbdbab0010153dda01af2fe9d9a778ab02c5fb"
    ),
    "standalone": (
        "08489fa092fdadd8252ed9a0d44f9ce32e1432f1200816cad920730d7679c5c5"
    ),
    "period": (
        "4cd5a94888cf818a92983ae4c985a34c4d3e930af9421d3232f157513983a84c"
    ),
    "behaviour": (
        "eeb6b7cb3f3f2b1f446b9bcf6f1e6c83a57b271a75d70ab6d85a1d57dc9e3e25"
    ),
    "concentration": (
        "720595ff43ac17f2fa51cdc22e55b8a0772e16b9c5b453f02d0105700dbb430f"
    ),
    "drawdown": (
        "aea55cbf0be878f7507129cfa9526805a1e9293f770e810a8f1f789dfa7a3935"
    ),
    "monthly": (
        "9a70bc90b9a62b9d50a220db5a755301c81d91728a74d8ca188547b5c766eabc"
    ),
    "overlap": (
        "3bf39381339140116ea35144860dd1ea2cf5cdd93ca321528d04febc0ae84e17"
    ),
    "pair_session": (
        "d8279cc8f41557cdf4f11012d878266abbe6bee5c2f63c22f05e541823b20e85"
    ),
    "regime": (
        "165d6161dfbcefceda6cb561faf702635d8e49fa8c3b0545ba51c3836817eaf2"
    ),
    "rolling": (
        "d63fb4689b2dcc17076a21b86c10a4d66e9583f051304ed21d5cb9f887689aab"
    ),
    "session": (
        "0e600b8cba7c49f3fc14f0bf91642289c3e17a1fac4738f720822a9b1412ffef"
    ),
    "pairs": (
        "e220e28b98a8df2082194a9dfacfae54a1e8d597761c1d3a83eaa8148d7eea19"
    ),
    "ledger_gap_fade_0p50_1r": (
        "67cc5efc71c07cf90dab86ae66ae56cf1d3217d960d7f5532b6946055beb8a1a"
    ),
    "ledger_premarket_continuation_0p50_time": (
        "b6a02559f66545181880b0c54aef00ed608b907f566bd87db06aa2e6dc8fe474"
    ),
    "ledger_premarket_continuation_0p75_time": (
        "f20565e12e7c914f37239a21649ceb40c03f6e22672dcfa460ed41d8f55155ac"
    ),
}

EXPECTED_REPORT_ASSETS: tuple[str, ...] = (
    "annual_comparison.png",
    "context_strength.png",
    "direction_exit.png",
    "entry_exit_time.png",
    "holding_time.png",
    "mfe_mae.png",
    "monthly_heatmaps.png",
    "overlap_detail.png",
    "overlap_matrix.png",
    "period_comparison.png",
    "pnl_correlation.png",
    "profit_concentration.png",
    "regime_heatmaps.png",
    "rolling_trade_behaviour.png",
    "sleeve_pair_drawdown.png",
    "sleeve_pair_equity.png",
    "standalone_drawdown.png",
    "standalone_equity_vs_benchmark.png",
)


def _normalize_scalar(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer, int)) and not isinstance(value, bool):
        return int(value)
    if isinstance(value, (np.floating, float)):
        numeric = float(value)
        if math.isnan(numeric):
            return None
        if math.isinf(numeric):
            return "Infinity" if numeric > 0.0 else "-Infinity"
        return numeric
    return value


def _normalize_object(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _normalize_object(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_normalize_object(item) for item in value]
    return _normalize_scalar(value)


def canonical_object_sha256(value: Any) -> str:
    encoded = json.dumps(
        _normalize_object(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def canonical_dataframe_sha256(frame: pd.DataFrame) -> str:
    records = [
        {
            str(key): _normalize_scalar(value)
            for key, value in row.items()
        }
        for row in frame.to_dict(orient="records")
    ]
    return canonical_object_sha256(records)


def load_json_object(path: Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def load_study_result(path: Path = STUDY_FILE) -> dict[str, Any]:
    return load_json_object(path)


def _load_csv(path: Path, sort_columns: list[str]) -> pd.DataFrame:
    return pd.read_csv(path).sort_values(
        sort_columns,
        kind="stable",
    ).reset_index(drop=True)


def load_standalone_measurements(
    path: Path = STANDALONE_FILE,
) -> pd.DataFrame:
    return _load_csv(path, ["candidate_id"])


def load_period_comparison(path: Path = PERIOD_FILE) -> pd.DataFrame:
    return _load_csv(path, ["candidate_id", "period"])


def load_behaviour_breakdowns(
    path: Path = BEHAVIOUR_FILE,
) -> pd.DataFrame:
    return _load_csv(path, ["candidate_id", "dimension", "value"])


def load_concentration_measurements(
    path: Path = CONCENTRATION_FILE,
) -> pd.DataFrame:
    return _load_csv(path, ["candidate_id"])


def load_drawdown_diagnostics(
    path: Path = DRAWDOWN_FILE,
) -> pd.DataFrame:
    return _load_csv(path, ["series_type", "series_id"])


def load_monthly_measurements(
    path: Path = MONTHLY_FILE,
) -> pd.DataFrame:
    return _load_csv(path, ["candidate_id", "month"])


def load_overlap_measurements(
    path: Path = OVERLAP_FILE,
) -> pd.DataFrame:
    return _load_csv(
        path,
        ["left_candidate_id", "right_candidate_id"],
    )


def load_pair_session_pnl(
    path: Path = PAIR_SESSION_FILE,
) -> pd.DataFrame:
    return _load_csv(path, ["session_date"])


def load_regime_context(path: Path = REGIME_FILE) -> pd.DataFrame:
    return _load_csv(path, ["session_date"])


def load_rolling_measurements(
    path: Path = ROLLING_FILE,
) -> pd.DataFrame:
    return _load_csv(
        path,
        [
            "candidate_id",
            "window_trades",
            "window_end_trade_number",
        ],
    )


def load_session_pnl(path: Path = SESSION_FILE) -> pd.DataFrame:
    return _load_csv(path, ["session_date"])


def load_sleeve_pair_measurements(
    path: Path = PAIR_FILE,
) -> pd.DataFrame:
    return _load_csv(path, ["pair_id"])


def load_enriched_ledger(candidate_id: str) -> pd.DataFrame:
    if candidate_id not in LEDGER_FILES:
        raise KeyError(f"Unknown EXP-014 finalist: {candidate_id}")
    return _load_csv(
        LEDGER_FILES[candidate_id],
        ["candidate_trade_number"],
    )


def _assert_close(actual: Any, expected: float, *, label: str) -> None:
    if not np.isclose(float(actual), expected, atol=1e-12, rtol=0.0):
        raise ValueError(
            f"EXP-014 {label} changed: expected {expected}, got {actual}."
        )


def _validate_result_identity(record: dict[str, Any]) -> None:
    if (
        record.get("schema_version") != 1
        or record.get("experiment_id") != "EXP-014"
        or record.get("result_status") != "MEASURED_BEHAVIOUR_REVIEW"
    ):
        raise ValueError("EXP-014 result identity changed.")

    git = record["git"]
    if (
        git["commit"] != EXPECTED_IMPLEMENTATION_COMMIT
        or git["short_commit"] != "f56c1e0"
        or git["working_tree_clean"] is not True
    ):
        raise ValueError("EXP-014 implementation provenance changed.")

    data = record["data"]
    if (
        data["source_experiment"] != "EXP-012"
        or data["included_sessions"] != 1331
        or data["historical_start"] != "2020-01-03"
        or data["historical_end"] != "2025-12-31"
        or data["new_data_cleaning_decisions"] != 0
    ):
        raise ValueError("EXP-014 frozen data evidence changed.")


def _validate_reconstruction_and_context(record: dict[str, Any]) -> None:
    reconstruction = record["reconstruction"]
    if (
        reconstruction["source_experiment"] != "EXP-013"
        or reconstruction["candidate_count"] != 3
        or tuple(reconstruction["candidate_ids"]) != FINALIST_IDS
        or reconstruction["all_candidates_match"] is not True
        or any(
            reconstruction[field]
            for field in (
                "strategy_rules_changed",
                "parameters_changed",
                "costs_changed",
                "position_sizing_changed",
            )
        )
    ):
        raise ValueError("EXP-014 finalist reconstruction changed.")

    context = record["exp013_context"]
    if (
        context["classification"] != "STRONG_HISTORICAL_EVIDENCE"
        or context["walk_forward_profitable_folds"] != 3
        or context["walk_forward_total_folds"] != 4
        or context["mcpt_candidate_count"] != 24
        or context["bootstrap_resamples_per_finalist"] != 10000
        or context["bootstrap_candidate_count"] != 3
        or context["reused_not_rerun"] is not True
    ):
        raise ValueError("EXP-014 frozen EXP-013 context changed.")
    _assert_close(
        context["walk_forward_net_profit_usd"],
        26295.0,
        label="EXP-013 walk-forward context",
    )
    _assert_close(
        context["discovery_wide_mcpt_p_value"],
        4 / 1001,
        label="EXP-013 discovery-wide MCPT context",
    )

    regime = record["regime_context"]
    if (
        regime["calibration_start"] != "2020-01-03"
        or regime["calibration_end"] != "2021-12-31"
        or regime["current_session_excluded"] is not True
        or regime["diagnostic_not_filter"] is not True
    ):
        raise ValueError("EXP-014 entry-known regime boundary changed.")
    _assert_close(
        regime["volatility_boundary"],
        0.013417071790747564,
        label="volatility regime boundary",
    )


def _validate_standalone_measurements(
    standalone: pd.DataFrame,
    period: pd.DataFrame,
) -> None:
    expected = {
        "gap_fade_0p50_1r": {
            "completed_trades": 186,
            "trade_profit_factor": 1.530923511019599,
            "net_profit_usd": 34810.0,
            "maximum_drawdown_usd": -5080.0,
            "profitable_years": 6,
            "low_sample": False,
        },
        "premarket_continuation_0p50_time": {
            "completed_trades": 291,
            "trade_profit_factor": 1.7363738499377523,
            "net_profit_usd": 121255.0,
            "maximum_drawdown_usd": -20695.0,
            "profitable_years": 5,
            "low_sample": False,
        },
        "premarket_continuation_0p75_time": {
            "completed_trades": 88,
            "trade_profit_factor": 2.0237378415933303,
            "net_profit_usd": 44205.0,
            "maximum_drawdown_usd": -5540.0,
            "profitable_years": 5,
            "low_sample": True,
        },
    }
    if (
        len(standalone) != 3
        or standalone["candidate_id"].nunique() != 3
        or set(standalone["candidate_id"]) != set(FINALIST_IDS)
        or not bool(standalone["reconstruction_match"].all())
        or bool(standalone["strategy_rules_changed"].any())
    ):
        raise ValueError("EXP-014 standalone finalist set changed.")

    indexed = standalone.set_index("candidate_id")
    for candidate_id, fields in expected.items():
        row = indexed.loc[candidate_id]
        for field, expected_value in fields.items():
            actual = row[field]
            if isinstance(expected_value, bool):
                if bool(actual) is not expected_value:
                    raise ValueError(
                        f"EXP-014 {candidate_id} {field} changed."
                    )
            elif isinstance(expected_value, int):
                if int(actual) != expected_value:
                    raise ValueError(
                        f"EXP-014 {candidate_id} {field} changed."
                    )
            else:
                _assert_close(
                    actual,
                    expected_value,
                    label=f"{candidate_id} {field}",
                )

    if (
        len(period) != 9
        or set(period["period"]) != {"2020-2024", "2022-2024", "2025"}
        or set(period["candidate_id"]) != set(FINALIST_IDS)
    ):
        raise ValueError("EXP-014 period comparison changed.")

    expected_2025 = {
        "gap_fade_0p50_1r": (38, 6070.0, 1.3358229598893498),
        "premarket_continuation_0p50_time": (
            44,
            9635.0,
            1.263972602739726,
        ),
        "premarket_continuation_0p75_time": (
            10,
            -2890.0,
            0.5250616269515201,
        ),
    }
    rows_2025 = period[period["period"] == "2025"].set_index(
        "candidate_id"
    )
    for candidate_id, (
        expected_trades,
        expected_net,
        expected_pf,
    ) in expected_2025.items():
        row = rows_2025.loc[candidate_id]
        if int(row["completed_trades"]) != expected_trades:
            raise ValueError(
                f"EXP-014 {candidate_id} 2025 trade count changed."
            )
        _assert_close(
            row["net_profit_usd"],
            expected_net,
            label=f"{candidate_id} 2025 net profit",
        )
        _assert_close(
            row["profit_factor"],
            expected_pf,
            label=f"{candidate_id} 2025 Profit Factor",
        )


def _validate_overlap_and_pairs(
    overlap: pd.DataFrame,
    pairs: pd.DataFrame,
) -> None:
    if len(overlap) != 3:
        raise ValueError("EXP-014 pairwise overlap row count changed.")

    overlap_index = overlap.set_index(
        ["left_candidate_id", "right_candidate_id"]
    )
    expected_overlap = {
        (
            "gap_fade_0p50_1r",
            "premarket_continuation_0p50_time",
        ): (15, 0, 0.041024767940562035),
        (
            "gap_fade_0p50_1r",
            "premarket_continuation_0p75_time",
        ): (6, 0, 0.02053197807929911),
        (
            "premarket_continuation_0p50_time",
            "premarket_continuation_0p75_time",
        ): (88, 0, 0.49094361769678574),
    }
    for key, (
        expected_sessions,
        expected_opposite,
        expected_correlation,
    ) in expected_overlap.items():
        row = overlap_index.loc[key]
        if (
            int(row["overlap_sessions"]) != expected_sessions
            or int(row["opposite_direction_overlap"])
            != expected_opposite
        ):
            raise ValueError(f"EXP-014 overlap counts changed for {key}.")
        _assert_close(
            row["all_session_pnl_correlation"],
            expected_correlation,
            label=f"{key} all-session P&L correlation",
        )

    expected_pairs = {
        "gap_fade_plus_premarket_0p50": {
            "net_profit_usd": 156065.0,
            "maximum_drawdown_usd": -23365.0,
            "net_profit_to_drawdown": 6.679435052428847,
            "profitable_years": 5,
            "total_years": 6,
            "worst_year_usd": -1915.0,
        },
        "gap_fade_plus_premarket_0p75": {
            "net_profit_usd": 79015.0,
            "maximum_drawdown_usd": -8045.0,
            "net_profit_to_drawdown": 9.821628340584214,
            "profitable_years": 6,
            "total_years": 6,
            "worst_year_usd": 1750.0,
        },
    }
    expected_pair_ids = {
        str(item["pair_id"]) for item in PAIR_DEFINITIONS
    }
    if (
        len(pairs) != 2
        or set(pairs["pair_id"]) != expected_pair_ids
        or not bool(
            pairs["diagnostic_not_executable_portfolio"].all()
        )
        or int(pairs["maximum_gross_contracts"].max()) != 2
    ):
        raise ValueError("EXP-014 fixed research sleeve pairs changed.")

    pair_index = pairs.set_index("pair_id")
    for pair_id, fields in expected_pairs.items():
        row = pair_index.loc[pair_id]
        for field, expected_value in fields.items():
            actual = row[field]
            if isinstance(expected_value, int):
                if int(actual) != expected_value:
                    raise ValueError(
                        f"EXP-014 {pair_id} {field} changed."
                    )
            else:
                _assert_close(
                    actual,
                    expected_value,
                    label=f"{pair_id} {field}",
                )


def _validate_supporting_shapes(
    *,
    behaviour: pd.DataFrame,
    concentration: pd.DataFrame,
    drawdown: pd.DataFrame,
    monthly: pd.DataFrame,
    pair_session: pd.DataFrame,
    regime: pd.DataFrame,
    rolling: pd.DataFrame,
    session: pd.DataFrame,
) -> None:
    if (
        len(behaviour) != 242
        or set(behaviour["candidate_id"]) != set(FINALIST_IDS)
        or len(concentration) != 3
        or set(concentration["candidate_id"]) != set(FINALIST_IDS)
        or len(drawdown) != 5
        or set(drawdown["series_type"])
        != {"standalone", "research_sleeve_pair"}
        or len(monthly) != 216
        or set(monthly["candidate_id"]) != set(FINALIST_IDS)
        or len(pair_session) != 1331
        or len(regime) != 1331
        or len(rolling) != 926
        or set(rolling["window_trades"]) != {20, 50}
        or len(session) != 1331
    ):
        raise ValueError("EXP-014 supporting measurement shape changed.")

    if (
        not pair_session["session_date"].equals(session["session_date"])
        or not regime["session_date"].equals(session["session_date"])
    ):
        raise ValueError("EXP-014 complete session axis changed.")

    expected_ledger_counts = {
        "gap_fade_0p50_1r": 186,
        "premarket_continuation_0p50_time": 291,
        "premarket_continuation_0p75_time": 88,
    }
    for candidate_id, expected_count in expected_ledger_counts.items():
        ledger = load_enriched_ledger(candidate_id)
        if (
            len(ledger) != expected_count
            or set(ledger["candidate_id"]) != {candidate_id}
            or list(ledger["candidate_trade_number"])
            != list(range(1, expected_count + 1))
        ):
            raise ValueError(
                f"EXP-014 enriched ledger changed for {candidate_id}."
            )


def _validate_interpretation(record: dict[str, Any]) -> None:
    interpretation = record["interpretation"]
    required_true = (
        "measurement_first",
        "no_pass_fail_gates",
        "no_composite_score",
        "no_automatic_winner",
        "no_strategy_parameter_selection",
        "no_regime_filter_selection",
        "arithmetic_pairs_not_executable_portfolios",
    )
    if (
        any(interpretation[field] is not True for field in required_true)
        or interpretation["expected_lifecycle_after_measurement"]
        != "REVIEW"
        or interpretation["independent_confirmation"] is not False
        or interpretation["paper_trading_authorized"] is not False
        or interpretation["live_trading_authorized"] is not False
        or record["automatic_lifecycle_source_edit"] is not False
    ):
        raise ValueError("EXP-014 research boundary changed.")


def _calculated_hashes(
    *,
    record: dict[str, Any],
    standalone: pd.DataFrame,
    period: pd.DataFrame,
    behaviour: pd.DataFrame,
    concentration: pd.DataFrame,
    drawdown: pd.DataFrame,
    monthly: pd.DataFrame,
    overlap: pd.DataFrame,
    pair_session: pd.DataFrame,
    regime: pd.DataFrame,
    rolling: pd.DataFrame,
    session: pd.DataFrame,
    pairs: pd.DataFrame,
) -> dict[str, str]:
    hashes = {
        "study_result": canonical_object_sha256(record),
        "standalone": canonical_dataframe_sha256(standalone),
        "period": canonical_dataframe_sha256(period),
        "behaviour": canonical_dataframe_sha256(behaviour),
        "concentration": canonical_dataframe_sha256(concentration),
        "drawdown": canonical_dataframe_sha256(drawdown),
        "monthly": canonical_dataframe_sha256(monthly),
        "overlap": canonical_dataframe_sha256(overlap),
        "pair_session": canonical_dataframe_sha256(pair_session),
        "regime": canonical_dataframe_sha256(regime),
        "rolling": canonical_dataframe_sha256(rolling),
        "session": canonical_dataframe_sha256(session),
        "pairs": canonical_dataframe_sha256(pairs),
    }
    for candidate_id in FINALIST_IDS:
        hashes[f"ledger_{candidate_id}"] = canonical_dataframe_sha256(
            load_enriched_ledger(candidate_id)
        )
    return hashes


def _validate_report_assets() -> None:
    if not REPORT_FILE.is_file():
        raise ValueError("EXP-014 report.html is missing.")
    missing = [
        name
        for name in EXPECTED_REPORT_ASSETS
        if not (REPORT_DIR / name).is_file()
    ]
    if missing:
        raise ValueError(
            "EXP-014 report assets are missing: "
            + ", ".join(sorted(missing))
        )


def validate_exp014_behaviour_result(
    *,
    record: dict[str, Any],
    standalone: pd.DataFrame,
    period: pd.DataFrame,
    behaviour: pd.DataFrame,
    concentration: pd.DataFrame,
    drawdown: pd.DataFrame,
    monthly: pd.DataFrame,
    overlap: pd.DataFrame,
    pair_session: pd.DataFrame,
    regime: pd.DataFrame,
    rolling: pd.DataFrame,
    session: pd.DataFrame,
    pairs: pd.DataFrame,
    verify_hashes: bool = True,
    verify_report: bool = True,
) -> None:
    validate_exp014_preregistration()
    _validate_result_identity(record)
    _validate_reconstruction_and_context(record)
    _validate_standalone_measurements(standalone, period)
    _validate_overlap_and_pairs(overlap, pairs)
    _validate_supporting_shapes(
        behaviour=behaviour,
        concentration=concentration,
        drawdown=drawdown,
        monthly=monthly,
        pair_session=pair_session,
        regime=regime,
        rolling=rolling,
        session=session,
    )
    _validate_interpretation(record)

    if verify_report:
        _validate_report_assets()

    if verify_hashes:
        actual = _calculated_hashes(
            record=record,
            standalone=standalone,
            period=period,
            behaviour=behaviour,
            concentration=concentration,
            drawdown=drawdown,
            monthly=monthly,
            overlap=overlap,
            pair_session=pair_session,
            regime=regime,
            rolling=rolling,
            session=session,
            pairs=pairs,
        )
        if actual != EXPECTED_CANONICAL_SHA256:
            changed = sorted(
                key
                for key in EXPECTED_CANONICAL_SHA256
                if actual.get(key) != EXPECTED_CANONICAL_SHA256[key]
            )
            raise ValueError(
                "EXP-014 frozen result hashes changed: "
                + ", ".join(changed)
            )


def verify_local_exp014_behaviour_result() -> dict[str, Any]:
    record = load_study_result()
    validate_exp014_behaviour_result(
        record=record,
        standalone=load_standalone_measurements(),
        period=load_period_comparison(),
        behaviour=load_behaviour_breakdowns(),
        concentration=load_concentration_measurements(),
        drawdown=load_drawdown_diagnostics(),
        monthly=load_monthly_measurements(),
        overlap=load_overlap_measurements(),
        pair_session=load_pair_session_pnl(),
        regime=load_regime_context(),
        rolling=load_rolling_measurements(),
        session=load_session_pnl(),
        pairs=load_sleeve_pair_measurements(),
    )
    return deepcopy(record)


if __name__ == "__main__":
    result = verify_local_exp014_behaviour_result()
    print("EXP-014 finalist behaviour result is frozen and valid.")
    print(
        "Implementation commit:",
        result["git"]["commit"],
    )
    print(
        "Lifecycle:",
        result["interpretation"][
            "expected_lifecycle_after_measurement"
        ],
    )
    print("No paper or live trading is authorized.")
