# 2026-04-30 Stage2 To-Do Checklist

## 오늘 목적

- `pre-submit price guard`와 `price snapshot split`이 장전 restart 후 메인 런타임에 정상 로드됐는지 닫는다.
- `mechanical_momentum_latency_relief` 운영 override가 전일 장중 반영된 상태라면 장전에는 코드/런타임 provenance만 확인하고, 실전 성과는 장중 post-restart cohort로 분리한다.
- 대한전선 진입가 후속조치는 신규 alpha 진입축이 아니라 비정상 저가 제출 차단과 감리 추적성 보강으로만 해석한다.
- `P0` 가드의 day-1 KPI와 rollback trigger를 장후 바로 잠가, 임의 임계값 고착을 막는다.
- `P1 resolver`와 `schema split`은 same-day live 확장이 아니라 observe/backtest ingress 조건 확정으로만 넘긴다.

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
- `mechanical_momentum_latency_relief`는 AI score 50/70 mechanical fallback 상태의 제출 drought를 푸는 entry 1축이다. `latency_signal_quality_quote_composite`, `latency_quote_fresh_composite`, legacy `other_danger/ws_jitter/spread` relief와 동시에 켜지 않으며, 장전에는 enable flag와 restart provenance만 확인한다.

## 장전 체크리스트 (08:45~08:55)

- [ ] `[MechanicalMomentumLatencyRelief0430-Preopen] mechanical_momentum_latency_relief 코드/런타임 로드 확인` (`Due: 2026-04-30`, `Slot: PREOPEN`, `TimeWindow: 08:40~08:45`, `Track: ScalpingLogic`)
  - Source: [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-29-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: main bot PID와 `/proc/<pid>/environ` 또는 import check로 `latency_quote_fresh_composite=False`, `latency_signal_quality_quote_composite=False`, `mechanical_momentum_latency_relief=True` 로드 여부를 확인한다. threshold는 `signal_score<=75`, `latest_strength>=110`, `buy_pressure_10t>=50`, `ws_age<=1200ms`, `ws_jitter<=500ms`, `spread<=0.0085`, `quote_stale=False`로 고정한다.
  - why: 이 축은 신규 alpha 확장이 아니라 제출 drought를 방치하지 않기 위한 운영 override다. PREOPEN에서는 same-day submitted/fill 성과가 아니라 단일축 로드와 rollback guard만 확인한다.
  - rollback guard: 장중 새 cohort에서 `budget_pass >= 150`인데 `submitted <= 2`면 효과 미약으로 OFF 검토를 연다. `pre_submit_price_guard_block_rate > 2.0%`, `fallback_regression > 0`, `normal_slippage_exceeded` 반복, 또는 canary cohort 일간 합산 손익이 당일 스캘핑 배정 NAV 대비 `<= -0.35%`이면 즉시 OFF 후보로 본다.
  - 다음 액션: 로드 확인 후 장중 `[MechanicalMomentumLatencyRelief0430-1000]`에서 `mechanical_momentum_relief_canary_applied`, `latency_mechanical_momentum_relief_normal_override`, `submitted/full/partial`, `COMPLETED + valid profit_rate`를 분리한다.

- [ ] `[DynamicEntryPriceP0Guard0430-Preopen] pre-submit price guard + price snapshot split 구현/검증` (`Due: 2026-04-30`, `Slot: PREOPEN`, `TimeWindow: 08:45~08:55`, `Track: ScalpingLogic`)
  - Source: [2026-04-29-daehan-cable-entry-price-audit-rereport.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-29-daehan-cable-entry-price-audit-rereport.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: main bot restart provenance를 확인하고, `SCALPING_PRE_SUBMIT_PRICE_GUARD_ENABLED=True`, `SCALPING_PRE_SUBMIT_MAX_BELOW_BID_BPS=80` 로드 여부와 `latency_pass/order_leg_request/order_bundle_submitted/pre_submit_price_guard_block` 가격 스냅샷 필드 기록 여부를 확인한다.
  - why: 대한전선 케이스는 신규 alpha canary가 아니라 비정상 저가 제출을 막는 안전가드와 감리 추적성 보강이다. PREOPEN에서는 same-day submitted/fill 성과가 아니라 코드 로드, restart, 이벤트 필드 기록 가능성만 확인한다.
  - 다음 액션: 장전 로드가 확인되면 장중에는 `pre_submit_price_guard_block` 발생 여부와 `submitted_order_price`, `best_bid_at_submit`, `price_below_bid_bps`, `resolution_reason` 품질만 관찰한다. 로드 실패 시 P0 guard를 OFF한 채로 두지 말고 restart/provenance 원인을 우선 수정한다.

## 장중 체크리스트 (09:00~15:20)

- [ ] `[MechanicalMomentumLatencyRelief0430-1000] mechanical_momentum_latency_relief 10시 1차 판정` (`Due: 2026-04-30`, `Slot: INTRADAY`, `TimeWindow: 10:00~10:15`, `Track: ScalpingLogic`)
  - Source: [2026-04-30-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-30-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `09:00~10:00` 또는 새 restart 이후 창 기준 `budget_pass`, `mechanical_momentum_relief_canary_applied`, `latency_mechanical_momentum_relief_normal_override`, `submitted`, `full_fill`, `partial_fill`, `pre_submit_price_guard_block`, `fallback_regression=0`를 확인한다. `full fill`과 `partial fill`은 분리한다.
  - why: 이 축은 거래수 회복을 위한 운영 override라 오전 1시간 안에 최소 방향성은 나와야 한다. `submitted`가 움직이지 않으면 같은 날 추가 유지 근거가 약하다.
  - 다음 액션: 제출 회복이 있으면 12시 full 창으로 유지판정하고, `budget_pass >= 150`인데 `submitted <= 2`면 장중 OFF/다음축 재분해를 연다.

## 장후 체크리스트 (16:00~16:35)

- [ ] `[DynamicEntryPriceP0Guard0430-Postclose] P0 guard KPI/rollback 1차 점검` (`Due: 2026-04-30`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:20`, `Track: ScalpingLogic`)
  - Source: [2026-04-29-daehan-cable-entry-price-audit-rereport.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-29-daehan-cable-entry-price-audit-rereport.md), [2026-04-29-daehan-cable-entry-price-audit-followup.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-29-daehan-cable-entry-price-audit-followup.md)
  - 판정 기준: same-day `pre_submit_price_guard_block_rate`, 전략별 제출 시도 수, `(best_bid - submitted_price)/best_bid` 분포 `p99`, `block 없이 통과한 deep bid` 재발 여부를 확인한다. 일간 차단율 `>0.5%`면 review trigger, `>2.0%`면 rollback 또는 threshold 완화 검토, `=0%`면 가드 비활성/로깅 누락 점검으로 닫는다.
  - why: P0는 가드를 켰다는 사실만으로 충분하지 않다. 운영 기준에서는 가드가 `너무 많이 막는지`, `아예 안 막는지`, `본 사고 유형을 실제로 막았는지`를 day-1부터 같이 봐야 한다.
  - 다음 액션: 차단율이 과도하면 `80bps` 임계를 provisional 값으로 재조정하고, 무차단 재발이 있으면 임계 강화 또는 resolver 우선 구현 검토로 승격한다. 전략별 표본이 부족하면 `2026-05-05` 분포 부록 항목과 연결해 rolling 7d 기준으로 재판정한다.

- [ ] `[CodeDebt0430] shadow/canary/cohort 런타임 분류/정리 판정` (`Due: 2026-04-30`, `Slot: POSTCLOSE`, `TimeWindow: 16:20~16:35`, `Track: Plan`)
  - Source: [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: 대한전선 후속조치와 `pre-submit price guard`를 기준으로 `remove`, `observe-only`, `baseline-promote`, `active-canary` 중 변동이 필요한 항목이 있는지 닫고, entry price 후속 검증에 쓰는 cohort도 `baseline cohort / candidate live cohort / observe-only cohort / excluded cohort / rollback owner / cross-contamination check`로 잠근다.
  - why: 이번 P0는 신규 alpha canary가 아니라 BUY 제출 안전가드다. cohort 분류를 문서와 같이 잠가야 `P0 guard`, `P1 resolver`, `P2 microstructure`가 서로 섞이지 않는다.
  - 다음 액션: 상태 변경이 있으면 checklist와 관련 기준문서에 함께 반영하고, 변경이 없으면 `변동 없음`과 근거를 남긴다.
