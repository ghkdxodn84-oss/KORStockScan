# BUY Funnel Sentinel 2026-05-06

## 판정

- primary: `UPSTREAM_AI_THRESHOLD`
- secondary: `LATENCY_DROUGHT`
- report_only: `true`
- live_runtime_effect: `false`

## 근거

- as_of: `2026-05-06T15:20:13`
- baseline_date: `2026-05-04`
- ai_confirmed unique: `111`
- budget_pass unique: `28`
- latency_pass unique: `6`
- submitted unique: `6`
- holding_started unique: `4`
- budget/ai unique: `25.2%` (baseline `78.3`)
- submitted/ai unique: `5.4%` (baseline `38.9`)
- top blockers: `blocked_strength_momentum:below_window_buy_value=142209, blocked_strength_momentum:below_strength_base=101505, blocked_overbought:-=97183, blocked_strength_momentum:insufficient_history=22874, blocked_swing_gap:-=12053`
- upstream blockers: `wait65_79_ev_candidate:score_65.0=378, blocked_ai_score:score_65.0=373, blocked_ai_score:ai_score_50_buy_hold_override=281, first_ai_wait:-=246, blocked_ai_score:score_45.0=186`
- latency blockers: `latency_block:latency_state_danger=838`
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

- `5m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_swing_gap:-=201, blocked_gatekeeper_reject:눌림 대기=1`, upstream=`-`
- `10m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_swing_gap:-=456, blocked_gatekeeper_reject:눌림 대기=1`, upstream=`-`
- `30m`: ai=19, budget=1, latency=0, submitted=0, top=`blocked_overbought:-=4297, blocked_strength_momentum:below_strength_base=3225, blocked_strength_momentum:below_window_buy_value=2866`, upstream=`wait65_79_ev_candidate:score_65.0=9, blocked_ai_score:score_65.0=9, blocked_ai_score:score_45.0=5`
