# Swing Selection Funnel Report - 2026-05-11

- owner: `SwingModelSelectionFunnelRepair`
- selection_mode: `SELECTED`
- selected_count: `3`
- fallback_written_to_recommendations: `False`
- csv_rows: `3`
- db_rows: `23`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- submitted_unique_records: `0`

## Pipeline Raw vs Unique

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 73 | 9 |
| `blocked_swing_gap` | 17801 | 4 |
| `blocked_swing_score_vpw` | 78950 | 21 |
| `gatekeeper_fast_reuse_bypass` | 74 | 9 |
| `holding_flow_ofi_smoothing_applied` | 62 | 7 |
| `holding_started` | 9 | 1 |
| `swing_probe_discarded` | 53330 | 23 |
| `swing_probe_entry_candidate` | 27 | 13 |
| `swing_probe_holding_started` | 27 | 13 |
| `swing_probe_scale_in_order_assumed_filled` | 4 | 4 |
| `swing_scale_in_micro_context_observed` | 4 | 4 |
| `swing_sim_scale_in_order_assumed_filled` | 4 | 4 |

## Top Code Stage

- `blocked_swing_gap` 삼성물산(028260): 8674
- `blocked_swing_gap` 현대차(005380): 6746
- `blocked_swing_score_vpw` 한화투자증권(003530): 5507
- `blocked_swing_score_vpw` LG전자(066570): 5503
- `blocked_swing_score_vpw` LG에너지솔루션(373220): 5300
- `blocked_swing_score_vpw` HD현대일렉트릭(267260): 5275
- `blocked_swing_score_vpw` 디아이씨(092200): 5239
- `blocked_swing_score_vpw` 와이투솔루션(011690): 4961
- `blocked_swing_score_vpw` 넥센(005720): 4753
- `blocked_swing_score_vpw` LG(003550): 4603

## OFI/QI Micro Context

- sample_count: `74`
- stale_missing_ratio: `0.9189`
- entry_micro_state_counts: `{}`
- scale_in_micro_state_counts: `{'insufficient': 6, 'neutral': 6}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 61, 'CONFIRM_EXIT': 1}`
