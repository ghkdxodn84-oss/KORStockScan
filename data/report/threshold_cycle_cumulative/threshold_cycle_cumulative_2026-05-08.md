# Cumulative Threshold Cycle Report - 2026-05-08

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-05-08`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 18 | 76616 | 176 | -0.4853 | 0.4148 | 0.5682 |
| rolling_5d | 5 | 34155 | 50 | -0.5414 | 0.38 | 0.62 |
| rolling_10d | 10 | 60374 | 143 | -0.521 | 0.4056 | 0.5804 |
| rolling_20d | 18 | 76616 | 176 | -0.4853 | 0.4148 | 0.5682 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 176 | -0.4853 | -2.02 | 1.29 | 0.4148 | 0.5682 |
| cumulative | normal_only | 176 | -0.4853 | -2.02 | 1.29 | 0.4148 | 0.5682 |
| cumulative | initial_only | 155 | -0.5823 | -2.03 | 1.29 | 0.3871 | 0.5935 |
| cumulative | pyramid_activated | 20 | 0.2635 | -1.42 | 1.18 | 0.65 | 0.35 |
| cumulative | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_5d | all_completed_valid | 50 | -0.5414 | -2.19 | 1.3 | 0.38 | 0.62 |
| rolling_5d | normal_only | 50 | -0.5414 | -2.19 | 1.3 | 0.38 | 0.62 |
| rolling_5d | initial_only | 43 | -0.5323 | -2.19 | 1.69 | 0.3953 | 0.6047 |
| rolling_5d | pyramid_activated | 6 | -0.625 | -1.2 | 0.6 | 0.3333 | 0.6667 |
| rolling_5d | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_10d | all_completed_valid | 143 | -0.521 | -2.03 | 1.18 | 0.4056 | 0.5804 |
| rolling_10d | normal_only | 143 | -0.521 | -2.03 | 1.18 | 0.4056 | 0.5804 |
| rolling_10d | initial_only | 124 | -0.6465 | -2.08 | 1.02 | 0.371 | 0.6129 |
| rolling_10d | pyramid_activated | 18 | 0.3389 | -1.2 | 1.59 | 0.6667 | 0.3333 |
| rolling_10d | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_20d | all_completed_valid | 176 | -0.4853 | -2.02 | 1.29 | 0.4148 | 0.5682 |
| rolling_20d | normal_only | 176 | -0.4853 | -2.02 | 1.29 | 0.4148 | 0.5682 |
| rolling_20d | initial_only | 155 | -0.5823 | -2.03 | 1.29 | 0.3871 | 0.5935 |
| rolling_20d | pyramid_activated | 20 | 0.2635 | -1.42 | 1.18 | 0.65 | 0.35 |
| rolling_20d | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 49466 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 49466 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | - | True | report_only_reference |
| cumulative | liquidity_gate_refined_candidate | entry | - | False | report_only_reference |
| cumulative | overbought_gate_refined_candidate | entry | - | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | - | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 575 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | - | True | report_only_reference |
| cumulative | reversal_add | holding_exit | - | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | - | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | - | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 40 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | - | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 2 | False | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | - | True | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 176 | False | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 10424 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 10424 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | - | True | report_only_reference |
| rolling_5d | liquidity_gate_refined_candidate | entry | - | False | report_only_reference |
| rolling_5d | overbought_gate_refined_candidate | entry | - | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | - | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 236 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | - | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | - | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | - | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | - | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 40 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | - | True | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 2 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | - | True | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 50 | False | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 33297 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 33297 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | - | True | report_only_reference |
| rolling_10d | liquidity_gate_refined_candidate | entry | - | False | report_only_reference |
| rolling_10d | overbought_gate_refined_candidate | entry | - | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | - | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 575 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | - | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | - | True | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | - | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | - | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 40 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | - | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 2 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | - | True | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 143 | False | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 49466 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 49466 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | - | True | report_only_reference |
| rolling_20d | liquidity_gate_refined_candidate | entry | - | False | report_only_reference |
| rolling_20d | overbought_gate_refined_candidate | entry | - | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | - | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 575 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | - | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | - | True | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | - | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | - | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 40 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | - | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 2 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | - | True | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 176 | False | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
