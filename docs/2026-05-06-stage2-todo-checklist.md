# 2026-05-06 Stage2 To-Do Checklist

## 오늘 목적

- 스캘핑 스캐너 미반영 구조 항목을 `실전 한 축 canary` 원칙에 맞게 분해하고 적용 순서를 잠근다.
- `candidate_pool -> enrich -> promoted_watchlist` 3단 구조 전환 범위와 rollback guard를 문서 기준으로 확정한다.
- `ka10095`, 신호 기반 재포착, 시간대별 소스 분기, composite score, DB/WS 경계 재설계를 같은 날 동시 반영하지 않도록 change set을 분리한다.
- 거래대금/VI freshness를 승격 gate에 어떻게 반영할지 정량 기준을 먼저 고정한다.

## 오늘 강제 규칙

- 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이며 상세 기준은 `Plan Rebase` §1~§6을 따른다.
- live 변경은 동일 단계 내 `1축 canary`만 허용한다. 진입병목축과 보유/청산축은 별개 단계이므로 병렬 canary가 가능하지만, 같은 단계 안에서는 canary 중복을 금지한다.
- 동일 단계 replacement는 `기존 축 OFF -> restart.flag -> 새 축 ON` 순서만 쓴다.
- 관찰창이 끝나면 `즉시 판정 -> 다음 축 즉시 착수`를 기본으로 한다. 이미 수집된 데이터로 닫을 수 있는 판정은 장후/익일로 미루지 않는다.
- `장후/익일/다음 장전` 이관은 예외사유 4종(`단일 조작점 미정`, `rollback guard 미문서화`, `restart/code-load 불가`, `운영 경계상 same-day 반영 불가`) 중 하나로만 허용한다. 막힌 조건과 다음 절대시각이 없으면 이관 판정은 무효다.
- PREOPEN은 전일에 이미 `단일 조작점 + rollback guard + 코드/테스트 + restart 절차`가 준비된 carry-over 축만 받는다.
- 일정은 모두 `YYYY-MM-DD KST`, `Slot`, `TimeWindow`로 고정한다.
- 손익은 `COMPLETED + valid profit_rate`만 사용하고 `full fill`과 `partial fill`은 분리한다.
- live 승인, replacement, stage-disjoint 예외, 관찰 개시 판정에는 `cohort`를 같이 잠근다. 최소 `baseline cohort`, `candidate live cohort`, `observe-only cohort`, `excluded cohort`를 구분하고 `partial/full`, `initial/pyramid`, `fallback` 혼합 결론을 금지한다.
- `ApplyTarget`은 문서에 명시된 값만 사용하고, parser/workorder가 `remote`를 추정하지 않도록 유지한다.
- 다축 동시 변경 금지, 승인 전 `main` 실주문 변경 금지 규칙을 유지한다.

## 장전 체크리스트 (08:50~09:00)

- 없음

## 장중 체크리스트 (09:00~15:20)

- 없음

## 장후 체크리스트 (16:00~17:30)

- [ ] `[ScalpingScannerTxnBoundary0506] DB/WS 경계 재설계와 rollback guard 확정` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:20`, `Track: ScalpingLogic`)
  - Source: [2026-04-28-scalping-scanner-enhancement-proposal.md](/home/ubuntu/KORStockScan/docs/2026-04-28-scalping-scanner-enhancement-proposal.md), [scalping_scanner.py](/home/ubuntu/KORStockScan/src/scanners/scalping_scanner.py:281)
  - 판정 기준: `DB 저장 -> recent_picks 기억 -> COMMAND_WS_REG 발행` 경계에서 발생할 수 있는 부분 커밋/미발행 불일치 케이스를 `failure matrix`, `rollback guard`, `canary-only 적용 범위`로 문서화하고, `일괄 커밋`, `후행 WS 발행`, `outbox`, `shadow-only 계측` 중 다음 change set 1개만 고른다.
  - why: 현재 구조는 런타임 중단 위험은 줄였지만 완전한 정합성 보장은 없다. 이 경계를 먼저 잠그지 않으면 후속 구조 변경의 원인귀속이 흐려진다.
  - 다음 액션: 선택한 경계 재설계안이 `same-day code/test/restart` 가능하면 `2026-05-07 PREOPEN` carry-over로 넘기고, 아니면 막힌 조건과 단일 조작점을 같은 항목에 남긴다.

- [ ] `[ScalpingScannerStageSplit0506] candidate_pool/enrich/promoted_watchlist 3단 구조 분해` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 16:20~16:40`, `Track: ScalpingLogic`)
  - Source: [2026-04-28-scalping-scanner-enhancement-proposal.md](/home/ubuntu/KORStockScan/docs/2026-04-28-scalping-scanner-enhancement-proposal.md), [scalping_scanner.py](/home/ubuntu/KORStockScan/src/scanners/scalping_scanner.py:214)
  - 판정 기준: `발굴(source)`, `정제(enrich)`, `승격(promote)` 단계별 데이터 구조, 함수 ownership, 저장 경계, `recent_picks`/`promoted_watchlist` 책임, 테스트 분리를 표로 고정한다.
  - why: `찾은 종목 = 바로 WS 등록 후보` 구조를 그대로 두면 소스 확장과 품질 정제를 더할수록 WS 부하와 승격 기준이 함께 엉킨다.
  - 다음 액션: 단계 분해안이 잠기면 `2026-05-07` 이후 구현 change set을 `1) stage split`, `2) enrich`, `3) gate tuning` 순으로 배치한다.

- [ ] `[ScalpingScannerEnrich0506] ka10095 일괄 정제와 승격 gate 정량 기준 확정` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 16:40~17:00`, `Track: ScalpingLogic`)
  - Source: [2026-04-28-scalping-scanner-enhancement-proposal.md](/home/ubuntu/KORStockScan/docs/2026-04-28-scalping-scanner-enhancement-proposal.md:219), [scalping-scanner-improvement-proposal.md](/home/ubuntu/KORStockScan/docs/scalping-scanner-improvement-proposal.md:41)
  - 판정 기준: 후보 상위 `N`개에 대한 `ka10095` 일괄 정제 호출 시점, rate-limit budget, 실패 fallback, 그리고 승격 gate에 넣을 `TradeValue`, `RankJump`, `VIReleaseTime freshness`, `CntrStr acceleration` 필드를 확정한다.
  - why: 거래대금 정보가 점수에만 약하게 반영된 상태로는 기대값 관점의 유동성 검증이 부족하다. 승격 gate를 먼저 잠가야 full/partial 체결 품질과 missed upside를 같이 볼 수 있다.
  - 다음 액션: gate 기준이 잠기면 `observe-only enrich log` 또는 `canary-only hard gate` 중 하나만 다음 슬롯에 올리고, 둘을 같은 날 동시에 열지 않는다.

- [ ] `[ScalpingScannerReentrySource0506] 신호 기반 재포착과 시간대별 소스 분기 규칙 확정` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: ScalpingLogic`)
  - Source: [2026-04-28-scalping-scanner-enhancement-proposal.md](/home/ubuntu/KORStockScan/docs/2026-04-28-scalping-scanner-enhancement-proposal.md:345), [scalping-scanner-improvement-proposal.md](/home/ubuntu/KORStockScan/docs/scalping-scanner-improvement-proposal.md:202)
  - 판정 기준: 고정 `25분 cooldown`을 대체할 `reentry predicates`와 `09:05~09:30`, `09:30~14:00`, `14:00~15:00` 시간대별 활성 소스 세트를 정의하고, `latency guard miss`, `liquidity gate miss`, `AI threshold miss`, `overbought gate miss`와의 충돌 없이 분리되는지 확인한다.
  - why: 재포착 규칙과 소스 분기를 같이 설계하되, 실전 반영은 별개 축으로 분리해야 missed opportunity와 WS 중복 부하를 동시에 관리할 수 있다.
  - 다음 액션: source split과 reentry 중 먼저 적용할 1축을 고르고, 나머지는 `observe-only`로 유지한다.

- [ ] `[ScalpingScannerCompositeScore0506] composite score 표준화와 canary 적용 순서 확정` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 17:15~17:30`, `Track: ScalpingLogic`)
  - Source: [scalping-scanner-improvement-proposal.md](/home/ubuntu/KORStockScan/docs/scalping-scanner-improvement-proposal.md:173), [2026-04-28-scalping-scanner-enhancement-proposal.md](/home/ubuntu/KORStockScan/docs/2026-04-28-scalping-scanner-enhancement-proposal.md)
  - 판정 기준: 기존 `_freshness_score` 대비 `z-score` 또는 동등한 standardized composite score의 입력 필드, 시장 분포 기준, shadow-only 계측 기간, pass/fail 기준, full/partial 분리 평가 규칙을 문서화한다.
  - why: 점수 체계를 바꾸면 승격 순서 전체가 바뀌므로 source/gate 변경과 같은 날 겹치면 기대값 개선 원인귀속이 깨진다.
  - 다음 액션: composite score는 source/gate 변경 이후 독립 canary로만 올리고, 표준화 분포가 비어 있으면 `shadow-only 계측`부터 연다.

- [ ] `[StateHandlersContext0506] sniper_state_handlers globals/context 경계 재설계` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 17:30~17:50`, `Track: ScalpingLogic`)
  - Source: [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:58), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `KIWOOM_TOKEN`, `DB`, `EVENT_BUS`, `ACTIVE_TARGETS`, `COOLDOWNS`, `ALERTED_STOCKS`, `HIGHEST_PRICES`, `LAST_LOG_TIMES`, `LAST_AI_CALL_TIMES` 등 모듈 전역 의존성을 `EngineContext` 또는 동등한 명시 context로 묶고, handler 호출부에 전달할 최소 필드/테스트 경계를 표로 확정한다.
  - why: 현재 구조는 테스트 격리, 병렬 실행, 함수 수준 검증을 어렵게 만든다. same-day 핫픽스 대상은 아니지만 구조 debt를 계속 미루면 진입/보유/청산 축 변경의 원인귀속이 점점 더 어려워진다.
  - 다음 액션: context 범위가 잠기면 `2026-05-07` 이후 구현 change set을 `1) context 주입`, `2) state handler split`, `3) cancellation/reconciliation dedupe` 순으로 분리한다.

- [ ] `[StateHandlersSplit0506] watching/holding/cancel 경로 모듈 분해와 ownership 고정` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 17:50~18:15`, `Track: ScalpingLogic`)
  - Source: [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:1834), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:3336)
  - 판정 기준: `handle_watching_state`, `handle_holding_state`, `process_order_cancellation/_cancel_pending_entry_orders`를 entry/holding/cancel 모듈로 나눌 때의 함수 ownership, shared helper 경계, nested function 추출 대상, 중복 DB 복구 경로를 고정한다.
  - why: 5k+ 라인 단일 모듈과 깊은 중첩은 변경 위험을 키우고 리뷰/테스트 비용을 급격히 높인다. 현재 리뷰에서 지적된 `locals()` 패턴, nested closure, cancellation 중복도 결국 이 분해가 안 되어 생긴 부작용이다.
  - 다음 액션: 분해 순서가 잠기면 `watching -> holding -> cancellation` 순의 소규모 change set으로 진행하고, 각 change set마다 rollback guard와 pytest 범위를 함께 잠근다.

- [ ] `[SwingTrailingPolicy0506] KOSDAQ/KOSPI trailing TODO 정량 정책화` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 18:15~18:30`, `Track: ScalpingLogic`)
  - Source: [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:4194), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:4238)
  - 판정 기준: KOSDAQ 되밀림 폭 `1.0%`와 KOSPI `TRAILING_START_PCT 즉시익절`을 유지/통합/분리 중 하나로 닫고, `TRAILING_DRAWDOWN_PCT`, `TRAILING_START_PCT`, 전략별 적용 범위를 문서 기준으로 명문화한다.
  - why: 코드 주석 TODO로만 남겨두면 실전 trailing 정책이 리뷰 결과와 분리되어 누락될 수 있다.
  - 다음 액션: 정책이 잠기면 주석 TODO를 제거하고 테스트/체크리스트/기준문서에 동일 용어로 반영한다.

- [ ] `[CodeDebt0506] shadow/canary/cohort 런타임 분류 및 정리 판정` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 18:30~18:45`, `Track: Plan`)
  - Source: [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: 스캐너 구조 변경 후보를 `remove`, `observe-only`, `baseline-promote`, `active-canary` 중 어디에 둘지 닫고, `baseline cohort`, `candidate live cohort`, `observe-only cohort`, `excluded cohort`, `rollback owner`, `cross-contamination check`를 같이 잠근다.
  - why: 스캐너 구조 변경은 진입병목축 판정에 직접 들어가므로 cohort 분류를 먼저 잠그지 않으면 다음 실전 축에서 원인귀속이 흐려진다.
  - 다음 액션: 상태 변경이 있으면 관련 기준문서와 구현 체크리스트를 같은 change set에서 갱신하고, 변동이 없으면 `변동 없음`과 근거를 남긴다.
