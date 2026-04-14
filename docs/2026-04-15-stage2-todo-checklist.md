# 2026-04-15 Stage 2 To-Do Checklist

## 목적

- `2026-04-14 장후` 결론을 `2026-04-15 08:30`까지 실제 실행으로 옮긴다.
- 오늘은 `관찰`보다 `착수`가 우선이다. 이미 구축한 관찰축은 변경 후 지속 점검용으로만 사용한다.
- `main` 반영은 오늘 실행하는 `develop` 축의 장후 결과가 있을 때만 연다. 같은 축의 `main` 선적용은 금지한다.
- `RELAX-DYNSTR`는 `momentum_tag` 1축 원격 canary를 시작한다.
- `partial fill min_fill_ratio`는 전용 코드 경로/롤백 토글을 먼저 추가하고, 준비가 끝나는 즉시 원격 canary를 연다.
- `Phase 2`는 오늘 시작한다. `RELAX-LATENCY`가 승격되면 `Phase 2-1`을 병행 착수하고, 승격이 보류되면 `Phase 2-2`를 단독 착수한다.
- `expired_armed` 처리 로직은 오늘 장후까지 설계 문서 완료를 목표로 한다.
- 전일 장후에 착수한 `AIPrompt 작업 5/8/10`은 오늘 구현 진행과 검증 입력 고정까지 이어간다.
- `SCALPING 모델 shadow 비교안`은 `2026-04-15`에 바로 실표본을 수집한다. `PREOPEN` 구현 착수, `INTRADAY` 첫 shadow 수집, `POSTCLOSE` 첫 비교표 생성을 같은 날 닫는다.

## 전일 장후에서 받아야 할 확정값

- `RELAX-LATENCY` 운영 반영/보류 최종 결론
- `RELAX-DYNSTR` 원격 canary 대상 `momentum_tag`
- `partial fill min_fill_ratio` 기본값과 rollback 가드
  - `2026-04-14 15:38 KST` 장후 확정 설계값은 `default=0.20`, `strong_absolute_override=0.10`, `SCALP_PRESET_TP=0.00(적용 제외)`다.
  - 코드 경로/토글은 `2026-04-14 POSTCLOSE`에 구현 완료했고, `2026-04-15`는 env 주입 + dry-run + canary 개시 판정만 수행한다.
- `expired_armed` 처리 로직 설계 범위와 문서 위치
  - `태광` 단일표본이 아니라 전수 `expired_armed` 분포 + 상위 코호트 + anchor case 조합으로 설계한다
- `AI overlap audit -> selective override` 착수 입력과 일정
- `AIPrompt 작업 5/8/10` write scope / rollback 가드 / 비교지표

## 장전 체크리스트 (08:00~08:30)

- [x] `[반영대상: main,remote]` `2026-04-14 장후` 결론대로 `RELAX-LATENCY` 반영/보류 상태를 운영/원격 설정에 적용
- [x] `[반영대상: remote]` `RELAX-DYNSTR` `momentum_tag` 1축 원격 canary 설정 완료 (`08:30`까지)
- [x] `[반영대상: remote]` `partial fill min_fill_ratio` env 주입값 확인 + dry-run 검증 완료 (`08:30`까지)
  - 기본값(`enabled=false`) 확인 후 원격 canary에서만 `enabled=true`로 전환한다.
- [x] `[반영대상: remote]` `SCALPING_PROMPT_SPLIT` 토글/실행값 확인 (`08:20`까지)
  - `KORSTOCKSCAN_SCALPING_PROMPT_SPLIT_ENABLED=true`(또는 unset) 확인
  - `ENTRY_PIPELINE/HOLDING_PIPELINE`에서 `ai_prompt_type=scalping_watching/scalping_holding` 표본 1건 이상 확인
- [x] `[반영대상: remote]` 장전 go/no-go 판정 기록 (`08:25~08:30`)
  - `Go`: `partial fill` dry-run 이상 없음 + 프롬프트 분리 표본 확인 + 위험 알람 없음
  - `No-Go`: dry-run 오류/프롬프트 분리 미확인/운영 리스크 발생 시 canary 보류, `사유+재시각` 기록
- [x] `Phase 2` 착수 선언 기록 (`RELAX-LATENCY 승격 시 2-1 병행`, `보류 시 2-2 단독`)
- [x] `[반영대상: main]` 오늘 `develop`에 적용한 축별 `main` 승격 최소 시점(`2026-04-16` 이후)을 작업 메모에 고정
- [x] 오늘 실행 축의 rollback 가드와 장중 관찰 포인트를 재고정
- [x] `expired_armed` 설계 입력은 `단일 종목`이 아니라 `전수 분포 + 상위 코호트 + anchor case` 기준으로 읽는다고 오늘 메모에 고정
- [x] `[반영대상: main,remote]` `SCALPING 모델 shadow 비교안` `WATCHING shared prompt` 구현 착수 및 원격/본서버 공통 로그 필드 고정
  - `08:30`까지 `Tier2 Gemini Flash vs GPT-4.1-mini` shadow 호출 경로와 `action/score/counterfactual` 로그 스키마를 develop 기준으로 닫는다.

## 2026-04-15 장전 실행 메모

- [x] `RELAX-LATENCY` 운영/원격 적용 상태 재확인 (`2026-04-15 07:50 KST`)
  - 판정: `main` 승격은 계속 보류, 원격은 기존 `remote_v2` 관찰축만 유지한다.
  - 근거: 전일 최종 결론이 `운영서버 승격 보류`였고, 오늘도 신규 latency 완화는 추가하지 않는 조건이 유지된다.
  - 다음 액션: 장중에는 `quote_stale=False` 여부보다 `latency_danger_reasons`, `expired_armed`, `preset_exit_sync_mismatch`만 재확인한다.

- [x] `RELAX-DYNSTR momentum_tag=SCANNER` 1축 원격 canary 적용 (`2026-04-15 07:50 KST`)
  - 판정: 적용 완료.
  - 근거: 원격 `override.conf`와 `bot_main.py` 런타임 env에서 `KORSTOCKSCAN_SCALP_DYNAMIC_STRENGTH_CANARY_ENABLED=true`, `..._TAGS=SCANNER`, 허용 사유 3종이 모두 확인됐다.
  - 다음 액션: 장중 퍼널은 `AI BUY -> entry_armed -> budget_pass -> submitted` 순으로만 기록하고, `main` 승격 판정은 `2026-04-16` 이후로 미룬다.

- [x] `partial fill min_fill_ratio` 원격 canary 개시 (`2026-04-15 07:50~07:51 KST`)
  - 판정: `Go`.
  - 근거: 원격 `.venv` 기준 관련 테스트 `74 passed`, `py_compile` 통과, `gunicorn`/`bot_main.py` 런타임 env에서 `enabled=true`, `default=0.20`, `strong_absolute_override=0.10`, `SCALP_PRESET_TP=0.00` 확인.
  - 다음 액션: 장중에는 `partial fill 억제`뿐 아니라 `submitted 감소/미진입 기회비용`까지 같이 본다.

- [x] `SCALPING_PROMPT_SPLIT` / `WATCHING shared prompt shadow` 착수 (`2026-04-15 07:51 KST`)
  - 판정: 코드 착수 및 공통 로그 필드 고정 완료.
  - 근거: `watching_shared_prompt_shadow` stage에 `gemini_action`, `gemini_score`, `gpt_action`, `gpt_score`, `action_diverged`, `score_gap`, `gpt_model`, `shadow_extra_ms`를 남기도록 구현했고, 원격 `bot_main.py` 재기동까지 완료했다.
  - 다음 액션: 장중 첫 표본 발생 후 `counterfactual` 연결은 장후 비교표에서 묶는다.

- [x] `Phase 2` 착수 선언 / 오늘 메모 고정 (`2026-04-15 07:51 KST`)
  - 판정: `RELAX-LATENCY` 승격 보류 기준으로 `Phase 2-2 단독 착수`.
  - 근거: 오늘 실제 실행 축은 `RELAX-DYNSTR`, `partial fill`, `WATCHING shared prompt`이며, `main` 승격 최소 시점은 `2026-04-16 POSTCLOSE 이후`로 고정한다.
  - 다음 액션: `expired_armed` 설계 문서는 전수 분포 + 상위 코호트 + anchor case 기준으로 장후까지 닫는다.

- [x] 오늘 실행 축 rollback 가드 / 장중 관찰 포인트 재고정 (`2026-04-15 07:51 KST`)
  - 판정: rollback 가드가 한 축씩 분리돼 있어 canary 운영 가능.
  - 근거: `RELAX-DYNSTR`는 `KORSTOCKSCAN_SCALP_DYNAMIC_STRENGTH_CANARY_ENABLED=false`, `partial fill`은 `KORSTOCKSCAN_SCALP_PARTIAL_FILL_RATIO_CANARY_ENABLED=false`, 프롬프트 분리는 `KORSTOCKSCAN_SCALPING_PROMPT_SPLIT_ENABLED=false` 1개 토글로 각각 닫힌다.
  - 다음 액션: 장중에는 `blocker 분포`, `체결 품질(full/partial 분리)`, `WATCHING shared prompt shadow action_diverged`만 본다.

## 장중 체크리스트 (09:00~15:30)

- [ ] `RELAX-DYNSTR` 1축 canary의 `AI BUY -> entry_armed -> budget_pass -> submitted` 퍼널 변화를 기록
- [ ] `partial fill min_fill_ratio` canary(개시 시)의 `partial fill 억제 / 체결 기회 감소`를 함께 기록
- [ ] `RELAX-LATENCY`는 전일 결론대로 적용된 축만 지속 점검하고, 신규 완화는 추가하지 않는다
- [ ] 기존 관찰축은 `변경 후 검증`에 필요한 범위로만 유지한다
- [ ] `expired_armed` 전수 분포 재확인
  - 시간대 / 종목 / `momentum_tag` / `threshold_profile` / `entry_armed_expired_after_wait` 상위 코호트를 다시 묶는다
  - `태광`은 anchor case로만 유지하고 단일 종목 결론으로 확대하지 않는다
- [ ] `AIPrompt 작업 5 WATCHING/HOLDING 프롬프트 물리 분리` 구현 진행 / 로그 비교축 확인
- [ ] `AIPrompt 작업 8 감사용 핵심값 3종 투입` 전일 착수분 구현/검증 지속
- [ ] `AIPrompt 작업 10 HOLDING hybrid 적용` `FORCE_EXIT` 제한형 MVP 구현 지속 / canary-ready 입력 정리
- [ ] `AIPrompt 작업 9 정량형 수급 피처 이식 1차` helper scope 초안 정리
- [ ] `SCALPING 모델 shadow 비교안` 첫 실표본 수집 시작
  - `WATCHING shared prompt` 동일 입력에 대해 `gemini_action/score`, `gpt_action/score`, `action_diverged`, `score_gap`를 오늘 장중부터 누적한다.

## 장후 체크리스트 (15:30~)

- [ ] `expired_armed` 처리 로직 설계 문서 작성 완료
  - 재진입 허용 여부는 `태광` 1건이 아니라 전수 분포와 상위 코호트 기준으로 판정한다
  - 문서에는 `anchor case`와 `통계 입력`을 분리해서 쓴다
- [ ] `RELAX-DYNSTR` 1일차 canary 결과 1차 정리
- [ ] `partial fill min_fill_ratio` 구현/검증 결과와 canary 개시 여부 1차 정리
- [ ] 오늘 `develop` 결과 기준으로 `2026-04-16 main` 승격 가능/불가 초안을 항목별로 기록
- [ ] `2026-04-16` `AI overlap audit -> selective override` 설계 착수 입력값을 고정
- [ ] `AIPrompt 즉시 코드축` 구현 진행 결과 정리
  - `작업 5/8/10`의 `2026-04-16` 평가 포인트를 고정한다
- [ ] `AIPrompt 작업 8 감사용 핵심값 3종 투입` 전일 착수분 결과 정리
- [ ] `AIPrompt 작업 9 정량형 수급 피처 이식 1차` helper scope 초안을 `2026-04-17` 확정형으로 정리
- [ ] `AIPrompt 작업 10 HOLDING hybrid 적용` `FORCE_EXIT` 제한형 MVP 착수 상태와 `2026-04-16` 입력값 정리
- [ ] `SCALPING 모델 shadow 비교안` 첫 장후 비교표 생성
  - `entered_if_gemini`, `entered_if_gpt`, `realized_pnl_if_gemini`, `realized_pnl_if_gpt`, `missed_winner_cost_if_gemini`, `missed_winner_cost_if_gpt`를 오늘 체결/미진입 복기와 연결해 1차 비교표로 남긴다.
- [ ] 오늘 보류된 항목이 있으면 `사유 + 다음 실행시각`을 문서에 명시

## 참고 문서

- [2026-04-14-stage2-todo-checklist.md](./2026-04-14-stage2-todo-checklist.md)
- [2026-04-14-audit-reflection-strong-directive.md](./2026-04-14-audit-reflection-strong-directive.md)
- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)
- [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md)
