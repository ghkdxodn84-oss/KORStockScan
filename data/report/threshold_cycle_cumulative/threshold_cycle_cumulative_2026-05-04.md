# Cumulative Threshold Cycle Report - 2026-05-04

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-05-04`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 14 | 69872 | 159 | -0.4709 | 0.4151 | 0.566 |
| rolling_5d | 5 | 38537 | 104 | -0.6657 | 0.3654 | 0.625 |
| rolling_10d | 10 | 69872 | 140 | -0.4911 | 0.4071 | 0.5786 |
| rolling_20d | 14 | 69872 | 159 | -0.4709 | 0.4151 | 0.566 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 159 | -0.4709 | -1.93 | 1.17 | 0.4151 | 0.566 |
| cumulative | normal_only | 159 | -0.4709 | -1.93 | 1.17 | 0.4151 | 0.566 |
| cumulative | initial_only | 139 | -0.5692 | -2 | 1.02 | 0.3885 | 0.5899 |
| cumulative | pyramid_activated | 19 | 0.2458 | -1.42 | 1.59 | 0.6316 | 0.3684 |
| cumulative | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_5d | all_completed_valid | 104 | -0.6657 | -2.03 | 0.94 | 0.3654 | 0.625 |
| rolling_5d | normal_only | 104 | -0.6657 | -2.03 | 0.94 | 0.3654 | 0.625 |
| rolling_5d | initial_only | 90 | -0.7559 | -2.03 | 0.81 | 0.3444 | 0.6444 |
| rolling_5d | pyramid_activated | 13 | -0.0592 | -1.2 | 1.17 | 0.5385 | 0.4615 |
| rolling_5d | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_10d | all_completed_valid | 140 | -0.4911 | -2 | 1.17 | 0.4071 | 0.5786 |
| rolling_10d | normal_only | 140 | -0.4911 | -2 | 1.17 | 0.4071 | 0.5786 |
| rolling_10d | initial_only | 122 | -0.6052 | -2 | 0.98 | 0.377 | 0.6066 |
| rolling_10d | pyramid_activated | 17 | 0.3235 | -1.2 | 1.59 | 0.6471 | 0.3529 |
| rolling_10d | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_20d | all_completed_valid | 159 | -0.4709 | -1.93 | 1.17 | 0.4151 | 0.566 |
| rolling_20d | normal_only | 159 | -0.4709 | -1.93 | 1.17 | 0.4151 | 0.566 |
| rolling_20d | initial_only | 139 | -0.5692 | -2 | 1.02 | 0.3885 | 0.5899 |
| rolling_20d | pyramid_activated | 19 | 0.2458 | -1.42 | 1.59 | 0.6316 | 0.3684 |
| rolling_20d | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 46700 | True | report_only_reference |
| cumulative | pre_submit_price_guard | entry | - | True | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 560 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | - | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | - | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 34 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | - | True | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 159 | False | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 15741 | True | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | - | True | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 560 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | - | True | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | - | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 34 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | - | True | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 104 | False | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 46700 | True | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | - | True | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 560 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | - | True | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | - | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 34 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | - | True | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 140 | False | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 46700 | True | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | - | True | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 560 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | - | True | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | - | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 34 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | - | True | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 159 | False | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
