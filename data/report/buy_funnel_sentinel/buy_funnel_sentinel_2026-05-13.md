# BUY Funnel Sentinel 2026-05-13

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

- as_of: `2026-05-13T15:20:43`
- baseline_date: `2026-05-12`
- ai_confirmed unique: `88`
- budget_pass unique: `1`
- latency_pass unique: `0`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `1.1%` (baseline `0.0`)
- submitted/ai unique: `0.0%` (baseline `0.0`)
- top blockers: `blocked_swing_score_vpw:-=279784, blocked_overbought:-=198341, blocked_strength_momentum:below_strength_base=111008, blocked_strength_momentum:below_window_buy_value=102340, blocked_swing_gap:-=76377`
- upstream blockers: `blocked_ai_score:score_62.0=502, blocked_ai_score:ai_score_50_buy_hold_override=118, first_ai_wait:-=101, blocked_ai_score:score_60.0=58, blocked_ai_score:score_58.0=44`
- latency blockers: `latency_block:latency_state_danger=642`
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

- `5m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=4471, blocked_swing_gap:-=1440, blocked_gatekeeper_reject:눌림 대기=1`, upstream=`-`
- `10m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=9031, blocked_swing_gap:-=2880, blocked_gatekeeper_reject:눌림 대기=1`, upstream=`-`
- `30m`: ai=7, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=26758, blocked_overbought:-=9742, blocked_swing_gap:-=7518`, upstream=`blocked_ai_score:score_62.0=9, blocked_ai_score:ai_score_50_buy_hold_override=2, wait65_79_ev_candidate:score_74.0=1`
