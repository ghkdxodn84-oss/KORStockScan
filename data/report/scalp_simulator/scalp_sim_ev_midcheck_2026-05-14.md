# Scalp Sim EV Midcheck 2026-05-14

- generated_at: `2026-05-14T15:04:35`
- latest_event_at: `2026-05-14T15:04:34.248383`
- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-05-14.jsonl`
- judgement: `non_positive_or_no_sample`
- runtime_mutation: `false`
- synthetic_excluded: `0`

## Summary

- completed: `2`
- sum_profit_pct: `-1.45%`
- avg_profit_pct: `-0.72%`
- median_profit_pct: `-0.72%`
- win_rate_pct: `50.0%`
- gross_win_pct: `+0.55%`
- gross_loss_pct: `-2.00%`

## Sim Stage Counts

- `scalp_sim_buy_order_assumed_filled`: `1`
- `scalp_sim_buy_order_virtual_pending`: `1`
- `scalp_sim_entry_armed`: `1`
- `scalp_sim_holding_started`: `1`
- `scalp_sim_sell_order_assumed_filled`: `2`

## Arm Split

| arm | completed | avg | median | win_rate | sum |
| --- | ---: | ---: | ---: | ---: | ---: |
| `avg_down` | 0 | - | - | -% | +0.00% |
| `exit_only` | 2 | -0.72% | -0.72% | 50.0% | -1.45% |
| `mixed_scale_in` | 0 | - | - | -% | +0.00% |
| `pyramid` | 0 | - | - | -% | +0.00% |

## Scale-In Summary

- positions_completed: `2`
- positions_with_scale_in: `0`
- positions_without_scale_in: `2`
- filled_events: `0`
- unfilled_events: `0`
- completed_filled_events: `0`
- completed_unfilled_events: `0`
- filled_by_add_type: `{}`
- unfilled_by_add_type: `{}`
- actual_order_submitted_false_only: `true`
- actual_order_checked_values: `6`

## Scale-In Position Outcomes

| 종목 | arm | add filled/unfilled | post-add MFE | post-add MAE | final exit | actual_order |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 한미반도체(042700) | `exit_only` | 0/0 | - | - | - | False |
| 알테오젠(196170) | `exit_only` | 0/0 | - | - | - | False |

## Initial Qty Provenance

- method: `actual_sim_qty_provenance_only`
- sample: `2`
- qty_sum: `8`
- uncapped_qty_sum: `8`
- cap_applied_count: `0`
- uncapped_qty_source_count: `1`
- virtual_budget_qty_source_count: `0`
- fixed_qty_source_count: `0`

| 종목 | sim_qty | uncapped_qty | qty_source | cap_applied | final exit |
| --- | ---: | ---: | --- | --- | ---: |
| 알테오젠(196170) | 1 | 1 | `uncapped_buy_capacity` | false | +0.55% |
| 한미반도체(042700) | 7 | 7 | `-` | false | -2.00% |

## Completed Rows

| 종목 | 수익률 | exit_rule | source |
| --- | ---: | --- | --- |
| 알테오젠(196170) | +0.55% | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 한미반도체(042700) | -2.00% | scalp_soft_stop_pct | HOLDING_FLOW_OVERRIDE |

## Expired Entries

| 종목 | limit_price | parent |
| --- | ---: | --- |

## Real Completed Reference

| 종목 | 수익률 | exit_rule |
| --- | ---: | --- |
