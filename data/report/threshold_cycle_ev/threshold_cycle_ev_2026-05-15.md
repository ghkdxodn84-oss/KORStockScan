# Threshold Cycle Daily EV Report - 2026-05-15

## Runtime Apply
- status: `auto_bounded_live_ready`
- runtime_change: `True`
- selected_families: `soft_stop_whipsaw_confirmation`

## Daily EV
- completed: `0` / open: `0`
- win/loss: `0` / `0` (`0.0`%)
- avg_profit_rate: `0.0`%
- realized_pnl_krw: `0`
- full_fill_completed_avg_profit_rate: `0.0`%

## Entry Funnel
- budget_pass_to_submitted: `0` / `0` (`0.0`%)
- latency pass/block: `0` / `0`
- full/partial fill: `0` / `0`

## Holding Exit
- holding_reviews: `0`
- exit_signals: `26`
- holding_review_ms_p95: `0.0`

## Scalp Simulator
- authority: `equal_weight` / fill_policy: `signal_inclusive_best_ask_v1`
- armed/filled/sold: `2` / `2` / `1`
- expired/unpriced/duplicate: `0` / `0` / `80`
- entry_ai_price applied/skip: `1` / `0`
- submit_revalidation warning/block: `1` / `0`
- scale_in filled/unfilled: `0` / `0`
- completed_profit_summary: `{'sample': 1, 'win_count': 0, 'loss_count': 1, 'avg_profit_rate': -1.83, 'median_profit_rate': -1.83, 'downside_p10_profit_rate': -1.83, 'upside_p90_profit_rate': -1.83, 'win_rate': 0.0, 'loss_rate': 1.0, 'stddev_profit_rate': None}`

## Missed Probe Counterfactual
- book: `scalp_score65_74_probe_counterfactual` / role: `missed_buy_probe_counterfactual`
- total/score65_74: `12` / `0`
- avg_expected_ev: `4.6082`% / score65_74_avg_expected_ev: `0.0`%
- actual_order_submitted: `False` / broker_order_forbidden: `True`
- authority: `missed_probe_ev_only_not_broker_execution`

## Pattern Lab Automation
- artifact: `-`
- fresh: gemini=`False` claude=`False`
- consensus/orders/family_candidates: `0` / `0` / `0`

## Swing Pattern Lab Automation
- artifact: `-`
- deepseek_lab_available: `None`
- findings/orders: `0` / `0`
- data_quality_warnings: `0`
- ofi_qi_stale_missing_unique_records: `0`
- ofi_qi_stale_missing_reasons: `{}`
- ofi_qi_stale_missing_reason_combinations: `{}`
- ofi_qi_stale_missing_reason_combination_unique_records: `{}`
- ofi_qi_observer_unhealthy_overlap: `{}`
- source_quality_blocked_families: `[]`
- carryover_warnings: `0`
- population_split_available: `False`

## Pipeline Event Verbosity
- artifact: `-`
- state: `missing`
- recommended_workorder_state: `missing`
- high_volume_line_count: `None`
- high_volume_byte_share_pct: `None`
- parity_ok: `None`
- suppress_eligibility: `None`

## Codebase Performance Workorder Source
- artifact: `-`
- authority: `-`
- accepted/deferred/rejected: `0` / `0` / `0`
- runtime_effect: `False`
- strategy_effect: `None`
- data_quality_effect: `None`
- tuning_axis_effect: `None`

## Swing Runtime Approval
- request_report: `/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-05-14.json`
- approval_artifact: `-`
- requested/approved/live_dry_run: `2` / `0` / `0`
- dry_run_forced: `False`
- real_canary_policy: `swing_one_share_real_canary_phase0`
- real_order_allowed_actions: `BUY_INITIAL, SELL_CLOSE`
- sim_only_actions: `AVG_DOWN, PYRAMID, SCALE_IN`
- scale_in_real_canary_policy: `swing_scale_in_real_canary_phase0`
- selected_scale_in_real_canary: `0`
- scale_in_real_execution_quality: `{'scale_in_canary_selected': 0, 'execution_quality_source': 'real_only', 'sim_probe_ev_source': 'separate_from_broker_execution_quality'}`
- blocked: `['approval_artifact_missing']`

## Code Improvement Workorder
- artifact: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-15.json`
- markdown: `/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-15.md`
- selected_order_count: `5`
- decision_counts: `{'implement_now': 3, 'design_family_candidate': 1, 'defer_evidence': 1}`

## Approval Requests
- none

## Swing Approval Requests
- `swing_model_floor` approval_id=`swing_runtime_approval:2026-05-14:swing_model_floor` score=`0.6811` target_env_keys=`['SWING_FLOOR_BULL', 'SWING_FLOOR_BEAR']`
- `swing_gatekeeper_reject_cooldown` approval_id=`swing_runtime_approval:2026-05-14:swing_gatekeeper_reject_cooldown` score=`0.6811` target_env_keys=`['ML_GATEKEEPER_REJECT_COOLDOWN']`

## Calibration Decisions
## Code Improvement Top Orders
- `order_ai_source_quality_not_evaluated_provenance` decision=`implement_now` subsystem=`runtime_instrumentation`
- `order_swing_source_quality_micro_context_provenance` decision=`implement_now` subsystem=`runtime_instrumentation`
- `order_threshold_window_policy_source_snapshot_alignment` decision=`implement_now` subsystem=`threshold_cycle_report`

- `soft_stop_whipsaw_confirmation`: `adjust_up` sample=`469/10`
- `holding_flow_ofi_smoothing`: `hold` sample=`61/20`
- `protect_trailing_smoothing`: `adjust_down` sample=`150/20`
- `trailing_continuation`: `freeze` sample=`119/20`
- `pre_submit_price_guard`: `hold_sample` sample=`0/20`
- `score65_74_recovery_probe`: `adjust_up` sample=`189/20`
- `liquidity_gate_refined_candidate`: `hold` sample=`28009/20`
- `overbought_gate_refined_candidate`: `hold` sample=`471261/20`
- `bad_entry_refined_canary`: `adjust_up` sample=`2821/10`
- `holding_exit_decision_matrix_advisory`: `hold_no_edge` sample=`3/1`
- `scale_in_price_guard`: `hold` sample=`314/20`
- `position_sizing_cap_release`: `hold_sample` sample=`28/30`
- `position_sizing_dynamic_formula`: `hold_sample` sample=`1/30`

## Warnings
- `pattern_lab_automation_missing`
- `swing_pattern_lab_automation_missing`
- `pipeline_event_verbosity_missing`
- `codebase_performance_workorder_missing`
