# Threshold Cycle Daily EV Report - 2026-05-14

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
- holding_reviews: `74`
- exit_signals: `12`
- holding_review_ms_p95: `3716.0`

## Scalp Simulator
- authority: `equal_weight` / fill_policy: `signal_inclusive_best_ask_v1`
- armed/filled/sold: `1` / `1` / `1`
- expired/unpriced/duplicate: `0` / `0` / `0`
- completed_profit_summary: `{'sample': 1, 'win_count': 0, 'loss_count': 1, 'avg_profit_rate': -2.0, 'median_profit_rate': -2.0, 'downside_p10_profit_rate': -2.0, 'upside_p90_profit_rate': -2.0, 'win_rate': 0.0, 'loss_rate': 1.0, 'stddev_profit_rate': None}`

## Missed Probe Counterfactual
- book: `scalp_score65_74_probe_counterfactual` / role: `missed_buy_probe_counterfactual`
- total/score65_74: `11` / `0`
- avg_expected_ev: `6.7576`% / score65_74_avg_expected_ev: `0.0`%
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

## Swing Runtime Approval
- request_report: `/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-05-13.json`
- approval_artifact: `-`
- requested/approved/live_dry_run: `0` / `0` / `0`
- dry_run_forced: `False`
- real_canary_policy: `swing_one_share_real_canary_phase0`
- real_order_allowed_actions: `BUY_INITIAL, SELL_CLOSE`
- sim_only_actions: `AVG_DOWN, PYRAMID, SCALE_IN`
- scale_in_real_canary_policy: `swing_scale_in_real_canary_phase0`
- selected_scale_in_real_canary: `0`
- scale_in_real_execution_quality: `{'scale_in_canary_selected': 0, 'execution_quality_source': 'real_only', 'sim_probe_ev_source': 'separate_from_broker_execution_quality'}`
- blocked: `[]`

## Code Improvement Workorder
- artifact: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-14.json`
- markdown: `/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-14.md`
- selected_order_count: `2`
- decision_counts: `{'design_family_candidate': 2}`

## Approval Requests
- none

## Swing Approval Requests
- none

## Calibration Decisions
## Code Improvement Top Orders
- `order_panic_sell_defense_lifecycle_transition_pack` decision=`design_family_candidate` subsystem=`panic_sell_defense`
- `order_panic_buy_runner_tp_canary_lifecycle_pack` decision=`design_family_candidate` subsystem=`panic_buying`

- `soft_stop_whipsaw_confirmation`: `hold_sample` sample=`4/10`
- `holding_flow_ofi_smoothing`: `hold_sample` sample=`1/20`
- `protect_trailing_smoothing`: `hold_sample` sample=`0/20`
- `trailing_continuation`: `freeze` sample=`0/20`
- `pre_submit_price_guard`: `hold_sample` sample=`0/20`
- `score65_74_recovery_probe`: `hold_sample` sample=`11/20`
- `liquidity_gate_refined_candidate`: `hold` sample=`2614/20`
- `overbought_gate_refined_candidate`: `hold` sample=`24123/20`
- `bad_entry_refined_canary`: `adjust_up` sample=`233/10`
- `holding_exit_decision_matrix_advisory`: `hold_no_edge` sample=`8/1`
- `scale_in_price_guard`: `hold_sample` sample=`2/20`
- `position_sizing_cap_release`: `hold_sample` sample=`4/30`
- `position_sizing_dynamic_formula`: `hold_sample` sample=`4/30`

## Warnings
- `pattern_lab_automation_missing`
- `swing_pattern_lab_automation_missing`
