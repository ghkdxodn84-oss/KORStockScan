# Threshold Cycle AI Correction - 2026-05-08 intraday

- AI status: `parsed`
- Authority: proposal-only; deterministic calibration guard is the source of truth.
- Runtime change: `false`

| family | ai_state | route | proposal | guard | reason |
| --- | --- | --- | --- | --- | --- |
| soft_stop_whipsaw_confirmation | agree | threshold_candidate | state=adjust_up, value=60, window=rolling_10d | accepted=True, effective_state=adjust_up, effective_value=60, runtime_change=False | High rebound rates justify enabling the candidate. Bounded to daily limits and pre-market activation. |
| holding_flow_ofi_smoothing | agree | normal_drift | state=hold, value=90, window=daily_intraday | accepted=True, effective_state=hold, effective_value=90, runtime_change=False | Current and recommended values align. Defer cost remains within acceptable limits. |
| protect_trailing_smoothing | agree | normal_drift | state=hold_sample, value=20, window=rolling_10d | accepted=False, effective_state=hold_sample, effective_value=20, runtime_change=False | window_policy_blocks_single_case_live_candidate:18/20 |
| trailing_continuation | safety_concern | incident | state=freeze, value=0.4, window=rolling_10d | accepted=False, effective_state=hold_sample, effective_value=0.4, runtime_change=False | window_policy_blocks_single_case_live_candidate:18/20 |
| score65_74_recovery_probe | correction_proposed | threshold_candidate | state=adjust_up, value=True, window=daily_intraday | accepted=True, effective_state=adjust_up, effective_value=True, runtime_change=False | Severe missed entry drought observed. Activating bounded canary to gather post-apply samples. |
| bad_entry_refined_canary | agree | threshold_candidate | state=adjust_up, value=True, window=rolling_10d | accepted=True, effective_state=adjust_up, effective_value=True, runtime_change=False | Soft-stop tail metrics support transitioning from naive block to a refined canary. |
| holding_exit_decision_matrix_advisory | correction_proposed | instrumentation_gap | state=freeze, value=False, window=cumulative | accepted=True, effective_state=hold_sample, effective_value=False, runtime_change=False | No clear edge in ADM/SAW matrix. Correcting non-compliant 'hold_no_edge' state to 'freeze'. |
| scale_in_price_guard | agree | instrumentation_gap | state=hold_sample, value=60, window=cumulative | accepted=True, effective_state=hold_sample, effective_value=60, runtime_change=False | Scale-in samples are extremely sparse (3/20). Guard value preserved. |
