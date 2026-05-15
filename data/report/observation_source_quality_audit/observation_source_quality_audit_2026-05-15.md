# Observation Source Quality Audit - 2026-05-15

- status: `warning`
- event_count: `564674`
- decision_authority: `source_quality_only`
- runtime_effect: `False`
- forbidden_uses: `runtime_threshold_apply, order_submit, provider_route_change, bot_restart, real_execution_quality_approval`

## Warning Stages
- `ai_confirmed` sample=`581` missing=`{'tick_source_quality_fields_sent': 0.6386, 'tick_accel_source': 0.6386, 'tick_context_quality': 0.6386, 'quote_age_source': 0.6386}` zero=`{}`
- `blocked_ai_score` sample=`698` missing=`{'tick_source_quality_fields_sent': 0.7321, 'tick_accel_source': 0.765, 'tick_context_quality': 0.765, 'quote_age_source': 0.765}` zero=`{'distance_from_day_high_pct': 0.2092, 'intraday_range_pct': 0.1748}`
- `wait65_79_ev_candidate` sample=`12` missing=`{'tick_source_quality_fields_sent': 0.6667, 'tick_accel_source': 0.6667, 'tick_context_quality': 0.6667, 'quote_age_source': 0.6667}` zero=`{}`
- `blocked_strength_momentum` sample=`180118` missing=`{}` zero=`{'distance_from_day_high_pct': 0.6953, 'intraday_range_pct': 0.6939}`
- `blocked_overbought` sample=`17737` missing=`{}` zero=`{'distance_from_day_high_pct': 0.7458, 'intraday_range_pct': 0.5089}`

## High Volume Stages Without Source-Like Fields
- `swing_probe_state_persisted` count=`76` routing=`instrumentation_gap_or_diagnostic_contract_needed`

## Top Stages
- `strength_momentum_observed`: `180118`
- `blocked_strength_momentum`: `180118`
- `blocked_swing_score_vpw`: `156034`
- `blocked_overbought`: `17737`
- `blocked_swing_gap`: `11180`
- `strength_momentum_pass`: `6152`
- `blocked_liquidity`: `5275`
- `swing_probe_discarded`: `4028`
- `dynamic_vpw_override_pass`: `1484`
- `blocked_ai_score`: `698`
- `ai_confirmed`: `581`
- `swing_reentry_counterfactual_after_loss`: `482`
- `first_ai_wait`: `177`
- `ai_cooldown_blocked`: `162`
- `swing_probe_state_persisted`: `76`
- `gatekeeper_fast_reuse_bypass`: `46`
- `blocked_gatekeeper_reject`: `46`
- `exit_signal`: `26`
- `swing_probe_exit_signal`: `26`
- `swing_probe_sell_order_assumed_filled`: `26`
