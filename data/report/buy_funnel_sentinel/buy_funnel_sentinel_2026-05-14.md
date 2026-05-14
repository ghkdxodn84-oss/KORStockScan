# BUY Funnel Sentinel 2026-05-14

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

- as_of: `2026-05-14T15:20:05`
- baseline_date: `2026-05-13`
- ai_confirmed unique: `95`
- budget_pass unique: `0`
- latency_pass unique: `0`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `0.0%` (baseline `1.1`)
- submitted/ai unique: `0.0%` (baseline `0.0`)
- top blockers: `blocked_swing_score_vpw:-=239396, blocked_strength_momentum:below_strength_base=147831, blocked_strength_momentum:below_window_buy_value=139015, blocked_swing_gap:-=107614, blocked_overbought:-=95928`
- upstream blockers: `blocked_ai_score:score_62.0=452, blocked_ai_score:ai_score_50_buy_hold_override=204, first_ai_wait:-=118, blocked_ai_score:score_60.0=60, blocked_ai_score:score_58.0=43`
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

- `5m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_swing_gap:-=3367, blocked_swing_score_vpw:-=2776, blocked_gatekeeper_reject:눌림 대기=1`, upstream=`-`
- `10m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_swing_gap:-=6727, blocked_swing_score_vpw:-=5656, blocked_gatekeeper_reject:눌림 대기=2`, upstream=`-`
- `30m`: ai=16, budget=0, latency=0, submitted=0, top=`blocked_swing_gap:-=17194, blocked_swing_score_vpw:-=17089, blocked_overbought:-=4149`, upstream=`blocked_ai_score:score_62.0=14, blocked_ai_score:ai_score_50_buy_hold_override=5, first_ai_wait:-=3`
