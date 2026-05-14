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

- as_of: `2026-05-14T13:50:11`
- baseline_date: `2026-05-13`
- ai_confirmed unique: `86`
- budget_pass unique: `0`
- latency_pass unique: `0`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `0.0%` (baseline `0.0`)
- submitted/ai unique: `0.0%` (baseline `0.0`)
- top blockers: `blocked_swing_score_vpw:-=186632, blocked_strength_momentum:below_strength_base=120763, blocked_strength_momentum:below_window_buy_value=112288, blocked_overbought:-=70824, blocked_swing_gap:-=68613`
- upstream blockers: `blocked_ai_score:score_62.0=366, blocked_ai_score:ai_score_50_buy_hold_override=173, first_ai_wait:-=105, blocked_ai_score:score_60.0=48, blocked_ai_score:score_58.0=35`
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

- `5m`: ai=9, budget=0, latency=0, submitted=0, top=`blocked_strength_momentum:below_strength_base=2958, blocked_swing_score_vpw:-=2853, blocked_swing_gap:-=1640`, upstream=`blocked_ai_score:score_62.0=6, blocked_ai_score:ai_score_50_buy_hold_override=4, blocked_ai_score:score_60.0=1`
- `10m`: ai=12, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=5437, blocked_strength_momentum:below_strength_base=5300, blocked_swing_gap:-=3296`, upstream=`blocked_ai_score:score_62.0=9, blocked_ai_score:ai_score_50_buy_hold_override=7, blocked_ai_score:score_60.0=2`
- `30m`: ai=21, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=17209, blocked_strength_momentum:below_window_buy_value=11841, blocked_strength_momentum:below_strength_base=11009`, upstream=`blocked_ai_score:score_62.0=25, blocked_ai_score:ai_score_50_buy_hold_override=18, blocked_ai_score:score_60.0=6`
