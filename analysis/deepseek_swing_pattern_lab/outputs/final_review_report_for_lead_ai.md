# DeepSeek Swing Pattern Lab - Final Review Report

## 판정

- 분석 기간: `2026-05-08` ~ `2026-05-09`
- trade_rows: `0`
- lifecycle_event_rows: `19`
- completed_valid_profit_rows: `0`
- ofi_qi_rows: `0`
- total_findings: `5`
- code_improvement_orders: `1`
- runtime_change: `False`

## 분류 요약

- implement_now: `0`
- attach_existing_family: `0`
- design_family_candidate: `1`
- defer_evidence: `4`
- reject: `0`

## Stage별 분석

- `entry`: 4 findings
- `holding_exit`: 1 findings

## Stage Findings

### 1. `swing_pattern_lab_deepseek_entry_gatekeeper_reject`

- title: Gatekeeper rejects swing entry candidates
- lifecycle_stage: `entry`
- route: `defer_evidence`
- mapped_family: `-`
- confidence: `solo`
- runtime_effect: `False`
- expected_ev_effect: Carryover-only blocker; observe before attaching to threshold family.

### 2. `swing_pattern_lab_deepseek_entry_gap_block`

- title: Swing gap/protection blocking entry
- lifecycle_stage: `entry`
- route: `defer_evidence`
- mapped_family: `-`
- confidence: `solo`
- runtime_effect: `False`
- expected_ev_effect: Carryover-only blocker; observe before designing new family.

### 3. `swing_pattern_lab_deepseek_entry_market_regime_block`

- title: Market regime hard block prevents entry
- lifecycle_stage: `entry`
- route: `defer_evidence`
- mapped_family: `swing_market_regime_sensitivity`
- confidence: `solo`
- runtime_effect: `False`
- expected_ev_effect: Market regime sensitivity should be assessed over longer sample.

### 4. `swing_pattern_lab_deepseek_entry_no_submissions`

- title: All selected candidates failed to reach order submission
- lifecycle_stage: `entry`
- route: `design_family_candidate`
- mapped_family: `-`
- confidence: `consensus`
- runtime_effect: `False`
- expected_ev_effect: Investigate the entry funnel for swing-specific bottlenecks.

### 5. `swing_pattern_lab_deepseek_holding_exit_no_trades`

- title: No completed swing trades in analysis window
- lifecycle_stage: `holding_exit`
- route: `defer_evidence`
- mapped_family: `-`
- confidence: `low_sample`
- runtime_effect: `False`
- expected_ev_effect: Insufficient evidence; defer until more trades complete.

## Code Improvement Orders

### 1. `order_swing_pattern_lab_deepseek_entry_no_submissions`

- title: All selected candidates failed to reach order submission
- lifecycle_stage: `entry`
- target_subsystem: `swing_entry_funnel`
- route: `design_family_candidate`
- mapped_family: `-`
- threshold_family: `-`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- expected_ev_effect: Investigate the entry funnel for swing-specific bottlenecks.
- files_likely_touched: `src/engine/swing_lifecycle_audit.py`, `src/engine/swing_selection_funnel_report.py`, `src/model/common_v2.py`

## Data Quality Warnings

- funnel fact has only 2 rows (min 3)
- no OFI/QI micro context data found
