# Threshold Cycle Daily EV Report - 2026-05-11

## Runtime Apply
- status: `auto_bounded_live_ready`
- runtime_change: `True`
- selected_families: `soft_stop_whipsaw_confirmation, score65_74_recovery_probe`

## Daily EV
- completed: `1` / open: `0`
- win/loss: `0` / `1` (`0.0`%)
- avg_profit_rate: `-1.55`%
- realized_pnl_krw: `-1172`
- full_fill_completed_avg_profit_rate: `0.0`%

## Entry Funnel
- budget_pass_to_submitted: `3` / `713` (`0.42`%)
- latency pass/block: `3` / `710`
- full/partial fill: `24` / `24`

## Holding Exit
- holding_reviews: `373`
- exit_signals: `50`
- holding_review_ms_p95: `3198.0`

## Scalp Simulator
- authority: `equal_weight` / fill_policy: `signal_inclusive_best_ask_v1`
- armed/filled/sold: `31` / `23` / `10`
- expired/unpriced/duplicate: `9` / `0` / `686`
- completed_profit_summary: `{'sample': 10, 'win_count': 7, 'loss_count': 3, 'avg_profit_rate': 3.944, 'median_profit_rate': 0.65, 'downside_p10_profit_rate': -2.58, 'upside_p90_profit_rate': 2.28, 'win_rate': 0.7, 'loss_rate': 0.3, 'stddev_profit_rate': 11.5839}`

## Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-05-11.json`
- fresh: gemini=`True` claude=`True`
- consensus/orders/family_candidates: `5` / `14` / `3`

## Swing Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-05-11.json`
- deepseek_lab_available: `False`
- findings/orders: `0` / `0`
- data_quality_warnings: `3`
- carryover_warnings: `0`
- population_split_available: `False`

## Swing Runtime Approval
- request_report: `-`
- approval_artifact: `-`
- requested/approved/live_dry_run: `0` / `0` / `0`
- dry_run_forced: `False`
- real_canary_policy: `-`
- real_order_allowed_actions: ``
- sim_only_actions: ``
- scale_in_real_canary_policy: `-`
- selected_scale_in_real_canary: `0`
- scale_in_real_execution_quality: `{'scale_in_canary_selected': 0, 'execution_quality_source': 'real_only', 'sim_probe_ev_source': 'separate_from_broker_execution_quality'}`
- blocked: `[]`

## Code Improvement Workorder
- artifact: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-11.json`
- markdown: `/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-11.md`
- selected_order_count: `19`
- decision_counts: `{'implement_now': 2, 'attach_existing_family': 4, 'design_family_candidate': 4, 'defer_evidence': 5, 'reject': 4}`

## Approval Requests
- none

## Swing Approval Requests
- none

## Calibration Decisions
## Code Improvement Top Orders
- `order_latency_guard_miss_ev_recovery` decision=`implement_now` subsystem=`runtime_instrumentation`
- `order_holding_exit_decision_matrix_edge_counterfactual` decision=`implement_now` subsystem=`runtime_instrumentation`
- `order_ai_threshold_miss_ev_recovery` decision=`attach_existing_family` subsystem=`entry_funnel`

## Pattern Lab Top Findings
- `AI threshold miss EV recovery` route=`existing_family` family=`score65_74_recovery_probe`
- `No acute observability alert` route=`auto_family_candidate` family=`-`
- `latency guard miss EV recovery` route=`instrumentation_order` family=`-`

- `soft_stop_whipsaw_confirmation`: `adjust_up` sample=`45/10`
- `holding_flow_ofi_smoothing`: `hold` sample=`187/20`
- `protect_trailing_smoothing`: `hold_sample` sample=`18/20`
- `trailing_continuation`: `freeze` sample=`18/20`
- `pre_submit_price_guard`: `freeze` sample=`710/20`
- `score65_74_recovery_probe`: `adjust_up` sample=`712/20`
- `liquidity_gate_refined_candidate`: `hold` sample=`3285/20`
- `overbought_gate_refined_candidate`: `hold` sample=`82230/20`
- `bad_entry_refined_canary`: `hold_sample` sample=`565/10`
- `holding_exit_decision_matrix_advisory`: `hold_no_edge` sample=`14/1`
- `scale_in_price_guard`: `hold` sample=`63/20`
- `position_sizing_cap_release`: `hold_sample` sample=`49/30`

## Warnings
- `swing_lab_dq:funnel fact has only 1 rows (min 3)`
- `swing_lab_dq:OFI/QI stale/missing ratio: 0.9189 (68/74)`
- `swing_lab_dq:swing_lab_stale: lab output blocked because invalid_required_output:deepseek_payload_summary(missing_schema_keys)`
- `swing_lab_stale:invalid_required_output:deepseek_payload_summary(missing_schema_keys)`
