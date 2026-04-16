# 2026-04-17 Stage 2 To-Do Checklist

## 목적

- `P2 HOLDING 포지션 컨텍스트 주입`은 `착수` 또는 `보류 사유 기록` 둘 중 하나로 닫는다.
- `WATCHING 선통과 조건 문맥 주입`도 같은 날 병렬 착수 또는 보류 사유 기록으로 닫는다.
- `P1`에서 이미 본 결과를 기준으로 `P2`로 넘어갈지, `P1` 보강을 하루 더 할지 결정한다.
- `AIPrompt 작업 9 정량형 수급 피처 이식 1차` helper scope를 확정한다.

## 장후 체크리스트 (15:30~)

- [ ] `AIPrompt P2 HOLDING 포지션 컨텍스트 주입` 착수 또는 보류 사유 기록
- [ ] `AIPrompt 작업 7 WATCHING 선통과 조건 문맥 주입` 착수 또는 보류 사유 기록
- [ ] `AIPrompt 작업 9 정량형 수급 피처 이식 1차` helper scope 확정
- [ ] `P1` 보류 시 `사유 + 다음 실행시각` 기록

## 장전 체크리스트 (08:00~09:00)

- [ ] `[Checklist0417] SCALP loss_fallback_probe add_judgment_locked 우회 canary 검증` (`Due: 2026-04-17`, `Slot: PREOPEN`, `TimeWindow: 08:00~08:10`)
  - 판정 기준: 손절 직전 `loss_fallback_probe`에서 `gate_reason=add_judgment_locked` 비중이 0%로 내려갔는지 확인
  - 근거: 기존 lock 공유로 fallback 관찰 타이밍이 구조적으로 차단됨
  - 다음 액션: 실패 시 즉시 롤백(`skip_add_judgment_lock=False`) 또는 별도 lock key 분리안 확정
- [ ] `[Checklist0417] SCALP 손절 직전 fallback 후보(loss_fallback_probe) 전일 로그 판정` (`Due: 2026-04-17`, `Slot: PREOPEN`, `TimeWindow: 08:00~08:20`)
  - 판정 기준: `loss_fallback_probe`에서 후보(`fallback_candidate=true`) 빈도/조건을 손절건과 대조해 유효성 판정
  - 근거: 한화오션 손절 리뷰에서 fallback 기회 계측 필요성 확인
  - 다음 액션: 1) observe-only 유지 또는 2) 실전 전환 승인안 작성
- [ ] `[Checklist0417] SCALP 손절 fallback 실전 전환 여부 결정(기본 OFF)` (`Due: 2026-04-17`, `Slot: PREOPEN`, `TimeWindow: 08:20~09:00`)
  - 판정 기준: `SCALP_LOSS_FALLBACK_ENABLED/OBSERVE_ONLY` 토글값 확정 및 운영기록 반영
  - 근거: 손절 축은 체결 리스크가 높아 관찰 근거 없이 즉시 ON 금지
  - 다음 액션: 승인 시 `observe_only=False` 전환, 미승인 시 관찰기간 연장

## 참고 문서

- [2026-04-16-stage2-todo-checklist.md](./2026-04-16-stage2-todo-checklist.md)
- [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md)
- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)
