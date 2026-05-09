# Swing EV Improvement Backlog for OPS

## 개요

- total_findings: `5`
- runtime_change: `False`
- purpose: report-only / proposal-only improvement backlog

## Improvement Candidates

### 1. Gatekeeper rejects swing entry candidates

- finding_id: `swing_pattern_lab_deepseek_entry_gatekeeper_reject`
- lifecycle_stage: `entry`
- route: `defer_evidence`
- priority: `LOW`
- mapped_family: `-`
- confidence: `solo`
- expected_ev_effect: Carryover-only blocker; observe before attaching to threshold family.

### 2. Swing gap/protection blocking entry

- finding_id: `swing_pattern_lab_deepseek_entry_gap_block`
- lifecycle_stage: `entry`
- route: `defer_evidence`
- priority: `LOW`
- mapped_family: `-`
- confidence: `solo`
- expected_ev_effect: Carryover-only blocker; observe before designing new family.

### 3. Market regime hard block prevents entry

- finding_id: `swing_pattern_lab_deepseek_entry_market_regime_block`
- lifecycle_stage: `entry`
- route: `defer_evidence`
- priority: `LOW`
- mapped_family: `swing_market_regime_sensitivity`
- confidence: `solo`
- expected_ev_effect: Market regime sensitivity should be assessed over longer sample.

### 4. All selected candidates failed to reach order submission

- finding_id: `swing_pattern_lab_deepseek_entry_no_submissions`
- lifecycle_stage: `entry`
- route: `design_family_candidate`
- priority: `MEDIUM`
- mapped_family: `-`
- confidence: `consensus`
- expected_ev_effect: Investigate the entry funnel for swing-specific bottlenecks.

### 5. No completed swing trades in analysis window

- finding_id: `swing_pattern_lab_deepseek_holding_exit_no_trades`
- lifecycle_stage: `holding_exit`
- route: `defer_evidence`
- priority: `LOW`
- mapped_family: `-`
- confidence: `low_sample`
- expected_ev_effect: Insufficient evidence; defer until more trades complete.

