# Cumulative Threshold Cycle Report - 2026-05-14

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-05-14`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 24 | 83137 | 177 | -0.4913 | 0.4124 | 0.5706 |
| rolling_5d | 5 | 6227 | 1 | -1.55 | 0 | 1 |
| rolling_10d | 10 | 13265 | 16 | -0.7962 | 0.375 | 0.625 |
| rolling_20d | 20 | 83137 | 158 | -0.5116 | 0.4051 | 0.5823 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 177 | -0.4913 | 0.4124 |
| cumulative | sim | 11 | 3.4036 | 0.6364 |
| cumulative | combined | 188 | -0.2634 | 0.4255 |
| rolling_5d | real | 1 | -1.55 | 0 |
| rolling_5d | sim | 11 | 3.4036 | 0.6364 |
| rolling_5d | combined | 12 | 2.9908 | 0.5833 |
| rolling_10d | real | 16 | -0.7962 | 0.375 |
| rolling_10d | sim | 11 | 3.4036 | 0.6364 |
| rolling_10d | combined | 27 | 0.9148 | 0.4815 |
| rolling_20d | real | 158 | -0.5116 | 0.4051 |
| rolling_20d | sim | 11 | 3.4036 | 0.6364 |
| rolling_20d | combined | 169 | -0.2568 | 0.4201 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 177 | -0.4913 | -2.02 | 1.29 | 0.4124 | 0.5706 |
| cumulative | normal_only | 177 | -0.4913 | -2.02 | 1.29 | 0.4124 | 0.5706 |
| cumulative | initial_only | 156 | -0.5885 | -2.03 | 1.29 | 0.3846 | 0.5962 |
| cumulative | pyramid_activated | 20 | 0.2635 | -1.42 | 1.18 | 0.65 | 0.35 |
| cumulative | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_5d | all_completed_valid | 1 | -1.55 | -1.55 | -1.55 | 0 | 1 |
| rolling_5d | normal_only | 1 | -1.55 | -1.55 | -1.55 | 0 | 1 |
| rolling_5d | initial_only | 1 | -1.55 | -1.55 | -1.55 | 0 | 1 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 16 | -0.7962 | -2.19 | 1.3 | 0.375 | 0.625 |
| rolling_10d | normal_only | 16 | -0.7962 | -2.19 | 1.3 | 0.375 | 0.625 |
| rolling_10d | initial_only | 15 | -0.8893 | -2.19 | 1.3 | 0.3333 | 0.6667 |
| rolling_10d | pyramid_activated | 1 | 0.6 | 0.6 | 0.6 | 1 | 0 |
| rolling_10d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_20d | all_completed_valid | 158 | -0.5116 | -2.03 | 1.3 | 0.4051 | 0.5823 |
| rolling_20d | normal_only | 158 | -0.5116 | -2.03 | 1.3 | 0.4051 | 0.5823 |
| rolling_20d | initial_only | 139 | -0.6224 | -2.07 | 1.3 | 0.3741 | 0.6115 |
| rolling_20d | pyramid_activated | 18 | 0.3389 | -1.2 | 1.59 | 0.6667 | 0.3333 |
| rolling_20d | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 50836 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 50836 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | - | True | report_only_reference |
| cumulative | liquidity_gate_refined_candidate | entry | - | False | report_only_reference |
| cumulative | overbought_gate_refined_candidate | entry | - | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | - | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 575 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | - | True | report_only_reference |
| cumulative | reversal_add | holding_exit | - | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | - | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | - | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 45 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | - | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 2 | False | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | - | True | report_only_reference |
| cumulative | position_sizing_cap_release | position_sizing | - | False | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | - | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 177 | False | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 1359 | False | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 1359 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | - | False | report_only_reference |
| rolling_5d | liquidity_gate_refined_candidate | entry | - | False | report_only_reference |
| rolling_5d | overbought_gate_refined_candidate | entry | - | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | - | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | - | False | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | - | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | - | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | - | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | - | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 5 | False | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | - | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | - | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | - | True | report_only_reference |
| rolling_5d | position_sizing_cap_release | position_sizing | - | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | - | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 1 | False | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 4136 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 4136 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | - | False | report_only_reference |
| rolling_10d | liquidity_gate_refined_candidate | entry | - | False | report_only_reference |
| rolling_10d | overbought_gate_refined_candidate | entry | - | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | - | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 15 | False | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | - | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | - | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | - | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | - | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 11 | False | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | - | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 2 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | - | True | report_only_reference |
| rolling_10d | position_sizing_cap_release | position_sizing | - | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | - | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 16 | False | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 50836 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 50836 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | - | True | report_only_reference |
| rolling_20d | liquidity_gate_refined_candidate | entry | - | False | report_only_reference |
| rolling_20d | overbought_gate_refined_candidate | entry | - | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | - | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 575 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | - | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | - | True | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | - | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | - | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 45 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | - | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 2 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | - | True | report_only_reference |
| rolling_20d | position_sizing_cap_release | position_sizing | - | False | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | - | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 158 | False | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
