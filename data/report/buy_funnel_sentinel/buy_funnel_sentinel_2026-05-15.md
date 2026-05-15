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

- as_of: `2026-05-15T12:35:06`
- baseline_date: `2026-05-14`
- ai_confirmed unique: `91`
- budget_pass unique: `0`
- latency_pass unique: `0`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `0.0%` (baseline `0.0`)
- submitted/ai unique: `0.0%` (baseline `0.0`)
- top blockers: `blocked_swing_score_vpw:-=169059, blocked_strength_momentum:below_window_buy_value=89942, blocked_strength_momentum:below_strength_base=87300, blocked_overbought:-=20436, blocked_swing_gap:-=11831`
- upstream blockers: `blocked_ai_score:score_62.0=370, blocked_ai_score:ai_score_50_buy_hold_override=200, first_ai_wait:-=188, blocked_ai_score:score_60.0=51, blocked_ai_score:score_58.0=50`
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

- `5m`: ai=11, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=4555, blocked_strength_momentum:below_strength_base=2761, blocked_strength_momentum:below_window_buy_value=2345`, upstream=`first_ai_wait:-=10, blocked_ai_score:score_62.0=6, blocked_ai_score:ai_score_50_buy_hold_override=5`
- `10m`: ai=12, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=9085, blocked_strength_momentum:below_strength_base=5607, blocked_strength_momentum:below_window_buy_value=4296`, upstream=`first_ai_wait:-=11, blocked_ai_score:score_62.0=10, blocked_ai_score:ai_score_50_buy_hold_override=8`
- `30m`: ai=16, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=28046, blocked_strength_momentum:below_strength_base=18588, blocked_strength_momentum:below_window_buy_value=14386`, upstream=`blocked_ai_score:score_62.0=31, blocked_ai_score:ai_score_50_buy_hold_override=25, first_ai_wait:-=23`
