# 2026-05-12 Stage2 To-Do Checklist

## 오늘 목적

- 2026-05-11 postclose 자동화가 만든 threshold apply 후보와 OpenAI WS 유지 상태를 장전 산출물 기준으로 확인한다.
- 스윙 실주문, 스윙 숫자 floor, 스윙 scale-in real canary는 approval request가 없으므로 사용자 artifact 없이 열지 않는다.
- 2026-05-11 code-improvement workorder는 자동 repo 수정이 아니라 사용자가 Codex에 구현을 지시한 경우에만 실행한다.

## 오늘 강제 규칙

- 장중 runtime threshold mutation은 금지한다. 적용은 PREOPEN `threshold_cycle_preopen_apply`가 생성한 runtime env만 source로 본다.
- OpenAI WS 확인은 transport/provenance 검증이며 threshold 값, 주문가/수량 guard, 스윙 dry-run guard를 변경하지 않는다.
- `actual_order_submitted=false`인 sim/probe 표본은 실주문 전환 근거가 아니라 EV/source-quality 입력이다. 실주문 전환은 별도 approval artifact와 checklist가 필요하다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

## 장전 체크리스트 (08:50~09:00)

- Runbook 운영 확인은 [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md) `장전 확인 절차`와 `build_codex_daily_workorder --slot PREOPEN`의 `PreopenAutomationHealthCheckYYYYMMDD` 블록을 기준으로 본다.

- [ ] `[ThresholdEnvAutoApplyPreopen0512] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-05-12`, `Slot: PREOPEN`, `TimeWindow: 08:50~09:00`, `Track: RuntimeStability`)
  - Source: [README.md](/home/ubuntu/KORStockScan/data/threshold_cycle/README.md), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_threshold_cycle_preopen.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_preopen.sh), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 트리거: `2026-05-12 07:35` PREOPEN apply wrapper가 종료됐거나 `08:50 KST`까지 runtime env/apply plan source 여부를 확인해야 할 때 실행한다.
  - 판단 입력: 전일 `threshold_cycle_ev_2026-05-11.{json,md}`, `data/threshold_cycle/apply_plans/threshold_apply_2026-05-12.json`, `data/threshold_cycle/runtime_env/threshold_runtime_env_2026-05-12.{env,json}`, `src/run_bot.sh`의 runtime env source 로그.
  - 필수 요건: apply mode `auto_bounded_live`, AI correction guard result, deterministic guard result, selected/blocked family, max step/bounds/sample window/safety/same-stage owner guard, generated env keys, `run_bot.sh` source log가 확인되어야 한다.
  - 판정 기준: `auto_bounded_live` guard를 통과한 family만 장전 runtime env로 반영됐는지 확인한다. blocked family는 `blocked_reason`, AI guard, same-stage owner conflict를 남기고 수동 env override를 하지 않는다.
  - 허용 결론: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나다. `partial_apply_with_blocked_families`는 selected env와 blocked reason이 모두 manifest에 있어야 한다.
  - 유지 가드: 장중 runtime threshold mutation은 계속 금지한다. 스윙 approval artifact가 없는 `approval_required` 요청은 env apply 대상이 아니다.

- [ ] `[OpenAIWSPreopenConfirm0512] OpenAI WS 유지 설정 및 entry_price provenance 다음 장전 확인` (`Due: 2026-05-12`, `Slot: PREOPEN`, `TimeWindow: 08:50~09:00`, `Track: RuntimeStability`)
  - Source: [openai_ws_stability_2026-05-11.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-05-11.md), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)
  - 실행 기준: `KORSTOCKSCAN_SCALPING_AI_ROUTE=openai`, `KORSTOCKSCAN_OPENAI_TRANSPORT_MODE=responses_ws`, `KORSTOCKSCAN_OPENAI_RESPONSES_WS_ENABLED=true`가 startup env에 유지되는지 확인한다.
  - entry_price 확인: 2026-05-11 canary 적용 3건은 있었지만 transport provenance가 누락됐으므로, 다음 영업일에는 `entry_ai_price_canary_*`의 `openai_endpoint_name=entry_price`, `openai_transport_mode=responses_ws`, fallback/fail-closed/latency provenance를 별도 확인한다.
  - 유지 가드: OpenAI WS 유지 확인은 provider transport 검증이며 threshold 값, 주문가/수량 guard, 스윙 dry-run guard를 변경하지 않는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-05-11` postclose -> `2026-05-12`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- 해당 슬롯 자동 생성 항목 없음.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0512] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-05-12`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-11.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-11.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, score65_74_recovery_probe가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[OpenAIWSIntradaySample0512] OpenAI WS/entry_price 장중 표본 및 fallback/fail-closed 재확인` (`Due: 2026-05-12`, `Slot: INTRADAY`, `TimeWindow: 09:20~09:35`, `Track: RuntimeStability`)
  - Source: [openai_ws_stability_2026-05-11.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-05-11.md)
  - 판정 기준: `analyze_target` WS latency/fallback과 `entry_price` transport metadata 누락 여부를 별도 표본으로 확인한다.
  - 금지: entry_price 표본 0건 또는 instrumentation gap을 OpenAI WS runtime 효과 0으로 해석하지 않는다.
  - 다음 액션: 표본 부족이면 postclose provenance 보강 workorder로 분리한다.

- [ ] `[SimProbeIntradayCoverage0512] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-05-12`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-05-11.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-11.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

## 장후 체크리스트 (16:30~18:55)

- [ ] `[ThresholdDailyEVReport0512] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-05-12`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-11.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-11.json)
  - 판정 기준: real/sim/combined split, selected/blocked family, runtime_change, warning을 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[CodeImprovementWorkorderReview0512] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-05-12`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~17:00`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-05-11.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-11.md), [code_improvement_workorder_2026-05-11.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-11.json)
  - 판정 기준: `generation_id`, `source_hash`, `lineage` diff와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인한다.
  - 2-pass 기준: 구현 요청 시 Pass1은 instrumentation/report/provenance만 수행하고, report/workorder 재생성 후 `lineage.new_order_ids` 중 `runtime_effect=false`만 Pass2 추가 구현 대상으로 본다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: 구현 필요, 설계 보류, reject, already_implemented 중 하나로 닫는다.

- [ ] `[HumanInterventionSummary0512] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-05-12`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-11.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-11.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `승인 artifact 필요`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[ShadowCanaryCohortReview0512] shadow/canary/cohort 런타임 분류 및 정리 판정` (`Due: 2026-05-12`, `Slot: POSTCLOSE`, `TimeWindow: 18:40~18:55`, `Track: Plan`)
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
