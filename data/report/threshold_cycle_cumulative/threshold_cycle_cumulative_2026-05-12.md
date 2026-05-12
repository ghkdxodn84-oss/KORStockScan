# Cumulative Threshold Cycle Report - 2026-05-12

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-05-12`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 22 | 80811 | 187 | -0.2541 | 0.4278 | 0.5561 |
| rolling_5d | 5 | 5222 | 14 | 2.525 | 0.5714 | 0.4286 |
| rolling_10d | 10 | 38435 | 61 | 0.1774 | 0.4262 | 0.5738 |
| rolling_20d | 20 | 80811 | 179 | -0.2463 | 0.4302 | 0.5587 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 177 | -0.4913 | 0.4124 |
| cumulative | sim | 10 | 3.944 | 0.7 |
| cumulative | combined | 187 | -0.2541 | 0.4278 |
| rolling_5d | real | 4 | -1.0225 | 0.25 |
| rolling_5d | sim | 10 | 3.944 | 0.7 |
| rolling_5d | combined | 14 | 2.525 | 0.5714 |
| rolling_10d | real | 51 | -0.5612 | 0.3725 |
| rolling_10d | sim | 10 | 3.944 | 0.7 |
| rolling_10d | combined | 61 | 0.1774 | 0.4262 |
| rolling_20d | real | 169 | -0.4943 | 0.4142 |
| rolling_20d | sim | 10 | 3.944 | 0.7 |
| rolling_20d | combined | 179 | -0.2463 | 0.4302 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 187 | -0.2541 | -2.02 | 1.41 | 0.4278 | 0.5561 |
| cumulative | normal_only | 187 | -0.2541 | -2.02 | 1.41 | 0.4278 | 0.5561 |
| cumulative | initial_only | 166 | -0.3154 | -2.03 | 1.41 | 0.4036 | 0.5783 |
| cumulative | pyramid_activated | 20 | 0.2635 | -1.42 | 1.18 | 0.65 | 0.35 |
| cumulative | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_5d | all_completed_valid | 14 | 2.525 | -2.09 | 2.28 | 0.5714 | 0.4286 |
| rolling_5d | normal_only | 14 | 2.525 | -2.09 | 2.28 | 0.5714 | 0.4286 |
| rolling_5d | initial_only | 14 | 2.525 | -2.09 | 2.28 | 0.5714 | 0.4286 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 61 | 0.1774 | -2.16 | 1.76 | 0.4262 | 0.5738 |
| rolling_10d | normal_only | 61 | 0.1774 | -2.16 | 1.76 | 0.4262 | 0.5738 |
| rolling_10d | initial_only | 54 | 0.2778 | -2.19 | 2.08 | 0.4444 | 0.5556 |
| rolling_10d | pyramid_activated | 6 | -0.625 | -1.2 | 0.6 | 0.3333 | 0.6667 |
| rolling_10d | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_20d | all_completed_valid | 179 | -0.2463 | -2.03 | 1.44 | 0.4302 | 0.5587 |
| rolling_20d | normal_only | 179 | -0.2463 | -2.03 | 1.44 | 0.4302 | 0.5587 |
| rolling_20d | initial_only | 160 | -0.311 | -2.03 | 1.41 | 0.4062 | 0.5813 |
| rolling_20d | pyramid_activated | 18 | 0.3389 | -1.2 | 1.59 | 0.6667 | 0.3333 |
| rolling_20d | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 50194 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 50194 | False | report_only_reference |
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
| cumulative | statistical_action_weight | decision_support | 187 | False | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 1431 | False | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 1431 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | - | False | report_only_reference |
| rolling_5d | liquidity_gate_refined_candidate | entry | - | False | report_only_reference |
| rolling_5d | overbought_gate_refined_candidate | entry | - | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | - | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | - | False | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | - | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | - | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | - | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | - | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 6 | False | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | - | True | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | - | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | - | True | report_only_reference |
| rolling_5d | position_sizing_cap_release | position_sizing | - | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 14 | False | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 11157 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 11157 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | - | True | report_only_reference |
| rolling_10d | liquidity_gate_refined_candidate | entry | - | False | report_only_reference |
| rolling_10d | overbought_gate_refined_candidate | entry | - | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | - | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 236 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | - | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | - | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | - | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | - | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 45 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | - | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 2 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | - | True | report_only_reference |
| rolling_10d | position_sizing_cap_release | position_sizing | - | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 61 | False | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 50194 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 50194 | False | report_only_reference |
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
| rolling_20d | statistical_action_weight | decision_support | 179 | False | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
