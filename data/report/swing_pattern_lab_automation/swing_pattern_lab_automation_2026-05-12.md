# Swing Pattern Lab Automation - 2026-05-12

## Summary
- deepseek_lab_available: `True`
- findings_count: `4`
- code_improvement_order_count: `2`
- data_quality_warning_count: `1`
- carryover_warning_count: `0`
- runtime_change: `False`

## Consensus Findings
- `swing_pattern_lab_deepseek_entry_no_submissions` route=`design_family_candidate` family=`-` stage=`entry`
- `swing_pattern_lab_deepseek_holding_exit_no_trades` route=`defer_evidence` family=`-` stage=`holding_exit`
- `swing_pattern_lab_deepseek_scale_in_events_observed` route=`attach_existing_family` family=`swing_scale_in_ofi_qi_confirmation` stage=`scale_in`
- `swing_pattern_lab_deepseek_ofi_qi_stale_missing` route=`defer_evidence` family=`swing_entry_ofi_qi_execution_quality` stage=`ofi_qi`

## Code Improvement Orders
- `order_swing_pattern_lab_deepseek_entry_no_submissions` All selected candidates failed to reach order submission decision=`design_family_candidate` subsystem=`swing_entry_funnel` runtime_effect=`False`
- `order_swing_pattern_lab_deepseek_scale_in_events_observed` Scale-in events observed for swing positions decision=`attach_existing_family` subsystem=`swing_scale_in` runtime_effect=`False`

## OFI/QI Quality
- stale_missing_ratio: `0.0776`
- stale_missing_unique_record_count: `3`
- reason_counts: `{'micro_missing': 9, 'micro_stale': 0, 'observer_unhealthy': 3, 'micro_not_ready': 9, 'state_insufficient': 9}`
- reason_combination_counts: `{'micro_missing+micro_not_ready+state_insufficient': 6, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 3}`
- reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 2, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}`
- stale_missing_group_counts: `{'scale_in': 9}`
- stale_missing_group_unique_record_counts: `{'scale_in': 3}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 3, 'observer_unhealthy_with_other_reason': 3, 'observer_unhealthy_only': 0}`
- source_quality_blocked_families: `[{'family': 'swing_scale_in_ofi_qi_confirmation', 'stage': 'scale_in', 'source_quality_blockers': ['scale_in_ofi_qi_invalid_micro_context'], 'invalid_micro_context_unique_record_count': 3, 'invalid_reason_combination_unique_record_counts': {'micro_missing+micro_not_ready+state_insufficient': 2, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}, 'automation_input': True, 'runtime_effect': False}]`
