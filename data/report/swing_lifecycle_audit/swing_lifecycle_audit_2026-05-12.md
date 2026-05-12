# Swing Lifecycle Audit - 2026-05-12

- owner: `SwingFullLifecycleSelfImprovementChain`
- runtime_change: `false`
- selected_count: `3`
- csv_rows: `3`
- db_rows: `30`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- completed_rows: `0`
- submitted_unique_records: `0`
- simulated_order_unique_records: `18`
- observation_axis_status: `{'ready': 8, 'hold_sample': 2}`

## Lifecycle Funnel

| group | raw | unique_records |
| --- | ---: | ---: |
| `entry` | 629500 | 30 |
| `holding` | 0 | 0 |
| `scale_in` | 84 | 15 |
| `exit` | 64 | 16 |
| `other` | 151 | 1 |

## Key Stages

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 40 | 11 |
| `blocked_swing_gap` | 56344 | 3 |
| `blocked_swing_score_vpw` | 558903 | 28 |
| `gatekeeper_fast_reuse_bypass` | 40 | 11 |
| `swing_probe_discarded` | 14105 | 30 |
| `swing_probe_entry_candidate` | 34 | 11 |
| `swing_probe_exit_signal` | 32 | 16 |
| `swing_probe_holding_started` | 34 | 11 |
| `swing_probe_scale_in_order_assumed_filled` | 28 | 15 |
| `swing_probe_sell_order_assumed_filled` | 32 | 16 |
| `swing_probe_state_persisted` | 133 | 1 |
| `swing_probe_state_restored` | 18 | 1 |
| `swing_scale_in_micro_context_observed` | 28 | 15 |
| `swing_sim_scale_in_order_assumed_filled` | 28 | 15 |

## OFI/QI Micro Context

- sample_count: `116`
- stale_missing_unique_record_count: `3`
- stale_missing_ratio: `0.0776`
- stale_missing_reason_counts: `{'micro_missing': 9, 'micro_not_ready': 9, 'state_insufficient': 9, 'observer_unhealthy': 3}`
- stale_missing_reason_combination_counts: `{'micro_missing+micro_not_ready+state_insufficient': 6, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 3}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 2, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}`
- stale_missing_group_counts: `{'scale_in': 9}`
- stale_missing_group_unique_record_counts: `{'scale_in': 3}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 3, 'observer_unhealthy_with_other_reason': 3, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{}`
- scale_in_micro_state_counts: `{'neutral': 69, 'bullish': 6, 'insufficient': 9}`
- exit_micro_state_counts: `{'neutral': 30, 'bearish': 1, 'bullish': 1}`
- exit_smoothing_action_counts: `{}`

## Scale-In Observation

- action_groups: `{'AVG_DOWN': 72, 'PYRAMID': 12}`
- add_triggers: `{'swing_avg_down_ok': 48, 'swing_pyramid_ok': 8}`
- price_policies: `{'KEEP_EXISTING_PRICE': 23, 'market': 56, 'ALLOW_EXISTING_PRICE': 2, 'NO_CHANGE': 3}`
- add_ratio_summary: `{'count': 56, 'min': 0.1667, 'max': 1.0, 'avg': 0.5611392857142857, 'mean': 0.5611392857142857, 'p50': 0.5, 'p95': 1.0}`
- post_add_outcomes: `{'pending_followup': 56}`
- guard_blockers: `{}`
- zero_sample_reason: `None`

## Simulation Opportunity

- available: `True`
- sample_state: `hold_sample`
- rows: `90`
- closed_count: `0`
- winner_count: `0`
- loser_count: `0`

| family | rows | closed | winner | loser | avg_net_ret |
| --- | ---: | ---: | ---: | ---: | ---: |
| `swing_gatekeeper_reject_cooldown` | 30 | 0 | 0 | 0 | None |
| `swing_market_regime_sensitivity` | 30 | 0 | 0 | 0 | None |
| `swing_model_floor` | 3 | 0 | 0 | 0 | None |
| `swing_selection_top_k` | 27 | 0 | 0 | 0 | None |

## Observation Axes

| axis | stage | family | sample | status |
| --- | --- | --- | ---: | --- |
| `swing_selection_model_floor` | `selection` | `swing_model_floor` | 3 | `ready` |
| `swing_recommendation_db_load` | `db_load` | `swing_selection_top_k` | 3 | `ready` |
| `swing_gatekeeper_accept_reject` | `entry` | `swing_gatekeeper_accept_reject` | 22 | `ready` |
| `swing_gap_market_budget_price_qty` | `entry` | `swing_market_regime_sensitivity` | 60 | `ready` |
| `swing_holding_mfe_mae_defer` | `holding` | `swing_holding_flow_defer` | 0 | `hold_sample` |
| `swing_scale_in_avg_down_pyramid` | `scale_in` | `swing_pyramid_trigger` | 15 | `ready` |
| `swing_exit_post_sell_attribution` | `exit` | `swing_trailing_stop_time_stop` | 16 | `ready` |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `swing_entry_ofi_qi_execution_quality` | 0 | `hold_sample` |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `swing_scale_in_ofi_qi_confirmation` | 84 | `ready` |
| `swing_exit_ofi_qi_smoothing` | `holding_exit` | `swing_exit_ofi_qi_smoothing` | 32 | `ready` |

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
