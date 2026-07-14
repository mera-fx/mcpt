from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parent
TRACKED_RESULT_FILE = PROJECT_DIR / "research" / "EXP-005_full_validation_result.json"
LOCAL_DECISION_FILE = (
    PROJECT_DIR / "results" / "EXP-005" / "full_validation"
    / "full_validation_decision.json"
)
EXPECTED_FILE_SHA256 = "7d2a3d1eb8716851fc913482c55809c360959b7a5d9eb3e474389b21131b6987"
EXPECTED_RESULT: dict[str, Any] = {'schema_version': 1,
 'experiment_id': 'EXP-005',
 'stage': 'FULL_VALIDATION',
 'calculated_at_utc': '2026-07-14T14:59:18+00:00',
 'git': {'commit': '1dc8b32f2eba1b19e19d3162d5f0acd2f820593e',
         'short_commit': '1dc8b32',
         'working_tree_clean': True},
 'data': {'confirmation_import_audit': 'C:\\Users\\hocke\\Documents\\mcpt\\results\\EXP-005\\confirmation_data\\quantower_confirmation_import_audit.json',
          'confirmation_import_commit': '53a740aedb63e2a7508e3e010f5370be49cf816a',
          'included_sessions': 733,
          'included_invalid_sessions': 0,
          'included_roll_switch_sessions': 0,
          'provider_unavailable_sessions_excluded': 2,
          'provider_complete_sessions_restored': 1,
          'potential_front_month_mismatch_sessions_excluded': 9,
          'fingerprints': {'NQ_1m': 'd91cf3123e0edea67dcb2a89fb2baf2c27d1e76f091d9bc2aeb4b34e61e92cd1',
                           'MNQ_1m': 'f08ee6b3e5f9d9243077cecd4b32229136dc74fabe6b9e9d75c110362a4c23f7',
                           'NQ_5m': '4a50a121b79fe50cd8b3042e7b2e88472908689b89880f2da56374fba5d4a340',
                           'MNQ_5m': 'a10db6f4112bf467f18dbd3de7f1b334a08c0f6f971bb7bec4e3edd3d083c51a'}},
 'fixed_rules': {'opening_range_minutes': 15,
                 'direction_mode': 'both',
                 'parameter_combinations': 1,
                 'optimization': False},
 'results': {'NQ': {'symbol': 'NQ',
                    'included_sessions': 733,
                    'completed_trades': 724,
                    'long_trades': 367,
                    'short_trades': 357,
                    'gross_pnl_usd': 127575.0,
                    'transaction_costs_usd': 10860.0,
                    'net_profit_usd': 116715.0,
                    'gross_profit_usd': 761100.0,
                    'gross_loss_usd': 644385.0,
                    'trade_profit_factor': 1.1811261900882237,
                    'win_rate_percent': 43.370165745856355,
                    'average_trade_usd': 161.2085635359116,
                    'median_trade_usd': -667.5,
                    'maximum_drawdown_usd': -36175.0,
                    'slippage_ticks_per_side': 1.0,
                    'round_trip_cost_usd': 15.0},
             'MNQ': {'symbol': 'MNQ',
                     'included_sessions': 733,
                     'completed_trades': 724,
                     'long_trades': 368,
                     'short_trades': 356,
                     'gross_pnl_usd': 12779.5,
                     'transaction_costs_usd': 2172.0,
                     'net_profit_usd': 10607.5,
                     'gross_profit_usd': 75743.5,
                     'gross_loss_usd': 65136.0,
                     'trade_profit_factor': 1.1628515720953083,
                     'win_rate_percent': 43.232044198895025,
                     'average_trade_usd': 14.651243093922652,
                     'median_trade_usd': -67.5,
                     'maximum_drawdown_usd': -3674.0,
                     'slippage_ticks_per_side': 1.0,
                     'round_trip_cost_usd': 3.0},
             'profitable_nq_calendar_years': 3},
 'mcpt': {'market': 'NQ',
          'permutations': 1000,
          'p_value': 0.03796203796203796,
          'permutations_at_least_real': 37,
          'run_info': {'requested_workers': 0,
                       'workers_used': 8,
                       'resumed_permutations': 0,
                       'newly_completed_permutations': 1000,
                       'checkpoint_file': 'C:\\Users\\hocke\\Documents\\mcpt\\results\\EXP-005\\full_validation\\mcpt_checkpoint_1000.json',
                       'signature': '559ef2e59ae1ce73c6ad38a38ed9adfe7af3c56efc16255a90a83385603dfe1b',
                       'source_engine_version': 'exp005_session_mcpt_v2'}},
 'evaluation': {'decision': 'PASS_TO_REVIEW',
                'passed': True,
                'gates': {'nq_trade_profit_factor': {'actual': 1.1811261900882237,
                                                     'operator': '>',
                                                     'threshold': 1.05,
                                                     'passed': True},
                          'mnq_trade_profit_factor': {'actual': 1.1628515720953083,
                                                      'operator': '>',
                                                      'threshold': 1.0,
                                                      'passed': True},
                          'nq_net_profit_usd': {'actual': 116715.0,
                                                'operator': '>',
                                                'threshold': 0.0,
                                                'passed': True},
                          'mnq_net_profit_usd': {'actual': 10607.5,
                                                 'operator': '>',
                                                 'threshold': 0.0,
                                                 'passed': True},
                          'nq_mcpt_p_value': {'actual': 0.03796203796203796,
                                              'operator': '<=',
                                              'threshold': 0.05,
                                              'passed': True},
                          'nq_completed_trades': {'actual': 724,
                                                  'operator': '>=',
                                                  'threshold': 500,
                                                  'passed': True},
                          'profitable_nq_calendar_years': {'actual': 3,
                                                           'operator': '>=',
                                                           'threshold': 2,
                                                           'passed': True},
                          'included_invalid_sessions': {'actual': 0,
                                                        'operator': '<=',
                                                        'threshold': 0,
                                                        'passed': True},
                          'included_roll_switch_sessions': {'actual': 0,
                                                            'operator': '<=',
                                                            'threshold': 0,
                                                            'passed': True}},
                'failed_gates': []},
 'confirmation_period_accessed': True,
 'confirmation_results_calculated': True,
 'quick_transfer_rerun': False,
 'source_experiment_reopened': False,
 'automatic_lifecycle_source_edit': False,
 'next_stage_if_passed': 'REVIEW'}

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def get_exp005_full_validation_result() -> dict[str, Any]:
    return deepcopy(EXPECTED_RESULT)

def _close(actual: Any, expected: float, name: str, tolerance: float = 1e-12) -> None:
    if abs(float(actual) - expected) > tolerance:
        raise ValueError(f"EXP-005 full result {name} changed.")

def validate_exp005_full_validation_result(
    record: dict[str, Any] | None = None,
) -> None:
    current = EXPECTED_RESULT if record is None else record
    if current.get("schema_version") != 1:
        raise ValueError("EXP-005 full result schema changed.")
    if current.get("experiment_id") != "EXP-005" or current.get("stage") != "FULL_VALIDATION":
        raise ValueError("EXP-005 full result identity changed.")
    git = current["git"]
    if (
        git["commit"] != "1dc8b32f2eba1b19e19d3162d5f0acd2f820593e"
        or git["short_commit"] != "1dc8b32"
        or git["working_tree_clean"] is not True
    ):
        raise ValueError("EXP-005 full result Git provenance changed.")
    data = current["data"]
    if (
        data["confirmation_import_commit"] != "53a740aedb63e2a7508e3e010f5370be49cf816a"
        or data["included_sessions"] != 733
        or data["included_invalid_sessions"] != 0
        or data["included_roll_switch_sessions"] != 0
        or data["provider_unavailable_sessions_excluded"] != 2
        or data["provider_complete_sessions_restored"] != 1
        or data["potential_front_month_mismatch_sessions_excluded"] != 9
    ):
        raise ValueError("EXP-005 full data evidence changed.")
    expected_fingerprints = {
        "NQ_1m": "d91cf3123e0edea67dcb2a89fb2baf2c27d1e76f091d9bc2aeb4b34e61e92cd1",
        "MNQ_1m": "f08ee6b3e5f9d9243077cecd4b32229136dc74fabe6b9e9d75c110362a4c23f7",
        "NQ_5m": "4a50a121b79fe50cd8b3042e7b2e88472908689b89880f2da56374fba5d4a340",
        "MNQ_5m": "a10db6f4112bf467f18dbd3de7f1b334a08c0f6f971bb7bec4e3edd3d083c51a",
    }
    if data["fingerprints"] != expected_fingerprints:
        raise ValueError("EXP-005 full data fingerprints changed.")
    if current["fixed_rules"] != {
        "opening_range_minutes": 15,
        "direction_mode": "both",
        "parameter_combinations": 1,
        "optimization": False,
    }:
        raise ValueError("EXP-005 full fixed rules changed.")
    expected_metrics = {
        "NQ": {
            "included_sessions": 733, "completed_trades": 724,
            "long_trades": 367, "short_trades": 357,
            "net_profit_usd": 116715.0,
            "trade_profit_factor": 1.1811261900882237,
            "average_trade_usd": 161.2085635359116,
            "maximum_drawdown_usd": -36175.0,
            "round_trip_cost_usd": 15.0,
        },
        "MNQ": {
            "included_sessions": 733, "completed_trades": 724,
            "long_trades": 368, "short_trades": 356,
            "net_profit_usd": 10607.5,
            "trade_profit_factor": 1.1628515720953083,
            "average_trade_usd": 14.651243093922652,
            "maximum_drawdown_usd": -3674.0,
            "round_trip_cost_usd": 3.0,
        },
    }
    for symbol, expected in expected_metrics.items():
        actual = current["results"][symbol]
        for field, value in expected.items():
            if isinstance(value, float):
                _close(actual[field], value, f"{symbol} {field}")
            elif actual[field] != value:
                raise ValueError(f"EXP-005 full result {symbol} {field} changed.")
    if current["results"]["profitable_nq_calendar_years"] != 3:
        raise ValueError("EXP-005 profitable-year count changed.")
    mcpt = current["mcpt"]
    if (
        mcpt["market"] != "NQ" or mcpt["permutations"] != 1000
        or mcpt["permutations_at_least_real"] != 37
        or mcpt["run_info"]["source_engine_version"] != "exp005_session_mcpt_v2"
    ):
        raise ValueError("EXP-005 full MCPT identity changed.")
    _close(mcpt["p_value"], 0.03796203796203796, "MCPT p-value", 1e-15)
    evaluation = current["evaluation"]
    if (
        evaluation["decision"] != "PASS_TO_REVIEW"
        or evaluation["passed"] is not True
        or evaluation["failed_gates"] != []
        or not all(gate["passed"] is True for gate in evaluation["gates"].values())
    ):
        raise ValueError("EXP-005 full pass decision changed.")
    if (
        current["confirmation_period_accessed"] is not True
        or current["confirmation_results_calculated"] is not True
        or current["quick_transfer_rerun"] is not False
        or current["source_experiment_reopened"] is not False
        or current["automatic_lifecycle_source_edit"] is not False
        or current["next_stage_if_passed"] != "REVIEW"
    ):
        raise ValueError("EXP-005 full protection fields changed.")

def load_tracked_result() -> dict[str, Any]:
    if not TRACKED_RESULT_FILE.exists():
        raise FileNotFoundError(f"Tracked EXP-005 full result is missing: {TRACKED_RESULT_FILE}")
    if sha256_file(TRACKED_RESULT_FILE) != EXPECTED_FILE_SHA256:
        raise ValueError("Tracked EXP-005 full result hash changed.")
    record = json.loads(TRACKED_RESULT_FILE.read_text(encoding="utf-8"))
    validate_exp005_full_validation_result(record)
    if record != EXPECTED_RESULT:
        raise ValueError("Tracked EXP-005 full result content changed.")
    return record

def verify_local_full_validation_decision() -> dict[str, Any]:
    tracked = load_tracked_result()
    if not LOCAL_DECISION_FILE.exists():
        raise FileNotFoundError(
            "The original local EXP-005 full-validation decision is missing: "
            f"{LOCAL_DECISION_FILE}"
        )
    local = json.loads(LOCAL_DECISION_FILE.read_text(encoding="utf-8"))
    validate_exp005_full_validation_result(local)
    if local != tracked:
        raise ValueError("Local and tracked EXP-005 full decisions differ.")
    return local

if __name__ == "__main__":
    verify_local_full_validation_decision()
    print("EXP-005 full-validation pass is frozen and valid.")
