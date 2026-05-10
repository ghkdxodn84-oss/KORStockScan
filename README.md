# KORStockScan

KORStockScan은 키움 REST/WebSocket, 실시간 스캐너, AI 판단, 주문/체결 상태머신, 장후 복기 리포트를 하나의 운영 루프로 묶은 한국 주식 자동매매/튜닝 플랫폼입니다.

업데이트 기준: `2026-05-10 KST`
현재 운영 단계: `Plan Rebase`

## 현재 목표

이 프로젝트의 현재 목표는 손실 억제가 아니라 `기대값/순이익 극대화`입니다. 운영 판단은 `main-only`, `normal_only`, `post_fallback_deprecation` 기준으로 보며, 손익 계산은 `COMPLETED + valid profit_rate`만 사용합니다. `NULL`, 미완료 상태, fallback 정규화 값은 손익 기준에서 제외합니다.

핵심 판정 순서는 `거래수 -> 퍼널 -> blocker -> 체결품질 -> missed_upside -> 손익`입니다. BUY 후 미진입은 `latency guard miss`, `liquidity gate miss`, `AI threshold miss`, `overbought gate miss`로 분리하고, `full fill`과 `partial fill`은 합산하지 않습니다.

현재 기준 문서는 [Plan Rebase](docs/plan-korStockScanPerformanceOptimization.rebase.md)이며, 실제 실행 항목은 날짜별 `docs/YYYY-MM-DD-stage2-todo-checklist.md`가 소유합니다. `2026-05-10` checklist는 없고, 최신 실행표는 [2026-05-11 checklist](docs/2026-05-11-stage2-todo-checklist.md)입니다.

## 시스템 개요

운영 흐름은 아래 파이프라인으로 구성됩니다.

1. 스캐너와 조건검색식이 후보 종목을 생성합니다.
2. 실시간 시세, 호가, 체결강도, 수급, AI 판단을 묶어 WATCHING 후보를 평가합니다.
3. 진입 latency/가격/유동성/AI gate를 통과한 종목만 주문 후보로 넘깁니다.
4. 주문/체결 receipt와 position tag를 기준으로 `BUY_ORDERED`, `HOLDING`, `SELL_ORDERED`, `COMPLETED` 상태를 관리합니다.
5. 보유 중에는 soft stop, trailing, AI holding review, scale-in/pyramid, bad-entry, overnight gate를 분리 판단합니다.
6. 장중/장후 pipeline event, monitor snapshot, threshold report, post-sell feedback으로 복기와 다음 튜닝 owner를 고정합니다.

## 주요 기능

- 키움 REST/WebSocket 기반 실시간 시세, 주문, 체결, 잔고 처리.
- 스캘핑 중심 WATCHING/HOLDING 상태머신과 주문 receipt 정합성 관리.
- Gemini, DeepSeek, OpenAI 라우팅을 포함한 AI 판단 엔진과 endpoint schema contract.
- 실시간 pipeline event JSONL 로깅과 compact threshold event stream.
- entry pipeline, trade review, performance tuning, post-sell feedback, missed-entry counterfactual, holding/exit observation 리포트.
- threshold cycle 장중/장후 calibration, AI correction, 장전 `auto_bounded_live` runtime env apply, daily EV report 자동화.
- Gemini/Claude scalping pattern lab 기반 improvement order와 auto family candidate 자동 생성.
- 스윙 추천 생성, 선정 funnel, live 주문 dry-run, lifecycle audit, threshold AI proposal review, improvement workorder, runtime approval request 자동화.
- System Error Detector 기반 process/cron/log/artifact/resource/stale-lock 운영 감시와 신규 기능 detector coverage 의무화.
- IPO 상장첫날 YAML-gated runner. 당일 `configs/ipo_listing_day_YYYY-MM-DD.yaml`이 있을 때만 별도 실주문 도구를 실행하며, threshold-cycle/daily EV 입력과 분리합니다.
- GitHub Project와 Google Calendar를 문서 checklist에서 동기화하는 운영 자동화.
- 웹 대시보드와 JSON API를 통한 일일 리포트, 진입 퍼널, gatekeeper replay, 성과 튜닝 조회.
- offline bundle 분석 도구로 장중 서버 로그 접근이 제한될 때도 same-slot 판정 가능.

## 현재 튜닝 진행축

현재 live/observe/open 축은 Plan Rebase 기준으로 관리합니다.

| 영역 | 현재 상태 |
| --- | --- |
| Entry operating override | `mechanical_momentum_latency_relief` ON. 5/6 spread cap 완화는 두산 손실 guard 이후 `0.0085`로 rollback됐고, 다음 원인축은 mechanical cap이 아니라 SAFE normal submit 직전 음수 수급/strength fade와 holding flow defer cost로 분리합니다. |
| Entry price | `dynamic_entry_price_resolver_p1` baseline + `dynamic_entry_ai_price_canary_p2` active canary. `target_buy_price`는 참고 기준가로만 쓰고, P2는 submitted 직전 AI가 `USE_DEFENSIVE`, `USE_REFERENCE`, `IMPROVE_LIMIT`, `SKIP` 중 하나를 선택합니다. `WAIT+score>=75+DANGER+USE_DEFENSIVE`는 passive probe lifecycle로 태그합니다. |
| Orderbook micro | OFI/QI는 P2 내부 입력 feature입니다. standalone hard gate나 watching/holding/exit 확장은 별도 workorder 없이 금지합니다. 5/11 후속은 `performance_tuning` Markdown stale guard와 SAW-6 orderbook context처럼 자동화체인 입력 품질 보강으로만 진행합니다. |
| Holding/exit | 현재 live owner는 `soft_stop_micro_grace`, `REVERSAL_ADD`, `holding_flow_override`입니다. `bad_entry_refined_canary`는 5/4 장후 OFF이며 report-only counterfactual로만 남깁니다. `soft_stop_whipsaw_confirmation`은 bounded apply 후보, `trailing_continuation`은 freeze/report-only입니다. |
| Position sizing | 신규 BUY, wait6579 probe, REVERSAL_ADD/AVG_DOWN, PYRAMID의 1주 수량 cap은 2026-05-09 후속 사용자 지시로 기본 ON입니다. 해제는 `position_sizing_cap_release` 기준이 daily EV/calibration에서 충족될 때 사용자 승인 요청으로만 승격하며, 자동 runtime apply는 하지 않습니다. |
| Scalping live simulator | `SCALP_LIVE_SIMULATOR_ENABLED=True`가 기본입니다. 스캘핑 AI/Gatekeeper BUY 확정 지점에서 종목당 1개 `scalp_ai_buy_all` sim 포지션을 만들고, Kiwoom WS는 유지하되 브로커 매수/매도/추가매수 접수는 차단합니다. `scalp_sim_*` completed rows는 real/sim/combined로 분리 표시하며 combined를 threshold-cycle/daily EV 튜닝 입력에 동급 반영합니다. |
| Swing lifecycle | 스윙 추천 floor는 상승장 `0.35`/하락장 `0.40`이며 fallback diagnostic 후보는 실전 후보와 분리합니다. `SWING_LIVE_ORDER_DRY_RUN_ENABLED=True`가 기본이라 장중 gatekeeper/market regime/budget/holding/exit 로직은 그대로 실행하고 실제 브로커 주문 접수만 차단합니다. 장후 `swing_lifecycle_audit`, `swing_threshold_ai_review`, `swing_improvement_automation`, `swing_runtime_approval`이 선정-진입-보유-추가매수-청산 전체 개선 후보와 EV trade-off 승인 요청을 생성합니다. 승인된 항목이 runtime env로 반영되어도 dry-run과 주문 차단은 유지됩니다. |
| Swing ML retrain | 스윙 ML v2 재학습은 `auto_retrain_pipeline.sh`가 진단, 상승장 특화모델 적용/기간 검토, staging 학습, 평가, 모델 artifact 승격/rollback을 수행합니다. `bull_specialist_mode=disabled`일 때도 `bx/bl`은 `hx/hl`로 중립화해 `META_FEATURES` schema를 유지합니다. 자동 승격은 모델 artifact 교체만 뜻하며 스윙 실주문 전환은 하지 않습니다. |
| Swing v2 feature lineage | `daily_stock_quotes`의 raw OHLCV/수급/신용 컬럼을 원천으로 보고, feature 계산 SSOT는 `src.model.common_v2.calculate_all_features`입니다. 이 facade는 `feature_engineering_v2.calculate_all_features`를 노출하며, nightly DB update, training panel, scanner/runtime scoring은 같은 feature contract를 사용합니다. |
| Swing 1-share real canary | 스윙 sim/combined가 볼 수 없는 broker execution 품질 수집을 위해 별도 approval-required 축으로 둡니다. 전체 dry-run 해제가 아니라 승인된 극소수 후보에만 `qty=1` 실제 BUY/SELL을 허용하는 phase0 계획이며, `max_new_entries_per_day=1`, `max_open_positions=3`, `max_total_notional_krw=300000`, phase0 scale-in 실주문 금지를 기본 guard로 둡니다. |
| AI engine | Gemini/DeepSeek/OpenAI 개선은 live routing 승격이 아니라 flag-off acceptance, endpoint schema contract, transport provenance로 관리합니다. OpenAI threshold AI correction은 runtime routing과 분리된 proposal layer이며 strict JSON schema와 deterministic guard가 최종 적용권을 분리합니다. |
| Threshold/action weight | threshold cycle 기본 apply mode는 완전 무인 `auto_bounded_live`입니다. deterministic guard + AI correction guard + same-stage owner rule을 통과한 family만 다음 장전 runtime env로 자동 반영합니다. 장중 runtime threshold mutation은 금지합니다. `statistical_action_weight`와 `holding_exit_decision_matrix`는 자체로 runtime을 바꾸지 않고 advisory/calibration 입력으로만 연결됩니다. |
| System error detector | 운영 감시는 `process_health`, `cron_completion`, `log_scanner`, `artifact_freshness`, `resource_usage`, `stale_lock` 6개 detector가 담당합니다. 신규 recurring runtime, cron wrapper, report artifact, daemon/thread를 추가하면 detector coverage를 같은 변경 세트에 반드시 선언해야 합니다. detector fail은 incident/instrumentation/code bug 분류 입력이며 threshold/spread/order guard를 자동 변경하지 않습니다. |
| Runtime/report 품질 | NaN cast guard, execution receipt binding, threshold collector IO, `exit_decision_source` provenance, OFI/QI freshness warning을 EV 판정 전제 품질축으로 봅니다. Counterfactual 3-mode는 report-only/설계 only입니다. |

종료/폐기 축은 [closed observation archive](docs/archive/closed-observation-axes-2026-05-01.md)에서만 확인합니다. `fallback_scout/main`, `fallback_single`, `latency fallback split-entry`, 종료된 latency composite 축은 새 workorder와 rollback guard 없이 재개하지 않습니다.

## 코드 구조

```text
KORStockScan/
├── src/
│   ├── bot_main.py                         # 운영 루프, 스케줄, 봇 진입점
│   ├── run_bot.sh                          # 봇 실행 wrapper
│   ├── engine/                             # 매매 엔진, AI, 리포트, 자동화 CLI
│   ├── trading/                            # entry/orderbook 관련 세부 로직
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
│   ├── config/                             # feature/threshold manifest
│   ├── gatekeeper/                         # gatekeeper snapshot JSONL
│   ├── pipeline_events/                    # runtime pipeline event JSONL
│   ├── post_sell/                          # post-sell candidate/evaluation JSONL
│   ├── report/                             # daily/monitor/threshold 리포트
│   ├── ipo_listing_day/                    # IPO 상장첫날 별도 runner 산출물
│   ├── threshold_cycle/                    # threshold compact stream/apply plan
│   └── runtime/                            # runtime flag/state artifacts
├── deploy/                                 # cron, systemd, nginx, 운영 wrapper
├── docs/                                   # Plan Rebase, checklist, workorder, audit, 하위 분류 문서
├── logs/                                   # 운영 로그
└── README.md
```

## 핵심 모듈

| 모듈 | 역할 |
| --- | --- |
| `src/bot_main.py` | 메인 운영 루프, 08:45 daily report, 08:50 추천 브로드캐스트, 23:50 재시작 감지 등 |
| `src/engine/kiwoom_sniper_v2.py` | 스캘핑 엔진 본체와 Kiwoom runtime orchestration |
| `src/engine/sniper_state_handlers.py` | WATCHING/HOLDING/SELL 상태 처리, 청산/보유/flow override 판단 |
| `src/engine/sniper_entry_latency.py` | latency gate, mechanical momentum relief, entry price guard |
| `src/engine/sniper_scale_in.py` | REVERSAL_ADD, PYRAMID, scale-in blocker와 attribution |
| `src/engine/sniper_execution_receipts.py` | 주문/체결 receipt binding, 평균가/상태전이 정합성 |
| `src/engine/ai_engine.py` | 기본 AI endpoint와 Gemini 계열 판단 |
| `src/engine/ai_engine_openai.py` | OpenAI schema/transport parity와 Responses WS shadow 경로 |
| `src/engine/runtime_ai_router.py` | prompt별 provider/model tier routing |
| `src/utils/pipeline_event_logger.py` | runtime event JSONL과 threshold compact event 적재 |
| `src/engine/daily_threshold_cycle_report.py` | threshold report, statistical action weight, holding/exit decision matrix 생성 |
| `src/engine/threshold_cycle_preopen_apply.py` | 장전 threshold apply plan과 bounded runtime env 생성, 현재 기본 `auto_bounded_live` |
| `src/engine/scalping_pattern_lab_automation.py` | Gemini/Claude pattern lab 결과를 기존 family 입력, auto family 후보, code improvement order로 정규화 |
| `src/engine/swing_selection_funnel_report.py` | 스윙 추천 CSV/DB/pipeline event raw count와 unique record funnel 리포트 |
| `src/engine/swing_lifecycle_audit.py` | 스윙 선정-진입-보유-추가매수-청산 lifecycle audit, threshold AI review, improvement automation, runtime approval request |
| `src/engine/swing_daily_simulation_report.py` | 스윙 추천 후보의 runtime dry-run proxy 시뮬레이션 리포트 |
| `src/engine/threshold_cycle_ev_report.py` | 무인 apply 이후 daily EV 성과와 pattern lab automation 요약 제출 |
| `src/engine/error_detector.py` | process/cron/log/artifact/resource/lock detector를 실행하고 `error_detection_YYYY-MM-DD.json`을 생성 |
| `src/engine/error_detector_coverage.py` | 신규 운영 기능의 detector coverage 필수 등록 manifest와 검증 기준 |
| `src/engine/ipo_listing_day_runner.py` | 상장첫날 전용 YAML-gated runner. 별도 state/artifact를 쓰며 threshold-cycle과 분리 |
| `src/engine/sync_docs_backlog_to_project.py` | 날짜별 checklist와 고정 source 문서를 parser로 읽어 Project backlog를 생성 |
| `src/web/app.py` | Flask dashboard와 JSON API |

## 실행 방법

Python 작업은 프로젝트 `.venv`를 기본으로 사용합니다.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

실거래 설정은 아래 파일과 환경변수에 의존합니다. 민감정보는 운영 환경에서만 관리합니다.

- `data/config_prod.json`
- `data/config_sample.json`
- `data/credentials.json`
- `src/utils/constants.py`
- `src/engine/sniper_config.py`

봇 실행:

```bash
PYTHONPATH=. .venv/bin/python src/bot_main.py
```

운영 wrapper:

```bash
cd src
bash run_bot.sh
```

웹/API 실행:

```bash
PYTHONPATH=. .venv/bin/python src/web/app.py
```

기본 바인딩은 `0.0.0.0:5000`입니다. systemd/nginx 운영 설정은 `deploy/systemd/`, `deploy/nginx/`를 봅니다.

## 처음부터 구축하기

이 섹션은 이 저장소를 fork한 뒤 새 서버에서 운영 환경을 처음 만드는 사용자를 위한 최소 경로입니다. 키움과 AI 제공자의 신청 화면/정책은 바뀔 수 있으므로, 실제 신청 전에는 각 공식 문서를 다시 확인합니다.

공식 참조:

- AWS Graviton: <https://aws.amazon.com/ec2/graviton/>
- AWS EC2 On-Demand pricing: <https://aws.amazon.com/ec2/pricing/on-demand/>
- Amazon EBS pricing: <https://aws.amazon.com/ebs/pricing/>
- Amazon VPC pricing: <https://aws.amazon.com/vpc/pricing/>
- EC2 instance launch wizard: <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-launch-instance-wizard.html>
- EC2 Elastic IP: <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/working-with-eips.html>
- Kiwoom REST API: <https://openapi.kiwoom.com/guide/index>
- OpenAI API quickstart: <https://developers.openai.com/api/docs/quickstart>
- OpenAI API pricing: <https://openai.com/ko-KR/api/pricing/>
- OpenAI project/key/budget 관리: <https://help.openai.com/en/articles/9186755-managing-your-work-in-the-api-platform-with-projects>
- Gemini API key: <https://ai.google.dev/gemini-api/docs/api-key>
- DeepSeek API: <https://api-docs.deepseek.com/api/deepseek-api/>
- Anthropic API: <https://docs.anthropic.com/en/api/overview>
- OpenRouter API key: <https://openrouter.ai/docs/api-keys>

### 1. AWS EC2 ARM 서버 생성

신규 운영 서버는 AWS EC2 Graviton ARM 계열을 권장합니다. 이 프로젝트는 장중에는 Python runtime, WebSocket, PostgreSQL, pandas/ML 라이브러리, 리포트 생성이 함께 돌기 때문에 x86보다 Graviton의 가격대비 성능과 전력 효율 이점이 잘 맞습니다. 단, 네이티브 wheel이 없는 라이브러리는 ARM에서 빌드될 수 있으므로 `build-essential`, `python3-dev`, `libpq-dev`를 설치합니다.

권장 시작점:

- 개발/검증: `t4g.medium` 이상
- 단일 서버 운영(PostgreSQL + bot + web): `t4g.large` 또는 `m7g.large` 이상
- AMI: Ubuntu Server LTS `arm64`
- Storage: gp3 EBS `40~80 GiB`에서 시작하고, `data/report`, `data/pipeline_events`, `logs` 증가량에 맞춰 확장
- IP: Kiwoom REST API 허용 IP 등록을 위해 Elastic IP를 할당해 instance에 연결

AWS Console 생성 절차:

1. AWS Console에서 EC2로 이동한 뒤, 운영할 Region을 먼저 고릅니다. Kiwoom 서버와의 지연을 줄이려면 서울 리전(`ap-northeast-2`)을 우선 검토합니다.
2. `Launch instance`를 선택합니다.
3. Name은 예를 들어 `korstockscan-prod-arm`처럼 지정합니다.
4. AMI는 Ubuntu Server LTS의 `64-bit (Arm)` 또는 `arm64` 이미지를 선택합니다.
5. Instance type은 `t4g.medium`, `t4g.large`, `m7g.large` 중 예산과 부하에 맞춰 선택합니다. 처음에는 `t4g.medium`으로 검증하고, 장후 리포트/DB/웹까지 같은 서버에서 돌릴 때 CPU steal, memory, swap, PostgreSQL latency를 보고 올립니다.
6. Key pair를 새로 만들거나 기존 key pair를 선택합니다. `Proceed without a key pair`는 복구 경로가 제한되므로 사용하지 않습니다.
7. Network settings에서 보안 그룹을 새로 만들고 inbound rule은 최소화합니다.
   - SSH `22`: 본인 고정 IP 또는 VPN IP만 허용
   - Web/API `5000`: 외부 공개 금지. 필요하면 본인 IP만 허용하거나 nginx `80/443` 뒤에 둡니다.
   - PostgreSQL `5432`: 같은 서버 안에서만 쓰는 경우 외부 inbound를 열지 않습니다.
8. Storage는 gp3 root volume `40 GiB` 이상으로 시작합니다. 장중 JSONL과 장후 report를 오래 보관하면 더 크게 잡습니다.
9. `Launch instance`로 생성하고, instance가 `running` 상태가 되면 Elastic IP를 allocate 후 해당 instance에 associate합니다. Elastic IP는 할당/연결 상태와 관계없이 비용이 발생할 수 있으므로 미사용 IP는 해제합니다.
10. Kiwoom OpenAPI 사이트의 허용 IP에는 Elastic IP를 등록합니다. public IP가 바뀌면 token/주문 API가 실패할 수 있으므로, 운영 서버를 교체할 때도 Elastic IP 재연결 순서를 먼저 잡습니다.

SSH 접속:

```bash
chmod 600 ~/Downloads/korstockscan-prod-arm.pem
ssh -i ~/Downloads/korstockscan-prod-arm.pem ubuntu@<elastic-ip>
```

#### 월 운영비 추정 (`t4g.large` + OpenAI engine)

기준일은 `2026-05-10 KST`이며, AWS 서울 리전(`ap-northeast-2`) On-Demand Linux, 월 `730`시간, gp3 `80 GiB`, Public IPv4 1개를 기준으로 잡습니다. Savings Plans/Reserved Instance/Free Tier, VAT, 카드 해외결제 수수료, NAT Gateway, snapshot, CloudWatch 추가 과금, 데이터 전송량은 제외합니다. KRW 환산은 예산 감을 잡기 위한 예시로 `1 USD = 1,350 KRW`를 사용합니다.

| 항목 | 산식/가정 | 월 예상 |
| --- | --- | --- |
| EC2 `t4g.large` | `$0.0832/hour * 730h` | `$60.74` |
| EBS gp3 root volume | `$0.0912/GB-month * 80GiB` | `$7.30` |
| Public IPv4/Elastic IP | `$0.005/hour * 730h` | `$3.65` |
| AWS subtotal | EC2 + EBS + IPv4 | `$71.68` |
| OpenAI baseline | 월 `10M` input / `1M` output, `FAST 70% + REPORT 25% + DEEP 5%` | `$5.63` |
| 합계 | AWS subtotal + OpenAI baseline | `$77.31` |

위 baseline의 OpenAI 라우팅은 현재 레포 기준 `FAST=gpt-5-nano`, `REPORT=gpt-5.4-mini`, `DEEP=gpt-5.4`를 사용한다고 가정합니다. 표준 처리 단가는 각각 `gpt-5-nano` 입력 `$0.05`/출력 `$0.40`, `gpt-5.4-mini` 입력 `$0.75`/출력 `$4.50`, `gpt-5.4` 입력 `$2.50`/출력 `$15.00` per 1M tokens 기준입니다. 같은 `10M/1M` token을 전부 `gpt-5.4`로 보내면 OpenAI 비용은 약 `$40.00/month`이고, threshold correction에서 `gpt-5.5`를 추가로 `1M/0.1M` tokens 쓰면 약 `$8.00`가 더 붙습니다.

따라서 기본 OpenAI 라우팅 기준 월 운영비는 VAT 제외 약 `$77.31`, 즉 약 `104,000 KRW`입니다. 10% VAT까지 보수적으로 잡으면 약 `115,000 KRW`를 1차 예산으로 둡니다. 운영 초기에는 OpenAI project budget/usage limit을 먼저 설정하고, `data/report`, `data/pipeline_events`, `logs` 증가량과 실제 token usage를 1주 단위로 보고 서버/예산을 조정합니다.

### 2. 서버와 레포 준비

권장 기본값은 Ubuntu 계열 서버, Python `3.13.12`(현재 `.venv/bin/python` 기준), PostgreSQL, systemd/tmux, 고정 outbound IP입니다. Kiwoom REST API는 허용 IP 기반 보안 정책을 쓰므로, 클라우드 서버를 쓰면 고정 공인 IP 또는 NAT egress IP를 먼저 정합니다.

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-dev build-essential postgresql postgresql-contrib libpq-dev tmux

git clone git@github.com:<your-org-or-user>/KORStockScan.git
cd KORStockScan

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

mkdir -p data/runtime logs
cp data/config_sample.json data/config_dev.json
chmod 600 data/config_dev.json
```

Core DB 경로는 현재 [constants.py](src/utils/constants.py)의 `POSTGRES_URL` 기본값을 사용합니다. 새 서버에서는 같은 user/db를 만들거나, 운영 방식에 맞춰 private fork에서 DB URL 로딩 방식을 정리합니다.

```bash
sudo -u postgres createuser --createdb quant_admin
sudo -u postgres createdb -O quant_admin korstockscan
sudo -u postgres psql -c "ALTER USER quant_admin WITH PASSWORD 'change-this-password';"
```

운영 전에는 `data/config_prod.json`을 별도로 만들고 `chmod 600`으로 제한합니다. 이 파일은 절대 공개 저장소에 커밋하지 않습니다.

### 3. Kiwoom REST API 신청

1. Kiwoom 증권 계좌와 온라인 ID를 준비하고, 휴면/거래종료/미사용 제한이 없는지 확인합니다.
2. <https://openapi.kiwoom.com>에 로그인한 뒤 `API 사용신청`을 진행합니다.
3. 실전/모의 사용 범위, 주문/계좌/시세/WebSocket 권한, 약관, 보안 프로그램, 허용 IP를 확인합니다.
4. 신청 후 `APPKEY`와 `SECRETKEY`를 발급받고, 운영 서버의 IP가 허용 목록에 들어갔는지 확인합니다.
5. 운영 설정에는 실전 서버 기준으로 아래 값을 둡니다.

```json
{
  "KIWOOM_BASE_URL": "https://api.kiwoom.com",
  "KIWOOM_WS_URI": "wss://api.kiwoom.com:10000/api/dostk/websocket",
  "KIWOOM_APPKEY": "YOUR_KIWOOM_APPKEY",
  "KIWOOM_SECRETKEY": "YOUR_KIWOOM_SECRETKEY"
}
```

토큰은 `data/runtime/kiwoom_token_cache.json`과 `data/runtime/kiwoom_token_cache.lock`으로 프로세스 간 재사용합니다. 토큰 캐시는 `.gitignore` 대상이며, 토큰 오류가 반복되면 캐시 삭제보다 로그의 `return_code`, 허용 IP, 계정 상태, token 발급 한도를 먼저 봅니다.

### 4. AI API 신청

이 레포의 현재 운영 기준은 Gemini/DeepSeek/OpenAI를 모두 "즉시 live routing 승격"이 아니라 endpoint contract, flag-off acceptance, proposal layer로 분리하는 것입니다. 키를 발급받아도 `Plan Rebase`와 runtime flag guard 없이 provider routing을 임의로 바꾸지 않습니다.

OpenAI:

1. OpenAI API 플랫폼에서 project를 만들고 billing과 budget/usage limit을 설정합니다.
2. project API key 또는 service account key를 생성합니다.
3. 운영 설정에는 `OPENAI_API_KEY`, 필요 시 fallback용 `OPENAI_API_KEY_2`를 넣습니다.
4. 현재 레포 기준 OpenAI runtime tier는 `FAST=gpt-5-nano`, `REPORT=gpt-5.4-mini`, `DEEP=gpt-5.4`이고, threshold AI correction은 `gpt-5.5 -> gpt-5.4 -> gpt-5.4-mini` fallback을 씁니다.

Gemini:

1. Google AI Studio에서 project를 만들거나 기존 Google Cloud project를 import합니다.
2. API key를 생성하고 Generative Language/Gemini API 용도로 제한합니다.
3. 운영 설정에는 `GEMINI_API_KEY`, 필요 시 `GEMINI_API_KEY_2`, `GEMINI_API_KEY_3`를 넣습니다.
4. Gemini schema/deterministic config 관련 flag는 기본 OFF입니다. live enable은 별도 acceptance와 rollback owner가 닫힌 뒤에만 합니다.

DeepSeek/Claude/OpenRouter:

1. DeepSeek는 공식 platform에서 API key를 만들고 `DEEPSEEK_API_KEY`로 설정합니다.
2. Anthropic Claude 계정은 Console/Workspace에서 API key를 만들고, 현재 코드 호환을 위해 기존 키명 `CLUADE_API_KEY`를 사용합니다.
3. OpenRouter는 key별 credit limit을 설정한 뒤 `OPENROUTER_API_KEY`로 넣습니다.

예시 `data/config_prod.json`:

```json
{
  "KIWOOM_BASE_URL": "https://api.kiwoom.com",
  "KIWOOM_WS_URI": "wss://api.kiwoom.com:10000/api/dostk/websocket",
  "KIWOOM_APPKEY": "YOUR_KIWOOM_APPKEY",
  "KIWOOM_SECRETKEY": "YOUR_KIWOOM_SECRETKEY",
  "DB_URL": "postgresql://quant_admin:change-this-password@localhost:5432/korstockscan",
  "TELEGRAM_TOKEN": "YOUR_TELEGRAM_BOT_TOKEN",
  "ADMIN_ID": "YOUR_TELEGRAM_CHAT_ID",
  "GEMINI_API_KEY": "YOUR_GEMINI_API_KEY",
  "GEMINI_API_KEY_2": "OPTIONAL_SECONDARY_GEMINI_KEY",
  "OPENAI_API_KEY": "YOUR_OPENAI_API_KEY",
  "OPENAI_API_KEY_2": "OPTIONAL_SECONDARY_OPENAI_KEY",
  "DEEPSEEK_API_KEY": "YOUR_DEEPSEEK_API_KEY",
  "CLUADE_API_KEY": "YOUR_ANTHROPIC_CLAUDE_API_KEY",
  "OPENROUTER_API_KEY": "YOUR_OPENROUTER_API_KEY",
  "ECOS_API_KEY": "OPTIONAL_ECOS_KEY",
  "FRED_API_KEY": "OPTIONAL_FRED_KEY",
  "MASSIVE_API_KEY": "OPTIONAL_MASSIVE_KEY",
  "VIRTUAL_ORDERABLE_AMOUNT": 0
}
```

### 5. 첫 기동 전 안전 점검

1. `pause.flag`를 만들어 신규 매수/추가매수 차단 상태에서 먼저 기동합니다.

   ```bash
   touch pause.flag
   ```

2. DB schema 생성 경로와 import가 정상인지 확인합니다.

   ```bash
   PYTHONPATH=. .venv/bin/python -m compileall -q src
   PYTHONPATH=. .venv/bin/pytest -q src/tests/test_kiwoom_token_cache.py src/tests/test_kiwoom_orders.py
   ```

3. token 발급, 계좌/잔고, 주문가능금액, WS 연결은 장중이 아닌 시간에 소액/모의 계정으로 먼저 확인합니다. `src/tests/test_deposit.py`, `src/tests/test_inventory_api.py`, `src/tests/test_api_data.py`는 실제 API 키와 네트워크가 필요한 live smoke 성격입니다.
4. `pause.flag` 해제와 `src/run_bot.sh` 실거래 기동은 계좌, 허용 IP, 주문가능금액, Telegram admin, rollback guard, 당일 checklist를 모두 확인한 뒤에만 합니다.

### 6. IPO 상장첫날 runner

IPO runner는 스캘핑/스윙 threshold-chain과 분리된 별도 실주문 도구입니다. 당일 `configs/ipo_listing_day_YYYY-MM-DD.yaml`이 있어야만 자동 wrapper가 실행됩니다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.ipo_listing_day_runner \
  --config configs/ipo_listing_day_$(TZ=Asia/Seoul date +%F).yaml \
  --dry-select
```

실제 자동 실행은 `deploy/run_ipo_listing_day_autorun.sh`가 담당합니다. `budget_cap_krw`는 YAML에서 읽지만 실제 주문 산출에는 종목별 최대 `5,000,000 KRW` 상한을 적용해 `effective_budget_cap_krw`로 기록합니다.

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

## 산출물과 로그

| 경로 | 내용 |
| --- | --- |
| `data/report/report_YYYY-MM-DD.json` | daily report canonical JSON |
| `data/report/monitor_snapshots/*_YYYY-MM-DD.json` | trade review, performance tuning, missed entry, post-sell 등 monitor snapshot |
| `data/report/threshold_cycle_YYYY-MM-DD.json` | 장후 threshold cycle canonical report |
| `data/report/threshold_cycle_calibration/threshold_cycle_calibration_YYYY-MM-DD_{intraday,postclose}.json` | 장중/장후 calibration artifact |
| `data/report/threshold_cycle_ai_review/threshold_cycle_ai_review_YYYY-MM-DD_{intraday,postclose}.{json,md}` | AI correction proposal와 deterministic guard 결과 |
| `data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_YYYY-MM-DD.{json,md}` | pattern lab 기반 improvement order 및 auto family 후보 |
| `data/runtime/scalp_live_simulator_state.json` | 스캘핑 live simulator open sim 포지션 재시작 복원 상태 |
| `data/report/swing_daily_simulation/swing_daily_simulation_YYYY-MM-DD.{json,md}` | 야간 DB 갱신 후 스윙 추천 후보의 runtime dry-run proxy 시뮬레이션 리포트 |
| `data/report/swing_selection_funnel/swing_selection_funnel_YYYY-MM-DD.{json,md}` | 스윙 추천/DB/장중 진입 funnel raw vs unique 리포트 |
| `data/report/swing_lifecycle_audit/swing_lifecycle_audit_YYYY-MM-DD.{json,md}` | 스윙 선정-진입-보유-추가매수-청산 lifecycle 관찰축 리포트 |
| `data/report/swing_threshold_ai_review/swing_threshold_ai_review_YYYY-MM-DD.{json,md}` | 스윙 threshold/logic 후보에 대한 proposal-only AI review |
| `data/report/swing_improvement_automation/swing_improvement_automation_YYYY-MM-DD.{json,md}` | 스윙 lifecycle 기반 improvement order 및 auto family 후보 |
| `data/report/swing_runtime_approval/swing_runtime_approval_YYYY-MM-DD.{json,md}` | 스윙 EV trade-off 기반 approval_required 요청과 blocked reason |
| `data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_YYYY-MM-DD.{json,md}` | DeepSeek 스윙 pattern lab fresh output을 report-only order로 정규화한 산출물 |
| `data/report/swing_model_retrain/*_YYYY-MM-DD.{json,md}` | 스윙 ML 재학습 진단, 상승장 특화모델 기간 검토, 재학습/승격 결과 |
| `data/model_registry/swing_v2/current.json` | 현재 승격된 스윙 ML v2 모델 manifest와 `bull_specialist_mode` |
| `docs/code-improvement-workorders/code_improvement_workorder_YYYY-MM-DD.md` | Codex 세션 입력용 code improvement 작업지시서 |
| `data/report/code_improvement_workorder/code_improvement_workorder_YYYY-MM-DD.json` | code improvement 작업지시서 machine-readable 요약 |
| `data/report/threshold_cycle_ev/threshold_cycle_ev_YYYY-MM-DD.{json,md}` | 무인 threshold 반영 이후 daily EV 성과 리포트 |
| `data/report/error_detection/error_detection_YYYY-MM-DD.json` | System Error Detector 실행 결과와 detector별 severity/details/recommended_action |
| `data/runtime/update_kospi_status/update_kospi_YYYY-MM-DD.json` | 야간 `update_kospi.py` chain 실행 결과, step별 성공/실패, feature source, 최신 DB quote 상태 |
| `data/ipo_listing_day/YYYY-MM-DD/` | IPO 상장첫날 runner의 events, decision, summary 산출물 |
| `data/ipo_listing_day/status/ipo_listing_day_YYYY-MM-DD.status.json` | IPO YAML-gated autorun status |
| `data/report/statistical_action_weight/` | statistical action weight JSON/Markdown |
| `data/report/holding_exit_decision_matrix/` | holding/exit decision matrix JSON/Markdown |
| `data/pipeline_events/pipeline_events_YYYY-MM-DD.jsonl` | runtime pipeline event stream |
| `data/threshold_cycle/threshold_events_YYYY-MM-DD.jsonl` | threshold compact event stream |
| `data/gatekeeper/gatekeeper_snapshots_YYYY-MM-DD.jsonl` | gatekeeper snapshot stream |
| `data/post_sell/post_sell_candidates_YYYY-MM-DD.jsonl` | post-sell 후보 |
| `data/post_sell/post_sell_evaluations_YYYY-MM-DD.jsonl` | post-sell 평가 |
| `logs/*.log` | runtime/cron/operator 로그 |
| `data/log_archive/YYYY-MM-DD/*.gz` | 압축된 날짜별 로그 archive |

JSON/JSONL이 canonical data이며, 사람이 장후 판정에 바로 읽어야 하는 항목만 Markdown report로 별도 생성합니다. report inventory는 [data/report/README.md](data/report/README.md)를 봅니다.

## 운영 자동화

| 자동화 | 경로 | 설명 |
| --- | --- | --- |
| threshold PREOPEN | `deploy/run_threshold_cycle_preopen.sh` | 전일 report/AI correction guard 기반 `auto_bounded_live` apply plan과 runtime env 생성 |
| threshold INTRADAY calibration | `deploy/run_threshold_cycle_calibration.sh` | 12:05 KST 장중 calibration/AI correction artifact 생성. runtime mutation 없음 |
| swing live dry-run POSTCLOSE | `deploy/run_swing_live_dry_run_report.sh` | 15:45 KST 스윙 selection funnel, lifecycle audit, threshold AI review, improvement automation 생성 |
| threshold POSTCLOSE | `deploy/run_threshold_cycle_postclose.sh` | compact backfill, postclose calibration/AI correction, swing lifecycle automation, pattern lab automation, code improvement workorder, daily EV report 생성 |
| swing model retrain POSTCLOSE | `auto_retrain_pipeline.sh`, `deploy/install_swing_model_retrain_cron.sh` | 17:30 KST 스윙 ML v2 재학습 필요성 진단과 staging 재학습/평가/자동 artifact 승격. 실주문 전환 없음 |
| tuning monitoring POSTCLOSE | `deploy/run_tuning_monitoring_postclose.sh` | Parquet/DuckDB refresh와 shadow diff. pattern lab은 기본 skip하고 `THRESHOLD_CYCLE_POSTCLOSE`를 canonical runner로 둠 |
| nightly KOSPI update | `src/utils/update_kospi.py` | 21:00 KST 원천 DB 업데이트 후 status JSON을 남깁니다. 후속 스윙 추천/시뮬레이션 리포트는 별도 artifact freshness로 확인합니다. |
| monitor snapshot | `deploy/run_monitor_snapshot_safe.sh`, `deploy/run_monitor_snapshot_incremental_cron.sh` | 장중/장후 snapshot 생성 |
| system metric sampler | `deploy/run_system_metric_sampler_cron.sh` | 1분 단위 시스템 지표 |
| system error detector | `deploy/run_error_detection.sh full` | 5분 단위 process/cron/log/artifact/resource/stale-lock 운영 감시 report 생성. detector 결과로 threshold/spread/order guard를 자동 변경하지 않음 |
| IPO listing-day autorun | `deploy/run_ipo_listing_day_autorun.sh` | 당일 YAML이 있을 때만 별도 IPO runner 실행. threshold-cycle/daily EV 자동 입력 금지 |
| daily workorder | `.github/workflows/build_codex_daily_workorder.yml` | checklist 기반 작업지시서 생성 |
| Project sync | `.github/workflows/sync_docs_backlog_to_project.yml` | 문서 backlog를 GitHub Project로 동기화 |
| Calendar sync | `.github/workflows/sync_project_to_google_calendar.yml` | GitHub Project 일정을 Google Calendar로 동기화 |

신규 운영 기능을 추가할 때는 detector coverage도 같은 변경 세트에 포함합니다.

### 후속 누락 방지 checkpoint

아래 판단시점은 실행 권한이 아니라 review/approval gate다. 날짜별 checklist에 parser-friendly `Due/Slot/TimeWindow/Track` 항목으로 남겨 Project/Calendar 동기화 대상이 되게 한다.

| checkpoint | 판단 입력 | 허용 결론 |
| --- | --- | --- |
| `SwingRealOrderTransitionDecision0511` | `swing_runtime_approval`, `swing_live_dry_run`, `swing_daily_simulation`, `threshold_cycle_ev` | global dry-run 유지, one-share real canary approval request, hold_sample/freeze |
| `SwingNumericFloorAutoChangeDecision0511` | `swing_runtime_approval.swing_model_floor`, 추천 후보수, downside tail, fallback contamination, regime별 성과 | approval_required, hold_sample, freeze. 사용자 approval artifact 없이는 floor env 미작성 |
| `ThresholdEnvAutoApplyPreopen0512` | 전일 `threshold_cycle_ev`, `threshold_apply`, `threshold_runtime_env_YYYY-MM-DD.env/json`, `src/run_bot.sh` source 여부 | `auto_bounded_live` guard 통과분만 장전 env 반영 확인. 장중 mutation 금지 |

| 신규 기능 유형 | 필수 등록 |
| --- | --- |
| cron/wrapper/정기 실행 job | `CRON_JOB_REGISTRY`와 `REQUIRED_CRON_JOB_IDS` |
| report/artifact 생성 기능 | `ARTIFACT_REGISTRY`와 `REQUIRED_ARTIFACT_IDS` |
| 장기 실행 thread/daemon | `write_heartbeat(component=...)`와 `REQUIRED_HEARTBEAT_COMPONENTS` |
| 새 health domain | `@register_detector` detector와 `error_detector.py` import |
| 감시 제외 대상 | `DETECTOR_COVERAGE_EXEMPTIONS`에 제외 사유 |

detector coverage 검증:

```bash
PYTHONPATH=. .venv/bin/pytest -q src/tests/test_error_detector_coverage.py
PYTHONPATH=. .venv/bin/python -m src.engine.error_detector --mode full --dry-run
```

문서 checklist를 수정한 뒤 parser 검증:

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500
```

Project/Calendar 동기화 표준 명령:

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

## 자동화 체인 플로우차트

현재 daily threshold/scalping improvement 체인은 사람의 장전 승인 없이 돌아간다. 스윙 runtime threshold 반영은 더 보수적으로 `proposal -> approval_required -> approved_live(dry-run)`를 따른다. 사람의 개입은 Project/Calendar 동기화, 신규 code improvement order를 실제 코드 패치로 전환하는 별도 작업, 스윙 approval artifact 작성, 운영 장애 대응에 남긴다.

```mermaid
flowchart TD
  PE[data/pipeline_events/pipeline_events_YYYY-MM-DD.jsonl]
  TE[data/threshold_cycle/threshold_events_YYYY-MM-DD.jsonl]
  REPORTS[data/report source bundle<br/>buy_funnel_sentinel, holding_exit_sentinel,<br/>holding_exit_observation, post_sell_feedback,<br/>trade_review, ADM/SAW]

  PE -->|runtime compact stages| TE
  REPORTS --> INTRA
  TE --> INTRA

  PREV[data/report/threshold_cycle_YYYY-MM-DD.json<br/>threshold_cycle_ai_review_*_postclose.json]
  PREOPEN[07:35 PREOPEN<br/>deploy/run_threshold_cycle_preopen.sh]
  APPLY[data/threshold_cycle/apply_plans/threshold_apply_YYYY-MM-DD.json]
  RENV[data/threshold_cycle/runtime_env/threshold_runtime_env_YYYY-MM-DD.env/json]
  BOT[bot start<br/>src/run_bot.sh sources runtime env]

  PREV --> PREOPEN
  PREOPEN --> APPLY
  PREOPEN --> RENV
  RENV --> BOT
  BOT --> PE

  INTRA[12:05 INTRADAY calibration<br/>deploy/run_threshold_cycle_calibration.sh]
  INTRACAL[data/report/threshold_cycle_calibration/threshold_cycle_calibration_YYYY-MM-DD_intraday.json]
  INTRAAI[data/report/threshold_cycle_ai_review/threshold_cycle_ai_review_YYYY-MM-DD_intraday.json/md]

  INTRA --> INTRACAL
  INTRA --> INTRAAI
  INTRACAL -. no runtime mutation .-> PREOPEN
  INTRAAI -. next preopen guard input .-> PREOPEN

  POST[16:10 POSTCLOSE<br/>deploy/run_threshold_cycle_postclose.sh]
  SNAP[data/threshold_cycle/snapshots/pipeline_events_YYYY-MM-DD_*.jsonl]
  PART[data/threshold_cycle/date=YYYY-MM-DD/family=*/part-*.jsonl]
  TC[data/report/threshold_cycle_YYYY-MM-DD.json]
  POSTAI[data/report/threshold_cycle_ai_review/threshold_cycle_ai_review_YYYY-MM-DD_postclose.json/md]
  LABS[Gemini/Claude pattern labs<br/>ANALYSIS_START_DATE=2026-04-21<br/>ANALYSIS_END_DATE=TARGET_DATE]
  LABAUTO[data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_YYYY-MM-DD.json/md]
  SWING[15:45 Swing lifecycle<br/>deploy/run_swing_live_dry_run_report.sh]
  SWINGSEL[data/report/swing_selection_funnel/swing_selection_funnel_YYYY-MM-DD.json/md]
  SWINGAUDIT[data/report/swing_lifecycle_audit<br/>swing_threshold_ai_review]
  SWINGAUTO[data/report/swing_improvement_automation/swing_improvement_automation_YYYY-MM-DD.json/md]
  WORKORDER[docs/code-improvement-workorders/code_improvement_workorder_YYYY-MM-DD.md]
  EV[data/report/threshold_cycle_ev/threshold_cycle_ev_YYYY-MM-DD.json/md]

  PE --> POST
  POST --> SNAP
  SNAP --> PART
  PART --> TC
  TC --> POSTAI
  TC --> LABS
  REPORTS --> LABS
  LABS --> LABAUTO
  PE --> SWING
  SWING --> SWINGSEL
  SWING --> SWINGAUDIT
  SWINGAUDIT --> SWINGAUTO
  LABAUTO --> WORKORDER
  SWINGAUTO --> WORKORDER
  TC --> EV
  POSTAI --> EV
  LABAUTO --> EV
  SWINGAUTO --> EV
  TC -->|next-day apply source| PREV
  POSTAI -->|next-day guard source| PREV
```

### 스윙 ML 재학습 자동화 플로우차트

스윙 ML 재학습 체인은 모델 artifact만 자동 승격한다. 승격 후에도 `SWING_LIVE_ORDER_DRY_RUN_ENABLED=True`와 `actual_order_submitted=false`는 유지되며, 스윙 실주문 전환과 1주 real canary는 별도 승인 체계가 담당한다.

```mermaid
flowchart TD
  START[17:30 POSTCLOSE<br/>auto_retrain_pipeline.sh]
  DIAG[data/report/swing_model_retrain<br/>diagnosis_YYYY-MM-DD.json]
  NEED{retrain_required?}
  BULLAI[AI/deterministic proposal<br/>bull mode + bull BASE_DT]
  BULLGUARD{period guard pass?<br/>DB range, samples, label safety}
  MODE[final bull_specialist_mode<br/>enabled / disabled / hold_current]
  STAGE[data/model_registry/swing_v2/runs/run_id<br/>staging output dir]
  HYBRID[train hybrid XGB/LGBM]
  BULL[train bull specialists]
  NEUTRAL[neutralize bull features<br/>bx=hx, bl=hl]
  HOLD[copy active bull artifacts]
  META[train meta ranker<br/>stable META_FEATURES]
  BT[backtest_v2 + candidate metrics]
  SCORE{hard floor + tradeoff score pass?}
  PROMOTE[backup active artifacts<br/>atomic promote candidate]
  SMOKE{recommend_daily_v2 smoke pass?}
  CURRENT[data/model_registry/swing_v2/current.json]
  REPORT[data/report/swing_model_retrain<br/>swing_model_retrain_YYYY-MM-DD.json/md]
  ROLLBACK[restore backup artifacts]
  ACTIVE[data/*.pkl active swing v2 models]
  DRYRUN[bot remains swing dry-run<br/>no broker order enable]

  START --> DIAG
  DIAG --> NEED
  NEED -- no --> REPORT
  NEED -- yes --> BULLAI
  BULLAI --> BULLGUARD
  BULLGUARD -- pass --> MODE
  BULLGUARD -- fail --> MODE
  MODE --> STAGE
  STAGE --> HYBRID
  HYBRID --> MODE
  MODE -- enabled --> BULL
  MODE -- disabled --> NEUTRAL
  MODE -- hold_current --> HOLD
  BULL --> META
  NEUTRAL --> META
  HOLD --> META
  META --> BT
  BT --> SCORE
  SCORE -- no --> REPORT
  SCORE -- yes --> PROMOTE
  PROMOTE --> SMOKE
  SMOKE -- pass --> CURRENT
  SMOKE -- fail --> ROLLBACK
  ROLLBACK --> REPORT
  CURRENT --> ACTIVE
  ACTIVE --> DRYRUN
  DRYRUN --> REPORT
```

### 체인 검토 결과

| 검토 항목 | 판정 | 근거/처리 |
| --- | --- | --- |
| PREOPEN 적용과 INTRADAY calibration 충돌 | 충돌 없음 | 12:05 calibration은 `threshold_cycle_calibration_*_intraday`와 AI review만 만들고 runtime env를 바꾸지 않는다. 다음 장전 apply 후보 입력으로만 전달한다. |
| POSTCLOSE pattern lab과 tuning monitoring pattern lab 중복 | 충돌 제거 | canonical lab 실행 위치를 `THRESHOLD_CYCLE_POSTCLOSE`로 고정했다. `run_tuning_monitoring_postclose.sh`는 기본적으로 pattern lab을 skip하고 status에 `canonical_runner=THRESHOLD_CYCLE_POSTCLOSE`를 남긴다. |
| Pattern lab 결과의 runtime 직접 반영 | 차단 | `scalping_pattern_lab_automation`은 `code_improvement_order(runtime_effect=false)`와 `auto_family_candidate(allowed_runtime_apply=false)`만 생성한다. 실제 runtime 반영은 별도 구현/테스트 후 기존 `auto_bounded_live` guard를 통과해야 한다. |
| Swing lifecycle 결과의 runtime 직접 반영 | 승인 필요 | `swing_runtime_approval`은 hard floor 통과 후 EV trade-off score가 충분할 때만 `approval_required`를 만든다. 수동 approval artifact가 있어야 다음 장전 env에 반영되며, 반영 후에도 스윙은 dry-run이고 실제 주문은 차단된다. |
| Swing 1-share real canary | 별도 승인 필요 | 스윙 broker execution 품질 수집용 1주 real canary는 `swing_runtime_approval`과 별도 approval artifact가 필요하다. 승인되어도 스윙 전체 실매매 전환이 아니며, phase0에서는 1주 BUY/SELL만 허용하고 추가매수 실주문은 금지한다. |
| AI correction의 직접 적용 | 차단 | AI는 수정안을 제안하지만 최종 state/value는 deterministic guard가 bounds, sample window, safety, same-stage owner rule로 결정한다. |
| 사람 개입 누락 | daily chain에는 없음 | 무인 반영 후 제출물은 `threshold_cycle_ev_YYYY-MM-DD.{json,md}`다. 사람이 필요한 지점은 운영 장애, 신규 code improvement order 구현 착수, Project/Calendar 동기화뿐이며 daily threshold 반영 승인 단계는 의도적으로 제거했다. |
| 제거된 `preclose_sell_target` tuning source 혼입 | 차단 | 2026-05-10 제거되어 calibration source bundle과 cron inventory에 포함하지 않는다. 과거 `data/report/preclose_sell_target*` 산출물도 사용자 요청으로 삭제했다. |

## 분석 도구

- `analysis/offline_live_canary_bundle/`: 장중 fresh 로그 접근이 어려울 때 lightweight bundle을 export하고 로컬 analyzer로 same-slot 판정을 닫는 standby diagnostic/report-only 도구. legacy gatekeeper/entry latency summary compatibility도 이 경로에서 생성한다.
- `analysis/offline_gatekeeper_fast_reuse_bundle/`: retired/deprecated compatibility wrapper와 과거 증적 링크 보존용. 신규 export/analyzer 표준 경로가 아니다.
- `analysis/gemini_scalping_pattern_lab/`, `analysis/claude_scalping_pattern_lab/`: `THRESHOLD_CYCLE_POSTCLOSE`에서 매일 `ANALYSIS_START_DATE=2026-04-21`, `ANALYSIS_END_DATE=TARGET_DATE`로 실행되는 스캘핑 패턴/EV 분석 lab. 결과는 `scalping_pattern_lab_automation`을 거쳐 기존 threshold family 입력, auto family 후보, code improvement order로만 쓰며 runtime/code를 직접 변경하지 않는다.
- `src/engine/server_report_comparison.py`: 원격 서버 report 비교. Plan Rebase 의사결정에서는 remote 비교값을 기본 입력에서 제외합니다.
- `src/engine/build_tuning_monitoring_parquet.py`, `src/engine/tuning_duckdb_repository.py`: 튜닝 관찰 데이터를 Parquet/DuckDB로 다루는 경로.

## 테스트

대표 테스트:

```bash
PYTHONPATH=. .venv/bin/pytest -q src/tests/test_sniper_entry_latency.py
PYTHONPATH=. .venv/bin/pytest -q src/tests/test_sniper_scale_in.py
PYTHONPATH=. .venv/bin/pytest -q src/tests/test_holding_flow_override.py
PYTHONPATH=. .venv/bin/pytest -q src/tests/test_daily_threshold_cycle_report.py
PYTHONPATH=. .venv/bin/pytest -q src/tests/test_ai_engine_openai_transport.py
PYTHONPATH=. .venv/bin/pytest -q src/tests/test_pipeline_event_logger.py
PYTHONPATH=. .venv/bin/pytest -q src/tests/test_error_detector*.py
PYTHONPATH=. .venv/bin/pytest -q src/tests/test_ipo_listing_day_runner.py src/tests/test_kiwoom_token_cache.py
```

문서만 수정한 경우에도 checklist/parser 영향이 있으면 아래 검증을 우선 실행합니다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500
```

## 주요 문서

| 문서 | 역할 |
| --- | --- |
| [docs/plan-korStockScanPerformanceOptimization.rebase.md](docs/plan-korStockScanPerformanceOptimization.rebase.md) | 현재 튜닝 원칙, active owner, live/observe/off 판정 |
| [docs/plan-korStockScanPerformanceOptimization.prompt.md](docs/plan-korStockScanPerformanceOptimization.prompt.md) | 다음 세션 시작용 경량 포인터 |
| [docs/plan-korStockScanPerformanceOptimization.execution-delta.md](docs/plan-korStockScanPerformanceOptimization.execution-delta.md) | 원안 대비 실행 변경 |
| [docs/plan-korStockScanPerformanceOptimization.performance-report.md](docs/plan-korStockScanPerformanceOptimization.performance-report.md) | Plan Rebase 성과 기준과 반복 성과값 |
| [docs/README.md](docs/README.md) | 문서 구조와 archive 기준 |
| [docs/time-based-operations-runbook.md](docs/time-based-operations-runbook.md) | 시간대별 장전/장중/장후 운영 runbook |
| [docs/2026-05-11-stage2-todo-checklist.md](docs/2026-05-11-stage2-todo-checklist.md) | 최신 미래 실행 항목 소유 문서 |
| [docs/code-reviews/system-error-detector-2026-05-09-implementation-review.md](docs/code-reviews/system-error-detector-2026-05-09-implementation-review.md) | System Error Detector 구현/수정 리뷰 기록 |
| [data/report/README.md](data/report/README.md) | report inventory와 Markdown 누락 후보 |
| [data/threshold_cycle/README.md](data/threshold_cycle/README.md) | threshold cycle 운영 원칙 |
| [docs/workorder-shadow-canary-runtime-classification.md](docs/workorder-shadow-canary-runtime-classification.md) | shadow/canary/historical 분류와 runtime ON/OFF 기준 |

## 문서 디렉터리 구조

`docs/` 루트에는 날짜별 checklist, Plan Rebase 기준 문서, 현재 workorder/runbook만 둡니다. 보조 문서는 아래 하위 디렉터리에 분류합니다.

| 경로 | 내용 |
| --- | --- |
| `docs/ai-acceptance/` | Gemini, DeepSeek, OpenAI flag-off acceptance spec과 parity review |
| `docs/audit-reports/` | 감리, OFI/QI, hotfix, 운영 감사 보고서 |
| `docs/code-reviews/` | 스나이퍼 엔진 코드리뷰, 성능 감사, holding flow override 리뷰 |
| `docs/code-improvement-workorders/` | 코드 개선 전용 workorder |
| `docs/proposals/` | 스캐너 개선, preclose sell target 등 운영 제안서 |
| `docs/personal/` | 개인 보조 메모. 실행 판정의 `Source`로 쓰지 않음 |
| `docs/reference/` | API 문서, AI coding instruction 등 일반 참조 |

## 운영 원칙

- 실전 변경은 동일 단계 내 `1축 canary`만 허용합니다.
- 진입병목축과 보유/청산축처럼 단계, 조작점, 적용시점, cohort tag, rollback guard가 분리되면 stage-disjoint concurrent canary로 병렬 검토할 수 있습니다.
- 신규/보완 alpha 튜닝축은 shadow 없이 canary-only로 봅니다. 단, AI transport/schema, statistical action weight, decision matrix 같은 지원축은 observe/report-only로 둘 수 있습니다.
- live 승격 전에는 분포 근거, candidate cohort, rollback guard, OFF 조건, 판정 시각, same-stage owner 충돌 여부를 문서에 닫아야 합니다.
- 리포트 정합성이나 event 복원이 불확실하면 전략 효과 판정보다 집계 품질 점검을 먼저 합니다.
- System Error Detector의 `fail`/`warning`은 운영 장애, instrumentation gap, code bug, normal drift로 먼저 분류합니다. 코드 수정이 필요하면 error detection report와 관련 log를 근거로 별도 Codex 작업을 지시합니다.
- detector coverage 없는 신규 recurring runtime/cron/report/thread 기능은 미완료로 봅니다.

## 면책

본 프로젝트는 자동매매 연구/운영 도구입니다. 투자 판단과 결과 책임은 사용자 본인에게 있으며, 실거래 적용 전 모의/소액 검증과 rollback guard 확인이 필요합니다.
