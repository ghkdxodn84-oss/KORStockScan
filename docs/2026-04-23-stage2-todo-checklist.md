# 2026-04-23 Stage 2 To-Do Checklist

## 목적

- `2026-04-21`에 `AIPrompt 작업 12 Raw 입력 축소 A/B 점검` 범위가 미확정이었을 때만 오늘 최종확정으로 닫는다.
- 구현까지 한 번에 밀지 않더라도 최소 범위 확정은 오늘 닫는다.
- `PYRAMID zero_qty Stage 1`은 현재 관찰축을 흔들지 않게 `remote canary 후보 범위/flag/rollback guard`까지만 고정한다.

## 장후 체크리스트 (15:30~)

- [ ] `[AuditFix0423] 2026-04-21 미확정 시 AIPrompt 작업 12 Raw 입력 축소 A/B 점검 범위 최종확정` (`Due: 2026-04-23`, `Slot: POSTCLOSE`, `TimeWindow: 15:30~15:40`, `Track: AIPrompt`)
  - 실행 메모: `2026-04-21`에 확정됐다면 상태 확인만 하고 재작성하지 않는다.
- [ ] `[AuditFix0423] 작업12 범위 미확정 시 사유 + 다음 실행시각 + escalation 경로 기록` (`Due: 2026-04-23`, `Slot: POSTCLOSE`, `TimeWindow: 15:40~15:50`, `Track: Plan`)
- [ ] `[ScaleIn0423] PYRAMID zero_qty Stage 1 원격 범위/feature flag/rollback guard 확정` (`Due: 2026-04-23`, `Slot: POSTCLOSE`, `TimeWindow: 15:50~16:00`, `Track: ScalpingLogic`)
  - 판정 기준: `SCALPING/PYRAMID only`, `remote canary 후보`, `main flag OFF`, `zero_qty/cap_qty/floor_applied` 관찰 로그 필수
- [ ] `[ScaleIn0423] PYRAMID zero_qty Stage 1은 split-entry/HOLDING 관찰축과 분리 유지 확인` (`Due: 2026-04-23`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:10`, `Track: Plan`)
  - 판정 기준: 같은 서버/같은 관찰창에 실주문 변경 2축 이상 금지
- [ ] `[ScaleIn0423] 물타기축(AVG_DOWN/REVERSAL_ADD) 재오픈 일정 및 shadow 전제조건 확정` (`Due: 2026-04-23`, `Slot: POSTCLOSE`, `TimeWindow: 16:10~16:20`, `Track: ScalpingLogic`)
  - 판정 기준: `buy_qty 분포`, `reversal_add_candidate 표본`, `add_judgment_locked 교차`, `next-week remote shadow-only 여부`를 함께 기록하고, 이번 주 실주문 변경 금지를 명시
- [ ] `[ScaleIn0423] 트레이더 검토용 add-position 축 보고서 기준으로 불타기/물타기/보유연장 우선순위 확정` (`Due: 2026-04-23`, `Slot: POSTCLOSE`, `TimeWindow: 16:20~16:30`, `Track: ScalpingLogic`)
  - 판정 기준: `2026-04-20-add-position-axis-trader-review.md`를 입력으로 사용하고, `PYRAMID 유지`, `AVG_DOWN shadow`, `REVERSAL_ADD shadow`, `보유연장 우선` 중 이번 주 결론 1개만 남긴다
- [ ] 범위 확정 실패 시 `사유 + 다음 실행시각` 기록 (`Due: 2026-04-23`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:35`, `Track: Plan`)

## 참고 문서

- [2026-04-22-stage2-todo-checklist.md](./2026-04-22-stage2-todo-checklist.md)
- [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md)
- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)
- [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md)
- [plan-korStockScanPerformanceOptimization.performance-report.md](./plan-korStockScanPerformanceOptimization.performance-report.md)
- [2026-04-20-add-position-axis-trader-review.md](./2026-04-20-add-position-axis-trader-review.md)
