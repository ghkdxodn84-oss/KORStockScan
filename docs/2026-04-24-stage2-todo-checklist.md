# 2026-04-24 Stage 2 To-Do Checklist

## 목적

- `2026-04-20~2026-04-23` 검증 결과를 기반으로 금요일에 결론을 미루지 않고 닫는다.
- 금요일 운영축은 `승격 1축 실행` 또는 `보류+재시각` 중 하나로 고정한다.
- 다축 동시 변경을 금지하고 `한 번에 한 축 canary` 원칙을 유지한다.
- 주간 판정에는 regime 태그(저변동/평상/고변동)와 조건부 유효범위를 함께 기록한다.
- `PYRAMID zero_qty Stage 1`은 `SCALPING/PYRAMID bugfix-only` 범위가 충분히 좁혀졌을 때만 다음주 원격 canary 후보로 올린다.

## 장후 체크리스트 (15:20~)

- [ ] `[VisibleResult0424] 금요일 승격 후보 1축 최종선정` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 15:20~15:30`, `Track: Plan`)
- [ ] `[VisibleResult0424] 승격 1축 실행 승인 또는 보류+재시각 확정` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 15:30~15:40`, `Track: ScalpingLogic`)
  - 판정 기준: `승격 실행`이면 축 1개만 선택하고 롤백 가드 포함, `보류`이면 원인 1개와 재실행 시각 1개를 동시에 기록
- [ ] `[OpsEODSplit0424] EOD/NXT 착수 여부 재판정` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 15:40~15:50`, `Track: ScalpingLogic`)
  - Source: [audit-reports/2026-04-22-plan-rebase-central-audit-review.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-22-plan-rebase-central-audit-review.md)
  - 판정 기준: `exit_rule`, `sell_order_status`, `sell_fail_reason`, `is_nxt`, `COMPLETED+valid profit_rate`, full/partial 분리 기준으로 착수/다음주 이관 중 하나를 기록한다.
- [ ] `[AIPrompt0424] AI 엔진 A/B 재개 여부 판정` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 15:50~16:00`, `Track: AIPrompt`)
  - Source: [2026-04-21-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-21-stage2-todo-checklist.md)
  - 판정 기준: `entry_filter_quality` canary 1차 판정과 `buy_recovery_canary` 1일차/2일차 결과가 충분할 때만 A/B 재개를 검토한다. 표본 부족이면 A/B 재개 금지, 추가 보류 사유와 다음 재검토 시각을 기록한다.
- [ ] `[ScaleIn0424] PYRAMID zero_qty Stage 1 remote canary 승인 또는 보류 사유 기록` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:10`, `Track: ScalpingLogic`)
  - 판정 기준: `SCALPING/PYRAMID only`, `zero_qty` 감소, `MAX_POSITION_PCT` 위반 0건, `full/partial fill` 체결품질 악화 없음일 때만 승인
- [ ] `[ScaleIn0424] main은 PYRAMID zero_qty Stage 1 코드 적재 가능 범위(flag OFF)만 허용 확인` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:10~16:15`, `Track: Plan`)
  - 판정 기준: `main` 실주문 변경은 금지, 다음 승인 전까지 `flag OFF` 유지
- [ ] `[ScaleIn0424] 물타기축(AVG_DOWN/REVERSAL_ADD) 다음주 remote shadow 착수 승인 또는 보류 사유 기록` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:15~16:25`, `Track: ScalpingLogic`)
  - 판정 기준: `reversal_add_candidate` 표본 충분성, `buy_qty>=3` 비율, `add_judgment_locked` 교차영향, `split-entry/HOLDING` 관찰축 비간섭 조건이 충족될 때만 다음주 `remote shadow-only` 승인
- [ ] `[AuditFix0424] 주간 regime 태그 및 평균 거래대금 수준 병기` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:30`, `Track: Plan`)
- [ ] `[AuditFix0424] canary 1축 유지 + 독립축 shadow 병렬허용 규칙 확인` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:35`, `Track: Plan`)
- [ ] `[VisibleResult0424] 기대값 중심 우선지표(거래수/퍼널/blocker/체결품질/missed_upside) 재검증` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:35~16:45`, `Track: Plan`)
- [ ] `[VisibleResult0424] 다음주 PREOPEN 실행지시서에 승격축 1개 반영` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~16:55`, `Track: AIPrompt`)
- [ ] `[OpsFollowup0424] 패턴랩 주간 cron 산출물/로그 정합성 점검` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:55~17:00`, `Track: Plan`)
  - 판정 기준: `logs/claude_scalping_pattern_lab_cron.log`, `logs/gemini_scalping_pattern_lab_cron.log` 에러 없음 + 각 `outputs/` 최신 산출물 갱신 확인
- [ ] 미확정 시 `사유 + 다음 실행시각` 기록 (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:10`, `Track: Plan`)

## 참고 문서

- [2026-04-18-nextweek-validation-axis-table.md](./archive/legacy-tuning-2026-04-06-to-2026-04-20/2026-04-18-nextweek-validation-axis-table.md)
- [2026-04-23-stage2-todo-checklist.md](./2026-04-23-stage2-todo-checklist.md)
- [2026-04-20-stage2-todo-checklist.md](./2026-04-20-stage2-todo-checklist.md)
- [2026-04-21-stage2-todo-checklist.md](./2026-04-21-stage2-todo-checklist.md)
- [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md)
- [plan-korStockScanPerformanceOptimization.performance-report.md](./plan-korStockScanPerformanceOptimization.performance-report.md)
- [2026-04-20-scale-in-qty-logic-final-review-v1.1.md](./archive/legacy-tuning-2026-04-06-to-2026-04-20/2026-04-20-scale-in-qty-logic-final-review-v1.1.md)
