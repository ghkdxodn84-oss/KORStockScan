# HOLD/EXIT Sentinel 2026-05-15

## 판정

- primary: `SOFT_STOP_WHIPSAW`
- secondary: `-`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `soft_stop_whipsaw_calibration_review`
- followup_owner: `postclose_threshold_cycle`
- runtime_effect: `report_only_no_mutation`

## 근거

- as_of: `2026-05-15T12:10:02`
- exit_signal unique: `16`
- sell_order_sent unique: `0`
- sell_completed unique: `0`
- real exit/sell_sent/sell_completed: `0` / `0` / `0`
- non-real exit/sell_sent/sell_completed: `16` / `0` / `0`
- sell_sent/exit_signal: `0.0%`
- real sell_sent/exit_signal: `0.0%`
- non-real sell_sent/exit_signal: `0.0%`
- flow defer events: `0`
- AI holding cache MISS: `0.0%`
- soft_stop rebound above sell 10m: `90.9%`
- trailing missed-upside: `27.8%`
- top reasons: `청산신호:kospi_regime_stop_loss=16, 청산신호:kosdaq_trailing_take_profit=5, 청산신호:kosdaq_stop_loss=3, 청산신호:kospi_trailing_start_take_profit=1`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Append soft-stop rebound examples to postclose threshold review.
