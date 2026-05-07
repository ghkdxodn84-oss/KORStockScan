# HOLD/EXIT Sentinel 2026-05-07

## 판정

- primary: `HOLD_DEFER_DANGER`
- secondary: `AI_HOLDING_OPS, SOFT_STOP_WHIPSAW, TRAILING_EARLY_EXIT`
- report_only: `true`
- live_runtime_effect: `false`

## 근거

- as_of: `2026-05-07T15:30:09`
- exit_signal unique: `9`
- sell_order_sent unique: `9`
- sell_completed unique: `9`
- sell_sent/exit_signal: `100.0%`
- flow defer events: `272`
- AI holding cache MISS: `100.0%`
- soft_stop rebound above sell 10m: `89.5%`
- trailing missed-upside: `31.2%`
- top reasons: `soft_stop_grace=285, AI보유감시:cache_miss=246, flow유예:scalp_soft_stop_pct=160, flow유예:scalp_trailing_take_profit=112, sell_order_sent=9`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review holding_flow_override defer examples and worsen floor evidence.
