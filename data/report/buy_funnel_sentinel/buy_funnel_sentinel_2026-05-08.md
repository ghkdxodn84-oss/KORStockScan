# BUY Funnel Sentinel 2026-05-08

## 판정

- primary: `UPSTREAM_AI_THRESHOLD`
- secondary: `LATENCY_DROUGHT`
- report_only: `true`
- live_runtime_effect: `false`

## 근거

- as_of: `2026-05-08T12:45:07`
- baseline_date: `2026-05-07`
- ai_confirmed unique: `114`
- budget_pass unique: `28`
- latency_pass unique: `7`
- submitted unique: `7`
- holding_started unique: `2`
- budget/ai unique: `24.6%` (baseline `25.5`)
- submitted/ai unique: `6.1%` (baseline `7.5`)
- top blockers: `blocked_strength_momentum:below_window_buy_value=71968, blocked_overbought:-=43310, blocked_strength_momentum:below_strength_base=32658, blocked_strength_momentum:insufficient_history=8461, blocked_strength_momentum:below_buy_ratio=6770`
- upstream blockers: `wait65_79_ev_candidate:score_65.0=286, blocked_ai_score:score_65.0=273, blocked_ai_score:ai_score_50_buy_hold_override=164, blocked_ai_score:score_45.0=150, first_ai_wait:-=95`
- latency blockers: `latency_block:latency_state_danger=439`
- price guards: `scale_in_price_guard_block:micro_vwap_bp>60.0=3`

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

- `5m`: ai=15, budget=1, latency=1, submitted=1, top=`blocked_strength_momentum:below_window_buy_value=1644, blocked_strength_momentum:below_strength_base=1141, blocked_overbought:-=689`, upstream=`wait65_79_ev_candidate:score_65.0=7, blocked_ai_score:score_65.0=7, blocked_ai_score:score_45.0=4`
- `10m`: ai=25, budget=1, latency=1, submitted=1, top=`blocked_strength_momentum:below_strength_base=2871, blocked_strength_momentum:below_window_buy_value=2801, blocked_overbought:-=1976`, upstream=`wait65_79_ev_candidate:score_65.0=20, blocked_ai_score:score_65.0=20, blocked_ai_score:ai_score_50_buy_hold_override=8`
- `30m`: ai=39, budget=7, latency=2, submitted=2, top=`blocked_strength_momentum:below_window_buy_value=10485, blocked_strength_momentum:below_strength_base=7164, blocked_overbought:-=6485`, upstream=`wait65_79_ev_candidate:score_65.0=39, blocked_ai_score:score_65.0=39, blocked_ai_score:ai_score_50_buy_hold_override=20`
