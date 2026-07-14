from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parent
TRACKED_RESULT_FILE = (
    PROJECT_DIR
    / "research"
    / "EXP-005_quick_transfer_result.json"
)
LOCAL_DECISION_FILE = (
    PROJECT_DIR
    / "results"
    / "EXP-005"
    / "quick_transfer"
    / "quick_transfer_decision.json"
)
EXPECTED_FILE_SHA256 = "4705eeece180b05f4242943680829256458625a3c5e4ed7f712c674bbc51c51d"

EXPECTED_RESULT: dict[str, Any] = {'schema_version': 1,
 'experiment_id': 'EXP-005',
 'stage': 'QUICK_TRANSFER',
 'calculated_at_utc': '2026-07-13T22:23:32+00:00',
 'git': {'commit': '4a791e121af129bcad75122e532def4ca27d70dd',
         'short_commit': '4a791e1',
         'working_tree_clean': True},
 'data': {'import_audit': 'C:\\Users\\hocke\\Documents\\mcpt\\results\\EXP-005\\data\\quantower_import_audit.json',
          'included_sessions': 906,
          'included_invalid_sessions': 0,
          'included_roll_switch_sessions': 0,
          'potential_mismatch_sessions_excluded': 3,
          'provider_unavailable_sessions_excluded': 3,
          'fingerprints': {'NQ_1m': '5a0a9fd5bf555865b39da5dec6576eb0fe3d3607176c04a931ca463950f31dda',
                           'MNQ_1m': '46bf07a69a506114447065d37e03c9195bf048d19df44a5aac277c3c4ea3c1a2',
                           'NQ_5m': '32ab30b4657592c84b00468ed46c0d5dd7904cf3796501f692f16b0cc40dd3f2',
                           'MNQ_5m': 'd1cd7d67f37b6bda16cf98bd9e199d979f0ababb9b97cd53d13583dbe4e5e0eb'}},
 'fixed_rules': {'opening_range_minutes': 15,
                 'direction_mode': 'both',
                 'parameter_combinations': 1,
                 'optimization': False},
 'results': {'NQ': {'symbol': 'NQ',
                    'included_sessions': 906,
                    'completed_trades': 884,
                    'long_trades': 457,
                    'short_trades': 427,
                    'gross_pnl_usd': 107920.0,
                    'transaction_costs_usd': 13260.0,
                    'net_profit_usd': 94660.0,
                    'gross_profit_usd': 800835.0,
                    'gross_loss_usd': 706175.0,
                    'trade_profit_factor': 1.1340460933904486,
                    'win_rate_percent': 45.81447963800905,
                    'average_trade_usd': 107.08144796380091,
                    'median_trade_usd': -297.5,
                    'maximum_drawdown_usd': -37925.0,
                    'slippage_ticks_per_side': 1.0,
                    'round_trip_cost_usd': 15.0},
             'MNQ': {'symbol': 'MNQ',
                     'included_sessions': 906,
                     'completed_trades': 884,
                     'long_trades': 454,
                     'short_trades': 430,
                     'gross_pnl_usd': 11201.5,
                     'transaction_costs_usd': 2652.0,
                     'net_profit_usd': 8549.5,
                     'gross_profit_usd': 79698.5,
                     'gross_loss_usd': 71149.0,
                     'trade_profit_factor': 1.120163319231472,
                     'win_rate_percent': 45.70135746606335,
                     'average_trade_usd': 9.671380090497738,
                     'median_trade_usd': -31.5,
                     'maximum_drawdown_usd': -4078.5,
                     'slippage_ticks_per_side': 1.0,
                     'round_trip_cost_usd': 3.0}},
 'mcpt': {'market': 'NQ',
          'permutations': 25,
          'p_value': 0.07692307692307693,
          'permutations_at_least_real': 1,
          'run_info': {'requested_workers': 0,
                       'workers_used': 8,
                       'resumed_permutations': 0,
                       'newly_completed_permutations': 25,
                       'checkpoint_file': 'C:\\Users\\hocke\\Documents\\mcpt\\results\\EXP-005\\quick_transfer\\mcpt_checkpoint.json',
                       'signature': '7810cc5f8833366580523a58708c502131320992c6e49dcbdd17950659b9a6c0'}},
 'evaluation': {'decision': 'PASS_TO_FULL_VALIDATION',
                'passed': True,
                'gates': {'nq_trade_profit_factor': {'actual': 1.1340460933904486,
                                                     'operator': '>',
                                                     'threshold': 1.05,
                                                     'passed': True},
                          'mnq_trade_profit_factor': {'actual': 1.120163319231472,
                                                      'operator': '>',
                                                      'threshold': 1.0,
                                                      'passed': True},
                          'nq_net_profit_usd': {'actual': 94660.0,
                                                'operator': '>',
                                                'threshold': 0.0,
                                                'passed': True},
                          'mnq_net_profit_usd': {'actual': 8549.5,
                                                 'operator': '>',
                                                 'threshold': 0.0,
                                                 'passed': True},
                          'nq_mcpt_p_value': {'actual': 0.07692307692307693,
                                              'operator': '<=',
                                              'threshold': 0.2,
                                              'passed': True},
                          'nq_completed_trades': {'actual': 884,
                                                  'operator': '>=',
                                                  'threshold': 700,
                                                  'passed': True},
                          'nq_long_trades': {'actual': 457,
                                             'operator': '>=',
                                             'threshold': 150,
                                             'passed': True},
                          'nq_short_trades': {'actual': 427,
                                              'operator': '>=',
                                              'threshold': 150,
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
 'confirmation_period_accessed': False,
 'confirmation_results_calculated': False,
 'source_experiment_reopened': False,
 'automatic_lifecycle_source_edit': False}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with Path(path).open("rb") as handle:
        for block in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def get_exp005_quick_transfer_result(
) -> dict[str, Any]:
    return deepcopy(EXPECTED_RESULT)


def validate_exp005_quick_transfer_result(
    record: dict[str, Any] | None = None,
) -> None:
    current = (
        EXPECTED_RESULT
        if record is None
        else record
    )

    if current.get("schema_version") != 1:
        raise ValueError(
            "EXP-005 quick result schema changed."
        )

    if (
        current.get("experiment_id") != "EXP-005"
        or current.get("stage") != "QUICK_TRANSFER"
    ):
        raise ValueError(
            "EXP-005 quick result identity changed."
        )

    git = current["git"]

    if (
        git["commit"]
        != "4a791e121af129bcad75122e532def4ca27d70dd"
        or git["short_commit"] != "4a791e1"
        or git["working_tree_clean"] is not True
    ):
        raise ValueError(
            "EXP-005 quick result Git provenance changed."
        )

    data = current["data"]

    if (
        data["included_sessions"] != 906
        or data["included_invalid_sessions"] != 0
        or data["included_roll_switch_sessions"] != 0
        or data["potential_mismatch_sessions_excluded"] != 3
        or data["provider_unavailable_sessions_excluded"] != 3
    ):
        raise ValueError(
            "EXP-005 quick data evidence changed."
        )

    expected_fingerprints = {
        "NQ_1m": (
            "5a0a9fd5bf555865b39da5dec6576eb0f"
            "e3d3607176c04a931ca463950f31dda"
        ),
        "MNQ_1m": (
            "46bf07a69a506114447065d37e03c9195"
            "bf048d19df44a5aac277c3c4ea3c1a2"
        ),
        "NQ_5m": (
            "32ab30b4657592c84b00468ed46c0d5d"
            "d7904cf3796501f692f16b0cc40dd3f2"
        ),
        "MNQ_5m": (
            "d1cd7d67f37b6bda16cf98bd9e199d97"
            "9f0ababb9b97cd53d13583dbe4e5e0eb"
        ),
    }

    if data["fingerprints"] != expected_fingerprints:
        raise ValueError(
            "EXP-005 quick data fingerprints changed."
        )

    results = current["results"]
    nq = results["NQ"]
    mnq = results["MNQ"]

    expected_metrics = {
        "NQ": {
            "completed_trades": 884,
            "long_trades": 457,
            "short_trades": 427,
            "net_profit_usd": 94660.0,
            "trade_profit_factor": 1.1340460933904486,
            "maximum_drawdown_usd": -37925.0,
        },
        "MNQ": {
            "completed_trades": 884,
            "long_trades": 454,
            "short_trades": 430,
            "net_profit_usd": 8549.5,
            "trade_profit_factor": 1.120163319231472,
            "maximum_drawdown_usd": -4078.5,
        },
    }

    for symbol, actual in (
        ("NQ", nq),
        ("MNQ", mnq),
    ):
        for field, expected in (
            expected_metrics[symbol].items()
        ):
            value = actual[field]

            if isinstance(expected, float):
                if abs(float(value) - expected) > 1e-12:
                    raise ValueError(
                        f"{symbol} {field} changed."
                    )
            elif value != expected:
                raise ValueError(
                    f"{symbol} {field} changed."
                )

    mcpt = current["mcpt"]

    if (
        mcpt["market"] != "NQ"
        or mcpt["permutations"] != 25
        or mcpt["permutations_at_least_real"] != 1
        or abs(
            float(mcpt["p_value"])
            - 0.07692307692307693
        )
        > 1e-15
    ):
        raise ValueError(
            "EXP-005 quick MCPT evidence changed."
        )

    evaluation = current["evaluation"]

    if (
        evaluation["decision"]
        != "PASS_TO_FULL_VALIDATION"
        or evaluation["passed"] is not True
        or evaluation["failed_gates"] != []
        or not all(
            gate["passed"] is True
            for gate in evaluation["gates"].values()
        )
    ):
        raise ValueError(
            "EXP-005 quick pass decision changed."
        )

    if (
        current["confirmation_period_accessed"] is not False
        or current["confirmation_results_calculated"] is not False
        or current["source_experiment_reopened"] is not False
        or current["automatic_lifecycle_source_edit"] is not False
    ):
        raise ValueError(
            "EXP-005 quick access protections changed."
        )


def load_tracked_result() -> dict[str, Any]:
    if not TRACKED_RESULT_FILE.exists():
        raise FileNotFoundError(
            f"Tracked result is missing: {TRACKED_RESULT_FILE}"
        )

    if sha256_file(
        TRACKED_RESULT_FILE
    ) != EXPECTED_FILE_SHA256:
        raise ValueError(
            "Tracked EXP-005 quick result hash changed."
        )

    record = json.loads(
        TRACKED_RESULT_FILE.read_text(
            encoding="utf-8"
        )
    )
    validate_exp005_quick_transfer_result(record)

    return record


def verify_local_quick_transfer_decision() -> dict[str, Any]:
    tracked = load_tracked_result()

    if not LOCAL_DECISION_FILE.exists():
        raise FileNotFoundError(
            "The original local quick-transfer decision "
            f"is missing: {LOCAL_DECISION_FILE}"
        )

    local = json.loads(
        LOCAL_DECISION_FILE.read_text(
            encoding="utf-8"
        )
    )
    validate_exp005_quick_transfer_result(local)

    if local != tracked:
        raise ValueError(
            "Local and tracked EXP-005 quick decisions differ."
        )

    return local


if __name__ == "__main__":
    verify_local_quick_transfer_decision()

    print(
        "EXP-005 quick-transfer pass is frozen and valid."
    )
