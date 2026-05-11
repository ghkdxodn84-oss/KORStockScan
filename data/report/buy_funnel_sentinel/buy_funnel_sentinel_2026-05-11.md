# BUY Funnel Sentinel 2026-05-11

## 판정

- primary: `PRICE_GUARD_DROUGHT`
- secondary: `LATENCY_DROUGHT, UPSTREAM_AI_THRESHOLD`
- report_only: `true`
- live_runtime_effect: `false`

## 근거

- as_of: `2026-05-11T12:55:07`
- baseline_date: `2026-05-08`
- ai_confirmed unique: `89`
- budget_pass unique: `15`
- latency_pass unique: `3`
- submitted unique: `3`
- holding_started unique: `0`
- budget/ai unique: `16.9%` (baseline `25.4`)
- submitted/ai unique: `3.4%` (baseline `7.0`)
- top blockers: `blocked_strength_momentum:below_window_buy_value=76402, blocked_strength_momentum:below_strength_base=59408, blocked_overbought:-=42590, blocked_strength_momentum:insufficient_history=11013, blocked_strength_momentum:below_buy_ratio=6291`
- upstream blockers: `first_ai_wait:-=356, blocked_ai_score:ai_score_50_buy_hold_override=308, blocked_ai_score:score_62.0=262, wait65_79_ev_candidate:score_65.0=85, blocked_ai_score:score_65.0=73`
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

- `5m`: ai=11, budget=0, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=2159, blocked_overbought:-=1791, blocked_strength_momentum:below_strength_base=1339`, upstream=`blocked_ai_score:score_62.0=4, blocked_ai_score:ai_score_50_buy_hold_override=4, blocked_ai_score:score_64.0=2`
- `10m`: ai=17, budget=0, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=4046, blocked_overbought:-=3532, blocked_strength_momentum:below_strength_base=3378`, upstream=`blocked_ai_score:score_62.0=12, blocked_ai_score:ai_score_50_buy_hold_override=8, blocked_ai_score:score_58.0=3`
- `30m`: ai=32, budget=0, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=14791, blocked_strength_momentum:below_strength_base=10252, blocked_overbought:-=8981`, upstream=`blocked_ai_score:score_62.0=46, blocked_ai_score:ai_score_50_buy_hold_override=16, first_ai_wait:-=14`
