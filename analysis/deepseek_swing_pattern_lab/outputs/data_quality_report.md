# DeepSeek Swing Pattern Lab - Data Quality Report

## Analysis Window: 2026-05-12 ~ 2026-05-12

## Fact Table Row Counts

- swing_trade_fact: `0`
- swing_lifecycle_funnel_fact: `1`
- swing_sequence_fact: `38`
- swing_ofi_qi_fact: `116`
- completed_trades: `0`
- valid_profit_trades: `0`

## OFI/QI Quality

- stale_missing_count: `9`
- stale_missing_unique_record_count: `3`
- stale_missing_ratio: `0.0776`
- reason_counts: `{'micro_missing': 9, 'micro_stale': 0, 'observer_unhealthy': 3, 'micro_not_ready': 9, 'state_insufficient': 9}`
- reason_combination_counts: `{'micro_missing+micro_not_ready+state_insufficient': 6, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 3}`
- reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 2, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}`
- stale_missing_group_counts: `{'scale_in': 9}`
- stale_missing_group_unique_record_counts: `{'scale_in': 3}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 3, 'observer_unhealthy_with_other_reason': 3, 'observer_unhealthy_only': 0}`

## Warnings

- OFI/QI stale/missing ratio: 0.0776 (9/116); reasons: micro_missing=9, observer_unhealthy=3, micro_not_ready=9, state_insufficient=9
