# 2026-04-23 Stage 2 To-Do Checklist

## 목적

- `2026-04-21`에 `AIPrompt 작업 12 Raw 입력 축소 A/B 점검` 범위가 미확정이었을 때만 오늘 최종확정으로 닫는다.
- `entry_filter_quality` 착수 가능성을 `2026-04-23 POSTCLOSE 15:20~15:35 KST`에 절대시각으로 재판정한다.
- 구현까지 한 번에 밀지 않더라도 최소 범위 확정은 오늘 닫는다.
- `PYRAMID zero_qty Stage 1`은 현재 관찰축을 흔들지 않게 `remote canary 후보 범위/flag/rollback guard`까지만 고정한다.

## 장후 체크리스트 (15:20~)

- [ ] `[PlanRebase0423] entry_filter_quality 착수 가능성 재판정` (`Due: 2026-04-23`, `Slot: POSTCLOSE`, `TimeWindow: 15:20~15:35`, `Track: ScalpingLogic`)
  - Source: [audit-reports/2026-04-22-plan-rebase-central-audit-review.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-22-plan-rebase-central-audit-review.md)
  - 판정 기준: `buy_recovery_canary` 1일차/2일차 결과, `normal_only` 실현손익, `full/partial` 체결품질, blocker 4축 분포, `recovery_false_positive_rate`를 기준으로 착수/미착수/재교정 중 하나로 닫는다.
  - 금지: `position_addition_policy`, EOD/NXT, AI 엔진 A/B와 같은 날 live 축으로 섞지 않는다.
- [ ] `[PlanSync0423] AI 엔진 A/B preflight 범위 확정` (`Due: 2026-04-23`, `Slot: POSTCLOSE`, `TimeWindow: 15:35~15:50`, `Track: AIPrompt`)
  - 판정 기준: `2026-04-24 POSTCLOSE 15:50~16:00` A/B 재개 여부 판정에 필요한 설정값, 관찰축, 롤백가드, remote 정합화 범위를 문서 고정한다.
- [ ] `[AuditFix0423] 2026-04-21 미확정 시 AIPrompt 작업 12 Raw 입력 축소 A/B 점검 범위 최종확정` (`Due: 2026-04-23`, `Slot: POSTCLOSE`, `TimeWindow: 15:50~16:00`, `Track: AIPrompt`)
  - 실행 메모: `2026-04-21`에 확정됐다면 상태 확인만 하고 재작성하지 않는다.
- [ ] `[AuditFix0423] 작업12 범위 미확정 시 사유 + 다음 실행시각 + escalation 경로 기록` (`Due: 2026-04-23`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:10`, `Track: Plan`)
- [ ] `[ScaleIn0423] PYRAMID zero_qty Stage 1 원격 범위/feature flag/rollback guard 확정` (`Due: 2026-04-23`, `Slot: POSTCLOSE`, `TimeWindow: 16:10~16:20`, `Track: ScalpingLogic`)
  - 판정 기준: `SCALPING/PYRAMID only`, `remote canary 후보`, `main flag OFF`, `zero_qty/cap_qty/floor_applied` 관찰 로그 필수
- [ ] `[ScaleIn0423] PYRAMID zero_qty Stage 1은 split-entry/HOLDING 관찰축과 분리 유지 확인` (`Due: 2026-04-23`, `Slot: POSTCLOSE`, `TimeWindow: 16:20~16:30`, `Track: Plan`)
  - 판정 기준: 같은 서버/같은 관찰창에 실주문 변경 2축 이상 금지
- [ ] `[ScaleIn0423] 물타기축(AVG_DOWN/REVERSAL_ADD) 재오픈 일정 및 shadow 전제조건 확정` (`Due: 2026-04-23`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:40`, `Track: ScalpingLogic`)
  - 판정 기준: `buy_qty 분포`, `reversal_add_candidate 표본`, `add_judgment_locked 교차`, `next-week remote shadow-only 여부`를 함께 기록하고, 이번 주 실주문 변경 금지를 명시
- [ ] `[PlanRebase0423] position_addition_policy 후순위 설계 초안` (`Due: 2026-04-23`, `Slot: POSTCLOSE`, `TimeWindow: 16:40~16:50`, `Track: ScalpingLogic`)
  - Source: [audit-reports/2026-04-22-plan-rebase-central-audit-review.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-22-plan-rebase-central-audit-review.md)
  - 판정 기준: `archive/legacy-tuning-2026-04-06-to-2026-04-20/2026-04-20-add-position-axis-trader-review.md`와 `[HoldingCtx0422]`의 `position_context` 확정 여부를 입력으로 사용해, live 적용 없이 상태머신 초안만 작성한다.
  - 금지: `entry_filter_quality` 착수/미착수 판정 전후 같은 날 live 축으로 열지 않는다.
- [ ] `[OpsEODSplit0423] 관찰축 정리 완료 시 KRX/NXT 분리 EOD 청산 시간/실행경로 확정` (`Due: 2026-04-23`, `Slot: POSTCLOSE`, `TimeWindow: 16:50~17:00`, `Track: ScalpingLogic`)
  - 판정 기준: `partial/rebase/soft-stop` 관찰축이 당일 기준으로 잠겼을 때만 착수한다. `KRX`는 정규장 종료 전 청산 재시도 버퍼를 확보하고, `NXT 가능` 종목은 별도 시간창/경로로 분리해 `sell_order_failed -> HOLDING 롤백 반복` 감소 목표를 수치로 기록한다.
  - 산출물: 다음 영업일 적용 전 `시간 기준(예: KRX 15:2x, NXT 15:4x+)`, `코호트 분류 기준(is_nxt)`, `롤백 가드` 3개를 문서에 고정한다.
- [ ] 범위 확정 실패 시 `사유 + 다음 실행시각` 기록 (`Due: 2026-04-23`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:05`, `Track: Plan`)

## 참고 문서

- [2026-04-22-stage2-todo-checklist.md](./2026-04-22-stage2-todo-checklist.md)
- [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md)
- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)
- [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md)
- [plan-korStockScanPerformanceOptimization.performance-report.md](./plan-korStockScanPerformanceOptimization.performance-report.md)
- [2026-04-20-add-position-axis-trader-review.md](./archive/legacy-tuning-2026-04-06-to-2026-04-20/2026-04-20-add-position-axis-trader-review.md)
