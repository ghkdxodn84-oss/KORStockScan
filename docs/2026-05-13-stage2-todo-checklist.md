# 2026-05-13 Stage2 To-Do Checklist

## 오늘 목적

- 전일 postclose 자동화가 만든 장전 apply 후보와 사용자 개입 요구사항을 산출물 기준으로 확인한다.
- 실주문, threshold, provider, sim/probe 관련 변경은 approval artifact와 checklist 기준 없이 열지 않는다.
- code-improvement workorder는 자동 repo 수정이 아니라 사용자가 Codex에 구현을 지시한 경우에만 실행한다.

## 오늘 강제 규칙

- 장중 runtime threshold mutation은 금지한다. 적용은 PREOPEN `threshold_cycle_preopen_apply`가 생성한 runtime env만 source로 본다.
- provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.
- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

### PreopenAutomationHealthCheck20260513 운영 확인 기록

- checked_at: `2026-05-13 08:44 KST`
- 판정: `pass`
- 근거: `threshold_cycle_preopen_cron.log`에 `2026-05-13` preopen `[DONE]` marker가 있고, `threshold_apply_2026-05-13.json` status=`auto_bounded_live_ready`, runtime_change=`true`다. runtime env는 `soft_stop_whipsaw_confirmation`, `score65_74_recovery_probe`만 selected family로 반영했고 bot PID `9785`가 동일 env와 OpenAI Responses WS env를 로드 중이다. `final_ensemble_scanner`는 `2026-05-13T07:29:51` `[DONE]` marker를 남겼고, error detector full dry-run도 pass다.
- warning: 최초 장전 확인 시 `openai_ws_stability_2026-05-12.md` artifact가 없어 `OpenAIWSIntradaySample0513` 장중 표본 재확인을 남겼다. `2026-05-13 08:47 KST`에 동일 모듈로 5/12 artifact를 재생성했고 `decision=keep_ws`, unique WS calls=`582`, fallback=`0`, entry_price WS sample=`0`을 확인했다.
- 다음 액션: 장중 runtime threshold mutation 없이 selected family provenance, OpenAI transport 표본, sim/probe source-quality만 확인한다.

### IntradayAutomationHealthCheck20260513 운영 확인 기록

- checked_at: `2026-05-13 09:37 KST`
- 판정: `warning`
- 근거: `buy_funnel_sentinel`, `holding_exit_sentinel`, `panic_sell_defense`, `buy_pause_guard`, `monitor_snapshot`, `error_detection_full`은 모두 당일 `[DONE]` marker 또는 fresh artifact를 남겼고, `run_error_detection.sh full` 재실행 결과 `summary_severity=pass`다. 단, 장중 리포트 상태는 `buy_funnel_sentinel.primary=UPSTREAM_AI_THRESHOLD`, `holding_exit_sentinel.primary=SELL_EXECUTION_DROUGHT`, `panic_sell_defense.panic_state=PANIC_SELL`로 관찰 경고가 있다.
- 금지 확인: 장중 runtime threshold mutation, provider route 변경, score/stop threshold 변경, 자동매도, bot restart는 수행하지 않았다.
- 다음 액션: 12:05 intraday calibration은 due 전이므로 장중에는 report-only 상태를 유지하고, panic/holding/buy funnel 원인은 장후 attribution과 postclose threshold-cycle source bundle에서 닫는다.
- 정정 (`2026-05-13 09:47 KST`): `holding_exit_sentinel.primary=SELL_EXECUTION_DROUGHT`는 probe-only `exit_signal`의 sparse provenance 오분류였다. 같은 `record_id`의 `swing_probe_*` sibling이 있으면 선행 `exit_signal`도 non-real로 귀속하도록 보정했고, 재생성 결과 `holding_exit_sentinel.primary=NORMAL`, `real_exit_signal=0`, `non_real_exit_signal=9`로 닫혔다. 남는 장중 관찰 경고는 `buy_funnel_sentinel.primary=UPSTREAM_AI_THRESHOLD`와 `panic_sell_defense.panic_state=PANIC_SELL`이다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-05-12` postclose -> `2026-05-13`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [x] `[ThresholdEnvAutoApplyPreopen0513] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-05-13`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-12.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-12.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.
  - 실행 메모 (`2026-05-13 08:11 KST`): 장전 preopen supersede로 `score65_74_recovery_probe`의 panic-adjusted floor 규칙을 추가했다. 5/12 `panic_state=RECOVERY_WATCH`, `panic_detected=true`, score65~74 sample `14/20`, EV `+2.2277%`, close10m `+2.5788%`, submitted drought 조건을 근거로 `panic_adjusted_ready -> adjust_up` 판정했고, `threshold_runtime_env_2026-05-13.env`를 재생성해 `KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED=true`를 복원했다. 기존 07:44 env는 08:11 env로 superseded됐고, bot PID `9785`가 새 env를 로드했다.
  - 판정 (`2026-05-13 08:44 KST`): `applied_guard_passed_env`.
  - 근거: `threshold_apply_2026-05-13.json` status=`auto_bounded_live_ready`, runtime_change=`true`, generated_at=`2026-05-13T08:16:05+09:00`; runtime env는 `KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED=true`, `KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED=true`만 포함한다. bot PID `9785`의 `/proc` env에서도 동일 값과 `KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE=2026-05-13`을 확인했다.
  - 다음 액션: 장중에는 runtime threshold mutation 없이 selected family provenance와 rollback guard만 관찰한다.

- [x] `[OpenAIWSPreopenConfirm0513] OpenAI WS 유지 설정 및 entry_price/analyze_target provenance 확인` (`Due: 2026-05-13`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: RuntimeStability`)
  - Source: [openai_ws_stability_2026-05-12.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-05-12.md), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py)
  - 판정 기준: startup env의 OpenAI route/Responses WS 설정과 `analyze_target`, `entry_price` transport provenance를 분리 확인한다.
  - 금지: provider transport 확인을 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경으로 해석하지 않는다.
  - 다음 액션: entry_price transport 표본이 부족하면 장중 표본 재확인 항목과 연결한다.
  - 판정 (`2026-05-13 08:44 KST`): `warning_source_report_missing_but_runtime_env_pass`.
  - 근거: 최초 확인 시 checklist Source의 `openai_ws_stability_2026-05-12.md`는 실제로 존재하지 않았고 최신 openai_ws stability artifact는 `2026-05-11`까지만 있었다. 원인은 `build_next_stage2_checklist.py`가 source_date OpenAI WS report를 무조건 Source로 참조하지만, `run_threshold_cycle_postclose.sh`에는 해당 report 생성 단계가 없었기 때문이다. `2026-05-13 08:47 KST`에 `src.engine.openai_ws_stability_report --date 2026-05-12`로 재생성했고 `decision=keep_ws`, unique WS calls=`582`, fallback=`0/582`, p95 AI response=`2648.2ms`, entry_price WS sample=`0`을 확인했다. 현재 bot PID `9785` env는 `KORSTOCKSCAN_SCALPING_AI_ROUTE=openai`, `KORSTOCKSCAN_OPENAI_TRANSPORT_MODE=responses_ws`, `KORSTOCKSCAN_OPENAI_RESPONSES_WS_ENABLED=true`, pool_size=`2`, timeout_ms=`15000`, reasoning_effort=`auto`를 로드했고, tmux runtime 로그에 `메인 스캘핑 OpenAI 엔진 고정 완료`가 남았다.
  - 다음 액션: `OpenAIWSIntradaySample0513`에서 `analyze_target`/`entry_price` 실제 transport provenance 표본을 장중 확인한다. 재발 방지를 위해 postclose wrapper가 `openai_ws_stability_report`를 생성하도록 보강했다.

- [x] `[SwingApprovalArtifactPreopen0513] 스윙 approval request 및 별도 승인 artifact 존재 여부 확인` (`Due: 2026-05-13`, `Slot: PREOPEN`, `TimeWindow: 08:45~08:50`, `Track: RuntimeStability`)
  - Source: [swing_runtime_approval_2026-05-12.json](/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-05-12.json), [threshold_cycle_ev_2026-05-12.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-12.json)
  - 판정 기준: approval request가 있더라도 사용자 승인 artifact가 없으면 env apply 대상이 아니다.
  - 금지: 스윙 dry-run 해제, real canary, floor, scale-in real canary를 서로 자동 승인하지 않는다.
  - 다음 액션: `approval_artifact_present`, `approval_artifact_missing`, `blocked_by_policy` 중 하나로 닫는다.
  - 판정 (`2026-05-13 08:44 KST`): `approval_artifact_missing`.
  - 근거: `swing_runtime_approval_2026-05-12.json`은 `swing_model_floor`, `swing_gatekeeper_reject_cooldown` 2건을 `approval_required`로 생성했지만 `threshold_apply_2026-05-13.json`의 `swing_runtime_approval`은 requested=`2`, approved=`0`, blocked=`approval_artifact_missing`, approval_artifact=`null`이다. runtime env에는 스윙 approval env가 추가되지 않았다.
  - 다음 액션: approval artifact 없는 상태에서는 스윙 floor/cooldown/real canary/scale-in real canary를 적용하지 않는다.

## 장중 체크리스트 (09:05~15:20)

- [x] `[RuntimeEnvIntradayObserve0513] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-05-13`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-12.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-12.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, score65_74_recovery_probe가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.
  - 판정 (`2026-05-13 09:37 KST`): `warning_provenance_partial`.
  - 근거: `data/threshold_cycle/threshold_events_2026-05-13.jsonl`에 `score65_74_recovery_probe` 적용 이벤트 1건이 남았고 `threshold_applied_value=enabled=True|score=65-74|budget=50000|qty=1`, `qty_cap=1`, `budget_cap_krw=50000` provenance가 확인된다. 같은 시각 `soft_stop_whipsaw_confirmation` 적용/rollback 표본은 아직 없어 해당 family는 표본 부족으로 남긴다. panic report는 `PANIC_SELL`이지만 runtime mutation은 없었다.
  - 다음 액션: 장후 `ThresholdDailyEVReport0513`에서 selected family별 표본/rollback guard를 real/sim 분리로 재확인한다.

- [x] `[OpenAIWSIntradaySample0513] OpenAI WS/entry_price 장중 표본 및 fallback/fail-closed 재확인` (`Due: 2026-05-13`, `Slot: INTRADAY`, `TimeWindow: 09:20~09:35`, `Track: RuntimeStability`)
  - Source: [openai_ws_stability_2026-05-12.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-05-12.md)
  - 판정 기준: `analyze_target` WS latency/fallback과 `entry_price` transport metadata 누락 여부를 별도 표본으로 확인한다.
  - 금지: entry_price 표본 0건 또는 instrumentation gap을 OpenAI WS runtime 효과 0으로 해석하지 않는다.
  - 다음 액션: 표본 부족이면 postclose provenance 보강 workorder로 분리한다.
  - 판정 (`2026-05-13 09:37 KST`): `warning_entry_price_sample_missing_but_analyze_target_ws_pass`.
  - 근거: `pipeline_events_2026-05-13.jsonl` 기준 OpenAI `analyze_target` 표본 101건은 `openai_transport_mode=responses_ws`, `openai_ws_used=True`, `openai_ws_http_fallback=False`로 확인됐다. 최근 표본의 `openai_ws_roundtrip_ms`는 대략 `873~3586ms` 범위다. `entry_ai_price`/`entry_price` transport 표본은 아직 0건이라 fail-closed/fallback 품질을 장중 표본으로 확정할 수 없다.
  - 다음 액션: postclose `openai_ws_stability_report`에서 entry_price 표본 발생 여부를 다시 확인하고, 계속 0건이면 provenance 보강 workorder가 아니라 표본 부족으로 닫는다.

- [x] `[SimProbeIntradayCoverage0513] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-05-13`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-05-12.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-12.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.
  - 판정 (`2026-05-13 09:37 KST`): `pass_with_panic_warning`.
  - 근거: `panic_sell_defense_2026-05-13.json`의 active sim/probe provenance check는 passed이며 active `swing_probe=10`, `scalp_sim=0`, checked positions `10`, violations `0`이다. pipeline event 집계에서도 `swing_probe_*`, `swing_sim_scale_in_order_assumed_filled`, `swing_reentry_counterfactual_after_loss` 표본은 `actual_order_submitted=False`, `broker_order_forbidden=True`로 분리되어 있다. 다만 같은 report의 `panic_state=PANIC_SELL`, active sim/probe 평균 미실현손익 `-0.0137%`, win rate `40.0%`이므로 EV 판단은 장후 attribution까지 보류한다.
  - 다음 액션: sim/probe EV는 broker execution 품질로 승격하지 않고, 장후 `ThresholdDailyEVReport0513`와 `PanicEntryFreezeGuardWorkorder0513`에서 panic 구간 표본으로 분리한다.
  - 보정 (`2026-05-13 09:47 KST`): `holding_exit_sentinel`이 같은 `record_id`의 `swing_probe_*` sibling provenance를 선행 `exit_signal`에 전파하도록 수정했다. 재생성한 `holding_exit_sentinel_2026-05-13.json`은 `primary=NORMAL`, `real_exit_signal=0`, `non_real_exit_signal=9`, `operator_action_required=false`다.

## 장후 체크리스트 (16:30~18:55)

- [ ] `[ThresholdDailyEVReport0513] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-05-13`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-12.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-12.json)
  - 판정 기준: real/sim/combined split, selected/blocked family, runtime_change, warning을 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[CodeImprovementWorkorderReview0513] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-05-13`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~17:00`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-05-12.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-12.md), [code_improvement_workorder_2026-05-12.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-12.json)
  - 판정 기준: selected_order_count=12와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: 구현 필요, 설계 보류, reject, already_implemented 중 하나로 닫는다.

- [ ] `[PanicEntryFreezeGuardWorkorder0513] panic_entry_freeze_guard 별도 workorder 및 rollback guard 필요 여부 판정` (`Due: 2026-05-13`, `Slot: POSTCLOSE`, `TimeWindow: 17:15~17:30`, `Track: RuntimeStability`)
  - Source: [panic_sell_defense_2026-05-12.json](/home/ubuntu/KORStockScan/data/report/panic_sell_defense/panic_sell_defense_2026-05-12.json), [threshold_cycle_ev_2026-05-12.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-12.json), [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)
  - 판정 기준: 장후 attribution으로 당일 `panic_state`, stop-loss cluster, active sim/probe recovery, post-sell rebound, microstructure detector signal을 확인하고 `panic_entry_freeze_guard`를 별도 workorder로 열지 판정한다.
  - 금지: workorder 없이 score threshold 완화/동결, stop 완화/지연, 자동매도, bot restart, 스윙 실주문 전환을 수행하지 않는다.
  - 다음 액션: `workorder_required`, `hold_report_only`, `reject_no_panic_evidence`, `defer_attribution_gap` 중 하나로 닫는다. `workorder_required`면 적용 범위, cohort tag, rollback guard, allowed_runtime_apply 기본 false, 다음 장전 bounded canary 조건을 함께 명시한다.

- [ ] `[HumanInterventionSummary0513] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-05-13`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-12.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-12.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `승인 artifact 필요`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.
  - 실행 메모 (`2026-05-13 07:57 KST`): `run_error_detection.sh`가 detector `summary_severity=fail`일 때 bot daemon/EventBus 없이도 `notify_error_detection_admin`으로 관리자 Telegram direct notify를 시도하도록 보강했다. 동일 fail signature는 10분 cooldown으로 중복 억제하고, 알림은 report-only이며 runtime threshold/spread/order/restart mutation 권한은 없다.
  - 실행 메모 (`2026-05-13 08:35 KST`): `panic_sell_state_detector`는 `panic_sell_defense_report`의 `microstructure_detector`로 소비되고, `panic_sell_defense`는 threshold-cycle source bundle과 `score65_74_recovery_probe` panic-adjusted floor 입력으로 연결된 것을 확인했다. 장중 cron 산출물 의존만으로는 장후 attribution canonical source가 약해질 수 있어 `run_threshold_cycle_postclose.sh`가 threshold-cycle report 전에 `panic_sell_defense_report`를 재생성하도록 보강했다. 이 단계는 report-only이며 score/stop threshold 변경, 자동매도, bot restart 권한이 없다.

- [ ] `[ShadowCanaryCohortReview0513] shadow/canary/cohort 런타임 분류 및 정리 판정` (`Due: 2026-05-13`, `Slot: POSTCLOSE`, `TimeWindow: 18:40~18:55`, `Track: Plan`)
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
