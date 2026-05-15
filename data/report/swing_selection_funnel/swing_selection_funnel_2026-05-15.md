# Swing Selection Funnel Report - 2026-05-15

- owner: `SwingModelSelectionFunnelRepair`
- selection_mode: `SELECTED`
- selected_count: `3`
- fallback_written_to_recommendations: `False`
- csv_rows: `3`
- db_rows: `24`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- submitted_unique_records: `0`

## Pipeline Raw vs Unique

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 81 | 11 |
| `blocked_swing_gap` | 28948 | 7 |
| `blocked_swing_score_vpw` | 332663 | 23 |
| `gatekeeper_fast_reuse_bypass` | 81 | 11 |
| `holding_flow_ofi_smoothing_applied` | 1 | 1 |
| `holding_started` | 1 | 1 |
| `swing_probe_discarded` | 8213 | 24 |
| `swing_probe_entry_candidate` | 42 | 16 |
| `swing_probe_exit_signal` | 42 | 21 |
| `swing_probe_holding_started` | 42 | 16 |
| `swing_probe_scale_in_order_assumed_filled` | 28 | 19 |
| `swing_probe_sell_order_assumed_filled` | 42 | 21 |
| `swing_reentry_counterfactual_after_loss` | 829 | 10 |
| `swing_same_symbol_loss_reentry_cooldown` | 21 | 13 |
| `swing_scale_in_micro_context_observed` | 28 | 19 |
| `swing_sim_scale_in_order_assumed_filled` | 28 | 19 |

## Top Code Stage

- `blocked_swing_score_vpw` NAVER(035420): 17771
- `blocked_swing_score_vpw` 삼성물산(028260): 17769
- `blocked_swing_gap` LG(003550): 17768
- `blocked_swing_score_vpw` 이마트(139480): 17768
- `blocked_swing_score_vpw` 대한항공(003490): 17767
- `blocked_swing_score_vpw` 크래프톤(259960): 17767
- `blocked_swing_score_vpw` 동원산업(006040): 17764
- `blocked_swing_score_vpw` 한국콜마(161890): 17762
- `blocked_swing_score_vpw` 현대백화점(069960): 17762
- `blocked_swing_score_vpw` 현대해상(001450): 16955

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
- exit_smoothing_action_counts: `{'NO_CHANGE': 1}`
