# Holding/Exit Decision Matrix - 2026-05-07

## 판정

- matrix_version: `holding_exit_decision_matrix_v1_2026-05-07`
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
| price_bucket | price_10k_30k | no_clear_edge | -1.2343 | - | 7 | 0.7143 | defensive_only_high_loss_rate |
| price_bucket | price_30k_70k | no_clear_edge | -0.9435 | - | 10 | 0.5 | candidate_weight_source |
| price_bucket | price_gte_70k | no_clear_edge | -0.6607 | - | 17 | 0.4706 | candidate_weight_source |
| price_bucket | price_lt_10k | no_clear_edge | -1.2231 | - | 6 | 1 | defensive_only_high_loss_rate |
| volume_bucket | volume_2m_10m | no_clear_edge | -1.2675 | - | 7 | 0.7143 | defensive_only_high_loss_rate |
| volume_bucket | volume_500k_2m | no_clear_edge | -0.8755 | - | 21 | 0.619 | candidate_weight_source |
| volume_bucket | volume_gte_10m | no_clear_edge | - | - | - | - | insufficient_sample |
| volume_bucket | volume_lt_500k | no_clear_edge | -1.2563 | - | 8 | 0.625 | candidate_weight_source |
| volume_bucket | volume_unknown | no_clear_edge | - | - | - | - | insufficient_sample |
| time_bucket | time_0900_0930 | no_clear_edge | -1.2248 | - | 5 | 0.6 | candidate_weight_source |
| time_bucket | time_0930_1030 | no_clear_edge | -0.5857 | - | 16 | 0.4375 | candidate_weight_source |
| time_bucket | time_1030_1400 | no_clear_edge | -1.3788 | - | 13 | 0.9231 | defensive_only_high_loss_rate |
| time_bucket | time_1400_1530 | no_clear_edge | -0.728 | - | 5 | 0.2 | candidate_weight_source |
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

- `ADM-2`에서는 이 matrix를 holding/exit shadow prompt context로만 주입한다.
- action_label/confidence/reason drift를 보고 observe-only nudge 여부를 판정한다.
- single-owner canary 승인 전에는 live AI 응답을 바꾸지 않는다.
