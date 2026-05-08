# Threshold Cycle Daily EV Report - 2026-05-08

## Runtime Apply
- status: `manifest_ready`
- runtime_change: `False`
- selected_families: `-`

## Daily EV
- completed: `3` / open: `0`
- win/loss: `1` / `2` (`33.33`%)
- avg_profit_rate: `-0.85`%
- realized_pnl_krw: `-431`
- full_fill_completed_avg_profit_rate: `-0.847`%

## Entry Funnel
- budget_pass_to_submitted: `10` / `703` (`1.42`%)
- latency pass/block: `11` / `692`
- full/partial fill: `12` / `9`

## Holding Exit
- holding_reviews: `31`
- exit_signals: `18`
- holding_review_ms_p95: `15354.0`

## Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-05-08.json`
- fresh: gemini=`True` claude=`True`
- consensus/orders/family_candidates: `5` / `14` / `2`

## Code Improvement Workorder
- artifact: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-08.json`
- markdown: `/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-08.md`
- selected_order_count: `12`
- decision_counts: `{'implement_now': 1, 'attach_existing_family': 2, 'design_family_candidate': 2, 'defer_evidence': 5, 'reject': 4}`

## Calibration Decisions
## Code Improvement Top Orders
- `order_latency_guard_miss_ev_recovery` decision=`implement_now` subsystem=`runtime_instrumentation`
- `order_ai_threshold_dominance` decision=`attach_existing_family` subsystem=`entry_funnel`
- `order_ai_threshold_miss_ev_recovery` decision=`attach_existing_family` subsystem=`entry_funnel`

## Pattern Lab Top Findings
- `AI threshold dominance` route=`existing_family` family=`score65_74_recovery_probe`
- `AI threshold miss EV recovery` route=`existing_family` family=`score65_74_recovery_probe`
- `latency guard miss EV recovery` route=`instrumentation_order` family=`-`

- `soft_stop_whipsaw_confirmation`: `adjust_up` sample=`28/10`
- `holding_flow_ofi_smoothing`: `hold` sample=`59/20`
- `protect_trailing_smoothing`: `hold_sample` sample=`18/20`
- `trailing_continuation`: `freeze` sample=`18/20`
- `pre_submit_price_guard`: `freeze` sample=`692/20`
- `score65_74_recovery_probe`: `adjust_up` sample=`703/20`
- `liquidity_gate_refined_candidate`: `hold_sample` sample=`0/20`
- `overbought_gate_refined_candidate`: `hold_sample` sample=`0/20`
- `bad_entry_refined_canary`: `hold_sample` sample=`55/10`
- `holding_exit_decision_matrix_advisory`: `hold_no_edge` sample=`14/1`
- `scale_in_price_guard`: `hold` sample=`21/20`
