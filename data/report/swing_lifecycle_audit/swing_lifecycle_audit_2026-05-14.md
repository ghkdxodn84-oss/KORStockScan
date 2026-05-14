# Swing Lifecycle Audit - 2026-05-14

- owner: `SwingFullLifecycleSelfImprovementChain`
- runtime_change: `false`
- selected_count: `3`
- csv_rows: `3`
- db_rows: `28`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- completed_rows: `0`
- submitted_unique_records: `0`
- simulated_order_unique_records: `17`
- observation_axis_status: `{'ready': 9, 'hold_sample': 1}`
- panic_state: `NORMAL`
- panic_active_sim_probe: `{'active_positions': 10, 'profit_sample': 10, 'avg_unrealized_profit_rate_pct': 1.5556, 'win_rate_pct': 80.0, 'wins': 8, 'losses': 1, 'flat': 1}`
- panic_origin_outcome: `{'blocked_swing_gap': {'count': 6, 'avg_profit_rate_pct': 0.918}, 'blocked_swing_score_vpw': {'count': 4, 'avg_profit_rate_pct': 2.5119}}`

## Lifecycle Funnel

| group | raw | unique_records |
| --- | ---: | ---: |
| `entry` | 436984 | 28 |
| `holding` | 28 | 2 |
| `scale_in` | 1068 | 12 |
| `exit` | 30 | 14 |
| `other` | 307 | 7 |

## Key Stages

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 74 | 12 |
| `blocked_swing_gap` | 156548 | 17 |
| `blocked_swing_score_vpw` | 270416 | 20 |
| `gatekeeper_fast_reuse_bypass` | 74 | 12 |
| `holding_flow_ofi_smoothing_applied` | 28 | 2 |
| `swing_probe_discarded` | 9842 | 28 |
| `swing_probe_entry_candidate` | 15 | 10 |
| `swing_probe_exit_signal` | 15 | 14 |
| `swing_probe_holding_started` | 15 | 10 |
| `swing_probe_scale_in_order_assumed_filled` | 1 | 1 |
| `swing_probe_sell_order_assumed_filled` | 15 | 14 |
| `swing_probe_state_persisted` | 43 | 1 |
| `swing_probe_state_restored` | 8 | 1 |
| `swing_reentry_counterfactual_after_loss` | 246 | 4 |
| `swing_same_symbol_loss_reentry_cooldown` | 7 | 6 |
| `swing_same_symbol_loss_reentry_cooldowns_restored` | 3 | 1 |
| `swing_scale_in_micro_context_observed` | 1066 | 12 |
| `swing_sim_scale_in_order_assumed_filled` | 1 | 1 |

## OFI/QI Micro Context

- sample_count: `1111`
- stale_missing_unique_record_count: `2`
- stale_missing_ratio: `0.0531`
- stale_missing_reason_counts: `{'micro_missing': 59, 'observer_unhealthy': 31, 'micro_not_ready': 2, 'state_insufficient': 2}`
- stale_missing_reason_combination_counts: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 2, 'micro_missing+observer_unhealthy': 29, 'micro_missing': 28}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 2, 'micro_missing+observer_unhealthy': 1}`
- stale_missing_group_counts: `{'scale_in': 31, 'exit': 28}`
- stale_missing_group_unique_record_counts: `{'scale_in': 2}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 31, 'observer_unhealthy_with_other_reason': 31, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{}`
- scale_in_micro_state_counts: `{'insufficient': 2, 'neutral': 1021, 'bearish': 27, 'bullish': 18}`
- exit_micro_state_counts: `{'bullish': 1, 'bearish': 4, 'neutral': 38}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 28}`

## Scale-In Observation

- action_groups: `{'AVG_DOWN': 788, 'PYRAMID': 280}`
- add_triggers: `{'swing_avg_down_ok': 2}`
- price_policies: `{'NO_CHANGE': 31, 'WAIT_FOR_PULLBACK': 27, 'KEEP_EXISTING_PRICE': 990, 'ALLOW_EXISTING_PRICE': 18, 'market': 2}`
- add_ratio_summary: `{'count': 2, 'min': 1.0, 'max': 1.0, 'avg': 1.0, 'mean': 1.0, 'p50': 1.0, 'p95': 1.0}`
- post_add_outcomes: `{'pending_followup': 2}`
- guard_blockers: `{}`
- zero_sample_reason: `None`

## Simulation Opportunity

- available: `True`
- sample_state: `hold_sample`
- rows: `84`
- closed_count: `0`
- winner_count: `0`
- loser_count: `0`

| family | rows | closed | winner | loser | avg_net_ret |
| --- | ---: | ---: | ---: | ---: | ---: |
| `swing_gatekeeper_reject_cooldown` | 28 | 0 | 0 | 0 | None |
| `swing_market_regime_sensitivity` | 28 | 0 | 0 | 0 | None |
| `swing_model_floor` | 3 | 0 | 0 | 0 | None |
| `swing_selection_top_k` | 25 | 0 | 0 | 0 | None |

## Observation Axes

| axis | stage | family | sample | status |
| --- | --- | --- | ---: | --- |
| `swing_selection_model_floor` | `selection` | `swing_model_floor` | 3 | `ready` |
| `swing_recommendation_db_load` | `db_load` | `swing_selection_top_k` | 3 | `ready` |
| `swing_gatekeeper_accept_reject` | `entry` | `swing_gatekeeper_accept_reject` | 22 | `ready` |
| `swing_gap_market_budget_price_qty` | `entry` | `swing_market_regime_sensitivity` | 64 | `ready` |
| `swing_holding_mfe_mae_defer` | `holding` | `swing_holding_flow_defer` | 2 | `ready` |
| `swing_scale_in_avg_down_pyramid` | `scale_in` | `swing_pyramid_trigger` | 12 | `ready` |
| `swing_exit_post_sell_attribution` | `exit` | `swing_trailing_stop_time_stop` | 14 | `ready` |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `swing_entry_ofi_qi_execution_quality` | 0 | `hold_sample` |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `swing_scale_in_ofi_qi_confirmation` | 1068 | `ready` |
| `swing_exit_ofi_qi_smoothing` | `holding_exit` | `swing_exit_ofi_qi_smoothing` | 28 | `ready` |

## AI Contract Audit

- schema_valid_rate: `None`
- parse_fail_count: `0`
- decision_disagreement_count: `0`
- latency_ms: `{'count': 0, 'min': None, 'max': None, 'avg': None, 'mean': None, 'p50': None, 'p95': None}`
- estimated_cost_krw: `{'count': 0, 'min': None, 'max': None, 'avg': None, 'mean': None, 'p50': None, 'p95': None}`
- prompt_types: `{}`

- `swing_gatekeeper_free_text_label` stage=`entry` severity=`medium`: Gatekeeper entry is currently reconstructed from report labels instead of a strict swing entry schema.
- `swing_holding_flow_scalping_prompt_reuse` stage=`holding_exit` severity=`medium`: Swing sell candidates can pass through holding-flow review that is named and tuned for scalping.
- `swing_scale_in_ai_contract_missing` stage=`scale_in` severity=`low`: Swing PYRAMID/AVG_DOWN observation is not yet represented by a dedicated AI proposal contract.
