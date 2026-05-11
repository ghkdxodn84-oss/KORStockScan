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
| `blocked_swing_gap` | 13371 | 4 |
| `blocked_swing_score_vpw` | 62756 | 21 |
| `gatekeeper_fast_reuse_bypass` | 74 | 9 |
| `holding_flow_ofi_smoothing_applied` | 62 | 7 |
| `holding_started` | 7 | 1 |
| `swing_probe_discarded` | 52965 | 23 |
| `swing_probe_entry_candidate` | 27 | 13 |
| `swing_probe_holding_started` | 27 | 13 |
| `swing_probe_scale_in_order_assumed_filled` | 4 | 4 |
| `swing_scale_in_micro_context_observed` | 4 | 4 |
| `swing_sim_scale_in_order_assumed_filled` | 4 | 4 |

## Top Code Stage

- `blocked_swing_gap` 삼성물산(028260): 6470
- `blocked_swing_gap` 현대차(005380): 4520
- `blocked_swing_score_vpw` 한화투자증권(003530): 3282
- `blocked_swing_score_vpw` 호텔신라(008770): 3281
- `blocked_swing_score_vpw` LG전자(066570): 3279
- `blocked_swing_score_vpw` 한국가스공사(036460): 3279
- `blocked_swing_score_vpw` 하나금융지주(086790): 3278
- `blocked_swing_score_vpw` HD현대일렉트릭(267260): 3277
- `blocked_swing_score_vpw` 이노션(214320): 3277
- `blocked_swing_score_vpw` LG에너지솔루션(373220): 3276

## OFI/QI Micro Context

- sample_count: `74`
- stale_missing_ratio: `0.9189`
- entry_micro_state_counts: `{}`
- scale_in_micro_state_counts: `{'insufficient': 6, 'neutral': 6}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 61, 'CONFIRM_EXIT': 1}`
