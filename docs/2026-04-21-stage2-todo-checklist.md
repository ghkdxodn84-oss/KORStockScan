# 2026-04-21 Stage 2 To-Do Checklist

## 목적

- `2026-04-20 rebase` 1일차 결과를 기준으로 다음 split-entry 축 착수 가능 여부를 먼저 닫는다.
- `split-entry 즉시 재평가`는 전일 `N_min/Δ_min/false_entry_rate` 기준이 고정된 경우에만 오늘 shadow 착수 후보로 본다.
- `split-entry leakage`와 `HOLDING shadow` 관측/기준정리를 `작업 12`보다 먼저 본다.
- `AIPrompt 작업 12 Raw 입력 축소 A/B 점검` 범위를 확정한다.
- `작업 10/11` 결과를 본 뒤 입력 축소 범위를 뒤로 미루지 않고 닫는다.
- `HOLDING 성과 최종판정`은 schema 변경 버퍼를 두고 `2026-04-22`로 이관한다.

## 장후 체크리스트 (15:30~)

- [ ] `[AuditFix0421] split-entry 즉시 재평가 shadow 1일차 착수 또는 보류 기록` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 15:30~15:40`, `Track: ScalpingLogic`)
  - 판정 기준: `N_min/Δ_min` 충족 + `false_entry_rate` 상한 확정 시에만 착수, 아니면 보류 사유와 재시각 기록
  - 선행 메모 (`2026-04-20 PREOPEN`): `D+1 이관 확정`. `N_min=50`, `Δ_min=+3.0%p`, `PrimaryMetric=budget_pass_to_submitted_rate` 미충족 시 착수 금지
- [ ] `[VisibleResult0421] split-entry leakage canary 승격 또는 보류 사유 기록` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 15:40~15:50`, `Track: ScalpingLogic`)
- [ ] `[AuditFix0421] HOLDING shadow baseline 재계산 + 관측버퍼(D+1) 확인` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 15:50~16:00`, `Track: AIPrompt`)
- [ ] `AIPrompt 작업 12 Raw 입력 축소 A/B 점검` 범위 확정 (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:10`, `Track: AIPrompt`)
- [ ] `[VisibleResult0421] 다음 영업일 승격축 1개 고정 또는 보류 사유 기록` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:10~16:20`, `Track: Plan`)
- [ ] `[PlanSync0421] 원격 canary 보류 유지 + AI 엔진 A/B 전환 일정 고정` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:20~16:30`, `Track: Plan`)
  - 판정 기준: 현재 튜닝 축에는 원격 신규 canary를 열지 않고, `A/B preflight`를 `2026-04-23 POSTCLOSE`로 고정
- [ ] `[PlanSync0421] 개별종목(에이럭스) 관찰축 4분해 유지 여부 재확인` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:40`, `Track: Plan`)
  - 판정 기준: `EntryGate/Latency/Liquidity/HoldingExit` 4축 표본이 충분하지 않으면 scale-in/holding/latency 로직 변경 모두 보류
- [ ] `[AuditFix0421] HOLDING 성과판정 D+2(2026-04-22) 이관 기록` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:20~16:25`, `Track: AIPrompt`)
- [ ] 범위 확정 실패 시 `사유 + 다음 실행시각` 기록 (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:30`, `Track: AIPrompt`)

## 참고 문서

- [2026-04-19-stage2-todo-checklist.md](./2026-04-19-stage2-todo-checklist.md)
- [2026-04-17-midterm-tuning-performance-report.md](./2026-04-17-midterm-tuning-performance-report.md)
- [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md)
- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)
- [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md)
- [plan-korStockScanPerformanceOptimization.performance-report.md](./plan-korStockScanPerformanceOptimization.performance-report.md)
