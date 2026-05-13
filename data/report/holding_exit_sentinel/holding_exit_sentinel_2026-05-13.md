# HOLD/EXIT Sentinel 2026-05-13

## 판정

- primary: `AI_HOLDING_OPS`
- secondary: `SOFT_STOP_WHIPSAW`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `ai_holding_provenance_review`
- followup_owner: `runtime_stability_review`
- runtime_effect: `report_only_no_mutation`

## 근거

- as_of: `2026-05-13T15:30:10`
- exit_signal unique: `15`
- sell_order_sent unique: `0`
- sell_completed unique: `0`
- real exit/sell_sent/sell_completed: `0` / `0` / `0`
- non-real exit/sell_sent/sell_completed: `15` / `0` / `0`
- sell_sent/exit_signal: `0.0%`
- real sell_sent/exit_signal: `0.0%`
- non-real sell_sent/exit_signal: `0.0%`
- flow defer events: `0`
- AI holding cache MISS: `100.0%`
- soft_stop rebound above sell 10m: `90.9%`
- trailing missed-upside: `27.8%`
- top reasons: `AI보유감시:cache_miss=84, 청산신호:kosdaq_stop_loss=8, 청산신호:kosdaq_trailing_take_profit=6, 청산신호:kospi_regime_stop_loss=2`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review AI cache/provenance/parse telemetry; do not mutate cache TTL automatically.
