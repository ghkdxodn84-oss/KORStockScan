# DeepSeek Swing Pattern Lab - Data Quality Report

## Analysis Window: 2026-05-13 ~ 2026-05-13

## Fact Table Row Counts

- swing_trade_fact: `0`
- swing_lifecycle_funnel_fact: `1`
- swing_sequence_fact: `35`
- swing_ofi_qi_fact: `161`
- completed_trades: `0`
- valid_profit_trades: `0`

## OFI/QI Quality

- stale_missing_count: `1`
- stale_missing_unique_record_count: `1`
- stale_missing_ratio: `0.0062`
- reason_counts: `{'micro_missing': 1, 'micro_stale': 0, 'observer_unhealthy': 0, 'micro_not_ready': 1, 'state_insufficient': 1}`
- reason_combination_counts: `{'micro_missing+micro_not_ready+state_insufficient': 1}`
- reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 1}`
- stale_missing_group_counts: `{'exit': 1}`
- stale_missing_group_unique_record_counts: `{'exit': 1}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`

## Warnings

- OFI/QI stale/missing ratio: 0.0062 (1/161); reasons: micro_missing=1, micro_not_ready=1, state_insufficient=1
