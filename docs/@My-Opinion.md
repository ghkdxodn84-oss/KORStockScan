1) 진입기회 확대 관련 튜닝 포인트 (4월22일 오전까지 확인)
  - WAIT 65~79 전용 EV 코호트를 별도로 고정 수집: buy_pressure, tick_accel, micro_vwap_bp, latency_state, parse_ok, ai_response_ms, terminal blocker까지 한 행으로 저장.
  - WAIT 65~79에 대해 paper-fill(가상체결) 시뮬레이션 추가: 예상 체결률/예상 EV를 같이 산출해서 “들어갔으면 실제로 체결됐는지”를 추정.
  - 소량 실전 probe canary(아주 작은 예산)로 체결품질 표본 확보: full/partial 분리로 최소 N 확보 후에만 임계값 하향 승인.

2) Gemini 경로 OpenAI v2 프로파일/액션 스키마 이식 (완료)
  - prompt_profile 분기: `watching/holding/exit/shared` 전부 지원.
  - 액션 스키마: 진입은 `BUY|WAIT|DROP`, 보유/청산은 `HOLD|TRIM|EXIT`(action_v2)로 분리.
  - 호환 레이어: 기존 핸들러용 `action`도 동시 제공(`HOLD->WAIT`, `TRIM->SELL`, `EXIT->DROP`).
  - 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_ai_engine_cache.py src/tests/test_scalping_feature_packet.py src/tests/test_wait6579_ev_cohort_report.py src/tests/test_log_archive_service.py src/tests/test_ai_engine_openai_v2_audit_fields.py` 결과 `26 passed, 1 warning`.
  - 2026-04-22 PREOPEN 판정: 프로파일별 특화 프롬프트 신규 canary는 미착수. `main-only buy_recovery_canary` 1축 유지 중이라 동시 행동 canary를 열지 않는다.
  - shared 잔여범위: `SCALPING_PROMPT_SPLIT_ENABLED=false` 롤백 경로, 기본값 호출, S15 fast-track/legacy sniper_analysis 보조 경로, OpenAI v2 task_type 기반 공통 프롬프트 경로를 후속 코드정리 후보로 잠근다.
  - canary 조건: 신규 프롬프트 canary를 열 경우 `N_min`, `reject_rate +15.0%p`, `latency_p95 15,900ms`, `partial_fill_ratio +10.0%p 복합 경고`, `buy_drought_persist`, `recovery_false_positive_rate`를 rollback guard로 둔다.
  - 2026-04-22 INTRADAY 확정시각: `12:20~12:30 KST`. 이 시간에 `watching 특화`, `holding 특화`, `exit 특화`, `shared 제거` 중 1축 canary 착수 또는 전부 미착수를 확정한다.
  - 오전 반나절 제한: `09:00~12:00`에 관측되지 않은 후보는 추가 관찰로 넘기지 않는다. 관측되지 않으면 관찰축 정의 오류 또는 live 영향 없음으로 판정하고, `코드정리` 또는 `현행 유지`로 닫는다.
  - shared 제거 판정: 오전 중 `ai_prompt_type=scalping_shared`가 주문 제출/보유/청산 의사결정에 연결되면 live canary 후보, 관측되지 않으면 매매 영향 canary가 아니라 기본값/legacy 호출부 정리 후보로 처리한다.

# 스캘핑 진입/보유/청산 다단계 판정표 (초안)

작성일: `2026-04-21`  
기준: `main-only baseline`, `Gemini route`, `buy_recovery_canary 분리 운영`

## 1) 다단계 경로 판정표

| 1단계 구간 | 2단계 경로 | 3단계(세부) | 다음 단계로 넘어가는 조건 | Drop/보류 조건 | 현재 문제/병목 | 수집 중인 항목 | 해결 가설(실행중/후보) | 기대효과 | Canary 일정 | 판정 일정 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 진입 | A. 정상 진입(`ALLOW_NORMAL`) | A1. Gatekeeper 통과 → A2. AI 판정(BUY) → A3. 주문 제출 | `latency_state != DANGER`, 유동성/예산 통과, AI score 기준 통과 | `latency_state=DANGER`, 예산/유동성 미달, AI score 미달 | **latency miss 비중 과다**(오전 84.3%) | `latency_state`, `gatekeeper_eval_ms_p95`, `gatekeeper_fast_reuse_ratio`, blocker 4축 분포 | 가설A-1: gatekeeper fast signature 재사용률 저하가 latency miss를 키운다. 가설A-2: `entry_filter_quality` 적용 전에는 latency 축 단독 보정이 기대값 회복에 더 직접적이다. | 미진입 기회비용 축소, BUY→제출 전환률 개선 | `2026-04-22 PREOPEN 08:00~08:10` (`buy_recovery_canary` 유지) | `2026-04-22 INTRADAY 12:00~12:20` (12:00 이후 첫 스냅샷 고정) |
| 진입 | B. WAIT65~79 재평가(`buy_recovery_canary`) | B1. 후보 포착 → B2. 2차 Gemini 재평가 → B3. score>=75면 승격 | `buy_pressure>=65`, `tick_accel>=1.20`, `micro_vwap_bp>=0`, `large_sell_print=false`, `latency!=DANGER` | 위 5개 중 하나라도 불충족, 2차 score<75 | **BUY drought**(WAIT 구간 과밀, BUY 전환 저조) | `wait65_79_ev_candidate`, `buy_pressure`, `tick_accel`, `micro_vwap_bp`, `parse_ok`, `ai_response_ms`, terminal blocker | 가설B-1: Gemini 라우팅 전환 시 입력 피처 누락/축소가 WAIT 과밀을 유발했다. 가설B-2: OpenAI v2 parity 피처 복구 후 WAIT65~79의 BUY 승격률과 제출률이 회복된다. 가설B-3: recovery는 `entry_filter_quality`와 분리 운용해야 원인 귀속이 가능하다. | 진입기회 회복, 코호트 표본 확대, 임계값 조정 가능성 확보 | `2026-04-22 PREOPEN 08:00~08:10` (이미 조기적용 상태 재확인) | `2026-04-22 INTRADAY 12:00~12:20` |
| 진입 | B-preflight. WAIT65~79 관측 경로 | B0. preflight 필드 산출 → B1. blocker 분리 → B2. 행동 변경 금지/허용 판정 | `behavior_change=none`, `observability_passed=true`, blocker breakdown 산출 | 04-22 장전 파일 없음, `submitted_candidates=0`, latency blocker 미분리 | 04-21 최신 실측 기준 제출 병목이 threshold가 아니라 latency/budget 후단에 있음 | `recovery_check_candidates=8`, `budget_pass_candidates=40`, `latency_block_candidates=40`, `submitted_candidates=0`, `latency_state_danger=33`, `latency_fallback_disabled=7` | `latency_fallback_disabled`는 fallback 폐기 정책 경로이며 bugfix 대상이 아니다. 12시 전 행동 canary 추가 금지. | 불필요한 threshold 완화 방지, `recheck -> submitted` 연결성 원인귀속 유지 | `2026-04-22 PREOPEN 08:30~08:40` (완료) | `2026-04-22 INTRADAY 12:00~12:20` |
| 진입 | C. Probe canary(소량 실전) | C1. BUY 승격 건 중 소량 주문 적용 → C2. 체결품질 측정 | `wait6579 promoted=true`, 소량 예산/수량 범위 내 | 예산 초과, 주문 품질 악화, rollback guard 위반 | 실체결 품질 표본 부족(가상체결 대비 오차 확인 필요) | `wait6579_probe_canary_applied`, 제출/체결 수량, fill split(FULL/PARTIAL/NONE), 기대EV 대비 실제 | 가상체결+소량 실전 병행으로 fill quality 바이어스 축소 | "들어갔으면 체결됐나?"의 실증 정확도 개선 | `2026-04-22 INTRADAY 09:00~11:30` (운영 중 수집) | `2026-04-22 INTRADAY 12:00~12:20` |
| 보유 | H. 보유 유지/이탈 판단 | H1. AI holding review → H2. stop/exit 조건 비교 | 보유 중 AI score/수익률/보유시간이 유지 조건 만족 | soft/hard stop, 시간초과, 리스크 규칙 트리거 | partial fill 표본에서 성과 악화 방향성 | `profit_rate`, `peak_profit`, `held_sec`, `soft_stop_count`, `capture_efficiency` | 보유축은 즉시 완화보다 데이터 확보 후 규칙 재설계(`entry_filter_quality` 이후) | 불필요 조기청산/지연청산 동시 감소 | `2026-04-22 POSTCLOSE 16:30~17:00` (`position_addition_policy` 초안과 연계) | `2026-04-22 POSTCLOSE 17:00~17:20` (후순위 1차 판정) |
| 청산 | E. 청산 경로 | E1. soft/hard stop → E2. trailing/preset/AI early exit → E3. EOD/NXT | 청산 트리거 발생 시 경로별 룰 충족 | 주문 실패, 규칙 충돌, NXT 미분리로 판정 모호 | EOD/NXT 경로가 단일판정에 가까워 해석력 부족 | `exit_rule`, `sell_order_status`, `sell_fail_reason`, `is_nxt`, `hold_sec` | EOD/NXT 분리 태깅 후 경로별 성과 비교 | 청산 원인별 개선점 명확화, 롤백 판단 정확도 개선 | `2026-04-22 POSTCLOSE 16:30~17:00` (태깅 설계 점검) | `2026-04-22 POSTCLOSE 17:20~17:40` (워크오더 최종판정 연계) |

## 2) 경로별 핵심 판정 규칙(요약)

1. 진입은 `정상 진입`과 `WAIT65~79 회복 경로`를 분리 판정한다.
2. `entry_filter_quality`(정식 튜닝축)와 `buy_recovery_canary`(긴급 회복축)는 혼용하지 않는다.
3. 임계값 하향은 `full/partial 분리 최소 N` 통과 후에만 허용한다.
4. 손익 판정은 `COMPLETED + valid profit_rate`만 사용한다.
5. 병목 판정 순서는 `퍼널 -> blocker 4축 -> 체결품질 -> 보유/청산 -> 손익` 순서를 유지한다.

## 3) 범례(약어/전문용어)

- `EV`: 기대값(Expected Value). 기대 수익 방향과 크기를 뜻함.
- `BUY drought`: AI가 BUY로 잘 안 넘어가는 현상.
- `WAIT65~79`: AI 점수가 65~79 구간에 머무는 후보군.
- `Gatekeeper`: 진입 전 지연/예산/유동성 등 사전 검증 단계.
- `fallback_scout/main`: 탐색 주문과 본 주문이 함께 나가던 fallback 2-leg 분할진입. 현재 영구 폐기.
- `fallback_single`: 단일 fallback 진입 경로. 현재 영구 폐기.
- `latency fallback split-entry`: latency 상태가 나쁠 때 fallback으로 분할진입을 시도하던 경로. 현재 영구 폐기.
- `main-only`: `songstock`/remote 비교 없이 메인서버 실전 로그만 보는 기준.
- `normal_only`: fallback 태그와 예외 진입이 섞이지 않은 정상 진입 표본.
- `p95`: 상위 95% 지점(지연시간 꼬리 구간 대표치).
- `FULL/PARTIAL/NONE`: 전량체결/부분체결/미체결.
- `Probe canary`: 소액으로 실전 표본만 수집하는 안전형 canary.
- `N gate`: 표본 수 최소 기준 통과 여부(통과 전 hard pass/fail 금지).

## 4) 자동 파싱용 작업항목(초안)

- [ ] `[ScalpingMap0422] 다단계 경로판정표 v1 잠금` (`Due: 2026-04-22`, `Slot: PREOPEN`, `TimeWindow: 08:00~08:10`, `Track: Plan`)
  - 판정 기준: 본 문서의 경로/조건/드롭 기준이 코드/로그 필드와 1:1로 연결되는지 확인한다.
- [ ] `[AIPrompt0422] BUY recovery canary 오전 수집 + 12시 이후 판정고정` (`Due: 2026-04-22`, `Slot: INTRADAY`, `TimeWindow: 12:00~12:20`, `Track: AIPrompt`)
  - 판정 기준: 오전 수집 종료 후 `12:00` 이후 첫 스냅샷 기준으로 유지/롤백/재교정을 확정한다.
- [ ] `[AIPrompt0422] 프로파일별 특화 프롬프트 1축 canary go/no-go 최종판정` (`Due: 2026-04-22`, `Slot: INTRADAY`, `TimeWindow: 12:20~12:30`, `Track: AIPrompt`)
  - 판정 기준: `09:00~12:00` 오전 반나절 관찰과 `12:00~12:20` 스냅샷으로 `watching/holding/exit/shared 제거` 중 1축만 선택하거나 전부 미착수로 닫는다.
- [ ] `[AIPrompt0422] shared 의존 제거 오전 관찰 종료판정` (`Due: 2026-04-22`, `Slot: INTRADAY`, `TimeWindow: 12:20~12:30`, `Track: AIPrompt`)
  - 판정 기준: `ai_prompt_type=scalping_shared`가 주문 제출/보유/청산 의사결정에 연결되지 않으면 live canary 후보에서 제외하고 코드정리/현행유지로 닫는다.
- [ ] `[PlanRebase0422] 보유/청산 후순위 경로 재설계 1차` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~17:20`, `Track: ScalpingLogic`)
  - 판정 기준: 보유/청산 경로를 3단계 이상으로 분리하고 drop 이유가 로그 필드로 재현 가능해야 한다.
