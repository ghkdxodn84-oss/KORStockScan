# Swing Improvement Automation - 2026-05-09

- Runtime change: `false`
- Generated orders are inputs for `build_code_improvement_workorder`; implementation is manual.

## Orders

| order_id | stage | subsystem | route | family | priority |
| --- | --- | --- | --- | --- | ---: |
| `order_swing_lifecycle_observation_coverage` | `full_lifecycle` | `runtime_instrumentation` | `instrumentation_order` | `-` | 1 |
| `order_swing_recommendation_db_load_gap` | `db_load` | `runtime_instrumentation` | `instrumentation_order` | `-` | 2 |
| `order_swing_ai_contract_structured_output_eval` | `ai_contract` | `swing_ai_contract` | `auto_family_candidate` | `-` | 5 |
| `order_swing_scale_in_avg_down_pyramid_observation` | `scale_in` | `swing_scale_in` | `auto_family_candidate` | `-` | 6 |
