# BUY Funnel Sentinel 2026-05-12

## 판정

- primary: `UPSTREAM_AI_THRESHOLD`
- secondary: `-`
- report_only: `true`
- live_runtime_effect: `false`

## 근거

- as_of: `2026-05-12T10:45:06`
- baseline_date: `2026-05-11`
- ai_confirmed unique: `86`
- budget_pass unique: `0`
- latency_pass unique: `0`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `0.0%` (baseline `18.2`)
- submitted/ai unique: `0.0%` (baseline `3.9`)
- top blockers: `blocked_swing_score_vpw:-=80350, blocked_strength_momentum:below_window_buy_value=27899, blocked_strength_momentum:below_strength_base=22327, blocked_overbought:-=12159, blocked_strength_momentum:below_buy_ratio=5126`
- upstream blockers: `blocked_ai_score:score_62.0=227, first_ai_wait:-=76, blocked_ai_score:ai_score_50_buy_hold_override=67, blocked_ai_score:score_60.0=45, blocked_ai_score:score_58.0=37`
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

- `5m`: ai=9, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=3354, blocked_strength_momentum:below_strength_base=1657, blocked_strength_momentum:below_window_buy_value=892`, upstream=`blocked_ai_score:score_62.0=6, blocked_ai_score:score_60.0=2, blocked_ai_score:ai_score_50_buy_hold_override=2`
- `10m`: ai=11, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=6396, blocked_strength_momentum:below_strength_base=2807, blocked_strength_momentum:below_window_buy_value=1838`, upstream=`blocked_ai_score:score_62.0=12, blocked_ai_score:ai_score_50_buy_hold_override=5, blocked_ai_score:score_58.0=4`
- `30m`: ai=31, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=23168, blocked_strength_momentum:below_window_buy_value=7756, blocked_strength_momentum:below_strength_base=6921`, upstream=`blocked_ai_score:score_62.0=43, blocked_ai_score:ai_score_50_buy_hold_override=17, blocked_ai_score:score_58.0=12`
