from __future__ import annotations

from copy import deepcopy


EXP019_CLOSURE = {'schema_version': 1,
 'experiment_id': 'EXP-019',
 'closed_date': '2026-07-25',
 'research_status': 'REVIEW',
 'classification': 'QUALIFIED_WITH_KNOWN_PROVIDER_CONDITIONS',
 'source': {'vendor': 'Databento',
            'dataset': 'GLBX.MDP3',
            'schema': 'ohlcv-1m',
            'market': 'Exact quarterly NQ futures contracts',
            'first_date': '2010-06-06',
            'end_exclusive': '2026-07-24',
            'contract_count': 66},
 'acquisition': {'successful_downloads': 66,
                 'automatic_retries': 0,
                 'attempted_estimated_cost_usd': 22.914097756145,
                 'maximum_authorized_cost_usd': 35.0,
                 'compressed_total_bytes': 104491346,
                 'archive_sha256': '225a64dc06cb6bb303fd83d186f2e7d81e2a8a8bec44382380c8ccc1b0b6baa3'},
 'audit': {'contracts_audited': 66,
           'records_audited': 6276486,
           'hard_checks': 17,
           'hard_failure_count': 0,
           'known_provider_warning_windows': 16,
           'missing_minute_run_count': 330174,
           'largest_missing_minute_run': 5808,
           'adjacent_pairs_measured': 65,
           'total_overlap_minutes': 807158,
           'databento_api_calls': 0,
           'archive_files_modified': False},
 'evidence_hashes': {'acquisition_manifest_sha256': 'f8fbac395bbe7f9cdafd0187a00c3d77ee8f6ded31d7ba6870d6ed3c8e3007b3',
                     'acquisition_completion_sha256': 'ef8ad499e62284d872edfd480e7aa635a26340e85ba1d74d98a51ed80f71f935',
                     'audit_summary_sha256': 'e02b3e6d67715fbdfa2c42677225ce74cdf444b8d14cbf93a80e897fbca18287',
                     'audit_contracts_sha256': '540008d208cf1d4f35d3b2cdbdb1eda71f25b18bb931c9c4091cfdad29548b11',
                     'audit_overlaps_sha256': 'e07d8cd41a0ae2544d1adb786fa50680a595f5c479ca699ff044d29991d26e7f',
                     'audit_report_sha256': '172719fee061f133dce5a4755caa29e29b48d8984065cb43df4c6ab93eb043da',
                     'audit_completion_sha256': '4f4f224531d3de440e20d9da600e93c6a0427ddec04b70e507005aecf67075b8'},
 'audit_provenance': {'audit_preregistration_commit': '0ffc71d048f1ccf82e8311794789a18a61519bd0',
                      'audit_execution_commit': '2f5e1898bc6a42ea7dccff50efef3c84d56911e2',
                      'audit_generated_at_utc': '2026-07-25T14:18:15.110934+00:00',
                      'audit_completed_at_utc': '2026-07-25T14:18:15.119388+00:00',
                      'working_tree_clean_after_audit': True},
 'interpretation': {'exact_contract_archive_qualified': True,
                    'qualified_with_known_provider_conditions': True,
                    'provider_conditions_must_remain_disclosed': True,
                    'exchange_accuracy_verified': False,
                    'best_vendor_selected': False,
                    'continuous_series_constructed': False,
                    'roll_rule_selected': False,
                    'adjustment_method_selected': False,
                    'strategy_run': False,
                    'strategy_use_authorized': False,
                    'paper_trading_authorized': False,
                    'live_trading_authorized': False,
                    'prior_experiments_changed': False},
 'next_research_boundary': {'exp019_frozen': True,
                            'rerun_exp019_prohibited': True,
                            'new_experiment_id_required': True,
                            'separate_preregistration_required': True,
                            'continuous_construction_not_authorized_here': True,
                            'strategy_research_not_authorized_here': True}}


def get_exp019_closure():
    return deepcopy(
        EXP019_CLOSURE
    )


def validate_exp019_closure(
    record=None,
):
    r = (
        EXP019_CLOSURE
        if record is None
        else record
    )

    if (
        r["experiment_id"] != "EXP-019"
        or r["closed_date"] != "2026-07-25"
        or r["research_status"] != "REVIEW"
        or r["classification"]
        != (
            "QUALIFIED_WITH_KNOWN_"
            "PROVIDER_CONDITIONS"
        )
    ):
        raise ValueError(
            "EXP-019 closure identity changed."
        )

    source = r["source"]

    if (
        source["vendor"] != "Databento"
        or source["dataset"] != "GLBX.MDP3"
        or source["schema"] != "ohlcv-1m"
        or source["first_date"]
        != "2010-06-06"
        or source["end_exclusive"]
        != "2026-07-24"
        or source["contract_count"] != 66
    ):
        raise ValueError(
            "EXP-019 source boundary changed."
        )

    acquisition = r["acquisition"]

    if (
        acquisition[
            "successful_downloads"
        ]
        != 66
        or acquisition[
            "automatic_retries"
        ]
        != 0
        or acquisition[
            "attempted_estimated_cost_usd"
        ]
        != 22.914097756145
        or acquisition[
            "maximum_authorized_cost_usd"
        ]
        != 35.0
        or acquisition[
            "compressed_total_bytes"
        ]
        != 104491346
        or acquisition["archive_sha256"]
        != (
            "225a64dc06cb6bb303fd83d186f2e7d8"
            "1e2a8a8bec44382380c8ccc1b0b6baa3"
        )
    ):
        raise ValueError(
            "EXP-019 acquisition result changed."
        )

    audit = r["audit"]

    if (
        audit["contracts_audited"] != 66
        or audit["records_audited"]
        != 6276486
        or audit["hard_checks"] != 17
        or audit["hard_failure_count"] != 0
        or audit[
            "known_provider_warning_windows"
        ]
        != 16
        or audit[
            "missing_minute_run_count"
        ]
        != 330174
        or audit[
            "largest_missing_minute_run"
        ]
        != 5808
        or audit[
            "adjacent_pairs_measured"
        ]
        != 65
        or audit[
            "total_overlap_minutes"
        ]
        != 807158
        or audit["databento_api_calls"] != 0
        or audit[
            "archive_files_modified"
        ]
        is not False
    ):
        raise ValueError(
            "EXP-019 audit result changed."
        )

    evidence = r["evidence_hashes"]

    expected_hashes = {
        "acquisition_manifest_sha256": (
            "f8fbac395bbe7f9cdafd0187a00c3d77"
            "ee8f6ded31d7ba6870d6ed3c8e3007b3"
        ),
        "acquisition_completion_sha256": (
            "ef8ad499e62284d872edfd480e7aa635"
            "a26340e85ba1d74d98a51ed80f71f935"
        ),
        "audit_summary_sha256": (
            "e02b3e6d67715fbdfa2c42677225ce74"
            "cdf444b8d14cbf93a80e897fbca18287"
        ),
        "audit_contracts_sha256": (
            "540008d208cf1d4f35d3b2cdbdb1eda7"
            "1f25b18bb931c9c4091cfdad29548b11"
        ),
        "audit_overlaps_sha256": (
            "e07d8cd41a0ae2544d1adb786fa50680"
            "a595f5c479ca699ff044d29991d26e7f"
        ),
        "audit_report_sha256": (
            "172719fee061f133dce5a4755caa29e2"
            "9b48d8984065cb43df4c6ab93eb043da"
        ),
        "audit_completion_sha256": (
            "4f4f224531d3de440e20d9da600e93c"
            "6a0427ddec04b70e507005aecf67075b8"
        ),
    }

    if evidence != expected_hashes:
        raise ValueError(
            "EXP-019 evidence hashes changed."
        )

    interpretation = r["interpretation"]

    required_true = (
        "exact_contract_archive_qualified",
        "qualified_with_known_provider_conditions",
        "provider_conditions_must_remain_disclosed",
    )

    if not all(
        interpretation[key] is True
        for key in required_true
    ):
        raise ValueError(
            "EXP-019 qualification interpretation changed."
        )

    required_false = (
        "exchange_accuracy_verified",
        "best_vendor_selected",
        "continuous_series_constructed",
        "roll_rule_selected",
        "adjustment_method_selected",
        "strategy_run",
        "strategy_use_authorized",
        "paper_trading_authorized",
        "live_trading_authorized",
        "prior_experiments_changed",
    )

    if not all(
        interpretation[key] is False
        for key in required_false
    ):
        raise ValueError(
            "EXP-019 interpretation boundary changed."
        )

    boundary = r[
        "next_research_boundary"
    ]

    if not all(
        value is True
        for value in boundary.values()
    ):
        raise ValueError(
            "EXP-019 next-research boundary changed."
        )
