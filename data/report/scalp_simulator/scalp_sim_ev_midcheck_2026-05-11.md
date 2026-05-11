# Scalp Sim EV Midcheck 2026-05-11

- generated_at: `2026-05-11T15:14:34`
- latest_event_at: `2026-05-11T15:14:33.522280`
- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-05-11.jsonl`
- judgement: `positive_ev_midcheck`
- runtime_mutation: `false`
- synthetic_excluded: `48`

## Summary

- completed: `10`
- sum_profit_pct: `+39.44%`
- avg_profit_pct: `+3.94%`
- median_profit_pct: `+0.81%`
- win_rate_pct: `70.0%`
- gross_win_pct: `+44.08%`
- gross_loss_pct: `-4.64%`

## Sim Stage Counts

- `scalp_sim_buy_order_assumed_filled`: `11`
- `scalp_sim_buy_order_virtual_pending`: `19`
- `scalp_sim_duplicate_buy_signal`: `686`
- `scalp_sim_entry_armed`: `19`
- `scalp_sim_entry_expired`: `9`
- `scalp_sim_holding_started`: `11`
- `scalp_sim_scale_in_order_unfilled`: `7`
- `scalp_sim_sell_order_assumed_filled`: `10`

## Arm Split

| arm | completed | avg | median | win_rate | sum |
| --- | ---: | ---: | ---: | ---: | ---: |
| `avg_down` | 0 | - | - | -% | +0.00% |
| `exit_only` | 10 | +3.94% | +0.81% | 70.0% | +39.44% |
| `mixed_scale_in` | 0 | - | - | -% | +0.00% |
| `pyramid` | 0 | - | - | -% | +0.00% |

## Scale-In Summary

- positions_completed: `10`
- positions_with_scale_in: `0`
- positions_without_scale_in: `10`
- filled_events: `0`
- unfilled_events: `7`
- completed_filled_events: `0`
- completed_unfilled_events: `7`
- filled_by_add_type: `{}`
- unfilled_by_add_type: `{'PYRAMID': 7}`
- actual_order_submitted_false_only: `true`
- actual_order_checked_values: `86`

## Scale-In Position Outcomes

| 종목 | arm | add filled/unfilled | post-add MFE | post-add MAE | final exit | actual_order |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| HJ중공업(097230) | `exit_only` | 0/0 | - | - | - | False |
| 헥토파이낸셜(234340) | `exit_only` | 0/0 | - | - | - | False |
| 씨젠(096530) | `exit_only` | 0/0 | - | - | - | False |
| 경인양행(012610) | `exit_only` | 0/0 | - | - | - | False |
| 티이엠씨(425040) | `exit_only` | 0/0 | - | - | - | False |
| 이랜시스(264850) | `exit_only` | 0/0 | - | - | - | False |
| 카카오페이(377300) | `exit_only` | 0/0 | - | - | - | False |
| 한미반도체(042700) | `exit_only` | 0/0 | - | - | - | False |
| 성호전자(043260) | `exit_only` | 0/0 | - | - | - | False |
| 대한전선(001440) | `exit_only` | 0/7 | - | - | - | False |

## Initial Qty Provenance

- method: `actual_sim_qty_provenance_only`
- sample: `10`
- qty_sum: `14`
- uncapped_qty_sum: `14`
- cap_applied_count: `0`
- uncapped_qty_source_count: `0`
- fixed_qty_source_count: `0`

| 종목 | sim_qty | uncapped_qty | qty_source | cap_applied | final exit |
| --- | ---: | ---: | --- | --- | ---: |
| 대한전선(001440) | 5 | 5 | `-` | false | +36.62% |
| 이랜시스(264850) | 1 | 1 | `-` | false | +2.28% |
| 씨젠(096530) | 1 | 1 | `-` | false | +1.76% |
| 헥토파이낸셜(234340) | 1 | 1 | `-` | false | +1.24% |
| 카카오페이(377300) | 1 | 1 | `-` | false | +0.96% |
| 한미반도체(042700) | 1 | 1 | `-` | false | +0.65% |
| 티이엠씨(425040) | 1 | 1 | `-` | false | +0.57% |
| HJ중공업(097230) | 1 | 1 | `-` | false | -0.05% |
| 경인양행(012610) | 1 | 1 | `-` | false | -2.01% |
| 성호전자(043260) | 1 | 1 | `-` | false | -2.58% |

## Completed Rows

| 종목 | 수익률 | exit_rule | source |
| --- | ---: | --- | --- |
| 대한전선(001440) | +36.62% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 이랜시스(264850) | +2.28% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 씨젠(096530) | +1.76% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 헥토파이낸셜(234340) | +1.24% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 카카오페이(377300) | +0.96% | scalp_preset_ai_review_exit | AI_REVIEW_EXIT |
| 한미반도체(042700) | +0.65% | scalp_ai_momentum_decay | HOLDING_FLOW_OVERRIDE |
| 티이엠씨(425040) | +0.57% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| HJ중공업(097230) | -0.05% | scalp_preset_protect_profit | PRESET_PROTECT |
| 경인양행(012610) | -2.01% | scalp_soft_stop_pct | HOLDING_FLOW_OVERRIDE |
| 성호전자(043260) | -2.58% | scalp_hard_stop_pct | MANUAL |

## Expired Entries

| 종목 | limit_price | parent |
| --- | ---: | --- |
| 대한전선(001440) | 48800 | 4219 |
| 세아베스틸지주(001430) | 75900 | 5811 |
| 펩트론(087010) | 287000 | 5814 |
| 펩트론(087010) | 289000 | 5814 |
| 삼아알미늄(006110) | 77500 | 5899 |
| 한화오션(042660) | 130200 | 5783 |
| 삼성물산(028260) | 440000 | 5786 |
| 삼성물산(028260) | 440500 | 5786 |
| LG이노텍(011070) | 697500 | 5877 |

## Real Completed Reference

| 종목 | 수익률 | exit_rule |
| --- | ---: | --- |
| 세아베스틸지주(001430) | -1.55% | scalp_preset_hard_stop_pct |
