# Swing Lifecycle Audit - 2026-05-15

- owner: `SwingFullLifecycleSelfImprovementChain`
- runtime_change: `false`
- selected_count: `3`
- csv_rows: `3`
- db_rows: `24`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- completed_rows: `0`
- submitted_unique_records: `0`
- simulated_order_unique_records: `26`
- observation_axis_status: `{'ready': 9, 'hold_sample': 1}`
- panic_state: `PANIC_SELL`
- panic_active_sim_probe: `{'active_positions': 9, 'profit_sample': 9, 'avg_unrealized_profit_rate_pct': -0.1665, 'win_rate_pct': 33.3, 'wins': 3, 'losses': 5, 'flat': 1}`
- panic_origin_outcome: `{'blocked_gatekeeper_reject': {'count': 2, 'avg_profit_rate_pct': -1.215}, 'blocked_swing_gap': {'count': 3, 'avg_profit_rate_pct': 0.0247}, 'blocked_swing_score_vpw': {'count': 4, 'avg_profit_rate_pct': 0.2143}}`

## Lifecycle Funnel

| group | raw | unique_records |
| --- | ---: | ---: |
| `entry` | 440559 | 24 |
| `holding` | 2 | 2 |
| `scale_in` | 84 | 19 |
| `exit` | 89 | 23 |
| `other` | 1003 | 14 |

## Key Stages

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 87 | 11 |
| `blocked_swing_gap` | 38386 | 7 |
| `blocked_swing_score_vpw` | 392437 | 23 |
| `gatekeeper_fast_reuse_bypass` | 87 | 11 |
| `holding_flow_ofi_smoothing_applied` | 1 | 1 |
| `holding_started` | 1 | 1 |
| `sell_order_sent` | 5 | 2 |
| `swing_probe_discarded` | 9478 | 24 |
| `swing_probe_entry_candidate` | 42 | 16 |
| `swing_probe_exit_signal` | 42 | 21 |
| `swing_probe_holding_started` | 42 | 16 |
| `swing_probe_scale_in_order_assumed_filled` | 28 | 19 |
| `swing_probe_sell_order_assumed_filled` | 42 | 21 |
| `swing_probe_state_empty_overwrite_blocked` | 1 | 1 |
| `swing_probe_state_persisted` | 118 | 1 |
| `swing_probe_state_restored` | 16 | 1 |
| `swing_reentry_counterfactual_after_loss` | 836 | 10 |
| `swing_same_symbol_loss_reentry_cooldown` | 21 | 13 |
| `swing_same_symbol_loss_reentry_cooldowns_restored` | 11 | 1 |
| `swing_scale_in_micro_context_observed` | 28 | 19 |
| `swing_sim_scale_in_order_assumed_filled` | 28 | 19 |

## OFI/QI Micro Context

- sample_count: `127`
- stale_missing_unique_record_count: `5`
- stale_missing_ratio: `0.126`
- stale_missing_reason_counts: `{'micro_missing': 16, 'observer_unhealthy': 2, 'micro_not_ready': 15, 'state_insufficient': 15}`
- stale_missing_reason_combination_counts: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 2, 'micro_missing+micro_not_ready+state_insufficient': 13, 'micro_missing': 1}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 2, 'micro_missing+micro_not_ready+state_insufficient': 4}`
- stale_missing_group_counts: `{'exit': 4, 'scale_in': 12}`
- stale_missing_group_unique_record_counts: `{'exit': 3, 'scale_in': 4}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 2, 'observer_unhealthy_with_other_reason': 2, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{}`
- scale_in_micro_state_counts: `{'neutral': 69, 'insufficient': 12, 'bearish': 3}`
- exit_micro_state_counts: `{'insufficient': 3, 'bearish': 4, 'neutral': 35, 'bullish': 1}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 1}`

## Scale-In Observation

- action_groups: `{'PYRAMID': 9, 'AVG_DOWN': 75}`
- add_triggers: `{'swing_pyramid_ok': 6, 'swing_avg_down_ok': 50}`
- price_policies: `{'KEEP_EXISTING_PRICE': 23, 'market': 56, 'NO_CHANGE': 4, 'WAIT_FOR_PULLBACK': 1}`
- add_ratio_summary: `{'count': 56, 'min': 0.25, 'max': 1.0, 'avg': 0.5043, 'mean': 0.5043, 'p50': 0.5, 'p95': 1.0}`
- post_add_outcomes: `{'pending_followup': 56}`
- guard_blockers: `{}`
- zero_sample_reason: `None`

## Simulation Opportunity

- available: `False`
- sample_state: `None`
- rows: `0`
- closed_count: `0`
- winner_count: `0`
- loser_count: `0`

| family | rows | closed | winner | loser | avg_net_ret |
| --- | ---: | ---: | ---: | ---: | ---: |

## Observation Axes

| axis | stage | family | sample | status |
| --- | --- | --- | ---: | --- |
| `swing_selection_model_floor` | `selection` | `swing_model_floor` | 3 | `ready` |
| `swing_recommendation_db_load` | `db_load` | `swing_selection_top_k` | 3 | `ready` |
| `swing_gatekeeper_accept_reject` | `entry` | `swing_gatekeeper_accept_reject` | 27 | `ready` |
| `swing_gap_market_budget_price_qty` | `entry` | `swing_market_regime_sensitivity` | 72 | `ready` |
| `swing_holding_mfe_mae_defer` | `holding` | `swing_holding_flow_defer` | 2 | `ready` |
| `swing_scale_in_avg_down_pyramid` | `scale_in` | `swing_pyramid_trigger` | 19 | `ready` |
| `swing_exit_post_sell_attribution` | `exit` | `swing_trailing_stop_time_stop` | 23 | `ready` |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `swing_entry_ofi_qi_execution_quality` | 0 | `hold_sample` |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `swing_scale_in_ofi_qi_confirmation` | 84 | `ready` |
| `swing_exit_ofi_qi_smoothing` | `holding_exit` | `swing_exit_ofi_qi_smoothing` | 1 | `ready` |

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
