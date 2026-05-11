# Scalp Sim EV Midcheck 2026-05-11

- generated_at: `2026-05-11T12:25:45`
- latest_event_at: `2026-05-11T12:25:43.912130`
- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-05-11.jsonl`
- judgement: `positive_ev_midcheck`
- runtime_mutation: `false`
- synthetic_excluded: `20`

## Summary

- completed: `9`
- sum_profit_pct: `+2.82%`
- avg_profit_pct: `+0.31%`
- median_profit_pct: `+0.65%`
- win_rate_pct: `66.67%`
- gross_win_pct: `+7.46%`
- gross_loss_pct: `-4.64%`

## Sim Stage Counts

- `scalp_sim_buy_order_assumed_filled`: `9`
- `scalp_sim_buy_order_virtual_pending`: `17`
- `scalp_sim_duplicate_buy_signal`: `602`
- `scalp_sim_entry_armed`: `17`
- `scalp_sim_entry_expired`: `9`
- `scalp_sim_holding_started`: `9`
- `scalp_sim_sell_order_assumed_filled`: `9`

## Completed Rows

| 종목 | 수익률 | exit_rule | source |
| --- | ---: | --- | --- |
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
