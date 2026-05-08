# HOLD/EXIT Sentinel 2026-05-08

## 판정

- primary: `HOLD_DEFER_DANGER`
- secondary: `AI_HOLDING_OPS, SOFT_STOP_WHIPSAW`
- report_only: `true`
- live_runtime_effect: `false`

## 근거

- as_of: `2026-05-08T15:30:07`
- exit_signal unique: `3`
- sell_order_sent unique: `3`
- sell_completed unique: `3`
- sell_sent/exit_signal: `100.0%`
- flow defer events: `59`
- AI holding cache MISS: `100.0%`
- soft_stop rebound above sell 10m: `90.5%`
- trailing missed-upside: `27.8%`
- top reasons: `flow유예:scalp_soft_stop_pct=48, AI보유감시:cache_miss=31, soft_stop_grace=28, flow유예:scalp_trailing_take_profit=11, sell_order_sent=3`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review holding_flow_override defer examples and worsen floor evidence.
