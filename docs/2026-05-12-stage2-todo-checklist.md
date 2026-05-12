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

### PreopenAutomationHealthCheck20260512 운영 확인 기록

- checked_at: `2026-05-12 08:36 KST`
- 판정: `warning`
- 근거: `threshold_cycle_preopen_cron.log`의 `[DONE] threshold-cycle preopen target_date=2026-05-12` marker, `threshold_apply_2026-05-12.json`의 `auto_bounded_live_ready`, runtime env 파일 생성, `run_bot.sh`의 당일 runtime env source, PID `4493` 환경변수 로드를 확인했다. 스윙 추천 생성은 `final_ensemble_scanner target_date=2026-05-12` `[DONE]` marker와 CSV 3개 우선 적재 로그를 확인했다.
- warning 사유: OpenAI `entry_price` transport provenance는 2026-05-11 리포트 기준 instrumentation gap이 남아 있고, 2026-05-12 08:36 KST 현재 장전이라 신규 `entry_price` 표본은 아직 없다. 또한 장전 error detector의 artifact freshness boundary 경고는 산출물 자체 실패가 아니라 detector 경계 판정 이슈로 분리한다.
- 다음 액션: 장중 `[OpenAIWSIntradaySample0512]`에서 `entry_ai_price_canary_*`의 `openai_endpoint_name=entry_price`, `openai_transport_mode=responses_ws`, fallback/fail-closed/latency provenance를 확인한다. runtime threshold 값과 주문 guard는 장중 변경하지 않는다.

- [x] `[ThresholdEnvAutoApplyPreopen0512] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-05-12`, `Slot: PREOPEN`, `TimeWindow: 08:50~09:00`, `Track: RuntimeStability`)
  - Source: [README.md](/home/ubuntu/KORStockScan/data/threshold_cycle/README.md), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_threshold_cycle_preopen.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_preopen.sh), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 트리거: `2026-05-12 07:35` PREOPEN apply wrapper가 종료됐거나 `08:50 KST`까지 runtime env/apply plan source 여부를 확인해야 할 때 실행한다.
  - 판단 입력: 전일 `threshold_cycle_ev_2026-05-11.{json,md}`, `data/threshold_cycle/apply_plans/threshold_apply_2026-05-12.json`, `data/threshold_cycle/runtime_env/threshold_runtime_env_2026-05-12.{env,json}`, `src/run_bot.sh`의 runtime env source 로그.
  - 필수 요건: apply mode `auto_bounded_live`, AI correction guard result, deterministic guard result, selected/blocked family, max step/bounds/sample window/safety/same-stage owner guard, generated env keys, `run_bot.sh` source log가 확인되어야 한다.
  - 판정 기준: `auto_bounded_live` guard를 통과한 family만 장전 runtime env로 반영됐는지 확인한다. blocked family는 `blocked_reason`, AI guard, same-stage owner conflict를 남기고 수동 env override를 하지 않는다.
  - 허용 결론: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나다. `partial_apply_with_blocked_families`는 selected env와 blocked reason이 모두 manifest에 있어야 한다.
  - 유지 가드: 장중 runtime threshold mutation은 계속 금지한다. 스윙 approval artifact가 없는 `approval_required` 요청은 env apply 대상이 아니다.
  - 완료 판정: `applied_guard_passed_env`.
  - 완료 근거: apply plan은 `status=auto_bounded_live_ready`, `apply_mode=auto_bounded_live`, `runtime_change=true`, selected family는 `soft_stop_whipsaw_confirmation`, `score65_74_recovery_probe`이며 env override는 `KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED=true`, `KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED=true`다. PID `4493` 환경에서도 `KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE=2026-05-12`와 두 env override가 로드됐다.
  - 완료 다음 액션: blocked family는 수동 env override하지 않고 장후 EV/blocked reason으로 재판정한다.

- [x] `[OpenAIWSPreopenConfirm0512] OpenAI WS 유지 설정 및 entry_price provenance 다음 장전 확인` (`Due: 2026-05-12`, `Slot: PREOPEN`, `TimeWindow: 08:50~09:00`, `Track: RuntimeStability`)
  - Source: [openai_ws_stability_2026-05-11.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-05-11.md), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)
  - 실행 기준: `KORSTOCKSCAN_SCALPING_AI_ROUTE=openai`, `KORSTOCKSCAN_OPENAI_TRANSPORT_MODE=responses_ws`, `KORSTOCKSCAN_OPENAI_RESPONSES_WS_ENABLED=true`가 startup env에 유지되는지 확인한다.
  - entry_price 확인: 2026-05-11 canary 적용 3건은 있었지만 transport provenance가 누락됐으므로, 다음 영업일에는 `entry_ai_price_canary_*`의 `openai_endpoint_name=entry_price`, `openai_transport_mode=responses_ws`, fallback/fail-closed/latency provenance를 별도 확인한다.
  - 유지 가드: OpenAI WS 유지 확인은 provider transport 검증이며 threshold 값, 주문가/수량 guard, 스윙 dry-run guard를 변경하지 않는다.
  - 완료 판정: `pass_with_followup`.
  - 완료 근거: `src/run_bot.sh`는 OpenAI route와 Responses WS를 export하며, PID `4493` 환경에서 `KORSTOCKSCAN_SCALPING_AI_ROUTE=openai`, `KORSTOCKSCAN_OPENAI_TRANSPORT_MODE=responses_ws`, `KORSTOCKSCAN_OPENAI_RESPONSES_WS_ENABLED=true`, `KORSTOCKSCAN_OPENAI_RESPONSES_WS_TIMEOUT_MS=15000`, `KORSTOCKSCAN_OPENAI_RESPONSES_MAX_OUTPUT_TOKENS=512`를 확인했다. 2026-05-11 OpenAI WS report는 `decision=keep_ws`, `unique WS calls=569`, `WS fallback=0/569`, `WS success rate=1.0`이다.
  - 완료 다음 액션: `entry_price WS sample count=0` 및 `entry_price canary instrumentation_gap=True`는 rollback이 아니라 장중 provenance 확인 대상으로 넘긴다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-05-11` postclose -> `2026-05-12`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- 해당 슬롯 자동 생성 항목 없음.

## 장중 체크리스트 (09:05~15:20)

### IntradayAutomationHealthCheck20260512 운영 확인 기록

- checked_at: `2026-05-12 09:08 KST`
- 판정: `pass`
- 근거: `bot_main.py` PID `15393`이 실행 중이고 `pipeline_events_2026-05-12.jsonl`은 09:08 KST 기준 5,121건으로 append 중이다. `buy_funnel_sentinel_2026-05-12`와 `holding_exit_sentinel_2026-05-12`는 모두 09:05 cron `[DONE]` marker와 `classification.primary=NORMAL`을 생성했다. `run_error_detection.log`도 09:05 full detector `[DONE]` marker를 남겼고 process/resource/stale-lock은 pass다. `threshold_events_2026-05-12.jsonl`은 7건으로 sparse stream이 생성됐으며, selected threshold family 직접 표본은 아직 없지만 runbook 기준 fatal stale이 아니라 source coverage 대기다.
- not_yet_due: `12:05` intraday threshold calibration과 장후/postclose 산출물은 아직 due 전이다.
- 다음 액션: Sentinel/Detector는 계속 report-only로 본다. selected runtime family, OpenAI `entry_price`, scalp sim BUY 확정 표본은 장후 EV/report에서 재확인하고 장중 runtime threshold mutation은 하지 않는다.

- [x] `[SwingMarketRegimeLocalBreadthGate0512] 스윙 market-regime 게이트 국내 breadth 반영 누락 점검` (`Due: 2026-05-12`, `Slot: INTRADAY`, `TimeWindow: 09:05~15:20`, `Track: SwingLogic`)
  - Source: [report_2026-05-12.json](/home/ubuntu/KORStockScan/data/report/report_2026-05-12.json), [market_regime_snapshot.json](/home/ubuntu/KORStockScan/data/cache/market_regime_snapshot.json), [service.py](/home/ubuntu/KORStockScan/src/market_regime/service.py), [sniper_market_regime.py](/home/ubuntu/KORStockScan/src/engine/sniper_market_regime.py)
  - 판정: `fix_applied_restarted`.
  - 근거: 일일 리포트 breadth는 `20일선 위 비율 62.8%`, `status_text=상승장`인데 기존 스윙 market-regime cache는 VIX/WTI/Fear&Greed만 점수화해 `oil=35`, `swing_score=35`, `risk_state=RISK_OFF`, `allow_swing_entry=false`로 닫혔다. 이는 표시 오류와 별개로 스윙 dry-run/probe 게이트에 영향을 주는 국내 breadth 반영 누락이다.
  - 조치: `MarketRegimeService`가 daily report/diagnostics의 국내 breadth context를 로드해 `local_breadth` component score로 합산하도록 수정했다. 현재 조건에서는 원유 반전 `35` + 국내 breadth `35`로 `swing_score=70`, `allow_swing_entry=true`가 된다. 단, VIX extreme이 아직 해소되지 않은 경우에는 local breadth override를 막는다.
  - 검증: `pytest` 10건 통과, `py_compile` 통과, `sync_docs_backlog_to_project --print-backlog-only --limit 500` parser 검증 통과. market regime cache는 `risk_state=RISK_ON`, `allow_swing_entry=true`, `swing_score=70`, `component_scores.local_breadth=35`로 재생성했다. 봇은 PID `4493 -> 15393`으로 재기동했고 `bot_history.log`에 `시장상태=상승장, 리스크=리스크온`, `시장환경 초기화 risk=RISK_ON, allow_swing=True`가 기록됐다.
  - 다음 액션: 장중 스윙 probe/dry-run 로그에서 `market_regime_pass`와 `actual_order_submitted=false` provenance를 분리 확인한다. 스윙 실주문 전환은 별도 approval artifact 없이는 열지 않는다.

- [x] `[RuntimeEnvIntradayObserve0512] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-05-12`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-11.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-11.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, score65_74_recovery_probe가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 완료 판정: `warning_sample_pending`.
  - 완료 근거: `threshold_runtime_env_2026-05-12.env`와 현재 봇 PID `15393` 환경에서 `KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED=true`, `KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED=true`, `KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE=2026-05-12` 로드를 확인했다. `data/pipeline_events/pipeline_events_2026-05-12.jsonl`은 09:08 KST 기준 5,121건으로 append 중이고, `data/threshold_cycle/threshold_events_2026-05-12.jsonl`은 7건의 sparse event를 생성했다. 다만 selected family `soft_stop_whipsaw_confirmation`, `score65_74_recovery_probe` 직접 provenance는 아직 0건이다. rollback/safety breach 문자열도 0건이다.
  - 완료 다음 액션: 표본 미발생은 runtime 실패가 아니라 `pending_applied_cohort`로 유지한다. 장후 `ThresholdDailyEVReport0512`에서 selected family 적용/미적용 cohort와 rollback guard를 다시 확인한다.

- [x] `[OpenAIWSIntradaySample0512] OpenAI WS/entry_price 장중 표본 및 fallback/fail-closed 재확인` (`Due: 2026-05-12`, `Slot: INTRADAY`, `TimeWindow: 09:20~09:35`, `Track: RuntimeStability`)
  - Source: [openai_ws_stability_2026-05-11.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-05-11.md)
  - 판정 기준: `analyze_target` WS latency/fallback과 `entry_price` transport metadata 누락 여부를 별도 표본으로 확인한다.
  - 금지: entry_price 표본 0건 또는 instrumentation gap을 OpenAI WS runtime 효과 0으로 해석하지 않는다.
  - 완료 판정: `pass_with_entry_price_sample_pending`.
  - 완료 근거: 09:08 KST 기준 `pipeline_events_2026-05-12.jsonl`에서 OpenAI 관련 `ai_confirmed` 7건을 확인했다. 7건 모두 `openai_endpoint_name=analyze_target`, `openai_transport_mode=responses_ws`, `openai_ws_used=True`, `openai_ws_http_fallback=False`, `ai_parse_fail=False`였다. roundtrip은 대략 `1014~3117ms`, queue wait는 `0~65ms` 범위다. `entry_price`/`entry_ai_price` 표본은 아직 0건이다.
  - 완료 다음 액션: `entry_price` 표본 0건은 OpenAI WS 실패가 아니라 해당 hook 미발생/표본 부족으로 분리한다. postclose 또는 다음 장중 표본에서 `openai_endpoint_name=entry_price`, `openai_transport_mode=responses_ws`, fallback/fail-closed provenance를 다시 확인한다.

- [x] `[SimProbeIntradayCoverage0512] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-05-12`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-05-11.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-11.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 완료 판정: `pass_with_scalp_sim_no_sample_yet`.
  - 완료 근거: `pipeline_events_2026-05-12.jsonl`에서 simulation provenance가 `SwingIntradayLiveEquivalentProbe0511` 115건, `SwingLiveOrderDryRunSimulation0511` 3건으로 확인됐고, `actual_order_submitted=False`는 108건 확인됐다. `data/runtime/swing_intraday_probe_state.json`은 `simulation_book=swing_intraday_live_equiv_probe`, `owner=SwingIntradayLiveEquivalentProbe0511`, `updated_at=2026-05-12T09:05:48`, active 10개이며 모든 active probe가 `simulated_order=True`, `actual_order_submitted=False`, `broker_order_forbidden=True`다. origin은 `blocked_swing_score_vpw` 4개, `blocked_gatekeeper_reject` 4개, `blocked_swing_gap` 2개다. `scalp_live_simulator_state.json`은 active 0개로, 스캘핑 BUY 확정 sim 표본은 아직 없다.
  - 추가 점검(10:13 KST): `pipeline_events_2026-05-12.jsonl` 기준 스캘핑 sim event는 0건이고, 스윙 probe는 entry 14건, scale-in 가정체결 13건, sell 가정체결 11건이다. sell 가정체결 11건은 모두 `actual_order_submitted=False`, `broker_order_forbidden=True`이며 승률 36.4%, 평균 수익률 -0.283%, 수수료/세금 전 가상 gross PnL +1,405원이다. `swing_intraday_probe_state.json`은 `updated_at=2026-05-12T10:13:41`, active 10개이며 source date는 2026-05-11 3개, 2026-05-12 7개다.
  - 완료 다음 액션: sim/probe는 계속 real/sim split으로만 본다. 스윙 probe cap 도달/discard는 source-quality 정보로 장후 리포트에 넘기고, scalp sim 0건은 BUY 확정 hook 미발생으로 분리한다.

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

- [ ] `[CodeImprovementNonImplementTriage0512] attach/design/defer 항목 재판정 및 다음 소유자 고정` (`Due: 2026-05-12`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-05-11.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-11.md), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: `attach_existing_family`는 기존 family 입력 흡수 여부, `design_family_candidate`는 설계 backlog 필요 여부, `defer_evidence`는 승격/계속보류/폐기 여부로 분리한다.
  - 금지: 비-implement 항목을 자동 구현 또는 자동 runtime apply로 취급하지 않는다.
  - 다음 액션: `attached_to_existing_family`, `needs_codex_instrumentation`, `design_backlog_required`, `continue_defer`, `drop_stale` 중 하나로 닫고, 사람이 다시 지시해야 하는 항목만 다음 checklist에 남긴다.

- [ ] `[HumanInterventionSummary0512] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-05-12`, `Slot: POSTCLOSE`, `TimeWindow: 17:15~17:30`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-11.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-11.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `승인 artifact 필요`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[ScalpingBlockerResolutionPlan0512] 스캘핑 blocker 해소계획 문서화 및 후속 owner 고정` (`Due: 2026-05-12`, `Slot: POSTCLOSE`, `TimeWindow: 17:30~17:45`, `Track: ScalpingLogic`)
  - Source: [scalping-runtime-blocker-resolution-plan-2026-05-12.md](/home/ubuntu/KORStockScan/docs/scalping-runtime-blocker-resolution-plan-2026-05-12.md), [runtime_approval_summary_2026-05-11.md](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-05-11.md), [threshold_apply_2026-05-12.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-05-12.json)
  - 판정 기준: `hold_sample`, `hold_no_edge`, `freeze`, `report_only_design`, `existing_guard_hold`를 한 문서에서 family별 blocker와 unblock 조건으로 분리한다.
  - 금지: 표본 부족을 모든 미적용 사유로 뭉뚱그리거나, sim/combined EV를 broker execution 품질 근거로 단독 사용하지 않는다.
  - 다음 액션: 각 family를 `ready_for_preopen_apply`, `ready_for_bounded_canary_request`, `continue_hold_sample`, `freeze_live_risk`, `report_only_design`, `drop_stale` 중 하나로 닫는다.

- [ ] `[BadEntryLifecycleJoinReadiness0512] bad_entry refined canary lifecycle join readiness guard 수치화` (`Due: 2026-05-12`, `Slot: POSTCLOSE`, `TimeWindow: 17:45~18:00`, `Track: ScalpingLogic`)
  - Source: [scalping-runtime-blocker-resolution-plan-2026-05-12.md](/home/ubuntu/KORStockScan/docs/scalping-runtime-blocker-resolution-plan-2026-05-12.md), [README.md](/home/ubuntu/KORStockScan/data/threshold_cycle/README.md), [threshold_apply_2026-05-12.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-05-12.json)
  - 판정 기준: `record_id -> post_sell_evaluations` join floor, preventable EV benefit, false-positive GOOD_EXIT 손상 guard, rollback owner를 readiness 조건으로 제안한다.
  - 금지: `bad_entry_refined_candidate` runtime provisional signal을 post-sell outcome 없이 최종 bad-entry 라벨로 확정하지 않는다.
  - 다음 액션: guard 수치가 부족하면 `continue_hold_sample`, 수치/owner가 닫히면 `ready_for_bounded_canary_request`로 분리한다.

- [ ] `[ScalpingBlockedFamilyReadinessGuards0512] 스캘핑 blocked family별 readiness guard 자동화 입력 정리` (`Due: 2026-05-12`, `Slot: POSTCLOSE`, `TimeWindow: 18:00~18:20`, `Track: ScalpingLogic`)
  - Source: [scalping-runtime-blocker-resolution-plan-2026-05-12.md](/home/ubuntu/KORStockScan/docs/scalping-runtime-blocker-resolution-plan-2026-05-12.md), [threshold_apply_2026-05-12.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-05-12.json)
  - 판정 기준: `protect_trailing_smoothing`, `trailing_continuation`, `pre_submit_price_guard`, `holding_exit_decision_matrix_advisory`, `position_sizing_cap_release`가 각각 sample floor, GOOD_EXIT 훼손, quote freshness, minimum edge, safety floor 중 어느 blocker에 걸렸는지 자동 산출 입력을 정의한다.
  - 금지: entry gate 완화, score threshold 완화, spread cap 완화, fallback 재개를 blocker 해소 수단으로 섞지 않는다.
  - 다음 액션: 다음 postclose EV/report에 넣을 필드와 live apply 금지 조건을 같이 남긴다.

- [ ] `[ScalpSimDecisionAccelerationPolicy0512] sim 표본 기반 의사결정 가속 기준과 real-only guard 분리` (`Due: 2026-05-12`, `Slot: POSTCLOSE`, `TimeWindow: 18:20~18:40`, `Track: ScalpingLogic`)
  - Source: [scalping-runtime-blocker-resolution-plan-2026-05-12.md](/home/ubuntu/KORStockScan/docs/scalping-runtime-blocker-resolution-plan-2026-05-12.md), [threshold_cycle_ev_2026-05-11.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-11.json)
  - 판정 기준: sim/real/combined split에서 sim 표본이 EV/source-quality 판단을 빠르게 하는 항목과 broker execution 때문에 real-only 증거가 필요한 항목을 분리한다.
  - 금지: `actual_order_submitted=false` 표본을 실주문 전환 또는 체결품질 승인 근거로 단독 사용하지 않는다.
  - 장중 선반영: `score65_74_recovery_probe`는 `scalp_ai_buy_all` 확정 BUY sim과 섞지 않고 `scalp_score65_74_probe_counterfactual` missed/probe counterfactual로 분리한다. `wait6579_ev_cohort`는 이 축을 `actual_order_submitted=false`, `broker_order_forbidden=true`, `runtime_effect=counterfactual_report_only`, `calibration_authority=missed_probe_ev_only_not_broker_execution`로 집계하고, `threshold_cycle_ev_report`는 `missed_probe_counterfactual` 섹션으로 별도 노출한다. 장중 재집계는 허용하되 runtime threshold/order mutation이나 봇 restart 없이 report regeneration만 수행한다.
  - 다음 액션: family별로 `sim_accelerates_decision=true/false`, `real_only_guard=true/false`, `approval_required=true/false`를 다음 automation 입력 후보로 남긴다.

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
