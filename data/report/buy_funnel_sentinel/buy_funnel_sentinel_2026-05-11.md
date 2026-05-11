# BUY Funnel Sentinel 2026-05-11

## 판정

- primary: `PRICE_GUARD_DROUGHT`
- secondary: `LATENCY_DROUGHT, UPSTREAM_AI_THRESHOLD`
- report_only: `true`
- live_runtime_effect: `false`

## 근거

- as_of: `2026-05-11T12:00:06`
- baseline_date: `2026-05-08`
- ai_confirmed unique: `87`
- budget_pass unique: `15`
- latency_pass unique: `3`
- submitted unique: `3`
- holding_started unique: `0`
- budget/ai unique: `17.2%` (baseline `21.0`)
- submitted/ai unique: `3.4%` (baseline `5.7`)
- top blockers: `blocked_strength_momentum:below_window_buy_value=53633, blocked_strength_momentum:below_strength_base=39625, blocked_overbought:-=25953, blocked_strength_momentum:insufficient_history=6315, blocked_strength_momentum:below_buy_ratio=5616`
- upstream blockers: `first_ai_wait:-=301, blocked_ai_score:ai_score_50_buy_hold_override=261, blocked_ai_score:score_62.0=164, wait65_79_ev_candidate:score_65.0=85, blocked_ai_score:score_65.0=73`
- latency blockers: `latency_block:latency_state_danger=611`
- price guards: `scale_in_price_guard_block:micro_vwap_bp>60.0=13`

## 금지된 자동변경

- `score_threshold_relaxation`
- `spread_cap_relaxation`
- `fallback_reenable`
- `live_threshold_runtime_mutation`
- `bot_restart`

## 권고 액션

- Review top price guard block labels and affected symbols.
- Keep threshold/runtime mutation blocked before ThresholdOpsTransition0506.

## Window Summary

- `5m`: ai=12, budget=0, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=1810, blocked_strength_momentum:below_strength_base=1652, blocked_overbought:-=1065`, upstream=`first_ai_wait:-=13, blocked_ai_score:score_62.0=10, blocked_ai_score:ai_score_50_buy_hold_override=7`
- `10m`: ai=17, budget=0, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=3443, blocked_strength_momentum:below_strength_base=3259, blocked_overbought:-=1855`, upstream=`first_ai_wait:-=27, blocked_ai_score:score_62.0=22, blocked_ai_score:ai_score_50_buy_hold_override=16`
- `30m`: ai=32, budget=1, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=10702, blocked_strength_momentum:below_strength_base=9391, blocked_overbought:-=7550`, upstream=`blocked_ai_score:score_62.0=57, first_ai_wait:-=44, blocked_ai_score:ai_score_50_buy_hold_override=34`
