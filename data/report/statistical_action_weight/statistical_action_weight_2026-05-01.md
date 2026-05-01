# Statistical Action Weight Report - 2026-05-01

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `True`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 100 |
| exit_only | 90 |
| avg_down_wait | 0 |
| pyramid_wait | 10 |
| compact_exit_signal | 28 |
| compact_sell_completed | 0 |
| compact_scale_in_executed | 42 |
| compact_decision_snapshot | 15 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 100 |
| volume_known | 94 |
| time_known | 100 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 12 |
| defensive_only_high_loss_rate | 1 |
| insufficient_sample | 1 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.8713 | - | 27 | -0.6133 | 0.5926 | candidate_weight_source |
| price_30k_70k | exit_only | -1.1982 | - | 7 | -0.6271 | 0.5714 | candidate_weight_source |
| price_gte_70k | exit_only | -0.7959 | - | 42 | -0.5545 | 0.5952 | candidate_weight_source |
| price_lt_10k | exit_only | -1.3085 | - | 14 | -1.1936 | 0.7857 | defensive_only_high_loss_rate |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -0.9252 | - | 24 | -0.695 | 0.625 | candidate_weight_source |
| volume_500k_2m | exit_only | -0.964 | - | 30 | -0.6797 | 0.6333 | candidate_weight_source |
| volume_gte_10m | exit_only | -1.1102 | - | 14 | -0.7671 | 0.6429 | candidate_weight_source |
| volume_lt_500k | exit_only | -0.8869 | - | 17 | -0.5288 | 0.5882 | candidate_weight_source |
| volume_unknown | exit_only | -1.2981 | - | 5 | -0.83 | 0.6 | candidate_weight_source |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | exit_only | -1.0736 | - | 15 | -0.75 | 0.6 | candidate_weight_source |
| time_0930_1030 | exit_only | -1.064 | - | 20 | -0.791 | 0.6 | candidate_weight_source |
| time_1030_1400 | pyramid_wait | 0.9172 | 1.8659 | 6 | 0.8783 | 0 | candidate_weight_source |
| time_1400_1530 | exit_only | -0.6499 | - | 10 | 0.023 | 0.3 | candidate_weight_source |
| time_outside_regular | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Threshold 반영 원칙

- 이 리포트는 AI/주문 runtime을 직접 변경하지 않는다.
- `candidate_weight_source`는 다음 threshold weight 또는 decision matrix 후보일 뿐이다.
- `no_clear_edge`, `insufficient_sample`, `defensive_only_high_loss_rate`는 live 반영 금지다.

## 다음 액션

- Markdown 자동생성 상태와 표본 충분성을 확인한다.
- sample-ready이면 `holding_exit_decision_matrix`와 shadow prompt 주입 후보로 넘긴다.
- 부족하면 `stat_action_decision_snapshot`와 completed/action join 품질을 먼저 보강한다.
