# Swing Selection Funnel Report - 2026-05-14

- owner: `SwingModelSelectionFunnelRepair`
- selection_mode: `SELECTED`
- selected_count: `3`
- fallback_written_to_recommendations: `False`
- csv_rows: `3`
- db_rows: `28`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- submitted_unique_records: `0`

## Pipeline Raw vs Unique

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 74 | 12 |
| `blocked_swing_gap` | 156259 | 17 |
| `blocked_swing_score_vpw` | 270246 | 20 |
| `gatekeeper_fast_reuse_bypass` | 74 | 12 |
| `holding_flow_ofi_smoothing_applied` | 28 | 2 |
| `swing_probe_discarded` | 9824 | 28 |
| `swing_probe_entry_candidate` | 15 | 10 |
| `swing_probe_exit_signal` | 15 | 14 |
| `swing_probe_holding_started` | 15 | 10 |
| `swing_probe_scale_in_order_assumed_filled` | 1 | 1 |
| `swing_probe_sell_order_assumed_filled` | 15 | 14 |
| `swing_reentry_counterfactual_after_loss` | 246 | 4 |
| `swing_same_symbol_loss_reentry_cooldown` | 7 | 6 |
| `swing_scale_in_micro_context_observed` | 1066 | 12 |
| `swing_sim_scale_in_order_assumed_filled` | 1 | 1 |

## Top Code Stage

- `blocked_swing_score_vpw` 대한항공(003490): 20448
- `blocked_swing_gap` 이마트(139480): 20393
- `blocked_swing_score_vpw` 현대차(005380): 18755
- `blocked_swing_score_vpw` 디아이씨(092200): 18755
- `blocked_swing_score_vpw` 두산밥캣(241560): 18754
- `blocked_swing_score_vpw` 기아(000270): 18754
- `blocked_swing_score_vpw` 현대글로비스(086280): 18754
- `blocked_swing_score_vpw` 한온시스템(018880): 18754
- `blocked_swing_score_vpw` SK텔레콤(017670): 18753
- `blocked_swing_score_vpw` HL만도(204320): 18753

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
- exit_smoothing_action_counts: `{'NO_CHANGE': 28}`
