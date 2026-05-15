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

- as_of: `2026-05-15T12:20:06`
- baseline_date: `2026-05-14`
- ai_confirmed unique: `91`
- budget_pass unique: `0`
- latency_pass unique: `0`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `0.0%` (baseline `0.0`)
- submitted/ai unique: `0.0%` (baseline `0.0`)
- top blockers: `blocked_swing_score_vpw:-=154934, blocked_strength_momentum:below_window_buy_value=83499, blocked_strength_momentum:below_strength_base=77703, blocked_overbought:-=17478, blocked_swing_gap:-=11125`
- upstream blockers: `blocked_ai_score:score_62.0=357, blocked_ai_score:ai_score_50_buy_hold_override=189, first_ai_wait:-=175, blocked_ai_score:score_58.0=48, blocked_ai_score:score_60.0=47`
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

- `5m`: ai=9, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=4261, blocked_strength_momentum:below_window_buy_value=2973, blocked_strength_momentum:below_strength_base=2586`, upstream=`blocked_ai_score:score_62.0=8, blocked_ai_score:ai_score_50_buy_hold_override=7, first_ai_wait:-=6`
- `10m`: ai=11, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=9041, blocked_strength_momentum:below_window_buy_value=5811, blocked_strength_momentum:below_strength_base=5768`, upstream=`blocked_ai_score:score_62.0=12, blocked_ai_score:ai_score_50_buy_hold_override=10, first_ai_wait:-=7`
- `30m`: ai=23, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=27375, blocked_strength_momentum:below_window_buy_value=17181, blocked_strength_momentum:below_strength_base=15077`, upstream=`blocked_ai_score:score_62.0=42, blocked_ai_score:ai_score_50_buy_hold_override=25, first_ai_wait:-=24`
