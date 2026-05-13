# 2026-05-14 Stage2 To-Do Checklist

## 오늘 목적

- 전일 postclose 자동화가 만든 장전 apply 후보와 사용자 개입 요구사항을 산출물 기준으로 확인한다.
- 실주문, threshold, provider, sim/probe 관련 변경은 approval artifact와 checklist 기준 없이 열지 않는다.
- code-improvement workorder는 자동 repo 수정이 아니라 사용자가 Codex에 구현을 지시한 경우에만 실행한다.

## 오늘 강제 규칙

- 장중 runtime threshold mutation은 금지한다. 적용은 PREOPEN `threshold_cycle_preopen_apply`가 생성한 runtime env만 source로 본다.
- provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.
- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

### PreopenAutomationHealthCheck20260514 운영 확인 기록

- checked_at: `2026-05-14 07:54 KST`
- 판정: `warning`
- 근거: `threshold_cycle_preopen_cron.log`에 `2026-05-14` preopen `[DONE]` marker가 있고, `threshold_apply_2026-05-14.json` status=`auto_bounded_live_ready`, apply_mode=`auto_bounded_live`, runtime_change=`true`다. runtime env는 `threshold_runtime_env_2026-05-14.env/json`으로 생성됐고 selected family는 `soft_stop_whipsaw_confirmation`, env override는 `KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED=true`다. `tmux bot` 세션은 `2026-05-14 07:40 KST`에 기동됐고 `bot_history.log`에는 main route=`openai`가 남아 있다.
- warning: `run_error_detection` 최신 full 결과는 process/cron/log/resource/stale-lock이 pass지만, `artifact_freshness`가 `daily_recommendations_v2.csv`와 diagnostics stale warning을 남겼다. `final_ensemble_scanner target_date=2026-05-14` 자체는 `[DONE]` marker와 추천 3건 적재 로그를 남겼으므로 운영 관찰 warning으로 분리한다.
- warning 해소 메모 (`2026-05-14 08:00 KST`): 최신 `error_detection_2026-05-14.json`은 summary_severity=`pass`, artifact_freshness=`pass`로 전환됐다. detector는 `daily_recommendations_*`를 `07:20~08:00` window, max_staleness_sec=`3600`으로 보는데, 파일 mtime이 `2026-05-13 21:26:02 KST`라 window 안에서는 stale warning이었다가 window 종료 후 `pass_after_window`로 닫혔다. 스캐너 로그에는 `final_ensemble_scanner target_date=2026-05-14` `[DONE]`과 `V2 CSV에서 3개 종목 우선 적재 완료`가 있어 preopen chain 실패는 아니다.
- detector 보정 메모 (`2026-05-14 08:04 KST`): `artifact_freshness`에 `daily_recommendations_v2.csv` 내부 `date`와 diagnostics 내부 `latest_date`/`selected_count` 검증을 추가했다. 보정 후 dry-run은 `daily_recommendations_csv_status=pass_content_date`, `daily_recommendations_diag_status=pass_content_date`, summary_severity=`pass`로 닫힌다. 이 보정은 운영 detector 판정만 바꾸며 threshold/provider/order guard는 변경하지 않는다.
- swing approval: `swing_runtime_approval_2026-05-13.json`은 `runtime_change=false`, approval request `0`이며 one-share real canary와 scale-in real canary는 모두 `approval_required`/`runtime_apply_allowed=false`다. `data/threshold_cycle/approvals` 아래 별도 approval artifact는 없다.
- 금지 확인: 확인 과정에서 threshold/provider/order guard, 스윙 dry-run guard, bot restart, broker 주문 상태를 변경하지 않았다.
- 다음 액션: 장중 runtime threshold mutation 없이 selected family provenance와 OpenAI `entry_price` 표본 부족을 기존 장중/장후 attribution에서 분리 확인한다. Project/Calendar 동기화는 표준 명령으로 사용자가 수행한다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-05-13` postclose -> `2026-05-14`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [x] `[ThresholdEnvAutoApplyPreopen0514] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-05-14`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-13.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-13.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.
  - 완료 판정: `applied_guard_passed_env`.
  - 완료 근거: `threshold_apply_2026-05-14.json`은 status=`auto_bounded_live_ready`, apply_mode=`auto_bounded_live`, runtime_change=`true`이며 `threshold_runtime_env_2026-05-14.{env,json}`을 생성했다. runtime env selected family는 `soft_stop_whipsaw_confirmation`, env override는 `KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED=true`다. `score65_74_recovery_probe`는 전일 selected family였지만 당일 runtime env override에는 새 값으로 쓰이지 않았다.
  - 완료 다음 액션: 미반영/hold_sample family는 수동 env override하지 않고 장후 EV/attribution에서 다시 판정한다.

- [x] `[OpenAIWSPreopenConfirm0514] OpenAI WS 유지 설정 및 entry_price/analyze_target provenance 확인` (`Due: 2026-05-14`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: RuntimeStability`)
  - Source: [openai_ws_stability_2026-05-13.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-05-13.md), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py)
  - 판정 기준: startup env의 OpenAI route/Responses WS 설정과 `analyze_target`, `entry_price` transport provenance를 분리 확인한다.
  - 금지: provider transport 확인을 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경으로 해석하지 않는다.
  - 다음 액션: entry_price transport 표본이 부족하면 장중 표본 재확인 항목과 연결한다.
  - 완료 판정: `pass_with_entry_price_followup`.
  - 완료 근거: `run_bot.sh`는 `KORSTOCKSCAN_SCALPING_AI_ROUTE=openai`, `KORSTOCKSCAN_OPENAI_TRANSPORT_MODE=responses_ws`, `KORSTOCKSCAN_OPENAI_RESPONSES_WS_ENABLED=true`를 export하며, `bot_history.log`에는 `2026-05-14 07:40:14 KST` main route=`openai`가 남아 있다. `openai_ws_stability_2026-05-13.md`는 decision=`keep_ws`, unique WS calls=`752`, endpoint=`analyze_target`, WS fallback=`0/752`, success rate=`1.0`이다.
  - 완료 다음 액션: `entry_price WS sample count=0`은 OpenAI WS 실패가 아니라 hook 미발생/표본 부족으로 분리한다. 장중/장후 attribution에서 `entry_price` transport provenance가 생기면 별도 확인하고, 이 확인만으로 threshold/order/provider/swing guard를 변경하지 않는다.

- [x] `[SwingApprovalArtifactPreopen0514] 스윙 approval request 및 별도 승인 artifact 존재 여부 확인` (`Due: 2026-05-14`, `Slot: PREOPEN`, `TimeWindow: 08:45~08:50`, `Track: RuntimeStability`)
  - Source: [swing_runtime_approval_2026-05-13.json](/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-05-13.json), [threshold_cycle_ev_2026-05-13.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-13.json)
  - 판정 기준: approval request가 있더라도 사용자 승인 artifact가 없으면 env apply 대상이 아니다.
  - 금지: 스윙 dry-run 해제, real canary, floor, scale-in real canary를 서로 자동 승인하지 않는다.
  - 다음 액션: `approval_artifact_present`, `approval_artifact_missing`, `blocked_by_policy` 중 하나로 닫는다.
  - 완료 판정: `approval_artifact_missing`.
  - 완료 근거: `swing_runtime_approval_2026-05-13.json`은 runtime_change=`false`, approval_requests=`0`이고, one-share real canary와 scale-in real canary는 각각 policy_state=`approval_required`, runtime_apply_allowed=`false`다. `data/threshold_cycle/approvals` 아래 별도 approval artifact도 없다.
  - 완료 다음 액션: 스윙 dry-run 해제, one-share real canary, scale-in real canary, floor/env 변경은 별도 approval artifact 없이는 열지 않는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0514] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-05-14`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-13.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-13.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, score65_74_recovery_probe가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0514] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-05-14`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-05-13.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-13.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

## 장후 체크리스트 (16:30~18:55)

- [ ] `[ThresholdDailyEVReport0514] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-05-14`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-13.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-13.json), [threshold_cycle_cumulative_2026-05-13.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_cumulative/threshold_cycle_cumulative_2026-05-13.json), [threshold_cycle_cumulative_2026-05-12.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_cumulative/threshold_cycle_cumulative_2026-05-12.json), [verify_threshold_cycle_postclose_chain.py](/home/ubuntu/KORStockScan/src/engine/verify_threshold_cycle_postclose_chain.py)
  - 판정 기준: real/sim/combined split, selected/blocked family, runtime_change, warning을 분리해 확인한다. 누적/rolling report는 전일 대비 `completed_valid_cumulative`와 `completed_by_source.real.sample`이 비정상적으로 0 또는 급감하지 않았는지 확인하고, 전일 real 표본이 있는데 당일 real 표본이 0이면 `--skip-db` 오염 또는 DB read 실패로 보고 DB 포함 재생성 후 다시 판정한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: `db_sample_ok`, `db_sample_drop_regenerated`, `source_quality_blocker`, `apply_input_ready`, `hold_sample`, `freeze` 중 하나로 닫고, 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[CodeImprovementWorkorderReview0514] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-05-14`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~17:00`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-05-13.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-13.md), [code_improvement_workorder_2026-05-13.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-13.json)
  - 판정 기준: selected_order_count=12와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인한다.
  - 기준 메모: 2026-05-13 2-pass 구현 후 최신 workorder generation_id=`2026-05-13-855236ba6498`는 `implement_now:0`이다. `order_holding_exit_decision_matrix_edge_counterfactual`은 removed, `order_latency_guard_miss_ev_recovery`는 `attach_existing_family(pre_submit_price_guard)`로 재분류됐다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: 구현 필요, 설계 보류, reject, already_implemented 중 하나로 닫는다.

- [ ] `[HumanInterventionSummary0514] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-05-14`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-13.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-13.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `승인 artifact 필요`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[PanicEntryFreezeGuardImplementationScope0514] panic_entry_freeze_guard 구현 착수 범위 및 approval guard 확인` (`Due: 2026-05-14`, `Slot: POSTCLOSE`, `TimeWindow: 17:15~17:30`, `Track: RuntimeStability`)
  - Source: [panic_entry_freeze_guard_v2_2026-05-13.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/panic_entry_freeze_guard_v2_2026-05-13.md), [runtime_approval_summary_2026-05-13.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-05-13.json), [panic_sell_defense_2026-05-13.json](/home/ubuntu/KORStockScan/data/report/panic_sell_defense/panic_sell_defense_2026-05-13.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py), [runtime_approval_summary.py](/home/ubuntu/KORStockScan/src/engine/runtime_approval_summary.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)
  - 판정 기준: `panic_entry_freeze_guard` 현재 구현 여부를 `report_only_candidate_only`, `approval_env_contract_ready`, `entry_hook_ready_flag_off`, `implementation_workorder_opened`, `hold_report_only`, `defer_attribution_gap` 중 하나로 닫는다. implementation open 시 1차는 approval artifact loader/env mapping/report attribution/runtime approval summary, 2차는 feature flag OFF 기본의 entry pre-submit hook/provenance로 분리한다.
  - 구현 체크: approval artifact 경로 `data/threshold_cycle/approvals/panic_entry_freeze_guard_YYYY-MM-DD.json`, `KORSTOCKSCAN_PANIC_ENTRY_FREEZE_GUARD_*` env key mapping, stale panic source guard, same-stage owner conflict guard, `panic_entry_freeze_block` event의 `actual_order_submitted=false` provenance가 모두 테스트 대상인지 확인한다.
  - 금지: approval artifact, rollback guard, same-stage owner rule이 닫히기 전에는 신규 BUY 차단, score threshold 완화/동결, stop 완화/지연, 자동매도, bot restart, 스윙 실주문 전환을 수행하지 않는다.
  - 다음 액션: 구현 착수 시 runtime 기본값은 OFF로 유지하고, `src/tests/test_threshold_cycle_preopen_apply.py`, `src/tests/test_daily_threshold_cycle_report.py`, `src/tests/test_runtime_approval_summary.py`와 entry hook 단위 테스트를 추가/수정한다. 실제 신규 BUY block은 별도 approval artifact와 preopen apply manifest 확인 전까지 열지 않는다.

- [ ] `[BotCPUHotspotFollowup0514] 장후 bot CPU hotspot throttle/worker split 후속 범위 확인` (`Due: 2026-05-14`, `Slot: POSTCLOSE`, `TimeWindow: 18:20~18:40`, `Track: RuntimeStability`)
  - Source: [2026-05-13-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-05-13-stage2-todo-checklist.md), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh), [bot_main.py](/home/ubuntu/KORStockScan/src/bot_main.py)
  - 판정 기준: 5/13 장후 `scanner_loop_throttle_required` 판정의 재현 여부를 확인하고, 장외 스캘핑 scanner throttle, pipeline logging batching, 별도 worker/process split 중 구현 범위를 하나로 좁힌다.
  - 금지: 장중 hot patch, bot restart, threshold/provider/order guard 변경, profiler 패키지 설치를 수행하지 않는다.
  - 다음 액션: `scanner_loop_throttle_workorder`, `worker_split_workorder`, `logging_batching_workorder`, `observe_only_no_action` 중 하나로 닫는다.

- [ ] `[ShadowCanaryCohortReview0514] shadow/canary/cohort 런타임 분류 및 정리 판정` (`Due: 2026-05-14`, `Slot: POSTCLOSE`, `TimeWindow: 18:40~18:55`, `Track: Plan`)
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
