# Observation Source Quality Audit - 2026-05-15

- status: `warning`
- event_count: `596422`
- decision_authority: `source_quality_only`
- runtime_effect: `False`
- forbidden_uses: `runtime_threshold_apply, order_submit, provider_route_change, bot_restart, real_execution_quality_approval`

## Warning Stages
- `ai_confirmed` sample=`589` missing=`{'tick_source_quality_fields_sent': 0.6316, 'tick_accel_source': 0.6316, 'tick_context_quality': 0.6316, 'quote_age_source': 0.6316}` zero=`{}`
- `blocked_ai_score` sample=`711` missing=`{'tick_source_quality_fields_sent': 0.7187, 'tick_accel_source': 0.7595, 'tick_context_quality': 0.7595, 'quote_age_source': 0.7595}` zero=`{'distance_from_day_high_pct': 0.2068, 'intraday_range_pct': 0.1716}`
- `wait65_79_ev_candidate` sample=`12` missing=`{'tick_source_quality_fields_sent': 0.6667, 'tick_accel_source': 0.6667, 'tick_context_quality': 0.6667, 'quote_age_source': 0.6667}` zero=`{}`
- `blocked_strength_momentum` sample=`190278` missing=`{}` zero=`{'distance_from_day_high_pct': 0.6587, 'intraday_range_pct': 0.657}`
- `blocked_overbought` sample=`19756` missing=`{}` zero=`{'distance_from_day_high_pct': 0.727, 'intraday_range_pct': 0.4569}`
- `swing_probe_state_persisted` sample=`77` missing=`{'metric_role': 0.987, 'decision_authority': 0.987, 'runtime_effect': 0.987, 'forbidden_uses': 0.987}` zero=`{}`
- `scale_in_price_p2_observe` sample=`22` missing=`{'orderbook_micro_ready': 0.0455, 'orderbook_micro_state': 0.0455, 'orderbook_micro_reason': 0.0455, 'orderbook_micro_snapshot_age_ms': 0.0455, 'orderbook_micro_observer_healthy': 0.0455}` zero=`{}`

## High Volume Stages Without Source-Like Fields
- none

## Top Stages
- `strength_momentum_observed`: `190278`
- `blocked_strength_momentum`: `190278`
- `blocked_swing_score_vpw`: `164517`
- `blocked_overbought`: `19756`
- `blocked_swing_gap`: `11604`
- `strength_momentum_pass`: `6234`
- `blocked_liquidity`: `5343`
- `swing_probe_discarded`: `4216`
- `dynamic_vpw_override_pass`: `1516`
- `blocked_ai_score`: `711`
- `ai_confirmed`: `589`
- `swing_reentry_counterfactual_after_loss`: `500`
- `first_ai_wait`: `178`
- `ai_cooldown_blocked`: `163`
- `swing_probe_state_persisted`: `77`
- `gatekeeper_fast_reuse_bypass`: `49`
- `blocked_gatekeeper_reject`: `48`
- `exit_signal`: `31`
- `swing_probe_exit_signal`: `26`
- `swing_probe_sell_order_assumed_filled`: `26`
