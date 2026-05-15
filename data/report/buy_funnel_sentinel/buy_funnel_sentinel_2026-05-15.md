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

- as_of: `2026-05-15T12:55:06`
- baseline_date: `2026-05-14`
- ai_confirmed unique: `93`
- budget_pass unique: `0`
- latency_pass unique: `0`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `0.0%` (baseline `0.0`)
- submitted/ai unique: `0.0%` (baseline `0.0`)
- top blockers: `blocked_swing_score_vpw:-=184767, blocked_strength_momentum:below_strength_base=100267, blocked_strength_momentum:below_window_buy_value=98417, blocked_overbought:-=24738, blocked_swing_gap:-=13222`
- upstream blockers: `blocked_ai_score:score_62.0=390, blocked_ai_score:ai_score_50_buy_hold_override=212, first_ai_wait:-=193, blocked_ai_score:score_60.0=53, blocked_ai_score:score_58.0=52`
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

- `5m`: ai=7, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=3437, blocked_strength_momentum:below_strength_base=3011, blocked_strength_momentum:below_window_buy_value=2087`, upstream=`blocked_ai_score:score_62.0=5, blocked_ai_score:ai_score_50_buy_hold_override=3, first_ai_wait:-=2`
- `10m`: ai=9, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=7152, blocked_strength_momentum:below_strength_base=6284, blocked_strength_momentum:below_window_buy_value=4220`, upstream=`blocked_ai_score:score_62.0=12, blocked_ai_score:ai_score_50_buy_hold_override=6, first_ai_wait:-=2`
- `30m`: ai=17, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=24793, blocked_strength_momentum:below_strength_base=18574, blocked_strength_momentum:below_window_buy_value=12771`, upstream=`blocked_ai_score:score_62.0=30, blocked_ai_score:ai_score_50_buy_hold_override=20, first_ai_wait:-=16`
