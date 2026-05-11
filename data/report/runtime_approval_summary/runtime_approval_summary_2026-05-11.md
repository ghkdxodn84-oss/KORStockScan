# Runtime Approval Summary - 2026-05-11

- 목적: 스캘핑 threshold-cycle 판정과 스윙 runtime approval 판정을 한 화면에서 보는 읽기 전용 요약이다.
- runtime_mutation_allowed: `False`
- scalping_items/selected: `12` / `2`
- swing_blocked/requested/approved: `11` / `2` / `0`
- env_generated_at: `2026-05-11T07:54:42`
- first_bot_start_at: `2026-05-11T07:40:04`
- first_bot_start_after_env_at: `2026-05-11T08:34:33`
- pre_env_boot_gap: `True`

## Scalping
| 항목 | 설명 | 현재 적용 | 상태 | 판정 해석 | 점수 | 차단/판정 사유 |
| --- | --- | --- | --- | --- | ---: | --- |
| `soft_stop_whipsaw_confirmation` | soft stop 직후 반등 가능성이 큰 표본은 1회 확인 시간을 두고 성급한 청산을 줄이는 축 | PREOPEN env 적용: 당일 runtime 변경 대상 | `adjust_up` | threshold-cycle guard 통과로 당일 PREOPEN env에 반영됨 | 1 | auto_bounded_live 선택 |
| `holding_flow_ofi_smoothing` | 보유/청산 AI flow 결과에 OFI/QI 미시수급을 붙여 EXIT 확정 또는 보류를 다듬는 축 | 기존 적용 유지: holding_flow_override 내부 OFI/QI postprocessor ON | `hold` | 현재 적용 상태와 값을 유지하고 추가 env 변경은 하지 않는다 | 1 | 유지 |
| `protect_trailing_smoothing` | protect/trailing 청산 후보에서 미시 반등 신호가 있으면 과조기 청산을 줄이는 축 | 관찰/리포트 only: protect/trailing live smoothing 미적용 | `hold_sample` | 축은 유지/관찰하지만 표본 부족으로 runtime 변경은 하지 않는다 | 0.9 | 표본 부족 |
| `trailing_continuation` | trailing 이후 추가 상승 여지가 큰 표본을 계속 보유할 수 있는지 보는 축 | 관찰/리포트 only: trailing 연장 live 미적용 | `freeze` | 계측/DB/safety 문제로 runtime 변경을 금지한다 | 0.9 | 동결 |
| `pre_submit_price_guard` | 주문 제출 직전 quote stale, spread, passive probe 가격품질 문제를 막는 진입 안전축 | 기존 적용/검증 유지: 제출 직전 가격품질 guard 계열 | `freeze` | 계측/DB/safety 문제로 runtime 변경을 금지한다 | 1 | 동결 |
| `score65_74_recovery_probe` | AI 점수 65~74 WAIT 구간 중 수급/가속 조건이 좋은 후보를 1주/소액 canary로 회수하는 축 | PREOPEN env 적용: 당일 runtime 변경 대상 | `adjust_up` | threshold-cycle guard 통과로 당일 PREOPEN env에 반영됨 | 1 | auto_bounded_live 선택 |
| `liquidity_gate_refined_candidate` | 유동성 gate가 막은 후보의 후행 EV를 보고 gate 완화/유지 필요성을 판단하는 축 | 관찰/리포트 only: gate 기준 변경 없음 | `hold` | 현재 적용 상태와 값을 유지하고 추가 env 변경은 하지 않는다 | 1 | 유지 |
| `overbought_gate_refined_candidate` | 과열 gate가 막은 후보의 후행 EV를 보고 과열 차단 기준을 다듬는 축 | 관찰/리포트 only: gate 기준 변경 없음 | `hold` | 현재 적용 상태와 값을 유지하고 추가 env 변경은 하지 않는다 | 1 | 유지 |
| `bad_entry_refined_canary` | 진입 직후 never-green/AI fade 위험이 큰 표본을 조기 정리할 수 있는지 보는 축 | OFF/관찰 only: refined canary live 미적용 | `hold_sample` | 축은 유지/관찰하지만 표본 부족으로 runtime 변경은 하지 않는다 | 1 | 표본 부족 |
| `holding_exit_decision_matrix_advisory` | 보유 중 가능한 행동(EXIT/HOLD/AVG_DOWN/PYRAMID)을 matrix 점수로 보조 판단하는 축 | 관찰/리포트 only: advisory live 적용 아님 | `hold_no_edge` | 명확한 edge가 없어 runtime 변경은 하지 않는다 | 1 | edge 부족 |
| `scale_in_price_guard` | 추가매수 직전 best bid/defensive limit, spread, stale quote로 가격품질을 보장하는 축 | 기존 적용 유지: 추가매수 가격품질 guard ON | `hold` | 현재 적용 상태와 값을 유지하고 추가 env 변경은 하지 않는다 | 1 | 유지 |
| `position_sizing_cap_release` | 신규/추가매수 1주 cap을 풀 수 있는지 EV와 downside 기준으로 보는 축 | 미적용: 1주 cap 유지 | `hold_sample` | 축은 유지/관찰하지만 표본 부족으로 runtime 변경은 하지 않는다 | 1 | 표본 부족 |

## Swing
| 항목 | 설명 | 현재 적용 | 상태 | 판정 해석 | 점수 | 차단/판정 사유 |
| --- | --- | --- | --- | --- | ---: | --- |
| `swing_selection_top_k` | 스윙 추천 후보 수(top-k)를 늘리거나 줄일 수 있는지 보는 선택 폭 축 | 스윙 dry-run/probe 관찰: 실주문 변경 없음 | `freeze` | 계측/DB/safety 문제로 runtime 변경을 금지한다 | 0.8907 | same_stage_owner_conflict:swing_model_floor |
| `swing_gatekeeper_accept_reject` | 스윙 gatekeeper가 accept/reject한 후보의 후행 성과를 비교하는 진입 판단 축 | 스윙 dry-run/probe 관찰: 실주문 변경 없음 | `freeze` | 계측/DB/safety 문제로 runtime 변경을 금지한다 | 0.8907 | runtime guard 없음 |
| `swing_market_regime_sensitivity` | 시장 regime에 따라 스윙 진입 민감도를 완화/강화할지 보는 축 | 스윙 dry-run/probe 관찰: 실주문 변경 없음 | `freeze` | 계측/DB/safety 문제로 runtime 변경을 금지한다 | 0.8907 | same_stage_owner_conflict:swing_gatekeeper_reject_cooldown |
| `swing_pyramid_trigger` | 스윙 보유 후 불타기(PYRAMID) 조건이 유효한지 보는 추가매수 축 | 스윙 dry-run/probe 관찰: 실주문 변경 없음 | `freeze` | 계측/DB/safety 문제로 runtime 변경을 금지한다 | 0.8907 | runtime guard 없음 |
| `swing_avg_down_eligibility` | 스윙 보유 후 물타기(AVG_DOWN) 조건이 유효한지 보는 추가매수 축 | 스윙 dry-run/probe 관찰: 실주문 변경 없음 | `hold_sample` | 축은 유지/관찰하지만 표본 부족으로 runtime 변경은 하지 않는다 | 0.8807 | 표본 부족, runtime guard 없음 |
| `swing_trailing_stop_time_stop` | 스윙 trailing/time stop 청산 조건의 적정성을 보는 exit 축 | 스윙 dry-run/probe 관찰: 실주문 변경 없음 | `hold_sample` | 축은 유지/관찰하지만 표본 부족으로 runtime 변경은 하지 않는다 | 0.8707 | 표본 부족, runtime guard 없음 |
| `swing_holding_flow_defer` | 스윙 보유/청산 AI가 청산 보류를 결정한 뒤 성과가 개선되는지 보는 축 | 스윙 dry-run/probe 관찰: 실주문 변경 없음 | `freeze` | 계측/DB/safety 문제로 runtime 변경을 금지한다 | 0.8907 | runtime guard 없음 |
| `swing_entry_ofi_qi_execution_quality` | 스윙 진입 시 OFI/QI와 주문품질이 실제 성과에 도움이 되는지 보는 축 | 스윙 dry-run/probe 관찰: 실주문 변경 없음 | `hold_sample` | 축은 유지/관찰하지만 표본 부족으로 runtime 변경은 하지 않는다 | 0.8407 | 표본 부족, runtime guard 없음 |
| `swing_scale_in_ofi_qi_confirmation` | 스윙 추가매수 직전 OFI/QI 확인 신호가 유효한지 보는 축 | 스윙 dry-run/probe 관찰: 실주문 변경 없음 | `freeze` | 계측/DB/safety 문제로 runtime 변경을 금지한다 | 0.8907 | runtime guard 없음 |
| `swing_exit_ofi_qi_smoothing` | 스윙 청산 직전 OFI/QI로 EXIT 확정/보류를 다듬을 수 있는지 보는 축 | 스윙 dry-run/probe 관찰: 실주문 변경 없음 | `freeze` | 계측/DB/safety 문제로 runtime 변경을 금지한다 | 0.8907 | runtime guard 없음 |
| `swing_scale_in_real_canary_phase0` | 승인된 실제 스윙 보유분에 한해 PYRAMID/AVG_DOWN 1주 추가매수 canary를 열 수 있는지 보는 정책 축 | 미적용: approval artifact 없이는 실주문 추가매수 금지 | `freeze` | 계측/DB/safety 문제로 runtime 변경을 금지한다 | 없음 | PYRAMID 표본 부족, 추가매수 outcome 누락, 최종 exit 수익률 누락, exit-only 비교 누락, 추가매수 MAE 누락 |
