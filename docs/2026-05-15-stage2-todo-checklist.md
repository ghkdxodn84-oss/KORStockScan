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
- `panic_regime_mode`와 `panic_buy_regime_mode`는 report/approval source이며, approval artifact와 rollback guard 없이 신규 BUY 차단, 미체결 주문 취소, holding/exit 강제 변경, 자동매도, TP/trailing 변경, 추격매수 차단, 시장가 전량청산에 직접 쓰지 않는다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-05-14` postclose -> `2026-05-15`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- 운영 확인 기록 (`PreopenAutomationHealthCheck20260515`, `PVTI_lAHOAXZuE84BUTcPzgsxrk4`): 판정은 `warning`. `threshold_cycle_preopen`과 bot runtime env 적용은 pass, OpenAI `entry_price` WS 표본 0건은 장중 재확인으로 연결, 스윙 approval request 2건은 approval artifact missing으로 정상 차단.

- 장전 재확인 기록 (`2026-05-15 08:14 KST`): 판정은 `warning_recheck_resolved`. `threshold_cycle_preopen` `[DONE]`, apply plan status=`auto_bounded_live_ready`, runtime env override=`KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED=true`, tmux `bot`/`bot_main.py` 실행, OpenAI route=`openai` 고정, 스윙 approval request 2건의 `approval_artifact_missing` 차단은 모두 기존 판정과 일치한다. 실행 중인 `bot_main.py` env에도 `KORSTOCKSCAN_OPENAI_TRANSPORT_MODE=responses_ws`, `KORSTOCKSCAN_OPENAI_RESPONSES_WS_ENABLED=true`가 들어 있어 현재 통신 방식은 WS다. 충돌 원인은 [openai_ws_stability_2026-05-14.json](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-05-14.json)의 기존 decision logic이 `TimeoutError` 2건을 fallback 0건/WS success 1.0/p95 2863ms와 분리하지 못하고 `rollback_http`로 과대 판정한 것이다. `openai_ws_stability_report`를 보정해 low-rate transport error는 `transport_warning.warning_only=true`로 분리했고, 재생성 결과 `decision=keep_ws`, `ws_error_count=2`, `ws_error_rate=0.0021`로 Markdown 판정과 일치한다. 이 warning만으로 runtime/provider/threshold/order guard를 변경하지 않는다.

- [x] `[ThresholdEnvAutoApplyPreopen0515] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-05-15`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-14.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 판정 (`2026-05-15 KST`): `applied_guard_passed_env`.
  - 근거: `logs/threshold_cycle_preopen_cron.log`에 `[DONE] threshold-cycle preopen target_date=2026-05-15` marker가 있고, [threshold_apply_2026-05-15.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-05-15.json)은 status=`auto_bounded_live_ready`, apply_mode=`auto_bounded_live`, runtime_change=`true`다. runtime env는 [threshold_runtime_env_2026-05-15.env](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-05-15.env)와 [threshold_runtime_env_2026-05-15.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-05-15.json)으로 생성됐고 selected family는 `soft_stop_whipsaw_confirmation`, override는 `KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED=true` 1개다. `bad_entry_refined_canary`는 same-stage owner conflict로 차단됐고, `protect_trailing_smoothing`은 `window_policy_blocks_single_case_live_candidate:18/20`, `score65_74_recovery_probe`는 `hold/no_runtime_env_override`로 수동 override 없이 제외됐다.
  - 검증: `tmux bot` 세션은 `2026-05-15 07:40:01 KST` 생성, `bot_main.py` PID `4779` 실행 중이며, [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)는 runtime env를 source한 뒤 봇을 기동하는 경로다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

### Score6574OpenDecisionRecheck0515 확인 기록

- checked_at: `2026-05-15 KST`
- 판정: `not_opened_by_actual_0515_preopen_apply`.
- 근거: 사용자 기억처럼 [2026-05-14 checklist](/home/ubuntu/KORStockScan/docs/2026-05-14-stage2-todo-checklist.md)의 `Score6574ApplyGuardRecheck0514`는 5/13 source를 기준으로 `sample_count=16`, `source_sample_count=16`, `sample_floor_status=panic_adjusted_ready`, `calibration_state=adjust_up`, `decision_reason=ai_guard_accepted`, env override `KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED=true`가 selected 될 수 있다고 재검증했다. 그러나 실제 5/15 preopen apply는 5/14 source를 다시 소비했고, [threshold_apply_2026-05-15.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-05-15.json)의 `score65_74_recovery_probe`는 `sample_window=rolling_5d_with_daily_trigger`, `window_policy.primary=rolling_5d`, `sample_count=177`, `source_sample_count=19`, `sample_floor_status=ready`, `calibration_state=hold`, `decision_reason=no_runtime_env_override`로 닫혔다. [threshold_cycle_2026-05-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_2026-05-14.json)의 `calibration_trigger_pack`도 `window_policy primary=rolling_5d 기준 재평가: score65~74 EV/close_10m 우위가 efficient trade-off gate에 미달해 값 유지`로 기록한다.
- 해석: daily 5/14는 score65~74 병목과 양의 EV/close 신호를 보여 후보로 남겼지만, Plan Rebase/threshold README의 current window policy는 daily trigger만으로 live/bounded apply를 확정하지 않고 rolling/cumulative primary로 재확인한다. 따라서 5/14 11:29의 `logic_fix_ready_not_runtime_applied`는 “5/13 source bug fix 검증 결과”이고, 5/15 실제 runtime env 적용 결과는 “5/14 rolling 재평가 후 미오픈”이다.
- 다음 액션: 장중 runtime threshold mutation은 하지 않는다. score65~74는 오늘 장후 `ThresholdDailyEVReport0515`와 `RuntimeEnvIntradayObserve0515`에서 `selected/applied/not-applied`, daily trigger, rolling primary를 분리해 다시 판정한다.

- [x] `[OpenAIWSPreopenConfirm0515] OpenAI WS 유지 설정 및 entry_price/analyze_target provenance 확인` (`Due: 2026-05-15`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: RuntimeStability`)
  - Source: [openai_ws_stability_2026-05-14.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-05-14.md), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py)
  - 판정 기준: startup env의 OpenAI route/Responses WS 설정과 `analyze_target`, `entry_price` transport provenance를 분리 확인한다.
  - 금지: provider transport 확인을 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경으로 해석하지 않는다.
  - 판정 (`2026-05-15 KST`): `warning / OpenAI route 유지, entry_price 표본 부족`.
  - 근거: [openai_ws_stability_2026-05-14.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-05-14.md)는 `analyze_target` WS unique calls=`962`, fallback=`0/962`, success rate=`1.0`, p95=`2863ms`, HTTP late baseline 대비 median improvement=`0.433`으로 WS 유지 근거를 남겼다. 다만 `entry_price WS sample count=0`이라 entry_price transport는 hook 미발생/표본 부족으로 분리했다. [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)는 `KORSTOCKSCAN_SCALPING_AI_ROUTE=openai`, `KORSTOCKSCAN_OPENAI_TRANSPORT_MODE=responses_ws`, `KORSTOCKSCAN_OPENAI_RESPONSES_WS_ENABLED=true`를 export하고, `bot_history.log`에는 `메인 스캘핑 OpenAI 엔진 고정 완료`, `AI 라우팅 활성화: role=main route=openai`가 남았다.
  - 다음 확인: 같은 checklist의 `[OpenAIWSIntradaySample0515]`에서 entry_price 장중 표본을 재확인한다. 이 warning은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경 근거가 아니다.
  - 다음 액션: entry_price transport 표본이 부족하면 장중 표본 재확인 항목과 연결한다.

- [x] `[SwingApprovalArtifactPreopen0515] 스윙 approval request 및 별도 승인 artifact 존재 여부 확인` (`Due: 2026-05-15`, `Slot: PREOPEN`, `TimeWindow: 08:45~08:50`, `Track: RuntimeStability`)
  - Source: [swing_runtime_approval_2026-05-14.json](/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-05-14.json), [threshold_cycle_ev_2026-05-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-14.json)
  - 판정 기준: approval request가 있더라도 사용자 승인 artifact가 없으면 env apply 대상이 아니다.
  - 금지: 스윙 dry-run 해제, real canary, floor, scale-in real canary를 서로 자동 승인하지 않는다.
  - 판정 (`2026-05-15 KST`): `approval_artifact_missing / blocked_by_policy`.
  - 근거: [swing_runtime_approval_2026-05-14.json](/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-05-14.json)은 `swing_model_floor`, `swing_gatekeeper_reject_cooldown` approval request 2건을 생성했지만 runtime_change=`false`다. `data/threshold_cycle/approvals/swing_runtime_approvals_2026-05-14.json`와 `data/threshold_cycle/approvals/swing_scale_in_real_canary_2026-05-14.json`은 존재하지 않는다. [threshold_apply_2026-05-15.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-05-15.json)의 `swing_runtime_approval`도 requested=`2`, approved=`0`, blocked=`approval_artifact_missing`, selected=`[]`, dry_run_forced=`false`로 차단했다.
  - 다음 액션: approval request는 사용자 승인 전까지 env apply/real canary/dry-run 해제 근거가 아니다. 승인할 경우 별도 approval artifact를 만든 뒤 다음 preopen apply에서만 소비한다.
  - 다음 액션: `approval_artifact_present`, `approval_artifact_missing`, `blocked_by_policy` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- 운영 확인 기록 (`IntradayAutomationHealthCheck20260515`): 판정은 `warning_resolved_for_next_sample`. `OpenAIWSIntradaySample0515`에서 `entry_price` 표본 0건 원인을 simulator BUY 경로의 `_apply_entry_ai_price_canary` 미연결로 확인했고, 실주문 호출 없이 `actual_order_submitted=false` simulator provenance에 `entry_price` canary를 적용하도록 보정했다.

- 운영 확인 기록 (`ErrorDetectionFail07250515`): 판정은 `source_quality_false_positive_fixed`. `2026-05-15 07:25:01 KST` full error detection fail은 `log_scanner`가 `macro_briefing_complete_error.log(+5)`를 `UNKNOWN(5)`로 분류한 것이다. 실제 5줄은 `[MACRO] live_bundle fetched`, `LIVE bundle_as_of`, `MACRO CACHE SAVE`, `applying LIVE bundle`, `collect_snapshot done` 정상 진행 로그였고, cron/process/artifact/resource/stale_lock 및 Kiwoom auth detector는 pass였다. 원인은 `macro_briefing_complete.py`가 정상 macro progress를 `log_error`로 남긴 로그 sink 오염이다. 정상 macro progress/cache 로그를 `log_info`로 내리도록 보정했으며 runtime threshold/provider/order/bot restart 변경은 없다. 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_error_detector_log_scanner.py` -> `14 passed`; `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/macro_briefing_complete.py src/engine/error_detectors/log_scanner.py`; `PYTHONPATH=. .venv/bin/python -m src.engine.error_detector --mode log_only --dry-run` -> `summary_severity=pass`, `log_scanner=pass`.

- 운영 확인 기록 (`ProcessHealthStartupRace07400515`): 판정은 `startup_boundary_false_positive_fixed`. `2026-05-15 07:40:02 KST` full error detection fail은 `process_health`가 봇 expected runtime window 시작 초(`07:40`)에 오래된 heartbeat PID `48192`를 읽어 `pid_dead`로 fail 처리한 것이다. 같은 시각 `tmux bot` 세션은 `07:40:01 KST` 생성 중이었고, 이후 `bot_main.py` PID `13479`가 정상 기동해 `07:45` full detection부터 pass로 회복됐다. 현재 `health_only --dry-run`도 `main_loop_pid=13479`, `main_loop_status=ok`, thread status=`ok`다. 조치: `process_health`에 `ERROR_DETECTOR_BOT_STARTUP_GRACE_SEC=180` startup grace를 추가해 expected start 직후 heartbeat/PID가 아직 갱신되지 않은 경우 fail이 아니라 warning/recheck로 분류하도록 보정했다. 이 조치는 detector race 보정이며 runtime threshold/provider/order guard 변경이 아니다. 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_error_detector_process_health.py src/tests/test_constants.py -k 'process_health or error_detector'` -> `14 passed, 10 deselected`; `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/error_detectors/process_health.py src/utils/constants.py`; `PYTHONPATH=. .venv/bin/python -m src.engine.error_detector --mode health_only --dry-run` -> `summary_severity=pass`, `process_health=pass`.

- 운영 확인 기록 (`OpenAITransportFixtureNoise07550515`): 판정은 `test_fixture_log_noise_fixed`. `2026-05-15 07:55:02 KST` full error detection fail은 `log_scanner`가 `ai_engine_openai_error.log(+10)`을 `UNKNOWN/API_ERROR/TIMEOUT_ERROR/WEBSOCKET_ERROR`로 분류한 것이다. 실제 10줄은 `테스트`, `test: ws timeout`, `OpenAI WS fail-closed ... 테스트`, `request_id mismatch`, `invalid_prompt retry` 등 OpenAI transport pytest/self-test fixture signature였고, 실제 운영 종목 오류가 아니다. 원인은 `log_scanner` ignore rule이 영문 `TEST`만 제외하고 한국어 `테스트` 및 `test:` context를 제외하지 못한 것이다. `테스트`/`test:` fixture signature를 scanner ignore rule에 추가했으며 runtime provider/threshold/order guard 변경은 없다. 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_error_detector_log_scanner.py` -> `15 passed`; `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/error_detectors/log_scanner.py`; `PYTHONPATH=. .venv/bin/python -m src.engine.error_detector --mode log_only --dry-run` -> `summary_severity=pass`, `log_scanner=pass`.

- 운영 확인 기록 (`AIInputFreshnessProvenance0515`): 판정은 `source_quality_operational_override_applied`. 스캘핑은 장중 즉시성 데이터이므로 BUY drought의 AI 입력 stale/flat 여부를 장후까지 미루지 않고 1~2시간 내 운영 오버라이드 대상으로 확인한다. 새 report/cron/threshold 축은 만들지 않고 기존 `ai_confirmed`/`blocked_ai_score` provenance를 보강해 `tick_sample_count`, `tick_latest_time`, `tick_latest_age_ms`, `tick_window_span_sec`, `tick_accel_source`, `tick_accel_effective_recent_5tick_seconds`, `tick_acceleration_ratio_raw`, `tick_context_stale`, `tick_context_quality`, `quote_age_ms`, `quote_age_source`, `quote_stale`를 JSONL에 남기도록 했다. 10:35 이후 재기동 표본 29건 확인 결과 `ai_confirmed` 13건 중 `accel_zero_recent_window` 5건이 있었고, tick latest age는 대체로 0~2초라 missing/stale보다 같은 초에 5틱이 몰리며 `recent_5tick_seconds=0`으로 가속도가 0 처리되는 feature flatness 문제로 판단했다. [scalping_feature_packet.py](/home/ubuntu/KORStockScan/src/engine/scalping_feature_packet.py)는 같은 초 10틱 burst에서 이전 5틱 window가 있으면 effective recent window를 1초로 두고 `tick_accel_source=same_second_burst_10ticks`, `tick_context_quality=fresh_computed`로 산출하도록 보정했다. [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)는 `ai_confirmed`, `blocked_ai_score`, wait65/79 EV 후보, recovery probe 이벤트에 같은 source-quality 필드를 전달한다. 이 조치는 AI 입력 데이터 품질 보정이며 score threshold, selected runtime family, 주문 guard, provider route를 바꾸는 장중 threshold mutation이 아니다. `restart.flag` 기반 우아한 재기동으로 `bot_main.py` PID가 `13479 -> 34781 -> 36360 -> 37367`로 교체됐고 새 PID env는 `KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE=2026-05-15`, `KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED=true`, `KORSTOCKSCAN_SCALPING_AI_ROUTE=openai`, `KORSTOCKSCAN_OPENAI_TRANSPORT_MODE=responses_ws`, `KORSTOCKSCAN_OPENAI_RESPONSES_WS_ENABLED=true`를 유지한다. 재기동 후 10:42 KST 표본에는 `same_second_burst_10ticks`가 `fresh_computed`로 기록됐고, 10:46 KST health check는 `summary_severity=pass`, `main_loop_pid=37367`, thread status=`ok`다. 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_scalping_feature_packet.py src/tests/test_ai_engine_openai_v2_audit_fields.py::test_openai_scalping_analyze_target_returns_feature_audit_fields` -> `5 passed, 1 warning`; `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/scalping_feature_packet.py src/engine/sniper_state_handlers.py`; `PYTHONPATH=. .venv/bin/python -m src.engine.error_detector --mode health_only --dry-run` -> `summary_severity=pass`.

- 운영 확인 기록 (`AIInputFreshnessDuplicateKwarg10510515`): 판정은 `runtime_error_fixed_and_restarted`. `2026-05-15 10:43~10:51 KST` log scanner UNKNOWN burst는 [sniper_state_handlers_error.log](/home/ubuntu/KORStockScan/logs/sniper_state_handlers_error.log)의 `src.engine.sniper_state_handlers._log_entry_pipeline() got multiple values for keyword argument 'tick_source_quality_fields_sent'` 반복이다. 원인은 `AIInputFreshnessProvenance0515` 보강 직후 `ai_confirmed`와 non-50 `blocked_ai_score`가 `feature_probe`의 source-quality 필드와 `ai_decision`의 audit 필드를 동시에 kwargs로 펼친 것이다. 해당 예외는 AI 호출 자체가 아니라 이벤트 로깅 예외였지만, try 블록 전체가 실패하며 해당 종목은 `Score 50 매수보류 override`로 처리됐다. 조치: [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)의 `ai_confirmed`와 non-50 `blocked_ai_score`에서는 `ai_decision` audit 필드만 사용하도록 중복 `feature_probe` kwargs를 제거했고, wait65/79 후보와 recovery probe처럼 AI ops audit 필드를 같이 펼치지 않는 이벤트는 source-quality 필드 전달을 유지했다. `restart.flag` 기반 우아한 재기동으로 `bot_main.py` PID가 `37367 -> 39117`로 교체됐고 새 PID env는 OpenAI WS route와 `soft_stop_whipsaw_confirmation` selected family를 유지한다. 검증: `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/sniper_state_handlers.py src/engine/scalping_feature_packet.py`; `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_scalping_feature_packet.py src/tests/test_ai_engine_openai_v2_audit_fields.py::test_openai_scalping_analyze_target_returns_feature_audit_fields` -> `5 passed, 1 warning`; `PYTHONPATH=. .venv/bin/python -m src.engine.error_detector --mode health_only --dry-run` -> `summary_severity=pass`, `main_loop_pid=39117`; `PYTHONPATH=. .venv/bin/python -m src.engine.error_detector --mode log_only --dry-run` -> `summary_severity=pass`, `No new error log entries detected`.

- [ ] `[ScalpAIInputFreshnessRecheck0515] 스캘핑 AI 입력 freshness/flatness 운영 오버라이드 후속 재확인` (`Due: 2026-05-15`, `Slot: INTRADAY`, `TimeWindow: 11:30~12:30`, `Track: ScalpingLogic`)
  - Source: [pipeline_events_2026-05-15.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-05-15.jsonl), [scalping_feature_packet.py](/home/ubuntu/KORStockScan/src/engine/scalping_feature_packet.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)
  - 판정 기준: 운영 오버라이드 적용 후 `ai_confirmed`/`blocked_ai_score`에 `tick_source_quality_fields_sent=true`, `tick_accel_source`, `tick_accel_effective_recent_5tick_seconds`, `tick_context_quality`, `quote_age_source`가 찍히고, same-second burst가 `accel_zero_recent_window`가 아니라 `same_second_burst_10ticks`/`fresh_computed`로 분류되는지 확인한다. 5틱 외에 quote timestamp provenance(`quote_age_source=missing`)와 AI 전 단계 strength momentum 차단 로그의 candle/range 기본값(`distance_from_day_high_pct=0`, `intraday_range_pct=0`)도 source-quality gap으로 함께 본다.
  - 금지: 이 재확인을 score threshold, selected runtime family, 주문 guard, provider route 장중 변경 근거로 쓰지 않는다.
  - 다음 액션: `freshness_ok`, `same_second_burst_fixed`, `stale_tick_blocker`, `quote_source_gap`, `ai_score_drought_not_input_stale` 중 하나 이상으로 닫고, BUY 0건이 지속되면 threshold 변경이 아니라 AI scoring/prompt/source-quality workorder 후보로 분리한다.

- [x] `[RuntimeEnvIntradayObserve0515] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-05-15`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-14.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 판정 (`2026-05-15 09:07 KST`): `runtime_env_present_event_sample_pending / rollback_guard_clear`.
  - 근거: [threshold_apply_2026-05-15.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-05-15.json)은 status=`auto_bounded_live_ready`, apply_mode=`auto_bounded_live`, runtime_change=`true`, runtime env override=`KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED=true`를 기록한다. [threshold_runtime_env_2026-05-15.env](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-05-15.env)와 [threshold_runtime_env_2026-05-15.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-05-15.json)의 selected family도 `soft_stop_whipsaw_confirmation` 1개다. 실행 중인 `bot_main.py` PID `13479` env에는 `KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE=2026-05-15`, `KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED=true`, `KORSTOCKSCAN_SCALPING_AI_ROUTE=openai`, `KORSTOCKSCAN_OPENAI_TRANSPORT_MODE=responses_ws`가 들어 있다.
  - 이벤트 확인: [pipeline_events_2026-05-15.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-05-15.jsonl)은 `2026-05-15 09:07 KST` 기준 JSONL 4,737건이며 `soft_stop_whipsaw_confirmation=0`, `rollback=0`, `safety_revert=0`, `threshold_runtime_mutation=0`, `runtime_mutation=0`, `unauthorized=0`, `guard_breach=0`이다. 따라서 env 적용은 present지만 holding/soft-stop runtime sample이 아직 없어 runtime event provenance는 `sample_pending`으로 분리한다.
  - 검증: `/proc/13479/environ` runtime env 확인, `threshold_runtime_env_2026-05-15.env/json` 확인, `threshold_apply_2026-05-15.json` 확인, `pipeline_events_2026-05-15.jsonl` JSONL 카운트 스캔.
  - 다음 액션: 장중 threshold mutation은 하지 않는다. 장후 `ThresholdDailyEVReport0515`/post-apply attribution에서 selected/applied/not-applied cohort와 실제 soft-stop runtime event provenance를 재확인한다.

- [x] `[OpenAIWSIntradaySample0515] OpenAI WS/entry_price 장중 표본 및 fallback/fail-closed 재확인` (`Due: 2026-05-15`, `Slot: INTRADAY`, `TimeWindow: 09:20~09:35`, `Track: RuntimeStability`)
  - Source: [openai_ws_stability_2026-05-14.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-05-14.md), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [test_scalp_live_simulator.py](/home/ubuntu/KORStockScan/src/tests/test_scalp_live_simulator.py)
  - 판정 기준: `analyze_target` WS latency/fallback과 `entry_price` transport metadata 누락 여부를 별도 표본으로 확인한다.
  - 금지: entry_price 표본 0건 또는 instrumentation gap을 OpenAI WS runtime 효과 0으로 해석하지 않는다.
  - 판정 (`2026-05-15 KST`): `root_cause_found_and_fix_applied`.
  - 근거: `data/pipeline_events/pipeline_events_2026-05-14.jsonl` 전체 스캔 결과 `scalp_sim_entry_armed=1`, `scalp_sim_buy_order_virtual_pending=1`, `scalp_sim_buy_order_assumed_filled=1`, `scalp_sim_holding_started=1`, `scalp_sim_sell_order_assumed_filled=2`가 있었지만 `openai_endpoint_name=entry_price`는 0건이었다. 원인은 실거래 제출 경로의 `_apply_entry_ai_price_canary`가 simulator BUY 신호 경로에는 연결되지 않아, sim 실적이 있어도 `entry_price` transport provenance가 생성되지 않는 구조였다.
  - 조치: `maybe_arm_scalp_live_simulator_from_buy_signal`에 `ai_engine`을 전달하고, simulator의 가상 주문도 `_apply_entry_ai_price_canary`를 통과하도록 보정했다. 이 조치는 `actual_order_submitted=false`와 `simulated_order=true`를 유지하며 실주문을 호출하지 않고, 가상 주문 가격/skip 여부와 `entry_price` OpenAI transport metadata만 남긴다.
  - 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_scalp_live_simulator.py` -> `18 passed`; `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_sniper_scale_in.py -k entry_ai_price_canary` -> `3 passed, 142 deselected`; `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_ai_engine_openai_transport.py` -> `17 passed`.
  - 다음 액션: 다음 장중/장후 openai_ws report에서 `entry_price_ws_sample_count`와 `entry_price_canary_summary.transport_observable_count`가 sim BUY 표본과 함께 증가하는지 확인한다.

- [x] `[SimProbeIntradayCoverage0515] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-05-15`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-05-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-14.json), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [swing_daily_simulation_report.py](/home/ubuntu/KORStockScan/src/engine/swing_daily_simulation_report.py)
  - 판정 기준: 스캘핑·스윙 모두에서 BUY/선정 가능 후보가 실주문 예수금/real cap/approval 부재와 무관하게 sim/probe 후보로 남고, `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 판정 (`2026-05-15 KST`): `partial_gap_fixed_with_remaining_declared_proxy`.
  - 근거: `OpenAI entry_price 표본 0건` 원인과 같은 유형의 silent gap을 점검한 결과, 스캘핑 sim entry는 `entry_price` canary 미연결을 이미 보정했고 추가로 passive-probe `stale_context_or_quote` submit revalidation이 sim pending 전에 적용되지 않던 gap을 보정했다. 스캘핑/스윙 scale-in 공통 함수도 sim/probe 분기 전에 실계좌 `get_deposit()`를 읽어 실계좌 주문가능금액이 sim scale-in 후보를 막을 수 있었으므로, simulated position은 `SIM_VIRTUAL_BUDGET_KRW`를 deposit 입력으로 쓰고 `virtual_budget_override=true`, `budget_authority=sim_virtual_not_real_orderable_amount`를 남기도록 보정했다.
  - 현재 동등/비동등 분류:
    - 스캘핑 runtime sim: BUY trigger를 넓게 잡기 위해 real budget/real broker submit은 의도적으로 건너뛰지만, entry price canary, passive submit revalidation, holding/exit, scale-in price resolver/dynamic qty는 runtime 함수와 연결된다. 결과는 `actual_order_submitted=false`이며 broker execution 품질 근거가 아니다.
    - 스윙 intraday probe/dry-run: real order submit은 금지하고, blocked stage에서 current price 기반 virtual holding을 만든다. holding/exit와 scale-in은 runtime handler를 공유하되, probe open/per-symbol/daily quota 초과는 `swing_probe_discarded`로 명시 기록된다.
    - 스윙 daily simulation: `runtime_order_dry_run_daily_proxy`이며 gatekeeper AI/tick/orderbook 입력을 일봉으로 replay할 수 없어 `gatekeeper_mode=dry_run_assumed_pass`로 표시한다. 이는 broad source bundle/approval 후보 입력이지 실시간 gatekeeper transport 또는 broker-equivalent 실행 검증이 아니다.
  - 이벤트 확인: `pipeline_events_2026-05-14.jsonl` 기준 `scalp_sim_entry_armed=1`, `scalp_sim_buy_order_assumed_filled=1`, `scalp_sim_sell_order_assumed_filled=2`, `swing_probe_entry_candidate=15`, `swing_probe_sell_order_assumed_filled=15`, `swing_sim_scale_in_order_assumed_filled=1`, `swing_probe_scale_in_order_assumed_filled=1`이 있었고, `swing_probe_discarded=14898`은 quota/duplicate/cooldown 등 명시 discard로 남았다.
  - 리포트 범위 확인 (`2026-05-15 KST`): 시뮬레이션 변경으로 새 canonical report chain은 만들지 않는다. 다만 `scalp_sim_entry_ai_price_applied`, `scalp_sim_entry_ai_price_skip_order`, `scalp_sim_entry_submit_revalidation_warning`, `scalp_sim_entry_submit_revalidation_block`은 `pre_submit_price_guard`, `scalp_sim_scale_in_order_*`는 `scale_in_price_guard`의 sim-only 관찰 범위로 명시 registry/리포트 집계에 포함하도록 보정했다. 실주문 calibration 값과 broker execution 품질에는 섞지 않고, `threshold_cycle_ev`의 Scalp Simulator 섹션에서 applied/skip, revalidation warning/block, scale-in filled/unfilled를 별도로 보이게 한다.
  - 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_scalp_live_simulator.py` -> `21 passed`; `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_sniper_scale_in.py -k 'entry_ai_price_canary or passive_probe_stale'` -> `4 passed, 141 deselected`; `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_model_selection_funnel_repair.py -k 'swing_intraday_probe or swing_probe or swing_same_symbol'` -> `13 passed, 28 deselected`.
  - 다음 액션: 장후 `SimFirstLifecycleCoverageAudit0515`에서 `swing_probe_discarded` 사유별 분포와 quota가 후보 coverage를 과도하게 줄이는지 확인한다. daily swing simulation은 live-equivalent로 승격하지 않고 proxy 권한을 유지한다.

## 장후 체크리스트 (16:30~18:55)

- [ ] `[SimFirstLifecycleCoverageAudit0515] 스캘핑/스윙 적극 sim-first 전주기 실행 및 consumer 연결 확인` (`Due: 2026-05-15`, `Slot: POSTCLOSE`, `TimeWindow: 16:20~16:30`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-14.json), [swing_lifecycle_audit_2026-05-14.json](/home/ubuntu/KORStockScan/data/report/swing_lifecycle_audit/swing_lifecycle_audit_2026-05-14.json), [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)
  - 판정 기준: 스캘핑 `scalp_ai_buy_all`/missed probe와 스윙 dry-run/probe가 entry->holding->scale-in->exit 관찰축을 생성하고, daily EV/threshold cycle/code-improvement workorder/runtime approval summary consumer에 누락 없이 들어갔는지 확인한다.
  - 금지: closed sample 부족, real order 불가, approval artifact 부재를 sim/probe 후보 생성 중단 사유로 쓰지 않는다. sim/probe 결과를 실주문 품질로 섞지도 않는다.
  - 다음 액션: `coverage_ok`, `consumer_gap`, `lifecycle_arm_gap`, `source_quality_blocker`, `sample_floor_gap` 중 하나 이상으로 닫고 gap은 workorder 후보로 연결한다.

- [x] `[WindowPolicyRegistryConsistency0515] threshold family window_policy 레지스트리와 daily/rolling/cumulative consumer 일관성 확인` (`Due: 2026-05-15`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:40`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_2026-05-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_2026-05-14.json), [threshold_cycle_cumulative_2026-05-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_cumulative/threshold_cycle_cumulative_2026-05-14.json), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py), [threshold_cycle_README.md](/home/ubuntu/KORStockScan/data/threshold_cycle/README.md)
  - 판정 기준: 각 family의 `window_policy.primary/secondary/daily_only_allowed`가 calibration candidate, `calibration_source_bundle_by_window`, AI correction input, preopen apply, EV summary, cumulative markdown sample denominator에 동일하게 반영됐는지 확인한다.
  - 금지: daily trigger 표본을 rolling/cumulative primary 표본처럼 표시하거나, registry와 다른 window 기준으로 threshold/code-improvement 결론을 내리지 않는다.
  - 실행 메모 (`2026-05-15 KST`): `daily_threshold_cycle_report.apply_window_policy_registry_to_report`가 `threshold_cycle_cumulative`의 `threshold_snapshot_by_window`와 `calibration_source_bundle_by_window`를 읽어 `window_policy_resolution`을 생성하고, non-daily primary family는 rolling/cumulative ready 표본으로 candidate를 재평가하는 것을 확인했다. `threshold_cycle_2026-05-14.json` 기준 `daily_only_leak_blocked=0`, `rolling_consumer_gap=0`, `sample_denominator_mismatch=0`이며 `rolling_source_snapshot_mismatch=4`는 source metric denominator가 snapshot denominator보다 큰 alignment warning으로 감사 필드에 표시된다. `threshold_apply_2026-05-15.json`은 selected family를 `soft_stop_whipsaw_confirmation` 1개로 제한했고, `score65_74_recovery_probe`는 rolling_5d decision window에서 `hold/no_runtime_env_override`로 남아 daily-only 승격 누수는 없었다.
  - 문서 보정: `data/threshold_cycle/README.md`의 `combined` 설명을 Plan Rebase와 코드의 `diagnostic_only_not_family_candidate_input` 계약에 맞게 수정했다.
  - 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_daily_threshold_cycle_report.py -k 'window_policy or cumulative_threshold_cycle_report'` -> `7 passed, 33 deselected`; `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_threshold_cycle_preopen_apply.py` -> `10 passed`.
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

- [ ] `[PanicLifecycleModePolicyReview0515] 패닉셀/패닉바잉 mode policy와 V2 owner 분리 확인` (`Due: 2026-05-15`, `Slot: POSTCLOSE`, `TimeWindow: 17:25~17:40`, `Track: RuntimeStability`)
  - Source: [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md), [panic_entry_freeze_guard_v2_2026-05-13.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/panic_entry_freeze_guard_v2_2026-05-13.md), [panic_buying_regime_mode_v2_2026-05-14.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/panic_buying_regime_mode_v2_2026-05-14.md), [panic_sell_defense_2026-05-14.json](/home/ubuntu/KORStockScan/data/report/panic_sell_defense/panic_sell_defense_2026-05-14.json), [panic_buying_2026-05-14.json](/home/ubuntu/KORStockScan/data/report/panic_buying/panic_buying_2026-05-14.json), [runtime_approval_summary_2026-05-14.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-05-14.json)
  - 판정 기준: `panic_regime_mode=NORMAL|PANIC_DETECTED|STABILIZING|RECOVERY_CONFIRMED`와 `panic_buy_regime_mode=NORMAL|PANIC_BUY_DETECTED|PANIC_BUY_CONTINUATION|PANIC_BUY_EXHAUSTION|COOLDOWN` 해석이 report-only/source-quality 계약으로 유지되는지 확인한다. 패닉셀 V2.0 `panic_entry_freeze_guard`, V2.1 미체결 진입 주문 cancel, V2.2 holding/exit context, V2.3 강제 축소/청산과 패닉바잉 V2.0 `panic_buy_runner_tp_canary`, V2.1 추격매수 차단, V2.2 continuation trailing, V2.3 exhaustion cleanup, V2.4 cooldown reentry guard owner를 섞지 않는다.
  - 금지: approval artifact, env key, rollback guard, same-stage owner rule 없이 신규 BUY 차단, 주문 취소, 자동매도, 시장가 전량청산, stop/TP/trailing/threshold/provider/bot restart 변경을 수행하지 않는다.
  - 다음 액션: `hold_report_only`, `open_panic_sell_v2_0_approval_contract`, `open_panic_buy_runner_tp_approval_contract`, `open_panic_buy_chase_freeze_design`, `defer_false_positive`, `source_quality_blocker` 중 하나 이상으로 닫는다.

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
