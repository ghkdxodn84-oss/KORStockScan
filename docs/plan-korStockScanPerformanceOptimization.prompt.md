# 계획: KORStockScan 성능 최적화 실행안 (Session Prompt)

기준 시각: `2026-04-21 KST (Plan Rebase 반영)`  
역할: 다음 세션에서 중심 기준 문서로 진입하기 위한 **경량 포인터**다.

이 문서는 세션 시작용 경량 포인터다.  
현재 Plan Rebase의 중심 기준은 [plan-korStockScanPerformanceOptimization.rebase.md](./plan-korStockScanPerformanceOptimization.rebase.md)를 우선한다.  
과거 일정, 장문 경과, 상세 해설은 `archive`, `Q&A`, `실행 변경사항`, `정기 성과측정` 문서로 분리한다.

## 현재 Source of Truth

1. 현재 활성 기준은 [plan-korStockScanPerformanceOptimization.rebase.md](./plan-korStockScanPerformanceOptimization.rebase.md)다.
2. 운영 실행표는 날짜별 `stage2 todo checklist`를 우선한다.
3. Plan Rebase 실행 로그와 상세 근거는 [workorder-0421-tuning-plan-rebase.md](./workorder-0421-tuning-plan-rebase.md)를 본다.
4. 감사 기반 성과/병목 판정은 [2026-04-21-auditor-performance-result-report.md](./2026-04-21-auditor-performance-result-report.md)를 본다.
5. [2026-04-21-plan-rebase-auditor-review.md](./archive/legacy-tuning-2026-04-06-to-2026-04-20/2026-04-21-plan-rebase-auditor-review.md), [2026-04-21-plan-rebase-auditor-re-review.md](./archive/legacy-tuning-2026-04-06-to-2026-04-20/2026-04-21-plan-rebase-auditor-re-review.md)는 감사 입력/중간 검토 기록이며, 현재 실행 기준으로 직접 사용하지 않는다.
6. `entry_filter` 문구는 감사인 원문 표현이고, 현재 실행 문서에서는 `entry_filter_quality`를 정식 명칭으로 사용한다.
7. `buy_recovery_canary`는 `entry_filter_quality`와 별도 축이다. `Gemini WAIT 65~79 BUY 회복`만 다룬다.
8. `fallback_scout/main`, `fallback_single`, `latency fallback split-entry` 등 영문 축 표현은 [Plan Rebase 용어 범례](./plan-korStockScanPerformanceOptimization.rebase.md#2-용어-범례)를 우선한다.

## 문서 맵

| 문서 | 역할 | 언제 먼저 보나 |
| --- | --- | --- |
| [plan-korStockScanPerformanceOptimization.rebase.md](./plan-korStockScanPerformanceOptimization.rebase.md) | Plan Rebase 중심 기준과 용어 범례 | 세션 시작 직후 |
| [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md) | 세션 시작용 경량 포인터 | 진입점 확인 시 |
| [plan-korStockScanPerformanceOptimization.qna.md](./plan-korStockScanPerformanceOptimization.qna.md) | 운영 판단 기준/자주 묻는 질문 | 왜 이렇게 운영하는지 확인할 때 |
| [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md) | 기본계획 대비 실행 변경사항 | 원안과 실제 실행이 달라졌을 때 |
| [plan-korStockScanPerformanceOptimization.performance-report.md](./plan-korStockScanPerformanceOptimization.performance-report.md) | 정기 성과측정 기준과 최신 baseline | 장후/주간 성과판정 때 |
| [workorder-0421-tuning-plan-rebase.md](./workorder-0421-tuning-plan-rebase.md) | Plan Rebase 실행 로그와 상세 근거 | 왜 해당 판정이 나왔는지 추적할 때 |
| [2026-04-21-auditor-performance-result-report.md](./2026-04-21-auditor-performance-result-report.md) | 감사 기반 성과/병목 판정 | 수치 근거 확인 시 |
| [plan-korStockScanPerformanceOptimization.archive-2026-04-19.md](./archive/legacy-tuning-2026-04-06-to-2026-04-20/plan-korStockScanPerformanceOptimization.archive-2026-04-19.md) | `2026-04-19` 정리 시점에 prompt에서 걷어낸 상세 경과 | 과거 판단 맥락이 필요할 때 |
| [plan-korStockScanPerformanceOptimization.archive-2026-04-08.md](./archive/legacy-tuning-2026-04-06-to-2026-04-20/plan-korStockScanPerformanceOptimization.archive-2026-04-08.md) | 초기 장문 백업본 | 초기 설계와 초반 구현 이력 확인 시 |
| [2026-04-18-nextweek-validation-axis-table-audited.md](./2026-04-18-nextweek-validation-axis-table-audited.md) | 다음주 일자별 검증축 감사표 | 주간 일정/정합성 점검 시 |
| [2026-04-17-midterm-tuning-performance-report.md](./2026-04-17-midterm-tuning-performance-report.md) | `2026-04-17` 고밀도 표본 기준 중간 진단 | 다음주 우선순위 재판정 시 |
| [workorder-integrated-dashboard-db-migration.md](./archive/legacy-workorders/workorder-integrated-dashboard-db-migration.md) | 통합대시보드 데이터 DB화 작업지시서 | 저장소/API 구조개편 착수 시 |
| `2026-04-20~2026-04-24 stage2 todo checklist` | 날짜별 실제 실행표 | 당일 PREOPEN/INTRADAY/POSTCLOSE 수행 시 |
| [2026-04-10-scalping-ai-coding-instructions.md](./2026-04-10-scalping-ai-coding-instructions.md) | 스캘핑 매매로직 기준 | 코드축 원문 확인 시 |
| [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md) | AI 프롬프트 트랙 기준 | 프롬프트축 원문 확인 시 |

## 문서 운영 규칙

1. 중심 기준은 `rebase` 문서가 소유하고, `prompt`는 세션 시작용 포인터만 남긴다.
2. 기본계획과 실제 실행이 달라지면 `execution-delta`에 먼저 적고, 그 결과만 `prompt`에 반영한다.
3. 장후/주간 성과 기준선과 최근 수치는 `performance-report`에 누적하고, `midterm` 보고서는 시점 진단본으로만 유지한다.
4. 과거 일정표, 완료된 실험의 상세 경과, 이미 지나간 공격 일정은 `archive`로 이동한다.
5. `Q&A`는 문서 책임, 모니터링 기간, 해석 기준 같은 **반복 참조 정책**만 남긴다.
6. 모든 작업일정은 `YYYY-MM-DD KST`, `Slot`, `TimeWindow`로 고정한다. 상대 일정이나 조건부 유예 문구는 사용하지 않는다.
7. live 영향 관찰은 오전/오후 반나절을 넘기지 않는다. 반나절에 미관측이면 관찰축 오류, live 영향 없음, 또는 그대로 진행 가능 중 하나로 닫는다.
8. 봇 재실행이 필요하고 권한/안전 조건이 맞으면 AI가 표준 wrapper로 직접 실행한다. 토큰/계정/운영 승인 경계가 있으면 실행하지 않고 필요한 1개 명령을 사용자에게 요청한다.
9. 문서 변경 후 parser 검증은 AI가 수행한다. Project/Calendar 동기화는 토큰 존재 여부를 AI가 확인하지 말고 사용자 수동 실행 명령 1개를 반드시 남긴다.

## 최종 목표와 운영 원칙

1. 최종 목표는 `손실 억제`가 아니라 `기대값/순이익 극대화`다.
2. 현재 단계는 `Plan Rebase`다. 기존 `partial/rebase/soft_stop/split-entry`(부분체결/기준가 재조정/소프트스탑/분할진입) 승격 판단은 중단하고, `진입/보유/청산 로직표 -> fallback 오염 코호트(보조 예외 진입이 섞인 표본) -> 신규 1축 canary` 순서로 재정렬한다.
3. 실전 변경은 항상 `한 번에 한 축 canary` 원칙을 지킨다.
4. 신규 관찰축/보완축은 `shadow 금지`, `canary-only`로 운영한다.
5. `fallback_scout/main`(탐색 주문/본 주문 동시 fallback 분할진입), `fallback_single`(단일 fallback 진입), `latency fallback split-entry`(지연 상태에서 fallback으로 분할진입하던 폐기축)는 영구 폐기한다. 재개/승격/재평가 canary 대상이 아니다.
6. `NULL`, 미완료 상태, fallback 정규화 값은 손익 기준에서 제외한다. 손익 계산은 `COMPLETED + valid profit_rate`만 사용한다.
7. 장후 리포트의 우선 지표는 `거래수 -> 퍼널 -> blocker -> 체결품질 -> missed_upside -> 손익` 순서다.
8. BUY 후 미진입은 `latency guard miss`, `liquidity gate miss`, `AI threshold miss`, `overbought gate miss`로 분리 해석한다.
9. `full fill`과 `partial fill`은 같은 표본으로 합치지 않는다.
10. 원인 귀속이 불명확하면 먼저 `리포트 정합성`, `이벤트 복원`, `집계 품질`을 점검한다.
11. 다음 정식 튜닝 1순위는 `entry_filter_quality`다. 단, 장중 긴급 실전축인 `main-only buy_recovery_canary`는 별도 회복축으로 분리 추적한다.
12. `holding_exit`, `position_addition_policy`, `EOD/NXT`, AI 엔진 A/B는 후순위다. 단, 보유 AI `position_context` 입력은 더 빠른 `holding_exit` 축에서 별도 1축으로 먼저 설계하고, `position_addition_policy`는 그 결과를 입력 전제로 사용한다.
13. Plan Rebase 기간의 live 스캘핑 AI 라우팅은 Gemini로 고정한다. OpenAI/Gemini A/B 및 dual-persona shadow는 `entry_filter_quality` 1차 판정 완료 후 재개 여부를 별도 판정한다.
14. `PREOPEN(08:00~09:00)`에는 `bot_main` 동작 중 `run_monitor_snapshot` full build를 금지하고, 필요 시 `sanity check`만 수행한다.
15. 물타기/불타기/분할진입은 별도 튜닝축이 아니라 후순위 `position_addition_policy` 상태머신 후보로 묶는다.
16. 개별 종목(예: 에이럭스) 이슈는 단일 원인으로 단정하지 않고 `entry gate + latency + liquidity + holding exit` 관찰축으로 먼저 분해 판정한다.
17. 기준선/롤백/승격 판단은 `문서 파생값`이 아니라 `DB 우선 스냅샷 실필드`만 사용한다.
18. `performance_tuning.trends.*` rolling 값은 당일 손익 baseline/rollback 기준으로 사용하지 않는다.

## 현재 기준 우선순위

| 워크스트림 | 현재 상태 | 판정 | 다음 닫힘 시점 |
| --- | --- | --- | --- |
| `Plan Rebase 정합성` | 로직표/코호트/우선순위 재정렬 완료, 잔여 문서 정리 필요 | `활성 기준` | `2026-04-21~2026-04-22` |
| `buy_recovery_canary` | `WAIT 65~79` 2차 Gemini 재평가 + rollback guard 반영 | `조기적용 완료, 1일차 판정 대기` | `2026-04-22 12:00~12:20` |
| `entry_filter_quality` | 감사인 정의의 정식 다음축 | `1순위 canary 후보` | `2026-04-23 POSTCLOSE 15:20~15:35` |
| `AIPrompt 프로파일별 특화` | 프로파일/액션 스키마 이식 완료, `shared` 잔여 의존 범위 잠금 완료. 04-22 PREOPEN 즉시 착수는 하지 않고 오전 반나절만 관찰 | `shadow 없이 canary 필요시 1축`. `09:00~12:00` 미관측 후보는 추가 유예 없이 관찰축 오류 또는 live 영향 없음으로 닫는다 | `2026-04-22 12:20~12:30` go/no-go 강제판정 |
| `HOLDING/청산` | action schema 분리 및 D+2 판정 구조 유지, 보유 AI `position_context` 입력 스키마 별도 1축 설계. 검증은 shadow 없이 canary + rollback guard로만 수행 | `후순위 판정 + 입력 보강 1축` | `2026-04-22 POSTCLOSE 15:40~16:00` |
| `position_addition_policy` | 불타기/물타기/추가진입 중단 상태머신 후보. `position_context` 확정 후 연결 | `후순위 설계` | `holding_exit position_context` 이후 |
| `AI 엔진 A/B` | Gemini live 고정, OpenAI/Gemini A/B 보류 | `재개 여부 별도 판정` | `2026-04-24 POSTCLOSE 15:50~16:00` |

## 2026-04-20~2026-04-24 실행 맵

| 일자 | 핵심 실행축 | 실행 원칙 | 기대 산출물 |
| --- | --- | --- | --- |
| `2026-04-21 (화)` | Plan Rebase 전환, fallback 영구 폐기, Gemini 라우팅 고정, `buy_recovery_canary` 조기적용 | 기존 split-entry/fallback 승격 흐름 중단, `main-only` 기준으로 재정렬 | 로직표, 오염 코호트, `buy_recovery_canary` guard, 04-22 판정 슬롯 |
| `2026-04-22 (수)` | `buy_recovery_canary` 오전 표본 판정, 프로파일별 특화 프롬프트 잔여과제 범위 잠금, HOLDING D+2 판정, 보유 AI `position_context` 입력 1축 설계, `buy_recovery_canary` 종합판정 | shadow 금지, 필요 시 canary 1축만 허용. 프로파일별 특화는 `09:00~12:00` 오전 반나절 관찰 후 `12:20~12:30`에 `watching 특화 / holding 특화 / exit 특화 / shared 제거 / 전부 미착수` 중 하나로 강제 종료한다. `position_context`는 live 완화와 묶지 않고 설계/테스트/로그 필드 고정까지만 처리하며, 검증은 `holding_exit position_context canary` + rollback guard로만 수행 | 유지/롤백/재교정 사유, 프로파일별 특화 canary 1축 또는 전부 미착수, `shared 제거=live canary/코드정리/현행유지` 판정, `position_context` 스키마, `17:00 KST` 다음 액션 |
| `2026-04-23 (목)` | `entry_filter_quality` 착수 가능성 재판정(`15:20~15:35`), A/B preflight 범위 확정(`15:35~15:50`), `position_addition_policy` 초안(`16:40~16:50`) | `buy_recovery_canary`와 혼용 금지, A/B는 아직 재개 판정 전, `position_addition_policy`는 live 적용 없이 후순위 설계만 허용 | 다음 정식 canary 후보와 rollback guard |
| `2026-04-24 (금)` | 주간 통합판정 + EOD/NXT 착수 여부 + AI 엔진 A/B 재개 여부 판정(`15:20~16:00`) | `entry_filter_quality` 1차 판정 완료 또는 최대기한 도달 시 별도 판정 | 다음주 PREOPEN 승격축 1개 또는 A/B/추가보류 사유 |

## 승격/보류 게이트

1. `live` 승격은 하루에 `1축`만 연다.
2. 신규 관찰축/보완축은 shadow를 만들지 않고 canary로만 착수한다.
3. 모든 판정 행에는 최소 `N_min`, `PrimaryMetric`, rollback guard를 남긴다.
4. `buy_recovery_canary` guard는 `N_min`, `loss_cap`, `reject_rate`, `latency_p95`, `partial_fill_ratio`, `fallback_regression`, `buy_drought_persist`, `recovery_false_positive_rate`를 사용한다.
5. HOLDING 성과판정은 schema 변경 직후에 내리지 않고 최소 `D+2`에 내린다.
6. `counterfactual` 수치는 직접 실현손익과 합산하지 않고 우선순위 판단 자료로만 쓴다.
7. `full fill`, `partial fill`, `fallback_contaminated`, `normal_only`, `post_fallback_deprecation`은 항상 별도 코호트로 본다.
8. `same_symbol_repeat`는 원 raw 필드/산식 추적 전까지 원인축이 아니라 참고 코호트로만 본다.
9. `entry_filter_quality`와 `buy_recovery_canary`는 명칭과 판정 지표를 혼용하지 않는다.
10. `AIPrompt 프로파일별 특화` go/no-go는 `2026-04-22 12:20~12:30 KST`에 닫는다. `shared 제거`는 `09:00~12:00`에 `ai_prompt_type=scalping_shared`가 주문 제출/보유/청산 의사결정에 연결되지 않으면 live canary 후보에서 제외하고 코드정리 또는 현행 유지로 처리한다.

## 현재 기준 문서 입력 규칙

1. 날짜별 실제 실행과 판정은 해당 `stage2 todo checklist`에 남긴다.
2. 원문 계획과 다른 실행 변경은 [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md)에 남긴다.
3. 장후/주간 baseline과 반복 성과값은 [plan-korStockScanPerformanceOptimization.performance-report.md](./plan-korStockScanPerformanceOptimization.performance-report.md)에 누적한다.
4. 장문 경과, 이미 지난 공격 일정, 세부 구현 경위는 archive로 이동한다.

## 현재 참고 문서

- [2026-04-18-nextweek-validation-axis-table-audited.md](./2026-04-18-nextweek-validation-axis-table-audited.md)
- [2026-04-17-midterm-tuning-performance-report.md](./2026-04-17-midterm-tuning-performance-report.md)
- [workorder-integrated-dashboard-db-migration.md](./archive/legacy-workorders/workorder-integrated-dashboard-db-migration.md)
- [2026-04-20-stage2-todo-checklist.md](./2026-04-20-stage2-todo-checklist.md)
- [2026-04-21-stage2-todo-checklist.md](./2026-04-21-stage2-todo-checklist.md)
- [2026-04-22-stage2-todo-checklist.md](./2026-04-22-stage2-todo-checklist.md)
- [2026-04-23-stage2-todo-checklist.md](./2026-04-23-stage2-todo-checklist.md)
- [2026-04-24-stage2-todo-checklist.md](./2026-04-24-stage2-todo-checklist.md)
- [2026-04-10-scalping-ai-coding-instructions.md](./2026-04-10-scalping-ai-coding-instructions.md)
- [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md)
- [2026-04-16-holding-profit-conversion-plan.md](./2026-04-16-holding-profit-conversion-plan.md)
