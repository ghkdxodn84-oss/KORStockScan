# 2026-05-06 Stage2 To-Do Checklist

## 오늘 목적

- 스캘핑 스캐너 미반영 구조 항목을 `실전 한 축 canary` 원칙에 맞게 분해하고 적용 순서를 잠근다.
- `candidate_pool -> enrich -> promoted_watchlist` 3단 구조 전환 범위와 rollback guard를 문서 기준으로 확정한다.
- `ka10095`, 신호 기반 재포착, 시간대별 소스 분기, composite score, DB/WS 경계 재설계를 같은 날 동시 반영하지 않도록 change set을 분리한다.
- 거래대금/VI freshness를 승격 gate에 어떻게 반영할지 정량 기준을 먼저 고정한다.
- `2026-05-05` 어린이날 휴장으로 실행할 수 없던 latency price guard / NaN cast / resolver 후속 항목을 다음 KRX 운영일 기준으로 이관해 닫는다.
- `REVERSAL_ADD`와 `PYRAMID` 수량 산식이 현재 고정 비율+cap 구조에 머무르는지 점검하고, 동적 수량화는 observe-only/counterfactual 설계로 먼저 분리한다.
- 가격대/거래량/시간대별 `exit_only`, `avg_down_wait`, `pyramid_wait` 실적 통계는 live 판단이 아니라 장후 threshold weight 입력으로 먼저 검증한다.
- `statistical_action_weight` 2차 고급축은 parking하지 않고 `SAW-1~SAW-6` 단계 로드맵으로 추적한다.
- AI 보유/청산 판단에도 통계 matrix를 참조시키는 `ADM-1~ADM-5` 로드맵을 threshold 적용과 별도 축으로 분리한다.

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

## 장후 체크리스트 (16:00~23:59)

- [ ] `[ScalpingScannerTxnBoundary0506] DB/WS 경계 재설계와 rollback guard 확정` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:20`, `Track: ScalpingLogic`)
  - Source: [2026-04-28-scalping-scanner-enhancement-proposal.md](/home/ubuntu/KORStockScan/docs/2026-04-28-scalping-scanner-enhancement-proposal.md), [scalping_scanner.py](/home/ubuntu/KORStockScan/src/scanners/scalping_scanner.py:281)
  - 판정 기준: `DB 저장 -> recent_picks 기억 -> COMMAND_WS_REG 발행` 경계에서 발생할 수 있는 부분 커밋/미발행 불일치 케이스를 `failure matrix`, `rollback guard`, `canary-only 적용 범위`로 문서화하고, `일괄 커밋`, `후행 WS 발행`, `outbox`, `observe-only 계측` 중 다음 change set 1개만 고른다.
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
  - 판정 기준: 기존 `_freshness_score` 대비 `z-score` 또는 동등한 standardized composite score의 입력 필드, 시장 분포 기준, observe-only 계측 기간, pass/fail 기준, full/partial 분리 평가 규칙을 문서화한다.
  - why: 점수 체계를 바꾸면 승격 순서 전체가 바뀌므로 source/gate 변경과 같은 날 겹치면 기대값 개선 원인귀속이 깨진다.
  - 다음 액션: composite score는 source/gate 변경 이후 독립 canary로만 올리고, 표준화 분포가 비어 있으면 `observe-only 분포 계측`부터 연다.

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
  - 다음 액션: v2 승인 전까지 v1 3틱은 임시값으로만 유지하고, table 후보는 observe-only/counterfactual 로그부터 추가한다.

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

- [ ] `[ExecutionReceiptsThreadSafety0506] receipt lock/snapshot 경계 재설계` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 20:55~21:10`, `Track: RuntimeStability`)
  - Source: [code-review-20260430-sniper-engine.md](/home/ubuntu/KORStockScan/docs/code-review-20260430-sniper-engine.md), [sniper_execution_receipts.py](/home/ubuntu/KORStockScan/src/engine/sniper_execution_receipts.py:38), [sniper_execution_receipts.py](/home/ubuntu/KORStockScan/src/engine/sniper_execution_receipts.py:1046)
  - 판정 기준: 1차 반영된 `RECEIPT_LOCK` 분리, `state_lock` 주입, `snapshot` 인자화 이후에도 `active order binding`, `BUY/ADD/SELL` 체결, `BROKER_RECOVER` 보정 경로에서 race 또는 truth drift가 없는지 점검한다. `weighted_avg_price` vs `_weighted_avg` canonical 단일화는 `2026-04-30`에 receipt 모듈 정밀 평균가 고정으로 닫혔고, `_find_execution_target` 매칭 우선순위도 `bundle -> terminal -> BUY_ORDERED exact -> pending_add exact -> single candidate` 테스트로 고정됐다. 남은 결정사항은 `RECEIPT_LOCK`/`ENTRY_LOCK` 운영상 ownership guide와 residual race review다.
  - why: 설계 여부 자체는 이미 일부 코드로 굳었다. 이제 남은 리스크는 `락을 왜 나눴는지`, `어떤 경로가 어느 락을 소유하는지`, `주석/테스트로 고정한 규칙과 실제 장중 event order가 어긋나는지`를 운영 기준으로 재검토하지 않은 점이다. 실전 체결 truth 품질이 흔들리면 entry/holding 개선의 원인귀속이 깨진다.
  - 다음 액션: `1) lock ownership guide 문서화`, `2) residual race review`, `3) 장중 anomaly case와 테스트 우선순위 대조` 순서로 닫는다.

- [ ] `[HoldingNetProfitExitRegression0506] holding_state net-profit sell decision 회귀 원인 격리` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 21:10~21:25`, `Track: RuntimeStability`)
  - Source: [test_live_trade_profit_rate.py](/home/ubuntu/KORStockScan/src/tests/test_live_trade_profit_rate.py:540), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)
  - 판정 기준: `test_holding_state_uses_net_profit_rate_for_sell_decision`가 왜 `sell_calls` 없이 끝나는지 원인을 분해하고, `KOSPI_ML` 보유 청산 결정 경로에서 `net profit rate` 기반 sell trigger가 여전히 살아있는지 확인한다. 최소 기준은 failing test 재현, 분기 원인 식별, 수정 또는 의도적 정책 변경 중 하나를 문서로 잠그는 것이다.
  - why: 이번 change set의 타깃 테스트는 green이지만 broader regression 기준으로는 holding exit 경로 1건이 여전히 실패한다. 이 상태를 문서화하지 않으면 `타깃 검증 통과`가 `전체 hold/exit 회귀 없음`으로 오해될 수 있다.
  - 다음 액션: 원인이 기존 정책 변경이면 테스트 기대값을 Plan Rebase 기준으로 재정의하고, 실제 회귀면 별도 patch로 분리해 고친다.

- [ ] `[ReversalAddDynamicQty0506] REVERSAL_ADD 동적 수량 산식 observe-only 설계` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [personal-decision-flow-notes.md](/home/ubuntu/KORStockScan/docs/personal-decision-flow-notes.md), [sniper_scale_in.py](/home/ubuntu/KORStockScan/src/engine/sniper_scale_in.py:400), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: 현재 `REVERSAL_ADD` 수량이 `buy_qty * REVERSAL_ADD_SIZE_RATIO` + `MAX_POSITION_PCT` cap + 1주 floor에 머무르는지 확인하고, `AI 회복폭`, `수급 3/4~4/4`, `soft/hard stop 거리`, `peak_profit never-green`, `remaining_budget`, `volatility`를 반영한 `would_qty` counterfactual 산식을 설계한다. live 수량 변경은 이 항목에서 켜지 않는다.
  - why: 유효 진입 회수형 추가매수라면 수량도 현재 상태 기반으로 재산정하는 편이 EV 관점에서 자연스럽다. 다만 `REVERSAL_ADD` 자체가 신규 holding canary라 수량까지 동시에 바꾸면 같은 단계 다축 변경이 되어 손익/soft stop tail 원인귀속이 깨진다.
  - 다음 액션: 산식 후보가 잠기면 `actual_qty`, `would_qty`, `qty_reason`, `post_add_mfe`, `post_add_stop_rate`, `COMPLETED + valid profit_rate`를 observe-only 로그로 먼저 남기고, 최소 표본 확보 후 별도 단일축 canary로 승격 여부를 판단한다.

- [ ] `[PyramidDynamicQty0506] PYRAMID 불타기 동적 수량 산식 observe-only 설계` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [personal-decision-flow-notes.md](/home/ubuntu/KORStockScan/docs/personal-decision-flow-notes.md), [sniper_scale_in.py](/home/ubuntu/KORStockScan/src/engine/sniper_scale_in.py:142), [sniper_scale_in.py](/home/ubuntu/KORStockScan/src/engine/sniper_scale_in.py:400)
  - 판정 기준: 현재 스캘핑 `PYRAMID` 수량이 `buy_qty * 0.50` + `MAX_POSITION_PCT` cap + 선택적 zero-qty floor 구조에 머무르는지 확인하고, `is_new_high`, `peak_profit - profit_rate <= 0.3`, 수익률 레벨, AI/수급 지속성, trailing giveback 여유, 당일 same-symbol reentry 여부를 반영한 `pyramid_would_qty` counterfactual 산식을 설계한다. live 수량 변경은 이 항목에서 켜지 않는다.
  - why: 불타기는 손실 회수형 `REVERSAL_ADD`보다 winner size-up 효과가 직접적이라 EV 개선 여지가 크다. 그러나 `initial-only`, `pyramid-activated`, `REVERSAL_ADD`, `soft_stop` 표본을 섞으면 원인귀속이 깨지므로 불타기 수량 동적화는 독립 observe-only 축으로만 연다.
  - 다음 액션: 산식 후보가 잠기면 `actual_qty`, `pyramid_would_qty`, `qty_reason`, `post_add_mfe`, `trailing_exit`, `COMPLETED + valid profit_rate`, `soft_stop` 전환율을 분리 로깅하고, 최소 표본 확보 후 별도 단일축 canary 후보로만 승격 검토한다.

- [ ] `[ThresholdCollectorIO0506] threshold 데이터 수집 IO 과부하 재발성 판정 및 증분 collector 설계` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 21:55~22:10`, `Track: RuntimeStability`)
  - Source: [2026-04-30-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-30-stage2-todo-checklist.md), [2026-04-30-data-driven-threshold-inventory.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-30-data-driven-threshold-inventory.md)
  - 판정 기준: `PerformanceTuningSnapshot` 및 `daily_threshold_cycle_report` 생성 시 스토리지 IO 과부하가 `초기 데이터 적재 1회성`인지, `매 사이클 raw jsonl full scan`으로 반복되는지 구분한다. `pipeline_events_YYYY-MM-DD.jsonl` 크기, cycle 실행 횟수, read bytes, wall time, lock contention, system availability 저하 로그를 함께 본다.
  - why: threshold 데이터 수집이 기대값 개선을 위한 핵심 기반이더라도, 장중/장후마다 400MB~GB급 raw 파일을 반복 스캔하면 실전 가용성과 체결 truth 품질을 훼손한다.
  - 다음 액션: 반복성 과부하면 cursor 기반 증분 collector, stage 필터 사전집계, 일자/분 단위 partition, single-pass shared snapshot 중 하나를 다음 구현 항목으로 고정한다. 1회성 초기 적재면 운영문서에 cold-start 예외와 금지 시간대를 명시한다.

- [ ] `[ThresholdOpsTransition0506] threshold 운영전환 자동화 acceptance 확정` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 22:10~22:30`, `Track: RuntimeStability`)
  - Source: [2026-04-30-data-driven-threshold-inventory.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-30-data-driven-threshold-inventory.md), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py), [backfill_threshold_cycle_events.py](/home/ubuntu/KORStockScan/src/engine/backfill_threshold_cycle_events.py)
  - 판정 기준: 최종 안정화 후 운영전환 acceptance가 `매일 자동 실행`, `다음 장전 승인 threshold 자동 적용 + 봇 기동`, `장후 threshold version별 실적분석 제출`, `실적 결과 기반 다음 threshold weight 미세조정` 4개를 모두 포함하는지 확인한다.
  - 현재 자동화 상태: `2026-05-01`에 4월 가용 raw partition bootstrap을 완료했고, `07:35 PREOPEN apply manifest`, `16:10 POSTCLOSE collector/report` cron을 설치했다. 단 live threshold runtime mutation은 acceptance 전까지 `manifest_only`다.
  - why: threshold cycle이 수동 리포트에 머물면 데이터 기반 완화값이 실전 기대값 개선으로 연결되지 않는다. 반대로 장중 실시간 자동변경으로 가면 원인귀속과 rollback guard가 깨지므로, 자동화는 일일 배치/다음 장전 적용 단위로만 닫아야 한다.
  - 다음 액션: acceptance가 잠기면 workflow/cron 설계 항목을 분리한다. 장중 compact collector, 장후 report+weight 산정, 장전 apply+bot start, 장후 performance attribution report를 각각 재실행 가능한 wrapper로 정의한다.

- [ ] `[StatActionWeight0506] 가격대/거래량/시간대별 행동가중치 리포트 1차 판정` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 22:30~22:50`, `Track: ScalpingLogic`)
  - Source: [2026-04-30-data-driven-threshold-inventory.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-30-data-driven-threshold-inventory.md), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py), [threshold_cycle_registry.py](/home/ubuntu/KORStockScan/src/utils/threshold_cycle_registry.py)
  - 판정 기준: `statistical_action_weight` family의 `price_bucket`, `volume_bucket`, `time_bucket`별 `exit_only`, `avg_down_wait`, `pyramid_wait` 표본과 평균손익/승률을 확인한다. 추가로 `stat_action_decision_snapshot`의 `chosen_action`, `eligible_actions`, `rejected_actions`, `scale_in_gate_reason`, `exit_rule_candidate`가 충분히 적재됐는지 본다. 단순 평균이 아니라 `confidence_adjusted_score`, `edge_margin`, `policy_hint(no_clear_edge/defensive_only_high_loss_rate/candidate_weight_source)`를 기준으로 본다. `volume_unknown` 비중이 높으면 거래량 결론은 금지하고 가격대/시간대 direction-only만 남긴다.
  - why: 현재 전략계층은 전문가 규칙 중심이라 “어떤 장면에서는 청산, 어떤 장면에서는 물타기/불타기 후 대기”라는 통계적 행동가중치가 부족했다. 이 축은 live 변경이 아니라 다음 threshold weight와 동적 수량 설계의 근거다. 작은 표본의 우연한 평균값을 믿지 않기 위해 empirical-bayes shrinkage와 불확실성 penalty를 같이 본다.
  - 다음 액션: sample-ready이면 다음 장후 산정에서 threshold weight 입력으로 연결하고, 부족하면 누락 필드(`daily_volume`, `buy_time`, `scale_in_executed`, `exit_signal`, `sell_completed`, `stat_action_decision_snapshot`) 적재 품질부터 보강한다. 4월 historical compact는 registry 추가 전 bootstrap이라 action stage가 비어 있을 수 있으므로, 필요하면 IO guard가 있는 maintenance backfill로 action family만 재적재한다.

- [ ] `[StatActionMarkdown0506] statistical_action_weight 운영자용 Markdown 리포트 자동생성 구현` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 22:50~23:10`, `Track: ScalpingLogic`)
  - Source: [2026-04-30-data-driven-threshold-inventory.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-30-data-driven-threshold-inventory.md), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: 장후 threshold cycle 실행 시 `data/report/statistical_action_weight/statistical_action_weight_YYYY-MM-DD.md`와 `.json`이 자동 생성되는지 확인한다. Markdown은 `판정`, `표본 충분성`, `price/volume/time bucket별 best action`, `no_clear_edge/insufficient_sample`, `threshold 반영 금지/가능 항목`, `다음 액션`을 포함해야 한다.
  - 선반영 메모: `2026-05-01` 휴장 maintenance에서 구현/테스트는 완료했다. 5/6에는 실제 운영일 postclose 자동 실행 산출물 health check와 표본 충분성 판정을 수행한다.
  - why: 현재 `statistical_action_weight`는 기계용 JSON 내부 섹션으로만 존재해 매일 사람이 읽고 의사결정하기 어렵다. 독립 Markdown이 없으면 2차 고급축 판정도 운영 흐름에서 누락될 수 있다.
  - 다음 액션: 생성 경로와 postclose wrapper 연결을 테스트로 고정하고, Project/Calendar에는 동일 제목으로 추적되게 유지한다.

- [ ] `[StatActionAdvancedAxes0506] statistical_action_weight 2차 고급축 SAW-2 설계 및 sample floor 확정` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 23:10~23:30`, `Track: ScalpingLogic`)
  - Source: [2026-04-30-data-driven-threshold-inventory.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-30-data-driven-threshold-inventory.md), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py)
  - 판정 기준: `price x time`, `volume x time`, `price x volume` 교차축을 report-only로 열기 위한 bucket 정의, `bucket-action sample>=20` floor, `volume_unknown` 제외 규칙, `policy_hint` 산식을 확정한다. 3축 교차와 live 반영은 금지한다.
  - why: 2차 고급축을 명시하지 않으면 “표본이 더 쌓이면”이라는 말이 parking으로 변한다. 다만 교차축은 표본 희소성이 크므로 먼저 floor와 제외 규칙을 잠가야 한다.
  - 다음 액션: 설계가 잠기면 `2026-05-07` 이후 `SAW-3 eligible-but-not-chosen 후행 MFE/MAE 연결`, `SAW-4~SAW-6 체결품질/시장맥락/orderbook 축`을 별도 항목으로 연다.

- [ ] `[AIDecisionMatrix0506] AI 보유/청산 decision matrix ADM-1 schema 확정` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 23:30~23:50`, `Track: AIPrompt`)
  - Source: [2026-04-30-data-driven-threshold-inventory.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-30-data-driven-threshold-inventory.md), [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py), [ai_engine_deepseek.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_deepseek.py)
  - 판정 기준: `holding_exit_decision_matrix_YYYY-MM-DD.json/md` schema를 확정한다. 최소 필드는 `matrix_version`, `valid_for_date`, `context_bucket`, `recommended_bias`, `confidence_adjusted_score`, `edge_margin`, `sample`, `loss_rate`, `hard_veto`, `prompt_hint`다. 이 matrix는 threshold live 적용이 아니라 AI holding/exit prompt 또는 후처리 가중치에 들어갈 decision-support artifact다.
  - 전환 ladder: 현재 단계는 `ADM-1 report-only ON`이다. 이후는 `ADM-2 shadow prompt OFF`, `ADM-3 advisory nudge OFF`, `ADM-4 weighted live OFF`, `ADM-5 policy gate OFF`로 잠근다. 5/6에는 ADM-2 진입 가능 여부만 판정하고, live AI 응답 변경은 열지 않는다.
  - ADM-2 진입 기준: 전일 matrix immutable load 경로, token budget, cache key 분리, matrix_version provenance, Gemini/OpenAI/DeepSeek parity 로그, `action_label/confidence/reason` drift 비교 필드가 모두 설계되어야 한다.
  - 선반영 메모: `2026-05-01` 휴장 maintenance에서 ADM-1 산출물 schema와 Markdown/JSON 저장은 구현했다. 5/6에는 운영일 산출물의 `recommended_bias`, `prompt_hint`, `hard_veto`, `matrix_version` provenance를 확인하고 `ADM-2 shadow prompt injection` 진입 여부를 판정한다.
  - why: 사용자가 요구한 것은 threshold 변경뿐 아니라 AI가 보유/청산 판단을 할 때 통계 matrix를 참조하고, 필요 시 가중치를 더하는 실시간성 개입 기능이다. 이 요구는 `statistical_action_weight` 내부 JSON만으로는 충족되지 않는다.
  - 다음 액션: schema가 잠기면 `2026-05-07`에 `ADM-2 shadow prompt injection`을 열고, matrix context가 AI 응답을 어떻게 바꾸는지 action drift를 먼저 본다.

- [ ] `[AIEngineFlagOffBacklog0506] Gemini/DeepSeek/OpenAI flag-off 잔여축 재점검 및 live enable 금지선 확인` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 23:50~23:59`, `Track: AIPrompt`)
  - Source: [workorder_gemini_engine_review.md](/home/ubuntu/KORStockScan/docs/workorder_gemini_engine_review.md), [2026-04-29-gemini-enable-acceptance-spec.md](/home/ubuntu/KORStockScan/docs/2026-04-29-gemini-enable-acceptance-spec.md), [2026-04-29-deepseek-enable-acceptance-spec.md](/home/ubuntu/KORStockScan/docs/2026-04-29-deepseek-enable-acceptance-spec.md), [2026-04-30-openai-enable-acceptance-spec.md](/home/ubuntu/KORStockScan/docs/2026-04-30-openai-enable-acceptance-spec.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: Gemini `system_instruction`/deterministic config/schema registry, DeepSeek retry/gatekeeper structured-output/holding cache/Tool Calling, OpenAI schema/deterministic/Responses WS/live routing을 `done`, `flag-off observe`, `backlog`, `new checklist required` 중 하나로 재분류한다. 추가로 `2026-05-02` live 보정된 prompt별 model tier routing과 호출 interval이 실제 로그의 `ai_prompt_type`, `ai_model`, `ai_response_ms`, `ai_result_source`로 추적되는지 확인한다.
  - 추가 점검: 스캘핑 AI engine 공통 policy 중 cooldown 일원화, `ai_disabled` 자동 복구 probe, provider protocol 추출, shadow 전용 lock/cache 격리는 active canary cadence를 바꾸지 않는 범위에서만 재분류한다.
  - why: AI 엔진 후속은 여러 문서에 분산돼 있어, 실전 enable 미승인 항목이 누락되거나 active entry/holding canary와 같은 날 섞이면 원인귀속이 깨진다.
  - 금지: 이 항목에서 Gemini/OpenAI/DeepSeek live routing, response schema live enable, deterministic config live enable을 켜지 않는다.
  - prompt cleanup 재분류: `SCALPING_SYSTEM_PROMPT(shared)`, `SCALPING_SYSTEM_PROMPT_75_CANARY`, `SCALPING_BUY_RECOVERY_CANARY_PROMPT`, 미사용 `SCALPING_EXIT_SYSTEM_PROMPT`, 비JSON `EOD_TOMORROW_LEADER_PROMPT`를 `live 유지`, `legacy fallback`, `archive/delete`, `new checklist required` 중 하나로 닫는다. `prompt_profile` 추적 공백은 [2026-04-11-scalping-ai-prompt-coding-instructions.md](/home/ubuntu/KORStockScan/docs/2026-04-11-scalping-ai-prompt-coding-instructions.md)의 `2026-05-02 KST Plan Rebase live 보정` 섹션과 대조한다.
  - Tier1 prompt 문자열 경량화 판정: `flash-lite`/`nano` hot path인 `SCALPING_WATCHING_SYSTEM_PROMPT`, `SCALPING_HOLDING_SYSTEM_PROMPT`, legacy `SCALPING_SYSTEM_PROMPT`에서 `상위 1%`, `프랍 트레이더`, `극강 공격적`, `전설적인`, 장황한 해석 역할극 문구를 제거하거나 Tier2/3 전용으로 격리한다. Tier1은 역할극이 아니라 `입력 핵심 필드 -> enum action -> score/confidence -> reason 1줄` 중심의 짧은 판정 규칙으로 재작성하고, 기대값 판단은 `BUY/WAIT/DROP` 또는 `HOLD/TRIM/EXIT` contract를 깨지 않는 범위에서만 남긴다.
  - 다음 액션: `new checklist required`가 있으면 다음 KRX 운영일 checklist에 `Due`, `Slot`, `TimeWindow`, rollback owner, cohort를 포함한 단일 항목으로만 올린다. 근거가 없으면 backlog로 유지하고, rebase에는 active/open으로 올리지 않는다.
