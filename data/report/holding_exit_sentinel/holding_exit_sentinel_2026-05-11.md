# HOLD/EXIT Sentinel 2026-05-11

## 판정

- primary: `SELL_EXECUTION_DROUGHT`
- secondary: `HOLD_DEFER_DANGER, AI_HOLDING_OPS, SOFT_STOP_WHIPSAW`
- report_only: `true`
- live_runtime_effect: `false`

## 근거

- as_of: `2026-05-11T12:00:04`
- exit_signal unique: `9`
- sell_order_sent unique: `1`
- sell_completed unique: `1`
- sell_sent/exit_signal: `11.1%`
- flow defer events: `64`
- AI holding cache MISS: `99.5%`
- soft_stop rebound above sell 10m: `90.9%`
- trailing missed-upside: `27.8%`
- top reasons: `AI보유감시:cache_miss=202, flow유예:scalp_trailing_take_profit=63, soft_stop_grace=44, 청산신호:scalp_trailing_take_profit=4, 청산신호:scalp_preset_protect_profit=1`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Check sell order receipt/order path before changing exit thresholds.
