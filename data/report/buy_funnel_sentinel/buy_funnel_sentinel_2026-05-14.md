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

- as_of: `2026-05-14T11:45:15`
- baseline_date: `2026-05-13`
- ai_confirmed unique: `71`
- budget_pass unique: `0`
- latency_pass unique: `0`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `0.0%` (baseline `0.0`)
- submitted/ai unique: `0.0%` (baseline `0.0`)
- top blockers: `blocked_swing_score_vpw:-=101004, blocked_strength_momentum:below_strength_base=75385, blocked_strength_momentum:below_window_buy_value=55657, blocked_swing_gap:-=31229, blocked_overbought:-=30979`
- upstream blockers: `blocked_ai_score:score_62.0=246, blocked_ai_score:ai_score_50_buy_hold_override=92, first_ai_wait:-=80, blocked_ai_score:score_60.0=28, blocked_ai_score:score_58.0=20`
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

- `5m`: ai=6, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=3408, blocked_strength_momentum:below_strength_base=2637, blocked_strength_momentum:below_window_buy_value=1684`, upstream=`first_ai_wait:-=4, blocked_ai_score:score_62.0=3, blocked_ai_score:score_60.0=2`
- `10m`: ai=11, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=7100, blocked_strength_momentum:below_strength_base=6293, blocked_overbought:-=3352`, upstream=`blocked_ai_score:score_62.0=10, first_ai_wait:-=7, blocked_ai_score:ai_score_50_buy_hold_override=4`
- `30m`: ai=17, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=21799, blocked_strength_momentum:below_strength_base=18713, blocked_strength_momentum:below_window_buy_value=9809`, upstream=`blocked_ai_score:score_62.0=29, blocked_ai_score:ai_score_50_buy_hold_override=25, first_ai_wait:-=22`
