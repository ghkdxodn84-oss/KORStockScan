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
- budget_pass_to_submitted: `0` / `82` (`0.0`%)
- latency pass/block: `0` / `82`
- full/partial fill: `3` / `3`

## Holding Exit
- holding_reviews: `25`
- exit_signals: `48`
- holding_review_ms_p95: `2530.0`

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
- total/score65_74: `19` / `0`
- avg_expected_ev: `7.4801`% / score65_74_avg_expected_ev: `0.0`%
- actual_order_submitted: `False` / broker_order_forbidden: `True`
- authority: `missed_probe_ev_only_not_broker_execution`

## Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-05-15.json`
- fresh: gemini=`True` claude=`True`
- consensus/orders/family_candidates: `6` / `15` / `3`

## Swing Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-05-15.json`
- deepseek_lab_available: `True`
- findings/orders: `5` / `3`
- data_quality_warnings: `1`
- ofi_qi_stale_missing_unique_records: `5`
- ofi_qi_stale_missing_reasons: `{'micro_missing': 16, 'micro_stale': 0, 'observer_unhealthy': 2, 'micro_not_ready': 15, 'state_insufficient': 15}`
- ofi_qi_stale_missing_reason_combinations: `{'micro_missing': 1, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 2, 'micro_missing+micro_not_ready+state_insufficient': 13}`
- ofi_qi_stale_missing_reason_combination_unique_records: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 2, 'micro_missing+micro_not_ready+state_insufficient': 4}`
- ofi_qi_observer_unhealthy_overlap: `{'observer_unhealthy_total': 2, 'observer_unhealthy_with_other_reason': 2, 'observer_unhealthy_only': 0}`
- source_quality_blocked_families: `[{'family': 'swing_scale_in_ofi_qi_confirmation', 'stage': 'scale_in', 'source_quality_blockers': ['scale_in_ofi_qi_invalid_micro_context'], 'invalid_micro_context_unique_record_count': 4, 'invalid_reason_combination_unique_record_counts': {'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 2, 'micro_missing+micro_not_ready+state_insufficient': 4}, 'automation_input': True, 'runtime_effect': False}]`
- carryover_warnings: `0`
- population_split_available: `True`

## Pipeline Event Verbosity
- artifact: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-05-15.json`
- state: `v2_shadow_missing`
- recommended_workorder_state: `open_shadow_order`
- high_volume_line_count: `1376713`
- high_volume_byte_share_pct: `96.87`
- parity_ok: `False`
- suppress_eligibility: `False`

## Codebase Performance Workorder Source
- artifact: `/home/ubuntu/KORStockScan/data/report/codebase_performance_workorder/codebase_performance_workorder_2026-05-15.json`
- authority: `ops_performance_workorder_source`
- accepted/deferred/rejected: `7` / `3` / `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`

## Swing Runtime Approval
- request_report: `/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-05-14.json`
- approval_artifact: `-`
- requested/approved/live_dry_run: `2` / `0` / `0`
- dry_run_forced: `False`
- real_canary_policy: `swing_one_share_real_canary_phase0`
- one_share_real_canary_artifact: `-`
- selected_one_share_real_canary: `0`
- real_order_allowed_actions: `BUY_INITIAL, SELL_CLOSE`
- sim_only_actions: `AVG_DOWN, PYRAMID, SCALE_IN`
- scale_in_real_canary_policy: `swing_scale_in_real_canary_phase0`
- selected_scale_in_real_canary: `0`
- scale_in_real_execution_quality: `{'one_share_canary_selected': 0, 'scale_in_canary_selected': 0, 'execution_quality_source': 'real_only', 'sim_probe_ev_source': 'separate_from_broker_execution_quality'}`
- blocked: `['approval_artifact_missing']`

## Code Improvement Workorder
- artifact: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-15.json`
- markdown: `/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-15.md`
- selected_order_count: `12`
- decision_counts: `{'implement_now': 11, 'attach_existing_family': 8, 'design_family_candidate': 6, 'defer_evidence': 10, 'reject': 6}`

## Approval Requests
- none

## Swing Approval Requests
- `swing_model_floor` approval_id=`swing_runtime_approval:2026-05-14:swing_model_floor` score=`0.6811` target_env_keys=`['SWING_FLOOR_BULL', 'SWING_FLOOR_BEAR']`
- `swing_gatekeeper_reject_cooldown` approval_id=`swing_runtime_approval:2026-05-14:swing_gatekeeper_reject_cooldown` score=`0.6811` target_env_keys=`['ML_GATEKEEPER_REJECT_COOLDOWN']`

## Calibration Decisions
## Code Improvement Top Orders
- `order_ai_source_quality_not_evaluated_provenance` decision=`implement_now` subsystem=`runtime_instrumentation`
- `order_perf_buy_funnel_json_scan` decision=`implement_now` subsystem=`buy_funnel_sentinel`
- `order_pipeline_event_compaction_v2_shadow` decision=`implement_now` subsystem=`runtime_instrumentation`

## Pattern Lab Top Findings
- `AI threshold dominance` route=`existing_family` family=`score65_74_recovery_probe`
- `AI threshold miss EV recovery` route=`existing_family` family=`score65_74_recovery_probe`
- `Budget pass without submit` route=`auto_family_candidate` family=`-`

- `soft_stop_whipsaw_confirmation`: `adjust_up` sample=`469/10`
- `holding_flow_ofi_smoothing`: `hold` sample=`61/20`
- `protect_trailing_smoothing`: `adjust_down` sample=`150/20`
- `trailing_continuation`: `freeze` sample=`119/20`
- `pre_submit_price_guard`: `freeze` sample=`82/20`
- `score65_74_recovery_probe`: `adjust_up` sample=`196/20`
- `liquidity_gate_refined_candidate`: `hold` sample=`31311/20`
- `overbought_gate_refined_candidate`: `hold` sample=`508830/20`
- `bad_entry_refined_canary`: `adjust_up` sample=`2821/10`
- `holding_exit_decision_matrix_advisory`: `hold_no_edge` sample=`3/1`
- `scale_in_price_guard`: `hold` sample=`316/20`
- `position_sizing_cap_release`: `hold_sample` sample=`29/30`
- `position_sizing_dynamic_formula`: `hold_sample` sample=`1/30`

## Warnings
- `swing_lab_dq:OFI/QI stale/missing ratio: 0.126 (16/127); reasons: micro_missing=16, observer_unhealthy=2, micro_not_ready=15, state_insufficient=15`
