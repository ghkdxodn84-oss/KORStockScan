# Time-Based Operations Runbook

작성 기준: `2026-05-09 KST`
목적: 장전, 장중, 장후 자동화 체인의 시간대별 실행 주체, 산출물, 운영 확인 기준을 한 장으로 고정한다.

이 문서는 실행 절차 runbook이다. 튜닝 원칙과 active owner는 [Plan Rebase](./plan-korStockScanPerformanceOptimization.rebase.md), 날짜별 작업 소유권은 `docs/YYYY-MM-DD-stage2-todo-checklist.md`, threshold-cycle/apply/daily EV 공통 산출물 정의는 [data/threshold_cycle/README.md](../data/threshold_cycle/README.md)를 기준으로 한다. 이 공통 정의는 스캘핑과 스윙이 threshold-cycle, daily EV, code-improvement workorder 체인에 들어오는 부분에 적용한다. 스윙 전용 lifecycle 산출물은 이 runbook의 `15:45`/장후 확인 절차와 `swing_lifecycle_audit`, `swing_improvement_automation`, `swing_pattern_lab_automation` artifact 정의를 함께 기준으로 본다.

## 운영 원칙

- 기본 흐름은 무인 자동화다. 사람의 장전 승인 없이 `auto_bounded_live` guard를 통과한 threshold만 runtime env로 반영한다.
- 장중 threshold runtime mutation은 금지한다. 장중 산출물은 다음 장전 apply 후보 입력으로만 쓴다.
- AI correction은 수정안 제안 layer다. 최종 threshold state/value는 deterministic guard가 결정한다.
- Pattern lab은 `code_improvement_order`와 `auto_family_candidate`만 생성한다. runtime/code를 직접 변경하지 않는다.
- 스윙은 `SWING_LIVE_ORDER_DRY_RUN_ENABLED=True` 기본값에서 live 선정-진입-보유-추가매수-청산 로직을 실행하되 브로커 주문 접수만 차단한다. `swing_sim_*` stage와 `actual_order_submitted=false`는 실제 `order_bundle_submitted`/`sell_order_sent`와 분리해서 본다.
- 스윙 self-improvement는 `selection -> db_load -> entry -> holding -> scale_in -> exit -> attribution` 전체 lifecycle을 대상으로 하며, DB load gap, OFI/QI, AI contract, AVG_DOWN/PYRAMID 관찰축은 report-only/proposal-only다.
- Sentinel은 Telegram 알림 기능을 제거한 운영 감시/report-only 축이다. 이상치는 mutation이 아니라 threshold source bundle, incident, instrumentation gap, normal drift로 라우팅한다.
- 사람이 반드시 개입하는 지점은 운영 장애, 생성된 code improvement workorder를 Codex 세션에 넣어 구현을 요청하는 단계, 문서 backlog Project/Calendar 동기화다.
- `build_codex_daily_workorder`는 Project 항목과 별도로 이 runbook의 장전/장중/장후 확인절차를 `Runbook 운영 확인` 블록으로 자동 포함한다. 이 항목은 GitHub Project/Calendar backlog를 늘리지 않는 Codex 실행용 상태 확인 작업이다.
- 이 문서에서 “확인”은 artifact, log, source-of-truth 문서를 읽고 아래 `판정 상태 정의` 중 하나로 분류하는 행위다. 확인만으로 live env, runtime threshold, broker 주문 상태를 변경하지 않는다.

## 역할/권한 경계

| 주체 | 할 일 | 하지 말 일 | 증적 |
| --- | --- | --- | --- |
| cron/runtime wrapper | 정해진 시각에 preopen/intraday/postclose job 실행, artifact와 log 생성 | 임의 threshold 변경, broker 주문 가드 우회, 실패 은폐 | `data/report/**`, `data/threshold_cycle/**`, `data/pattern_lab/**`, cron log |
| deterministic guard | threshold family별 bounds, max step, sample floor, rollback guard를 적용해 최종 state/value 산출 | AI 제안을 그대로 live 적용, 장중 runtime mutation 수행 | apply plan JSON, runtime env JSON, daily EV report |
| 자동 AI reviewer | threshold/logic/prompt 개선 후보를 proposal-only로 작성 | live env 변경, 주문 판단 직접 변경, deterministic guard 대체 | `swing_threshold_ai_review`, AI correction artifact, strict JSON schema 결과 |
| Codex | 사용자가 요청한 범위에서 코드/문서 수정, artifact 검증, parser/test 실행, workorder 작성 또는 구현 | GitHub Project/Calendar 동기화 실행, 사용자 승인 없는 live guard 완화, broker 주문 제출, 임의 패키지 설치 | 변경 파일, 테스트 결과, 최종 답변 |
| 사람/operator | 장전/장중/장후 판정 검토, 외부 동기화 명령 실행, 운영 장애 복구 판단, 생성 workorder의 구현 지시 여부 결정 | 자동화 artifact만 보고 이미 live 변경됐다고 간주, 출처 없는 수동 threshold 변경 | 수동 실행 명령, Project/Calendar 상태, 운영 메모 |

## 판정 상태 정의

- `pass`: 필수 artifact가 존재하고, 필수 필드가 유효하며, 금지된 runtime 변경이나 provenance 누락이 없다.
- `warning`: artifact는 존재하지만 sample 부족, stale/missing 관찰축, retry, 일부 보조 산출물 지연처럼 다음 관찰이 필요한 상태다. 이 상태만으로 live threshold를 변경하지 않는다.
- `fail`: 필수 artifact 누락, schema/parse 실패, cron/wrapper 실패, runtime provenance 누락, 금지된 runtime 변경 징후가 있는 상태다. 조치는 운영 장애 복구, instrumentation 보강, 또는 workorder 생성이지 즉시 threshold 수동 변경이 아니다.
- `not_yet_due`: 정해진 실행 시각이 아직 지나지 않았거나, 장후 장시간 job이 허용 대기시간 안에서 실행 중인 상태다.

## 체크리스트 반영 기준

- 날짜별 `stage2 todo checklist`는 구현/판정/미래 재확인처럼 소유자가 필요한 작업항목만 체크박스로 소유한다.
- 장전/장중/장후 반복 운영 확인은 날짜별 체크박스가 아니라 `build_codex_daily_workorder --slot PREOPEN|INTRADAY|POSTCLOSE`가 생성하는 `Runbook 운영 확인` 블록이 소유한다.
- 날짜별 checklist의 장전/장중 섹션이 신규 수동 작업 없음으로 비어 있어도 runbook 운영 확인은 생략된 것이 아니다. 해당 섹션에는 runbook 확인절차 참조 문구를 남긴다.
- runbook의 반복 확인 artifact, 시간표, 금지사항을 바꾸면 [build_codex_daily_workorder.py](/home/ubuntu/KORStockScan/src/engine/build_codex_daily_workorder.py)의 `build_runbook_operational_checks`와 관련 테스트를 같은 변경 세트로 맞춘다.
- 새 recurring operational check는 Project/Calendar backlog를 늘리지 않는다. 특정 날짜에만 확인해야 하거나 사람이 구현해야 하는 후속은 날짜별 checklist에 자동 파싱 가능한 `- [ ]` 항목으로 별도 등록한다.

## 시간대별 Runbook

| 시간대 KST | 실행 주체 | 실행/트리거 | 산출물 | 운영 확인 기준 | 금지/주의 |
| --- | --- | --- | --- | --- | --- |
| `07:20` | cron | `final_ensemble_scanner.py` | `logs/ensemble_scanner.log`, `data/daily_recommendations_v2.csv`, `data/daily_recommendations_v2_diagnostics.json` | 스캐너 실패/빈 결과, fallback diagnostic 혼입, 추천 CSV/DB 적재 gap 여부만 확인 | 스캐너 결과만으로 floor/threshold 수동 변경 금지 |
| `07:30` | cron | 기존 `tmux bot` 세션 종료 | tmux session 상태 | 기존 세션이 남아 있으면 `tmux ls` 확인 | 장중 실행 중 강제 종료 금지 |
| `07:35` | cron | `deploy/run_threshold_cycle_preopen.sh` with `THRESHOLD_CYCLE_APPLY_MODE=auto_bounded_live`, `THRESHOLD_CYCLE_AUTO_APPLY_REQUIRE_AI=true` | `data/threshold_cycle/apply_plans/threshold_apply_YYYY-MM-DD.json`, `data/threshold_cycle/runtime_env/threshold_runtime_env_YYYY-MM-DD.{env,json}`, `logs/threshold_cycle_preopen_cron.log` | 실패 시 apply plan의 `blocked_reason`, AI guard, same-stage owner 충돌 확인 | 실패했다고 수동으로 env 값을 직접 덮어쓰지 않는다 |
| `07:40` | cron | `src/run_bot.sh`를 tmux `bot` 세션에서 실행 | bot runtime log, source된 runtime env echo | `runtime_env` 적용 여부와 봇 기동 여부 확인 | runtime env 파일이 없으면 전일 guard 실패로 보고 원인 확인 |
| `08:00~09:00` | operator/guard | PREOPEN 안정 구간 | 없음 | checklist 상단 `오늘 목적/강제 규칙`과 전일 EV report를 읽고 불일치가 있으면 `warning`으로 기록 | full monitor snapshot build는 wrapper가 차단한다. 새 workorder 없는 live toggle 금지 |
| `09:00~09:05` | runtime | 장 시작 후 실전 이벤트 수집 시작 | `data/pipeline_events/pipeline_events_YYYY-MM-DD.jsonl`, `data/threshold_cycle/threshold_events_YYYY-MM-DD.jsonl` | 봇 연결, 계좌/잔고/주문 가능 상태 확인 | threshold 변경, provider 라우팅 변경 금지 |
| `09:05~15:20` | cron | `deploy/run_buy_funnel_sentinel_intraday.sh` 5분 주기 | `data/report/buy_funnel_sentinel/buy_funnel_sentinel_YYYY-MM-DD.md`, `logs/run_buy_funnel_sentinel_cron.log` | `UPSTREAM_AI_THRESHOLD`, `LATENCY_DROUGHT`, `PRICE_GUARD_DROUGHT`, `RUNTIME_OPS` 추세 확인 | Sentinel 결과로 score/spread/fallback/restart 자동 변경 금지 |
| `09:05~15:30` | cron | `deploy/run_holding_exit_sentinel_intraday.sh` 5분 주기 | `data/report/holding_exit_sentinel/holding_exit_sentinel_YYYY-MM-DD.md`, `logs/run_holding_exit_sentinel_cron.log` | `HOLD_DEFER_DANGER`, `SOFT_STOP_WHIPSAW`, `AI_HOLDING_OPS` 추세 확인 | Sentinel 결과로 자동 매도, threshold mutation, bot restart 금지 |
| `09:30~11:00` | cron | `src.engine.buy_pause_guard evaluate` 5분 주기 | `logs/buy_pause_guard.log` | pause guard 반복 발동 여부 확인 | pause guard를 진입 threshold 튜닝 근거로 단독 사용 금지 |
| `09:35~12:00` | cron | monitor snapshot incremental/full | `data/report/monitor_snapshots/*_YYYY-MM-DD.json`, `logs/run_monitor_snapshot_cron.log` | snapshot failure, async timeout, manifest status 확인 | 장전 full build 차단을 우회하지 않는다 |
| `12:05` | cron | `deploy/run_threshold_cycle_calibration.sh` with `THRESHOLD_CYCLE_AI_CORRECTION_PROVIDER=openai` | `data/report/threshold_cycle_calibration/threshold_cycle_calibration_YYYY-MM-DD_intraday.json`, `data/report/threshold_cycle_ai_review/threshold_cycle_ai_review_YYYY-MM-DD_intraday.{json,md}`, `logs/threshold_cycle_calibration_intraday_cron.log` | `calibration_state`, `safety_revert_required`, `ai_status`, `guard_reject_reason` 확인 | 장중 calibration 결과를 당일 runtime에 적용 금지 |
| `15:00` | cron | `deploy/run_preclose_sell_target_report.sh` | `data/report/preclose_sell_target/preclose_sell_target_YYYY-MM-DD.md`, `logs/preclose_sell_target_cron.log` | operator preclose review 산출 여부 확인 | tuning/calibration source로 사용 금지 |
| `15:20~15:30` | runtime/cron | 오버나이트 flow, HOLD/EXIT sentinel final window | pipeline events, holding sentinel | `SELL_TODAY`, `HOLD_OVERNIGHT`, force-exit/safety 이벤트 확인 | flow `TRIM`을 부분청산 구현 없이 HOLD로 해석 금지 |
| `15:45` | cron | `deploy/run_swing_live_dry_run_report.sh` | `data/report/swing_selection_funnel/swing_selection_funnel_YYYY-MM-DD.{json,md}`, `data/report/swing_lifecycle_audit/swing_lifecycle_audit_YYYY-MM-DD.{json,md}`, `data/report/swing_threshold_ai_review/swing_threshold_ai_review_YYYY-MM-DD.{json,md}`, `data/report/swing_improvement_automation/swing_improvement_automation_YYYY-MM-DD.{json,md}`, status JSON, `logs/swing_live_dry_run_cron.log` | `swing_sim_*` stage, `actual_order_submitted=false`, `recommendation_db_load.db_load_skip_reason`, `scale_in_observation`, `ai_contract_metrics`, lifecycle axis coverage, swing threshold AI proposal-only status 확인 | 스윙 dry-run/lifecycle 리포트 결과로 당일 runtime guard 완화 금지 |
| `16:10` | cron | `deploy/run_threshold_cycle_postclose.sh` with OpenAI correction | threshold partition, `threshold_cycle_YYYY-MM-DD.json`, `statistical_action_weight`, `holding_exit_decision_matrix`, `threshold_cycle_cumulative`, postclose AI review, swing lifecycle automation, pattern lab automation, code improvement workorder, daily EV report | `logs/threshold_cycle_postclose_cron.log`, `threshold_cycle_ev_YYYY-MM-DD.md`, swing/scalping automation freshness, `docs/code-improvement-workorders/code_improvement_workorder_YYYY-MM-DD.md`를 확인하고 지연/누락은 `warning` 또는 `fail`로 분류 | postclose 실패 시 다음 장전 auto apply 입력이 부정확하므로 먼저 재실행/복구 |
| `18:00` | cron | `deploy/run_tuning_monitoring_postclose.sh` | Parquet/DuckDB refresh status, `data/report/tuning_monitoring/status/*` | `canonical_runner=THRESHOLD_CYCLE_POSTCLOSE`인지 확인 | pattern lab 중복 실행 금지 |
| `21:00` | cron | `update_kospi.py` | `logs/update_kospi.log` | 데이터 업데이트 실패 여부 확인 | 매매 runtime과 무관한 데이터 갱신으로 취급 |
| `22:30` | cron | `eod_analyzer.py` | `logs/eod_analyzer.log` | EOD 분석 실패 여부 확인 | threshold daily EV를 대체하지 않는다 |
| `22:55` | cron | 봇 tmux 세션 종료 | tmux session 상태 | 장 종료 후 잔여 세션 확인 | 장중 세션 종료와 혼동 금지 |
| `23:10` | cron | dashboard DB archive | `logs/dashboard_db_archive_cron.log` | archive skipped/error 확인 | 미검증 파일 강제 삭제 금지 |
| `23:20` | cron | log rotation cleanup | `logs/log_rotation_cleanup_cron.log` | deleted/size 추세 확인 | 당일 장애 분석 전 로그 수동 삭제 금지 |
| `*:00/5` | cron | `deploy/run_error_detection.sh full` | `data/report/error_detection/error_detection_YYYY-MM-DD.json`, `logs/run_error_detection.log` | 6개 detector (process health, cron, log, artifact, resource, stale lock). 4개 report-only, 2개 filesystem maintenance mutation (flag gated) | 탐지 결과로 runtime threshold/spread/주문 자동 변경 금지 |

## System Error Detector 사용 절차

System Error Detector는 전략 튜닝 도구가 아니라 운영 감시 도구다. 사용 목적은 봇/cron/log/artifact/resource/lock 상태를 조기에 발견하고 `pass`, `warning`, `fail`로 분류하는 것이다. 탐지 결과는 incident, instrumentation gap, runtime ops 확인으로 라우팅하며, score threshold, spread cap, 주문 guard, provider routing, bot restart를 자동 변경하지 않는다.

### 실행 경로

| 경로 | 용도 | 명령/트리거 | 결과 |
| --- | --- | --- | --- |
| cron | 5분 단위 운영 report 생성 | `deploy/run_error_detection.sh full` | `data/report/error_detection/error_detection_YYYY-MM-DD.json`, `logs/run_error_detection.log` |
| bot daemon | 장중 빠른 health alert | `bot_main.py` 내부 `error_detection_loop` | 동일 report 갱신, fail 전환/summary 변경 시 `SYSTEM_HEALTH_ALERT` |
| 수동 dry-run | 배포 전/수정 후 안전 점검 | `PYTHONPATH=. .venv/bin/python -m src.engine.error_detector --mode full --dry-run` | report 파일 미작성, filesystem mutation 차단 |
| 수동 단일 범위 | 특정 detector 재현 | `--mode health_only|cron_only|log_only|artifact_only|resource_only` | 해당 detector만 실행 |

설치/갱신 명령:

```bash
bash deploy/install_error_detection_cron.sh
```

수동 확인 명령:

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.error_detector --mode full --dry-run
tail -n 120 logs/run_error_detection.log
ls -l data/report/error_detection/error_detection_$(TZ=Asia/Seoul date +%F).json
```

### Detector별 판정과 조치

| detector | fail/warning 의미 | operator 조치 | 자동 변경 금지 |
| --- | --- | --- | --- |
| `process_health` | main loop, daemon thread heartbeat stale 또는 PID 불일치 | heartbeat owner와 실제 tmux/process 상태 확인. 장애면 운영 복구 playbook으로 분리 | 자동 restart, threshold 변경 |
| `cron_completion` | 필수 cron log의 당일 DONE 누락 또는 FAIL 최신 marker | 해당 cron log와 산출물 재확인 후 같은 date 재실행 여부 판단 | 실패를 threshold 성과로 해석 |
| `log_scanner` | error log burst 또는 신규 error pattern | stack trace/source artifact 확인 후 incident 또는 code workorder로 분리 | 에러만 보고 live guard 완화 |
| `artifact_freshness` | 시간창 기준 필수 report/artifact stale 또는 누락 | window, trading_day skip, upstream cron 실패 확인 | 누락 artifact를 수동 값으로 대체 |
| `resource_usage` | CPU/memory/swap/load/disk threshold 위반, sampler stale | resource pressure 원인 확인. disk-low면 log rotate 결과와 cooldown state 확인 | 전략 runtime parameter 변경 |
| `stale_lock` | 오래된 lock 발견 또는 cleanup 실패 | active lock인지 확인. 반복되면 wrapper lock lifecycle 보강 | 실행 중인 process lock 강제 삭제 |

### 허용된 filesystem maintenance

6개 detector 중 4개는 순수 report-only다. 아래 2개만 운영 파일 정리 mutation을 허용한다.

- `stale_lock`: `ERROR_DETECTOR_STALE_LOCK_CLEANUP_ENABLED=True`이고 dry-run이 아닐 때, `tmp/*.lock` 중 `ERROR_DETECTOR_STALE_LOCK_MAX_AGE_SEC`를 넘고 `fcntl` non-blocking lock 획득에 성공한 파일만 삭제한다.
- `resource_usage`: disk free가 `ERROR_DETECTOR_DISK_FREE_MIN_MB` 미만이고 `ERROR_DETECTOR_DISK_LOG_ROTATE_ENABLED=True`이며 dry-run이 아닐 때 `deploy/run_logs_rotation_cleanup_cron.sh 7`을 호출한다. 성공한 호출만 `tmp/error_detector_last_log_rotate_ts.txt`에 기록하며, 30분 cooldown 중에는 `log_rotate_trigger=cooldown_active`로 보고한다.

maintenance mutation도 전략 runtime 변경이 아니다. 실패하거나 반복되면 `warning/fail`로 보고 원인 복구를 진행하며, 매매 threshold를 수동 조정하지 않는다.

### Env override

| env var | 효과 | 사용 기준 |
| --- | --- | --- |
| `KORSTOCKSCAN_ERROR_DETECTOR_ENABLED=false` | bot daemon health detector 비활성화 | detector 자체 장애로 bot 기동을 방해할 때 임시 차단 |
| `KORSTOCKSCAN_ERROR_DETECTOR_DAEMON_INTERVAL_SEC=<sec>` | bot daemon 실행 주기 변경 | alert 과다/부하 조정이 필요할 때 |
| `KORSTOCKSCAN_ERROR_DETECTOR_RESOURCE_MAX_SAMPLE_AGE_SEC=<sec>` | resource sampler stale 기준 변경 | sampler 주기 변경과 함께만 조정 |
| `KORSTOCKSCAN_ERROR_DETECTOR_STALE_LOCK_CLEANUP_ENABLED=false` | stale lock 자동 삭제 차단 | lock lifecycle 조사 중 cleanup을 멈출 때 |
| `KORSTOCKSCAN_ERROR_DETECTOR_STALE_LOCK_MAX_AGE_SEC=<sec>` | stale lock age 기준 변경 | wrapper별 lock 보존시간이 다른 경우 |
| `KORSTOCKSCAN_ERROR_DETECTOR_DISK_LOG_ROTATE_ENABLED=false` | disk-low 자동 log rotate 차단 | 장애 분석을 위해 로그 보존이 우선일 때 |

Env override는 운영 안전장치 조정이다. 적용/해제 시 runbook 또는 날짜별 checklist에 이유와 복구 기준을 남긴다.

## 장전 확인 절차

`build_codex_daily_workorder --slot PREOPEN`은 이 절차를 `PreopenAutomationHealthCheckYYYYMMDD`로 자동 포함한다.

1. `logs/threshold_cycle_preopen_cron.log`에서 preopen apply가 완료됐는지 확인한다.
2. `logs/ensemble_scanner.log`, `data/daily_recommendations_v2.csv`, `data/daily_recommendations_v2_diagnostics.json`에서 스윙 추천 생성/empty/fallback diagnostic 분리를 확인한다.
3. `data/threshold_cycle/apply_plans/threshold_apply_YYYY-MM-DD.json`에서 selected family와 blocked family를 본다.
4. `data/threshold_cycle/runtime_env/threshold_runtime_env_YYYY-MM-DD.json`이 있으면 `runtime_change=true` family와 env key를 확인한다. 파일이 없으면 apply plan의 `blocked_reason`을 읽고 `warning` 또는 `fail`로 분류한다.
5. `src/run_bot.sh` 기동 로그에서 당일 runtime env 파일 source 여부를 확인한다.
6. 스윙은 dry-run 기본값을 유지한다. 장전에는 주문 guard를 완화하거나 `SWING_LIVE_ORDER_DRY_RUN_ENABLED`를 임의로 끄지 않는다.
7. 실패 시 수동 approve가 아니라 `safety_revert_required`, `hold_sample`, `hold_no_edge`, `AI instrumentation_gap/incident`, same-stage owner 충돌 중 어느 차단인지 판정한다.

표준 확인 명령:

```bash
tail -n 80 logs/threshold_cycle_preopen_cron.log
tail -n 80 logs/ensemble_scanner.log
ls -l data/daily_recommendations_v2.csv data/daily_recommendations_v2_diagnostics.json
ls -l data/threshold_cycle/apply_plans/threshold_apply_$(TZ=Asia/Seoul date +%F).json
ls -l data/threshold_cycle/runtime_env/threshold_runtime_env_$(TZ=Asia/Seoul date +%F).json
tmux ls
```

## 장중 확인 절차

`build_codex_daily_workorder --slot INTRADAY`는 이 절차를 `IntradayAutomationHealthCheckYYYYMMDD`로 자동 포함한다.

1. Sentinel은 상태 확인용이다. BUY/HOLD-EXIT 이상치가 보여도 runtime threshold를 바꾸지 않는다.
2. `12:05` 장중 calibration은 anomaly correction 후보와 source freshness만 확인한다.
3. `pipeline_events_YYYY-MM-DD.jsonl`와 `threshold_events_YYYY-MM-DD.jsonl` append가 멈추지 않았는지 확인한다.
4. 스윙 dry-run은 실전 판단 흐름 관찰용이다. `swing_sim_*`, `swing_entry_micro_context_observed`, `swing_scale_in_micro_context_observed`, `holding_flow_ofi_smoothing_applied`가 보이면 주문 제출 여부와 별도로 provenance만 본다.
5. `RUNTIME_OPS`, snapshot failure, model call timeout, 주문 receipt/provenance 손상이 있으면 전략 threshold 문제가 아니라 운영 장애로 분류한다.
6. safety breach가 아니라 목표 미달이면 rollback이 아니라 postclose calibration 입력으로 넘긴다.

표준 확인 명령:

```bash
tail -n 80 logs/run_buy_funnel_sentinel_cron.log
tail -n 80 logs/run_holding_exit_sentinel_cron.log
tail -n 80 logs/threshold_cycle_calibration_intraday_cron.log
ls -l data/pipeline_events/pipeline_events_$(TZ=Asia/Seoul date +%F).jsonl
ls -l data/threshold_cycle/threshold_events_$(TZ=Asia/Seoul date +%F).jsonl
ls -l data/report/threshold_cycle_ai_review/threshold_cycle_ai_review_$(TZ=Asia/Seoul date +%F)_intraday.md
```

## 장후 확인 절차

`build_codex_daily_workorder --slot POSTCLOSE`는 이 절차를 `PostcloseAutomationHealthCheckYYYYMMDD`로 자동 포함한다.

1. `threshold_cycle_postclose`가 완료됐는지 먼저 확인한다.
2. 제출 기준은 `data/report/threshold_cycle_ev/threshold_cycle_ev_YYYY-MM-DD.md`다.
3. threshold 후보의 상세 원인은 `threshold_cycle_YYYY-MM-DD.json`, AI correction은 `threshold_cycle_ai_review_*_postclose.md`, lab order는 `scalping_pattern_lab_automation_YYYY-MM-DD.md`, 스윙 lifecycle order는 `swing_improvement_automation_YYYY-MM-DD.json`을 본다.
4. 스윙 postclose는 `recommendation_db_load`, `scale_in_observation`, `ai_contract_metrics`, `ofi_qi_summary`, `runtime_effect=false`, `allowed_runtime_apply=false`를 확인한다.
5. DeepSeek 스윙 lab re-entry는 `run_manifest.json`의 `analysis_window.start == target_date == end`와 필수 JSON schema 유효성이 닫힌 경우에만 fresh로 본다. stale/range/malformed output은 warning만 남기고 order로 승격하지 않는다.
6. 신규 code improvement order는 scalping/swing source를 병합해 자동으로 작업지시서로 변환된다. 사용자는 `docs/code-improvement-workorders/code_improvement_workorder_YYYY-MM-DD.md`를 Codex 세션에 넣고 구현을 요청한다.
7. 날짜별 checklist를 수정했다면 parser 검증 후 Project/Calendar 동기화 명령을 사용자에게 남긴다.
8. OpenAI AI correction은 품질 우선 `gpt-5.5` 경로라 수 분 단위로 걸릴 수 있다. 2026-05-08 postclose 재측정 기준 `real 744.78s`가 소요됐고, `OPENAI_API_KEY_2`, `gpt-5.5`, `reasoning_effort=high`, `schema_name=threshold_ai_correction_v1`, `ai_status=parsed`로 완료됐다. 15분 이내 실행 중이면 `not_yet_due`, 15분 초과 미생성이면 cron log와 job 종료 여부를 확인해 `warning` 또는 `fail`로 분류한다. cron timeout은 이보다 짧게 잡지 않는다.

표준 확인 명령:

```bash
tail -n 120 logs/threshold_cycle_postclose_cron.log
ls -l data/report/threshold_cycle_ev/threshold_cycle_ev_$(TZ=Asia/Seoul date +%F).md
ls -l data/report/swing_selection_funnel/swing_selection_funnel_$(TZ=Asia/Seoul date +%F).md
ls -l data/report/swing_lifecycle_audit/swing_lifecycle_audit_$(TZ=Asia/Seoul date +%F).md
ls -l data/report/swing_threshold_ai_review/swing_threshold_ai_review_$(TZ=Asia/Seoul date +%F).md
ls -l data/report/swing_improvement_automation/swing_improvement_automation_$(TZ=Asia/Seoul date +%F).json
ls -l data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_$(TZ=Asia/Seoul date +%F).md
ls -l docs/code-improvement-workorders/code_improvement_workorder_$(TZ=Asia/Seoul date +%F).md
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500
```

## 신규 Code Improvement Order 처리 절차

`code_improvement_order`는 pattern lab이 만든 machine-readable 작업지시다. 생성 자체는 runtime 효과가 없으며, repo 파일을 직접 수정하지 않는다. postclose wrapper는 이를 Codex 세션 입력용 Markdown 작업지시서로 자동 변환한다. Codex는 사용자가 명시적으로 요청한 workorder만 구현하고 검증한다. 사람/operator가 남는 지점은 생성된 Markdown을 검토한 뒤 Codex 세션에 넣고 "이 작업지시서를 구현하고 검증해줘"라고 요청할지 결정하는 단계다.

### 1. Intake

입력 artifact:

- `data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_YYYY-MM-DD.json`
- `data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_YYYY-MM-DD.md`
- `data/report/swing_lifecycle_audit/swing_lifecycle_audit_YYYY-MM-DD.md`
- `data/report/swing_threshold_ai_review/swing_threshold_ai_review_YYYY-MM-DD.md`
- `data/report/swing_improvement_automation/swing_improvement_automation_YYYY-MM-DD.json`
- `data/report/threshold_cycle_ev/threshold_cycle_ev_YYYY-MM-DD.md`
- `data/report/code_improvement_workorder/code_improvement_workorder_YYYY-MM-DD.json`
- `docs/code-improvement-workorders/code_improvement_workorder_YYYY-MM-DD.md`

확인 필드:

| 필드 | 의미 | 처리 |
| --- | --- | --- |
| `order_id` | 구현 작업 식별자 | checklist/commit/test 이름에 그대로 보존 |
| `target_subsystem` | 영향 영역 | entry, holding_exit, runtime_instrumentation, report 등으로 owner 분리 |
| `lifecycle_stage` | 스윙/스캘핑 생명주기 단계 | selection, db_load, entry, holding, scale_in, exit, ai_contract 등으로 구분 |
| `threshold_family` | 연결 threshold family | existing family 입력 보강인지 new family 설계인지 판정 |
| `intent` | 개선 목적 | EV 개선, 계측 보강, family 설계 중 무엇인지 분류 |
| `evidence` | Gemini/Claude/EV 근거 | 단일 lab 단독 근거면 priority를 낮추고 runtime 후보 금지 |
| `expected_ev_effect` | 기대 효과 | daily EV의 어떤 metric으로 확인할지 연결 |
| `files_likely_touched` | 예상 변경 파일 | 실제 diff scope의 시작점으로 사용 |
| `acceptance_tests` | 완료 조건 | 구현 전 테스트 계획으로 변환 |
| `runtime_effect` | lab order 자체 runtime 영향 | 항상 `false`여야 하며, `true`면 artifact 오류로 본다 |
| `allowed_runtime_apply` | 자동 runtime 적용 허용 여부 | 신규 family/설계 후보는 `false`여야 하며, `true`면 guard 근거와 registry metadata를 확인 |
| `priority` | 실행 우선순위 | safety/instrumentation > existing family input > new family design 순으로 재정렬 가능 |

수동 생성/재생성 명령:

```bash
TARGET_DATE=$(TZ=Asia/Seoul date +%F)
PYTHONPATH=. .venv/bin/python -m src.engine.build_code_improvement_workorder --date "$TARGET_DATE" --max-orders 12
```

### 2. 승격 판정

`build_code_improvement_workorder`가 각 order를 아래 중 하나로 deterministic 분류한다.

| 판정 | 조건 | 다음 액션 |
| --- | --- | --- |
| `implement_now` | safety, receipt/provenance, report source 누락, 기존 family calibration을 막는 계측 결함 | 생성된 Markdown의 상위 구현 대상으로 배치 |
| `attach_existing_family` | 이미 존재하는 threshold family의 source/input/provenance 보강 | 해당 family report/calibration 테스트와 함께 구현 |
| `design_family_candidate` | 기존 family에 매핑되지 않는 반복 패턴 | `auto_family_candidate.allowed_runtime_apply=false` 유지. registry/metadata/test 설계 후 별도 구현 |
| `defer_evidence` | lab stale, sample 부족, 단일 lab solo finding | EV report warning 또는 next postclose 재평가로 유지 |
| `reject` | fallback 재개, shadow 재개, safety guard 우회, 현재 폐기축 부활 | `rejected_findings` 또는 checklist 판정 메모에 사유만 남김 |

승격 기준:

- `runtime_effect=false`인 order만 intake한다.
- runtime을 바꿀 수 있는 패치는 반드시 기존 `auto_bounded_live` guard 또는 별도 feature flag를 통과해야 한다.
- 새 family는 처음부터 runtime 적용 후보가 아니다. `allowed_runtime_apply=false`로 시작하고, source metric, sample floor, safety guard, target env key, tests가 닫힌 뒤에만 threshold registry에 승격한다.
- `shadow` 재개를 요구하는 order는 현재 원칙과 충돌하므로 그대로 구현하지 않는다. Codex는 이를 `report_only_calibration` 또는 `bounded canary` 설계안으로 번역하고, live enable은 하지 않는다.

### 3. 구현 작업 만들기

구현 착수 시 문서/코드에 남길 최소 정보:

- 원본 `order_id`
- 원본 artifact path와 date
- target subsystem과 touched files
- runtime 영향 여부: `runtime_effect=false`, `report_only`, `feature_flag_off`, `auto_bounded_live_candidate` 중 하나
- acceptance tests
- daily EV에서 확인할 metric

날짜별 checklist에 등록할 때 형식:

```markdown
- [ ] `[OrderId0511] 원본 order title 요약` (`Due: 2026-05-11`, `Slot: POSTCLOSE`, `TimeWindow: HH:MM~HH:MM`, `Track: RuntimeStability`)
  - Source: [scalping_pattern_lab_automation_YYYY-MM-DD.json](/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_YYYY-MM-DD.json)
  - 판정 기준: 원본 `order_id`, `target_subsystem`, `expected_ev_effect`, `acceptance_tests`를 구현 완료 조건으로 사용한다.
  - 범위: runtime 직접 변경 없음 또는 feature flag/auto_bounded_live guard 경유.
  - 다음 액션: 구현, 테스트, postclose EV report에서 metric 확인.
```

기본 운영에서는 위 checklist 등록을 사람이 직접 하지 않는다. generator가 만든 `docs/code-improvement-workorders/code_improvement_workorder_YYYY-MM-DD.md`가 Codex 입력이다. 사용자가 바로 구현을 지시한 경우에는 원본 order id를 final report와 commit message에 남긴다. 단, 미래 재확인이나 특정 시각 검증이 필요하면 날짜별 checklist에 자동 파싱 가능한 항목으로 남긴다.

### 4. 구현과 검증

구현 순서:

1. `files_likely_touched`를 시작점으로 실제 call path를 확인한다.
2. report-only 보강인지 runtime 후보인지 먼저 분리한다.
3. runtime 후보면 feature flag, threshold family metadata, provenance field, safety guard, same-stage owner rule을 같이 닫는다.
4. acceptance tests를 repo 테스트로 변환한다.
5. 관련 문서와 report README/runbook/checklist를 같은 변경 세트로 갱신한다.

필수 검증:

```bash
PYTHONPATH=. .venv/bin/pytest -q <관련 테스트 파일>
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500
git diff --check
```

threshold/postclose 체인에 영향을 주면 추가 검증:

```bash
bash -n deploy/run_threshold_cycle_preopen.sh deploy/run_threshold_cycle_calibration.sh deploy/run_threshold_cycle_postclose.sh
PYTHONPATH=. .venv/bin/pytest -q src/tests/test_daily_threshold_cycle_report.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_threshold_cycle_ev_report.py
```

### 5. 자동화 체인 재투입

구현 완료 후에도 즉시 성과를 단정하지 않는다.

- report/instrumentation order: 다음 `16:10` postclose report와 daily EV에서 source freshness, sample count, warning 감소를 확인한다.
- existing family input 보강: 다음 `12:05` intraday calibration과 `16:10` postclose calibration에서 해당 family의 `calibration_state` 변화를 확인한다.
- new family design: `auto_family_candidate.allowed_runtime_apply=false`를 유지하다가 registry metadata, sample floor, safety guard, tests가 닫힌 뒤에만 `allowed_runtime_apply=true` 후보로 승격한다.
- runtime 후보: 다음 장전 `auto_bounded_live` apply plan에서 selected/blocked reason과 runtime env provenance를 확인한다.

완료 기준:

- 원본 `order_id`가 구현 PR/commit/checklist 판정에 남아 있다.
- acceptance tests가 자동화 테스트 또는 report 검증 명령으로 닫혔다.
- daily EV 또는 postclose artifact에 기대 metric이 나타난다.
- runtime 변경이 있다면 threshold version/family/applied value가 pipeline event 또는 runtime env JSON에서 복원 가능하다.

## 장애 대응 기준

| 증상 | 우선 판정 | 다음 액션 |
| --- | --- | --- |
| preopen runtime env 미생성 | guard 차단 또는 전일 postclose 산출물 누락 | apply plan의 blocked reason 확인 후 postclose 산출물 복구. 수동 env override 금지 |
| intraday AI correction 실패 | AI proposal unavailable | deterministic calibration artifact가 생성됐으면 `warning`으로 기록하고 live runtime은 변경하지 않는다. postclose에서 fallback 상태 확인 |
| OpenAI AI correction 장시간 대기 | 고품질 모델 응답 지연 또는 key/model fallback | 15분 이내 실행 중이면 `not_yet_due`, 15분 초과 미완료면 `warning`으로 기록한다. deterministic calibration artifact가 이미 있으면 runtime 변경 없이 유지하고, 반복 초과 시 provider/timeout 보강 workorder로 분리 |
| postclose threshold report 실패 | 다음 장전 apply 입력 누락 | `logs/threshold_cycle_postclose_cron.log`와 checkpoint 확인 후 같은 date로 wrapper 재실행 |
| Sentinel `RUNTIME_OPS` 반복 | 운영/계측 문제 후보 | snapshot, model latency, receipt/provenance, pipeline event append 상태 확인. threshold 변경으로 처리하지 않음 |
| safety breach 발생 | safety revert 후보 | hard/protect/emergency stop 지연, 주문 실패, provenance 손상, severe loss guard 여부를 daily EV와 checklist에 남김 |
| pattern lab stale | lab freshness 경고 | EV report의 warning으로 관리. runtime family 자동 적용 후보로 승격하지 않음 |

## 동기화 규칙

문서/checklist를 수정했으면 parser 검증은 AI가 실행한다. GitHub Project와 Google Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
