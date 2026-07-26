from __future__ import annotations

from copy import deepcopy
import hashlib
import json


EXP022_CLOSURE = {'schema_version': 1,
 'experiment_id': 'EXP-022',
 'closed_date': '2026-07-26',
 'research_status': 'REVIEW',
 'classification': 'QUALIFIED_AS_SELECTED_VOLUME_ROLL_CONTINUOUS_SERIES',
 'repository': {'preregistration_commit': '73c1255bcb904e71d927ed1097788de9b791bb54',
                'implementation_commit': '6dd69307c3dcfed876c57d6f62ae6d98bcb6ad93',
                'authorization_commit': '22d89d7d4521c7f34283fe01342377dceb286b94',
                'construction_head': '22d89d7d4521c7f34283fe01342377dceb286b94'},
 'locked_records': {'preregistration_sha256': '527b7222fb56e8f070e404e0f49977730fd9709b254157cbb73710ccc6cee252',
                    'authorization_sha256': '587d9f12974cfd3161a7843012ac9c8e7b94420099334ba4d6dde3f7fbfb2ba7',
                    'exp021_closure_commit': '253ef695bae819102ec75c3e0cadfa99c8f78d3f',
                    'exp021_closure_record_sha256': 'f4e1aa2966852c74a966a318dbe427f590c591122bebf02a15bc267338fd21a4'},
 'source': {'exp019_archive_sha256': '225a64dc06cb6bb303fd83d186f2e7d81e2a8a8bec44382380c8ccc1b0b6baa3',
            'contract_count': 66,
            'record_count': 6276486,
            'archive_or_prior_output_modified': False},
 'construction': {'started_at_utc': '2026-07-26T14:59:36.051376+00:00',
                  'completed_at_utc': '2026-07-26T15:01:54.872165+00:00',
                  'selected_method': 'VOL_GT_OUT_2S_E3',
                  'series_count': 2,
                  'row_count_per_series': 5457606,
                  'first_timestamp_utc': '2010-06-06T22:00:00+00:00',
                  'last_timestamp_utc': '2026-07-23T23:59:00+00:00',
                  'transition_count': 65,
                  'clean_transition_count': 42,
                  'volume_driven_transition_count': 40,
                  'calendar_fallback_count': 25,
                  'warning_calendar_fallback_count': 23,
                  'clean_calendar_fallback_count': 2,
                  'hard_checks': 20,
                  'hard_failure_count': 0,
                  'independent_rebuild': True,
                  'databento_api_calls': 0,
                  'credentials_used': False,
                  'construction_complete': True,
                  'construction_rerun_authorized': False},
 'semantic_hashes': {'roll_ledger_semantic_sha256': 'c800004230ae0db630a4414db81d1c030c02976ec06c47731ba4384265069090',
                     'selected_roll_backward_adjusted_semantic_sha256': '3c6fa83821183ca54bc547c555834ceb16a126be50f90d8c6db5684220929951',
                     'selected_roll_unadjusted_semantic_sha256': '29daf3f20b022fb69967349095eb9663bd04276cbc5743a65b1ecabc33113640'},
 'output_files': {'CONSTRUCTION_COMPLETE.json': {'size_bytes': 3171,
                                                 'sha256': 'af69c2e0d426d3f3f57bc683abfb8a28e050f4494d03d7c16bf180365095eef8'},
                  'construction_summary.json': {'size_bytes': 3108,
                                                'sha256': '045ae06f0ccb43e723f6297181e70f5b011936eeaad62500e27497ac8c2f3030'},
                  'contract_contribution.csv': {'size_bytes': 7411,
                                                'sha256': 'aac7dc35c06d8be0fc87659d373a694390b75855c5a80c37941c3612ae5a1260'},
                  'output_hashes.json': {'size_bytes': 810,
                                         'sha256': '7bd7f513d7b948111df709f1754865afc9745a35aff5ca3ae702eed9d9a3f57e'},
                  'report.md': {'size_bytes': 1999,
                                'sha256': '563e1186a56facba90da879c23625a241e84470921ab894053c9ebd7ccadc7bf'},
                  'roll_ledger.csv': {'size_bytes': 15343,
                                      'sha256': '74dbd346f27ea980e3d66e81acf99c6e08df80ca573100a7618f52b131d151aa'},
                  'selected_roll_backward_adjusted.parquet': {'size_bytes': 71964074,
                                                              'sha256': '61ccb3621b53fa313147a866948ec1f2c7a6b36956d2ba26090162b518c30c84'},
                  'selected_roll_unadjusted.parquet': {'size_bytes': 73760121,
                                                       'sha256': '606a69bbba4f4a5db3e0356d7b2849f9481e4555dc24cae4c6b9d1d12f673ab1'}},
 'interpretation': {'selected_continuous_series_qualified': True,
                    'selected_method_was_operationally_selected': True,
                    'selected_method_was_strategy_performance_selected': False,
                    'dataset_qualification_only': True,
                    'strategy_edge_tested': False,
                    'strategy_run': False,
                    'strategy_use_authorized': False,
                    'exchange_accuracy_verified': False,
                    'best_vendor_selected': False,
                    'paper_trading_authorized': False,
                    'live_trading_authorized': False},
 'next_research_boundary': {'exp022_frozen': True,
                            'rerun_exp022_prohibited': True,
                            'modify_exp022_outputs_prohibited': True,
                            'new_experiment_id_required': True,
                            'exp023_preregistration_required': True,
                            'strategy_research_requires_separate_preregistration': True,
                            'paper_or_live_trading_not_authorized': True}}

EXPECTED_EXP022_CLOSURE_SHA256 = (
    "1cc01baddeeae3acf81b0785923b581fad6aac0b6e36071d07d0d83d35bf588d"
)


def canonical_record_hash(record):
    encoded = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def get_exp022_closure():
    return deepcopy(EXP022_CLOSURE)


def validate_exp022_closure(candidate=None):
    record = (
        EXP022_CLOSURE
        if candidate is None
        else candidate
    )

    if (
        record["experiment_id"] != "EXP-022"
        or record["closed_date"] != "2026-07-26"
        or record["research_status"] != "REVIEW"
        or record["classification"]
        != (
            "QUALIFIED_AS_SELECTED_VOLUME_ROLL_"
            "CONTINUOUS_SERIES"
        )
    ):
        raise ValueError(
            "EXP-022 closure identity changed."
        )

    if (
        canonical_record_hash(record)
        != EXPECTED_EXP022_CLOSURE_SHA256
    ):
        raise ValueError(
            "EXP-022 closure record changed."
        )
