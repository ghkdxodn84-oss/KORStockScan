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

## Calibration Decisions
## Pattern Lab Top Findings
- `AI threshold dominance` route=`existing_family` family=`score65_74_recovery_probe`
- `AI threshold miss EV recovery` route=`existing_family` family=`score65_74_recovery_probe`
- `latency guard miss EV recovery` route=`instrumentation_order` family=`-`

- `soft_stop_whipsaw_confirmation`: `adjust_up` sample=`28/10`
- `holding_flow_ofi_smoothing`: `hold` sample=`59/20`
- `protect_trailing_smoothing`: `hold_sample` sample=`18/20`
- `trailing_continuation`: `freeze` sample=`18/20`
- `score65_74_recovery_probe`: `adjust_up` sample=`703/20`
- `bad_entry_refined_canary`: `hold_sample` sample=`55/10`
- `holding_exit_decision_matrix_advisory`: `hold_no_edge` sample=`14/1`
- `scale_in_price_guard`: `hold` sample=`21/20`
