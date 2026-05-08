# Time-Based Operations Runbook

작성 기준: `2026-05-08 KST`
목적: 장전, 장중, 장후 자동화 체인의 시간대별 실행 주체, 산출물, 사람 확인 지점을 한 장으로 고정한다.

이 문서는 실행 절차 runbook이다. 튜닝 원칙과 active owner는 [Plan Rebase](./plan-korStockScanPerformanceOptimization.rebase.md), 날짜별 작업 소유권은 `docs/YYYY-MM-DD-stage2-todo-checklist.md`, threshold 산출물 정의는 [data/threshold_cycle/README.md](../data/threshold_cycle/README.md)를 기준으로 한다.

## 운영 원칙

- 기본 흐름은 무인 자동화다. 사람의 장전 승인 없이 `auto_bounded_live` guard를 통과한 threshold만 runtime env로 반영한다.
- 장중 threshold runtime mutation은 금지한다. 장중 산출물은 다음 장전 apply 후보 입력으로만 쓴다.
- AI correction은 수정안 제안 layer다. 최종 threshold state/value는 deterministic guard가 결정한다.
- Pattern lab은 `code_improvement_order`와 `auto_family_candidate`만 생성한다. runtime/code를 직접 변경하지 않는다.
- Sentinel은 Telegram 알림 기능을 제거한 운영 감시/report-only 축이다. 이상치는 mutation이 아니라 threshold source bundle, incident, instrumentation gap, normal drift로 라우팅한다.
- 사람이 반드시 개입하는 지점은 운영 장애, 생성된 code improvement workorder를 Codex 세션에 넣어 구현을 요청하는 단계, 문서 backlog Project/Calendar 동기화다.
- `build_codex_daily_workorder`는 Project 항목과 별도로 이 runbook의 장전/장중/장후 확인절차를 `Runbook 운영 확인` 블록으로 자동 포함한다. 이 항목은 GitHub Project/Calendar backlog를 늘리지 않는 Codex 실행용 상태 확인 작업이다.

## 시간대별 Runbook

| 시간대 KST | 실행 주체 | 실행/트리거 | 산출물 | 사람 확인 | 금지/주의 |
| --- | --- | --- | --- | --- | --- |
| `07:20` | cron | `final_ensemble_scanner.py` | `logs/ensemble_scanner.log` | 스캐너 실패/빈 결과 여부만 확인 | 스캐너 결과만으로 threshold 수동 변경 금지 |
| `07:30` | cron | 기존 `tmux bot` 세션 종료 | tmux session 상태 | 기존 세션이 남아 있으면 `tmux ls` 확인 | 장중 실행 중 강제 종료 금지 |
| `07:35` | cron | `deploy/run_threshold_cycle_preopen.sh` with `THRESHOLD_CYCLE_APPLY_MODE=auto_bounded_live`, `THRESHOLD_CYCLE_AUTO_APPLY_REQUIRE_AI=true` | `data/threshold_cycle/apply_plans/threshold_apply_YYYY-MM-DD.json`, `data/threshold_cycle/runtime_env/threshold_runtime_env_YYYY-MM-DD.{env,json}`, `logs/threshold_cycle_preopen_cron.log` | 실패 시 apply plan의 `blocked_reason`, AI guard, same-stage owner 충돌 확인 | 실패했다고 수동으로 env 값을 직접 덮어쓰지 않는다 |
| `07:40` | cron | `src/run_bot.sh`를 tmux `bot` 세션에서 실행 | bot runtime log, source된 runtime env echo | `runtime_env` 적용 여부와 봇 기동 여부 확인 | runtime env 파일이 없으면 전일 guard 실패로 보고 원인 확인 |
| `08:00~09:00` | operator/guard | PREOPEN 안정 구간 | 없음 | 필요 시 checklist 상단 `오늘 목적/강제 규칙`과 전일 EV report 확인 | full monitor snapshot build는 wrapper가 차단한다. 새 workorder 없는 live toggle 금지 |
| `09:00~09:05` | runtime | 장 시작 후 실전 이벤트 수집 시작 | `data/pipeline_events/pipeline_events_YYYY-MM-DD.jsonl`, `data/threshold_cycle/threshold_events_YYYY-MM-DD.jsonl` | 봇 연결, 계좌/잔고/주문 가능 상태 확인 | threshold 변경, provider 라우팅 변경 금지 |
| `09:05~15:20` | cron | `deploy/run_buy_funnel_sentinel_intraday.sh` 5분 주기 | `data/report/buy_funnel_sentinel/buy_funnel_sentinel_YYYY-MM-DD.md`, `logs/run_buy_funnel_sentinel_cron.log` | `UPSTREAM_AI_THRESHOLD`, `LATENCY_DROUGHT`, `PRICE_GUARD_DROUGHT`, `RUNTIME_OPS` 추세 확인 | Sentinel 결과로 score/spread/fallback/restart 자동 변경 금지 |
| `09:05~15:30` | cron | `deploy/run_holding_exit_sentinel_intraday.sh` 5분 주기 | `data/report/holding_exit_sentinel/holding_exit_sentinel_YYYY-MM-DD.md`, `logs/run_holding_exit_sentinel_cron.log` | `HOLD_DEFER_DANGER`, `SOFT_STOP_WHIPSAW`, `AI_HOLDING_OPS` 추세 확인 | Sentinel 결과로 자동 매도, threshold mutation, bot restart 금지 |
| `09:30~11:00` | cron | `src.engine.buy_pause_guard evaluate` 5분 주기 | `logs/buy_pause_guard.log` | pause guard 반복 발동 여부 확인 | pause guard를 진입 threshold 튜닝 근거로 단독 사용 금지 |
| `09:35~12:00` | cron | monitor snapshot incremental/full | `data/report/monitor_snapshots/*_YYYY-MM-DD.json`, `logs/run_monitor_snapshot_cron.log` | snapshot failure, async timeout, manifest status 확인 | 장전 full build 차단을 우회하지 않는다 |
| `12:05` | cron | `deploy/run_threshold_cycle_calibration.sh` with `THRESHOLD_CYCLE_AI_CORRECTION_PROVIDER=openai` | `data/report/threshold_cycle_calibration/threshold_cycle_calibration_YYYY-MM-DD_intraday.json`, `data/report/threshold_cycle_ai_review/threshold_cycle_ai_review_YYYY-MM-DD_intraday.{json,md}`, `logs/threshold_cycle_calibration_intraday_cron.log` | `calibration_state`, `safety_revert_required`, `ai_status`, `guard_reject_reason` 확인 | 장중 calibration 결과를 당일 runtime에 적용 금지 |
| `15:00` | cron | `deploy/run_preclose_sell_target_report.sh` | `data/report/preclose_sell_target/preclose_sell_target_YYYY-MM-DD.md`, `logs/preclose_sell_target_cron.log` | operator preclose review 산출 여부 확인 | tuning/calibration source로 사용 금지 |
| `15:20~15:30` | runtime/cron | 오버나이트 flow, HOLD/EXIT sentinel final window | pipeline events, holding sentinel | `SELL_TODAY`, `HOLD_OVERNIGHT`, force-exit/safety 이벤트 확인 | flow `TRIM`을 부분청산 구현 없이 HOLD로 해석 금지 |
| `16:10` | cron | `deploy/run_threshold_cycle_postclose.sh` with OpenAI correction | threshold partition, `threshold_cycle_YYYY-MM-DD.json`, `statistical_action_weight`, `holding_exit_decision_matrix`, `threshold_cycle_cumulative`, postclose AI review, pattern lab automation, code improvement workorder, daily EV report | `logs/threshold_cycle_postclose_cron.log`, `threshold_cycle_ev_YYYY-MM-DD.md`, `docs/code-improvement-workorders/code_improvement_workorder_YYYY-MM-DD.md` 확인 | postclose 실패 시 다음 장전 auto apply 입력이 부정확하므로 먼저 재실행/복구 |
| `18:00` | cron | `deploy/run_tuning_monitoring_postclose.sh` | Parquet/DuckDB refresh status, `data/report/tuning_monitoring/status/*` | `canonical_runner=THRESHOLD_CYCLE_POSTCLOSE`인지 확인 | pattern lab 중복 실행 금지 |
| `21:00` | cron | `update_kospi.py` | `logs/update_kospi.log` | 데이터 업데이트 실패 여부 확인 | 매매 runtime과 무관한 데이터 갱신으로 취급 |
| `22:30` | cron | `eod_analyzer.py` | `logs/eod_analyzer.log` | EOD 분석 실패 여부 확인 | threshold daily EV를 대체하지 않는다 |
| `22:55` | cron | 봇 tmux 세션 종료 | tmux session 상태 | 장 종료 후 잔여 세션 확인 | 장중 세션 종료와 혼동 금지 |
| `23:10` | cron | dashboard DB archive | `logs/dashboard_db_archive_cron.log` | archive skipped/error 확인 | 미검증 파일 강제 삭제 금지 |
| `23:20` | cron | log rotation cleanup | `logs/log_rotation_cleanup_cron.log` | deleted/size 추세 확인 | 당일 장애 분석 전 로그 수동 삭제 금지 |

## 장전 확인 절차

`build_codex_daily_workorder --slot PREOPEN`은 이 절차를 `PreopenAutomationHealthCheckYYYYMMDD`로 자동 포함한다.

1. `logs/threshold_cycle_preopen_cron.log`에서 preopen apply가 완료됐는지 확인한다.
2. `data/threshold_cycle/apply_plans/threshold_apply_YYYY-MM-DD.json`에서 selected family와 blocked family를 본다.
3. `data/threshold_cycle/runtime_env/threshold_runtime_env_YYYY-MM-DD.json`이 있으면 `runtime_change=true` family와 env key를 확인한다.
4. `src/run_bot.sh` 기동 로그에서 당일 runtime env 파일 source 여부를 확인한다.
5. 실패 시 수동 approve가 아니라 `safety_revert_required`, `hold_sample`, `hold_no_edge`, `AI instrumentation_gap/incident`, same-stage owner 충돌 중 어느 차단인지 확인한다.

표준 확인 명령:

```bash
tail -n 80 logs/threshold_cycle_preopen_cron.log
ls -l data/threshold_cycle/apply_plans/threshold_apply_$(TZ=Asia/Seoul date +%F).json
ls -l data/threshold_cycle/runtime_env/threshold_runtime_env_$(TZ=Asia/Seoul date +%F).json
tmux ls
```

## 장중 확인 절차

`build_codex_daily_workorder --slot INTRADAY`는 이 절차를 `IntradayAutomationHealthCheckYYYYMMDD`로 자동 포함한다.

1. Sentinel은 상태 확인용이다. BUY/HOLD-EXIT 이상치가 보여도 runtime threshold를 바꾸지 않는다.
2. `12:05` 장중 calibration은 anomaly correction 후보와 source freshness만 확인한다.
3. 운영 장애가 의심되면 `RUNTIME_OPS`, snapshot failure, model call timeout, 주문 receipt/provenance 손상 여부를 먼저 본다.
4. safety breach가 아니라 목표 미달이면 rollback이 아니라 postclose calibration 입력으로 넘긴다.

표준 확인 명령:

```bash
tail -n 80 logs/run_buy_funnel_sentinel_cron.log
tail -n 80 logs/run_holding_exit_sentinel_cron.log
tail -n 80 logs/threshold_cycle_calibration_intraday_cron.log
ls -l data/report/threshold_cycle_ai_review/threshold_cycle_ai_review_$(TZ=Asia/Seoul date +%F)_intraday.md
```

## 장후 확인 절차

`build_codex_daily_workorder --slot POSTCLOSE`는 이 절차를 `PostcloseAutomationHealthCheckYYYYMMDD`로 자동 포함한다.

1. `threshold_cycle_postclose`가 완료됐는지 먼저 확인한다.
2. 제출 기준은 `data/report/threshold_cycle_ev/threshold_cycle_ev_YYYY-MM-DD.md`다.
3. threshold 후보의 상세 원인은 `threshold_cycle_YYYY-MM-DD.json`, AI correction은 `threshold_cycle_ai_review_*_postclose.md`, lab order는 `scalping_pattern_lab_automation_YYYY-MM-DD.md`를 본다.
4. 신규 code improvement order는 자동으로 작업지시서로 변환된다. 사용자는 `docs/code-improvement-workorders/code_improvement_workorder_YYYY-MM-DD.md`를 Codex 세션에 넣고 구현을 요청한다.
5. 날짜별 checklist를 수정했다면 parser 검증 후 Project/Calendar 동기화 명령을 사용자에게 남긴다.
6. OpenAI AI correction은 품질 우선 `gpt-5.5` 경로라 수 분 단위로 걸릴 수 있다. 2026-05-08 postclose 재측정 기준 `real 744.78s`가 소요됐고, `OPENAI_API_KEY_2`, `gpt-5.5`, `reasoning_effort=high`, `schema_name=threshold_ai_correction_v1`, `ai_status=parsed`로 완료됐다. cron timeout은 이보다 짧게 잡지 않는다.

표준 확인 명령:

```bash
tail -n 120 logs/threshold_cycle_postclose_cron.log
ls -l data/report/threshold_cycle_ev/threshold_cycle_ev_$(TZ=Asia/Seoul date +%F).md
ls -l data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_$(TZ=Asia/Seoul date +%F).md
ls -l docs/code-improvement-workorders/code_improvement_workorder_$(TZ=Asia/Seoul date +%F).md
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500
```

## 신규 Code Improvement Order 처리 절차

`code_improvement_order`는 pattern lab이 만든 machine-readable 작업지시다. 생성 자체는 runtime 효과가 없으며, repo 파일을 직접 수정하지 않는다. postclose wrapper는 이를 Codex 세션 입력용 Markdown 작업지시서로 자동 변환한다. 사람이 남는 지점은 생성된 Markdown을 Codex 세션에 넣고 "이 작업지시서를 구현하고 검증해줘"라고 요청하는 단계다.

### 1. Intake

입력 artifact:

- `data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_YYYY-MM-DD.json`
- `data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_YYYY-MM-DD.md`
- `data/report/threshold_cycle_ev/threshold_cycle_ev_YYYY-MM-DD.md`
- `data/report/code_improvement_workorder/code_improvement_workorder_YYYY-MM-DD.json`
- `docs/code-improvement-workorders/code_improvement_workorder_YYYY-MM-DD.md`

확인 필드:

| 필드 | 의미 | 처리 |
| --- | --- | --- |
| `order_id` | 구현 작업 식별자 | checklist/commit/test 이름에 그대로 보존 |
| `target_subsystem` | 영향 영역 | entry, holding_exit, runtime_instrumentation, report 등으로 owner 분리 |
| `intent` | 개선 목적 | EV 개선, 계측 보강, family 설계 중 무엇인지 분류 |
| `evidence` | Gemini/Claude/EV 근거 | 단일 lab 단독 근거면 priority를 낮추고 runtime 후보 금지 |
| `expected_ev_effect` | 기대 효과 | daily EV의 어떤 metric으로 확인할지 연결 |
| `files_likely_touched` | 예상 변경 파일 | 실제 diff scope의 시작점으로 사용 |
| `acceptance_tests` | 완료 조건 | 구현 전 테스트 계획으로 변환 |
| `runtime_effect` | lab order 자체 runtime 영향 | 항상 `false`여야 하며, `true`면 artifact 오류로 본다 |
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
- `shadow` 재개를 요구하는 order는 현재 원칙과 충돌하므로 그대로 구현하지 않는다. 필요한 경우 `report_only_calibration` 또는 `bounded canary` 설계로 번역한다.

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
| intraday AI correction 실패 | AI proposal unavailable | deterministic calibration artifact가 생성됐으면 운영 지속. postclose에서 fallback 상태 확인 |
| OpenAI AI correction 장시간 대기 | 고품질 모델 응답 지연 또는 key/model fallback | 15분 이상 완료 여부를 먼저 확인한다. deterministic calibration artifact가 이미 있으면 runtime 변경 없이 운영 지속하고, 반복 초과 시 provider/timeout 보강 workorder로 분리 |
| postclose threshold report 실패 | 다음 장전 apply 입력 누락 | `logs/threshold_cycle_postclose_cron.log`와 checkpoint 확인 후 같은 date로 wrapper 재실행 |
| Sentinel `RUNTIME_OPS` 반복 | 운영/계측 문제 후보 | snapshot, model latency, receipt/provenance, pipeline event append 상태 확인. threshold 변경으로 처리하지 않음 |
| safety breach 발생 | safety revert 후보 | hard/protect/emergency stop 지연, 주문 실패, provenance 손상, severe loss guard 여부를 daily EV와 checklist에 남김 |
| pattern lab stale | lab freshness 경고 | EV report의 warning으로 관리. runtime family 자동 적용 후보로 승격하지 않음 |

## 동기화 규칙

문서/checklist를 수정했으면 parser 검증은 AI가 실행한다. GitHub Project와 Google Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
