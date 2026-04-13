# 2026-04-14 Stage 2 To-Do Checklist

## 목적

- `2026-04-13` 장후 판정을 `2026-04-14` 운영 체크리스트로 승격한다.
- 최우선은 `RELAX-LATENCY` 원격 강화 관찰의 반복 재현성 확인이다.
- `RELAX-DYNSTR/RELAX-OVERBOUGHT`는 실전 재오픈이 아니라 `재설계/표본 누적`만 진행한다.
- `관찰 축 추가`는 여기서 끝낸다. `2026-04-14 장후`에는 `반영 / 보류+단일축 전환 / 관찰 종료` 중 하나로 결론내고, `2026-04-15 장전`에는 바로 착수한다.
- `기존 관찰축`은 더 많은 분석을 위한 입력이 아니라, `2026-04-14 장후 개선 결론`과 `2026-04-15 장중 지속 점검`을 위한 검증축으로만 사용한다.

## 2026-04-13 장후 승격 요약

- `RELAX-LATENCY`: `강화 유지`
  - `submitted_stocks=0` 유지라 즉시 확대 근거는 없지만, `quote_stale=False` 축을 포함한 `latency_danger_reasons` 분해와 `remote_v2` 관찰은 계속 유효하다.
- `RELAX-DYNSTR`: `유지 + 재설계`
  - `below_window_buy_value / below_buy_ratio / below_strength_base` 분해가 가능한 로그는 확보됐다.
- `RELAX-OVERBOUGHT`: `유지`
  - `blocked_overbought=20` 수준으로 표본이 누적돼 실전 완화 재오픈 근거는 없다.
- 체결 품질:
  - `entered_rows=1`, `completed_trades=1`, `holding_events=0`
  - 신규 `submitted/holding_started` 전환이 없어 `full fill / partial fill` 해석은 추가 표본이 필요하다.
- live hard stop taxonomy:
  - `hard_time_stop_shadow`는 여전히 shadow-only로 유지한다.
  - live exit는 `scalp_preset_hard_stop_pct`, `protect_hard_stop`, `scalp_hard_stop_pct`를 분리해서 본다.
- 원격 비교검증:
  - `2026-04-13 15:46:39` 자동 비교에서 `Performance Tuning`, `Entry Pipeline Flow`가 `remote_error`였다.
  - 따라서 `2026-04-14`에는 API 비교만으로 닫지 말고 snapshot 기준 재점검이 필요하다.

## 장전 체크리스트 (08:00~09:00)

- [ ] `2026-04-13` 장후 판정이 원격/본서버 설정에 의도치 않게 번진 축이 없는지 확인
- [ ] `RELAX-LATENCY` 관찰 기준을 `quote_stale=False`, `latency_danger_reasons`, `expired_armed` 중심으로 재고정
- [ ] `GitHub Project -> Google Calendar` / `Sync Docs Backlog To GitHub Project` 마지막 실행 상태 확인
- [ ] 전일 `remote_error` 난 `Performance Tuning` / `Entry Pipeline Flow`를 snapshot 기준 재점검할 경로 확인
- [ ] `신규 관찰축 추가 금지`, `개선 먼저`, `기존 축은 개선 후 점검용` 원칙을 오늘 작업지시로 재고정

## 장중 체크리스트 (09:00~15:30)

- [ ] `RELAX-LATENCY` 반복 재현성 관찰
  - `AI BUY -> entry_armed -> budget_pass -> submitted` 퍼널 재확인
  - `quote_stale=False latency_block`와 `expired_armed`를 분리 기록
  - `latency_danger_reasons` 상위 사유 1~3개가 유지되는지 본다
- [ ] 체결 품질 관찰
  - `full fill / partial fill`을 분리 기록
  - `preset_exit_sync_mismatch` 여부를 함께 본다
- [ ] `RELAX-DYNSTR` 재설계 표본 누적
  - `below_window_buy_value / below_buy_ratio / below_strength_base`를 `momentum_tag / threshold_profile`별로 계속 분리 기록
- [ ] `RELAX-OVERBOUGHT` 표본 누적
  - `blocked_overbought`가 missed-winner와 직접 연결되는지 계속 분리 기록
- [ ] live hard stop taxonomy 관찰
  - `scalp_preset_hard_stop_pct / protect_hard_stop / scalp_hard_stop_pct / hard_time_stop_shadow` 표본 여부를 계속 기록
- [ ] 원격서버 비교검증
  - API 비교가 `remote_error`이면 `trade_review / performance_tuning / post_sell_feedback / entry_pipeline_flow`를 snapshot 기준으로 다시 대조한다
  - 비교 결과는 `safe metric`, `fetch 재현성`, `원인 설명 가능 여부` 기준으로 짧게 메모한다
- [ ] 장후 개선 결론 준비
  - 신규 가설 발굴이 아니라 `RELAX-LATENCY 반영/보류`, `RELAX-DYNSTR 1축 착수 여부`를 결정할 만큼만 기존 관찰축을 점검한다

## 장후 체크리스트 (15:30~)

- [ ] `RELAX-LATENCY` 운영서버 승격 가능/불가 1차 결론
- [ ] `RELAX-LATENCY` 운영서버 승격 가능/불가 최종 결론
- [ ] 체결 품질 표본이 생기면 `full fill / partial fill / preset_exit_sync_mismatch`까지 포함해 재판정
- [ ] `RELAX-DYNSTR` 재설계 후보를 `threshold_profile`별 canary 축 1개로 압축
- [ ] `post-sell` 지표 기준 `원격 1축 매도시점 canary` 재후보화
- [ ] `2026-04-15` 장전 반영/착수 항목 확정
- [ ] 원격 비교검증을 snapshot 기준으로 닫고 `remote_error` 원인을 설명 가능하게 정리
- [ ] `2026-04-15 장중 지속 점검용 관찰축`만 남기고, `신규 관찰축 추가`는 명시적으로 중단

## 참고 문서

- [2026-04-13-stage2-todo-checklist.md](./2026-04-13-stage2-todo-checklist.md)
- [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md)
- [2026-04-10-scalping-ai-coding-instructions.md](./2026-04-10-scalping-ai-coding-instructions.md)
- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)
