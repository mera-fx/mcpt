from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any


EXP026_PREREGISTRATION: dict[str, Any] = {'schema_version': 1,
 'experiment_id': 'EXP-026',
 'title': 'Databento-Native NQ Multi-Family Strategy Development Tournament',
 'locked_date': '2026-07-27',
 'research_status': 'PRE_REGISTERED',
 'implementation_status': 'NOT_IMPLEMENTED',
 'execution_status': 'NOT_RUN',
 'purpose': 'Develop, compare and reduce a bounded set of NQ intraday candidates using '
            'the frozen Databento-derived EXP-022 continuous series while preserving '
            '2026 as a separate protected confirmation period.',
 'research_question': 'Which bounded gap-fade, premarket-continuation and '
                      'opening-drive parameter combinations provide the most useful '
                      'measured trade-offs across profitability, drawdown, '
                      'consistency, costs, stability and sample size before untouched '
                      '2026 confirmation?',
 'prior_result_disclosure': {'exp009_through_exp014_results_viewed': True,
                             'exp023_transfer_results_viewed': True,
                             'exp024_and_exp025_diagnostics_viewed': True,
                             'known_prior_finalists': ('gap_fade_0p50_1r',
                                                       'premarket_continuation_0p50_time',
                                                       'premarket_continuation_0p75_time'),
                             'known_2020_2025_results_exist': True,
                             'candidate_grid_informed_by_prior_research': True,
                             'cannot_claim_blind_discovery': True,
                             'cannot_claim_independent_confirmation': True,
                             'databento_native_2010_2019_strategy_results_viewed': False,
                             'protected_2026_strategy_results_viewed': False},
 'frozen_inputs': {'exp025_closure_commit': '14c6a32eb3f7f44c3196fa6296679c4b906150dd',
                   'exp025_closure_record_sha256': 'b386a0c45a81e40a3f9459f802882b8c749b6038e1d447b75d14d59acfea660c',
                   'exp025_classification': 'BLOCKED_DATA_UNAVAILABLE',
                   'historical_data_policy_path': 'research/HISTORICAL_DATA_POLICY.md',
                   'historical_data_policy_sha256': '638cd9da878590bd0cb08302a7fcde81d0fa3380d0d2262af4491c9da63a19b9',
                   'exp022_closure_commit': '9d157c8e7a6ba584a96cb5d37086672ad5b64ea1',
                   'exp022_closure_record_sha256': '1cc01baddeeae3acf81b0785923b581fad6aac0b6e36071d07d0d83d35bf588d',
                   'exp022_classification': 'QUALIFIED_AS_SELECTED_VOLUME_ROLL_CONTINUOUS_SERIES',
                   'selected_roll_method': 'VOL_GT_OUT_2S_E3',
                   'series_row_count': 5457606,
                   'series_first_timestamp_utc': '2010-06-06T22:00:00+00:00',
                   'series_last_timestamp_utc': '2026-07-23T23:59:00+00:00',
                   'series': ({'representation_id': 'BACKWARD_ADJUSTED',
                               'role': 'PRIMARY_RESEARCH_SERIES',
                               'path': 'results/EXP-022/selected_continuous_series/selected_roll_backward_adjusted.parquet',
                               'size_bytes': 71964074,
                               'sha256': '61ccb3621b53fa313147a866948ec1f2c7a6b36956d2ba26090162b518c30c84',
                               'semantic_sha256': '3c6fa83821183ca54bc547c555834ceb16a126be50f90d8c6db5684220929951'},
                              {'representation_id': 'UNADJUSTED',
                               'role': 'POST_SELECTION_REPRESENTATION_SENSITIVITY_ONLY',
                               'path': 'results/EXP-022/selected_continuous_series/selected_roll_unadjusted.parquet',
                               'size_bytes': 73760121,
                               'sha256': '606a69bbba4f4a5db3e0356d7b2849f9481e4555dc24cae4c6b9d1d12f673ab1',
                               'semantic_sha256': '29daf3f20b022fb69967349095eb9663bd04276cbc5743a65b1ecabc33113640'}),
                   'all_source_inputs_read_only': True,
                   'databento_api_calls': 0,
                   'credentials_required': False},
 'objective': {'bounded_parameter_development': True,
               'cross_family_comparison': True,
               'within_family_selection': True,
               'measurement_first': True,
               'fixed_controls_reported': True,
               'new_market_data_download': False,
               'roll_rule_selection': False,
               'price_adjustment_selection': False,
               'position_sizing_optimization': False,
               'portfolio_weight_optimization': False,
               'paper_trading': False,
               'live_trading': False},
 'research_periods': {'phase_a_development': {'session_start': '2010-06-07',
                                              'session_end': '2017-12-31',
                                              'purpose': 'Measure all 22 development '
                                                         'candidates and select up to '
                                                         'two candidates per family.',
                                              'results_viewed_before_lock': False},
                      'phase_b_internal_validation': {'session_start': '2018-01-01',
                                                      'session_end': '2019-12-31',
                                                      'purpose': 'Evaluate only '
                                                                 'Phase-A survivors '
                                                                 'and select up to one '
                                                                 'frozen finalist per '
                                                                 'family.',
                                                      'results_viewed_before_lock': False},
                      'phase_c_known_comparison': {'session_start': '2020-01-03',
                                                   'session_end': '2025-12-31',
                                                   'purpose': 'Measure frozen '
                                                              'finalists against '
                                                              'already-known '
                                                              'historical years '
                                                              'without reselection.',
                                                   'results_are_not_independent_confirmation': True},
                      'protected_exp027_confirmation': {'session_start': '2026-01-01',
                                                        'session_end': '2026-07-23',
                                                        'materialization_prohibited': True,
                                                        'strategy_calculation_prohibited': True,
                                                        'metadata_or_aggregate_result_inspection_prohibited': True}},
 'data_access_boundary': {'allowed_strategy_session_start': '2010-06-07',
                          'allowed_strategy_session_end': '2025-12-31',
                          'research_timezone': 'America/New_York',
                          'source_timestamp_timezone': 'UTC',
                          'session_start_local': '18:00',
                          'session_date_filter_before_materialization_required': True,
                          'maximum_materialized_trading_date': '2025-12-31',
                          'parquet_filter_pushdown_required': True,
                          'full_file_byte_hash_verification_permitted': True,
                          'parquet_metadata_inspection_permitted': True,
                          'protected_2026_row_deserialization_prohibited': True,
                          'no_network_access': True,
                          'no_databento_api_request': True,
                          'missing_minutes_filled': False,
                          'synthetic_bars_created': False,
                          'source_ohlcv_modified': False},
 'candidate_grid': {'family_count': 3,
                    'development_candidate_count': 22,
                    'control_candidate_count': 2,
                    'total_reported_candidate_count': 24,
                    'families': {'gap_fade': {'candidate_count': 6,
                                              'thresholds': (0.25, 0.5, 0.75),
                                              'exit_modes': ('prior_cash_close_or_time',
                                                             '1r_or_time'),
                                              'candidates': ({'candidate_id': 'gap_fade_0p25_prior_close',
                                                              'family_id': 'gap_fade',
                                                              'minimum_gap_fraction': 0.25,
                                                              'exit_mode': 'prior_cash_close_or_time',
                                                              'eligible_for_selection': True},
                                                             {'candidate_id': 'gap_fade_0p25_1r',
                                                              'family_id': 'gap_fade',
                                                              'minimum_gap_fraction': 0.25,
                                                              'exit_mode': '1r_or_time',
                                                              'eligible_for_selection': True},
                                                             {'candidate_id': 'gap_fade_0p50_prior_close',
                                                              'family_id': 'gap_fade',
                                                              'minimum_gap_fraction': 0.5,
                                                              'exit_mode': 'prior_cash_close_or_time',
                                                              'eligible_for_selection': True},
                                                             {'candidate_id': 'gap_fade_0p50_1r',
                                                              'family_id': 'gap_fade',
                                                              'minimum_gap_fraction': 0.5,
                                                              'exit_mode': '1r_or_time',
                                                              'eligible_for_selection': True},
                                                             {'candidate_id': 'gap_fade_0p75_prior_close',
                                                              'family_id': 'gap_fade',
                                                              'minimum_gap_fraction': 0.75,
                                                              'exit_mode': 'prior_cash_close_or_time',
                                                              'eligible_for_selection': True},
                                                             {'candidate_id': 'gap_fade_0p75_1r',
                                                              'family_id': 'gap_fade',
                                                              'minimum_gap_fraction': 0.75,
                                                              'exit_mode': '1r_or_time',
                                                              'eligible_for_selection': True})},
                                 'premarket_momentum_continuation': {'candidate_count': 8,
                                                                     'thresholds': (0.5,
                                                                                    0.625,
                                                                                    0.75,
                                                                                    0.875),
                                                                     'exit_modes': ('time',
                                                                                    '1p5r_or_time'),
                                                                     'candidates': ({'candidate_id': 'premarket_continuation_0p50_time',
                                                                                     'family_id': 'premarket_momentum_continuation',
                                                                                     'minimum_drive_fraction': 0.5,
                                                                                     'exit_mode': 'time',
                                                                                     'eligible_for_selection': True},
                                                                                    {'candidate_id': 'premarket_continuation_0p50_1p5r',
                                                                                     'family_id': 'premarket_momentum_continuation',
                                                                                     'minimum_drive_fraction': 0.5,
                                                                                     'exit_mode': '1p5r_or_time',
                                                                                     'eligible_for_selection': True},
                                                                                    {'candidate_id': 'premarket_continuation_0p625_time',
                                                                                     'family_id': 'premarket_momentum_continuation',
                                                                                     'minimum_drive_fraction': 0.625,
                                                                                     'exit_mode': 'time',
                                                                                     'eligible_for_selection': True},
                                                                                    {'candidate_id': 'premarket_continuation_0p625_1p5r',
                                                                                     'family_id': 'premarket_momentum_continuation',
                                                                                     'minimum_drive_fraction': 0.625,
                                                                                     'exit_mode': '1p5r_or_time',
                                                                                     'eligible_for_selection': True},
                                                                                    {'candidate_id': 'premarket_continuation_0p75_time',
                                                                                     'family_id': 'premarket_momentum_continuation',
                                                                                     'minimum_drive_fraction': 0.75,
                                                                                     'exit_mode': 'time',
                                                                                     'eligible_for_selection': True},
                                                                                    {'candidate_id': 'premarket_continuation_0p75_1p5r',
                                                                                     'family_id': 'premarket_momentum_continuation',
                                                                                     'minimum_drive_fraction': 0.75,
                                                                                     'exit_mode': '1p5r_or_time',
                                                                                     'eligible_for_selection': True},
                                                                                    {'candidate_id': 'premarket_continuation_0p875_time',
                                                                                     'family_id': 'premarket_momentum_continuation',
                                                                                     'minimum_drive_fraction': 0.875,
                                                                                     'exit_mode': 'time',
                                                                                     'eligible_for_selection': True},
                                                                                    {'candidate_id': 'premarket_continuation_0p875_1p5r',
                                                                                     'family_id': 'premarket_momentum_continuation',
                                                                                     'minimum_drive_fraction': 0.875,
                                                                                     'exit_mode': '1p5r_or_time',
                                                                                     'eligible_for_selection': True})},
                                 'opening_drive_continuation': {'candidate_count': 8,
                                                                'thresholds': (0.25,
                                                                               0.5,
                                                                               0.75,
                                                                               1.0),
                                                                'exit_modes': ('time',
                                                                               '1p5r_or_time'),
                                                                'candidates': ({'candidate_id': 'opening_drive_0p25_time',
                                                                                'family_id': 'opening_drive_continuation',
                                                                                'minimum_drive_fraction': 0.25,
                                                                                'exit_mode': 'time',
                                                                                'eligible_for_selection': True},
                                                                               {'candidate_id': 'opening_drive_0p25_1p5r',
                                                                                'family_id': 'opening_drive_continuation',
                                                                                'minimum_drive_fraction': 0.25,
                                                                                'exit_mode': '1p5r_or_time',
                                                                                'eligible_for_selection': True},
                                                                               {'candidate_id': 'opening_drive_0p50_time',
                                                                                'family_id': 'opening_drive_continuation',
                                                                                'minimum_drive_fraction': 0.5,
                                                                                'exit_mode': 'time',
                                                                                'eligible_for_selection': True},
                                                                               {'candidate_id': 'opening_drive_0p50_1p5r',
                                                                                'family_id': 'opening_drive_continuation',
                                                                                'minimum_drive_fraction': 0.5,
                                                                                'exit_mode': '1p5r_or_time',
                                                                                'eligible_for_selection': True},
                                                                               {'candidate_id': 'opening_drive_0p75_time',
                                                                                'family_id': 'opening_drive_continuation',
                                                                                'minimum_drive_fraction': 0.75,
                                                                                'exit_mode': 'time',
                                                                                'eligible_for_selection': True},
                                                                               {'candidate_id': 'opening_drive_0p75_1p5r',
                                                                                'family_id': 'opening_drive_continuation',
                                                                                'minimum_drive_fraction': 0.75,
                                                                                'exit_mode': '1p5r_or_time',
                                                                                'eligible_for_selection': True},
                                                                               {'candidate_id': 'opening_drive_1p00_time',
                                                                                'family_id': 'opening_drive_continuation',
                                                                                'minimum_drive_fraction': 1.0,
                                                                                'exit_mode': 'time',
                                                                                'eligible_for_selection': True},
                                                                               {'candidate_id': 'opening_drive_1p00_1p5r',
                                                                                'family_id': 'opening_drive_continuation',
                                                                                'minimum_drive_fraction': 1.0,
                                                                                'exit_mode': '1p5r_or_time',
                                                                                'eligible_for_selection': True})}},
                    'development_candidates': ({'candidate_id': 'gap_fade_0p25_prior_close',
                                                'family_id': 'gap_fade',
                                                'minimum_gap_fraction': 0.25,
                                                'exit_mode': 'prior_cash_close_or_time',
                                                'eligible_for_selection': True},
                                               {'candidate_id': 'gap_fade_0p25_1r',
                                                'family_id': 'gap_fade',
                                                'minimum_gap_fraction': 0.25,
                                                'exit_mode': '1r_or_time',
                                                'eligible_for_selection': True},
                                               {'candidate_id': 'gap_fade_0p50_prior_close',
                                                'family_id': 'gap_fade',
                                                'minimum_gap_fraction': 0.5,
                                                'exit_mode': 'prior_cash_close_or_time',
                                                'eligible_for_selection': True},
                                               {'candidate_id': 'gap_fade_0p50_1r',
                                                'family_id': 'gap_fade',
                                                'minimum_gap_fraction': 0.5,
                                                'exit_mode': '1r_or_time',
                                                'eligible_for_selection': True},
                                               {'candidate_id': 'gap_fade_0p75_prior_close',
                                                'family_id': 'gap_fade',
                                                'minimum_gap_fraction': 0.75,
                                                'exit_mode': 'prior_cash_close_or_time',
                                                'eligible_for_selection': True},
                                               {'candidate_id': 'gap_fade_0p75_1r',
                                                'family_id': 'gap_fade',
                                                'minimum_gap_fraction': 0.75,
                                                'exit_mode': '1r_or_time',
                                                'eligible_for_selection': True},
                                               {'candidate_id': 'premarket_continuation_0p50_time',
                                                'family_id': 'premarket_momentum_continuation',
                                                'minimum_drive_fraction': 0.5,
                                                'exit_mode': 'time',
                                                'eligible_for_selection': True},
                                               {'candidate_id': 'premarket_continuation_0p50_1p5r',
                                                'family_id': 'premarket_momentum_continuation',
                                                'minimum_drive_fraction': 0.5,
                                                'exit_mode': '1p5r_or_time',
                                                'eligible_for_selection': True},
                                               {'candidate_id': 'premarket_continuation_0p625_time',
                                                'family_id': 'premarket_momentum_continuation',
                                                'minimum_drive_fraction': 0.625,
                                                'exit_mode': 'time',
                                                'eligible_for_selection': True},
                                               {'candidate_id': 'premarket_continuation_0p625_1p5r',
                                                'family_id': 'premarket_momentum_continuation',
                                                'minimum_drive_fraction': 0.625,
                                                'exit_mode': '1p5r_or_time',
                                                'eligible_for_selection': True},
                                               {'candidate_id': 'premarket_continuation_0p75_time',
                                                'family_id': 'premarket_momentum_continuation',
                                                'minimum_drive_fraction': 0.75,
                                                'exit_mode': 'time',
                                                'eligible_for_selection': True},
                                               {'candidate_id': 'premarket_continuation_0p75_1p5r',
                                                'family_id': 'premarket_momentum_continuation',
                                                'minimum_drive_fraction': 0.75,
                                                'exit_mode': '1p5r_or_time',
                                                'eligible_for_selection': True},
                                               {'candidate_id': 'premarket_continuation_0p875_time',
                                                'family_id': 'premarket_momentum_continuation',
                                                'minimum_drive_fraction': 0.875,
                                                'exit_mode': 'time',
                                                'eligible_for_selection': True},
                                               {'candidate_id': 'premarket_continuation_0p875_1p5r',
                                                'family_id': 'premarket_momentum_continuation',
                                                'minimum_drive_fraction': 0.875,
                                                'exit_mode': '1p5r_or_time',
                                                'eligible_for_selection': True},
                                               {'candidate_id': 'opening_drive_0p25_time',
                                                'family_id': 'opening_drive_continuation',
                                                'minimum_drive_fraction': 0.25,
                                                'exit_mode': 'time',
                                                'eligible_for_selection': True},
                                               {'candidate_id': 'opening_drive_0p25_1p5r',
                                                'family_id': 'opening_drive_continuation',
                                                'minimum_drive_fraction': 0.25,
                                                'exit_mode': '1p5r_or_time',
                                                'eligible_for_selection': True},
                                               {'candidate_id': 'opening_drive_0p50_time',
                                                'family_id': 'opening_drive_continuation',
                                                'minimum_drive_fraction': 0.5,
                                                'exit_mode': 'time',
                                                'eligible_for_selection': True},
                                               {'candidate_id': 'opening_drive_0p50_1p5r',
                                                'family_id': 'opening_drive_continuation',
                                                'minimum_drive_fraction': 0.5,
                                                'exit_mode': '1p5r_or_time',
                                                'eligible_for_selection': True},
                                               {'candidate_id': 'opening_drive_0p75_time',
                                                'family_id': 'opening_drive_continuation',
                                                'minimum_drive_fraction': 0.75,
                                                'exit_mode': 'time',
                                                'eligible_for_selection': True},
                                               {'candidate_id': 'opening_drive_0p75_1p5r',
                                                'family_id': 'opening_drive_continuation',
                                                'minimum_drive_fraction': 0.75,
                                                'exit_mode': '1p5r_or_time',
                                                'eligible_for_selection': True},
                                               {'candidate_id': 'opening_drive_1p00_time',
                                                'family_id': 'opening_drive_continuation',
                                                'minimum_drive_fraction': 1.0,
                                                'exit_mode': 'time',
                                                'eligible_for_selection': True},
                                               {'candidate_id': 'opening_drive_1p00_1p5r',
                                                'family_id': 'opening_drive_continuation',
                                                'minimum_drive_fraction': 1.0,
                                                'exit_mode': '1p5r_or_time',
                                                'eligible_for_selection': True}),
                    'control_candidates': ({'candidate_id': 'orb_control_exp005_15m_both_time',
                                            'family_id': 'opening_range_breakout_control',
                                            'source_experiment': 'EXP-005',
                                            'opening_range_minutes': 15,
                                            'direction_mode': 'both',
                                            'last_signal_close_time_new_york': '11:55',
                                            'exit_mode': '15:55_time',
                                            'eligible_for_selection': False},
                                           {'candidate_id': 'orb_control_exp007_30m_long_1r',
                                            'family_id': 'opening_range_breakout_control',
                                            'source_experiment': 'EXP-007',
                                            'opening_range_minutes': 30,
                                            'direction_mode': 'long_only',
                                            'last_signal_close_time_new_york': '13:55',
                                            'exit_mode': '1r_or_14:00_time',
                                            'eligible_for_selection': False}),
                    'candidate_additions_after_registration_prohibited': True,
                    'candidate_removals_after_registration_prohibited': True,
                    'parameter_changes_after_registration_prohibited': True},
 'strategy_definitions': {'gap_fade': {'previous_cash_close': 'Final one-minute close '
                                                              'before 16:00 on the '
                                                              'immediately preceding '
                                                              'eligible cash session.',
                                       'previous_cash_range': '09:30 through 15:59 '
                                                              'high minus low on that '
                                                              'same previous cash '
                                                              'session.',
                                       'gap_fraction': 'Absolute current 09:30 open '
                                                       'minus previous cash close, '
                                                       'divided by previous cash '
                                                       'range.',
                                       'setup_operator': '>=',
                                       'signal': 'The completed 09:30-09:35 bar closes '
                                                 'in the direction opposite the '
                                                 'opening gap.',
                                       'entry': '09:35 five-minute bar open.',
                                       'stop': 'Outer extreme of the completed '
                                               '09:30-09:35 bar.',
                                       'targets': 'Previous cash close or one times '
                                                  'initial risk, according to '
                                                  'candidate exit_mode.',
                                       'forced_flat': '15:55 one-minute bar open.',
                                       'direction_mode': 'both'},
                          'premarket_momentum_continuation': {'premarket_window': '08:00 '
                                                                                  'through '
                                                                                  '09:29',
                                                              'drive_fraction': 'Absolute '
                                                                                '09:29 '
                                                                                'close '
                                                                                'minus '
                                                                                '08:00 '
                                                                                'open, '
                                                                                'divided '
                                                                                'by '
                                                                                'the '
                                                                                '08:00-09:29 '
                                                                                'high-low '
                                                                                'range.',
                                                              'setup_operator': '>=',
                                                              'signal': 'The completed '
                                                                        '09:30-09:35 '
                                                                        'bar closes in '
                                                                        'the same '
                                                                        'direction as '
                                                                        'the premarket '
                                                                        'move.',
                                                              'entry': '09:35 '
                                                                       'five-minute '
                                                                       'bar open.',
                                                              'stop': 'Opposite '
                                                                      'extreme of the '
                                                                      'completed '
                                                                      '09:30-09:35 '
                                                                      'bar.',
                                                              'targets': 'No target or '
                                                                         '1.5 times '
                                                                         'initial '
                                                                         'risk, '
                                                                         'according to '
                                                                         'candidate '
                                                                         'exit_mode.',
                                                              'forced_flat': '15:55 '
                                                                             'one-minute '
                                                                             'bar '
                                                                             'open.',
                                                              'direction_mode': 'both'},
                          'opening_drive_continuation': {'measurement_window': '09:30 '
                                                                               'through '
                                                                               '09:59',
                                                         'drive_fraction': 'Absolute '
                                                                           'first-30-minute '
                                                                           'close '
                                                                           'minus '
                                                                           'open, '
                                                                           'divided by '
                                                                           'the '
                                                                           'first-30-minute '
                                                                           'high-low '
                                                                           'range.',
                                                         'setup_operator': '>=',
                                                         'direction': 'Trade in the '
                                                                      'sign of the '
                                                                      'first-30-minute '
                                                                      'return.',
                                                         'entry': '10:00 five-minute '
                                                                  'bar open.',
                                                         'stop': 'Opposite side of the '
                                                                 'first 30-minute '
                                                                 'opening range.',
                                                         'targets': 'No target or 1.5 '
                                                                    'times initial '
                                                                    'risk, according '
                                                                    'to candidate '
                                                                    'exit_mode.',
                                                         'forced_flat': '15:55 '
                                                                        'one-minute '
                                                                        'bar open.',
                                                         'direction_mode': 'both'},
                          'controls': {'exp005': 'Unchanged 15-minute both-direction '
                                                 'ORB, first eligible close breakout, '
                                                 'entries through 12:00, opening-range '
                                                 'opposite-side stop and 15:55 exit.',
                                       'exp007': 'Unchanged 30-minute long-only ORB, '
                                                 'one-R target, entries through 13:55 '
                                                 'and 14:00 exit.',
                                       'controls_are_not_selection_candidates': True}},
 'session_and_execution_rules': {'source_resolution': '1 minute',
                                 'signal_resolution': '5 minutes',
                                 'five_minute_bars_use_observed_minutes_only': True,
                                 'completed_signal_bars_only': True,
                                 'maximum_trades_per_candidate_per_session': 1,
                                 'same_day_reentry': False,
                                 'overnight_positions': False,
                                 'entry_uses_actual_open': True,
                                 'entry_minute_can_exit': True,
                                 'evaluate_exit_minutes_chronologically': True,
                                 'same_minute_stop_target_rule': 'STOP_FIRST_CONSERVATIVE',
                                 'stop_gap_rule': 'If a one-minute bar opens through '
                                                  'the stop, fill at that opening '
                                                  'price; otherwise fill at the stop '
                                                  'boundary.',
                                 'target_gap_rule': 'No favourable target price '
                                                    'improvement.',
                                 'invalid_nonpositive_risk_trade': 'DO_NOT_ENTER',
                                 'candidate_native_eligibility_is_primary': True,
                                 'all_family_common_session_sensitivity_is_secondary': True},
 'position_and_cost_model': {'market': 'NQ',
                             'position_size': 'FIXED_ONE_CONTRACT',
                             'multiplier_usd_per_point': 20.0,
                             'tick_size_points': 0.25,
                             'tick_value_usd': 5.0,
                             'fees_usd_per_side': 2.5,
                             'base_slippage_ticks_per_side': 1.0,
                             'base_round_trip_cost_usd': 15.0,
                             'reference_capital_usd': 100000.0,
                             'cost_sensitivity_ticks_per_side': (0, 1, 2, 3),
                             'position_sizing_optimization': False},
 'phase_sequence': {'phase_a': {'mode': 'DEVELOPMENT',
                                'candidate_population': 'All 22 development candidates '
                                                        'plus two controls.',
                                'select_up_to_per_family': 2,
                                'rank': ('trade_profit_factor descending',
                                         'net_profit_to_maximum_drawdown descending',
                                         'net_profit_usd descending',
                                         'completed_trades descending',
                                         'candidate_id ascending'),
                                'zero_trade_candidates_are_not_selectable': True,
                                'no_minimum_profit_gate': True,
                                'completion_record_must_be_committed_before_phase_b': True},
                    'phase_b': {'mode': 'INTERNAL_VALIDATION',
                                'candidate_population': 'Phase-A survivors only plus '
                                                        'two controls.',
                                'select_up_to_per_family': 1,
                                'rank': ('profitable_internal_validation_years '
                                         'descending',
                                         'internal_validation_trade_profit_factor '
                                         'descending',
                                         'internal_validation_net_profit_to_drawdown '
                                         'descending',
                                         'internal_validation_net_profit_usd '
                                         'descending',
                                         'development_trade_profit_factor descending',
                                         'candidate_id ascending'),
                                'zero_internal_validation_trade_candidates_not_selectable': True,
                                'no_minimum_profit_gate': True,
                                'finalist_count_minimum': 0,
                                'finalist_count_maximum': 3,
                                'completion_record_must_be_committed_before_phase_c': True},
                    'phase_c': {'mode': 'KNOWN_COMPARISON',
                                'candidate_population': 'Frozen Phase-B finalists plus '
                                                        'two controls.',
                                'candidate_reselection': False,
                                'parameter_changes': False,
                                'known_period_does_not_change_finalist_identity': True,
                                'known_period_is_not_confirmation': True}},
 'robustness_plan': {'selection_aware_mcpt': {'enabled': True,
                                              'phase': 'PHASE_B',
                                              'permutations': 1000,
                                              'random_seed': 26026,
                                              'all_22_candidates_inside_each_permutation': True,
                                              'full_phase_a_and_phase_b_selection_repeated': True,
                                              'primary_statistic': 'sum of selected '
                                                                   'family-finalist '
                                                                   'internal-validation '
                                                                   'net '
                                                                   'profit-to-drawdown '
                                                                   'ranks',
                                              'plus_one_p_value': True,
                                              'exact_serial_parallel_parity_required': True,
                                              'decision_gate': False},
                     'bootstrap': {'enabled': True,
                                   'phase': 'PHASE_B',
                                   'resamples': 10000,
                                   'random_seed': 26027,
                                   'confidence_level': 0.95,
                                   'session_block_resampling': True,
                                   'decision_gate': False},
                     'anchored_walk_forward': {'enabled': True,
                                               'test_years': (2014,
                                                              2015,
                                                              2016,
                                                              2017,
                                                              2018,
                                                              2019),
                                               'training_start': '2010-06-07',
                                               'selection_repeated_inside_each_training_window': True,
                                               'all_22_candidates_available_inside_each_fold': True,
                                               'training_end_precedes_test_start': True,
                                               'decision_gate': False},
                     'parameter_neighbour_stability': {'enabled': True,
                                                       'threshold_neighbours_reported': True,
                                                       'paired_exit_mode_neighbours_reported': True,
                                                       'family_surface_tables_required': True,
                                                       'decision_gate': False},
                     'representation_sensitivity': {'primary_selection_on_backward_adjusted_only': True,
                                                    'unadjusted_run_after_finalist_freeze_only': True,
                                                    'unadjusted_results_cannot_change_selection': True},
                     'known_comparison_years': (2020, 2021, 2022, 2023, 2024, 2025)},
 'measurement_plan': {'metric_columns': ('ALL_TRADES', 'LONG_TRADES', 'SHORT_TRADES'),
                      'performance_metrics': ('net_profit_usd',
                                              'gross_profit_usd',
                                              'gross_loss_usd',
                                              'trade_profit_factor',
                                              'completed_trades',
                                              'win_rate',
                                              'average_trade_usd',
                                              'median_trade_usd',
                                              'average_winner_usd',
                                              'average_loser_usd',
                                              'payoff_ratio'),
                      'risk_metrics': ('maximum_drawdown_usd',
                                       'maximum_drawdown_percent',
                                       'net_profit_to_drawdown',
                                       'drawdown_duration',
                                       'recovery_duration',
                                       'maximum_consecutive_losses',
                                       'worst_20_trade_result',
                                       'worst_50_trade_result',
                                       'worst_100_trade_result'),
                      'consistency_metrics': ('profitable_year_count',
                                              'profitable_month_fraction',
                                              'rolling_100_trade_profit_factor',
                                              'top_1_trade_profit_share',
                                              'top_5_trade_profit_share',
                                              'top_10_trade_profit_share'),
                      'practical_metrics': ('trades_per_year',
                                            'session_participation_rate',
                                            'average_holding_minutes',
                                            'median_holding_minutes',
                                            'average_trade_to_round_trip_cost',
                                            'entry_time_distribution',
                                            'exit_reason_distribution'),
                      'all_candidates_remain_visible': True,
                      'single_composite_score': False,
                      'formal_accept_reject_gates': False,
                      'automatic_trading_winner': False},
 'reporting_requirements': {'vertical_full_width_layout': True,
                            'plain_english_strategy_rules': True,
                            'candidate_grid_visible': True,
                            'phase_boundaries_visible': True,
                            'all_long_short_metrics_table': True,
                            'full_width_equity_curves': True,
                            'full_width_drawdown_curves': True,
                            'annual_results': True,
                            'monthly_results': True,
                            'trade_distributions': True,
                            'cost_sensitivity': True,
                            'parameter_stability': True,
                            'walk_forward': True,
                            'bootstrap': True,
                            'mcpt': True,
                            'known_2020_2025_status_disclosed': True,
                            'protected_2026_status_visible': True,
                            'positive_numbers_use_neutral_text': True,
                            'adverse_numbers_use_red_text': True,
                            'green_reserved_for_status_words': True,
                            'charts_use_opaque_white_canvas': True},
 'required_outputs': {'phase_a': ('development_summary.json',
                                  'candidate_registry.csv',
                                  'development_metrics.csv',
                                  'development_annual_results.csv',
                                  'phase_a_survivors.json',
                                  'output_hashes.json',
                                  'report.md',
                                  'PHASE_A_COMPLETE.json'),
                      'phase_b': ('internal_validation_summary.json',
                                  'internal_validation_metrics.csv',
                                  'selected_finalists.json',
                                  'walk_forward_results.csv',
                                  'bootstrap_summary.csv',
                                  'mcpt_summary.json',
                                  'parameter_stability.csv',
                                  'output_hashes.json',
                                  'report.md',
                                  'report.html',
                                  'PHASE_B_COMPLETE.json'),
                      'phase_c': ('known_comparison_summary.json',
                                  'known_comparison_metrics.csv',
                                  'annual_results.csv',
                                  'monthly_results.csv',
                                  'cost_sensitivity.csv',
                                  'representation_sensitivity.csv',
                                  'trade_distribution.csv',
                                  'drawdown_episodes.csv',
                                  'output_hashes.json',
                                  'report.md',
                                  'report.html',
                                  'PHASE_C_COMPLETE.json')},
 'hard_checks': ('exp025_closure_commit_and_hash_match',
                 'historical_data_policy_hash_matches',
                 'exp022_closure_commit_and_hash_match',
                 'exp022_selected_series_byte_hashes_match',
                 'exp022_selected_series_semantic_hashes_match',
                 'source_series_remain_read_only',
                 'no_databento_api_or_network_access',
                 'primary_representation_is_backward_adjusted',
                 'unadjusted_representation_is_audit_only',
                 'candidate_family_count_is_three',
                 'development_candidate_count_is_twenty_two',
                 'control_candidate_count_is_two',
                 'candidate_ids_are_unique',
                 'controls_are_not_selection_eligible',
                 'candidate_grid_is_unchanged_after_registration',
                 'phase_a_reads_only_development_period',
                 'phase_a_selection_is_committed_before_phase_b',
                 'phase_b_reads_only_development_and_internal_validation',
                 'phase_b_selection_is_committed_before_phase_c',
                 'phase_c_uses_frozen_finalists_without_reselection',
                 'protected_2026_values_are_not_materialized',
                 'session_date_filter_is_applied_before_materialization',
                 'missing_minutes_are_not_filled',
                 'synthetic_bars_are_not_created',
                 'five_minute_bars_use_observed_minutes_only',
                 'strategy_rules_match_registered_definitions',
                 'baseline_cost_model_is_unchanged',
                 'same_minute_stop_target_rule_is_conservative',
                 'all_long_short_and_total_metrics_are_reported',
                 'selection_aware_mcpt_repeats_full_selection',
                 'walk_forward_repeats_selection_inside_training_folds',
                 'bootstrap_seed_and_resample_count_are_fixed',
                 'parameter_neighbour_stability_is_reported',
                 'all_candidates_remain_visible',
                 'no_composite_score_is_used',
                 'no_paper_or_live_trading_occurs',
                 'required_outputs_and_hashes_are_complete'),
 'hard_check_count': 37,
 'execution_boundary': {'result_free_implementation_commit_required': True,
                        'implementation_preflight_required': True,
                        'separate_phase_a_authorization_commit_required': True,
                        'phase_a_completion_commit_required': True,
                        'separate_phase_b_authorization_commit_required': True,
                        'phase_b_completion_commit_required': True,
                        'separate_phase_c_authorization_commit_required': True,
                        'one_authorized_run_per_phase': True,
                        'independent_rebuild_required_per_phase': True,
                        'phase_rerun_after_completion': False,
                        'new_databento_download': False,
                        'databento_api_calls': 0,
                        'network_access': False,
                        'order_api_access': False},
 'prohibited_actions': {'modify_exp022_outputs': True,
                        'modify_exp025_closure_or_policy': True,
                        'reselect_roll_rule': True,
                        'change_price_adjustment_method': True,
                        'add_or_remove_candidates_after_registration': True,
                        'change_candidate_parameters_after_registration': True,
                        'use_controls_in_selection': True,
                        'access_phase_b_before_phase_a_commit': True,
                        'access_phase_c_before_phase_b_commit': True,
                        'materialize_protected_2026_market_values': True,
                        'calculate_protected_2026_strategy_results': True,
                        'use_known_2020_2025_results_for_reselection': True,
                        'fill_or_repair_missing_bars': True,
                        'optimize_position_size': True,
                        'optimize_portfolio_weights': True,
                        'paper_trading': True,
                        'live_trading': True},
 'interpretation': {'exploratory_development': True,
                    'measurement_first': True,
                    'prior_parameter_knowledge_disclosed': True,
                    'known_comparison_is_not_confirmation': True,
                    'finalists_are_measurement_leaders_not_validated_edges': True,
                    'exp027_required_for_protected_confirmation': True,
                    'no_strategy_is_accepted_for_trading_by_exp026': True,
                    'paper_trading_authorized': False,
                    'live_trading_authorized': False}}

EXPECTED_EXP026_PREREGISTRATION_SHA256 = (
    "bbd2e6d8bb50c135d0c6ca04873eed2876c4e7db6a2714b91a934dcf554331a0"
)


def canonical_record_hash(
    record: dict[str, Any],
) -> str:
    encoded = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def get_exp026_preregistration() -> dict[str, Any]:
    return deepcopy(EXP026_PREREGISTRATION)


def validate_exp026_preregistration(
    candidate: dict[str, Any] | None = None,
) -> None:
    record = (
        EXP026_PREREGISTRATION
        if candidate is None
        else candidate
    )

    if (
        record.get("experiment_id") != "EXP-026"
        or record.get("locked_date") != "2026-07-27"
        or record.get("research_status") != "PRE_REGISTERED"
        or record.get("implementation_status")
        != "NOT_IMPLEMENTED"
        or record.get("execution_status") != "NOT_RUN"
    ):
        raise ValueError(
            "EXP-026 preregistration identity changed."
        )

    frozen = record["frozen_inputs"]

    if (
        frozen["exp025_closure_commit"]
        != "14c6a32eb3f7f44c3196fa6296679c4b906150dd"
        or frozen["exp025_closure_record_sha256"]
        != "b386a0c45a81e40a3f9459f802882b8c749b6038e1d447b75d14d59acfea660c"
        or frozen["historical_data_policy_sha256"]
        != "638cd9da878590bd0cb08302a7fcde81d0fa3380d0d2262af4491c9da63a19b9"
        or frozen["exp022_closure_commit"]
        != "9d157c8e7a6ba584a96cb5d37086672ad5b64ea1"
        or frozen["exp022_closure_record_sha256"]
        != "1cc01baddeeae3acf81b0785923b581fad6aac0b6e36071d07d0d83d35bf588d"
        or frozen["series_row_count"] != 5_457_606
    ):
        raise ValueError(
            "EXP-026 frozen input boundary changed."
        )

    periods = record["research_periods"]

    if (
        periods["phase_a_development"]["session_start"]
        != "2010-06-07"
        or periods["phase_a_development"]["session_end"]
        != "2017-12-31"
        or periods["phase_b_internal_validation"][
            "session_start"
        ]
        != "2018-01-01"
        or periods["phase_b_internal_validation"][
            "session_end"
        ]
        != "2019-12-31"
        or periods["phase_c_known_comparison"][
            "session_start"
        ]
        != "2020-01-03"
        or periods["phase_c_known_comparison"][
            "session_end"
        ]
        != "2025-12-31"
        or periods["protected_exp027_confirmation"][
            "materialization_prohibited"
        ]
        is not True
    ):
        raise ValueError(
            "EXP-026 research-period boundary changed."
        )

    grid = record["candidate_grid"]
    candidates = tuple(
        grid["development_candidates"]
    )
    controls = tuple(
        grid["control_candidates"]
    )
    candidate_ids = [
        item["candidate_id"]
        for item in candidates
    ]
    control_ids = [
        item["candidate_id"]
        for item in controls
    ]

    if (
        grid["family_count"] != 3
        or grid["development_candidate_count"] != 22
        or grid["control_candidate_count"] != 2
        or grid["total_reported_candidate_count"] != 24
        or len(candidates) != 22
        or len(controls) != 2
        or len(candidate_ids) != len(set(candidate_ids))
        or set(candidate_ids) & set(control_ids)
        or any(
            item["eligible_for_selection"] is not True
            for item in candidates
        )
        or any(
            item["eligible_for_selection"] is not False
            for item in controls
        )
    ):
        raise ValueError(
            "EXP-026 candidate grid changed."
        )

    family_counts = {
        family_id: sum(
            item["family_id"] == family_id
            for item in candidates
        )
        for family_id in (
            "gap_fade",
            "premarket_momentum_continuation",
            "opening_drive_continuation",
        )
    }

    if family_counts != {
        "gap_fade": 6,
        "premarket_momentum_continuation": 8,
        "opening_drive_continuation": 8,
    }:
        raise ValueError(
            "EXP-026 family candidate counts changed."
        )

    phase = record["phase_sequence"]

    if (
        phase["phase_a"]["select_up_to_per_family"] != 2
        or phase["phase_b"]["select_up_to_per_family"] != 1
        or phase["phase_b"]["finalist_count_maximum"] != 3
        or phase["phase_c"]["candidate_reselection"] is not False
        or phase["phase_c"][
            "known_period_does_not_change_finalist_identity"
        ]
        is not True
    ):
        raise ValueError(
            "EXP-026 selection sequence changed."
        )

    boundary = record["execution_boundary"]
    prohibited = record["prohibited_actions"]

    if (
        boundary[
            "result_free_implementation_commit_required"
        ]
        is not True
        or boundary[
            "separate_phase_a_authorization_commit_required"
        ]
        is not True
        or boundary[
            "separate_phase_b_authorization_commit_required"
        ]
        is not True
        or boundary[
            "separate_phase_c_authorization_commit_required"
        ]
        is not True
        or boundary["databento_api_calls"] != 0
        or prohibited[
            "materialize_protected_2026_market_values"
        ]
        is not True
        or prohibited["paper_trading"] is not True
        or prohibited["live_trading"] is not True
    ):
        raise ValueError(
            "EXP-026 execution boundary changed."
        )

    if (
        len(record["hard_checks"])
        != record["hard_check_count"]
    ):
        raise ValueError(
            "EXP-026 hard-check count changed."
        )

    if (
        canonical_record_hash(record)
        != EXPECTED_EXP026_PREREGISTRATION_SHA256
    ):
        raise ValueError(
            "EXP-026 preregistration record changed."
        )
