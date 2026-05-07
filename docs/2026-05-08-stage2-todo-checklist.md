# 2026-05-08 Stage2 To-Do Checklist

## 오늘 목적

- `statistical_action_weight` 2차 고급축 중 `SAW-4~SAW-6`의 적재 가능성과 리포트 확장 순서를 판정한다.
- 체결품질, 시장/종목 맥락, orderbook absorption 축을 행동가중치에 넣을 수 있는지 sample/readiness 기준으로 분리한다.
- OFI/QI가 P2 내부 live 입력 feature로 반영된 뒤 stale 되지 않도록 prompt/report/calibration 확장 ladder와 owner를 확정한다.

## 오늘 강제 규칙

- 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이며 상세 기준은 `Plan Rebase` §1~§6을 따른다.
- `statistical_action_weight`는 report-only/decision-support 축이며 직접 runtime threshold나 주문 행동을 바꾸지 않는다.
- 체결품질 분석은 full/partial fill을 합치지 않는다.
- orderbook/microstructure 필드가 누락되면 추정값으로 손익 결론을 만들지 않는다.
- OFI/QI는 판단축이 아니라 입력데이터 품질개선축으로 관리한다. 현재 live 배선은 `entry-only` P2 내부 feature로 유지하되, `watching/holding/exit`에는 report-only context enrichment 설계 없이 live gate로 바로 연결하지 않는다.

## 장전 체크리스트 (08:50~09:00)

- 없음

## 장중 체크리스트 (09:00~15:20)

- 없음

## 장후 체크리스트 (16:00~18:35)

- [ ] `[EntryFunnelRecoveryDecision0508] submitted/full/partial funnel 회복과 score65_74 probe 다음 enable 조건 잠금` (`Due: 2026-05-08`, `Slot: POSTCLOSE`, `TimeWindow: 18:35~18:55`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md), [sniper_missed_entry_counterfactual.py](/home/ubuntu/KORStockScan/src/engine/sniper_missed_entry_counterfactual.py), [2026-05-06-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-05-06-stage2-todo-checklist.md), [2026-05-07-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-05-07-stage2-todo-checklist.md)
  - 판정 기준: `BUY Funnel Sentinel`의 `UPSTREAM_AI_THRESHOLD/LATENCY_DROUGHT/PRICE_GUARD_DROUGHT`와 `missed_entry_counterfactual`, `submitted/full/partial/COMPLETED + valid profit_rate`를 한 owner에서 같이 본다. `score65_74 recovery probe`는 단독 MISSED_WINNER가 아니라 `submitted 회복`, `full/partial 체결 품질`, `soft_stop tail`까지 닫혀야 다음 장전 enable 후보가 된다.
  - 범위: broad score threshold 완화, fallback 재개, spread cap 재완화는 금지한다. 이번 owner는 `baseline vs blocked_ai_score65_74 vs would-have-submitted/filled`를 분리하는 report-only 판정이다.
  - 다음 액션: `enable`, `hold`, `drop` 중 하나로 닫고, enable이면 다음 장전 단일 canary load item을 새로 만든다. hold/drop이면 owner를 종료하거나 다른 병목축으로 전환한다.

- [ ] `[StatActionAdvancedContext0508] SAW-4~SAW-6 체결품질/시장맥락/orderbook 축 적재 가능성 판정` (`Due: 2026-05-08`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:45`, `Track: ScalpingLogic`)
  - Source: [2026-04-30-data-driven-threshold-inventory.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-30-data-driven-threshold-inventory.md), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py), [sniper_execution_receipts.py](/home/ubuntu/KORStockScan/src/engine/sniper_execution_receipts.py)
  - 판정 기준: `SAW-4` full/partial/slippage/adverse fill, `SAW-5` market_regime/volatility/marcap/sector/VI freshness, `SAW-6` orderbook absorption/large sell print/micro VWAP 이탈을 action weight report에 넣을 수 있는지 확인한다. 각 축별 필드 존재율, join key, sample floor, compact stream 포함 여부, report-only 유지 조건을 표로 잠근다.
  - why: 1차 가격/거래량/시간대 축만으로는 행동 선택의 기대값 차이를 충분히 설명하지 못한다. 다만 체결품질과 orderbook 축은 필드 누락 시 왜곡 위험이 크므로 적재 가능성부터 닫아야 한다.
  - 다음 액션: readiness가 높은 축 1개만 다음 구현 항목으로 승격하고, 나머지는 누락 필드 보강 항목으로 분리한다.

- [ ] `[OFIQExpansionLadder0508] OFI/QI P2 내부 feature 확대적용 ladder 및 stale 방지 owner 확정` (`Due: 2026-05-08`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~17:15`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [2026-05-03-ofi-audit-response-result-report.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-05-03-ofi-audit-response-result-report.md), [README.md](/home/ubuntu/KORStockScan/data/report/README.md), [orderbook_stability_observer.py](/home/ubuntu/KORStockScan/src/trading/entry/orderbook_stability_observer.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [sniper_performance_tuning_report.py](/home/ubuntu/KORStockScan/src/engine/sniper_performance_tuning_report.py)
  - 판정 기준: OFI/QI 후속을 `P2 prompt contract 명문화`, `performance_tuning Markdown OFI/QI 섹션`, `bucket calibration ON 기준`, `symbol anomaly watch`, `prompt drift/stale guard` 5단계 ladder로 잠근다. 각 단계별 owner, 금지 범위, 필요한 로그 필드, sample floor, rollback owner를 표로 남긴다. 별도로 `holding/exit context enrichment`는 live 판단 변경이 아니라 입력 품질 보강 후보로 분리해 필요한 필드와 attribution owner만 정의한다.
  - prompt 기준: `entry_price_v1` prompt에서 OFI/QI의 사용 범위를 `submitted 직전 주문가/USE_DEFENSIVE/IMPROVE_LIMIT/SKIP 판단 보조`로 명시하고, `neutral/insufficient`이면 OFI/QI 단독 SKIP 금지를 유지한다. prompt 문자열 개선은 AIEngineFlagOffBacklog와 충돌하지 않도록 P2 entry_price contract 전용 workorder로만 연다.
  - report 기준: `performance_tuning_YYYY-MM-DD.md` 구현 후보에 OFI/QI 섹션을 포함한다. 최소 필드는 `ofi_orderbook_micro_states`, `ofi_orderbook_micro_threshold_sources`, `ofi_orderbook_micro_buckets`, `ofi_orderbook_micro_warnings`, `symbol_anomalies`, `entry_ai_price_skip_policy_warning/basis`다.
  - holding/exit 입력 품질 기준: 매도/보유 쪽 OFI/QI는 `exit_context.orderbook_micro`, `snapshot_age_ms`, `micro_state`, `ofi/qi threshold source`, `post_exit_mfe/mae`, `exit_rule` join이 report-only로 닫히기 전에는 live exit gate로 쓰지 않는다. 이 단계는 새 매도 canary가 아니라 입력 context 품질 보강이며, 이후 성과 귀속이 확인될 때만 별도 guarded canary 여부를 판단한다.
  - 민감도 기준: `bearish_supported SKIP`과 `neutral/insufficient warning SKIP`을 별도 cohort로 분리한다. `skip_without_bearish_ofi`가 반복되면 OFI/QI threshold 완화가 아니라 `SKIP -> USE_DEFENSIVE/P1 fallback` demotion guard 후보로 보고, missed upside와 adverse fill 회피 효과를 같이 비교한다.
  - 5/4 근거: [2026-05-04 checklist](./2026-05-04-stage2-todo-checklist.md) `OrderbookMicroP2Canary0504-Postclose` 기준 P2 stage 111건 중 `USE_DEFENSIVE=96`, `SKIP=8`, micro state는 `neutral=99`, `bearish=7`, `insufficient=3`이다. SKIP 8건 중 `ofi_bearish_supported=6`, `neutral=2`, `skip_without_bearish_ofi=4` warning이 있어 neutral/insufficient demotion guard 검토 근거가 있다.
  - calibration 기준: `SCALPING_ENTRY_PRICE_ORDERBOOK_MICRO_BUCKET_CALIBRATION_ENABLED`는 기본 OFF다. ON 후보는 `ThresholdOpsTransition0506` 이후에도 별도 workorder, manifest id/version, sample floor, fallback 급증 guard, restart 절차가 닫혀야 한다.
  - stale 방지: 2영업일 연속 OFI/QI 로그 표본이 0이거나, `snapshot_age_ms`/observer health/fallback reason이 report에 누락되거나, SKIP warning 분포가 Markdown에 나타나지 않으면 `stale_context`로 보고 다음 checklist에 보강 작업을 자동 생성한다.
  - 다음 액션: ladder가 잠기면 `performance_tuning Markdown 구현`, `entry_price_v1 prompt contract 보강`, `bucket calibration ON/OFF workorder` 중 readiness가 높은 1개만 다음 단일 작업항목으로 분리한다.

- [x] `[Phase3Quality0508] counterfactual realism 3-mode 및 exit decision authority provenance 채택 여부 판정` (`Due: 2026-05-08`, `Slot: POSTCLOSE`, `TimeWindow: 17:15~17:35`, `Track: ScalpingLogic`) (`실행: 2026-05-07 16:57 KST`)
  - Source: [2026-04-10-scalping-ai-coding-instructions.md](/home/ubuntu/KORStockScan/docs/2026-04-10-scalping-ai-coding-instructions.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [sniper_missed_entry_counterfactual.py](/home/ubuntu/KORStockScan/src/engine/sniper_missed_entry_counterfactual.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [sniper_trade_review_report.py](/home/ubuntu/KORStockScan/src/engine/sniper_trade_review_report.py)
  - 판정 기준: `Phase 3-1`은 현재 `missed_entry_counterfactual` 관찰축과 `counterfactual 손익 미합산` 원칙으로 부분 채택됐는지, 그리고 `optimistic/realistic/conservative` 3모드가 실제 구현됐는지 분리 판정한다. `Phase 3-2`는 `exit_decision_source` 필드와 `PRESET_HARD_STOP/PRESET_PROTECT/AI_REVIEW_EXIT/SOFT_STOP/TIMEOUT/MANUAL` authority taxonomy가 runtime log/report/test에 존재하는지 확인한다.
  - why: 초기 튜닝 문서의 `분석 품질 고도화`는 현재 Rebase에 원칙 단위로만 흡수돼 있고, 구현 단위로는 `partial adopted`와 `missing`이 섞여 있다. 이 상태를 그대로 두면 `counterfactual realism`과 `청산 authority provenance`가 다시 stale 된다.
  - 판정: `Phase 3-1`은 `partial adopted`다. `missed_entry_counterfactual` 관찰축과 `counterfactual 손익 미합산` 원칙은 반영됐지만 `optimistic/realistic/conservative` 3모드는 실제 구현되지 않았다. `sniper_missed_entry_counterfactual.py`는 단일 `metrics_5m/metrics_10m/outcome` 체계만 가진다.
  - 판정: `Phase 3-2`는 `missing`이다. `exit_decision_source` 문자열은 runtime/report/test 경로에 없고, 현재는 `exit_rule/reason/sell_reason_type/stage`가 암묵 provenance 역할만 한다. `PRESET_HARD_STOP/PRESET_PROTECT/AI_REVIEW_EXIT/SOFT_STOP/TIMEOUT/MANUAL` taxonomy를 잠근 단일 field가 없다.
  - 근거: repo grep 기준 `exit_decision_source`는 설계 문서에만 있고 코드에는 없다. 반면 `missed_entry_counterfactual`는 이미 monitor snapshot/report owner가 있으며 `counterfactual != realized PnL` 원칙도 Rebase에 반영돼 있다. 따라서 readiness가 더 높은 다음 단일 구현 owner는 `exit_decision_source provenance`다.
  - 다음 액션: `exit_decision_source provenance`를 다음 단일 구현 owner로 승격하고, `3-mode counterfactual`는 `report-only/설계 only`로 잠근다.

- [x] `[ExitDecisionSourceProvenance0508] exit_decision_source taxonomy runtime/report/test 반영` (`Due: 2026-05-08`, `Slot: POSTCLOSE`, `TimeWindow: 18:55~19:20`, `Track: ScalpingLogic`) (`실행: 2026-05-07 17:12 KST`)
  - Source: [2026-04-10-scalping-ai-coding-instructions.md](/home/ubuntu/KORStockScan/docs/2026-04-10-scalping-ai-coding-instructions.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [sniper_trade_review_report.py](/home/ubuntu/KORStockScan/src/engine/sniper_trade_review_report.py)
  - 판정 기준: `PRESET_HARD_STOP`, `PRESET_PROTECT`, `AI_REVIEW_EXIT`, `SOFT_STOP`, `TRAILING`, `TIMEOUT`, `MANUAL`, `OVERNIGHT_FLOW`, `HOLDING_FLOW_OVERRIDE` 중 하나로 귀속되는 `exit_decision_source` field를 runtime log/report/test에 추가한다. `exit_rule`와 별도 field로 남기고 realized PnL 집계 기준을 바꾸지 않는다.
  - 금지선: 새 taxonomy를 근거로 live 청산 우선순위를 바꾸지 않는다. matrix advisory flag, soft stop rule, holding_flow_override action 자체를 이 항목에서 바꾸지 않는다.
  - 실행 메모 (`2026-05-07 KST`): `sniper_state_handlers.py`에 `exit_decision_source` resolver를 추가해 `exit_signal`, `sell_order_sent`, `sell_order_failed`, `sell_order_blocked_market_closed`에 authority taxonomy를 기록했다. `sniper_execution_receipts.py`는 `sell_completed`까지 같은 field를 넘기고, `sniper_trade_review_report.py`는 필드가 있으면 그대로 표기하고 과거 로그는 `exit_rule/reason`으로 fallback 추정한다. `sniper_post_sell_feedback.py` candidate payload에도 동일 provenance를 포함했다.
  - 판정: runtime/report/test provenance는 닫혔다. `PRESET_HARD_STOP/PRESET_PROTECT/AI_REVIEW_EXIT/SOFT_STOP/TRAILING/TIMEOUT/OVERNIGHT_FLOW/HOLDING_FLOW_OVERRIDE/MANUAL` taxonomy가 공통 field로 고정됐다.
  - 검증: `pytest src/tests/test_sniper_scale_in.py src/tests/test_holding_flow_override.py src/tests/test_trade_review_report_revival.py src/tests/test_post_sell_feedback.py -q` 통과 (`157 passed`). `py_compile` 통과.
  - 다음 액션: provenance가 닫혔으므로 이후 `ADM advisory enable`, `winner wide-window`, `bad-entry refined` 해석은 같은 authority field를 공통 근거로 사용한다.

- [x] `[SAW3EligibleOutcomeImplementation0508] eligible-but-not-chosen 후행 MFE/MAE report-only 구현` (`Due: 2026-05-08`, `Slot: POSTCLOSE`, `TimeWindow: 17:35~17:50`, `Track: ScalpingLogic`)
  - Source: [2026-05-07-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-05-07-stage2-todo-checklist.md), [postclose_decision_support_followup_2026-05-07.md](/home/ubuntu/KORStockScan/data/report/postclose_decision_support_followup_2026-05-07.md), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)
  - 판정 기준: `stat_action_decision_snapshot`의 `chosen_action/eligible_actions/rejected_actions/record_id/emitted_at`를 후행 quote 또는 position outcome과 join해 `eligible_but_not_chosen`별 `post_decision_mfe`, `post_decision_mae`, `missed_upside`, `avoided_loss`를 계산하는 report-only 섹션을 구현한다. compact partition read cap, horizon, 중복 snapshot downsample, selection-bias caveat를 같이 잠근다.
  - 금지선: 선택하지 않은 action의 counterfactual을 realized PnL과 합산하지 않는다. live 주문/청산 threshold나 AI 응답을 직접 바꾸지 않는다.
  - 선반영: 2026-05-07 장후 `statistical_action_weight` Markdown/JSON에 `eligible_but_not_chosen` 섹션을 추가했다. 5/8에는 true 후행 quote join과 snapshot 중복 downsample 품질 보강만 별도 필요 시 분리한다.

- [x] `[ADMReportOnlyContract0508] holding_exit_decision_matrix report-only 계약 및 ADM-2 불허선 정리` (`Due: 2026-05-08`, `Slot: POSTCLOSE`, `TimeWindow: 17:50~18:05`, `Track: AIPrompt`)
  - Source: [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md), [2026-05-07-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-05-07-stage2-todo-checklist.md), [holding_exit_decision_matrix_2026-05-07.json](/home/ubuntu/KORStockScan/data/report/holding_exit_decision_matrix/holding_exit_decision_matrix_2026-05-07.json), [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py), [ai_engine_deepseek.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_deepseek.py)
  - 판정 기준: 5/7 판정에 따라 ADM-2 runtime shadow prompt 주입은 불허하고, ADM-1 report-only matrix의 `matrix_version`, `prompt_hint`, `hard_veto`, provenance, offline operator review 계약만 정리한다. `prompt_profile=exit`는 holding route alias로 유지하되 matrix context를 runtime prompt/cache key에 넣지 않는다.
  - 금지선: ADM-2 shadow, ADM-3 advisory nudge, ADM-4 weighted live, ADM-5 policy gate는 별도 사용자 승인 전까지 OFF다. live AI 응답을 채택하지 않는다.
  - 선반영: 2026-05-07 장후 Plan Rebase/checklist/follow-up에 ADM-1 report-only 허용선과 ADM-2 불허선을 정리했다. 필요한 경우 matrix prompt_hint/token budget 축소만 별도 작업으로 분리한다.

- [x] `[ADMCanaryLivePivot0508] holding_exit_decision_matrix live canary pivot readiness 판정` (`Due: 2026-05-08`, `Slot: POSTCLOSE`, `TimeWindow: 18:35~18:55`, `Track: AIPrompt`) (`실행: 2026-05-07 16:50 KST`)
  - Source: [2026-05-07-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-05-07-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [holding_exit_decision_matrix_2026-05-07.json](/home/ubuntu/KORStockScan/data/report/holding_exit_decision_matrix/holding_exit_decision_matrix_2026-05-07.json), [holding_exit_matrix_runtime.py](/home/ubuntu/KORStockScan/src/engine/holding_exit_matrix_runtime.py), [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py), [ai_engine_deepseek.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_deepseek.py), [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py)
  - 판정 기준: `AIDecisionMatrixShadow0507`의 shadow naming을 폐기하고, 실제 다음 축을 `single-owner advisory/live canary`로 전환할지 판정한다. 최소 조건은 runtime matrix loader, feature flag, cache key 분리, matrix provenance logging, provider parity 범위 고정, rollback owner, baseline/candidate/excluded cohort 정의다.
  - 추가 기준: current matrix entry가 대부분 `no_clear_edge`이면 plumbing 구현과 live enable 판정을 분리한다. loader/flag/logging 구현이 완료되어도 `COMPLETED + valid profit_rate`, `GOOD_EXIT/MISSED_UPSIDE`, soft stop tail, holding defer cost 기준이 닫히지 않으면 live enable은 불허한다.
  - 금지선: matrix를 score override나 hard veto bypass 용도로 쓰지 않는다. holding/exit same-stage 다축 live 변경, self-updating matrix, bot restart 자동 연동은 금지한다.
  - 실행 메모 (`2026-05-07 KST`): `holding_exit_matrix_runtime.py`를 추가해 holding prompt/exit alias 전용 runtime loader를 구현했다. `ai_engine.py`, `ai_engine_openai.py`, `ai_engine_deepseek.py`는 `prompt_profile=holding|exit` 경로에서만 matrix provenance를 로드하고, `HOLDING_EXIT_MATRIX_ADVISORY_ENABLED` flag가 켜질 때만 prompt context를 붙인다. cache key는 `:adm:{cohort}:{matrix_version}:{price_bucket}:{volume_bucket}:{time_bucket}` suffix로 분리했고, result/log에는 `holding_exit_matrix_status/cohort/version/source_date/buckets/decision_alignment`를 남긴다.
  - 판정: readiness plumbing 구현은 완료다. baseline/candidate/excluded cohort도 정의했다. baseline은 `holding prompt` + flag OFF, candidate는 `holding prompt` + advisory flag ON, excluded는 non-holding/shared prompt 및 현 owner 범위 밖 surface다. 다만 5/7 matrix는 `recommended_bias=no_clear_edge` 비중이 높고 `holding_flow_override`는 현 owner 유지가 우선이라 same-day advisory/live enable은 보류한다.
  - 근거: `holding_exit_decision_matrix_2026-05-07.json`은 14개 entry 대부분이 `no_clear_edge`이며 `defensive_only_high_loss_rate`/`candidate_weight_source`가 다수다. 따라서 plumbing은 닫혀도 runtime AI 응답 변경까지 바로 올릴 edge가 아니다. provider parity는 관련 pytest가 통과했고 flag 기본값은 OFF다.
  - 다음 액션: next matrix에서 directional edge가 생기기 전까지 `HOLDING_EXIT_MATRIX_ADVISORY_ENABLED=False`를 유지한다. live enable 재판정은 다음 장후 matrix와 `GOOD_EXIT/MISSED_UPSIDE/holding defer cost`가 닫힐 때만 별도 checklist로 연다.

- [x] `[PrecloseSellTargetAIRecovery0508] preclose sell target AI/Telegram acceptance 재검증` (`Due: 2026-05-08`, `Slot: POSTCLOSE`, `TimeWindow: 18:05~18:20`, `Track: Plan`)
  - Source: [preclose-sell-target-revival-plan.md](/home/ubuntu/KORStockScan/docs/preclose-sell-target-revival-plan.md), [2026-05-07-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-05-07-stage2-todo-checklist.md), [preclose_sell_target_report.py](/home/ubuntu/KORStockScan/src/scanners/preclose_sell_target_report.py)
  - 판정 기준: 5/7 Gemini 503 `UNAVAILABLE` 후 별도 승인 시 AI 호출, 응답 JSON contract, schema parse, Telegram publish 대상을 각각 분리 검증한다. dry-run과 `--no-telegram`으로 실제 전송을 먼저 차단한다.
  - 금지선: AI/Telegram acceptance는 자동 주문, threshold mutation, bot restart와 연결하지 않는다.
  - 선반영: 2026-05-07 장후 Gemini key fallback을 구현했고 key2로 AI JSON schema parse와 report-only artifact 생성이 통과했다. 같은 날 사용자 승인으로 Telegram 실제 전송도 실행했다.

- [x] `[PrecloseSellTargetCronWrapper0508] preclose sell target cron wrapper lock/status/holiday skip 판정` (`Due: 2026-05-08`, `Slot: POSTCLOSE`, `TimeWindow: 18:20~18:35`, `Track: RuntimeStability`)
  - Source: [data/report/README.md](/home/ubuntu/KORStockScan/data/report/README.md), [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md), [run_preclose_sell_target_report.sh](/home/ubuntu/KORStockScan/deploy/run_preclose_sell_target_report.sh)
  - 판정 기준: cron 등록이 아니라 wrapper에 lock, status manifest, log path, failure alert, holiday skip, retry/cooldown이 필요한지 확인한다. report-only profile은 `--no-ai --no-telegram`을 기본으로 본다.
  - 금지선: cron 등록은 산출물 생성 정기화일 뿐 live threshold mutation, bot restart, 자동 주문 제출이 아니다.
  - 선반영: 2026-05-07 장후 wrapper에 lock/status manifest/log path/venv guard/weekend guard를 추가했고, 같은 날 사용자 승인으로 `15:00` cron 등록까지 반영했다. 다만 consumer 연결은 별도 owner 전까지 열지 않는다.
