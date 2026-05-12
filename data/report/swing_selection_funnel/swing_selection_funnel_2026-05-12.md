# Swing Selection Funnel Report - 2026-05-12

- owner: `SwingModelSelectionFunnelRepair`
- selection_mode: `SELECTED`
- selected_count: `3`
- fallback_written_to_recommendations: `False`
- csv_rows: `3`
- db_rows: `30`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- submitted_unique_records: `0`

## Pipeline Raw vs Unique

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
| `swing_scale_in_micro_context_observed` | 28 | 15 |
| `swing_sim_scale_in_order_assumed_filled` | 28 | 15 |

## Top Code Stage

- `blocked_swing_score_vpw` 삼성전자(005930): 21917
- `blocked_swing_score_vpw` LG화학(051910): 21916
- `blocked_swing_score_vpw` KT&G(033780): 21916
- `blocked_swing_score_vpw` iM금융지주(139130): 21916
- `blocked_swing_score_vpw` 한화오션(042660): 21916
- `blocked_swing_score_vpw` 현대엘리베이터(017800): 21916
- `blocked_swing_score_vpw` GS(078930): 21916
- `blocked_swing_score_vpw` KB금융(105560): 21916
- `blocked_swing_score_vpw` 기아(000270): 21916
- `blocked_swing_score_vpw` 대한항공(003490): 21916

## OFI/QI Micro Context

- sample_count: `116`
- stale_missing_ratio: `0.0776`
- entry_micro_state_counts: `{}`
- scale_in_micro_state_counts: `{'neutral': 69, 'bullish': 6, 'insufficient': 9}`
- exit_smoothing_action_counts: `{}`
