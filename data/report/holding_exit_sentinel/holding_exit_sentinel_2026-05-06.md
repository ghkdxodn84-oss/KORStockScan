# HOLD/EXIT Sentinel 2026-05-06

## 판정

- primary: `HOLD_DEFER_DANGER`
- secondary: `AI_HOLDING_OPS, SOFT_STOP_WHIPSAW, TRAILING_EARLY_EXIT`
- report_only: `true`
- live_runtime_effect: `false`

## 근거

- as_of: `2026-05-06T15:42:21`
- exit_signal unique: `5`
- sell_order_sent unique: `5`
- sell_completed unique: `5`
- sell_sent/exit_signal: `100.0%`
- flow defer events: `239`
- AI holding cache MISS: `100.0%`
- soft_stop rebound above sell 10m: `92.9%`
- trailing missed-upside: `33.3%`
- top reasons: `AI보유감시:cache_miss=374, flow유예:scalp_trailing_take_profit=155, flow유예:scalp_soft_stop_pct=48, flow유예:scalp_ai_momentum_decay=36, soft_stop_grace=16`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review holding_flow_override defer examples and worsen floor evidence.
