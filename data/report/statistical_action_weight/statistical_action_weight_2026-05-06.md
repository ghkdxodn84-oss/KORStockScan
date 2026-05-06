# Statistical Action Weight Report - 2026-05-06

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `True`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 109 |
| exit_only | 94 |
| avg_down_wait | 1 |
| pyramid_wait | 14 |
| compact_exit_signal | 54 |
| compact_sell_completed | 5 |
| compact_scale_in_executed | 47 |
| compact_decision_snapshot | 513 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 109 |
| volume_known | 102 |
| time_known | 109 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 8 |
| defensive_only_high_loss_rate | 4 |
| insufficient_sample | 2 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.9489 | - | 24 | -0.62 | 0.625 | candidate_weight_source |
| price_30k_70k | exit_only | -1.253 | - | 12 | -0.995 | 0.6667 | defensive_only_high_loss_rate |
| price_gte_70k | pyramid_wait | -0.5576 | 0.1769 | 5 | -0.166 | 0.4 | candidate_weight_source |
| price_lt_10k | exit_only | -1.4406 | - | 16 | -1.4181 | 0.875 | defensive_only_high_loss_rate |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | pyramid_wait | -0.336 | 0.7098 | 5 | 0.17 | 0.4 | candidate_weight_source |
| volume_500k_2m | exit_only | -0.7652 | - | 36 | -0.4628 | 0.6111 | candidate_weight_source |
| volume_gte_10m | exit_only | -1.5253 | - | 7 | -1.3457 | 0.8571 | defensive_only_high_loss_rate |
| volume_lt_500k | exit_only | -1.2115 | - | 24 | -1.0621 | 0.6667 | defensive_only_high_loss_rate |
| volume_unknown | exit_only | -1.1422 | - | 5 | -0.302 | 0.4 | candidate_weight_source |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | exit_only | -0.9735 | - | 20 | -0.6515 | 0.55 | candidate_weight_source |
| time_0930_1030 | exit_only | -0.7505 | - | 26 | -0.3262 | 0.5 | candidate_weight_source |
| time_1030_1400 | pyramid_wait | -0.2843 | 0.917 | 9 | 0.11 | 0.3333 | candidate_weight_source |
| time_1400_1530 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_outside_regular | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Threshold 반영 원칙

- 이 리포트는 AI/주문 runtime을 직접 변경하지 않는다.
- `candidate_weight_source`는 다음 threshold weight 또는 decision matrix 후보일 뿐이다.
- `no_clear_edge`, `insufficient_sample`, `defensive_only_high_loss_rate`는 live 반영 금지다.

## 다음 액션

- Markdown 자동생성 상태와 표본 충분성을 확인한다.
- sample-ready이면 `holding_exit_decision_matrix`와 shadow prompt 주입 후보로 넘긴다.
- 부족하면 `stat_action_decision_snapshot`와 completed/action join 품질을 먼저 보강한다.
