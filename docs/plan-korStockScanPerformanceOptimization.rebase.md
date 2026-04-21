# KORStockScan Plan Rebase 중심 문서

기준일: `2026-04-22 KST`  
역할: 현재 튜닝 원칙, 판정축, 실행과제, 일정, 효과를 한곳에 고정하는 중심축 문서다.  
주의: 이 문서는 자동 파싱용 체크리스트를 소유하지 않는다. Project/Calendar 동기화 대상 작업항목은 날짜별 `stage2 todo checklist`가 소유한다.

---

## 1. 현재 판정

현재 단계는 손실 억제형 미세조정이 아니라 `기대값/순이익 극대화`를 위한 `Plan Rebase`다.

1. `fallback_scout/main`(탐색 주문/본 주문 동시 fallback 분할진입), `fallback_single`(단일 fallback 진입), `latency fallback split-entry`(지연 상태에서 fallback으로 분할진입하던 폐기축)는 영구 폐기한다.
2. 기준선은 `main-only`(메인서버 단독 기준), `normal_only`(fallback 오염이 없는 정상 진입 표본), `post_fallback_deprecation`(fallback 폐기 이후 표본) 중심으로 본다.
3. 다음 live 변경은 한 번에 한 축 canary만 허용한다.
4. 현재 실전 유지축은 `main-only buy_recovery_canary`다.
5. 다음 정식 후보는 `entry_filter_quality`다. 단, `buy_recovery_canary` 1차 판정 전에는 섞지 않는다.

## 2. 용어 범례

| 표현 | 한글 설명 | 현재 판정 |
| --- | --- | --- |
| `fallback` | 정상 진입이 막힌 상황에서 보조 주문 경로로 진입을 시도하던 예외 경로 | 신규 사용 금지, 폐기 유지 |
| `fallback_scout/main` | `fallback_scout` 탐색 주문과 `fallback_main` 본 주문이 같은 축에서 함께 나가던 2-leg fallback 분할진입 | 영구 폐기. 재개/승격/canary 대상 아님 |
| `fallback_single` | scout/main으로 나뉘지 않은 단일 fallback 진입 경로 | 영구 폐기. 재개/승격/canary 대상 아님 |
| `latency fallback split-entry` | latency 상태가 `CAUTION/DANGER`일 때 fallback 허용으로 분할진입을 시도하던 경로 | 영구 폐기. latency bugfix 대상과 분리 |
| `main-only` | `songstock`/remote 비교를 제외하고 메인서버 실전 로그만 기준으로 보는 방식 | Plan Rebase 기간의 기준선 |
| `normal_only` | fallback 태그와 예외 진입이 섞이지 않은 정상 진입 표본 | 손익/성과 비교의 우선 기준 |
| `post_fallback_deprecation` | `2026-04-21 09:45 KST` fallback 폐기 이후 새로 쌓인 표본 | 폐기 이후 효과 확인 기준 |
| `canary` | 작은 범위로 실전에 적용해 성과와 리스크를 검증하는 1축 변경 | 하루 1축만 허용 |
| `shadow` | 실전 주문에는 반영하지 않고 병렬 계산만 하던 검증 방식 | 신규/보완축에서는 금지 |
| `buy_recovery_canary` | Gemini `WAIT 65~79` 과밀 구간을 2차 재평가해 BUY 회복 여부를 보는 실전 1축 | 현재 유지축 |
| `entry_filter_quality` | 불량 진입을 줄이고 제출/체결 품질을 높이는 다음 정식 튜닝 후보 | `buy_recovery_canary` 1차 판정 후 재판정 |

## 3. 튜닝 원칙

1. 최종 목표는 손실 억제가 아니라 기대값/순이익 극대화다.
2. 손익 판단은 `COMPLETED + valid profit_rate`만 사용한다.
3. `NULL`, 미완료, fallback 정규화 값은 손익 기준으로 사용하지 않는다.
4. 비교 우선순위는 `거래수 -> 퍼널 -> blocker -> 체결품질 -> missed_upside -> 손익`이다.
5. BUY 후 미진입은 `latency guard miss`, `liquidity gate miss`, `AI threshold miss`, `overbought gate miss`로 분리한다.
6. `full fill`과 `partial fill`은 합산하지 않는다.
7. 원인 귀속이 불명확하면 먼저 리포트 정합성, 이벤트 복원, 집계 품질을 점검한다.
8. `counterfactual` 수치는 직접 실현손익과 합산하지 않고 우선순위 판단 자료로만 쓴다.

## 4. 작업 규칙

| 규칙 | 기준 | 위반 시 처리 |
| --- | --- | --- |
| 단일 live canary | 하루에 live 변경축 1개만 허용 | 새 축 미착수 또는 기존 축 OFF 후 전환 |
| shadow 금지 | 신규/보완축은 shadow 없이 canary-only | shadow 항목은 폐기 또는 코드정리로 격하 |
| 원격 비교 제외 | Plan Rebase 기간은 main-only 기준 | songstock/remote 비교는 의사결정 입력에서 제외 |
| 라우팅 고정 | live 스캘핑 AI는 Gemini 고정 | A/B는 `entry_filter_quality` 1차 판정 후 별도 판단 |
| 문서 기준 | 중심 문서는 기준, checklist는 실행, report는 근거 | 중복 작업항목 생성 금지 |
| 일정 날짜 고정 | 모든 작업일정은 `YYYY-MM-DD KST`와 `Slot/TimeWindow`로 고정 | `후보비교 완료시`, `관찰 후`, `다음주` 같은 상대 일정은 무효. 당일 안에 절대 날짜/시각으로 재작성 |
| 관찰 반나절 제한 | live 영향 여부 관찰은 오전/오후 반나절을 넘기지 않음 | 반나절에 미관측이면 관찰축 오류, live 영향 없음, 또는 그대로 진행 가능 중 하나로 판정 |
| 봇 재실행 | 검증/반영에 봇 재실행이 필요하고 권한/안전 조건이 맞으면 AI가 표준 wrapper로 직접 실행 | 토큰/계정/운영 승인 등 보안 경계가 있으면 실행하지 않고 필요한 1개 명령을 사용자에게 요청 |
| canary ON/OFF 반영 | canary flag는 `TRADING_RULES` 생성 시 env/code에서 읽히므로 hot-reload 기준이 아니다. OFF/ON 변경은 env/code 반영 후 `restart.flag` 기반 우아한 봇 재시작이 표준이다 | rollback guard 발동 시 canary OFF 값을 먼저 고정하고 `restart.flag`로 재시작한다. 목표 소요시간은 5분 이내, 토큰/운영 승인 경계가 있으면 사용자 실행 명령을 남김 |
| 문서/동기화 | 문서 변경 후 parser 검증은 AI가 실행하고, Project/Calendar 동기화는 토큰 보안 경계가 있으면 사용자 수동 실행 요청을 포함 | `GH_PROJECT_TOKEN` 등 보안 토큰이 없으면 실패 원인과 재실행 명령을 보고 |
| 환경 변경 | 패키지 설치/업그레이드/제거 전 사용자 승인 | 승인 전 대안 경로 사용 |

## 5. 완료 기준

| 항목 | 완료 기준 |
| --- | --- |
| 튜닝축 선정 | pain point, 실행과제, 정량 목표, rollback guard, 판정시각, 상태가 한 줄로 연결됨 |
| live canary | `N_min`, 주요 metric, rollback guard, OFF 조건, 판정시각이 문서와 로그에 고정됨 |
| 성과판정 | `COMPLETED + valid profit_rate`, full/partial 분리, blocker 분포, 체결품질이 함께 제시됨 |
| 보류/미착수 | 보류 사유, 기대값 영향, 다음 판정시각 또는 폐기/코드정리 판정이 명시됨 |
| 폐기 | 재개 조건이 없으면 폐기 문서/부속문서로 내리고 중심 문서에는 요약만 유지 |
| 하위 참조 | 일일 체크리스트, 감사보고서, Q&A, 폐기과제가 역할별로 분리됨 |
| 실제 효과 갱신 | 일일 체크리스트 완료 시 §11 실제 효과 기록을 같은 턴에 갱신함 |

## 6. 정량 목표와 가드

| 지표 | 목표/발동 조건 | 적용축 | 조치 |
| --- | --- | --- | --- |
| `N_min` | 판정 시점 `trade_count < 50`이고 `submitted_orders < 20` | 모든 canary | hard pass/fail 금지, 방향성 판정 |
| `loss_cap` | canary cohort 일간 합산 실현손익이 당일 스캘핑 배정 NAV 대비 `<= -0.35%` | live canary | canary OFF, 전일 설정 복귀 |
| `reject_rate` | `normal_only` baseline 대비 `+15.0%p` 이상 증가 | entry canary | canary OFF |
| `latency_p95` | `gatekeeper_eval_ms_p95 > 15,900ms`, 샘플 `>=50` | entry/latency | canary OFF, latency 경로 재점검 |
| `partial_fill_ratio` | baseline 대비 `+10.0%p` 이상 증가 | entry canary | 경고. `loss_cap` 또는 soft-stop 악화 동반 시 OFF |
| `fallback_regression` | `fallback_scout/main`(탐색/본 주문 동시 fallback) 또는 `fallback_single`(단일 fallback) 신규 1건 이상 | 전체 | 즉시 OFF, 회귀 조사 |
| `buy_drought_persist` | canary 후에도 BUY count가 baseline 하위 3분위수 미만이고 `blocked_ai_score_share` 개선 없음 | `buy_recovery_canary` | canary 유지 금지, score/prompt 재교정 |
| `recovery_false_positive_rate` | canary로 회복된 BUY 중 soft_stop 비율이 `normal_only` baseline 대비 `+5.0%p` 이상 증가 | `buy_recovery_canary` | canary OFF, score/prompt 재교정 |

## 7. 매매단계별 Pain Point

| 단계 | Pain point | 현재 증거 | 기대값 영향 | 우선 판정 |
| --- | --- | --- | --- | --- |
| 진입 | Gemini 전환 후 BUY drought, WAIT65~79 과밀 | 04-21 `WAIT65~79` 후보 54건, 제출 0건 | 미진입 기회비용 증가, 표본 고갈 | `buy_recovery_canary` 유지 관찰 |
| 진입 | BUY 후 제출 전 latency/budget 병목 | 04-21 preflight `latency_block=40`, `submitted=0` | threshold 완화만으로 거래 회복 불가 | recheck -> submitted 연결성 우선 |
| 진입 | `shared` 호출 혼입 가능성 | 오전 실전 로그에서 연결 여부 확인 필요 | shared 혼입 시 진입 판정 귀속 불가 → 불량 진입 원인분석 차단 | 04-22 12:20~12:30 강제판정 |
| 보유 | 포지션 맥락 부족 | 보유 AI가 수익률/고점/보유시간을 직접 입력으로 받는지 미완 | 조기청산/지연청산 동시 악화 가능 | `position_context` 스키마 설계 |
| 청산 | EOD/NXT 및 exit_rule 혼선 | NXT 가능/불가능 종목의 EOD 판단 분리 필요 | 청산 원인별 기대값 개선 지점 불명확 | 후순위 설계 |
| 포지션 증감 | 물타기/불타기/분할진입 축 혼재 | 불타기 수익 확대 관찰, fallback 오염 존재 | 추가진입 기대값 판단 오염 | `position_addition_policy` 후순위 |
| 운영/데이터 | 리포트 basis 혼선 | 문서 파생값과 DB 실필드 혼용 위험 | 잘못된 승격/롤백 위험 | DB 우선, 체크리스트 동기화 |

## 8. Pain Point별 실행과제

| ID | Pain point | 실행과제 | 일정 | 상태 | 판정 basis | 기대효과 | 실제효과 | 참조 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `BR-0422` | WAIT65~79 BUY drought | `main-only buy_recovery_canary` 1일차 판정 | `2026-04-22 12:00~12:20` | 진행중 | 퍼널 지표 + 실현손익, paper-fill은 counterfactual 참고 | WAIT 과밀 완화, BUY 표본 복구 | TBD | [2026-04-22 checklist](./2026-04-22-stage2-todo-checklist.md) |
| `BR2-0422` | `buy_recovery_canary` 1일차 종합 | 오전/장중 결과 종합판정 + 다음 액션 고정 | `2026-04-22 16:30~17:00` | 예정 | 퍼널 지표 + guard 대조 | 다음 live 축 유지/롤백/재교정 명확화 | TBD | [2026-04-22 checklist](./2026-04-22-stage2-todo-checklist.md) |
| `LP-0422` | recheck -> submitted 병목 | WAIT65~79 preflight 및 latency blocker 분리 | `2026-04-22 PREOPEN 08:30~08:40` | 완료 | 퍼널 지표 | threshold 오판 방지 | `latency_state_danger=33`, `latency_fallback_disabled=7` 분리 | [auditor report](./2026-04-21-auditor-performance-result-report.md) |
| `PP-0422` | 프로파일 특화 go/no-go | `watching/holding/exit/shared 제거` 중 1축 강제판정 | `2026-04-22 12:20~12:30` | 예정 | 퍼널 지표 + 실전 로그 | 프롬프트 귀속 명확화, 행동 canary 남발 방지 | TBD | [2026-04-22 checklist](./2026-04-22-stage2-todo-checklist.md) |
| `SH-0422` | shared 호출 혼입 가능성 | 오전 `scalping_shared` live 영향 관찰 종료판정 | `2026-04-22 12:20~12:30` | 예정 | 실전 로그 + 퍼널 지표 | shared 호출 건수와 진입 결과를 분리해 불량 진입 원인분석 가능 | TBD | [@My-Opinion](./@My-Opinion.md) |
| `HC-0422` | 보유 포지션 맥락 부족 | `position_context` 입력 스키마 설계 | `2026-04-22 15:40~15:50` | 예정 | 스키마/로그 필드 | GOOD_EXIT/capture_efficiency 개선 기반 | TBD | [2026-04-22 checklist](./2026-04-22-stage2-todo-checklist.md) |
| `HE-0422` | HOLDING 성과 불명확 | D+2 최종판정 | `2026-04-22 15:50~16:00` | 예정 | 실현손익 + missed_upside/capture_efficiency | 보유/청산 개선축 우선순위 확정 | TBD | [performance report](./plan-korStockScanPerformanceOptimization.performance-report.md) |
| `EFQ-0423` | 정상 진입 품질 저하 | `entry_filter_quality` 착수 가능성 재판정 | `2026-04-23 POSTCLOSE 15:20~15:35` | 예정 | 퍼널 지표 + 실현손익 | 불량 진입 감소, 제출/체결 품질 개선 | TBD | [2026-04-23 checklist](./2026-04-23-stage2-todo-checklist.md) |
| `PA-0423` | 포지션 증감 축 혼재 | `position_addition_policy` 상태머신 초안 | `2026-04-23 POSTCLOSE 16:40~16:50` | 예정 | 설계/로그 필드 | 물타기/불타기/분할진입 통합 설계 | TBD | [2026-04-23 checklist](./2026-04-23-stage2-todo-checklist.md) |
| `EOD-0424` | EOD/NXT 및 exit_rule 혼선 | EOD/NXT 착수 여부 재판정 | `2026-04-24 POSTCLOSE 15:40~15:50` | 후순위 | 실현손익 + exit funnel | 청산 경로별 기대값 개선 지점 확정 | TBD | [2026-04-24 checklist](./2026-04-24-stage2-todo-checklist.md) |
| `AB-0424` | AI 엔진 A/B 재개 판단 | A/B 재개 여부 판정 | `2026-04-24 POSTCLOSE 15:50~16:00` | 예정 | 퍼널 지표 + 모델 비교 준비상태 | Gemini 고정 이후 모델 비교 재개 여부 확정 | TBD | [2026-04-24 checklist](./2026-04-24-stage2-todo-checklist.md) |

## 9. 일정

| 일자 | 판정시각 | 핵심 판정 | 소유 문서 |
| --- | --- | --- | --- |
| `2026-04-22` | `12:00~12:20` | `buy_recovery_canary` 1일차 계량 | [2026-04-22 checklist](./2026-04-22-stage2-todo-checklist.md) |
| `2026-04-22` | `12:20~12:30` | 프로파일별 특화 1축 go/no-go, shared 제거 종료판정 | [2026-04-22 checklist](./2026-04-22-stage2-todo-checklist.md) |
| `2026-04-22` | `15:40~17:00` | `position_context`, HOLDING D+2, `buy_recovery_canary` 종합판정 | [2026-04-22 checklist](./2026-04-22-stage2-todo-checklist.md) |
| `2026-04-23` | `15:20~15:50` | `entry_filter_quality`, A/B preflight | [2026-04-23 checklist](./2026-04-23-stage2-todo-checklist.md) |
| `2026-04-24` | `15:20~16:00` | 주간 통합판정, EOD/NXT, AI 엔진 A/B 재개 여부 | [2026-04-24 checklist](./2026-04-24-stage2-todo-checklist.md) |

## 10. 과제 상태

| 상태 | 과제 |
| --- | --- |
| 완료 | fallback 관련 축 영구 폐기, main-only 기준 전환, Gemini 라우팅 고정, WAIT65~79 EV 코호트/paper-fill/N gate/probe 계측 |
| 진행중 | `buy_recovery_canary` 1일차 판정 |
| 예정 | 프로파일별 특화 go/no-go, shared 제거 종료판정, `position_context`, HOLDING D+2, `buy_recovery_canary` 종합판정, `entry_filter_quality`, AI 엔진 A/B |
| 후순위 | `position_addition_policy`(`2026-04-23 POSTCLOSE 16:40~16:50`), EOD/NXT(`2026-04-24 POSTCLOSE 15:40~15:50`) |
| 폐기 | `fallback_scout/main`(탐색/본 주문 동시 fallback), `fallback_single`(단일 fallback), legacy shadow 독립축, songstock 비교축 |

## 11. 실제 효과 기록

| 날짜 | 과제 | 실제 효과 | 판정 |
| --- | --- | --- | --- |
| `2026-04-21` | fallback(보조 예외 진입 경로) 폐기 후 main-only(메인서버 단독 기준) 정렬 | `fallback_bundle_ready=0`, `ALLOW_FALLBACK=0` 확인 | 폐기 유지 |
| `2026-04-21` | WAIT65~79 preflight | `total_candidates=54`, `budget_pass=40`, `latency_block=40`, `submitted=0` | 제출 병목 우선 |
| `2026-04-22` | `buy_recovery_canary` 1일차 | TBD | `12:00~12:20` 판정 |
| `2026-04-22` | 프로파일 특화/shared 제거 | TBD | `12:20~12:30` 판정 |
| `2026-04-22` | Plan Rebase 중심 문서 감리 반영 | S-1~S-3, B-1~B-4 반영 | 조건부 승인 시정 완료 |

## 12. 하위 참조문서

| 문서 | 역할 |
| --- | --- |
| [2026-04-22-stage2-todo-checklist.md](./2026-04-22-stage2-todo-checklist.md) | 오늘 실행 체크리스트와 자동 파싱 작업항목 |
| [2026-04-23-stage2-todo-checklist.md](./2026-04-23-stage2-todo-checklist.md) | 다음 영업일 실행 체크리스트 |
| [2026-04-24-stage2-todo-checklist.md](./2026-04-24-stage2-todo-checklist.md) | 주간 통합판정 체크리스트 |
| [2026-04-21-auditor-performance-result-report.md](./2026-04-21-auditor-performance-result-report.md) | 감사 기반 성과/병목 판정 |
| [audit-reports/2026-04-22-plan-rebase-central-audit-review.md](./audit-reports/2026-04-22-plan-rebase-central-audit-review.md) | Plan Rebase 중심 문서 구조/원칙/일정 감리보고서 |
| [workorder-0421-tuning-plan-rebase.md](./workorder-0421-tuning-plan-rebase.md) | Plan Rebase 실행 로그와 상세 근거 |
| [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md) | 원안 대비 실행 변경사항 |
| [plan-korStockScanPerformanceOptimization.performance-report.md](./plan-korStockScanPerformanceOptimization.performance-report.md) | 정기 성과 기준선과 반복 성과값 |
| [plan-korStockScanPerformanceOptimization.qna.md](./plan-korStockScanPerformanceOptimization.qna.md) | 반복 판단 기준과 감리 Q&A |
| [archive/](./archive/) | 폐기 과제, 과거 workorder, legacy shadow/fallback 경과 |
