# Statistical Action Weight Report - 2026-05-13

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 22 |
| exit_only | 22 |
| avg_down_wait | 0 |
| pyramid_wait | 0 |
| compact_exit_signal | 16 |
| compact_sell_completed | 0 |
| compact_scale_in_executed | 0 |
| compact_decision_snapshot | 85 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 22 |
| volume_known | 11 |
| time_known | 12 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 6 |
| defensive_only_high_loss_rate | 1 |
| insufficient_sample | 6 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.0898 | - | 5 | -0.296 | 0.6 | candidate_weight_source |
| price_30k_70k | exit_only | -2.4726 | - | 7 | 4.7757 | 0.4286 | candidate_weight_source |
| price_gte_70k | exit_only | -0.3488 | - | 5 | -0.618 | 0.6 | candidate_weight_source |
| price_lt_10k | exit_only | -0.4149 | - | 5 | -0.508 | 0.6 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_500k_2m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_gte_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_lt_500k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_unknown | exit_only | -0.6288 | - | 11 | 3.7745 | 0.2727 | candidate_weight_source |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_0930_1030 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_1030_1400 | exit_only | -0.394 | - | 6 | -1.4683 | 0.8333 | defensive_only_high_loss_rate |
| time_unknown | exit_only | -0.9403 | - | 10 | 3.944 | 0.3 | candidate_weight_source |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `85`
- sample_candidates: `85`
- post_sell_joined_candidates: `0`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 85 | 0 | -0.1809 | 0.1741 | - | - |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| hold_defer | 85 | 0 | -0.1809 | 0.1741 | - | - |

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
