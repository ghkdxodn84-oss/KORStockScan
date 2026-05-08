# BUY Funnel Sentinel 2026-05-08

## 판정

- primary: `UPSTREAM_AI_THRESHOLD`
- secondary: `LATENCY_DROUGHT`
- report_only: `true`
- live_runtime_effect: `false`

## 근거

- as_of: `2026-05-08T15:20:10`
- baseline_date: `2026-05-07`
- ai_confirmed unique: `116`
- budget_pass unique: `30`
- latency_pass unique: `9`
- submitted unique: `9`
- holding_started unique: `3`
- budget/ai unique: `25.9%` (baseline `25.9`)
- submitted/ai unique: `7.8%` (baseline `8.6`)
- top blockers: `blocked_strength_momentum:below_window_buy_value=110070, blocked_overbought:-=87284, blocked_strength_momentum:below_strength_base=67738, blocked_strength_momentum:insufficient_history=16442, blocked_strength_momentum:below_buy_ratio=9344`
- upstream blockers: `wait65_79_ev_candidate:score_65.0=456, blocked_ai_score:score_65.0=442, blocked_ai_score:score_45.0=256, blocked_ai_score:ai_score_50_buy_hold_override=242, blocked_ai_score:score_35.0=118`
- latency blockers: `latency_block:latency_state_danger=585`
- price guards: `scale_in_price_guard_block:micro_vwap_bp>60.0=3, entry_ai_price_canary_skip_order:매도 잔량 11배 우위의 극심한 불균형과 Latency DANGER 상태가 결합되어 하방 체결 위험이 매우 높음=1`

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

- `5m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_swing_gap:-=126, blocked_gatekeeper_reject:눌림 대기=1`, upstream=`-`
- `10m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_swing_gap:-=126, blocked_gatekeeper_reject:전량 회피=1, blocked_gatekeeper_reject:눌림 대기=1`, upstream=`-`
- `30m`: ai=19, budget=0, latency=0, submitted=0, top=`blocked_strength_momentum:below_strength_base=3214, blocked_overbought:-=2877, blocked_strength_momentum:below_window_buy_value=2433`, upstream=`wait65_79_ev_candidate:score_65.0=8, blocked_ai_score:score_65.0=8, blocked_ai_score:score_45.0=7`
