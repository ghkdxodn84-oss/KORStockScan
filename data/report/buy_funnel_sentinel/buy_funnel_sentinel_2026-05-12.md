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

- as_of: `2026-05-12T15:20:23`
- baseline_date: `2026-05-11`
- ai_confirmed unique: `100`
- budget_pass unique: `0`
- latency_pass unique: `0`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `0.0%` (baseline `15.7`)
- submitted/ai unique: `0.0%` (baseline `2.9`)
- top blockers: `blocked_swing_score_vpw:-=377842, blocked_strength_momentum:below_strength_base=189913, blocked_strength_momentum:below_window_buy_value=102860, blocked_overbought:-=80361, blocked_swing_gap:-=35971`
- upstream blockers: `blocked_ai_score:score_62.0=440, blocked_ai_score:ai_score_50_buy_hold_override=182, first_ai_wait:-=113, blocked_ai_score:score_60.0=63, blocked_ai_score:score_58.0=56`
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

- `5m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=6019, blocked_swing_gap:-=473`, upstream=`-`
- `10m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=12071, blocked_swing_gap:-=921`, upstream=`-`
- `30m`: ai=9, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=34111, blocked_strength_momentum:below_strength_base=6466, blocked_swing_gap:-=3368`, upstream=`blocked_ai_score:score_62.0=13, blocked_ai_score:ai_score_50_buy_hold_override=3, blocked_ai_score:score_58.0=2`
