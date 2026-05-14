# Swing Threshold AI Review - 2026-05-14

- AI status: `parsed`
- Authority: proposal-only; deterministic guard and manual workorder remain the source of truth.
- Runtime change: `false`

| family | stage | deterministic | ai_state | proposal | guard |
| --- | --- | --- | --- | --- | --- |
| `swing_model_floor` | `selection` | `approval_required` | `correction_proposed` | state=hold, value=floor_bull=0.35,floor_bear=0.4 | accepted=False, reason=missing_numeric_bounds_for_value_proposal |
| `swing_selection_top_k` | `selection` | `freeze` | `agree` | state=freeze, value=3 | accepted=True, reason=- |
| `swing_gatekeeper_accept_reject` | `entry` | `freeze` | `agree` | state=freeze, value=None | accepted=True, reason=- |
| `swing_gatekeeper_reject_cooldown` | `entry` | `approval_required` | `correction_proposed` | state=hold_sample, value=7200 | accepted=True, reason=- |
| `swing_market_regime_sensitivity` | `entry` | `freeze` | `agree` | state=freeze, value=regime_sensitivity=standard | accepted=False, reason=missing_numeric_bounds_for_value_proposal |
| `swing_pyramid_trigger` | `scale_in` | `freeze` | `agree` | state=freeze, value=None | accepted=True, reason=- |
| `swing_avg_down_eligibility` | `scale_in` | `freeze` | `agree` | state=freeze, value=None | accepted=True, reason=- |
| `swing_trailing_stop_time_stop` | `exit` | `freeze` | `agree` | state=freeze, value=None | accepted=True, reason=- |
| `swing_holding_flow_defer` | `holding_exit` | `hold_sample` | `agree` | state=hold_sample, value=None | accepted=True, reason=- |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `hold_sample` | `agree` | state=hold_sample, value=None | accepted=True, reason=- |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `freeze` | `agree` | state=freeze, value=None | accepted=True, reason=- |
| `swing_exit_ofi_qi_smoothing` | `holding_exit` | `freeze` | `agree` | state=freeze, value=None | accepted=True, reason=- |
