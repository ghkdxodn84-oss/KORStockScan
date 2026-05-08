# Threshold Cycle AI Correction - 2026-05-08 postclose

- AI status: `parsed`
- Authority: proposal-only; deterministic calibration guard is the source of truth.
- Runtime change: `false`

| family | ai_state | route | proposal | guard | reason |
| --- | --- | --- | --- | --- | --- |
| soft_stop_whipsaw_confirmation | insufficient_context | - | state=-, value=-, window=- | accepted=False, effective_state=adjust_up, effective_value=60, runtime_change=False | ai_proposal_missing_for_family |
| holding_flow_ofi_smoothing | insufficient_context | - | state=-, value=-, window=- | accepted=False, effective_state=hold, effective_value=90, runtime_change=False | ai_proposal_missing_for_family |
| protect_trailing_smoothing | caution | normal_drift | state=hold_sample, value=20, window=rolling_10d | accepted=False, effective_state=hold_sample, effective_value=20, runtime_change=False | window_policy_blocks_single_case_live_candidate:18/20 |
| trailing_continuation | safety_concern | normal_drift | state=freeze, value=0.4, window=rolling_10d | accepted=False, effective_state=hold_sample, effective_value=0.4, runtime_change=False | window_policy_blocks_single_case_live_candidate:18/20 |
| score65_74_recovery_probe | insufficient_context | - | state=-, value=-, window=- | accepted=False, effective_state=adjust_up, effective_value=False, runtime_change=False | ai_proposal_missing_for_family |
| bad_entry_refined_canary | agree | normal_drift | state=hold_sample, value=False, window=rolling_10d | accepted=True, effective_state=hold_sample, effective_value=False, runtime_change=False | 런타임 provisional 시그널이므로 최종 확정은 장후 post-sell outcome 조인까지 보류하는 조치에 동의합니다. |
| holding_exit_decision_matrix_advisory | correction_proposed | normal_drift | state=hold, value=False, window=rolling_10d | accepted=True, effective_state=hold, effective_value=False, runtime_change=False | 제안된 상태 'hold_no_edge'는 비표준 상태값이므로 허용된 'hold'로 수정하며, 뚜렷한 edge가 없으므로 현행을 유지합니다. |
| scale_in_price_guard | insufficient_context | - | state=-, value=-, window=- | accepted=False, effective_state=hold, effective_value=60, runtime_change=False | ai_proposal_missing_for_family |
