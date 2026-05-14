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
- holding_reviews: `352`
- exit_signals: `17`
- holding_review_ms_p95: `2699.0`

## Scalp Simulator
- authority: `equal_weight` / fill_policy: `signal_inclusive_best_ask_v1`
- armed/filled/sold: `1` / `1` / `2`
- expired/unpriced/duplicate: `0` / `0` / `0`
- completed_profit_summary: `{'sample': 2, 'win_count': 1, 'loss_count': 1, 'avg_profit_rate': -0.725, 'median_profit_rate': -2.0, 'downside_p10_profit_rate': -2.0, 'upside_p90_profit_rate': 0.55, 'win_rate': 0.5, 'loss_rate': 0.5, 'stddev_profit_rate': 1.8031}`

## Missed Probe Counterfactual
- book: `scalp_score65_74_probe_counterfactual` / role: `missed_buy_probe_counterfactual`
- total/score65_74: `19` / `0`
- avg_expected_ev: `1.6344`% / score65_74_avg_expected_ev: `0.0`%
- actual_order_submitted: `False` / broker_order_forbidden: `True`
- authority: `missed_probe_ev_only_not_broker_execution`

## Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-05-14.json`
- fresh: gemini=`True` claude=`True`
- consensus/orders/family_candidates: `5` / `14` / `2`

## Swing Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-05-14.json`
- deepseek_lab_available: `True`
- findings/orders: `5` / `3`
- data_quality_warnings: `1`
- ofi_qi_stale_missing_unique_records: `2`
- ofi_qi_stale_missing_reasons: `{'micro_missing': 59, 'micro_stale': 0, 'observer_unhealthy': 31, 'micro_not_ready': 2, 'state_insufficient': 2}`
- ofi_qi_stale_missing_reason_combinations: `{'micro_missing': 28, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 2, 'micro_missing+observer_unhealthy': 29}`
- ofi_qi_stale_missing_reason_combination_unique_records: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 2, 'micro_missing+observer_unhealthy': 1}`
- ofi_qi_observer_unhealthy_overlap: `{'observer_unhealthy_total': 31, 'observer_unhealthy_with_other_reason': 31, 'observer_unhealthy_only': 0}`
- source_quality_blocked_families: `[{'family': 'swing_scale_in_ofi_qi_confirmation', 'stage': 'scale_in', 'source_quality_blockers': ['scale_in_ofi_qi_invalid_micro_context'], 'invalid_micro_context_unique_record_count': 2, 'invalid_reason_combination_unique_record_counts': {'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 2, 'micro_missing+observer_unhealthy': 1}, 'automation_input': True, 'runtime_effect': False}]`
- carryover_warnings: `0`
- population_split_available: `True`

## Pipeline Event Verbosity
- artifact: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-05-14.json`
- state: `v2_shadow_missing`
- recommended_workorder_state: `open_shadow_order`
- high_volume_line_count: `1342730`
- high_volume_byte_share_pct: `95.39`
- parity_ok: `False`
- suppress_eligibility: `False`

## Codebase Performance Workorder Source
- artifact: `/home/ubuntu/KORStockScan/data/report/codebase_performance_workorder/codebase_performance_workorder_2026-05-14.json`
- authority: `ops_performance_workorder_source`
- accepted/deferred/rejected: `7` / `3` / `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`

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
- selected_order_count: `12`
- decision_counts: `{'implement_now': 9, 'attach_existing_family': 7, 'design_family_candidate': 6, 'defer_evidence': 10, 'reject': 6}`

## Approval Requests
- none

## Swing Approval Requests
- none

## Calibration Decisions
## Code Improvement Top Orders
- `order_perf_buy_funnel_json_scan` decision=`implement_now` subsystem=`buy_funnel_sentinel`
- `order_pipeline_event_compaction_v2_shadow` decision=`implement_now` subsystem=`runtime_instrumentation`
- `order_perf_daily_report_bulk_history` decision=`implement_now` subsystem=`daily_report`

## Pattern Lab Top Findings
- `AI threshold dominance` route=`existing_family` family=`score65_74_recovery_probe`
- `AI threshold miss EV recovery` route=`existing_family` family=`score65_74_recovery_probe`
- `latency guard miss EV recovery` route=`instrumentation_order` family=`-`

- `soft_stop_whipsaw_confirmation`: `adjust_up` sample=`378/10`
- `holding_flow_ofi_smoothing`: `hold` sample=`165/20`
- `protect_trailing_smoothing`: `adjust_down` sample=`149/20`
- `trailing_continuation`: `freeze` sample=`84/20`
- `pre_submit_price_guard`: `hold_sample` sample=`0/20`
- `score65_74_recovery_probe`: `hold` sample=`177/20`
- `liquidity_gate_refined_candidate`: `hold` sample=`22940/20`
- `overbought_gate_refined_candidate`: `hold` sample=`456860/20`
- `bad_entry_refined_canary`: `adjust_up` sample=`2732/10`
- `holding_exit_decision_matrix_advisory`: `hold_no_edge` sample=`8/1`
- `scale_in_price_guard`: `hold` sample=`256/20`
- `position_sizing_cap_release`: `hold_sample` sample=`4/30`
- `position_sizing_dynamic_formula`: `hold_sample` sample=`4/30`

## Warnings
- `swing_lab_dq:OFI/QI stale/missing ratio: 0.0531 (59/1111); reasons: micro_missing=59, observer_unhealthy=31, micro_not_ready=2, state_insufficient=2`
