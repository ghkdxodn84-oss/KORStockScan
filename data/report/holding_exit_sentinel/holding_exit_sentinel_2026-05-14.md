# HOLD/EXIT Sentinel 2026-05-14

## 판정

- primary: `NORMAL`
- secondary: `-`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `normal_no_action`
- followup_owner: `none`
- runtime_effect: `report_only_no_mutation`

## 근거

- as_of: `2026-05-14T10:45:04`
- exit_signal unique: `11`
- sell_order_sent unique: `0`
- sell_completed unique: `0`
- real exit/sell_sent/sell_completed: `0` / `0` / `0`
- non-real exit/sell_sent/sell_completed: `11` / `0` / `0`
- sell_sent/exit_signal: `0.0%`
- real sell_sent/exit_signal: `0.0%`
- non-real sell_sent/exit_signal: `0.0%`
- flow defer events: `0`
- AI holding cache MISS: `100.0%`
- soft_stop rebound above sell 10m: `0.0%`
- trailing missed-upside: `0.0%`
- top reasons: `청산신호:kosdaq_trailing_take_profit=6, soft_stop_grace=4, 청산신호:kosdaq_stop_loss=4, AI보유감시:cache_miss=2, 청산신호:scalp_soft_stop_pct=1`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Continue monitoring; no dynamic action required.
