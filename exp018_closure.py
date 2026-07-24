from __future__ import annotations

from copy import deepcopy


EXP018_CLOSURE = {'schema_version': 1,
 'experiment_id': 'EXP-018',
 'closed_date': '2026-07-24',
 'research_status': 'REVIEW',
 'classification': 'QUALIFIED_AS_ACCESSIBLE_EXACT_CONTRACT_SOURCE',
 'source': {'vendor': 'Databento',
            'dataset': 'GLBX.MDP3',
            'schema': 'ohlcv-1m',
            'market': 'Exact quarterly NQ futures contracts'},
 'request_result': {'initial_windows_measured': 6,
                    'repeatability_windows_measured': 2,
                    'successful_bar_requests': 8,
                    'automatic_retries': 0,
                    'total_estimated_cost_usd': 0.36695495247699994},
 'coverage': {'minimum_regular_trade_minute_coverage': 1.0,
              'minimum_extended_trade_minute_coverage': 0.9991869918699187,
              'required_regular_trade_minute_coverage': 0.999,
              'required_extended_trade_minute_coverage': 0.995},
 'structural_quality': {'identity_mismatch_rows': 0,
                        'duplicate_timestamp_rows': 0,
                        'duplicate_full_rows': 0,
                        'invalid_ohlc_rows': 0,
                        'negative_volume_rows': 0,
                        'nonfinite_ohlcv_rows': 0,
                        'off_tick_ohlc_values': 0},
 'repeatability': [{'window_id': 'nqh25_march_dst',
                    'delay_hours': 48.39434066611111,
                    'minimum_delay_met': True,
                    'canonical_hash_match': True,
                    'row_count_match': True,
                    'timestamp_set_match': True,
                    'raw_hash_match': True},
                   {'window_id': 'nqz24_thanksgiving',
                    'delay_hours': 48.39816502222222,
                    'minimum_delay_met': True,
                    'canonical_hash_match': True,
                    'row_count_match': True,
                    'timestamp_set_match': True,
                    'raw_hash_match': True}],
 'audit_provenance': {'audit_created_at_utc': '2026-07-24T12:01:03.925929+00:00',
                      'audit_git_commit': 'dae198f57ba311c8030700b380e5e14df967a6f0',
                      'working_tree_clean_during_audit': True},
 'interpretation': {'accessible_exact_contract_source_qualified': True,
                    'exchange_accuracy_verified': False,
                    'best_vendor_selected': False,
                    'full_history_downloaded': False,
                    'continuous_series_constructed': False,
                    'strategy_run': False,
                    'prior_experiments_changed': False,
                    'paper_trading_authorized': False,
                    'live_trading_authorized': False}}


def get_exp018_closure():
    return deepcopy(EXP018_CLOSURE)


def validate_exp018_closure(record=None):
    r = EXP018_CLOSURE if record is None else record

    if (
        r["experiment_id"] != "EXP-018"
        or r["research_status"] != "REVIEW"
        or r["classification"]
        != "QUALIFIED_AS_ACCESSIBLE_EXACT_CONTRACT_SOURCE"
    ):
        raise ValueError("EXP-018 closure identity changed.")

    requests = r["request_result"]

    if (
        requests["initial_windows_measured"] != 6
        or requests["repeatability_windows_measured"] != 2
        or requests["successful_bar_requests"] != 8
        or requests["automatic_retries"] != 0
        or requests["total_estimated_cost_usd"] != 0.36695495247699994
    ):
        raise ValueError("EXP-018 request result changed.")

    coverage = r["coverage"]

    if (
        coverage["minimum_regular_trade_minute_coverage"]
        < coverage["required_regular_trade_minute_coverage"]
        or coverage["minimum_extended_trade_minute_coverage"]
        < coverage["required_extended_trade_minute_coverage"]
    ):
        raise ValueError("EXP-018 coverage result changed.")

    quality = r["structural_quality"]

    if any(int(value) != 0 for value in quality.values()):
        raise ValueError("EXP-018 structural quality changed.")

    repeats = r["repeatability"]

    if len(repeats) != 2:
        raise ValueError("EXP-018 repeatability changed.")

    expected_ids = {
        "nqz24_thanksgiving",
        "nqh25_march_dst",
    }

    if {
        item["window_id"]
        for item in repeats
    } != expected_ids:
        raise ValueError("EXP-018 repeatability changed.")

    for item in repeats:
        if (
            item["delay_hours"] < 24.0
            or item["minimum_delay_met"] is not True
            or item["canonical_hash_match"] is not True
            or item["row_count_match"] is not True
            or item["timestamp_set_match"] is not True
        ):
            raise ValueError("EXP-018 repeatability changed.")

    interpretation = r["interpretation"]

    if (
        interpretation[
            "accessible_exact_contract_source_qualified"
        ]
        is not True
        or interpretation["exchange_accuracy_verified"]
        is not False
        or interpretation["best_vendor_selected"]
        is not False
        or interpretation["full_history_downloaded"]
        is not False
        or interpretation["continuous_series_constructed"]
        is not False
        or interpretation["strategy_run"]
        is not False
        or interpretation["prior_experiments_changed"]
        is not False
        or interpretation["paper_trading_authorized"]
        is not False
        or interpretation["live_trading_authorized"]
        is not False
    ):
        raise ValueError("EXP-018 interpretation changed.")
