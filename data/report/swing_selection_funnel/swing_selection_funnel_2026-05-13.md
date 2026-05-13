# Swing Selection Funnel Report - 2026-05-13

- owner: `SwingModelSelectionFunnelRepair`
- selection_mode: `SELECTED`
- selected_count: `3`
- fallback_written_to_recommendations: `False`
- csv_rows: `3`
- db_rows: `27`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- submitted_unique_records: `0`

## Pipeline Raw vs Unique

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 86 | 18 |
| `blocked_swing_gap` | 93429 | 10 |
| `blocked_swing_score_vpw` | 330940 | 23 |
| `gatekeeper_fast_reuse_bypass` | 86 | 18 |
| `swing_probe_discarded` | 9550 | 27 |
| `swing_probe_entry_candidate` | 17 | 13 |
| `swing_probe_exit_signal` | 16 | 15 |
| `swing_probe_holding_started` | 17 | 13 |
| `swing_probe_scale_in_order_assumed_filled` | 10 | 9 |
| `swing_probe_sell_order_assumed_filled` | 16 | 15 |
| `swing_reentry_counterfactual_after_loss` | 323 | 5 |
| `swing_same_symbol_loss_reentry_cooldown` | 10 | 9 |
| `swing_scale_in_micro_context_observed` | 125 | 11 |
| `swing_sim_scale_in_order_assumed_filled` | 10 | 9 |

## Top Code Stage

- `blocked_swing_score_vpw` 하나금융지주(086790): 19191
- `blocked_swing_score_vpw` LG씨엔에스(064400): 19191
- `blocked_swing_score_vpw` 카카오페이(377300): 19191
- `blocked_swing_score_vpw` 금호석유화학(011780): 19191
- `blocked_swing_score_vpw` 한화(000880): 19190
- `blocked_swing_score_vpw` LG(003550): 19190
- `blocked_swing_score_vpw` DN오토모티브(007340): 19190
- `blocked_swing_score_vpw` 콜마홀딩스(024720): 19184
- `blocked_swing_score_vpw` YG PLUS(037270): 18365
- `blocked_swing_score_vpw` HD한국조선해양(009540): 18364

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
- exit_smoothing_action_counts: `{}`
