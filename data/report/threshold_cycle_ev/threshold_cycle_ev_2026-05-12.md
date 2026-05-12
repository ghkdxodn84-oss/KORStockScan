# Threshold Cycle Daily EV Report - 2026-05-12

## Runtime Apply
- status: `auto_bounded_live_ready`
- runtime_change: `True`
- selected_families: `soft_stop_whipsaw_confirmation, score65_74_recovery_probe`

## Daily EV
- completed: `2` / open: `0`
- win/loss: `2` / `0` (`100.0`%)
- avg_profit_rate: `8.3`%
- realized_pnl_krw: `180642`
- full_fill_completed_avg_profit_rate: `0.0`%

## Entry Funnel
- budget_pass_to_submitted: `0` / `0` (`0.0`%)
- latency pass/block: `0` / `0`
- full/partial fill: `0` / `0`

## Holding Exit
- holding_reviews: `0`
- exit_signals: `32`
- holding_review_ms_p95: `0.0`

## Scalp Simulator
- authority: `equal_weight` / fill_policy: `signal_inclusive_best_ask_v1`
- armed/filled/sold: `0` / `0` / `0`
- expired/unpriced/duplicate: `0` / `0` / `0`
- completed_profit_summary: `{'sample': 0, 'win_count': 0, 'loss_count': 0, 'avg_profit_rate': None, 'median_profit_rate': None, 'downside_p10_profit_rate': None, 'upside_p90_profit_rate': None, 'win_rate': None, 'loss_rate': None, 'stddev_profit_rate': None}`

## Missed Probe Counterfactual
- book: `scalp_score65_74_probe_counterfactual` / role: `missed_buy_probe_counterfactual`
- total/score65_74: `14` / `4`
- avg_expected_ev: `2.2277`% / score65_74_avg_expected_ev: `1.8095`%
- actual_order_submitted: `False` / broker_order_forbidden: `True`
- authority: `missed_probe_ev_only_not_broker_execution`

## Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-05-12.json`
- fresh: gemini=`True` claude=`True`
- consensus/orders/family_candidates: `5` / `14` / `2`

## Swing Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-05-12.json`
- deepseek_lab_available: `True`
- findings/orders: `4` / `2`
- data_quality_warnings: `1`
- ofi_qi_stale_missing_unique_records: `3`
- ofi_qi_stale_missing_reasons: `{'micro_missing': 9, 'micro_stale': 0, 'observer_unhealthy': 3, 'micro_not_ready': 9, 'state_insufficient': 9}`
- ofi_qi_stale_missing_reason_combinations: `{'micro_missing+micro_not_ready+state_insufficient': 6, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 3}`
- ofi_qi_stale_missing_reason_combination_unique_records: `{'micro_missing+micro_not_ready+state_insufficient': 2, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}`
- ofi_qi_observer_unhealthy_overlap: `{'observer_unhealthy_total': 3, 'observer_unhealthy_with_other_reason': 3, 'observer_unhealthy_only': 0}`
- source_quality_blocked_families: `[{'family': 'swing_scale_in_ofi_qi_confirmation', 'stage': 'scale_in', 'source_quality_blockers': ['scale_in_ofi_qi_invalid_micro_context'], 'invalid_micro_context_unique_record_count': 3, 'invalid_reason_combination_unique_record_counts': {'micro_missing+micro_not_ready+state_insufficient': 2, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}, 'automation_input': True, 'runtime_effect': False}]`
- carryover_warnings: `0`
- population_split_available: `True`

## Swing Runtime Approval
- request_report: `/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-05-11.json`
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
- artifact: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-12.json`
- markdown: `/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-12.md`
- selected_order_count: `12`
- decision_counts: `{'implement_now': 2, 'attach_existing_family': 5, 'design_family_candidate': 4, 'defer_evidence': 5, 'reject': 4}`

## Approval Requests
- none

## Swing Approval Requests
- `swing_model_floor` approval_id=`swing_runtime_approval:2026-05-11:swing_model_floor` score=`0.8907` target_env_keys=`['SWING_FLOOR_BULL', 'SWING_FLOOR_BEAR']`
- `swing_gatekeeper_reject_cooldown` approval_id=`swing_runtime_approval:2026-05-11:swing_gatekeeper_reject_cooldown` score=`0.8907` target_env_keys=`['ML_GATEKEEPER_REJECT_COOLDOWN']`

## Calibration Decisions
## Code Improvement Top Orders
- `order_latency_guard_miss_ev_recovery` decision=`implement_now` subsystem=`runtime_instrumentation`
- `order_holding_exit_decision_matrix_edge_counterfactual` decision=`implement_now` subsystem=`runtime_instrumentation`
- `order_ai_threshold_dominance` decision=`attach_existing_family` subsystem=`entry_funnel`

## Pattern Lab Top Findings
- `AI threshold dominance` route=`existing_family` family=`score65_74_recovery_probe`
- `AI threshold miss EV recovery` route=`existing_family` family=`score65_74_recovery_probe`
- `latency guard miss EV recovery` route=`instrumentation_order` family=`-`

- `soft_stop_whipsaw_confirmation`: `adjust_up` sample=`22/10`
- `holding_flow_ofi_smoothing`: `hold_sample` sample=`0/20`
- `protect_trailing_smoothing`: `hold_sample` sample=`18/20`
- `trailing_continuation`: `freeze` sample=`18/20`
- `pre_submit_price_guard`: `hold_sample` sample=`0/20`
- `score65_74_recovery_probe`: `hold_sample` sample=`14/20`
- `liquidity_gate_refined_candidate`: `hold` sample=`8360/20`
- `overbought_gate_refined_candidate`: `hold` sample=`80361/20`
- `bad_entry_refined_canary`: `hold_sample` sample=`22/10`
- `holding_exit_decision_matrix_advisory`: `hold_no_edge` sample=`14/1`
- `scale_in_price_guard`: `hold_sample` sample=`56/20`
- `position_sizing_cap_release`: `hold_sample` sample=`28/30`

## Warnings
- `swing_lab_dq:OFI/QI stale/missing ratio: 0.0776 (9/116); reasons: micro_missing=9, observer_unhealthy=3, micro_not_ready=9, state_insufficient=9`
