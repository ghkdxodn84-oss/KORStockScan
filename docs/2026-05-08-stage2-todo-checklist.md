# 2026-05-08 Stage2 To-Do Checklist

## 오늘 목적

- `statistical_action_weight` 2차 고급축 중 `SAW-4~SAW-6`의 적재 가능성과 리포트 확장 순서를 판정한다.
- 체결품질, 시장/종목 맥락, orderbook absorption 축을 행동가중치에 넣을 수 있는지 sample/readiness 기준으로 분리한다.

## 오늘 강제 규칙

- 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이며 상세 기준은 `Plan Rebase` §1~§6을 따른다.
- `statistical_action_weight`는 report-only/decision-support 축이며 직접 runtime threshold나 주문 행동을 바꾸지 않는다.
- 체결품질 분석은 full/partial fill을 합치지 않는다.
- orderbook/microstructure 필드가 누락되면 추정값으로 손익 결론을 만들지 않는다.

## 장전 체크리스트 (08:50~09:00)

- 없음

## 장중 체크리스트 (09:00~15:20)

- 없음

## 장후 체크리스트 (16:00~16:45)

- [ ] `[StatActionAdvancedContext0508] SAW-4~SAW-6 체결품질/시장맥락/orderbook 축 적재 가능성 판정` (`Due: 2026-05-08`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:45`, `Track: ScalpingLogic`)
  - Source: [2026-04-30-data-driven-threshold-inventory.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-30-data-driven-threshold-inventory.md), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py), [sniper_execution_receipts.py](/home/ubuntu/KORStockScan/src/engine/sniper_execution_receipts.py)
  - 판정 기준: `SAW-4` full/partial/slippage/adverse fill, `SAW-5` market_regime/volatility/marcap/sector/VI freshness, `SAW-6` orderbook absorption/large sell print/micro VWAP 이탈을 action weight report에 넣을 수 있는지 확인한다. 각 축별 필드 존재율, join key, sample floor, compact stream 포함 여부, report-only 유지 조건을 표로 잠근다.
  - why: 1차 가격/거래량/시간대 축만으로는 행동 선택의 기대값 차이를 충분히 설명하지 못한다. 다만 체결품질과 orderbook 축은 필드 누락 시 왜곡 위험이 크므로 적재 가능성부터 닫아야 한다.
  - 다음 액션: readiness가 높은 축 1개만 다음 구현 항목으로 승격하고, 나머지는 누락 필드 보강 항목으로 분리한다.
