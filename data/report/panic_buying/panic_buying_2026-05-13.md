# Panic Buying 2026-05-13

## 판정

- panic_buy_state: `NORMAL`
- report_only: `true`
- runtime_effect: `report_only_no_mutation`
- as_of: `2026-05-13T16:12:49`
- latest_event_at: `2026-05-13T16:12:48`
- reasons: `no panic buying threshold breached`

## 패닉바잉 지표

- evaluated_symbol_count: `19`
- panic_buy_active_count: `0`
- panic_buy_watch_count: `0`
- allow_tp_override_count: `0`
- allow_runner_count: `0`
- max_panic_buy_score: `0.3779`
- avg_confidence: `0.5316`

## 소진 지표

- exhaustion_candidate_count: `0`
- exhaustion_confirmed_count: `0`
- force_exit_runner_count: `0`
- max_exhaustion_score: `0.545`

## TP Counterfactual

- tp_like_exit_count: `6`
- trailing_winner_count: `6`
- candidate_context_count: `12`
- avg_tp_profit_rate_pct: `4.735`
- runtime_effect: `counterfactual_only_no_order_change`

## Microstructure Detector

- missing_orderbook_count: `9`
- degraded_orderbook_count: `9`
- missing_trade_aggressor_count: `12`

## Canary Candidates

- `panic_buy_runner_tp_canary`: `hold_until_confirmed_panic_buy_with_tp_context`, allowed_runtime_apply=`false`

## 금지된 자동변경

- `live_threshold_runtime_mutation`
- `take_profit_policy_change`
- `trailing_policy_change`
- `auto_sell`
- `auto_buy`
- `bot_restart`
- `provider_route_change`
