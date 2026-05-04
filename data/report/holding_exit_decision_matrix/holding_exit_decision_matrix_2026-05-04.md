# Holding/Exit Decision Matrix - 2026-05-04

## 판정

- matrix_version: `holding_exit_decision_matrix_v1_2026-05-04`
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
| price_bucket | price_10k_30k | no_clear_edge | -0.8097 | - | 29 | 0.5862 | candidate_weight_source |
| price_bucket | price_30k_70k | no_clear_edge | -1.0307 | - | 14 | 0.5714 | candidate_weight_source |
| price_bucket | price_gte_70k | prefer_pyramid_wait | -0.2515 | 0.322 | 6 | 0.3333 | candidate_weight_source |
| price_bucket | price_lt_10k | prefer_pyramid_wait | -0.4392 | 0.9424 | 5 | 0.4 | candidate_weight_source |
| volume_bucket | volume_2m_10m | prefer_pyramid_wait | -0.3157 | 0.5689 | 5 | 0.6 | candidate_weight_source |
| volume_bucket | volume_500k_2m | no_clear_edge | -0.8226 | - | 44 | 0.6136 | candidate_weight_source |
| volume_bucket | volume_gte_10m | no_clear_edge | -1.0901 | - | 14 | 0.6429 | candidate_weight_source |
| volume_bucket | volume_lt_500k | no_clear_edge | -0.8084 | - | 20 | 0.55 | candidate_weight_source |
| volume_bucket | volume_unknown | no_clear_edge | -1.1138 | - | 6 | 0.5 | candidate_weight_source |
| time_bucket | time_0900_0930 | no_clear_edge | -0.9556 | - | 21 | 0.5714 | candidate_weight_source |
| time_bucket | time_0930_1030 | no_clear_edge | -0.6363 | - | 31 | 0.4839 | candidate_weight_source |
| time_bucket | time_1030_1400 | prefer_pyramid_wait | -0.0612 | 0.9723 | 10 | 0.3 | candidate_weight_source |
| time_bucket | time_1400_1530 | no_clear_edge | -0.5005 | - | 10 | 0.2 | candidate_weight_source |
| time_bucket | time_outside_regular | no_clear_edge | - | - | - | - | insufficient_sample |

## Prompt Hints

- `price_bucket=price_10k_30k` / `no_clear_edge`: price_bucket=price_10k_30k 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `price_bucket=price_30k_70k` / `no_clear_edge`: price_bucket=price_30k_70k 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `price_bucket=price_gte_70k` / `prefer_pyramid_wait`: price_bucket=price_gte_70k 과거 표본은 winner size-up 대기 후보가 상대적으로 우위다. trailing giveback과 체결품질을 확인한다.
- `price_bucket=price_lt_10k` / `prefer_pyramid_wait`: price_bucket=price_lt_10k 과거 표본은 winner size-up 대기 후보가 상대적으로 우위다. trailing giveback과 체결품질을 확인한다.
- `volume_bucket=volume_2m_10m` / `prefer_pyramid_wait`: volume_bucket=volume_2m_10m 과거 표본은 winner size-up 대기 후보가 상대적으로 우위다. trailing giveback과 체결품질을 확인한다.
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
