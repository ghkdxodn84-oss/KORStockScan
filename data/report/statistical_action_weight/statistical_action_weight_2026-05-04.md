# Statistical Action Weight Report - 2026-05-04

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `True`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 119 |
| exit_only | 106 |
| avg_down_wait | 0 |
| pyramid_wait | 13 |
| compact_exit_signal | 65 |
| compact_sell_completed | 24 |
| compact_scale_in_executed | 55 |
| compact_decision_snapshot | 697 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 119 |
| volume_known | 111 |
| time_known | 119 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 12 |
| defensive_only_high_loss_rate | 1 |
| insufficient_sample | 1 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.7358 | - | 27 | -0.4215 | 0.5556 | candidate_weight_source |
| price_30k_70k | exit_only | -0.9056 | - | 12 | -0.4833 | 0.5 | candidate_weight_source |
| price_gte_70k | pyramid_wait | 0.1225 | 0.7016 | 5 | 0.4 | 0.2 | candidate_weight_source |
| price_lt_10k | exit_only | -1.3307 | - | 17 | -1.3259 | 0.8235 | defensive_only_high_loss_rate |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -0.8169 | - | 28 | -0.5775 | 0.5714 | candidate_weight_source |
| volume_500k_2m | exit_only | -0.7955 | - | 40 | -0.54 | 0.6 | candidate_weight_source |
| volume_gte_10m | exit_only | -1.0453 | - | 13 | -0.7115 | 0.6154 | candidate_weight_source |
| volume_lt_500k | exit_only | -0.7272 | - | 19 | -0.3284 | 0.5263 | candidate_weight_source |
| volume_unknown | exit_only | -1.0779 | - | 6 | -0.5567 | 0.5 | candidate_weight_source |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | exit_only | -0.9383 | - | 21 | -0.6952 | 0.5714 | candidate_weight_source |
| time_0930_1030 | exit_only | -0.6234 | - | 31 | -0.2742 | 0.4839 | candidate_weight_source |
| time_1030_1400 | pyramid_wait | 0.6572 | 1.5935 | 7 | 0.78 | 0 | candidate_weight_source |
| time_1400_1530 | exit_only | -0.4435 | - | 8 | 0.3613 | 0.125 | candidate_weight_source |
| time_outside_regular | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Threshold 반영 원칙

- 이 리포트는 AI/주문 runtime을 직접 변경하지 않는다.
- `candidate_weight_source`는 다음 threshold weight 또는 decision matrix 후보일 뿐이다.
- `no_clear_edge`, `insufficient_sample`, `defensive_only_high_loss_rate`는 live 반영 금지다.

## 다음 액션

- Markdown 자동생성 상태와 표본 충분성을 확인한다.
- sample-ready이면 `holding_exit_decision_matrix`와 shadow prompt 주입 후보로 넘긴다.
- 부족하면 `stat_action_decision_snapshot`와 completed/action join 품질을 먼저 보강한다.
