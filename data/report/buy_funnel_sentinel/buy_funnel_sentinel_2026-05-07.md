# BUY Funnel Sentinel 2026-05-07

## 판정

- primary: `UPSTREAM_AI_THRESHOLD`
- secondary: `LATENCY_DROUGHT`
- report_only: `true`
- live_runtime_effect: `false`

## 근거

- as_of: `2026-05-07T15:23:05`
- baseline_date: `2026-05-06`
- ai_confirmed unique: `116`
- budget_pass unique: `30`
- latency_pass unique: `11`
- submitted unique: `10`
- holding_started unique: `8`
- budget/ai unique: `25.9%` (baseline `25.2`)
- submitted/ai unique: `8.6%` (baseline `5.4`)
- top blockers: `blocked_strength_momentum:below_strength_base=166600, blocked_strength_momentum:below_window_buy_value=138392, blocked_overbought:-=50425, blocked_strength_momentum:insufficient_history=25386, blocked_strength_momentum:below_buy_ratio=6912`
- upstream blockers: `blocked_ai_score:score_65.0=353, wait65_79_ev_candidate:score_65.0=349, blocked_ai_score:score_45.0=187, blocked_ai_score:ai_score_50_buy_hold_override=176, first_ai_wait:-=93`
- latency blockers: `latency_block:latency_state_danger=969`
- price guards: `scale_in_price_guard_block:micro_vwap_bp>60.0=4, entry_ai_price_canary_skip_order:Latency DANGER 상태와 매도 우위 호가 잔량(Net Bid Depth -3082)에 따른 가격 불확실성 및 체결 불리성 판단=1`

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

- `5m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_gatekeeper_reject:눌림 대기=1`, upstream=`-`
- `10m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_gatekeeper_reject:눌림 대기=2`, upstream=`-`
- `30m`: ai=9, budget=0, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=3300, blocked_strength_momentum:below_strength_base=3091, blocked_overbought:-=1135`, upstream=`wait65_79_ev_candidate:score_65.0=7, blocked_ai_score:score_65.0=7, blocked_ai_score:ai_score_50_buy_hold_override=3`
