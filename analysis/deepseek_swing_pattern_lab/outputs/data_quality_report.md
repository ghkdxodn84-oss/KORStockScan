# DeepSeek Swing Pattern Lab - Data Quality Report

## Analysis Window: 2026-05-14 ~ 2026-05-14

## Fact Table Row Counts

- swing_trade_fact: `0`
- swing_lifecycle_funnel_fact: `1`
- swing_sequence_fact: `38`
- swing_ofi_qi_fact: `1111`
- completed_trades: `0`
- valid_profit_trades: `0`

## OFI/QI Quality

- stale_missing_count: `59`
- stale_missing_unique_record_count: `2`
- stale_missing_ratio: `0.0531`
- reason_counts: `{'micro_missing': 59, 'micro_stale': 0, 'observer_unhealthy': 31, 'micro_not_ready': 2, 'state_insufficient': 2}`
- reason_combination_counts: `{'micro_missing': 28, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 2, 'micro_missing+observer_unhealthy': 29}`
- reason_combination_unique_record_counts: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 2, 'micro_missing+observer_unhealthy': 1}`
- stale_missing_group_counts: `{'holding': 28, 'scale_in': 31}`
- stale_missing_group_unique_record_counts: `{'scale_in': 2}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 31, 'observer_unhealthy_with_other_reason': 31, 'observer_unhealthy_only': 0}`

## Warnings

- OFI/QI stale/missing ratio: 0.0531 (59/1111); reasons: micro_missing=59, observer_unhealthy=31, micro_not_ready=2, state_insufficient=2
