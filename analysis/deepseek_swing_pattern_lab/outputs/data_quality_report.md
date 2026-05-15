# DeepSeek Swing Pattern Lab - Data Quality Report

## Analysis Window: 2026-05-15 ~ 2026-05-15

## Fact Table Row Counts

- swing_trade_fact: `0`
- swing_lifecycle_funnel_fact: `1`
- swing_sequence_fact: `39`
- swing_ofi_qi_fact: `127`
- completed_trades: `0`
- valid_profit_trades: `0`

## OFI/QI Quality

- stale_missing_count: `16`
- stale_missing_unique_record_count: `5`
- stale_missing_ratio: `0.126`
- reason_counts: `{'micro_missing': 16, 'micro_stale': 0, 'observer_unhealthy': 2, 'micro_not_ready': 15, 'state_insufficient': 15}`
- reason_combination_counts: `{'micro_missing': 1, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 2, 'micro_missing+micro_not_ready+state_insufficient': 13}`
- reason_combination_unique_record_counts: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 2, 'micro_missing+micro_not_ready+state_insufficient': 4}`
- stale_missing_group_counts: `{'holding': 1, 'exit': 3, 'scale_in': 12}`
- stale_missing_group_unique_record_counts: `{'exit': 3, 'scale_in': 4}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 2, 'observer_unhealthy_with_other_reason': 2, 'observer_unhealthy_only': 0}`

## Warnings

- OFI/QI stale/missing ratio: 0.126 (16/127); reasons: micro_missing=16, observer_unhealthy=2, micro_not_ready=15, state_insufficient=15
