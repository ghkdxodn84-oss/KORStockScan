# Swing Lifecycle Audit - 2026-05-13

- owner: `SwingFullLifecycleSelfImprovementChain`
- runtime_change: `false`
- selected_count: `3`
- csv_rows: `3`
- db_rows: `27`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- completed_rows: `0`
- submitted_unique_records: `0`
- simulated_order_unique_records: `20`
- observation_axis_status: `{'ready': 8, 'hold_sample': 2}`
- panic_state: `RECOVERY_WATCH`
- panic_active_sim_probe: `{'active_positions': 11, 'profit_sample': 11, 'avg_unrealized_profit_rate_pct': 0.8023, 'win_rate_pct': 54.5, 'wins': 6, 'losses': 3, 'flat': 2}`
- panic_origin_outcome: `{'blocked_gatekeeper_reject': {'count': 1, 'avg_profit_rate_pct': 1.5177}, 'blocked_swing_gap': {'count': 5, 'avg_profit_rate_pct': 0.9281}, 'blocked_swing_score_vpw': {'count': 4, 'avg_profit_rate_pct': 0.6667}, 'unknown': {'count': 1, 'avg_profit_rate_pct': 0.0}}`

## Lifecycle Funnel

| group | raw | unique_records |
| --- | ---: | ---: |
| `entry` | 434518 | 27 |
| `holding` | 0 | 0 |
| `scale_in` | 145 | 11 |
| `exit` | 32 | 15 |
| `other` | 380 | 11 |

## Key Stages

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 86 | 18 |
| `blocked_swing_gap` | 93525 | 10 |
| `blocked_swing_score_vpw` | 331228 | 23 |
| `gatekeeper_fast_reuse_bypass` | 86 | 18 |
| `swing_probe_discarded` | 9559 | 27 |
| `swing_probe_entry_candidate` | 17 | 13 |
| `swing_probe_exit_signal` | 16 | 15 |
| `swing_probe_holding_started` | 17 | 13 |
| `swing_probe_scale_in_order_assumed_filled` | 10 | 9 |
| `swing_probe_sell_order_assumed_filled` | 16 | 15 |
| `swing_probe_state_persisted` | 43 | 1 |
| `swing_probe_state_restored` | 3 | 1 |
| `swing_reentry_counterfactual_after_loss` | 323 | 5 |
| `swing_same_symbol_loss_reentry_cooldown` | 10 | 9 |
| `swing_same_symbol_loss_reentry_cooldowns_restored` | 1 | 1 |
| `swing_scale_in_micro_context_observed` | 125 | 11 |
| `swing_sim_scale_in_order_assumed_filled` | 10 | 9 |

## OFI/QI Micro Context

- sample_count: `161`
- stale_missing_unique_record_count: `1`
- stale_missing_ratio: `0.0062`
- stale_missing_reason_counts: `{'micro_missing': 1, 'micro_not_ready': 1, 'state_insufficient': 1}`
- stale_missing_reason_combination_counts: `{'micro_missing+micro_not_ready+state_insufficient': 1}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 1}`
- stale_missing_group_counts: `{'exit': 1}`
- stale_missing_group_unique_record_counts: `{'exit': 1}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{}`
- scale_in_micro_state_counts: `{'bearish': 6, 'neutral': 139}`
- exit_micro_state_counts: `{'neutral': 12, 'insufficient': 1, 'bearish': 3}`
- exit_smoothing_action_counts: `{}`

## Scale-In Observation

- action_groups: `{'PYRAMID': 18, 'AVG_DOWN': 127}`
- add_triggers: `{'swing_pyramid_ok': 2, 'swing_avg_down_ok': 18}`
- price_policies: `{'WAIT_FOR_PULLBACK': 4, 'market': 20, 'KEEP_EXISTING_PRICE': 121}`
- add_ratio_summary: `{'count': 20, 'min': 0.25, 'max': 1.0, 'avg': 0.53054, 'mean': 0.53054, 'p50': 0.4722, 'p95': 1.0}`
- post_add_outcomes: `{'pending_followup': 20}`
- guard_blockers: `{}`
- zero_sample_reason: `None`

## Simulation Opportunity

- available: `True`
- sample_state: `hold_sample`
- rows: `81`
- closed_count: `0`
- winner_count: `0`
- loser_count: `0`

| family | rows | closed | winner | loser | avg_net_ret |
| --- | ---: | ---: | ---: | ---: | ---: |
| `swing_gatekeeper_reject_cooldown` | 27 | 0 | 0 | 0 | None |
| `swing_market_regime_sensitivity` | 27 | 0 | 0 | 0 | None |
| `swing_model_floor` | 3 | 0 | 0 | 0 | None |
| `swing_selection_top_k` | 24 | 0 | 0 | 0 | None |

## Observation Axes

| axis | stage | family | sample | status |
| --- | --- | --- | ---: | --- |
| `swing_selection_model_floor` | `selection` | `swing_model_floor` | 3 | `ready` |
| `swing_recommendation_db_load` | `db_load` | `swing_selection_top_k` | 3 | `ready` |
| `swing_gatekeeper_accept_reject` | `entry` | `swing_gatekeeper_accept_reject` | 31 | `ready` |
| `swing_gap_market_budget_price_qty` | `entry` | `swing_market_regime_sensitivity` | 66 | `ready` |
| `swing_holding_mfe_mae_defer` | `holding` | `swing_holding_flow_defer` | 0 | `hold_sample` |
| `swing_scale_in_avg_down_pyramid` | `scale_in` | `swing_pyramid_trigger` | 11 | `ready` |
| `swing_exit_post_sell_attribution` | `exit` | `swing_trailing_stop_time_stop` | 15 | `ready` |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `swing_entry_ofi_qi_execution_quality` | 0 | `hold_sample` |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `swing_scale_in_ofi_qi_confirmation` | 145 | `ready` |
| `swing_exit_ofi_qi_smoothing` | `holding_exit` | `swing_exit_ofi_qi_smoothing` | 16 | `ready` |

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
