# BUY Funnel Sentinel 2026-05-13

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

- as_of: `2026-05-13T11:10:15`
- baseline_date: `2026-05-12`
- ai_confirmed unique: `63`
- budget_pass unique: `0`
- latency_pass unique: `0`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `0.0%` (baseline `0.0`)
- submitted/ai unique: `0.0%` (baseline `0.0`)
- top blockers: `blocked_swing_score_vpw:-=86024, blocked_strength_momentum:below_strength_base=43757, blocked_strength_momentum:below_window_buy_value=41866, blocked_overbought:-=36986, blocked_strength_momentum:below_buy_ratio=8654`
- upstream blockers: `blocked_ai_score:score_62.0=194, first_ai_wait:-=64, blocked_ai_score:ai_score_50_buy_hold_override=47, blocked_ai_score:score_60.0=28, blocked_ai_score:score_58.0=17`
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

- `5m`: ai=13, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=3042, blocked_strength_momentum:below_window_buy_value=1963, blocked_overbought:-=1935`, upstream=`first_ai_wait:-=8, blocked_ai_score:score_62.0=5, blocked_ai_score:ai_score_50_buy_hold_override=3`
- `10m`: ai=15, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=6768, blocked_strength_momentum:below_window_buy_value=3952, blocked_overbought:-=3808`, upstream=`blocked_ai_score:score_62.0=12, first_ai_wait:-=9, blocked_ai_score:score_60.0=4`
- `30m`: ai=28, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=22104, blocked_overbought:-=12460, blocked_strength_momentum:below_window_buy_value=10888`, upstream=`blocked_ai_score:score_62.0=48, first_ai_wait:-=12, blocked_ai_score:ai_score_50_buy_hold_override=7`
