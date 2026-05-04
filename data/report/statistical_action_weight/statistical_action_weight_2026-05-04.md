# Statistical Action Weight Report - 2026-05-04

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `True`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 132 |
| exit_only | 114 |
| avg_down_wait | 1 |
| pyramid_wait | 17 |
| compact_exit_signal | 345 |
| compact_sell_completed | 99 |
| compact_scale_in_executed | 199 |
| compact_decision_snapshot | 4564 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 132 |
| volume_known | 124 |
| time_known | 132 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 13 |
| insufficient_sample | 1 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.8097 | - | 29 | -0.5159 | 0.5862 | candidate_weight_source |
| price_30k_70k | exit_only | -1.0307 | - | 14 | -0.6936 | 0.5714 | candidate_weight_source |
| price_gte_70k | pyramid_wait | -0.2515 | 0.322 | 6 | 0.1383 | 0.3333 | candidate_weight_source |
| price_lt_10k | pyramid_wait | -0.4392 | 0.9424 | 5 | 0.432 | 0.4 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | pyramid_wait | -0.3157 | 0.5689 | 5 | -0.248 | 0.6 | candidate_weight_source |
| volume_500k_2m | exit_only | -0.8226 | - | 44 | -0.5807 | 0.6136 | candidate_weight_source |
| volume_gte_10m | exit_only | -1.0901 | - | 14 | -0.7786 | 0.6429 | candidate_weight_source |
| volume_lt_500k | exit_only | -0.8084 | - | 20 | -0.4245 | 0.55 | candidate_weight_source |
| volume_unknown | exit_only | -1.1138 | - | 6 | -0.5567 | 0.5 | candidate_weight_source |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | exit_only | -0.9556 | - | 21 | -0.6952 | 0.5714 | candidate_weight_source |
| time_0930_1030 | exit_only | -0.6363 | - | 31 | -0.2742 | 0.4839 | candidate_weight_source |
| time_1030_1400 | pyramid_wait | -0.0612 | 0.9723 | 10 | 0.192 | 0.3 | candidate_weight_source |
| time_1400_1530 | exit_only | -0.5005 | - | 10 | 0.213 | 0.2 | candidate_weight_source |
| time_outside_regular | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Threshold 반영 원칙

- 이 리포트는 AI/주문 runtime을 직접 변경하지 않는다.
- `candidate_weight_source`는 다음 threshold weight 또는 decision matrix 후보일 뿐이다.
- `no_clear_edge`, `insufficient_sample`, `defensive_only_high_loss_rate`는 live 반영 금지다.

## 다음 액션

- Markdown 자동생성 상태와 표본 충분성을 확인한다.
- sample-ready이면 `holding_exit_decision_matrix`와 shadow prompt 주입 후보로 넘긴다.
- 부족하면 `stat_action_decision_snapshot`와 completed/action join 품질을 먼저 보강한다.
