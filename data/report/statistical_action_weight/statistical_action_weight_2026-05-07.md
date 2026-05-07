# Statistical Action Weight Report - 2026-05-07

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 47 |
| exit_only | 40 |
| avg_down_wait | 1 |
| pyramid_wait | 6 |
| compact_exit_signal | 9 |
| compact_sell_completed | 9 |
| compact_scale_in_executed | 0 |
| compact_decision_snapshot | 459 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 47 |
| volume_known | 44 |
| time_known | 47 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 7 |
| defensive_only_high_loss_rate | 4 |
| insufficient_sample | 3 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -1.2343 | - | 7 | -0.4286 | 0.7143 | defensive_only_high_loss_rate |
| price_30k_70k | exit_only | -0.9435 | - | 10 | -0.473 | 0.5 | candidate_weight_source |
| price_gte_70k | exit_only | -0.6607 | - | 17 | -0.0665 | 0.4706 | candidate_weight_source |
| price_lt_10k | exit_only | -1.2231 | - | 6 | -1.915 | 1 | defensive_only_high_loss_rate |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -1.2675 | - | 7 | -1.1743 | 0.7143 | defensive_only_high_loss_rate |
| volume_500k_2m | exit_only | -0.8755 | - | 21 | -0.4952 | 0.619 | candidate_weight_source |
| volume_gte_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_lt_500k | exit_only | -1.2563 | - | 8 | -0.5325 | 0.625 | candidate_weight_source |
| volume_unknown | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | exit_only | -1.2248 | - | 5 | -0.788 | 0.6 | candidate_weight_source |
| time_0930_1030 | exit_only | -0.5857 | - | 16 | 0.0981 | 0.4375 | candidate_weight_source |
| time_1030_1400 | exit_only | -1.3788 | - | 13 | -1.5269 | 0.9231 | defensive_only_high_loss_rate |
| time_1400_1530 | exit_only | -0.728 | - | 5 | 0.824 | 0.2 | candidate_weight_source |
| time_outside_regular | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `459`
- sample_candidates: `465`
- post_sell_joined_candidates: `465`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 175 | 175 | -0.7397 | 1.2303 | 0.1589 | -9.9169 |
| exit_now | 281 | 281 | -0.369 | 1.3664 | 0.3368 | -8.7306 |
| hold_wait | 9 | 9 | 2.0889 | 0.1478 | -0.0968 | -12.4638 |

- `post_decision_*_proxy`는 record_id가 post_sell 평가와 맞는 경우의 10분 proxy이며 live 판단 근거가 아니다.
- true 후행 quote join이 추가되기 전까지는 selection-bias 점검과 후보 발굴에만 쓴다.

## Threshold 반영 원칙

- 이 리포트는 AI/주문 runtime을 직접 변경하지 않는다.
- `candidate_weight_source`는 다음 threshold weight 또는 decision matrix 후보일 뿐이다.
- `no_clear_edge`, `insufficient_sample`, `defensive_only_high_loss_rate`는 live 반영 금지다.

## 다음 액션

- Markdown 자동생성 상태와 표본 충분성을 확인한다.
- sample-ready이면 `holding_exit_decision_matrix` report-only contract 후보로 넘긴다.
- 부족하면 `stat_action_decision_snapshot`와 completed/action join 품질을 먼저 보강한다.
