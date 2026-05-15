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

- as_of: `2026-05-15T12:10:07`
- baseline_date: `2026-05-14`
- ai_confirmed unique: `89`
- budget_pass unique: `0`
- latency_pass unique: `0`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `0.0%` (baseline `0.0`)
- submitted/ai unique: `0.0%` (baseline `0.0`)
- top blockers: `blocked_swing_score_vpw:-=145853, blocked_strength_momentum:below_window_buy_value=77659, blocked_strength_momentum:below_strength_base=71908, blocked_overbought:-=15946, blocked_swing_gap:-=10670`
- upstream blockers: `blocked_ai_score:score_62.0=345, blocked_ai_score:ai_score_50_buy_hold_override=179, first_ai_wait:-=168, blocked_ai_score:score_58.0=47, blocked_ai_score:score_60.0=46`
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

- `5m`: ai=7, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=4820, blocked_strength_momentum:below_strength_base=3183, blocked_strength_momentum:below_window_buy_value=2095`, upstream=`blocked_ai_score:score_62.0=6, blocked_ai_score:ai_score_50_buy_hold_override=4, first_ai_wait:-=3`
- `10m`: ai=16, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=8921, blocked_strength_momentum:below_window_buy_value=5037, blocked_strength_momentum:below_strength_base=5004`, upstream=`blocked_ai_score:score_62.0=18, first_ai_wait:-=13, blocked_ai_score:ai_score_50_buy_hold_override=13`
- `30m`: ai=26, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=27681, blocked_strength_momentum:below_window_buy_value=15861, blocked_strength_momentum:below_strength_base=14586`, upstream=`blocked_ai_score:score_62.0=44, first_ai_wait:-=23, blocked_ai_score:ai_score_50_buy_hold_override=19`
