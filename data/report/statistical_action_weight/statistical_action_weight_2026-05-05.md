# Statistical Action Weight Report - 2026-05-05

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `True`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 126 |
| exit_only | 108 |
| avg_down_wait | 1 |
| pyramid_wait | 17 |
| compact_exit_signal | 0 |
| compact_sell_completed | 0 |
| compact_scale_in_executed | 0 |
| compact_decision_snapshot | 0 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 126 |
| volume_known | 119 |
| time_known | 126 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 11 |
| defensive_only_high_loss_rate | 2 |
| insufficient_sample | 1 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.9426 | - | 25 | -0.6564 | 0.64 | candidate_weight_source |
| price_30k_70k | exit_only | -1.0461 | - | 14 | -0.6936 | 0.5714 | candidate_weight_source |
| price_gte_70k | pyramid_wait | -0.2515 | 0.3591 | 6 | 0.1383 | 0.3333 | candidate_weight_source |
| price_lt_10k | pyramid_wait | -0.4392 | 0.9398 | 5 | 0.432 | 0.4 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | pyramid_wait | -0.1294 | 0.5801 | 5 | 0.17 | 0.4 | candidate_weight_source |
| volume_500k_2m | pyramid_wait | -0.0762 | 0.7135 | 5 | 0.31 | 0.2 | candidate_weight_source |
| volume_gte_10m | exit_only | -1.4755 | - | 7 | -1.3457 | 0.8571 | defensive_only_high_loss_rate |
| volume_lt_500k | exit_only | -1.1013 | - | 30 | -0.9537 | 0.6667 | defensive_only_high_loss_rate |
| volume_unknown | exit_only | -1.0847 | - | 5 | -0.302 | 0.4 | candidate_weight_source |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | exit_only | -0.9673 | - | 21 | -0.6952 | 0.5714 | candidate_weight_source |
| time_0930_1030 | exit_only | -0.711 | - | 28 | -0.3332 | 0.5 | candidate_weight_source |
| time_1030_1400 | pyramid_wait | -0.0612 | 1.0291 | 10 | 0.192 | 0.3 | candidate_weight_source |
| time_1400_1530 | exit_only | -0.5193 | - | 10 | 0.213 | 0.2 | candidate_weight_source |
| time_outside_regular | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Threshold 반영 원칙

- 이 리포트는 AI/주문 runtime을 직접 변경하지 않는다.
- `candidate_weight_source`는 다음 threshold weight 또는 decision matrix 후보일 뿐이다.
- `no_clear_edge`, `insufficient_sample`, `defensive_only_high_loss_rate`는 live 반영 금지다.

## 다음 액션

- Markdown 자동생성 상태와 표본 충분성을 확인한다.
- sample-ready이면 `holding_exit_decision_matrix`와 shadow prompt 주입 후보로 넘긴다.
- 부족하면 `stat_action_decision_snapshot`와 completed/action join 품질을 먼저 보강한다.
