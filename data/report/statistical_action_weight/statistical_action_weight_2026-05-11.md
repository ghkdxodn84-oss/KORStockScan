# Statistical Action Weight Report - 2026-05-11

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 26 |
| exit_only | 25 |
| avg_down_wait | 0 |
| pyramid_wait | 1 |
| compact_exit_signal | 46 |
| compact_sell_completed | 1 |
| compact_scale_in_executed | 49 |
| compact_decision_snapshot | 607 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 26 |
| volume_known | 14 |
| time_known | 16 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 5 |
| defensive_only_high_loss_rate | 3 |
| insufficient_sample | 6 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.0644 | - | 6 | -0.1333 | 0.5 | candidate_weight_source |
| price_30k_70k | exit_only | -1.9525 | - | 8 | 4.34 | 0.375 | candidate_weight_source |
| price_gte_70k | exit_only | -0.5204 | - | 6 | -0.88 | 0.6667 | defensive_only_high_loss_rate |
| price_lt_10k | exit_only | -0.5087 | - | 5 | -0.508 | 0.6 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_500k_2m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_gte_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_lt_500k | exit_only | -0.4173 | - | 5 | -1.356 | 0.8 | defensive_only_high_loss_rate |
| volume_unknown | exit_only | -0.4777 | - | 12 | 3.5675 | 0.25 | candidate_weight_source |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_0930_1030 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_1030_1400 | exit_only | -0.5692 | - | 7 | -1.5714 | 0.8571 | defensive_only_high_loss_rate |
| time_1400_1530 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_unknown | exit_only | -1.008 | - | 10 | 3.944 | 0.3 | candidate_weight_source |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `607`
- sample_candidates: `636`
- post_sell_joined_candidates: `0`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 365 | 0 | -3.9962 | 4.3262 | - | - |
| exit_now | 229 | 0 | 23.9139 | 0.6254 | - | - |
| hold_wait | 42 | 0 | 20.4845 | 0.0826 | - | - |

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
