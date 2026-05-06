# Cumulative Threshold Cycle Report - 2026-05-06

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-05-06`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 16 | 72723 | 164 | -0.4581 | 0.4207 | 0.561 |
| rolling_5d | 5 | 30381 | 38 | -0.4418 | 0.3947 | 0.6053 |
| rolling_10d | 10 | 72717 | 145 | -0.4759 | 0.4138 | 0.5724 |
| rolling_20d | 16 | 72723 | 164 | -0.4581 | 0.4207 | 0.561 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 164 | -0.4581 | -1.98 | 1.17 | 0.4207 | 0.561 |
| cumulative | normal_only | 164 | -0.4581 | -1.98 | 1.17 | 0.4207 | 0.561 |
| cumulative | initial_only | 143 | -0.5592 | -2 | 1.02 | 0.3916 | 0.5874 |
| cumulative | pyramid_activated | 20 | 0.2635 | -1.42 | 1.18 | 0.65 | 0.35 |
| cumulative | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_5d | all_completed_valid | 38 | -0.4418 | -2.19 | 1.69 | 0.3947 | 0.6053 |
| rolling_5d | normal_only | 38 | -0.4418 | -2.19 | 1.69 | 0.3947 | 0.6053 |
| rolling_5d | initial_only | 31 | -0.4068 | -2.19 | 1.69 | 0.4194 | 0.5806 |
| rolling_5d | pyramid_activated | 6 | -0.625 | -1.2 | 0.6 | 0.3333 | 0.6667 |
| rolling_5d | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_10d | all_completed_valid | 145 | -0.4759 | -2 | 1.18 | 0.4138 | 0.5724 |
| rolling_10d | normal_only | 145 | -0.4759 | -2 | 1.18 | 0.4138 | 0.5724 |
| rolling_10d | initial_only | 126 | -0.5927 | -2.03 | 1.02 | 0.381 | 0.6032 |
| rolling_10d | pyramid_activated | 18 | 0.3389 | -1.2 | 1.59 | 0.6667 | 0.3333 |
| rolling_10d | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_20d | all_completed_valid | 164 | -0.4581 | -1.98 | 1.17 | 0.4207 | 0.561 |
| rolling_20d | normal_only | 164 | -0.4581 | -1.98 | 1.17 | 0.4207 | 0.561 |
| rolling_20d | initial_only | 143 | -0.5592 | -2 | 1.02 | 0.3916 | 0.5874 |
| rolling_20d | pyramid_activated | 20 | 0.2635 | -1.42 | 1.18 | 0.65 | 0.35 |
| rolling_20d | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 47652 | True | report_only_reference |
| cumulative | pre_submit_price_guard | entry | - | True | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | - | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 566 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | - | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | - | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 36 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | - | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 1 | False | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | - | True | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 164 | False | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 8617 | True | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | - | True | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | - | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 227 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | - | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | - | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 36 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | - | True | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 1 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | - | True | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 38 | False | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 47650 | True | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | - | True | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | - | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 566 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | - | True | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | - | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 36 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | - | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 1 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | - | True | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 145 | False | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 47652 | True | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | - | True | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | - | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 566 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | - | True | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | - | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 36 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | - | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 1 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | - | True | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 164 | False | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
