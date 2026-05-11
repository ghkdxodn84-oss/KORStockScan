# BUY Funnel Sentinel 2026-05-11

## 판정

- primary: `PRICE_GUARD_DROUGHT`
- secondary: `LATENCY_DROUGHT, UPSTREAM_AI_THRESHOLD`
- report_only: `true`
- live_runtime_effect: `false`

## 근거

- as_of: `2026-05-11T12:50:07`
- baseline_date: `2026-05-08`
- ai_confirmed unique: `88`
- budget_pass unique: `15`
- latency_pass unique: `3`
- submitted unique: `3`
- holding_started unique: `0`
- budget/ai unique: `17.0%` (baseline `24.6`)
- submitted/ai unique: `3.4%` (baseline `6.1`)
- top blockers: `blocked_strength_momentum:below_window_buy_value=74243, blocked_strength_momentum:below_strength_base=58069, blocked_overbought:-=40799, blocked_strength_momentum:insufficient_history=10578, blocked_strength_momentum:below_buy_ratio=6280`
- upstream blockers: `first_ai_wait:-=355, blocked_ai_score:ai_score_50_buy_hold_override=304, blocked_ai_score:score_62.0=258, wait65_79_ev_candidate:score_65.0=85, blocked_ai_score:score_65.0=73`
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

- `5m`: ai=11, budget=0, latency=0, submitted=0, top=`blocked_strength_momentum:below_strength_base=2039, blocked_strength_momentum:below_window_buy_value=1887, blocked_overbought:-=1741`, upstream=`blocked_ai_score:score_62.0=8, blocked_ai_score:ai_score_50_buy_hold_override=4, blocked_ai_score:score_58.0=1`
- `10m`: ai=19, budget=0, latency=0, submitted=0, top=`blocked_strength_momentum:below_strength_base=4202, blocked_strength_momentum:below_window_buy_value=3890, blocked_overbought:-=2865`, upstream=`blocked_ai_score:score_62.0=16, blocked_ai_score:ai_score_50_buy_hold_override=7, first_ai_wait:-=2`
- `30m`: ai=32, budget=0, latency=0, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=14603, blocked_strength_momentum:below_strength_base=10358, blocked_overbought:-=9388`, upstream=`blocked_ai_score:score_62.0=52, first_ai_wait:-=19, blocked_ai_score:ai_score_50_buy_hold_override=14`
