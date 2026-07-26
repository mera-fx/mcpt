from __future__ import annotations

from copy import deepcopy
import hashlib
import json


EXP022_CONSTRUCTION_AUTHORIZATION = {'schema_version': 1,
 'experiment_id': 'EXP-022',
 'authorization_id': 'EXP-022-CONSTRUCTION-AUTH-001',
 'authorized_date': '2026-07-26',
 'locked_preregistration_commit': '73c1255bcb904e71d927ed1097788de9b791bb54',
 'locked_preregistration_sha256': '527b7222fb56e8f070e404e0f49977730fd9709b254157cbb73710ccc6cee252',
 'locked_implementation_commit': '6dd69307c3dcfed876c57d6f62ae6d98bcb6ad93',
 'selected_method': 'VOL_GT_OUT_2S_E3',
 'construction_authorized': True,
 'one_time_construction': True,
 'maximum_construction_runs': 1,
 'protected_preflight_authorized': True,
 'construction_mode': 'LOCAL_FROZEN_SOURCE_ONLY',
 'output_directory': 'results/EXP-022/selected_continuous_series',
 'output_series_count': 2,
 'independent_rebuild_required': True,
 'databento_api_calls': 0,
 'credentials_required': False,
 'source_archive_modification_authorized': False,
 'exp020_output_modification_authorized': False,
 'exp021_output_modification_authorized': False,
 'roll_rule_reselection_authorized': False,
 'roll_date_recalculation_authorized': False,
 'strategy_run_authorized': False,
 'strategy_optimization_authorized': False,
 'mcpt_authorized': False,
 'bootstrap_authorized': False,
 'walk_forward_authorized': False,
 'paper_trading_authorized': False,
 'live_trading_authorized': False,
 'authorization_boundary': 'This authorization permits the protected read-only '
                           'preflight and one local construction of the two EXP-022 '
                           'selected-roll series representations. It permits no rerun '
                           'after completion and no strategy use.'}

EXPECTED_EXP022_CONSTRUCTION_AUTHORIZATION_SHA256 = (
    "587d9f12974cfd3161a7843012ac9c8e7b94420099334ba4d6dde3f7fbfb2ba7"
)


def canonical_record_hash(record):
    encoded = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def get_exp022_construction_authorization():
    return deepcopy(
        EXP022_CONSTRUCTION_AUTHORIZATION
    )


def validate_exp022_construction_authorization(
    candidate=None,
):
    record = (
        EXP022_CONSTRUCTION_AUTHORIZATION
        if candidate is None
        else candidate
    )

    if (
        record["experiment_id"] != "EXP-022"
        or record["authorization_id"]
        != "EXP-022-CONSTRUCTION-AUTH-001"
        or record["locked_preregistration_commit"]
        != "73c1255bcb904e71d927ed1097788de9b791bb54"
        or record["locked_implementation_commit"]
        != "6dd69307c3dcfed876c57d6f62ae6d98bcb6ad93"
        or record["selected_method"]
        != "VOL_GT_OUT_2S_E3"
    ):
        raise ValueError(
            "EXP-022 construction authorization "
            "identity changed."
        )

    if (
        record["construction_authorized"]
        is not True
        or record["one_time_construction"]
        is not True
        or record["maximum_construction_runs"] != 1
        or record["protected_preflight_authorized"]
        is not True
        or record["databento_api_calls"] != 0
        or record["strategy_run_authorized"]
        is not False
    ):
        raise ValueError(
            "EXP-022 construction authorization "
            "boundary changed."
        )

    if (
        canonical_record_hash(record)
        != EXPECTED_EXP022_CONSTRUCTION_AUTHORIZATION_SHA256
    ):
        raise ValueError(
            "EXP-022 construction authorization "
            "record changed."
        )
