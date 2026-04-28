# 2026-05-05 Stage2 To-Do Checklist

## 오늘 목적

- `latency_override_defensive_ticks=3` v1 임시 방어폭을 1주 실전 표본으로 재튜닝한다.
- fixed tick 방식을 bps/가격대별 defensive table로 바꿀 필요가 있는지 판정한다.
- BUY 진입가 전용 변경과 SELL/청산가 정책을 분리해 원인귀속을 유지한다.
- `NaN cast` 계열 오류를 메인 코드베이스 기준 최소 safe cast 계획과 upstream source 재분해 계획으로 잠근다.

## 오늘 강제 규칙

- 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이며 상세 기준은 `Plan Rebase` §1~§6을 따른다.
- live 변경은 동일 단계 내 `1축 canary`만 허용한다.
- 손익은 `COMPLETED + valid profit_rate`만 사용하고 `full fill`과 `partial fill`은 분리한다.
- `latency_entry_price_guard`는 신규 entry canary가 아니라 기존 active entry canary의 BUY 체결품질 보호 가드로 해석한다.
- 3틱은 v1 임시값이며, 재튜닝 전에는 정식 정책으로 고정하지 않는다.
- fallback/scout/split-entry는 재도입하지 않는다.
- `NaN cast` follow-up은 live canary가 아니라 런타임 안정화/집계 품질 보강 축으로만 다룬다.

## 장전 체크리스트 (08:50~09:00)

- 없음

## 장중 체크리스트 (09:00~15:20)

- 없음

## 장후 체크리스트 (16:00~17:10)

- [ ] `[LatencyEntryPriceGuard0505] 3틱 v1 fill/slippage/profit 재튜닝 판정` (`Due: 2026-05-05`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:20`, `Track: ScalpingLogic`)
  - Source: [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md), [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-28-stage2-todo-checklist.md)
  - 판정 기준: `latency_override_defensive_ticks=3` 적용 cohort와 기존/비적용 normal cohort를 `fill_rate`, `realized_slippage`, `full_fill`, `partial_fill`, `COMPLETED + valid profit_rate`, `normal_slippage_exceeded`로 비교한다.
  - why: 3틱은 v1 임시값이며 1주 데이터 없이 정식 정책으로 고정하지 않는다.
  - 다음 액션: 우위가 확인되면 유지 또는 v2 전환 설계로 넘기고, fill 손실/기회비용이 크면 1틱/2틱/가격대별 table 재튜닝 후보를 연다.

- [ ] `[LatencyEntryPriceGuardV2] bps/가격대별 defensive table 설계` (`Due: 2026-05-05`, `Slot: POSTCLOSE`, `TimeWindow: 16:20~16:35`, `Track: ScalpingLogic`)
  - Source: [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md), [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-28-stage2-todo-checklist.md)
  - 판정 기준: fixed tick 대신 저가주/중가주/고가주 가격대별 bps 부담을 반영한 defensive table을 설계한다.
  - why: 동일 3틱이라도 가격대별 bps 비용이 달라 기대값/체결률 trade-off가 왜곡될 수 있다.
  - 다음 액션: v2 승인 전까지 v1 3틱은 임시값으로만 유지하고, table 후보는 shadow/counterfactual 로그부터 추가한다.

- [ ] `[LatencyExitPriceGuardReview] 매도/청산 latency 가격가드 현황 명문화` (`Due: 2026-05-05`, `Slot: POSTCLOSE`, `TimeWindow: 16:35~16:50`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-28-stage2-todo-checklist.md)
  - 판정 기준: 이번 변경은 BUY 진입가 전용이다. SELL/청산가에 latency 위험 대칭 정책이 있는지 확인하고, 기존 정책 유지/별도 canary/observe-only 중 하나로 명문화한다.
  - why: 진입 방어폭만 강화하고 청산가 정책을 불명확하게 두면 realized slippage와 missed upside 해석이 섞인다.
  - 다음 액션: 매도 측 정책 변경이 필요하면 진입가 v1 재튜닝과 별도 축으로 분리하고, 같은 날 한 축 canary 원칙을 유지한다.

- [ ] `[NaNCastGuard0505] NaN cast runtime 안정화 후속계획 확정` (`Due: 2026-05-05`, `Slot: POSTCLOSE`, `TimeWindow: 16:50~17:10`, `Track: RuntimeStability`)
  - Source: [2026-04-28-nan-cast-guard-hotfix-report.md](/home/ubuntu/KORStockScan/docs/2026-04-28-nan-cast-guard-hotfix-report.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: 원격과 동일 patch set 복제 여부가 아니라 메인 코드베이스 기준 `NaN/inf` 안전 캐스팅 최소 범위, 재발건수, 상태전이 실패 경로, upstream source 후보(`buy_qty/buy_price/target_buy_price/marcap/preset_tp_*`, websocket `curr/ask_tot/bid_tot`, 체결 `price/qty`)를 확정한다.
  - why: `NaN cast`는 루프 중단과 체결 후 상태전이 실패를 만들어 기대값과 미진입/미청산 기회비용을 직접 훼손한다. same-day hotfix를 보고서로만 남기면 메인 기준의 수정범위와 재발 방지 계획이 비어 있다.
  - 다음 액션: 메인 기준 최소 safe cast patch 범위와 테스트(`pytest`/`py_compile`)를 잠그고, 재발이 있으면 source 추적 작업을 다음 거래일 PREOPEN/POSTCLOSE checklist로 승격한다.
