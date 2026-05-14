# KORStockScan

KORStockScan은 키움 REST/WebSocket 기반 한국 주식 자동매매 엔진과 장중/장후 리포트, threshold 자동 튜닝, 스캘핑/스윙 시뮬레이션, 운영 감시를 하나의 자동화체인으로 묶은 프로젝트입니다.

업데이트 기준: `2026-05-14 KST`

## 현재 운영 목표

현재 목표는 손실 억제형 미세조정이 아니라 `기대값/순이익 극대화`입니다. 전략 판단은 `main-only`, `normal_only`, `post_fallback_deprecation` 기준으로 보고, 손익은 `COMPLETED + valid profit_rate`만 사용합니다. `NULL`, 미완료, fallback 정규화 값은 손익 기준에서 제외합니다.

승률은 보조 진단(`diagnostic_win_rate`)이고, 적용/승격의 primary 판단은 EV입니다. EV 필드는 `equal_weight_avg_profit_pct`, `notional_weighted_ev_pct`, `source_quality_adjusted_ev_pct`처럼 명시적으로 구분합니다. `simple_sum_profit_pct`는 EV로 취급하지 않습니다.

현재 기준 문서는 [Plan Rebase](docs/plan-korStockScanPerformanceOptimization.rebase.md)입니다. 실행 작업과 Due/Slot/TimeWindow/Track은 날짜별 `docs/YYYY-MM-DD-stage2-todo-checklist.md`가 소유합니다.

## 운영 원칙

- 장중 runtime threshold mutation은 금지합니다. 적용은 장후 리포트와 다음 장전 runtime env를 통해서만 이뤄집니다.
- 실전 변경은 같은 단계 내 단일 owner canary를 기본으로 합니다. stage, 조작점, cohort tag, rollback guard가 분리된 경우에만 병렬 canary를 허용합니다.
- sim/probe/counterfactual은 source bundle과 approval request 근거가 될 수 있지만, real execution 품질이나 실주문 전환 근거로 단독 사용하지 않습니다.
- Sentinel, panic sell/buying, system error detector는 report-only/source-quality/incident 입력입니다. approval artifact와 rollback guard 없이 주문, 청산, threshold, provider, bot 상태를 직접 바꾸지 않습니다.
- code-improvement workorder는 자동 repo 수정이 아니라 Codex 구현 지시 입력입니다.

## 시스템 구성

1. 스캐너와 조건검색식이 WATCHING 후보를 생성합니다.
2. 실시간 시세, 호가, 체결강도, 수급, AI 판단을 묶어 entry 후보를 평가합니다.
3. latency, 가격품질, 유동성, AI score, 과열/overbought gate를 통과한 후보만 주문 또는 sim/probe 경로로 넘어갑니다.
4. 주문/체결 receipt와 position tag를 기준으로 `BUY_ORDERED`, `HOLDING`, `SELL_ORDERED`, `COMPLETED` 상태를 관리합니다.
5. 보유 중에는 hard/protect/emergency stop, soft stop, trailing, holding-flow AI review, scale-in/pyramid, bad-entry, overnight gate를 분리 판단합니다.
6. 장중/장후 pipeline event, threshold compact event, monitor snapshot, Sentinel, panic report, swing lifecycle audit를 source bundle로 모읍니다.
7. threshold-cycle 자동화체인이 다음 장전 적용 후보와 code-improvement workorder, approval summary를 생성합니다.

## 주요 기능

- 키움 REST/WebSocket 기반 실시간 시세, 주문, 체결, 잔고 처리.
- 스캘핑 WATCHING/HOLDING/SELL 상태머신과 주문 receipt 정합성 관리.
- OpenAI 중심 live AI route와 provider transport/provenance 분리.
- 실시간 pipeline event JSONL과 threshold compact event stream.
- entry funnel, holding/exit, performance tuning, post-sell feedback, missed-entry counterfactual 리포트.
- threshold cycle 장중/장후 calibration, AI correction guard, 장전 `auto_bounded_live` runtime env apply.
- 스캘핑 pattern lab과 code-improvement workorder 자동 생성.
- 스윙 추천, selection funnel, dry-run lifecycle audit, threshold AI review, improvement automation, runtime approval request.
- 패닉셀/패닉바잉 risk-regime report-only source bundle.
- System Error Detector 기반 process, cron, log, artifact, resource, stale-lock 운영 감시.
- 웹 대시보드와 JSON API.
- GitHub Project와 Google Calendar 동기화용 문서 backlog parser.

## 자동화체인

KORStockScan의 중심 루프는 아래 R0~R6 체인입니다.

| 단계 | 역할 | live 영향 |
| --- | --- | --- |
| `R0_collect` | pipeline event, threshold compact event, DB completed trade, monitor snapshot 수집 | 없음 |
| `R1_daily_report` | Sentinel, panic, threshold, swing, system report 생성 | 없음 |
| `R2_cumulative_report` | rolling/cumulative cohort와 owner baseline 생성 | 없음 |
| `R3_manifest_only` | 후보 family와 source bundle 생성, env 미반영 | 없음 |
| `R4_preopen_apply_candidate` | deterministic guard, AI correction, source-quality, same-stage owner rule 확인 | 직접 변경 전 단계 |
| `R5_bounded_calibrated_apply` | guard 통과 family만 다음 장전 runtime env에 반영 | 있음 |
| `R6_post_apply_attribution` | selected/applied/not-applied cohort, daily EV, approval summary 생성 | 없음 |

자동화체인은 새 관찰축을 무한히 늘리는 방식이 아니라 기존 source bundle을 재사용합니다. BUY 쪽은 `buy_funnel_sentinel`, `wait6579_ev_cohort`, `missed_entry_counterfactual`, `performance_tuning`; 보유/청산 쪽은 `holding_exit_observation`, `post_sell_feedback`, `trade_review`, `holding_exit_sentinel`; 패닉 쪽은 `panic_sell_defense`, `panic_buying`; decision-support 쪽은 `holding_exit_decision_matrix`, `statistical_action_weight`를 우선 source로 사용합니다.

## 튜닝과 적용 방식

| 영역 | 현재 특징 |
| --- | --- |
| entry 판단 | score 50 fallback/neutral은 신규 BUY 제출로 내려보내지 않고 `blocked_ai_score`로 보류합니다. selected runtime family는 다음 장전 `auto_bounded_live` guard를 통과한 env만 인정합니다. |
| entry price | `dynamic_entry_price_resolver_p1`과 `dynamic_entry_ai_price_canary_p2`가 entry price 품질을 담당합니다. stale quote, spread, passive probe 가격품질 문제는 broker 제출 전 차단합니다. |
| holding/exit | `soft_stop_micro_grace`, `soft_stop_whipsaw_confirmation`, `holding_flow_override` 계열은 hard/protect/emergency/order safety를 우회하지 않습니다. |
| scale-in/position sizing | scale-in price resolver와 dynamic qty safety를 유지합니다. 신규/추가매수 1주 cap 해제는 `position_sizing_cap_release` approval request 이후 사용자 승인으로만 다룹니다. |
| statistical decision support | `statistical_action_weight`와 `holding_exit_decision_matrix`는 advisory/calibration 입력입니다. 자체로 runtime을 바꾸지 않습니다. |
| panic lifecycle | `panic_regime_mode`와 `panic_buy_regime_mode`는 risk-regime 해석 계층입니다. report/approval source로만 쓰며 approval artifact 전 주문/청산/TP/trailing/threshold 변경 권한이 없습니다. |
| OpenAI route | live 스캘핑 AI route는 OpenAI 고정입니다. transport/provenance 확인은 threshold, 주문가, 수량 guard 변경과 분리합니다. |

## 시뮬레이션과 Probe

실주문 가능 여부, 예수금, 1주 cap, 현재 selected family 여부는 sim/probe 후보 제외 사유가 아닙니다. 대신 provenance로 남겨 real/sim/combined를 분리합니다.

| 축 | 설명 | 금지선 |
| --- | --- | --- |
| `scalp_ai_buy_all` | 스캘핑 BUY 후보를 실주문 없이 lifecycle로 추적하는 sim-first 관찰축 | real execution 품질이나 실주문 전환 근거로 단독 사용 금지 |
| missed-entry counterfactual | latency, liquidity, AI threshold, overbought gate miss를 분리 관찰 | 실제 체결 손익과 합산 금지 |
| swing dry-run | 스윙 추천부터 entry, holding, scale-in, exit, attribution까지 dry-run으로 실행 | approval artifact 없는 실주문 전환 금지 |
| swing live-equivalent probe | blocked candidate도 `actual_order_submitted=false` virtual holding으로 관찰 | broker order 품질로 해석 금지 |
| panic sell/buying counterfactual | 패닉셀 방어, 패닉바잉 runner TP 가능성을 source bundle에 고정 | 자동매도, 추격매수, TP/trailing 변경 금지 |

## 패닉셀/패닉바잉 Risk Regime

패닉 신호는 현재 매매 로직을 즉시 덮어쓰는 alpha signal이 아닙니다. risk-regime 상태를 report-only로 분리해 다음 workorder, approval request, runtime approval summary에 전달합니다.

| report | mode | 1차 후보 |
| --- | --- | --- |
| `panic_sell_defense` | `NORMAL -> PANIC_DETECTED -> STABILIZING -> RECOVERY_CONFIRMED` | `panic_entry_freeze_guard`, scalping `entry_pre_submit` 신규 BUY 차단 후보 |
| `panic_buying` | `NORMAL -> PANIC_BUY_DETECTED -> PANIC_BUY_CONTINUATION -> PANIC_BUY_EXHAUSTION -> COOLDOWN` | `panic_buy_runner_tp_canary`, 기존 보유분 TP/runner 후보 |

미체결 진입 주문 cancel, holding/exit panic context, 강제 축소/청산, 추격매수 차단, continuation trailing, exhaustion cleanup, cooldown reentry guard는 각각 별도 owner, approval artifact, rollback guard가 필요합니다.

## 스윙 자동화

스윙은 dry-run self-improvement 체인입니다. `selection -> db_load -> entry -> holding -> scale_in -> exit -> attribution` lifecycle을 장후 감사하고, 승인 요청은 만들 수 있지만 별도 approval artifact 없이는 runtime env/live order 전환으로 보지 않습니다.

주요 산출물:

- `swing_selection_funnel`
- `swing_daily_simulation`
- `swing_lifecycle_audit`
- `swing_threshold_ai_review`
- `swing_improvement_automation`
- `swing_runtime_approval`
- `swing_pattern_lab_automation`

스윙 one-share real canary와 scale-in real canary는 별도 approval-required 축입니다. 전체 스윙 실주문 전환으로 해석하지 않습니다.

## 코드 구조

```text
KORStockScan/
├── src/
│   ├── bot_main.py                         # 운영 루프, 봇 진입점
│   ├── run_bot.sh                          # runtime env source 후 봇 실행
│   ├── engine/                             # 매매 엔진, AI, 리포트, 자동화 CLI
│   ├── trading/                            # entry/orderbook 관련 로직
│   ├── scanners/                           # 스캐너, 장전/장후 후보 분석
│   ├── web/                                # Flask 대시보드/API
│   ├── database/                           # DB manager와 모델
│   ├── model/                              # ML dataset/training/recommendation
│   ├── market_regime/                      # 시장 레짐 데이터/룰/서비스
│   ├── notify/                             # Telegram 등 알림
│   ├── utils/                              # constants, runtime flags, event logger
│   └── tests/                              # pytest 회귀 테스트
├── analysis/                               # offline bundle, pattern lab, 관찰 분석
├── data/
│   ├── pipeline_events/                    # runtime pipeline event JSONL
│   ├── threshold_cycle/                    # compact stream, apply plan, runtime env
│   ├── report/                             # daily/monitor/threshold/swing 리포트
│   ├── runtime/                            # runtime flag/state artifacts
│   └── config/                             # feature/threshold manifest
├── deploy/                                 # cron, systemd, nginx, 운영 wrapper
├── docs/                                   # Plan Rebase, checklist, workorder, runbook
└── logs/                                   # 운영 로그
```

## 핵심 모듈

| 모듈 | 역할 |
| --- | --- |
| `src/bot_main.py` | 메인 운영 루프 |
| `src/engine/kiwoom_sniper_v2.py` | 스캘핑 엔진 본체와 Kiwoom runtime orchestration |
| `src/engine/sniper_state_handlers.py` | WATCHING/HOLDING/SELL 상태 처리 |
| `src/engine/sniper_entry_latency.py` | latency gate, entry price guard |
| `src/engine/sniper_scale_in.py` | REVERSAL_ADD, PYRAMID, scale-in blocker와 attribution |
| `src/engine/sniper_execution_receipts.py` | 주문/체결 receipt binding |
| `src/engine/ai_engine_openai.py` | OpenAI schema, transport, Responses WS 경로 |
| `src/engine/daily_threshold_cycle_report.py` | threshold source bundle과 calibration report 생성 |
| `src/engine/threshold_cycle_preopen_apply.py` | 장전 apply plan과 runtime env 생성 |
| `src/engine/threshold_cycle_ev_report.py` | daily EV와 post-apply attribution |
| `src/engine/panic_sell_defense_report.py` | 패닉셀 report-only risk-regime source |
| `src/engine/panic_buying_report.py` | 패닉바잉 report-only risk-regime source |
| `src/engine/runtime_approval_summary.py` | 스캘핑/스윙/패닉 approval 상태 요약 |
| `src/engine/build_code_improvement_workorder.py` | 자동화 산출물 기반 code-improvement 작업지시 생성 |
| `src/engine/swing_lifecycle_audit.py` | 스윙 lifecycle audit와 improvement source |
| `src/engine/error_detector.py` | 운영 감시 detector 실행 |
| `src/web/app.py` | Flask dashboard와 JSON API |

## 주요 산출물

| 경로 | 내용 |
| --- | --- |
| `data/pipeline_events/pipeline_events_YYYY-MM-DD.jsonl` | runtime pipeline event stream |
| `data/threshold_cycle/threshold_events_YYYY-MM-DD.jsonl` | threshold compact event stream |
| `data/report/threshold_cycle_YYYY-MM-DD.json` | threshold cycle canonical report |
| `data/report/threshold_cycle_calibration/` | 장중/장후 calibration artifact |
| `data/report/threshold_cycle_ai_review/` | AI correction proposal와 deterministic guard 결과 |
| `data/threshold_cycle/apply_plans/threshold_apply_YYYY-MM-DD.json` | 다음 장전 apply plan |
| `data/threshold_cycle/runtime_env/threshold_runtime_env_YYYY-MM-DD.{env,json}` | guard 통과 runtime env |
| `data/report/threshold_cycle_ev/` | daily EV, selected/applied/not-applied attribution |
| `data/report/runtime_approval_summary/` | runtime approval 상태 요약 |
| `data/report/panic_sell_defense/` | 패닉셀 source bundle |
| `data/report/panic_buying/` | 패닉바잉 source bundle |
| `data/report/swing_*` | 스윙 selection/simulation/lifecycle/approval 산출물 |
| `docs/code-improvement-workorders/` | Codex 구현 지시용 workorder |
| `docs/YYYY-MM-DD-stage2-todo-checklist.md` | 다음 영업일 판정/승인/운영 체크리스트 |
| `data/report/error_detection/` | System Error Detector 결과 |

JSON/JSONL이 canonical data입니다. 사람이 장후 판정에 바로 읽어야 하는 항목만 Markdown report로 별도 생성합니다. report inventory는 [data/report/README.md](data/report/README.md)를 봅니다.

## 운영 자동화

| 자동화 | 경로 | 설명 |
| --- | --- | --- |
| threshold PREOPEN | `deploy/run_threshold_cycle_preopen.sh` | 전일 report/AI correction guard 기반 `auto_bounded_live` apply plan과 runtime env 생성 |
| threshold INTRADAY calibration | `deploy/run_threshold_cycle_calibration.sh` | 장중 calibration/AI correction artifact 생성. runtime mutation 없음 |
| panic sell/buy intraday | `deploy/run_panic_sell_defense_intraday.sh`, `deploy/run_panic_buying_intraday.sh` | 패닉 risk-regime report-only source 생성 |
| swing live dry-run POSTCLOSE | `deploy/run_swing_live_dry_run_report.sh` | 스윙 selection funnel, lifecycle audit, AI review, improvement automation 생성 |
| threshold POSTCLOSE | `deploy/run_threshold_cycle_postclose.sh` | calibration, cumulative, AI review, swing/scalping automation, workorder, daily EV, checklist 생성 |
| tuning monitoring POSTCLOSE | `deploy/run_tuning_monitoring_postclose.sh` | Parquet/DuckDB refresh와 tuning monitoring |
| nightly KOSPI update | `src/utils/update_kospi.py` | 야간 원천 DB 업데이트와 status JSON 생성 |
| monitor snapshot | `deploy/run_monitor_snapshot_safe.sh`, `deploy/run_monitor_snapshot_incremental_cron.sh` | 장중/장후 snapshot 생성 |
| system error detector | `deploy/run_error_detection.sh full` | process/cron/log/artifact/resource/stale-lock 감시 |
| Project/Calendar sync | `src.engine.sync_docs_backlog_to_project`, `src.engine.sync_github_project_calendar` | checklist backlog와 일정 동기화 |

신규 recurring job, report artifact, daemon/thread를 추가하면 detector coverage도 같은 변경 세트에 포함합니다.

## 실행 방법

Python 작업은 프로젝트 `.venv`를 기본으로 사용합니다.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

실거래 설정은 운영 환경의 민감정보 파일과 환경변수에 의존합니다. 민감정보는 공개 저장소에 커밋하지 않습니다.

주요 설정 파일:

- `data/config_prod.json`
- `data/config_sample.json`
- `data/credentials.json`
- `src/utils/constants.py`
- `src/engine/sniper_config.py`

봇 직접 실행:

```bash
PYTHONPATH=. .venv/bin/python src/bot_main.py
```

운영 wrapper:

```bash
cd src
bash run_bot.sh
```

웹/API:

```bash
PYTHONPATH=. .venv/bin/python src/web/app.py
```

기본 바인딩은 `0.0.0.0:5000`입니다. systemd/nginx 운영 설정은 `deploy/systemd/`, `deploy/nginx/`를 봅니다.

## 주요 API

| 경로 | 용도 |
| --- | --- |
| `GET /api/daily-report?date=YYYY-MM-DD` | 일일 리포트 JSON |
| `GET /api/entry-pipeline-flow?date=YYYY-MM-DD&since=HH:MM:SS&top=10` | 진입 퍼널/blocked flow |
| `GET /api/gatekeeper-replay?date=YYYY-MM-DD&code=000000&time=HH:MM:SS` | gatekeeper 판단 복원 |
| `GET /api/performance-tuning?date=YYYY-MM-DD&since=HH:MM:SS` | 튜닝/성과 snapshot |
| `GET /api/post-sell-feedback?date=YYYY-MM-DD` | 매도 후 missed upside/good exit 평가 |
| `GET /api/strategy-performance?date=YYYY-MM-DD` | 전략/포지션 성과 |
| `GET /api/trade-review?date=YYYY-MM-DD&code=000000` | 거래 리뷰 |
| `GET /api/strength-momentum?date=YYYY-MM-DD&since=HH:MM:SS&top=10` | strength/momentum 분석 |

HTML 대시보드 경로는 `/`, `/dashboard`, `/daily-report`, `/entry-pipeline-flow`, `/gatekeeper-replay`, `/performance-tuning`, `/post-sell-feedback`, `/strategy-performance`, `/trade-review`, `/strength-momentum`입니다.

## 테스트와 검증

기본 테스트:

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q
```

문서 checklist parser 검증:

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500
```

Project/Calendar 동기화 표준 명령:

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

운영 감시 dry-run:

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.error_detector --mode full --dry-run
```

## 핵심 문서

| 문서 | 역할 |
| --- | --- |
| [Plan Rebase](docs/plan-korStockScanPerformanceOptimization.rebase.md) | 현재 튜닝 원칙, active/open 상태, 금지선 |
| [Report Automation Traceability](docs/report-based-automation-traceability.md) | R0~R6 ladder, source bundle, metric decision contract |
| [Threshold Cycle README](data/threshold_cycle/README.md) | threshold collector/report/apply plan/runtime env 운영방법 |
| [Time-Based Operations Runbook](docs/time-based-operations-runbook.md) | cron/window별 운영 확인 기준 |
| [Data Report README](data/report/README.md) | 정기 report inventory |
| 날짜별 `stage2-todo-checklist` | 장전/장중/장후 실행 항목과 Project/Calendar 동기화 source |

## 면책

이 프로젝트는 개인 자동매매/리서치 운영 코드입니다. 실계좌 주문, API key, 계좌 권한, 주문가능금액, 세금/수수료, 거래소/브로커 장애는 사용자가 직접 관리해야 합니다. README와 리포트는 투자 조언이 아니며, 실주문 전환은 항상 approval artifact, rollback guard, runtime owner, source-quality gate를 확인한 뒤에만 다룹니다.
