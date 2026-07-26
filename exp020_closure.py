from __future__ import annotations

from copy import deepcopy
import hashlib
import json


EXP020_CLOSURE = {'schema_version': 1,
 'experiment_id': 'EXP-020',
 'closed_date': '2026-07-26',
 'research_status': 'REVIEW',
 'classification': 'QUALIFIED_WITH_DISCLOSED_CALENDAR_FALLBACKS',
 'repository': {'implementation_commit': '36473b354c0b1a200c01494d4b64a78cee1e3430',
                'original_authorization_commit': 'e497b1abf247ed83295caa9378c2a4e6869922b1',
                'corrected_implementation_commit': 'fde5ee88b306f97b9e567fabe1b12267c9db4ae8',
                'correction_authorization_commit': 'b153a874df912a040b85117aab239ecdc98e5fda',
                'construction_head': 'b153a874df912a040b85117aab239ecdc98e5fda'},
 'source': {'experiment_id': 'EXP-019',
            'archive_sha256': '225a64dc06cb6bb303fd83d186f2e7d81e2a8a8bec44382380c8ccc1b0b6baa3',
            'contract_count': 66,
            'record_count': 6276486,
            'known_provider_warning_windows': 16,
            'archive_modified': False},
 'construction': {'started_at_utc': '2026-07-26T11:17:27.219447+00:00',
                  'completed_at_utc': '2026-07-26T11:19:49.117321+00:00',
                  'series_count': 4,
                  'row_count_per_series': 5463753,
                  'transition_count_per_method': 65,
                  'hard_checks': 20,
                  'hard_failure_count': 0,
                  'independent_rebuild': True,
                  'databento_api_calls': 0,
                  'construction_complete': True,
                  'construction_rerun_authorized': False},
 'method_result': {'primary_method': 'VOLUME_CROSSOVER_2_SESSION_WITH_CALENDAR_FALLBACK',
                   'benchmark_method': 'CALENDAR_THURSDAY_8_DAYS_BEFORE_EXPIRY',
                   'volume_crossovers_selected': 0,
                   'primary_calendar_fallbacks': 65,
                   'provider_warning_transitions': 23,
                   'fallbacks_without_provider_warnings': 42,
                   'identical_roll_dates': 65,
                   'identical_roll_differences': 65,
                   'unadjusted_market_data_identical': True,
                   'adjusted_market_data_identical': True,
                   'distinct_continuous_datasets': 2},
 'output_hashes': {'calendar_roll_backward_adjusted.parquet': '363670228327447833f23d1b223d63f75a44980804363770fd84dca907ada800',
                   'calendar_roll_unadjusted.parquet': 'b4058e1f9f496f117e4bd78c66fe56e6b82eb869215eba088e783d5d6dbe0285',
                   'CONSTRUCTION_COMPLETE.json': 'ba0b38184733d19df0cd56f5343797d2c6355407ac8bd72cf0b20bea6adbe593',
                   'construction_summary.json': 'afe2a60f6f7f284a46e6f54de157b4948528bc229ee8c5d7a0b6fea23116f830',
                   'contract_contribution.csv': '0f11cc4681d71008ea851a83cce6f07898c0437e77c6b0e239d39858a199e765',
                   'method_comparison.csv': '28438a952aa1696d9fe6381b67e9f8b8b5a563400bd9ab4882a9cbd35cfaf828',
                   'output_hashes.json': '8b06b1cc9967de27024ff19b29358d3b7d930bdfef82c91f62ca63d293f30580',
                   'report.md': '8ded0ddd7577bc82cab6898a0e61627f52b8888fd80d2e0353872e92415966d2',
                   'roll_ledger.csv': '6935bc97353cf68344795302ed15f6276af1492900ea333f3fb03ca34ff56214',
                   'volume_roll_backward_adjusted.parquet': '0a416d7ee25abadd899bc5033a4931edfc807d667749befa4ee5c3999788cc1e',
                   'volume_roll_unadjusted.parquet': '133e59235060ebf0d5a4c7c777729c8ab17d999b85a23aa401a6fb0daf825124'},
 'output_sizes_bytes': {'calendar_roll_backward_adjusted.parquet': 72111721,
                        'calendar_roll_unadjusted.parquet': 73918195,
                        'CONSTRUCTION_COMPLETE.json': 1486,
                        'construction_summary.json': 5156,
                        'contract_contribution.csv': 18326,
                        'method_comparison.csv': 774,
                        'output_hashes.json': 990,
                        'report.md': 2158,
                        'roll_ledger.csv': 28608,
                        'volume_roll_backward_adjusted.parquet': 72128150,
                        'volume_roll_unadjusted.parquet': 73934624},
 'interpretation': {'continuous_series_construction_qualified': True,
                    'primary_volume_trigger_active': False,
                    'primary_method_collapsed_to_calendar': True,
                    'dataset_qualification_only': True,
                    'exchange_accuracy_verified': False,
                    'best_vendor_selected': False,
                    'strategy_edge_tested': False,
                    'strategy_run': False,
                    'strategy_use_authorized': False,
                    'paper_trading_authorized': False,
                    'live_trading_authorized': False},
 'next_research_boundary': {'exp020_frozen': True,
                            'rerun_exp020_prohibited': True,
                            'new_experiment_id_required': True,
                            'exp021_preregistration_required': True,
                            'exp021_diagnostic_only': True,
                            'strategy_research_not_authorized': True}}

EXPECTED_EXP020_CLOSURE_SHA256 = "d23232285776135e623f35c10db57918274fc475111d70926a241d357f4e106f"


def canonical_record_hash(record):
    encoded = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def get_exp020_closure():
    return deepcopy(EXP020_CLOSURE)


def validate_exp020_closure(record=None):
    candidate = (
        EXP020_CLOSURE
        if record is None
        else record
    )

    if (
        candidate["experiment_id"] != "EXP-020"
        or candidate["closed_date"] != "2026-07-26"
        or candidate["research_status"] != "REVIEW"
        or candidate["classification"]
        != "QUALIFIED_WITH_DISCLOSED_CALENDAR_FALLBACKS"
    ):
        raise ValueError(
            "EXP-020 closure identity changed."
        )

    if (
        canonical_record_hash(candidate)
        != EXPECTED_EXP020_CLOSURE_SHA256
    ):
        raise ValueError(
            "EXP-020 closure record changed."
        )
