# BUY Funnel Sentinel 2026-05-11

## 판정

- primary: `PRICE_GUARD_DROUGHT`
- secondary: `LATENCY_DROUGHT, UPSTREAM_AI_THRESHOLD`
- report_only: `true`
- live_runtime_effect: `false`

## 근거

- as_of: `2026-05-11T15:20:14`
- baseline_date: `2026-05-08`
- ai_confirmed unique: `102`
- budget_pass unique: `16`
- latency_pass unique: `3`
- submitted unique: `3`
- holding_started unique: `0`
- budget/ai unique: `15.7%` (baseline `25.9`)
- submitted/ai unique: `2.9%` (baseline `7.8`)
- top blockers: `blocked_strength_momentum:below_window_buy_value=120014, blocked_strength_momentum:below_strength_base=94729, blocked_overbought:-=82230, blocked_swing_score_vpw:-=40919, blocked_strength_momentum:insufficient_history=16311`
- upstream blockers: `blocked_ai_score:score_62.0=501, first_ai_wait:-=465, blocked_ai_score:ai_score_50_buy_hold_override=410, wait65_79_ev_candidate:score_65.0=86, blocked_ai_score:score_65.0=74`
- latency blockers: `latency_block:latency_state_danger=697`
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

- `5m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=4880, blocked_swing_gap:-=488`, upstream=`-`
- `10m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=9860, blocked_swing_gap:-=986`, upstream=`-`
- `30m`: ai=22, budget=0, latency=0, submitted=0, top=`blocked_swing_score_vpw:-=28040, blocked_overbought:-=3234, blocked_strength_momentum:below_window_buy_value=3210`, upstream=`blocked_ai_score:score_62.0=27, first_ai_wait:-=11, wait65_79_ev_candidate:score_65.0=1`
