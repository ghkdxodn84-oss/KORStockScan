# 2026-05-15 Stage2 To-Do Checklist

## 오늘 목적

- 전일 postclose 자동화가 만든 장전 apply 후보와 사용자 개입 요구사항을 산출물 기준으로 확인한다.
- 실주문, threshold, provider, sim/probe 관련 변경은 approval artifact와 checklist 기준 없이 열지 않는다.
- 실주문 예수금/1주 cap/selected family 여부와 무관하게 스캘핑·스윙의 BUY/선정 가능 후보는 sim/probe 전주기 관찰 대상으로 최대한 남기고, 병목 해소·손실 축소 후보를 분리해 threshold-cycle 입력으로 보낸다.
- code-improvement workorder는 자동 repo 수정이 아니라 사용자가 Codex에 구현을 지시한 경우에만 실행한다.

## 오늘 강제 규칙

- 장중 runtime threshold mutation은 금지한다. 적용은 PREOPEN `threshold_cycle_preopen_apply`가 생성한 runtime env만 source로 본다.
- provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.
- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality와 threshold 개선 입력이며, 실주문 전환·broker execution 품질 근거가 아니다.
- 실계좌 주문가능금액, real order guard, approval artifact 부재는 sim/probe 후보 생성 제외 사유가 아니다. 단, provenance는 real/sim/combined를 분리한다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-05-14` postclose -> `2026-05-15`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [ ] `[ThresholdEnvAutoApplyPreopen0515] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-05-15`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-14.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

- [ ] `[OpenAIWSPreopenConfirm0515] OpenAI WS 유지 설정 및 entry_price/analyze_target provenance 확인` (`Due: 2026-05-15`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: RuntimeStability`)
  - Source: [openai_ws_stability_2026-05-14.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-05-14.md), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py)
  - 판정 기준: startup env의 OpenAI route/Responses WS 설정과 `analyze_target`, `entry_price` transport provenance를 분리 확인한다.
  - 금지: provider transport 확인을 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경으로 해석하지 않는다.
  - 다음 액션: entry_price transport 표본이 부족하면 장중 표본 재확인 항목과 연결한다.

- [ ] `[SwingApprovalArtifactPreopen0515] 스윙 approval request 및 별도 승인 artifact 존재 여부 확인` (`Due: 2026-05-15`, `Slot: PREOPEN`, `TimeWindow: 08:45~08:50`, `Track: RuntimeStability`)
  - Source: [swing_runtime_approval_2026-05-14.json](/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-05-14.json), [threshold_cycle_ev_2026-05-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-14.json)
  - 판정 기준: approval request가 있더라도 사용자 승인 artifact가 없으면 env apply 대상이 아니다.
  - 금지: 스윙 dry-run 해제, real canary, floor, scale-in real canary를 서로 자동 승인하지 않는다.
  - 다음 액션: `approval_artifact_present`, `approval_artifact_missing`, `blocked_by_policy` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0515] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-05-15`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-14.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[OpenAIWSIntradaySample0515] OpenAI WS/entry_price 장중 표본 및 fallback/fail-closed 재확인` (`Due: 2026-05-15`, `Slot: INTRADAY`, `TimeWindow: 09:20~09:35`, `Track: RuntimeStability`)
  - Source: [openai_ws_stability_2026-05-14.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-05-14.md)
  - 판정 기준: `analyze_target` WS latency/fallback과 `entry_price` transport metadata 누락 여부를 별도 표본으로 확인한다.
  - 금지: entry_price 표본 0건 또는 instrumentation gap을 OpenAI WS runtime 효과 0으로 해석하지 않는다.
  - 다음 액션: 표본 부족이면 postclose provenance 보강 workorder로 분리한다.

- [ ] `[SimProbeIntradayCoverage0515] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-05-15`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-05-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-14.json)
  - 판정 기준: 스캘핑·스윙 모두에서 BUY/선정 가능 후보가 실주문 예수금/real cap/approval 부재와 무관하게 sim/probe 후보로 남고, `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count, entry/holding/scale-in/exit arm 누락 여부를 같이 기록한다.

## 장후 체크리스트 (16:30~18:55)

- [ ] `[SimFirstLifecycleCoverageAudit0515] 스캘핑/스윙 적극 sim-first 전주기 실행 및 consumer 연결 확인` (`Due: 2026-05-15`, `Slot: POSTCLOSE`, `TimeWindow: 16:20~16:30`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-14.json), [swing_lifecycle_audit_2026-05-14.json](/home/ubuntu/KORStockScan/data/report/swing_lifecycle_audit/swing_lifecycle_audit_2026-05-14.json), [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)
  - 판정 기준: 스캘핑 `scalp_ai_buy_all`/missed probe와 스윙 dry-run/probe가 entry->holding->scale-in->exit 관찰축을 생성하고, daily EV/threshold cycle/code-improvement workorder/runtime approval summary consumer에 누락 없이 들어갔는지 확인한다.
  - 금지: closed sample 부족, real order 불가, approval artifact 부재를 sim/probe 후보 생성 중단 사유로 쓰지 않는다. sim/probe 결과를 실주문 품질로 섞지도 않는다.
  - 다음 액션: `coverage_ok`, `consumer_gap`, `lifecycle_arm_gap`, `source_quality_blocker`, `sample_floor_gap` 중 하나 이상으로 닫고 gap은 workorder 후보로 연결한다.

- [ ] `[WindowPolicyRegistryConsistency0515] threshold family window_policy 레지스트리와 daily/rolling/cumulative consumer 일관성 확인` (`Due: 2026-05-15`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:40`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_2026-05-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_2026-05-14.json), [threshold_cycle_cumulative_2026-05-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_cumulative/threshold_cycle_cumulative_2026-05-14.json), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py), [threshold_cycle_README.md](/home/ubuntu/KORStockScan/data/threshold_cycle/README.md)
  - 판정 기준: 각 family의 `window_policy.primary/secondary/daily_only_allowed`가 calibration candidate, `calibration_source_bundle_by_window`, AI correction input, preopen apply, EV summary, cumulative markdown sample denominator에 동일하게 반영됐는지 확인한다.
  - 금지: daily trigger 표본을 rolling/cumulative primary 표본처럼 표시하거나, registry와 다른 window 기준으로 threshold/code-improvement 결론을 내리지 않는다.
  - 다음 액션: `registry_consistent`, `daily_only_leak`, `rolling_consumer_gap`, `sample_denominator_mismatch`, `report_rendering_gap` 중 하나 이상으로 닫고 gap은 code-improvement workorder 후보로 연결한다.

- [ ] `[ThresholdDailyEVReport0515] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-05-15`, `Slot: POSTCLOSE`, `TimeWindow: 16:40~16:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-14.json)
  - 판정 기준: real/sim/combined split, selected/blocked family, runtime_change, warning을 분리하고 sim 결과가 threshold 개선 후보 또는 workorder 후보로 소비됐는지 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[CodeImprovementWorkorderReview0515] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-05-15`, `Slot: POSTCLOSE`, `TimeWindow: 16:55~17:10`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-05-14.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-14.md), [code_improvement_workorder_2026-05-14.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-14.json)
  - 판정 기준: selected_order_count=12와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, sim-first 전주기 실행/consumer 연결을 막는 성능·계측·source-quality 병목이 우선순위에 반영됐는지 확인한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: 구현 필요, 설계 보류, reject, already_implemented 중 하나로 닫는다.

- [ ] `[HumanInterventionSummary0515] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-05-15`, `Slot: POSTCLOSE`, `TimeWindow: 17:10~17:25`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-14.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `승인 artifact 필요`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[ShadowCanaryCohortReview0515] shadow/canary/cohort 런타임 분류 및 정리 판정` (`Due: 2026-05-15`, `Slot: POSTCLOSE`, `TimeWindow: 18:40~18:55`, `Track: Plan`)
  - Source: [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: 당일 변경/관찰 결과를 기준으로 `remove`, `observe-only`, `baseline-promote`, `active-canary` 상태 변동 여부를 닫는다.
  - 금지: shadow 금지, canary-only, baseline 승격 원칙을 코드/문서 상태와 분리하지 않는다.
  - 다음 액션: 변경이 있으면 기준문서와 checklist를 함께 갱신하고 cohort 잠금 필드를 남긴다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->


## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
