# Cumulative Threshold Cycle Report - 2026-05-07

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-05-07`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 17 | 75589 | 173 | -0.479 | 0.4162 | 0.5665 |
| rolling_5d | 5 | 33213 | 47 | -0.5219 | 0.383 | 0.617 |
| rolling_10d | 10 | 67930 | 146 | -0.486 | 0.4178 | 0.5685 |
| rolling_20d | 17 | 75589 | 173 | -0.479 | 0.4162 | 0.5665 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 173 | -0.479 | -2 | 1.18 | 0.4162 | 0.5665 |
| cumulative | normal_only | 173 | -0.479 | -2 | 1.18 | 0.4162 | 0.5665 |
| cumulative | initial_only | 152 | -0.577 | -2.03 | 1.17 | 0.3882 | 0.5921 |
| cumulative | pyramid_activated | 20 | 0.2635 | -1.42 | 1.18 | 0.65 | 0.35 |
| cumulative | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_5d | all_completed_valid | 47 | -0.5219 | -2.19 | 1.69 | 0.383 | 0.617 |
| rolling_5d | normal_only | 47 | -0.5219 | -2.19 | 1.69 | 0.383 | 0.617 |
| rolling_5d | initial_only | 40 | -0.5087 | -2.25 | 1.69 | 0.4 | 0.6 |
| rolling_5d | pyramid_activated | 6 | -0.625 | -1.2 | 0.6 | 0.3333 | 0.6667 |
| rolling_5d | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_10d | all_completed_valid | 146 | -0.486 | -2.03 | 1.29 | 0.4178 | 0.5685 |
| rolling_10d | normal_only | 146 | -0.486 | -2.03 | 1.29 | 0.4178 | 0.5685 |
| rolling_10d | initial_only | 127 | -0.6034 | -2.07 | 1.29 | 0.3858 | 0.5984 |
| rolling_10d | pyramid_activated | 18 | 0.3389 | -1.2 | 1.59 | 0.6667 | 0.3333 |
| rolling_10d | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_20d | all_completed_valid | 173 | -0.479 | -2 | 1.18 | 0.4162 | 0.5665 |
| rolling_20d | normal_only | 173 | -0.479 | -2 | 1.18 | 0.4162 | 0.5665 |
| rolling_20d | initial_only | 152 | -0.577 | -2.03 | 1.17 | 0.3882 | 0.5921 |
| rolling_20d | pyramid_activated | 20 | 0.2635 | -1.42 | 1.18 | 0.65 | 0.35 |
| rolling_20d | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 48763 | True | report_only_reference |
| cumulative | pre_submit_price_guard | entry | - | True | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | - | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 575 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | - | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | - | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 39 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | - | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 2 | False | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | - | True | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 173 | False | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 9726 | True | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | - | True | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | - | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 236 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | - | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | - | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 39 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | - | True | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 2 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | - | True | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 47 | False | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 41142 | True | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | - | True | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | - | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 575 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | - | True | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | - | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 39 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | - | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 2 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | - | True | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 146 | False | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 48763 | True | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | - | True | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | - | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 575 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | - | True | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | - | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 39 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | - | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 2 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | - | True | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 173 | False | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
