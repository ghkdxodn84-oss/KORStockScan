# Swing Runtime Approval - 2026-05-14

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
- scale-in real canary policy: `swing_scale_in_real_canary_phase0`
- scale-in allowed actions: `PYRAMID, AVG_DOWN`
- requested/blocked/approved: `2` / `11` / `0`

## Approval Requests

| approval_id | family | stage | score | sample | target_env_keys |
| --- | --- | --- | ---: | ---: | --- |
| `swing_runtime_approval:2026-05-14:swing_model_floor` | `swing_model_floor` | `selection` | 0.6811 | 3/3 | `SWING_FLOOR_BULL, SWING_FLOOR_BEAR` |
| `swing_runtime_approval:2026-05-14:swing_gatekeeper_reject_cooldown` | `swing_gatekeeper_reject_cooldown` | `entry` | 0.6811 | 12/5 | `ML_GATEKEEPER_REJECT_COOLDOWN` |

## Blocked

| family | state | score | reasons |
| --- | --- | ---: | --- |
| `swing_selection_top_k` | `freeze` | 0.6811 | `same_stage_owner_conflict:swing_model_floor` |
| `swing_gatekeeper_accept_reject` | `freeze` | 0.6811 | `runtime_family_guard_missing` |
| `swing_market_regime_sensitivity` | `freeze` | 0.6811 | `same_stage_owner_conflict:swing_gatekeeper_reject_cooldown` |
| `swing_pyramid_trigger` | `freeze` | 0.6811 | `runtime_family_guard_missing` |
| `swing_avg_down_eligibility` | `freeze` | 0.6811 | `runtime_family_guard_missing` |
| `swing_trailing_stop_time_stop` | `freeze` | 0.6811 | `runtime_family_guard_missing` |
| `swing_holding_flow_defer` | `hold_sample` | 0.6511 | `family_sample_floor_not_met, runtime_family_guard_missing` |
| `swing_entry_ofi_qi_execution_quality` | `hold_sample` | 0.6311 | `family_sample_floor_not_met, runtime_family_guard_missing` |
| `swing_scale_in_ofi_qi_confirmation` | `freeze` | 0.6811 | `scale_in_ofi_qi_invalid_micro_context, runtime_family_guard_missing` |
| `swing_exit_ofi_qi_smoothing` | `freeze` | 0.6811 | `runtime_family_guard_missing` |
| `swing_scale_in_real_canary_phase0` | `freeze` | None | `scale_in_ofi_qi_invalid_micro_context, final_exit_return_missing, exit_only_delta_missing, post_add_mae_missing, scale_in_ofi_qi_invalid_micro_context, final_exit_return_missing, exit_only_delta_missing, post_add_mae_missing` |

## Source Quality Blockers

| family | stage | reasons | valid/invalid |
| --- | --- | --- | ---: |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `scale_in_ofi_qi_invalid_micro_context` | 1037/2 |
| `swing_scale_in_real_canary_phase0` | `scale_in` | `scale_in_ofi_qi_invalid_micro_context` | 1037/2 |
