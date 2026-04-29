# 2026-05-06 Stage2 To-Do Checklist

## 오늘 목적

- 스캘핑 스캐너 미반영 구조 항목을 `실전 한 축 canary` 원칙에 맞게 분해하고 적용 순서를 잠근다.
- `candidate_pool -> enrich -> promoted_watchlist` 3단 구조 전환 범위와 rollback guard를 문서 기준으로 확정한다.
- `ka10095`, 신호 기반 재포착, 시간대별 소스 분기, composite score, DB/WS 경계 재설계를 같은 날 동시 반영하지 않도록 change set을 분리한다.
- 거래대금/VI freshness를 승격 gate에 어떻게 반영할지 정량 기준을 먼저 고정한다.
- `2026-05-05` 어린이날 휴장으로 실행할 수 없던 latency price guard / NaN cast / resolver 후속 항목을 다음 KRX 운영일 기준으로 이관해 닫는다.

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
- 휴장일 이월 항목은 원래 Due가 아니라 실제 KRX 운영일 Due를 기준으로 Project/Calendar에 등록한다.

## 장전 체크리스트 (08:50~09:00)

- 없음

## 장중 체크리스트 (09:00~15:20)

- 없음

## 장후 체크리스트 (16:00~20:55)

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

- [ ] `[LatencyEntryPriceGuard0506HolidayCarry] 3틱 v1 fill/slippage/profit 재튜닝 판정` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 18:45~19:05`, `Track: ScalpingLogic`)
  - Source: [2026-05-05-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-05-05-stage2-todo-checklist.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - 판정 기준: `latency_override_defensive_ticks=3` 적용 cohort와 기존/비적용 normal cohort를 `fill_rate`, `realized_slippage`, `full_fill`, `partial_fill`, `COMPLETED + valid profit_rate`, `normal_slippage_exceeded`로 비교한다.
  - why: `2026-05-05`는 어린이날 휴장이라 실전 표본을 추가할 수 없다. 실제 운영일인 `2026-05-06` 기준으로 3틱 v1의 유지/재튜닝 여부를 닫는다.
  - 다음 액션: 우위가 확인되면 유지 또는 v2 전환 설계로 넘기고, fill 손실/기회비용이 크면 1틱/2틱/가격대별 table 재튜닝 후보를 연다.

- [ ] `[LatencyEntryPriceGuardV2_0506HolidayCarry] bps/가격대별 defensive table 설계` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 19:05~19:20`, `Track: ScalpingLogic`)
  - Source: [2026-05-05-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-05-05-stage2-todo-checklist.md), [2026-04-29-daehan-cable-entry-price-audit-rereport.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-29-daehan-cable-entry-price-audit-rereport.md)
  - 판정 기준: fixed tick 대신 저가주/중가주/고가주 가격대별 bps 부담을 반영한 defensive table을 설계한다.
  - why: 동일 3틱이라도 가격대별 bps 비용이 달라 기대값/체결률 trade-off가 왜곡될 수 있다.
  - 다음 액션: v2 승인 전까지 v1 3틱은 임시값으로만 유지하고, table 후보는 shadow/counterfactual 로그부터 추가한다.

- [ ] `[LatencyExitPriceGuardReview0506HolidayCarry] 매도/청산 latency 가격가드 현황 명문화` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 19:20~19:35`, `Track: ScalpingLogic`)
  - Source: [2026-05-05-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-05-05-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: 이번 변경은 BUY 진입가 전용이다. SELL/청산가에 latency 위험 대칭 정책이 있는지 확인하고, 기존 정책 유지/별도 canary/observe-only 중 하나로 명문화한다.
  - why: 진입 방어폭만 강화하고 청산가 정책을 불명확하게 두면 realized slippage와 missed upside 해석이 섞인다.
  - 다음 액션: 매도 측 정책 변경이 필요하면 진입가 v1 재튜닝과 별도 축으로 분리하고, 같은 날 한 축 canary 원칙을 유지한다.

- [ ] `[NaNCastGuard0506HolidayCarry] NaN cast runtime 안정화 후속계획 확정` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 19:35~19:55`, `Track: RuntimeStability`)
  - Source: [2026-05-05-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-05-05-stage2-todo-checklist.md), [2026-04-28-nan-cast-guard-hotfix-report.md](/home/ubuntu/KORStockScan/docs/2026-04-28-nan-cast-guard-hotfix-report.md)
  - 판정 기준: 원격과 동일 patch set 복제 여부가 아니라 메인 코드베이스 기준 `NaN/inf` 안전 캐스팅 최소 범위, 재발건수, 상태전이 실패 경로, upstream source 후보(`buy_qty/buy_price/target_buy_price/marcap/preset_tp_*`, websocket `curr/ask_tot/bid_tot`, 체결 `price/qty`)를 확정한다.
  - why: `NaN cast`는 루프 중단과 체결 후 상태전이 실패를 만들어 기대값과 미진입/미청산 기회비용을 직접 훼손한다. 휴장일 이월 후에도 메인 기준 수정범위와 재발 방지 계획을 비워두지 않는다.
  - 다음 액션: 메인 기준 최소 safe cast patch 범위와 테스트(`pytest`/`py_compile`)를 잠그고, 재발이 있으면 source 추적 작업을 다음 거래일 PREOPEN/POSTCLOSE checklist로 승격한다.

- [ ] `[PreSubmitGuardDist0506HolidayCarry] 80bps 임계 분포 부록 및 percentile 재앵커` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 19:55~20:10`, `Track: ScalpingLogic`)
  - Source: [2026-05-05-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-05-05-stage2-todo-checklist.md), [2026-04-29-daehan-cable-entry-price-audit-rereport.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-29-daehan-cable-entry-price-audit-rereport.md)
  - 판정 기준: 최근 `30~60` 영업일 `submitted` 코호트를 대상으로 `(best_bid - submitted_price) / best_bid * 10000` 분포를 재구성해 histogram과 `p90/p95/p99/p99.5`를 확정하고, `80bps`가 어느 percentile에 위치하는지 문서 부록으로 고정한다. 현재 `2026-04-28~2026-04-29` stage-paired 표본 `8건`은 provisional reference로만 사용한다.
  - why: 대한전선 단일 사례는 `337~412bps` outlier를 보여주지만, `80bps` 자체의 적정성은 분포 기반으로 다시 잠가야 한다.
  - 다음 액션: `80bps`가 너무 타이트하면 완화 후보를, 너무 느슨하면 강화 후보를 열고, 결정값은 `PreSubmitGuardKPI`와 함께 SLO로 고정한다.

- [ ] `[PreSubmitGuardObserve0506HolidayCarry] 비-SCALPING observe-only guard logging 범위 확정` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 20:10~20:25`, `Track: ScalpingLogic`)
  - Source: [2026-05-05-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-05-05-stage2-todo-checklist.md), [2026-04-29-daehan-cable-entry-price-audit-followup.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-29-daehan-cable-entry-price-audit-followup.md)
  - 판정 기준: `BREAKOUT/PULLBACK/RESERVE` 등 비-`SCALPING` 전략에 대해 차단 없는 `pre_submit_price_guard_observe` 이벤트를 기록할지, 기록한다면 동일 임계(`80bps`)와 어떤 필드(`submitted_order_price`, `best_bid_at_submit`, `price_below_bid_bps`, strategy`)를 남길지 확정한다.
  - why: 차단 없는 observe-only는 회귀 위험이 거의 없으면서도 P1 resolver 설계의 사각지대를 줄인다.
  - 다음 액션: 구현 범위가 잠기면 1~2주 누적 후 전략별 pathology 존재 여부를 닫고, 차단 확대 여부는 분포 기준으로만 결정한다.

- [ ] `[BuyPriceSchemaSplitP1_0506HolidayCarry] submitted_order_price canonical 승격 조건 확정` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 20:25~20:40`, `Track: ScalpingLogic`)
  - Source: [2026-05-05-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-05-05-stage2-todo-checklist.md), [2026-04-29-daehan-cable-entry-price-audit-followup.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-29-daehan-cable-entry-price-audit-followup.md)
  - 판정 기준: `BUY_ORDERED.buy_price`를 언제 `submitted_order_price` canonical로 승격할지 closing condition을 문서로 고정한다. 최소 조건은 `P1 resolver 도입`, downstream 손익/보유/리포트 경로 영향도 목록화, migration/alias 정책 확정이다.
  - why: schema 보존은 P0에서는 맞는 결정이지만, closing condition 없이 두면 영구 부채가 된다.
  - 다음 액션: trigger가 잠기면 P1 change set에 schema split을 묶고, trigger가 아직 모호하면 막힌 조건을 명시한다.

- [ ] `[DynamicEntryResolverIngress0506HolidayCarry] P1 resolver ingress gate와 anchor case 확정` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 20:40~20:55`, `Track: ScalpingLogic`)
  - Source: [2026-05-05-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-05-05-stage2-todo-checklist.md), [2026-04-29-daehan-cable-entry-price-audit-rereport.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-29-daehan-cable-entry-price-audit-rereport.md)
  - 판정 기준: P1 승인 전 단계(`backtest -> observe-only -> canary`)와 각 단계 산출물(`가격차 분포`, `resolver divergence rate`, `submitted_but_unfilled_rate`, `slippage_bps`, `time_to_fill_p50/p90`)을 확정하고, `record_id=4219`가 backtest/observe-only에서 abort되는지 unit test anchor case로 고정한다.
  - why: ingress gate가 없으면 P1이 기술 판단이 아니라 운영 승인 사안으로 변질된다.
  - 다음 액션: gate가 잠기면 `LatencyEntryPriceGuardV2`와 분리된 독립 change set으로 resolver 검증축을 연다.
