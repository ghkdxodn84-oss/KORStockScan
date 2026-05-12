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

- as_of: `2026-05-12T13:10:17`
- baseline_date: `2026-05-11`
- ai_confirmed unique: `95`
- budget_pass unique: `0`
- latency_pass unique: `0`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `0.0%` (baseline `16.0`)
- submitted/ai unique: `0.0%` (baseline `3.2`)
- top blockers: `blocked_swing_score_vpw:-=237880, blocked_strength_momentum:below_strength_base=121131, blocked_strength_momentum:below_window_buy_value=71997, blocked_overbought:-=47220, blocked_swing_gap:-=20215`
- upstream blockers: `blocked_ai_score:score_62.0=322, blocked_ai_score:ai_score_50_buy_hold_override=138, first_ai_wait:-=104, blocked_ai_score:score_60.0=56, blocked_ai_score:score_58.0=44`
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

- `5m`: ai=9, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=5025, blocked_strength_momentum:below_strength_base=2647, blocked_strength_momentum:below_window_buy_value=1617`, upstream=`blocked_ai_score:score_62.0=5, blocked_ai_score:ai_score_50_buy_hold_override=2, blocked_ai_score:score_58.0=2`
- `10m`: ai=9, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=10425, blocked_strength_momentum:below_strength_base=6159, blocked_overbought:-=3659`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=6, blocked_ai_score:score_62.0=6, blocked_ai_score:score_58.0=2`
- `30m`: ai=19, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=31500, blocked_strength_momentum:below_strength_base=14691, blocked_strength_momentum:below_window_buy_value=10681`, upstream=`blocked_ai_score:score_62.0=32, blocked_ai_score:ai_score_50_buy_hold_override=13, first_ai_wait:-=6`
