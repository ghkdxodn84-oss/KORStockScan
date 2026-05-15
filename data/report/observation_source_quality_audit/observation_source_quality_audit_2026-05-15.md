# Observation Source Quality Audit - 2026-05-15

- status: `warning`
- event_count: `497404`
- decision_authority: `source_quality_only`
- runtime_effect: `False`
- forbidden_uses: `runtime_threshold_apply, order_submit, provider_route_change, bot_restart, real_execution_quality_approval`

## Warning Stages
- `ai_confirmed` sample=`551` missing=`{'tick_source_quality_fields_sent': 0.6715, 'tick_accel_source': 0.6715, 'tick_context_quality': 0.6715, 'quote_age_source': 0.6715}` zero=`{}`
- `blocked_ai_score` sample=`650` missing=`{'tick_source_quality_fields_sent': 0.7862, 'tick_accel_source': 0.7938, 'tick_context_quality': 0.7938, 'quote_age_source': 0.7938}` zero=`{'distance_from_day_high_pct': 0.2231, 'intraday_range_pct': 0.1877}`
- `wait65_79_ev_candidate` sample=`12` missing=`{'tick_source_quality_fields_sent': 0.6667, 'tick_accel_source': 0.6667, 'tick_context_quality': 0.6667, 'quote_age_source': 0.6667}` zero=`{}`
- `blocked_strength_momentum` sample=`157777` missing=`{}` zero=`{'distance_from_day_high_pct': 0.7929, 'intraday_range_pct': 0.7918}`
- `blocked_overbought` sample=`14562` missing=`{}` zero=`{'distance_from_day_high_pct': 0.7707, 'intraday_range_pct': 0.6199}`

## High Volume Stages Without Source-Like Fields
- `swing_probe_state_persisted` count=`76` routing=`instrumentation_gap_or_diagnostic_contract_needed`

## Top Stages
- `strength_momentum_observed`: `157777`
- `blocked_strength_momentum`: `157777`
- `blocked_swing_score_vpw`: `138553`
- `blocked_overbought`: `14562`
- `blocked_swing_gap`: `10305`
- `strength_momentum_pass`: `5909`
- `blocked_liquidity`: `5097`
- `swing_probe_discarded`: `3628`
- `dynamic_vpw_override_pass`: `1407`
- `blocked_ai_score`: `650`
- `ai_confirmed`: `551`
- `swing_reentry_counterfactual_after_loss`: `444`
- `first_ai_wait`: `160`
- `ai_cooldown_blocked`: `144`
- `swing_probe_state_persisted`: `76`
- `gatekeeper_fast_reuse_bypass`: `43`
- `blocked_gatekeeper_reject`: `43`
- `exit_signal`: `26`
- `swing_probe_exit_signal`: `26`
- `swing_probe_sell_order_assumed_filled`: `26`
