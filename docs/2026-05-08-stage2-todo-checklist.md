# 2026-05-08 Stage2 To-Do Checklist

## 오늘 목적

- `statistical_action_weight` 2차 고급축 중 `SAW-4~SAW-6`의 적재 가능성과 리포트 확장 순서를 판정한다.
- 체결품질, 시장/종목 맥락, orderbook absorption 축을 행동가중치에 넣을 수 있는지 sample/readiness 기준으로 분리한다.
- OFI/QI가 P2 내부 live 입력 feature로 반영된 뒤 stale 되지 않도록 prompt/report/calibration 확장 ladder와 owner를 확정한다.

## 오늘 강제 규칙

- 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이며 상세 기준은 `Plan Rebase` §1~§6을 따른다.
- `statistical_action_weight`는 report-only/decision-support 축이며 직접 runtime threshold나 주문 행동을 바꾸지 않는다.
- 체결품질 분석은 full/partial fill을 합치지 않는다.
- orderbook/microstructure 필드가 누락되면 추정값으로 손익 결론을 만들지 않는다.
- OFI/QI는 `entry-only` P2 내부 feature로 유지한다. `OFI standalone hard gate`, `watching/holding/exit` 확장, symbol-level runtime threshold는 별도 workorder 없이는 금지한다.

## 장전 체크리스트 (08:50~09:00)

- 없음

## 장중 체크리스트 (09:00~15:20)

- 없음

## 장후 체크리스트 (16:00~17:15)

- [ ] `[StatActionAdvancedContext0508] SAW-4~SAW-6 체결품질/시장맥락/orderbook 축 적재 가능성 판정` (`Due: 2026-05-08`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:45`, `Track: ScalpingLogic`)
  - Source: [2026-04-30-data-driven-threshold-inventory.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-30-data-driven-threshold-inventory.md), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py), [sniper_execution_receipts.py](/home/ubuntu/KORStockScan/src/engine/sniper_execution_receipts.py)
  - 판정 기준: `SAW-4` full/partial/slippage/adverse fill, `SAW-5` market_regime/volatility/marcap/sector/VI freshness, `SAW-6` orderbook absorption/large sell print/micro VWAP 이탈을 action weight report에 넣을 수 있는지 확인한다. 각 축별 필드 존재율, join key, sample floor, compact stream 포함 여부, report-only 유지 조건을 표로 잠근다.
  - why: 1차 가격/거래량/시간대 축만으로는 행동 선택의 기대값 차이를 충분히 설명하지 못한다. 다만 체결품질과 orderbook 축은 필드 누락 시 왜곡 위험이 크므로 적재 가능성부터 닫아야 한다.
  - 다음 액션: readiness가 높은 축 1개만 다음 구현 항목으로 승격하고, 나머지는 누락 필드 보강 항목으로 분리한다.

- [ ] `[OFIQExpansionLadder0508] OFI/QI P2 내부 feature 확대적용 ladder 및 stale 방지 owner 확정` (`Due: 2026-05-08`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~17:15`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [2026-05-03-ofi-audit-response-result-report.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-05-03-ofi-audit-response-result-report.md), [README.md](/home/ubuntu/KORStockScan/data/report/README.md), [orderbook_stability_observer.py](/home/ubuntu/KORStockScan/src/trading/entry/orderbook_stability_observer.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [sniper_performance_tuning_report.py](/home/ubuntu/KORStockScan/src/engine/sniper_performance_tuning_report.py)
  - 판정 기준: OFI/QI 후속을 `P2 prompt contract 명문화`, `performance_tuning Markdown OFI/QI 섹션`, `bucket calibration ON 기준`, `symbol anomaly watch`, `prompt drift/stale guard` 5단계 ladder로 잠근다. 각 단계별 owner, 금지 범위, 필요한 로그 필드, sample floor, rollback owner를 표로 남긴다.
  - prompt 기준: `entry_price_v1` prompt에서 OFI/QI의 사용 범위를 `submitted 직전 주문가/USE_DEFENSIVE/IMPROVE_LIMIT/SKIP 판단 보조`로 명시하고, `neutral/insufficient`이면 OFI/QI 단독 SKIP 금지를 유지한다. prompt 문자열 개선은 AIEngineFlagOffBacklog와 충돌하지 않도록 P2 entry_price contract 전용 workorder로만 연다.
  - report 기준: `performance_tuning_YYYY-MM-DD.md` 구현 후보에 OFI/QI 섹션을 포함한다. 최소 필드는 `ofi_orderbook_micro_states`, `ofi_orderbook_micro_threshold_sources`, `ofi_orderbook_micro_buckets`, `ofi_orderbook_micro_warnings`, `symbol_anomalies`, `entry_ai_price_skip_policy_warning/basis`다.
  - calibration 기준: `SCALPING_ENTRY_PRICE_ORDERBOOK_MICRO_BUCKET_CALIBRATION_ENABLED`는 기본 OFF다. ON 후보는 `ThresholdOpsTransition0506` 이후에도 별도 workorder, manifest id/version, sample floor, fallback 급증 guard, restart 절차가 닫혀야 한다.
  - stale 방지: 2영업일 연속 OFI/QI 로그 표본이 0이거나, `snapshot_age_ms`/observer health/fallback reason이 report에 누락되거나, SKIP warning 분포가 Markdown에 나타나지 않으면 `stale_context`로 보고 다음 checklist에 보강 작업을 자동 생성한다.
  - 다음 액션: ladder가 잠기면 `performance_tuning Markdown 구현`, `entry_price_v1 prompt contract 보강`, `bucket calibration ON/OFF workorder` 중 readiness가 높은 1개만 다음 단일 작업항목으로 분리한다.

- [ ] `[Phase3Quality0508] counterfactual realism 3-mode 및 exit decision authority provenance 채택 여부 판정` (`Due: 2026-05-08`, `Slot: POSTCLOSE`, `TimeWindow: 17:15~17:35`, `Track: ScalpingLogic`)
  - Source: [2026-04-10-scalping-ai-coding-instructions.md](/home/ubuntu/KORStockScan/docs/2026-04-10-scalping-ai-coding-instructions.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [sniper_missed_entry_counterfactual.py](/home/ubuntu/KORStockScan/src/engine/sniper_missed_entry_counterfactual.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [sniper_trade_review_report.py](/home/ubuntu/KORStockScan/src/engine/sniper_trade_review_report.py)
  - 판정 기준: `Phase 3-1`은 현재 `missed_entry_counterfactual` 관찰축과 `counterfactual 손익 미합산` 원칙으로 부분 채택됐는지, 그리고 `optimistic/realistic/conservative` 3모드가 실제 구현됐는지 분리 판정한다. `Phase 3-2`는 `exit_decision_source` 필드와 `PRESET_HARD_STOP/PRESET_PROTECT/AI_REVIEW_EXIT/SOFT_STOP/TIMEOUT/MANUAL` authority taxonomy가 runtime log/report/test에 존재하는지 확인한다.
  - why: 초기 튜닝 문서의 `분석 품질 고도화`는 현재 Rebase에 원칙 단위로만 흡수돼 있고, 구현 단위로는 `partial adopted`와 `missing`이 섞여 있다. 이 상태를 그대로 두면 `counterfactual realism`과 `청산 authority provenance`가 다시 stale 된다.
  - 다음 액션: `3-mode counterfactual`, `exit_decision_source provenance` 중 readiness가 높은 1개만 다음 단일 작업항목으로 분리하고, 다른 1개는 `report-only/설계 only`로 잠근다.
