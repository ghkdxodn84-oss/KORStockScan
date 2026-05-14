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

- as_of: `2026-05-14T10:40:27`
- baseline_date: `2026-05-13`
- ai_confirmed unique: `62`
- budget_pass unique: `0`
- latency_pass unique: `0`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `0.0%` (baseline `0.0`)
- submitted/ai unique: `0.0%` (baseline `0.0`)
- top blockers: `blocked_swing_score_vpw:-=56783, blocked_strength_momentum:below_strength_base=38899, blocked_strength_momentum:below_window_buy_value=33174, blocked_swing_gap:-=15524, blocked_overbought:-=13675`
- upstream blockers: `blocked_ai_score:score_62.0=177, first_ai_wait:-=49, blocked_ai_score:ai_score_50_buy_hold_override=41, blocked_ai_score:score_60.0=17, blocked_ai_score:score_58.0=16`
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

- `5m`: ai=11, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=3330, blocked_strength_momentum:below_strength_base=2709, blocked_strength_momentum:below_window_buy_value=1858`, upstream=`blocked_ai_score:score_62.0=9, blocked_ai_score:score_58.0=2, blocked_ai_score:ai_score_50_buy_hold_override=1`
- `10m`: ai=16, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=6409, blocked_strength_momentum:below_strength_base=5426, blocked_strength_momentum:below_window_buy_value=3815`, upstream=`blocked_ai_score:score_62.0=20, blocked_ai_score:ai_score_50_buy_hold_override=3, blocked_ai_score:score_58.0=2`
- `30m`: ai=32, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=18550, blocked_strength_momentum:below_strength_base=14490, blocked_strength_momentum:below_window_buy_value=11777`, upstream=`blocked_ai_score:score_62.0=50, blocked_ai_score:ai_score_50_buy_hold_override=13, first_ai_wait:-=5`
