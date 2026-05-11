# BUY Funnel Sentinel 2026-05-11

## 판정

- primary: `PRICE_GUARD_DROUGHT`
- secondary: `LATENCY_DROUGHT, UPSTREAM_AI_THRESHOLD`
- report_only: `true`
- live_runtime_effect: `false`

## 근거

- as_of: `2026-05-11T11:15:05`
- baseline_date: `2026-05-08`
- ai_confirmed unique: `82`
- budget_pass unique: `14`
- latency_pass unique: `3`
- submitted unique: `3`
- holding_started unique: `0`
- budget/ai unique: `17.1%` (baseline `17.3`)
- submitted/ai unique: `3.7%` (baseline `4.1`)
- top blockers: `blocked_strength_momentum:below_window_buy_value=37702, blocked_strength_momentum:below_strength_base=26164, blocked_overbought:-=14456, blocked_strength_momentum:below_buy_ratio=4886, blocked_strength_momentum:insufficient_history=3754`
- upstream blockers: `first_ai_wait:-=231, blocked_ai_score:ai_score_50_buy_hold_override=210, wait65_79_ev_candidate:score_65.0=84, blocked_ai_score:score_62.0=81, blocked_ai_score:score_65.0=72`
- latency blockers: `latency_block:latency_state_danger=535`
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

- `5m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=4290, blocked_strength_momentum:below_strength_base=2000, blocked_overbought:-=1000`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=5, blocked_ai_score:score_62.0=3, blocked_ai_score:score_58.0=2`
- `10m`: ai=10, budget=0, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=6917, blocked_strength_momentum:below_strength_base=3942, blocked_overbought:-=2026`, upstream=`blocked_ai_score:score_62.0=9, blocked_ai_score:ai_score_50_buy_hold_override=9, blocked_ai_score:score_58.0=4`
- `30m`: ai=35, budget=0, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=16211, blocked_strength_momentum:below_strength_base=10572, blocked_overbought:-=4299`, upstream=`blocked_ai_score:score_62.0=50, first_ai_wait:-=43, blocked_ai_score:ai_score_50_buy_hold_override=29`
