# Panic Sell Defense 2026-05-12

## 판정

- panic_state: `RECOVERY_WATCH`
- report_only: `true`
- runtime_effect: `report_only_no_mutation`
- as_of: `2026-05-12T12:01:40`
- latest_event_at: `2026-05-12T12:01:39`
- reasons: `panic thresholds breached; recovery watch triggered by active sim/probe or post-sell rebound above sell`

## 패닉 지표

- real_exit_count: `28`
- non_real_exit_count: `28`
- stop_loss_exit_count: `22`
- current_30m_stop_loss_exit_count: `0`
- max_rolling_30m_stop_loss_exit_count: `17`
- stop_loss_exit_ratio_pct: `78.6`
- avg_exit_profit_rate_pct: `-1.3621`
- confirmation_eligible_exit_count: `6`
- never_delay_exit_count: `0`

## 회복 지표

- active_positions: `8`
- active_profit_sample: `8`
- active_avg_unrealized_profit_rate_pct: `0.7995`
- active_win_rate_pct: `62.5`
- sim_probe_provenance_passed: `true`
- post_sell_rebound_above_sell_10_20m_pct: `0`
- post_sell_rebound_above_buy_10_20m_pct: `0`

## 방어 액션

- `hard_protect_emergency_delay_forbidden`: `enforced` / runtime_effect=`false`
- `live_threshold_mutation_forbidden`: `enforced` / runtime_effect=`false`
- `recovery_probe_review`: `candidate_only` / runtime_effect=`false`
- `soft_trailing_flow_confirmation_review`: `candidate_only` / runtime_effect=`false`

## Canary Candidates

- `panic_entry_freeze_guard`: `report_only_candidate`, allowed_runtime_apply=`false`
- `panic_stop_confirmation`: `report_only_candidate`, allowed_runtime_apply=`false`
- `panic_rebound_probe`: `hold_until_recovery_confirmed`, allowed_runtime_apply=`false`
- `panic_attribution_pack`: `active_report_only`, allowed_runtime_apply=`false`

## 금지된 자동변경

- `live_threshold_runtime_mutation`
- `score_threshold_relaxation`
- `stop_loss_relaxation`
- `auto_sell`
- `bot_restart`
- `swing_real_order_enable`
