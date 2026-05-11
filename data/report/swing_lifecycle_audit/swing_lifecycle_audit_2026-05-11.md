# Swing Lifecycle Audit - 2026-05-11

- owner: `SwingFullLifecycleSelfImprovementChain`
- runtime_change: `false`
- selected_count: `3`
- csv_rows: `3`
- db_rows: `0`
- db_load_gap: `True`
- db_load_skip_reason: `db_load_error`
- entered_rows: `0`
- completed_rows: `0`
- submitted_unique_records: `0`
- simulated_order_unique_records: `13`
- observation_axis_status: `{'ready': 8, 'instrumentation_gap': 1, 'hold_sample': 1}`

## Lifecycle Funnel

| group | raw | unique_records |
| --- | ---: | ---: |
| `entry` | 143875 | 23 |
| `holding` | 69 | 8 |
| `scale_in` | 12 | 4 |
| `exit` | 36 | 3 |
| `other` | 6 | 1 |

## Key Stages

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 73 | 9 |
| `blocked_swing_gap` | 16541 | 4 |
| `blocked_swing_score_vpw` | 73910 | 21 |
| `gatekeeper_fast_reuse_bypass` | 74 | 9 |
| `holding_flow_ofi_smoothing_applied` | 62 | 7 |
| `holding_started` | 7 | 1 |
| `sell_order_sent` | 36 | 3 |
| `swing_probe_discarded` | 53223 | 23 |
| `swing_probe_entry_candidate` | 27 | 13 |
| `swing_probe_holding_started` | 27 | 13 |
| `swing_probe_scale_in_order_assumed_filled` | 4 | 4 |
| `swing_probe_state_persisted` | 2 | 1 |
| `swing_probe_state_restored` | 4 | 1 |
| `swing_scale_in_micro_context_observed` | 4 | 4 |
| `swing_sim_scale_in_order_assumed_filled` | 4 | 4 |

## OFI/QI Micro Context

- sample_count: `74`
- stale_missing_ratio: `0.9189`
- entry_micro_state_counts: `{}`
- scale_in_micro_state_counts: `{'insufficient': 6, 'neutral': 6}`
- exit_micro_state_counts: `{'neutral': 57, 'bearish': 2, 'bullish': 3}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 61, 'CONFIRM_EXIT': 1}`

## Scale-In Observation

- action_groups: `{'AVG_DOWN': 12}`
- add_triggers: `{}`
- price_policies: `{'NO_CHANGE': 6, 'KEEP_EXISTING_PRICE': 6}`
- add_ratio_summary: `{'count': 0, 'min': None, 'max': None, 'avg': None, 'mean': None, 'p50': None, 'p95': None}`
- post_add_outcomes: `{}`
- guard_blockers: `{}`
- zero_sample_reason: `None`

## Simulation Opportunity

- available: `True`
- sample_state: `hold_sample`
- rows: `69`
- closed_count: `0`
- winner_count: `0`
- loser_count: `0`

| family | rows | closed | winner | loser | avg_net_ret |
| --- | ---: | ---: | ---: | ---: | ---: |
| `swing_gatekeeper_reject_cooldown` | 23 | 0 | 0 | 0 | None |
| `swing_market_regime_sensitivity` | 23 | 0 | 0 | 0 | None |
| `swing_model_floor` | 3 | 0 | 0 | 0 | None |
| `swing_selection_top_k` | 20 | 0 | 0 | 0 | None |

## Observation Axes

| axis | stage | family | sample | status |
| --- | --- | --- | ---: | --- |
| `swing_selection_model_floor` | `selection` | `swing_model_floor` | 3 | `ready` |
| `swing_recommendation_db_load` | `db_load` | `swing_selection_top_k` | 3 | `ready` |
| `swing_gatekeeper_accept_reject` | `entry` | `swing_gatekeeper_accept_reject` | 22 | `ready` |
| `swing_gap_market_budget_price_qty` | `entry` | `swing_market_regime_sensitivity` | 51 | `ready` |
| `swing_holding_mfe_mae_defer` | `holding` | `swing_holding_flow_defer` | 8 | `instrumentation_gap` |
| `swing_scale_in_avg_down_pyramid` | `scale_in` | `swing_pyramid_trigger` | 4 | `ready` |
| `swing_exit_post_sell_attribution` | `exit` | `swing_trailing_stop_time_stop` | 3 | `ready` |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `swing_entry_ofi_qi_execution_quality` | 0 | `hold_sample` |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `swing_scale_in_ofi_qi_confirmation` | 12 | `ready` |
| `swing_exit_ofi_qi_smoothing` | `holding_exit` | `swing_exit_ofi_qi_smoothing` | 62 | `ready` |

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
