# BUY Funnel Sentinel 2026-05-12

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

- as_of: `2026-05-12T12:05:11`
- baseline_date: `2026-05-11`
- ai_confirmed unique: `87`
- budget_pass unique: `0`
- latency_pass unique: `0`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `0.0%` (baseline `17.2`)
- submitted/ai unique: `0.0%` (baseline `3.4`)
- top blockers: `blocked_swing_score_vpw:-=168486, blocked_strength_momentum:below_strength_base=80928, blocked_strength_momentum:below_window_buy_value=52393, blocked_overbought:-=29521, blocked_strength_momentum:below_buy_ratio=16173`
- upstream blockers: `blocked_ai_score:score_62.0=264, blocked_ai_score:ai_score_50_buy_hold_override=104, first_ai_wait:-=77, blocked_ai_score:score_60.0=47, blocked_ai_score:score_58.0=39`
- latency blockers: `-`
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

- `5m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=5876, blocked_strength_momentum:below_strength_base=4062, blocked_strength_momentum:below_window_buy_value=1707`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=3, blocked_ai_score:score_62.0=1`
- `10m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=11778, blocked_strength_momentum:below_strength_base=8148, blocked_strength_momentum:below_window_buy_value=3174`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=6, blocked_ai_score:score_62.0=2`
- `30m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=35334, blocked_strength_momentum:below_strength_base=24456, blocked_strength_momentum:below_window_buy_value=9356`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=17, blocked_ai_score:score_62.0=6`
