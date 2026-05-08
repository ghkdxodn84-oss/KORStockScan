# Statistical Action Weight Report - 2026-05-08

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 50 |
| exit_only | 43 |
| avg_down_wait | 1 |
| pyramid_wait | 6 |
| compact_exit_signal | 18 |
| compact_sell_completed | 3 |
| compact_scale_in_executed | 21 |
| compact_decision_snapshot | 89 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 50 |
| volume_known | 47 |
| time_known | 50 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 7 |
| defensive_only_high_loss_rate | 5 |
| insufficient_sample | 2 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -1.2769 | - | 8 | -0.6362 | 0.75 | defensive_only_high_loss_rate |
| price_30k_70k | exit_only | -0.954 | - | 10 | -0.473 | 0.5 | candidate_weight_source |
| price_gte_70k | exit_only | -0.6682 | - | 17 | -0.0665 | 0.4706 | candidate_weight_source |
| price_lt_10k | exit_only | -1.4202 | - | 8 | -1.4925 | 0.875 | defensive_only_high_loss_rate |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -1.0686 | - | 13 | -0.61 | 0.6154 | candidate_weight_source |
| volume_500k_2m | exit_only | -0.5179 | - | 14 | 0.2229 | 0.4286 | candidate_weight_source |
| volume_gte_10m | exit_only | -1.159 | - | 6 | -1.8317 | 1 | defensive_only_high_loss_rate |
| volume_lt_500k | exit_only | -1.4301 | - | 7 | -1.61 | 0.8571 | defensive_only_high_loss_rate |
| volume_unknown | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | exit_only | -1.0995 | - | 6 | -0.44 | 0.5 | candidate_weight_source |
| time_0930_1030 | exit_only | -0.5935 | - | 16 | 0.0981 | 0.4375 | candidate_weight_source |
| time_1030_1400 | exit_only | -1.4255 | - | 15 | -1.5793 | 0.9333 | defensive_only_high_loss_rate |
| time_1400_1530 | exit_only | -0.7426 | - | 5 | 0.824 | 0.2 | candidate_weight_source |
| time_outside_regular | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `89`
- sample_candidates: `88`
- post_sell_joined_candidates: `79`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 23 | 14 | -27.627 | 27.7783 | 1.5561 | -9.9761 |
| exit_now | 62 | 62 | -1.2816 | 1.5416 | 2.3418 | -8.6669 |
| hold_wait | 3 | 3 | 1.82 | 0.1533 | 0.117 | -13.52 |

- `post_decision_*_proxy`는 record_id가 post_sell 평가와 맞는 경우의 10분 proxy이며 live 판단 근거가 아니다.
- true 후행 quote join이 추가되기 전까지는 selection-bias 점검과 후보 발굴에만 쓴다.

## Threshold 반영 원칙

- 이 리포트는 AI/주문 runtime을 직접 변경하지 않는다.
- `candidate_weight_source`는 ADM advisory canary/live-readiness 후보로 연결할 수 있다.
- `no_clear_edge`, `insufficient_sample`, `defensive_only_high_loss_rate`는 최소 edge 부재 또는 calibration 보류 상태다.

## 다음 액션

- Markdown 자동생성 상태와 표본 충분성을 확인한다.
- sample-ready bucket은 `holding_exit_decision_matrix` advisory canary 후보로 넘긴다.
- 부족하면 live 금지가 아니라 `hold_sample` calibration과 join 품질 보강으로 남긴다.
