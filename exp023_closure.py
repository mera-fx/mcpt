from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any


EXP023_CLOSURE: dict[str, Any] = {
    "schema_version": 1,
    "experiment_id": "EXP-023",
    "closed_date": "2026-07-26",
    "research_status": "REVIEW",
    "classification": (
        "TRANSFER_DIAGNOSTIC_COMPLETE_WITH_MATERIAL_DIFFERENCES"
    ),
    "repository": {
        "preregistration_commit": (
            "66ba6a46f31cc8715447179c19caf2f4c1a1e8be"
        ),
        "implementation_commit": (
            "c17e9ea567c234e2d941f949168d62721f6d4963"
        ),
        "authorization_commit": (
            "9dbce86c040fa468a55fdb53501a13a0c74609f5"
        ),
        "execution_head": (
            "9dbce86c040fa468a55fdb53501a13a0c74609f5"
        ),
    },
    "locked_records": {
        "preregistration_sha256": (
            "20c7295123adead63b5e9c398419a3129"
            "aa93c4fcd3e597e6e92c295dc2841be"
        ),
        "authorization_sha256": (
            "810e04027692a9edc14b05fa2a9326e3"
            "bcaa8cce15000ce60ebc2312bed5a55c"
        ),
        "exp022_closure_commit": (
            "9d157c8e7a6ba584a96cb5d37086672ad5b64ea1"
        ),
        "exp022_closure_record_sha256": (
            "1cc01baddeeae3acf81b0785923b581fa"
            "d6aac0b6e36071d07d0d83d35bf588d"
        ),
    },
    "execution": {
        "started_at_utc": "2026-07-26T17:28:24.105761+00:00",
        "completed_at_utc": "2026-07-26T17:33:56.432099+00:00",
        "authorized_run_count": 1,
        "reference_session_count": 1_331,
        "candidate_count": 3,
        "representation_count": 2,
        "hard_check_count": 20,
        "hard_failure_count": 0,
        "independent_rebuild": True,
        "independent_rebuild_hashes_match": True,
        "output_manifest_file_count": 18,
        "frozen_output_file_count": 20,
        "visual_asset_count": 7,
        "partial_output_directory_absent": True,
        "protected_history_accessed": False,
        "out_of_overlap_strategy_values_calculated": False,
        "databento_api_calls": 0,
        "network_access": False,
        "optimization": False,
        "mcpt": False,
        "bootstrap": False,
        "walk_forward": False,
        "strategy_ranking": False,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
        "transfer_diagnostic_complete": True,
        "rerun_authorized": False,
    },
    "primary_candidate_results": (
        {
            "candidate_id": "gap_fade_0p50_1r",
            "representation_id": "BACKWARD_ADJUSTED",
            "eligible_session_count": 1_326,
            "eligible_session_share": 0.9962434259954921,
            "trade_indicator_and_direction_agreement": (
                0.9645550527903469
            ),
            "reference_trade_count": 186,
            "transfer_trade_count": 230,
            "trade_count_relative_difference": (
                0.23655913978494625
            ),
            "common_trade_count": 184,
            "common_trade_match_share": 0.7931034482758621,
            "matching_entry_timestamp_agreement": 1.0,
            "common_trade_gross_pnl_correlation": (
                0.999988183644088
            ),
            "common_trade_gross_pnl_sign_agreement": 1.0,
            "transfer_profit_factor": 1.3669991687448046,
            "transfer_net_profit_usd": 30_905.0,
            "transfer_maximum_drawdown_usd": -8_735.0,
            "all_transfer_gates_pass": False,
            "failed_gates": (
                "trade_indicator_and_direction_agreement",
                "trade_count_relative_difference",
                "common_trade_match_share",
            ),
        },
        {
            "candidate_id": "premarket_continuation_0p50_time",
            "representation_id": "BACKWARD_ADJUSTED",
            "eligible_session_count": 1_329,
            "eligible_session_share": 0.9984973703981969,
            "trade_indicator_and_direction_agreement": (
                0.9984951091045899
            ),
            "reference_trade_count": 291,
            "transfer_trade_count": 289,
            "trade_count_relative_difference": (
                0.006872852233676976
            ),
            "common_trade_count": 289,
            "common_trade_match_share": 0.993127147766323,
            "matching_entry_timestamp_agreement": 1.0,
            "common_trade_gross_pnl_correlation": (
                0.9999970424236826
            ),
            "common_trade_gross_pnl_sign_agreement": 1.0,
            "transfer_profit_factor": 1.718173515981735,
            "transfer_net_profit_usd": 117_960.0,
            "transfer_maximum_drawdown_usd": -20_715.0,
            "all_transfer_gates_pass": True,
            "failed_gates": (),
        },
        {
            "candidate_id": "premarket_continuation_0p75_time",
            "representation_id": "BACKWARD_ADJUSTED",
            "eligible_session_count": 1_329,
            "eligible_session_share": 0.9984973703981969,
            "trade_indicator_and_direction_agreement": (
                0.999247554552295
            ),
            "reference_trade_count": 88,
            "transfer_trade_count": 87,
            "trade_count_relative_difference": (
                0.011363636363636364
            ),
            "common_trade_count": 87,
            "common_trade_match_share": 0.9886363636363636,
            "matching_entry_timestamp_agreement": 1.0,
            "common_trade_gross_pnl_correlation": (
                0.9999968378214901
            ),
            "common_trade_gross_pnl_sign_agreement": 1.0,
            "transfer_profit_factor": 1.9226493747105142,
            "transfer_net_profit_usd": 39_840.0,
            "transfer_maximum_drawdown_usd": -5_555.0,
            "all_transfer_gates_pass": False,
            "failed_gates": (
                "trade_count_relative_difference",
            ),
        },
    ),
    "secondary_representation_results": (
        {
            "candidate_id": "gap_fade_0p50_1r",
            "representation_id": "UNADJUSTED",
            "trade_indicator_and_direction_agreement": (
                0.9630467571644042
            ),
            "trade_count_relative_difference": (
                0.23655913978494625
            ),
            "common_trade_match_share": 0.7854077253218884,
            "all_transfer_gates_pass": False,
        },
        {
            "candidate_id": "premarket_continuation_0p50_time",
            "representation_id": "UNADJUSTED",
            "trade_indicator_and_direction_agreement": (
                0.9984951091045899
            ),
            "trade_count_relative_difference": (
                0.006872852233676976
            ),
            "common_trade_match_share": 0.993127147766323,
            "all_transfer_gates_pass": True,
        },
        {
            "candidate_id": "premarket_continuation_0p75_time",
            "representation_id": "UNADJUSTED",
            "trade_indicator_and_direction_agreement": (
                0.999247554552295
            ),
            "trade_count_relative_difference": (
                0.011363636363636364
            ),
            "common_trade_match_share": 0.9886363636363636,
            "all_transfer_gates_pass": False,
        },
    ),
    "representation_sensitivity": (
        {
            "candidate_id": "gap_fade_0p50_1r",
            "common_eligible_session_count": 1_326,
            "decision_agreement": 0.9969834087481146,
            "backward_adjusted_trade_count": 230,
            "unadjusted_trade_count": 230,
            "common_trade_count": 228,
            "common_trade_match_share": 0.9827586206896551,
            "gross_pnl_correlation": 1.0,
        },
        {
            "candidate_id": "premarket_continuation_0p50_time",
            "common_eligible_session_count": 1_329,
            "decision_agreement": 1.0,
            "backward_adjusted_trade_count": 289,
            "unadjusted_trade_count": 289,
            "common_trade_count": 289,
            "common_trade_match_share": 1.0,
            "gross_pnl_correlation": 1.0,
        },
        {
            "candidate_id": "premarket_continuation_0p75_time",
            "common_eligible_session_count": 1_329,
            "decision_agreement": 1.0,
            "backward_adjusted_trade_count": 87,
            "unadjusted_trade_count": 87,
            "common_trade_count": 87,
            "common_trade_match_share": 1.0,
            "gross_pnl_correlation": 1.0,
        },
    ),
    "frame_semantic_hashes": {
        "metrics": (
            "b44e602e84c983f0a3e2f7b6704f3b9"
            "d4a3862020297930e7850f7af52d1835d"
        ),
        "periods": (
            "d08be3d923cdbb70200116e99480df2b"
            "38f11a57d828887857b3a95c94f21935"
        ),
        "roll_proximity": (
            "0a3caae92df03e29adec0c80aa8f727a"
            "d8cecd4266a812e65b537afd1df446a0"
        ),
        "sensitivity": (
            "e6171360f6565012c534ee6b76c4ad1f"
            "ef7406669094e9a0f4383c9309e92ae4"
        ),
        "session_alignment": (
            "bb26c92cdf49a6016ccfe8f5211375b6"
            "eacb19348cdf37c2be1b48ac1a202a28"
        ),
        "trade_alignment": (
            "351024fc7221fcac29d631dd9dab71c2f"
            "4159769500a738894379e6e0c664ca3"
        ),
        "transfer_trades": (
            "9800859441b2ed495c7ff0cd9f9da5bb"
            "3a8724f071bbf57c905b828f913aedef"
        ),
    },
    "output_manifest_sha256": (
        "05731ab19c85eff57750dc126da9b2227"
        "937094b8bbb1d7da31c38847392194b"
    ),
    "output_files": {
        "assets/annual_comparison.png": {
            "size_bytes": 84_834,
            "sha256": (
                "0fa37c857076ea0bb62df670849ad1087"
                "136906502a849d038fbc9a52a5f5705"
            ),
        },
        "assets/common_trade_pnl_scatter.png": {
            "size_bytes": 73_903,
            "sha256": (
                "cc2cf79e1fdc1e8d40dab190aa5a9295"
                "abdeedcff6267787343235ddef62eba8"
            ),
        },
        "assets/reference_vs_transfer_equity.png": {
            "size_bytes": 151_817,
            "sha256": (
                "6c8b9b25937b196ce849c71e5af9a9f2"
                "562097d7cd05606391ceb27fabcb4b49"
            ),
        },
        "assets/representation_sensitivity.png": {
            "size_bytes": 52_227,
            "sha256": (
                "2bfdf8ec04879c4b4daeb97dd16d94d8"
                "befa98f3d4442700ab5184925d94c8a1"
            ),
        },
        "assets/roll_proximity_difference.png": {
            "size_bytes": 40_161,
            "sha256": (
                "ad323551aa398d90c99bc474b227f5551"
                "3244b669aa01bb210b17e1c88d97198"
            ),
        },
        "assets/session_coverage.png": {
            "size_bytes": 62_764,
            "sha256": (
                "7746fb4ab0311dc002dc00f31116c9c93"
                "dfb619a3dd1bcc2786365f1aa672ab2"
            ),
        },
        "assets/trade_agreement.png": {
            "size_bytes": 63_910,
            "sha256": (
                "4270d020fe1ff6c1dbdee925587baa41d4"
                "6521fd5d11a3531b2306ea3cf28646"
            ),
        },
        "candidate_transfer_metrics.csv": {
            "size_bytes": 2_103,
            "sha256": (
                "24e9d5f53faaafee4a09762f8525c089"
                "750ec38874bea3fdfff5affcaf9b97fb"
            ),
        },
        "ineligible_sessions.csv": {
            "size_bytes": 3_111,
            "sha256": (
                "2e240481dec836e418363468905e39892"
                "d7884d43b7751811c75639bba4dc75d"
            ),
        },
        "output_hashes.json": {
            "size_bytes": 2_773,
            "sha256": (
                "05731ab19c85eff57750dc126da9b2227"
                "937094b8bbb1d7da31c38847392194b"
            ),
        },
        "period_comparison.csv": {
            "size_bytes": 49_712,
            "sha256": (
                "a350f6c0041e811c8ed6f28f945bf547"
                "30d5b6b87aa122730428fe860532bacd"
            ),
        },
        "report.html": {
            "size_bytes": 3_334,
            "sha256": (
                "ca3d0cacef415bcff709f33cc811ce4e"
                "a9d41d9b095a0b8cd88f71033b957de9"
            ),
        },
        "report.md": {
            "size_bytes": 2_434,
            "sha256": (
                "dde6fad1c0d7454ffa84e2160a377a80"
                "914201797ee3531bcceff29840c528de"
            ),
        },
        "representation_sensitivity.csv": {
            "size_bytes": 509,
            "sha256": (
                "32a9db4fc8ed6eb2907e03bab5cf080e"
                "fd74b3f74e6ecfdb159a2d7b92c51bd9"
            ),
        },
        "roll_proximity_differences.csv": {
            "size_bytes": 78_370,
            "sha256": (
                "8af120663b531f2d5f3a00587a5ef358"
                "0781e51b66f2b5bfc6ebbab004dfecaa"
            ),
        },
        "session_alignment.csv": {
            "size_bytes": 1_001_712,
            "sha256": (
                "c0a81009b7af49a9714553d54b9045a3"
                "df60c3a32a876052c9a5987db8f40774"
            ),
        },
        "trade_alignment.csv": {
            "size_bytes": 981_790,
            "sha256": (
                "715ada134530a9c71238025afd0275fba"
                "3af31931ba8e56c08e89c18b9779d89"
            ),
        },
        "TRANSFER_DIAGNOSTIC_COMPLETE.json": {
            "size_bytes": 363,
            "sha256": (
                "aac79a622ee09618d304a0c7b5cf41d6"
                "f810c1fcf7ffb58b63f16fc2cf78e150"
            ),
        },
        "transfer_summary.json": {
            "size_bytes": 10_551,
            "sha256": (
                "8980bbac1f85ff1afc965430d5cae047"
                "901681bb0279109f8f251a4b8ee0fac4"
            ),
        },
        "transfer_trade_ledger.csv": {
            "size_bytes": 274_220,
            "sha256": (
                "fe01f55a278334eec62fc273844ec6c14"
                "c89080b47d418e4145da7646e21f010"
            ),
        },
    },
    "visual_review": {
        "all_seven_assets_opened": True,
        "readable": True,
        "opaque_white_backgrounds": True,
        "trade_agreement_difference_visible": True,
        "session_coverage_threshold_visible": True,
        "common_trade_pnl_diagonal_visible": True,
        "representation_sensitivity_visible": True,
    },
    "interpretation": {
        "known_overlap_transfer_diagnostic_only": True,
        "independent_edge_confirmation": False,
        "all_three_candidates_qualified": False,
        "qualified_candidate_count": 1,
        "failed_candidate_count": 2,
        "all_three_candidates_remain_separate": True,
        "no_candidate_ranked_or_selected": True,
        "automatic_candidate_promotion_authorized": False,
        "profitability_is_measurement_not_gate": True,
        "protected_history_validation_authorized": False,
        "earlier_and_2026_strategy_evidence_preserved": True,
        "strategy_parameter_or_gate_change_authorized": False,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
    },
    "next_research_boundary": {
        "exp023_frozen": True,
        "rerun_exp023_prohibited": True,
        "modify_exp023_outputs_prohibited": True,
        "protected_history_remains_locked": True,
        "candidate_rescue_or_retuning_prohibited": True,
        "threshold_change_prohibited": True,
        "winner_selection_under_exp023_prohibited": True,
        "new_experiment_id_required": True,
        "separate_preregistration_and_authorization_required": True,
        "paper_or_live_trading_not_authorized": True,
    },
}

EXPECTED_EXP023_CLOSURE_SHA256 = (
    "e3addce87c97b3cbaf1b5bddee0c9be2be0c75fedb45d3267ae293556e2f2c11"
)


def canonical_record_hash(record: dict[str, Any]) -> str:
    encoded = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def get_exp023_closure() -> dict[str, Any]:
    return deepcopy(EXP023_CLOSURE)


def validate_exp023_closure(
    candidate: dict[str, Any] | None = None,
) -> None:
    record = EXP023_CLOSURE if candidate is None else candidate
    if (
        record["experiment_id"] != "EXP-023"
        or record["closed_date"] != "2026-07-26"
        or record["research_status"] != "REVIEW"
        or record["classification"]
        != "TRANSFER_DIAGNOSTIC_COMPLETE_WITH_MATERIAL_DIFFERENCES"
    ):
        raise ValueError("EXP-023 closure identity changed.")
    if (
        canonical_record_hash(record)
        != EXPECTED_EXP023_CLOSURE_SHA256
    ):
        raise ValueError("EXP-023 closure record changed.")
