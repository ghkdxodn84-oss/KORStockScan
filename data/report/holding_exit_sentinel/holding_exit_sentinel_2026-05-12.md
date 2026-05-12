# HOLD/EXIT Sentinel 2026-05-12

## 판정

- primary: `SELL_EXECUTION_DROUGHT`
- secondary: `-`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `true`
- followup_route: `sell_receipt_order_path_check`
- followup_owner: `postclose_holding_exit_attribution`
- runtime_effect: `report_only_no_mutation`

## 근거

- as_of: `2026-05-12T12:00:07`
- exit_signal unique: `16`
- sell_order_sent unique: `0`
- sell_completed unique: `0`
- real exit/sell_sent/sell_completed: `16` / `0` / `0`
- non-real exit/sell_sent/sell_completed: `0` / `0` / `0`
- sell_sent/exit_signal: `0.0%`
- real sell_sent/exit_signal: `0.0%`
- non-real sell_sent/exit_signal: `0.0%`
- flow defer events: `0`
- AI holding cache MISS: `0.0%`
- soft_stop rebound above sell 10m: `0.0%`
- trailing missed-upside: `0.0%`
- top reasons: `청산신호:kosdaq_stop_loss=17, 청산신호:kospi_regime_stop_loss=5, 청산신호:kosdaq_trailing_take_profit=3, 청산신호:kospi_trailing_start_take_profit=3`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Check sell order receipt/order path before changing exit thresholds.
