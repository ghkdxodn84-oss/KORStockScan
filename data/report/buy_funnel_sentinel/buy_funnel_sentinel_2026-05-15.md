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

- as_of: `2026-05-15T15:20:07`
- baseline_date: `-`
- ai_confirmed unique: `100`
- budget_pass unique: `1`
- latency_pass unique: `0`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `1.0%` (baseline `-`)
- submitted/ai unique: `0.0%` (baseline `-`)
- top blockers: `blocked_swing_score_vpw:-=307146, blocked_strength_momentum:below_strength_base=180010, blocked_strength_momentum:below_window_buy_value=157678, blocked_overbought:-=51970, blocked_swing_gap:-=24919`
- upstream blockers: `blocked_ai_score:score_62.0=503, blocked_ai_score:ai_score_50_buy_hold_override=248, first_ai_wait:-=203, blocked_ai_score:score_60.0=69, blocked_ai_score:score_58.0=63`
- latency blockers: `latency_block:latency_state_danger=45`
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

- `5m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=4522, blocked_swing_gap:-=714, blocked_gatekeeper_reject:눌림 대기=1`, upstream=`-`
- `10m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=9190, blocked_swing_gap:-=1436, blocked_gatekeeper_reject:눌림 대기=2`, upstream=`-`
- `30m`: ai=5, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=28072, blocked_strength_momentum:below_strength_base=6994, blocked_strength_momentum:below_window_buy_value=5140`, upstream=`blocked_ai_score:score_62.0=4, blocked_ai_score:score_60.0=2, blocked_ai_score:ai_score_50_buy_hold_override=2`
