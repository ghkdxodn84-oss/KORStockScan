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

- as_of: `2026-05-14T14:45:06`
- baseline_date: `2026-05-13`
- ai_confirmed unique: `93`
- budget_pass unique: `0`
- latency_pass unique: `0`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `0.0%` (baseline `1.1`)
- submitted/ai unique: `0.0%` (baseline `0.0`)
- top blockers: `blocked_swing_score_vpw:-=219115, blocked_strength_momentum:below_strength_base=142760, blocked_strength_momentum:below_window_buy_value=133485, blocked_overbought:-=89475, blocked_swing_gap:-=88369`
- upstream blockers: `blocked_ai_score:score_62.0=433, blocked_ai_score:ai_score_50_buy_hold_override=198, first_ai_wait:-=115, blocked_ai_score:score_60.0=59, blocked_ai_score:score_58.0=41`
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

- `5m`: ai=12, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=2963, blocked_strength_momentum:below_strength_base=2870, blocked_swing_gap:-=1959`, upstream=`blocked_ai_score:score_62.0=7, blocked_ai_score:ai_score_50_buy_hold_override=3, blocked_ai_score:score_60.0=2`
- `10m`: ai=17, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=5912, blocked_strength_momentum:below_strength_base=5589, blocked_swing_gap:-=4225`, upstream=`blocked_ai_score:score_62.0=15, blocked_ai_score:ai_score_50_buy_hold_override=4, blocked_ai_score:score_60.0=4`
- `30m`: ai=22, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=18734, blocked_strength_momentum:below_strength_base=13260, blocked_strength_momentum:below_window_buy_value=11864`, upstream=`blocked_ai_score:score_62.0=40, blocked_ai_score:ai_score_50_buy_hold_override=10, blocked_ai_score:score_60.0=7`
