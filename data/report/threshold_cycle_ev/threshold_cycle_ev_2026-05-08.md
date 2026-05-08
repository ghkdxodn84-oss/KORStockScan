# Threshold Cycle Daily EV Report - 2026-05-08

## Runtime Apply
- status: `manifest_ready`
- runtime_change: `False`
- selected_families: `-`

## Daily EV
- completed: `2` / open: `0`
- win/loss: `1` / `1` (`50.0`%)
- avg_profit_rate: `-0.39`%
- realized_pnl_krw: `-282`
- full_fill_completed_avg_profit_rate: `-0.395`%

## Entry Funnel
- budget_pass_to_submitted: `6` / `368` (`1.63`%)
- latency pass/block: `6` / `362`
- full/partial fill: `2` / `0`

## Holding Exit
- holding_reviews: `17`
- exit_signals: `2`
- holding_review_ms_p95: `17022.0`

## Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-05-08.json`
- fresh: gemini=`False` claude=`False`
- consensus/orders/family_candidates: `0` / `0` / `0`

## Calibration Decisions
- `soft_stop_whipsaw_confirmation`: `hold_sample` sample=`13/10`
- `holding_flow_ofi_smoothing`: `hold` sample=`50/20`
- `protect_trailing_smoothing`: `hold_sample` sample=`0/20`
- `trailing_continuation`: `freeze` sample=`1/20`
- `score65_74_recovery_probe`: `adjust_up` sample=`294/20`
- `bad_entry_refined_canary`: `adjust_up` sample=`20/10`
- `holding_exit_decision_matrix_advisory`: `hold_no_edge` sample=`0/1`
- `scale_in_price_guard`: `hold_sample` sample=`3/20`

## Warnings
- `pattern_lab_gemini_stale`
- `pattern_lab_claude_stale`
