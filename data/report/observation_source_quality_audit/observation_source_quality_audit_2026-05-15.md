# Observation Source Quality Audit - 2026-05-15

- status: `warning`
- event_count: `1413933`
- decision_authority: `source_quality_only`
- runtime_effect: `False`
- forbidden_uses: `runtime_threshold_apply, order_submit, provider_route_change, bot_restart, real_execution_quality_approval`

## Warning Stages
- `ai_confirmed` sample=`786` missing=`{'tick_source_quality_fields_sent': 0.4796, 'tick_accel_source': 0.4796, 'tick_context_quality': 0.4796, 'quote_age_source': 0.4796}` zero=`{}`
- `blocked_ai_score` sample=`955` missing=`{'tick_source_quality_fields_sent': 0.5351, 'tick_accel_source': 0.6209, 'tick_context_quality': 0.6209, 'quote_age_source': 0.6209}` zero=`{'distance_from_day_high_pct': 0.1634, 'intraday_range_pct': 0.1277}`
- `wait65_79_ev_candidate` sample=`19` missing=`{'tick_source_quality_fields_sent': 0.4211, 'tick_accel_source': 0.4211, 'tick_context_quality': 0.4211, 'quote_age_source': 0.4211}` zero=`{}`
- `blocked_strength_momentum` sample=`370917` missing=`{}` zero=`{'distance_from_day_high_pct': 0.34, 'intraday_range_pct': 0.3378}`
- `blocked_overbought` sample=`51970` missing=`{}` zero=`{'distance_from_day_high_pct': 0.551, 'intraday_range_pct': 0.1737}`
- `swing_probe_state_persisted` sample=`118` missing=`{'metric_role': 0.6441, 'decision_authority': 0.6441, 'runtime_effect': 0.6441, 'forbidden_uses': 0.6441}` zero=`{}`
- `scale_in_price_p2_observe` sample=`29` missing=`{'orderbook_micro_ready': 0.0345, 'orderbook_micro_state': 0.0345, 'orderbook_micro_reason': 0.0345, 'orderbook_micro_snapshot_age_ms': 0.0345, 'orderbook_micro_observer_healthy': 0.0345}` zero=`{}`

## High Volume Stages Without Source-Like Fields
- `blocked_gatekeeper_reject` count=`101` routing=`instrumentation_gap_or_diagnostic_contract_needed`
- `soft_stop_micro_grace` count=`91` routing=`instrumentation_gap_or_diagnostic_contract_needed`
- `budget_pass` count=`82` routing=`instrumentation_gap_or_diagnostic_contract_needed`
- `entry_armed_resume` count=`75` routing=`instrumentation_gap_or_diagnostic_contract_needed`
- `holding_flow_override_defer_exit` count=`61` routing=`instrumentation_gap_or_diagnostic_contract_needed`

## Top Stages
- `blocked_swing_score_vpw`: `523784`
- `strength_momentum_observed`: `370917`
- `blocked_strength_momentum`: `370917`
- `blocked_swing_gap`: `59125`
- `blocked_overbought`: `51970`
- `swing_probe_discarded`: `12161`
- `strength_momentum_pass`: `9537`
- `blocked_liquidity`: `8371`
- `dynamic_vpw_override_pass`: `2391`
- `blocked_ai_score`: `955`
- `swing_reentry_counterfactual_after_loss`: `836`
- `ai_confirmed`: `786`
- `first_ai_wait`: `203`
- `ai_cooldown_blocked`: `191`
- `swing_probe_state_persisted`: `118`
- `gatekeeper_fast_reuse_bypass`: `101`
- `blocked_gatekeeper_reject`: `101`
- `stat_action_decision_snapshot`: `92`
- `soft_stop_micro_grace`: `91`
- `bad_entry_refined_candidate`: `89`
