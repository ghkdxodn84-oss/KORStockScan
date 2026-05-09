# Threshold Cycle Daily EV Report - 2026-05-09

## Runtime Apply
- status: `None`
- runtime_change: `False`
- selected_families: `-`

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
- exit_signals: `0`
- holding_review_ms_p95: `0.0`

## Pattern Lab Automation
- artifact: `-`
- fresh: gemini=`False` claude=`False`
- consensus/orders/family_candidates: `0` / `0` / `0`

## Swing Pattern Lab Automation
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_2026-05-09.json`
- deepseek_lab_available: `False`
- findings/orders: `0` / `0`
- data_quality_warnings: `3`
- carryover_warnings: `0`
- population_split_available: `False`

## Code Improvement Workorder
- artifact: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-09.json`
- markdown: `/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-09.md`
- selected_order_count: `4`
- decision_counts: `{'implement_now': 2, 'design_family_candidate': 2}`

## Calibration Decisions
## Code Improvement Top Orders
- `order_swing_lifecycle_observation_coverage` decision=`implement_now` subsystem=`runtime_instrumentation`
- `order_swing_recommendation_db_load_gap` decision=`implement_now` subsystem=`runtime_instrumentation`
- `order_swing_ai_contract_structured_output_eval` decision=`design_family_candidate` subsystem=`swing_ai_contract`

- no calibration decisions

## Warnings
- `trade_review_missing`
- `performance_tuning_missing`
- `calibration_report_missing`
- `apply_manifest_missing`
- `pattern_lab_automation_missing`
- `swing_lab_dq:funnel fact has only 2 rows (min 3)`
- `swing_lab_dq:no OFI/QI micro context data found`
- `swing_lab_dq:swing_lab_stale: lab output blocked because analysis_start_mismatch(expected=2026-05-09, actual=2026-05-08)`
- `swing_lab_stale:analysis_start_mismatch(expected=2026-05-09, actual=2026-05-08)`
