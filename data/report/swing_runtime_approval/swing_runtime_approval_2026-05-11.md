# Swing Runtime Approval - 2026-05-11

- Runtime change: `false`
- Approval state: `proposal -> approval_required -> approved_live_dry_run`
- Broker order submission: `false`
- tradeoff_score_threshold: `0.68`
- EV calibration source: `combined_real_plus_sim`
- sim authority: `equal_for_ev_calibration_when_sim_lifecycle_closed`
- execution quality source: `real_only`
- real canary policy: `swing_one_share_real_canary_phase0`
- real canary allowed actions: `BUY_INITIAL, SELL_CLOSE`
- sim-only actions: `AVG_DOWN, PYRAMID, SCALE_IN`
- requested/blocked/approved: `0` / `12` / `0`

## Approval Requests

| approval_id | family | stage | score | sample | target_env_keys |
| --- | --- | --- | ---: | ---: | --- |
| `-` | `none` | `-` | 0 | 0/0 | `-` |

## Blocked

| family | state | score | reasons |
| --- | --- | ---: | --- |
| `swing_model_floor` | `freeze` | 0.8657 | `critical_instrumentation_gap, db_load_gap` |
| `swing_selection_top_k` | `freeze` | 0.8657 | `critical_instrumentation_gap, db_load_gap` |
| `swing_gatekeeper_accept_reject` | `freeze` | 0.8657 | `critical_instrumentation_gap, db_load_gap, runtime_family_guard_missing` |
| `swing_gatekeeper_reject_cooldown` | `freeze` | 0.8657 | `critical_instrumentation_gap, db_load_gap` |
| `swing_market_regime_sensitivity` | `hold_sample` | 0.8157 | `family_sample_floor_not_met, critical_instrumentation_gap, db_load_gap` |
| `swing_pyramid_trigger` | `hold_sample` | 0.8157 | `family_sample_floor_not_met, critical_instrumentation_gap, db_load_gap, runtime_family_guard_missing` |
| `swing_avg_down_eligibility` | `hold_sample` | 0.8157 | `family_sample_floor_not_met, critical_instrumentation_gap, db_load_gap, runtime_family_guard_missing` |
| `swing_trailing_stop_time_stop` | `hold_sample` | 0.8457 | `family_sample_floor_not_met, critical_instrumentation_gap, db_load_gap, runtime_family_guard_missing` |
| `swing_holding_flow_defer` | `freeze` | 0.8657 | `critical_instrumentation_gap, db_load_gap, runtime_family_guard_missing` |
| `swing_entry_ofi_qi_execution_quality` | `hold_sample` | 0.8157 | `family_sample_floor_not_met, critical_instrumentation_gap, db_load_gap, runtime_family_guard_missing` |
| `swing_scale_in_ofi_qi_confirmation` | `hold_sample` | 0.8157 | `family_sample_floor_not_met, critical_instrumentation_gap, db_load_gap, runtime_family_guard_missing` |
| `swing_exit_ofi_qi_smoothing` | `freeze` | 0.8657 | `critical_instrumentation_gap, db_load_gap, runtime_family_guard_missing` |
