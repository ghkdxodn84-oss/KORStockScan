# Holding/Exit Decision Matrix - 2026-05-08

## 판정

- matrix_version: `holding_exit_decision_matrix_v1_2026-05-08`
- application_mode: `advisory_canary_live_readiness_until_owner_approval`
- runtime_change: `False`

## Hard Veto

- `emergency_or_hard_stop`
- `active_sell_order_pending`
- `invalid_feature`
- `post_add_eval_exclusion`

## Matrix Entries

| axis | bucket | bias | score | edge | sample | loss_rate | policy |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| price_bucket | price_10k_30k | no_clear_edge | -1.2769 | - | 8 | 0.75 | defensive_only_high_loss_rate |
| price_bucket | price_30k_70k | no_clear_edge | -0.954 | - | 10 | 0.5 | candidate_weight_source |
| price_bucket | price_gte_70k | no_clear_edge | -0.6682 | - | 17 | 0.4706 | candidate_weight_source |
| price_bucket | price_lt_10k | no_clear_edge | -1.4202 | - | 8 | 0.875 | defensive_only_high_loss_rate |
| volume_bucket | volume_2m_10m | no_clear_edge | -1.0686 | - | 13 | 0.6154 | candidate_weight_source |
| volume_bucket | volume_500k_2m | no_clear_edge | -0.5179 | - | 14 | 0.4286 | candidate_weight_source |
| volume_bucket | volume_gte_10m | no_clear_edge | -1.159 | - | 6 | 1 | defensive_only_high_loss_rate |
| volume_bucket | volume_lt_500k | no_clear_edge | -1.4301 | - | 7 | 0.8571 | defensive_only_high_loss_rate |
| volume_bucket | volume_unknown | no_clear_edge | - | - | - | - | insufficient_sample |
| time_bucket | time_0900_0930 | no_clear_edge | -1.0995 | - | 6 | 0.5 | candidate_weight_source |
| time_bucket | time_0930_1030 | no_clear_edge | -0.5935 | - | 16 | 0.4375 | candidate_weight_source |
| time_bucket | time_1030_1400 | no_clear_edge | -1.4255 | - | 15 | 0.9333 | defensive_only_high_loss_rate |
| time_bucket | time_1400_1530 | no_clear_edge | -0.7426 | - | 5 | 0.2 | candidate_weight_source |
| time_bucket | time_outside_regular | no_clear_edge | - | - | - | - | insufficient_sample |

## Prompt Hints

- `price_bucket=price_10k_30k` / `no_clear_edge`: price_bucket=price_10k_30k 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `price_bucket=price_30k_70k` / `no_clear_edge`: price_bucket=price_30k_70k 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `price_bucket=price_gte_70k` / `no_clear_edge`: price_bucket=price_gte_70k 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `price_bucket=price_lt_10k` / `no_clear_edge`: price_bucket=price_lt_10k 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `volume_bucket=volume_2m_10m` / `no_clear_edge`: volume_bucket=volume_2m_10m 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `volume_bucket=volume_500k_2m` / `no_clear_edge`: volume_bucket=volume_500k_2m 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `volume_bucket=volume_gte_10m` / `no_clear_edge`: volume_bucket=volume_gte_10m 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `volume_bucket=volume_lt_500k` / `no_clear_edge`: volume_bucket=volume_lt_500k 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `volume_bucket=volume_unknown` / `no_clear_edge`: volume_bucket=volume_unknown 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `time_bucket=time_0900_0930` / `no_clear_edge`: time_bucket=time_0900_0930 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `time_bucket=time_0930_1030` / `no_clear_edge`: time_bucket=time_0930_1030 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `time_bucket=time_1030_1400` / `no_clear_edge`: time_bucket=time_1030_1400 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `time_bucket=time_1400_1530` / `no_clear_edge`: time_bucket=time_1400_1530 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `time_bucket=time_outside_regular` / `no_clear_edge`: time_bucket=time_outside_regular 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.

## 다음 액션

- `ADM`은 shadow가 아니라 advisory canary/live-readiness 축으로 관리한다.
- `recommended_bias != no_clear_edge`이고 `policy_hint=candidate_weight_source`인 bucket만 다음 bounded canary 후보로 본다.
- all `no_clear_edge`이면 perfect spot 대기가 아니라 최소 edge 부재로 판정하고 live AI 응답을 바꾸지 않는다.
