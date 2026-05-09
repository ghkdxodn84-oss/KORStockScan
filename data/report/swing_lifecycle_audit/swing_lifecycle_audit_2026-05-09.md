# Swing Lifecycle Audit - 2026-05-09

- owner: `SwingFullLifecycleSelfImprovementChain`
- runtime_change: `false`
- selected_count: `5`
- csv_rows: `5`
- db_rows: `0`
- entered_rows: `0`
- completed_rows: `0`
- submitted_unique_records: `0`
- simulated_order_unique_records: `0`
- observation_axis_status: `{'ready': 3, 'hold_sample': 3, 'instrumentation_gap': 1}`

## Lifecycle Funnel

| group | raw | unique_records |
| --- | ---: | ---: |
| `entry` | 0 | 0 |
| `holding` | 4 | 1 |
| `scale_in` | 0 | 0 |
| `exit` | 20 | 2 |
| `other` | 0 | 0 |

## Key Stages

| stage | raw | unique_records |
| --- | ---: | ---: |
| `holding_started` | 4 | 1 |
| `sell_order_sent` | 20 | 2 |

## Observation Axes

| axis | stage | family | sample | status |
| --- | --- | --- | ---: | --- |
| `swing_selection_model_floor` | `selection` | `swing_model_floor` | 5 | `ready` |
| `swing_recommendation_db_load` | `db_load` | `swing_selection_top_k` | 5 | `ready` |
| `swing_gatekeeper_accept_reject` | `entry` | `swing_gatekeeper_accept_reject` | 0 | `hold_sample` |
| `swing_gap_market_budget_price_qty` | `entry` | `swing_market_regime_sensitivity` | 0 | `hold_sample` |
| `swing_holding_mfe_mae_defer` | `holding` | `swing_holding_flow_defer` | 1 | `instrumentation_gap` |
| `swing_scale_in_avg_down_pyramid` | `scale_in` | `swing_pyramid_trigger` | 0 | `hold_sample` |
| `swing_exit_post_sell_attribution` | `exit` | `swing_trailing_stop_time_stop` | 2 | `ready` |

## AI Contract Audit

- `swing_gatekeeper_free_text_label` stage=`entry` severity=`medium`: Gatekeeper entry is currently reconstructed from report labels instead of a strict swing entry schema.
- `swing_holding_flow_scalping_prompt_reuse` stage=`holding_exit` severity=`medium`: Swing sell candidates can pass through holding-flow review that is named and tuned for scalping.
- `swing_scale_in_ai_contract_missing` stage=`scale_in` severity=`low`: Swing PYRAMID/AVG_DOWN observation is not yet represented by a dedicated AI proposal contract.
