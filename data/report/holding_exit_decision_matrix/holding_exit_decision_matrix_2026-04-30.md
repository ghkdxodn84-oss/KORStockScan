# Holding/Exit Decision Matrix - 2026-04-30

## 판정

- matrix_version: `holding_exit_decision_matrix_v1_2026-04-30`
- application_mode: `shadow_prompt_or_observe_only_until_owner_approval`
- runtime_change: `False`

## Hard Veto

- `emergency_or_hard_stop`
- `active_sell_order_pending`
- `invalid_feature`
- `post_add_eval_exclusion`

## Matrix Entries

| axis | bucket | bias | score | edge | sample | loss_rate | policy |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| price_bucket | price_10k_30k | no_clear_edge | -0.8565 | - | 28 | 0.6071 | candidate_weight_source |
| price_bucket | price_30k_70k | no_clear_edge | -0.7862 | - | 12 | 0.4167 | candidate_weight_source |
| price_bucket | price_gte_70k | no_clear_edge | -0.777 | - | 44 | 0.5909 | candidate_weight_source |
| price_bucket | price_lt_10k | no_clear_edge | -1.3113 | - | 15 | 0.8 | defensive_only_high_loss_rate |
| volume_bucket | volume_2m_10m | no_clear_edge | -0.8253 | - | 29 | 0.5862 | candidate_weight_source |
| volume_bucket | volume_500k_2m | no_clear_edge | -0.8771 | - | 33 | 0.6061 | candidate_weight_source |
| volume_bucket | volume_gte_10m | no_clear_edge | -1.0943 | - | 14 | 0.6429 | candidate_weight_source |
| volume_bucket | volume_lt_500k | no_clear_edge | -0.8937 | - | 18 | 0.6111 | candidate_weight_source |
| volume_bucket | volume_unknown | no_clear_edge | -1.2711 | - | 5 | 0.6 | candidate_weight_source |
| time_bucket | time_0900_0930 | no_clear_edge | -0.9939 | - | 16 | 0.5625 | candidate_weight_source |
| time_bucket | time_0930_1030 | no_clear_edge | -0.9342 | - | 24 | 0.5417 | candidate_weight_source |
| time_bucket | time_1030_1400 | prefer_pyramid_wait | 0.9172 | 1.8351 | 6 | 0 | candidate_weight_source |
| time_bucket | time_1400_1530 | no_clear_edge | -0.6304 | - | 10 | 0.3 | candidate_weight_source |
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
- `time_bucket=time_1030_1400` / `prefer_pyramid_wait`: time_bucket=time_1030_1400 과거 표본은 winner size-up 대기 후보가 상대적으로 우위다. trailing giveback과 체결품질을 확인한다.
- `time_bucket=time_1400_1530` / `no_clear_edge`: time_bucket=time_1400_1530 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `time_bucket=time_outside_regular` / `no_clear_edge`: time_bucket=time_outside_regular 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.

## 다음 액션

- `ADM-2`에서는 이 matrix를 holding/exit shadow prompt context로만 주입한다.
- action_label/confidence/reason drift를 보고 observe-only nudge 여부를 판정한다.
- single-owner canary 승인 전에는 live AI 응답을 바꾸지 않는다.
