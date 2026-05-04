# Cumulative Threshold Cycle Report - 2026-05-04

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-05-04`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 14 | 46066 | 146 | -0.3992 | 0.4452 | 0.5342 |
| rolling_5d | 5 | 14731 | 91 | -0.5784 | 0.4066 | 0.5824 |
| rolling_10d | 10 | 46066 | 127 | -0.4107 | 0.4409 | 0.5433 |
| rolling_20d | 14 | 46066 | 146 | -0.3992 | 0.4452 | 0.5342 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 146 | -0.3992 | -1.9 | 1.18 | 0.4452 | 0.5342 |
| cumulative | normal_only | 146 | -0.3992 | -1.9 | 1.18 | 0.4452 | 0.5342 |
| cumulative | initial_only | 131 | -0.5166 | -1.9 | 1.02 | 0.4046 | 0.5725 |
| cumulative | pyramid_activated | 15 | 0.6267 | -1.42 | 1.59 | 0.8 | 0.2 |
| cumulative | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_5d | all_completed_valid | 91 | -0.5784 | -2.03 | 1 | 0.4066 | 0.5824 |
| rolling_5d | normal_only | 91 | -0.5784 | -2.03 | 1 | 0.4066 | 0.5824 |
| rolling_5d | initial_only | 82 | -0.6901 | -2.03 | 0.81 | 0.3659 | 0.622 |
| rolling_5d | pyramid_activated | 9 | 0.44 | -1.45 | 1.18 | 0.7778 | 0.2222 |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 127 | -0.4107 | -1.98 | 1.41 | 0.4409 | 0.5433 |
| rolling_10d | normal_only | 127 | -0.4107 | -1.98 | 1.41 | 0.4409 | 0.5433 |
| rolling_10d | initial_only | 114 | -0.5473 | -2 | 1.02 | 0.3947 | 0.5877 |
| rolling_10d | pyramid_activated | 13 | 0.7869 | -0.07 | 1.59 | 0.8462 | 0.1538 |
| rolling_10d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_20d | all_completed_valid | 146 | -0.3992 | -1.9 | 1.18 | 0.4452 | 0.5342 |
| rolling_20d | normal_only | 146 | -0.3992 | -1.9 | 1.18 | 0.4452 | 0.5342 |
| rolling_20d | initial_only | 131 | -0.5166 | -1.9 | 1.02 | 0.4046 | 0.5725 |
| rolling_20d | pyramid_activated | 15 | 0.6267 | -1.42 | 1.59 | 0.8 | 0.2 |
| rolling_20d | reversal_add_activated | 0 | - | - | - | - | - |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 39727 | True | report_only_reference |
| cumulative | pre_submit_price_guard | entry | - | True | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 357 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | - | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | - | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 11 | False | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | - | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 146 | False | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 8768 | True | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | - | True | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 357 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | - | True | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | - | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 11 | False | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | - | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 91 | False | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 39727 | True | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | - | True | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 357 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | - | True | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | - | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 11 | False | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | - | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 127 | False | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 39727 | True | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | - | True | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 357 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | - | True | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | - | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 11 | False | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | - | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 146 | False | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
