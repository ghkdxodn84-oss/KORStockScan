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

- [ ] `[BadEntryRefinedRollback0506-Preopen] refined bad_entry canary OFF 로드 및 재승격 금지 확인` (`Due: 2026-05-06`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: ScalpingLogic`)
  - Source: [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py), [2026-05-04-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-05-04-stage2-todo-checklist.md)
  - 판정 기준: `SCALP_BAD_ENTRY_REFINED_CANARY_ENABLED=False`가 런타임에 로드되고, env `KORSTOCKSCAN_SCALP_BAD_ENTRY_REFINED_CANARY_ENABLED=true` 오염이 없으며, `bad_entry_refined_candidate`는 관찰/리포트 입력으로만 남고 `bad_entry_refined_exit` 실청산은 발생하지 않아야 한다.
  - why: 5/4 장후 `BadEntryRefinedCanary0504-Postclose`에서 canary-applied cohort가 `holding_flow_override` 유예와 장마감 `sell_order_failed` 반복에 섞여 원인귀속과 rollback guard를 통과하지 못했다.
  - 다음 액션: 재개하려면 기존 축 keep이 아니라 `adverse fill detector` 또는 `MAE/MFE quantile stop` 중 하나를 새 단일축 canary/workorder로 다시 열고, 같은 날 `holding_flow_override` semantics 변경과 합산하지 않는다.

- [ ] `[OvernightFlowTrimSemantics0506-Preopen] 오버나이트 flow TRIM=SELL_TODAY 유지 로드 확인` (`Due: 2026-05-06`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [sniper_overnight_gatekeeper.py](/home/ubuntu/KORStockScan/src/engine/sniper_overnight_gatekeeper.py), [2026-05-04-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-05-04-stage2-todo-checklist.md)
  - 판정 기준: 오버나이트 `SELL_TODAY` 재검문에서 flow `HOLD`만 `HOLD_OVERNIGHT`로 승격하고, flow `TRIM`은 `overnight_flow_override_exit_confirmed(force_reason=flow_trim_unsupported)`로 원래 `SELL_TODAY`를 유지하는지 확인한다.
  - why: 5/4 `쏠리드(050890)`처럼 `TRIM/소강/음수 profit`을 전량 보유로 바꾸면 리스크 축소 라벨이 정반대로 해석된다. 부분청산 구현이 없는 v1에서는 `TRIM`을 HOLD로 승격하지 않는다.
  - 다음 액션: 부분청산을 실제로 구현하려면 `TRIM` 실주문 수량, 주문 가능 시간, 잔고/영수증 attribution, rollback guard를 별도 작업항목으로 분리한다.

## 장중 체크리스트 (09:00~15:20)

- [ ] `[PrecloseSellTargetRevival0506-Intraday] preclose sell target report-only 재개 dry-run 및 정기화 판정` (`Due: 2026-05-06`, `Slot: INTRADAY`, `TimeWindow: 14:50~15:10`, `Track: Plan`)
  - Source: [preclose-sell-target-revival-plan.md](/home/ubuntu/KORStockScan/docs/preclose-sell-target-revival-plan.md), [preclose_sell_target_report.py](/home/ubuntu/KORStockScan/src/scanners/preclose_sell_target_report.py), [data/report/README.md](/home/ubuntu/KORStockScan/data/report/README.md), [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)
  - 판정 기준: `deploy/run_preclose_sell_target_report.sh 2026-05-06 --no-ai --no-telegram`로 `data/report/preclose_sell_target/preclose_sell_target_2026-05-06.{json,md}`가 생성되고, JSON에 `policy_status=report_only`, `live_runtime_effect=false`, `automation_stage=R1_daily_report`가 들어가는지 확인한다. 기존 루트 Markdown은 호환성 산출물로만 본다.
  - why: 2026-04-15 단발 `preclose_sell_target`는 cron 미등록/legacy archive로 중단됐지만, 15:00 기준 보유/오버나이트/스윙 후보를 구조화하면 향후 threshold/ADM/swing trailing 개선의 입력 품질을 높일 수 있다. 즉시 live 주문이나 threshold mutation에 연결하면 원인귀속이 깨지므로 report-only 재개부터 닫는다.
  - 다음 액션: dry-run이 통과하면 `AI/Telegram acceptance`, `cron 등록`, `threshold/ADM consumer 연결`을 각각 별도 checklist owner로 분리한다. 실패하면 DB 후보 조회, T-1 ML score freshness, schema write, Telegram/AI 의존성 중 어느 축에서 막혔는지 분리하고 cron 등록은 보류한다.

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
  - 5/4 anchor 보강: [2026-05-04 checklist](./2026-05-04-stage2-todo-checklist.md) `KAIWideWindowExit0504-Postclose`의 `한국항공우주(047810)` `ID 4932`는 peak `+1.45%`, trailing 체결 `+0.78%`, post-sell 20분 `close_vs_buy=+1.850%`로 스캘핑 익절 후에도 1일 이상 또는 최소 intraday wide-window 후보였는지 검토할 anchor다. 반대로 `ID 4976`은 더 높은 가격 재진입 후 `-1.16%`라, 종목 단위 swing 전환이 아니라 winner 상태 전환 조건으로만 설계한다.
  - 다음 액션: 정책이 잠기면 주석 TODO를 제거하고 테스트/체크리스트/기준문서에 동일 용어로 반영한다. `would_extend_window`, `winner_wide_window_candidate`, `reentry_after_winner_exit`는 report-only field 후보로만 두고 live 청산 변경은 별도 단일축 canary 전까지 열지 않는다.

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
  - 5/4 anchor 보강: [2026-05-04 checklist](./2026-05-04-stage2-todo-checklist.md) `G2PowerReceiptMismatch0504-Postclose`의 `지투파워(388050)` `ID 4988`은 신규 `holding_started/ENTRY_FILL` 없이 `exit_signal/sell_order_sent`만 발생했고 DB에는 `COMPLETED -0.23%`가 남은 `receipt_mismatch_zero_sellable` excluded cohort다. `ID 4799` 정상 lifecycle과 같은 종목 revive row를 비교해 active order binding과 completed truth drift를 재현 anchor로 둔다.
  - 다음 액션: `1) lock ownership guide 문서화`, `2) residual race review`, `3) 장중 anomaly case와 테스트 우선순위 대조` 순서로 닫는다. `COMPLETED`라도 receipt-matched fill이 없는 row는 threshold/report 손익 입력에서 제외하거나 flag 처리하는 경로를 함께 확인한다.

- [ ] `[HoldingNetProfitExitRegression0506] holding_state net-profit sell decision 회귀 원인 격리` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 21:10~21:25`, `Track: RuntimeStability`)
  - Source: [test_live_trade_profit_rate.py](/home/ubuntu/KORStockScan/src/tests/test_live_trade_profit_rate.py:540), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)
  - 판정 기준: `test_holding_state_uses_net_profit_rate_for_sell_decision`가 왜 `sell_calls` 없이 끝나는지 원인을 분해하고, `KOSPI_ML` 보유 청산 결정 경로에서 `net profit rate` 기반 sell trigger가 여전히 살아있는지 확인한다. 최소 기준은 failing test 재현, 분기 원인 식별, 수정 또는 의도적 정책 변경 중 하나를 문서로 잠그는 것이다.
  - why: 이번 change set의 타깃 테스트는 green이지만 broader regression 기준으로는 holding exit 경로 1건이 여전히 실패한다. 이 상태를 문서화하지 않으면 `타깃 검증 통과`가 `전체 hold/exit 회귀 없음`으로 오해될 수 있다.
  - 다음 액션: 원인이 기존 정책 변경이면 테스트 기대값을 Plan Rebase 기준으로 재정의하고, 실제 회귀면 별도 patch로 분리해 고친다.

- [x] `[PostCloseSellFailureLoopGuard0506] 장마감 주문불가 sell_order_failed 반복 방지 가드 설계` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 21:10~21:25`, `Track: RuntimeStability`)
  - Source: [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [2026-05-04-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-05-04-stage2-todo-checklist.md), [pipeline_events_2026-05-04.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-05-04.jsonl)
  - 판정 기준: `15:30 KST` 이후 regular-session 매도 주문이 `[2000](999999:주문 불가능합니다.)`로 반복될 때 같은 종목/exit_rule에 대해 초 단위 재시도가 계속되지 않도록 `market_closed_sell_block`, 상태 유지/익일 처리, DB status, 알림, rollback guard를 확정한다.
  - why: 5/4 `쏠리드(050890)`에서 `15:31~15:32` `scalp_soft_stop_pct` 매도 주문 실패가 `98건` 반복됐다. 이 문제는 손실 최소화가 아니라 주문/상태 truth와 다음 장전 처리 품질을 훼손해 기대값 분석 기반을 깨뜨린다.
  - 다음 액션: 단순히 주문을 숨기지 말고 `after-close impossible`, `temporary broker rejection`, `sellable_qty mismatch`, `already sold`를 다른 stage로 분리하고, report에서는 `COMPLETED + valid profit_rate`에 섞지 않는다.
  - 조기 완료 (`2026-05-04 16:30 KST`): 현재 장후에 처리 가능한 safety gap이라 5/6까지 미루지 않고 [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)에 반영했다. `15:30 KST` 이후 SCALPING 매도 신호는 실주문 전송 없이 `sell_order_blocked_market_closed` 1회 로그와 `market_closed_sell_pending=True` 상태로 남긴다.
  - 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_sniper_scale_in.py -k 'market_close_blocks_order_once or sell_reject_with_zero_sellable_qty or sell_reject_with_positive_sellable_qty'` -> `3 passed, 121 deselected`.

- [x] `[BadEntryNextAxisDesign0506] refined bad_entry OFF 이후 다음 단일축 설계 판정` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [2026-05-04-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-05-04-stage2-todo-checklist.md), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)
  - 판정 기준: `bad_entry_refined_canary`를 그대로 keep/retry하지 않는다. 5/4 후보/exit 표본을 `soft_stop_zone`, `loss_too_shallow`, `peak_recovered`, `ai_recovered`, `flow_defer_cross`, `sell_order_failed_cross`로 분리하고, 다음 단일축 후보를 `adverse_fill_detector`, `MAE/MFE quantile stop`, `bad-entry report-only counterfactual enrichment` 중 하나로 선택한다.
  - why: 5/4 OFF 판정은 "bad-entry 조기정리 필요 없음"이 아니라 canary-applied cohort가 flow defer와 주문 실패에 섞여 원인귀속이 깨졌다는 뜻이다. 다음 축 owner 없이 작업을 닫으면 soft stop tail 절단 과제가 누락된다.
  - 다음 액션: 선택한 축은 같은 항목에서 바로 live로 켜지 않는다. `단일 조작점`, `cohort tag`, `rollback guard`, `excluded cohort`, `full/partial 및 initial/pyramid 분리`, `holding_flow_override와의 arbitration 순서`를 잠근 뒤 별도 날짜별 checklist로 구현/관찰을 올린다.
  - 조기 완료 (`2026-05-04 16:30 KST`): 현재 데이터로 판정 가능하므로 5/6까지 미루지 않았다. 선택축은 `bad-entry report-only counterfactual enrichment`다. `adverse_fill_detector`와 `MAE/MFE quantile stop`은 바로 live canary로 열지 않고, refined 후보가 flow defer/order failure와 교차될 때의 arbitration/excluded cohort를 먼저 복원한다.
  - 코드 조치: `SCALP_BAD_ENTRY_REFINED_CANARY_ENABLED=False`는 유지하고, `SCALP_BAD_ENTRY_REFINED_OBSERVE_ENABLED=True`로 `bad_entry_refined_candidate` report-only 로그를 유지한다. `would_exit`와 `should_exit`를 분리해 counterfactual 후보와 실청산을 분리한다.
  - 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_sniper_scale_in.py -k 'bad_entry_refined'` -> `3 passed, 121 deselected`; `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_constants.py -k 'runtime_shadow_defaults_are_off'` -> `1 passed, 6 deselected`.

- [ ] `[ReversalAddDynamicQty0506] REVERSAL_ADD 동적 수량 산식 observe-only 설계` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [personal-decision-flow-notes.md](/home/ubuntu/KORStockScan/docs/personal-decision-flow-notes.md), [sniper_scale_in.py](/home/ubuntu/KORStockScan/src/engine/sniper_scale_in.py:400), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: 현재 `REVERSAL_ADD` 수량이 `buy_qty * REVERSAL_ADD_SIZE_RATIO` + `MAX_POSITION_PCT` cap + 1주 floor에 머무르는지 확인하고, `AI 회복폭`, `수급 3/4~4/4`, `soft/hard stop 거리`, `peak_profit never-green`, `remaining_budget`, `volatility`를 반영한 `would_qty` counterfactual 산식을 설계한다. live 수량 변경은 이 항목에서 켜지 않는다.
  - why: 유효 진입 회수형 추가매수라면 수량도 현재 상태 기반으로 재산정하는 편이 EV 관점에서 자연스럽다. 다만 `REVERSAL_ADD` 자체가 신규 holding canary라 수량까지 동시에 바꾸면 같은 단계 다축 변경이 되어 손익/soft stop tail 원인귀속이 깨진다.
  - 5/4 anchor 보강: `피노(033790)`은 시간창/AI 회복 부족으로 REVERSAL_ADD 미도달, `대한광통신(010170)`은 REVERSAL_ADD 직후 `POST_EVAL 7초` 청산으로 분리한다. 이 둘은 수량 산식과 같은 축에서 조정하지 않고, `would_qty`와 별도로 `would_allow_if_hold_window_extended`, `post_eval_sample_span_sec` 후보를 report-only로 기록할지 판단한다.
  - 다음 액션: 산식 후보가 잠기면 `actual_qty`, `would_qty`, `qty_reason`, `post_add_mfe`, `post_add_stop_rate`, `COMPLETED + valid profit_rate`를 observe-only 로그로 먼저 남기고, 최소 표본 확보 후 별도 단일축 canary로 승격 여부를 판단한다.

- [ ] `[PyramidDynamicQty0506] PYRAMID 불타기 동적 수량 산식 observe-only 설계` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [personal-decision-flow-notes.md](/home/ubuntu/KORStockScan/docs/personal-decision-flow-notes.md), [sniper_scale_in.py](/home/ubuntu/KORStockScan/src/engine/sniper_scale_in.py:142), [sniper_scale_in.py](/home/ubuntu/KORStockScan/src/engine/sniper_scale_in.py:400)
  - 판정 기준: 현재 스캘핑 `PYRAMID` 수량이 `buy_qty * 0.50` + `MAX_POSITION_PCT` cap + 선택적 zero-qty floor 구조에 머무르는지 확인하고, `is_new_high`, `peak_profit - profit_rate <= 0.3`, 수익률 레벨, AI/수급 지속성, trailing giveback 여유, 당일 same-symbol reentry 여부를 반영한 `pyramid_would_qty` counterfactual 산식을 설계한다. live 수량 변경은 이 항목에서 켜지 않는다.
  - why: 불타기는 손실 회수형 `REVERSAL_ADD`보다 winner size-up 효과가 직접적이라 EV 개선 여지가 크다. 그러나 `initial-only`, `pyramid-activated`, `REVERSAL_ADD`, `soft_stop` 표본을 섞으면 원인귀속이 깨지므로 불타기 수량 동적화는 독립 observe-only 축으로만 연다.
  - 다음 액션: 산식 후보가 잠기면 `actual_qty`, `pyramid_would_qty`, `qty_reason`, `post_add_mfe`, `trailing_exit`, `COMPLETED + valid profit_rate`, `soft_stop` 전환율을 분리 로깅하고, 최소 표본 확보 후 별도 단일축 canary 후보로만 승격 검토한다.

- [ ] `[TrailingProtectSensitivity0506] trailing/protect 익절 민감도 단일 owner 재판정` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 22:35~22:50`, `Track: ScalpingLogic`)
  - Source: [2026-05-04-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-05-04-stage2-todo-checklist.md), [threshold_cycle_2026-05-04.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_2026-05-04.json), [post_sell_evaluations_2026-05-04.jsonl](/home/ubuntu/KORStockScan/data/post_sell/post_sell_evaluations_2026-05-04.jsonl), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)
  - 판정 기준: `scalp_trailing_take_profit`의 weak limit `0.4 -> 후보 0.64`, strong AI 경계 `75 -> 70~74 후보`, `protect_trailing_smoothing`의 `min_span_sec/min_samples` 보강을 `initial-only`, `pyramid_signaled_not_executed`, `pyramid_executed`, `protect_hard_stop` 제외 표본으로 나눠 재판정한다. live runtime mutation은 이 항목에서 켜지지 않고, `ThresholdOpsTransition0506` 승인 전에는 manifest/report-only로만 둔다.
  - why: 5/4 trailing은 평균 수익이 양호했지만 `weak_borderline=13`, `would_hold_if_weak_limit_plus_10bp=13`으로 조급한 익절 후보가 많았다. protect trailing은 `유안타증권/한화투자증권`처럼 손실 확대 차단 표본과 `리노공업` 같은 missed upside가 섞여 단일 tick 민감도만으로 판단하면 기대값이 왜곡된다.
  - 5/4 anchor 보강: `한국항공우주(047810) ID 4932`는 winner wide-window 후보, `자람테크놀로지(389020) ID 4982`는 positive peak `+0.95%` 후 soft stop `-2.25%`와 signal-to-fill 약 `0.51%p` 불리 체결 표본, `유안타증권(003470) ID 4902`는 PYRAMID 후 protect trailing 손실 확대 차단 표본이다. 세 표본을 하나의 trailing 완화 결론으로 합치지 않는다.
  - 다음 액션: 5/6 리포트에서 같은 방향성이 반복되면 threshold manifest 후보로만 산출하고, live 적용은 별도 단일축 canary/rollback guard/코호트가 준비된 뒤 검토한다.

- [ ] `[CooldownPolicyInventory0506] 쿨다운 단독 blocker 목록 및 복합 threshold 전환 필요성 점검` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 21:55~22:05`, `Track: ScalpingLogic`)
  - Source: [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [scalping_scanner.py](/home/ubuntu/KORStockScan/src/scanners/scalping_scanner.py), [2026-05-04-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-05-04-stage2-todo-checklist.md)
  - 판정 기준: `SCALE_IN_COOLDOWN_SEC`, `SCALE_IN_CANCEL_COOLDOWN_SEC`, `ADD_JUDGMENT_LOCK_SEC`, scanner `reentry_cooldown_sec=25분`, `AI_WATCHING_COOLDOWN`, `AI_HOLDING_*_COOLDOWN`, `AI_WAIT_DROP_COOLDOWN`, `AI_SCORE_50_BUY_HOLD_OVERRIDE_ENABLED`, `ML_GATEKEEPER_*_COOLDOWN`, `ZERO_DEPOSIT_RETRY_COOLDOWN_SEC`, `same_symbol_loss_reentry_cooldown`을 `단독 hard blocker`, `중복/스팸 방지 안전장치`, `임시 운영가드`, `복합 threshold 후보`로 분류한다. `same_symbol_soft_stop_cooldown_shadow`/`hard_time_stop_shadow`/`partial_only_timeout_shadow`는 5/4 runtime 기본 OFF 정리 상태로 확인만 한다.
  - why: 불타기/물타기는 기대값을 직접 키우는 상위 행동 후보인데, 시간 쿨다운 하나만으로 후보 평가를 막으면 의도한 PYRAMID/REVERSAL_ADD 작동이 깨질 수 있다. 쿨다운은 가능하면 `pending/protection/position_cap/near-close/token` 같은 안전장치가 아닌 이상, 수급/가격경로/호가품질/AI 회복과 결합된 복합 threshold로만 hard blocker가 되어야 한다.
  - 다음 액션: `scale_in_cooldown`이 PYRAMID 후 REVERSAL_ADD를 막는 표본이 반복되면 `post_pyramid_reversal_add_override`를 바로 켜지 말고, `cooldown_remaining_sec`, `post_add_elapsed_sec`, `true_adverse_flow`, `micro_noise`, `reversal_add_predicate_pass_count`, `would_allow_if_composite`를 report-only로 먼저 남기는 단일 작업항목으로 분리한다. 주문 중복 방지용 pending/cancel/protection 계열은 safety guard로 유지하되, 기대값 행동 선택을 단독 시간값으로 차단하는지 별도 표시한다.

- [ ] `[DowntrendReentryComposite0506] 손실 후 하향 재진입 복합 threshold 설계 여부 판정` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 22:20~22:35`, `Track: ScalpingLogic`)
  - Source: [2026-05-04-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-05-04-stage2-todo-checklist.md), [sniper_strength_momentum.py](/home/ubuntu/KORStockScan/src/engine/sniper_strength_momentum.py), [sniper_entry_latency.py](/home/ubuntu/KORStockScan/src/engine/sniper_entry_latency.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)
  - 판정 기준: `유안타증권`, `SK네트웍스`처럼 손실 청산 후 동일종목이 하향 가격구조에서 다시 entry armed/submitted 되는 표본을 모아 `previous_same_symbol_completed_loss`, `last_same_symbol_sell_price`, `entry_vs_last_loss_price_bps`, `recent lower-high/lower-low`, `AI score 50 fallback/blocked`, `strong_absolute_override`, `latency_mechanical_momentum_relief`, `OFI/QI state`를 하나의 복합 feature 후보로 잠근다. `다시 살 논리`가 있으면 기존 보유 중 `REVERSAL_ADD/POST_ADD_EVAL`에서 처리하고, 손절 thesis invalidation 뒤 revive된 신규 WATCHING은 별도 회복 근거 없이는 막는 상태전이 규칙을 함께 검토한다.
  - why: 5/4의 60분 동일종목 손실 재진입 쿨다운은 반복손실을 막는 임시 운영가드다. 기대값 관점의 최종 형태는 단순 시간 차단이 아니라, 회복 수급이 확인될 때는 재진입 기회를 살리고 하향 추세/AI fallback/중립 orderbook 조합은 막는 복합 threshold여야 한다.
  - 다음 액션: 복합 feature가 report에서 복원 가능하면 `manifest_only` 추천값으로 먼저 산출하고, score 50 보류 override가 막은 missed winner/avoided loser를 별도 분리한다. live 전환은 별도 단일축 canary/rollback guard/코호트가 준비된 뒤에만 검토한다. 5/6에는 live mutation을 열지 않는다.

- [ ] `[ThresholdCollectorIO0506] threshold 데이터 수집 IO 과부하 재발성 판정 및 증분 collector 설계` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 21:55~22:10`, `Track: RuntimeStability`)
  - Source: [2026-04-30-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-30-stage2-todo-checklist.md), [2026-04-30-data-driven-threshold-inventory.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-30-data-driven-threshold-inventory.md)
  - 판정 기준: `PerformanceTuningSnapshot` 및 `daily_threshold_cycle_report` 생성 시 스토리지 IO 과부하가 `초기 데이터 적재 1회성`인지, `매 사이클 raw jsonl full scan`으로 반복되는지 구분한다. `pipeline_events_YYYY-MM-DD.jsonl` 크기, cycle 실행 횟수, read bytes, wall time, lock contention, system availability 저하 로그를 함께 본다.
  - `2026-05-04` 누적 리포트 품질 점검 반영: [threshold_cycle_cumulative_2026-05-04.md](/home/ubuntu/KORStockScan/data/report/threshold_cycle_cumulative/threshold_cycle_cumulative_2026-05-04.md)는 기준 구간을 `2026-04-21~2026-05-04` 14일로 표시하지만, JSON pipeline load상 `2026-04-21~2026-04-24`는 `data_source=none`, `2026-05-02~2026-05-03`은 `legacy_compact`로 섞여 있다. 5/6 점검에서는 calendar window와 실제 data window를 분리하고, empty/mixed source 날짜가 누적 방향성을 과대해석하게 만드는지 확인한다.
  - why: threshold 데이터 수집이 기대값 개선을 위한 핵심 기반이더라도, 장중/장후마다 400MB~GB급 raw 파일을 반복 스캔하면 실전 가용성과 체결 truth 품질을 훼손한다.
  - 다음 액션: 반복성 과부하면 cursor 기반 증분 collector, stage 필터 사전집계, 일자/분 단위 partition, single-pass shared snapshot 중 하나를 다음 구현 항목으로 고정한다. 1회성 초기 적재면 운영문서에 cold-start 예외와 금지 시간대를 명시한다.

- [ ] `[ReportAutomationTraceability0506] report 기반 자동화 추적성 registry와 ThresholdOpsTransition gap 점검` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 22:05~22:10`, `Track: RuntimeStability`)
  - Source: [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md), [README.md](/home/ubuntu/KORStockScan/data/threshold_cycle/README.md), [README.md](/home/ubuntu/KORStockScan/data/report/README.md)
  - 판정 기준: `산출물 -> Producer -> Consumer -> 자동화 단계 -> 다음 owner`가 모두 추적되는지 확인한다. `threshold version attribution report`, `auto apply/restart wrapper`, `post-apply rollback guard`처럼 `미구현`, `blocked`, `pending acceptance`인 항목은 `ThresholdOpsTransition0506` 또는 별도 날짜별 checklist owner가 있어야 한다.
  - why: report 기반 자동화가 daily/cumulative/manifest/AI decision-support로 분산되면서, 자동 threshold 적용이나 적용 후 attribution report가 답변 메모에만 남으면 실제 운영전환에서 누락될 수 있다.
  - 다음 액션: owner가 없는 gap이 있으면 `ThresholdOpsTransition0506`에서 묶지 말고 `R5 live_threshold_apply`, `R6 post_apply_attribution`, `Markdown/report inventory`처럼 단계별 체크리스트로 분리한다.

- [ ] `[ThresholdOpsTransition0506] threshold 운영전환 자동화 acceptance 확정` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 22:10~22:30`, `Track: RuntimeStability`)
  - Source: [2026-04-30-data-driven-threshold-inventory.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-30-data-driven-threshold-inventory.md), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py), [backfill_threshold_cycle_events.py](/home/ubuntu/KORStockScan/src/engine/backfill_threshold_cycle_events.py), [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)
  - 판정 기준: 최종 안정화 후 운영전환 acceptance가 `매일 자동 실행`, `다음 장전 승인 threshold 자동 적용 + 봇 기동`, `장후 threshold version별 실적분석 제출`, `실적 결과 기반 다음 threshold weight 미세조정` 4개를 모두 포함하는지 확인한다.
  - 현재 자동화 상태: `2026-05-01`에 4월 가용 raw partition bootstrap을 완료했고, `07:35 PREOPEN apply manifest`, `16:10 POSTCLOSE collector/report` cron을 설치했다. 단 live threshold runtime mutation은 acceptance 전까지 `manifest_only`다.
  - `2026-05-04` 누적 리포트 해석 반영: [threshold_cycle_cumulative_2026-05-04.md](/home/ubuntu/KORStockScan/data/report/threshold_cycle_cumulative/threshold_cycle_cumulative_2026-05-04.md)는 cumulative normal 평균 `-0.4709`, rolling_10d `-0.4911`, rolling_5d `-0.6657`로 최근 5일 손익이 더 악화됐다. `initial_only`는 cumulative `139건/-0.5692`, rolling_5d `90건/-0.7559`로 주된 음수 EV 축이며, broad threshold 완화가 아니라 진입 품질/초기 청산 민감도/체결 품질 분해 대상이다. `pyramid_activated`는 cumulative `19건/+0.2458`, rolling_10d `17건/+0.3235`로 기대값 후보지만 rolling_5d `13건/-0.0592`라 안정적 승인 근거는 아니다. `reversal_add_activated`는 표본 1건으로 결론 금지다. 이 해석은 `PyramidDynamicQty0506`, `ReversalAddDynamicQty0506`, `TrailingProtectSensitivity0506`, `StatActionWeight0506`의 입력으로만 쓰고, 5/6에도 live mutation은 열지 않는다.
  - why: threshold cycle이 수동 리포트에 머물면 데이터 기반 완화값이 실전 기대값 개선으로 연결되지 않는다. 반대로 장중 실시간 자동변경으로 가면 원인귀속과 rollback guard가 깨지므로, 자동화는 일일 배치/다음 장전 적용 단위로만 닫아야 한다.
  - 다음 액션: acceptance가 잠기면 workflow/cron 설계 항목을 분리한다. 장중 compact collector, 장후 report+weight 산정, 장전 apply+bot start, 장후 performance attribution report를 각각 재실행 가능한 wrapper로 정의한다.

- [ ] `[StatActionWeight0506] 가격대/거래량/시간대별 행동가중치 리포트 1차 판정` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 22:30~22:50`, `Track: ScalpingLogic`)
  - Source: [2026-04-30-data-driven-threshold-inventory.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-30-data-driven-threshold-inventory.md), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py), [threshold_cycle_registry.py](/home/ubuntu/KORStockScan/src/utils/threshold_cycle_registry.py)
  - 판정 기준: `statistical_action_weight` family의 `price_bucket`, `volume_bucket`, `time_bucket`별 `exit_only`, `avg_down_wait`, `pyramid_wait` 표본과 평균손익/승률을 확인한다. 추가로 `stat_action_decision_snapshot`의 `chosen_action`, `eligible_actions`, `rejected_actions`, `scale_in_gate_reason`, `exit_rule_candidate`가 충분히 적재됐는지 본다. 단순 평균이 아니라 `confidence_adjusted_score`, `edge_margin`, `policy_hint(no_clear_edge/defensive_only_high_loss_rate/candidate_weight_source)`를 기준으로 본다. `volume_unknown` 비중이 높으면 거래량 결론은 금지하고 가격대/시간대 direction-only만 남긴다.
  - `2026-05-04` 리포트 해석 반영: [statistical_action_weight_2026-05-04.md](/home/ubuntu/KORStockScan/data/report/statistical_action_weight/statistical_action_weight_2026-05-04.md)는 `completed_valid=132`, `compact_decision_snapshot=4564`로 weight source 자체는 준비됐지만 행동별 표본은 불균형하다. `exit_only`는 표본 114건이나 평균 `-0.5968`, 손실률 `0.5965`로 손실 편향이 강하고, `pyramid_wait`는 표본 17건에서 평균 `+0.3235`, 승률 `0.6471`, 손실률 `0.3529`로 기대값 후보지만 sample floor 전에는 live 반영 금지다. `avg_down_wait`는 표본 1건이라 tuning 결론에서 제외한다. 5/6에는 이 결과를 `pyramid_wait` 동적 수량/대기 조건 후보와 `exit_only` 과민 청산 점검 입력으로만 쓰고, threshold/live mutation은 열지 않는다.
  - why: 현재 전략계층은 전문가 규칙 중심이라 “어떤 장면에서는 청산, 어떤 장면에서는 물타기/불타기 후 대기”라는 통계적 행동가중치가 부족했다. 이 축은 live 변경이 아니라 다음 threshold weight와 동적 수량 설계의 근거다. 작은 표본의 우연한 평균값을 믿지 않기 위해 empirical-bayes shrinkage와 불확실성 penalty를 같이 본다.
  - 다음 액션: sample-ready이면 다음 장후 산정에서 threshold weight 입력으로 연결하고, 부족하면 누락 필드(`daily_volume`, `buy_time`, `scale_in_executed`, `exit_signal`, `sell_completed`, `stat_action_decision_snapshot`) 적재 품질부터 보강한다. 4월 historical compact는 registry 추가 전 bootstrap이라 action stage가 비어 있을 수 있으므로, 필요하면 IO guard가 있는 maintenance backfill로 action family만 재적재한다.

- [ ] `[StatActionMarkdown0506] statistical_action_weight 운영자용 Markdown 리포트 자동생성 구현` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 22:50~23:10`, `Track: ScalpingLogic`)
  - Source: [2026-04-30-data-driven-threshold-inventory.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-30-data-driven-threshold-inventory.md), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh), [README.md](/home/ubuntu/KORStockScan/data/report/README.md)
  - 판정 기준: 장후 threshold cycle 실행 시 `data/report/statistical_action_weight/statistical_action_weight_YYYY-MM-DD.md`와 `.json`이 자동 생성되는지 확인한다. Markdown은 `판정`, `표본 충분성`, `price/volume/time bucket별 best action`, `no_clear_edge/insufficient_sample`, `threshold 반영 금지/가능 항목`, `다음 액션`을 포함해야 한다.
  - 선반영 메모: `2026-05-01` 휴장 maintenance에서 구현/테스트는 완료했다. 5/6에는 실제 운영일 postclose 자동 실행 산출물 health check와 표본 충분성 판정을 수행한다.
  - why: 현재 `statistical_action_weight`는 기계용 JSON 내부 섹션으로만 존재해 매일 사람이 읽고 의사결정하기 어렵다. 독립 Markdown이 없으면 2차 고급축 판정도 운영 흐름에서 누락될 수 있다.
  - 추가 확인: [README.md](/home/ubuntu/KORStockScan/data/report/README.md)의 Markdown 누락 후보 중 `threshold_cycle`, `performance_tuning`, `trade_review`를 우선순위 상위 3개로 보고, 5/6 산출물 health check에서 별도 Markdown 구현 workorder가 필요한지 판정한다.
  - 다음 액션: 생성 경로와 postclose wrapper 연결을 테스트로 고정하고, Project/Calendar에는 동일 제목으로 추적되게 유지한다. 누락 후보를 구현 대상으로 확정하면 별도 단일 작업항목으로 분리한다.

- [ ] `[StatActionAdvancedAxes0506] statistical_action_weight 2차 고급축 SAW-2 설계 및 sample floor 확정` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 23:10~23:30`, `Track: ScalpingLogic`)
  - Source: [2026-04-30-data-driven-threshold-inventory.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-30-data-driven-threshold-inventory.md), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py)
  - 판정 기준: `price x time`, `volume x time`, `price x volume` 교차축을 report-only로 열기 위한 bucket 정의, `bucket-action sample>=20` floor, `volume_unknown` 제외 규칙, `policy_hint` 산식을 확정한다. 3축 교차와 live 반영은 금지한다.
  - `2026-05-04` matrix 해석 반영: [holding_exit_decision_matrix_2026-05-04.md](/home/ubuntu/KORStockScan/data/report/holding_exit_decision_matrix/holding_exit_decision_matrix_2026-05-04.md)는 `time_1030_1400`에서 `prefer_pyramid_wait` 방향성(`sample=10`, `loss_rate=0.3`, `edge=0.9723`)을 보였지만 sample floor 미달이다. `price_lt_10k`, `price_gte_70k`, `volume_2m_10m`도 `prefer_pyramid_wait` 후보이나 표본 5~6 수준이고, 특히 `volume_2m_10m`은 `loss_rate=0.6`이라 단독 완화 근거가 아니다. 5/6에는 이 후보들을 live 반영이 아니라 `time x price`, `time x volume`, `initial/pyramid`, trailing giveback/체결품질 교차축 설계 입력으로만 쓴다.
  - why: 2차 고급축을 명시하지 않으면 “표본이 더 쌓이면”이라는 말이 parking으로 변한다. 다만 교차축은 표본 희소성이 크므로 먼저 floor와 제외 규칙을 잠가야 한다.
  - 다음 액션: 설계가 잠기면 `2026-05-07` 이후 `SAW-3 eligible-but-not-chosen 후행 MFE/MAE 연결`, `SAW-4~SAW-6 체결품질/시장맥락/orderbook 축`을 별도 항목으로 연다.

- [ ] `[AIDecisionMatrix0506] AI 보유/청산 decision matrix ADM-1 schema 확정` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 23:30~23:50`, `Track: AIPrompt`)
  - Source: [2026-04-30-data-driven-threshold-inventory.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-30-data-driven-threshold-inventory.md), [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py), [ai_engine_deepseek.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_deepseek.py)
  - 판정 기준: `holding_exit_decision_matrix_YYYY-MM-DD.json/md` schema를 확정한다. 최소 필드는 `matrix_version`, `valid_for_date`, `context_bucket`, `recommended_bias`, `confidence_adjusted_score`, `edge_margin`, `sample`, `loss_rate`, `hard_veto`, `prompt_hint`다. 이 matrix는 threshold live 적용이 아니라 AI holding/exit prompt 또는 후처리 가중치에 들어갈 decision-support artifact다.
  - 전환 ladder: 현재 단계는 `ADM-1 report-only ON`이다. 이후는 `ADM-2 shadow prompt OFF`, `ADM-3 advisory nudge OFF`, `ADM-4 weighted live OFF`, `ADM-5 policy gate OFF`로 잠근다. 5/6에는 ADM-2 진입 가능 여부만 판정하고, live AI 응답 변경은 열지 않는다.
  - ADM-2 진입 기준: 전일 matrix immutable load 경로, token budget, cache key 분리, matrix_version provenance, Gemini/OpenAI/DeepSeek parity 로그, `action_label/confidence/reason` drift 비교 필드가 모두 설계되어야 한다.
  - `2026-05-04` matrix 해석 반영: [holding_exit_decision_matrix_2026-05-04.md](/home/ubuntu/KORStockScan/data/report/holding_exit_decision_matrix/holding_exit_decision_matrix_2026-05-04.md)의 다수 bucket은 `no_clear_edge`다. 따라서 ADM-2 prompt context는 `prefer_pyramid_wait`를 강한 지시로 넣지 않고 “winner size-up 대기 후보이나 trailing giveback/체결품질 확인 필요” 수준의 shadow hint로만 넣는다. hard veto(`emergency_or_hard_stop`, `active_sell_order_pending`, `invalid_feature`, `post_add_eval_exclusion`)는 matrix보다 우선한다.
  - 선반영 메모: `2026-05-01` 휴장 maintenance에서 ADM-1 산출물 schema와 Markdown/JSON 저장은 구현했다. 5/6에는 운영일 산출물의 `recommended_bias`, `prompt_hint`, `hard_veto`, `matrix_version` provenance를 확인하고 `ADM-2 shadow prompt injection` 진입 여부를 판정한다.
  - why: 사용자가 요구한 것은 threshold 변경뿐 아니라 AI가 보유/청산 판단을 할 때 통계 matrix를 참조하고, 필요 시 가중치를 더하는 실시간성 개입 기능이다. 이 요구는 `statistical_action_weight` 내부 JSON만으로는 충족되지 않는다.
  - 다음 액션: schema가 잠기면 `2026-05-07`에 `ADM-2 shadow prompt injection`을 열고, matrix context가 AI 응답을 어떻게 바꾸는지 action drift를 먼저 본다.

- [ ] `[AIEngineFlagOffBacklog0506] Gemini/DeepSeek/OpenAI flag-off 잔여축 재점검 및 live enable 금지선 확인` (`Due: 2026-05-06`, `Slot: POSTCLOSE`, `TimeWindow: 23:50~23:59`, `Track: AIPrompt`)
  - Source: [workorder_gemini_engine_review.md](/home/ubuntu/KORStockScan/docs/workorder_gemini_engine_review.md), [2026-04-29-gemini-enable-acceptance-spec.md](/home/ubuntu/KORStockScan/docs/2026-04-29-gemini-enable-acceptance-spec.md), [2026-04-29-deepseek-enable-acceptance-spec.md](/home/ubuntu/KORStockScan/docs/2026-04-29-deepseek-enable-acceptance-spec.md), [2026-04-30-openai-enable-acceptance-spec.md](/home/ubuntu/KORStockScan/docs/2026-04-30-openai-enable-acceptance-spec.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: Gemini `system_instruction`/deterministic config/schema registry, DeepSeek retry/gatekeeper structured-output/holding cache/Tool Calling, OpenAI schema/deterministic/Responses WS/live routing을 `done`, `flag-off observe`, `backlog`, `new checklist required` 중 하나로 재분류한다. 추가로 `2026-05-02` live 보정된 prompt별 model tier routing과 호출 interval이 실제 로그의 `ai_prompt_type`, `ai_model`, `ai_response_ms`, `ai_result_source`로 추적되는지 확인한다.
  - OpenAI 후반 owner 명시: `2026-05-04` 점검 기준 현재 `main` 스캘핑 live routing은 Gemini이며 `ai_engine_openai.py`는 runtime owner가 아니다. 따라서 OpenAI는 `transport/schema readiness backlog`로만 재검토하고, `HTTP baseline live` 표현은 쓰지 않는다. 후반 판정에서는 `1) route가 실제로 열려 있는지`, `2) diagnostic/shadow 메트릭이 있는지`, `3) 없다면 backlog only로 유지할지`, `4) live routing 검토가 필요하면 새 checklist가 필요한지`를 분리한다.
  - 추가 점검: 스캘핑 AI engine 공통 policy 중 cooldown 일원화, `ai_disabled` 자동 복구 probe, provider protocol 추출, shadow 전용 lock/cache 격리는 active canary cadence를 바꾸지 않는 범위에서만 재분류한다.
  - why: AI 엔진 후속은 여러 문서에 분산돼 있어, 실전 enable 미승인 항목이 누락되거나 active entry/holding canary와 같은 날 섞이면 원인귀속이 깨진다.
  - 금지: 이 항목에서 Gemini/OpenAI/DeepSeek live routing, response schema live enable, deterministic config live enable을 켜지 않는다.
  - prompt cleanup 재분류: `SCALPING_SYSTEM_PROMPT(shared)`, `SCALPING_SYSTEM_PROMPT_75_CANARY`, `SCALPING_BUY_RECOVERY_CANARY_PROMPT`, 미사용 `SCALPING_EXIT_SYSTEM_PROMPT`, 비JSON `EOD_TOMORROW_LEADER_PROMPT`를 `live 유지`, `legacy fallback`, `archive/delete`, `new checklist required` 중 하나로 닫는다. `prompt_profile` 추적 공백은 [2026-04-11-scalping-ai-prompt-coding-instructions.md](/home/ubuntu/KORStockScan/docs/2026-04-11-scalping-ai-prompt-coding-instructions.md)의 `2026-05-02 KST Plan Rebase live 보정` 섹션과 대조한다.
  - Tier1 prompt 문자열 경량화 판정: `flash-lite`/`nano` hot path인 `SCALPING_WATCHING_SYSTEM_PROMPT`, `SCALPING_HOLDING_SYSTEM_PROMPT`, legacy `SCALPING_SYSTEM_PROMPT`에서 `상위 1%`, `프랍 트레이더`, `극강 공격적`, `전설적인`, 장황한 해석 역할극 문구를 제거하거나 Tier2/3 전용으로 격리한다. Tier1은 역할극이 아니라 `입력 핵심 필드 -> enum action -> score/confidence -> reason 1줄` 중심의 짧은 판정 규칙으로 재작성하고, 기대값 판단은 `BUY/WAIT/DROP` 또는 `HOLD/TRIM/EXIT` contract를 깨지 않는 범위에서만 남긴다.
  - 다음 액션: `new checklist required`가 있으면 다음 KRX 운영일 checklist에 `Due`, `Slot`, `TimeWindow`, rollback owner, cohort를 포함한 단일 항목으로만 올린다. 근거가 없으면 backlog로 유지하고, rebase에는 active/open으로 올리지 않는다.
