# BUY Funnel Sentinel 2026-05-15

## 판정

- primary: `UPSTREAM_AI_THRESHOLD`
- secondary: `-`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `score65_74_counterfactual_review`
- followup_owner: `postclose_threshold_cycle`
- runtime_effect: `report_only_no_mutation`

## 근거

- as_of: `2026-05-15T14:50:08`
- baseline_date: `-`
- ai_confirmed unique: `100`
- budget_pass unique: `1`
- latency_pass unique: `0`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `1.0%` (baseline `-`)
- submitted/ai unique: `0.0%` (baseline `-`)
- top blockers: `blocked_swing_score_vpw:-=279014, blocked_strength_momentum:below_strength_base=172971, blocked_strength_momentum:below_window_buy_value=152505, blocked_overbought:-=49401, blocked_strength_momentum:insufficient_history=22880`
- upstream blockers: `blocked_ai_score:score_62.0=499, blocked_ai_score:ai_score_50_buy_hold_override=246, first_ai_wait:-=203, blocked_ai_score:score_60.0=67, blocked_ai_score:score_58.0=63`
- latency blockers: `latency_block:latency_state_danger=45`
- price guards: `-`

## 금지된 자동변경

- `score_threshold_relaxation`
- `spread_cap_relaxation`
- `fallback_reenable`
- `live_threshold_runtime_mutation`
- `bot_restart`

## 권고 액션

- Append score50/wait65_74 missed-winner and avoided-loser cohorts to report-only review.
- Do not relax score threshold or revive fallback without a new single-axis workorder.

## Window Summary

- `5m`: ai=4, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=4373, blocked_strength_momentum:below_strength_base=3643, blocked_strength_momentum:below_window_buy_value=2286`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=2, blocked_ai_score:score_62.0=2, blocked_ai_score:score_58.0=1`
- `10m`: ai=4, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=8534, blocked_strength_momentum:below_strength_base=7872, blocked_strength_momentum:below_window_buy_value=4001`, upstream=`blocked_ai_score:score_62.0=5, blocked_ai_score:ai_score_50_buy_hold_override=3, blocked_ai_score:score_58.0=2`
- `30m`: ai=8, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=25124, blocked_strength_momentum:below_strength_base=23475, blocked_strength_momentum:below_window_buy_value=12743`, upstream=`blocked_ai_score:score_62.0=14, blocked_ai_score:ai_score_50_buy_hold_override=6, blocked_ai_score:score_60.0=4`
