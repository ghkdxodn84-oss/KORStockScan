# 2026-04-22 Stage 2 To-Do Checklist

## 목적

- `same-symbol split-entry cooldown`(동일 종목 분할진입 재시도 제한)은 앞선 split-entry(분할진입) 축과 독립 관찰이 가능할 때만 D+2 canary 착수 후보로 본다.
- `AIPrompt 작업 11 HOLDING critical 전용 경량 프롬프트 분리` 미완료분이 있으면 오늘 보강 실행한다.
- 속도 개선축을 정확도 개선축 뒤에 무기한 두지 않는다.
- `HOLDING schema 변경(D+2)` 성과판정을 오늘 최종 수행한다.
- `프롬프트 프로파일별 특화` 잔여과제는 `shadow 없이`, 필요 시 `canary 1축`으로 가장 빠른 일정에 반영한다.

## 용어 범례

| 표현 | 한글 설명 | 현재 처리 |
| --- | --- | --- |
| `fallback_scout/main` | 탐색 주문과 본 주문이 함께 나가던 fallback 2-leg 분할진입 | 영구 폐기, canary 대상 아님 |
| `fallback_single` | 단일 fallback 진입 경로 | 영구 폐기, canary 대상 아님 |
| `latency fallback split-entry` | latency 상태가 나쁠 때 fallback으로 분할진입을 시도하던 경로 | 영구 폐기, bugfix와 분리 |
| `main-only` | 메인서버 실전 로그만 기준으로 보는 방식 | 오늘 판정 기준선 |
| `canary` | 작은 범위로 실전에 적용해 검증하는 1축 변경 | 하루 1축만 허용 |
| `shadow` | 실전 주문 없이 병렬 계산만 하던 검증 방식 | 신규/보완축에서는 금지 |

## 운영 규칙

- 작업일정은 모두 `YYYY-MM-DD KST`, `Slot`, `TimeWindow`로 고정한다. `후보비교 완료시`, `관찰 후` 같은 유예 표현은 쓰지 않는다.
- live 영향 관찰은 오전/오후 반나절을 넘기지 않는다. 반나절에 미관측이면 관찰축 오류, live 영향 없음, 또는 그대로 진행 가능 중 하나로 닫는다.
- 봇 재실행이 필요하고 권한/안전 조건이 맞으면 AI가 표준 wrapper로 직접 실행한다. 토큰/계정/운영 승인 경계가 있으면 실행하지 않고 필요한 1개 명령을 사용자에게 요청한다.
- 문서 변경 후 parser 검증은 AI가 수행한다. Project/Calendar 동기화는 토큰 보안 경계가 있으면 사용자 수동 실행 명령을 남긴다.

## 장전/장중 체크리스트 (08:00~12:20)

- [x] `[AIPrompt0422] 프로파일별 특화 프롬프트 잔여과제 범위 잠금(shared 의존 제거 포함)` (`Due: 2026-04-22`, `Slot: PREOPEN`, `TimeWindow: 08:00~08:10`, `Track: AIPrompt`) (`실행: 2026-04-22 07:27 KST`)
  - 판정 기준: `watching/holding/exit/shared` 중 잔여과제를 코드/로그/지표 기준으로 분해하고, `공통 프롬프트 재사용`과 `프로파일별 특화`를 구분해 문서에 잠근다.
  - 판정: 범위 잠금 완료. 실전 watching/holding 호출은 `prompt_profile="watching"` 및 `prompt_profile="holding"`로 분기되고, `exit` 액션 스키마(`HOLD/TRIM/EXIT`)도 지원된다. `shared`는 `SCALPING_PROMPT_SPLIT_ENABLED=false` 롤백, 기본값 호출, S15 fast-track/legacy sniper_analysis 보조 경로에 남은 공통 프롬프트 경로로 분리한다.
  - 근거: `AIEngine._resolve_scalping_prompt()`가 `watching/holding/exit/shared`를 모두 라우팅하고, `RuntimeAIRouter.analyze_target()`가 `prompt_profile`을 OpenAI/Gemini 양쪽으로 전달한다. `sniper_state_handlers`의 실전 감시/보유 호출은 각각 `watching`, `holding` 프로파일을 사용한다.
  - 잔여과제: `shared` 의존 제거는 보조 경로의 호출부 정리와 OpenAI v2의 task_type 기반 공통 프롬프트 의존 축소다. 오늘 장전에는 행동 canary가 아니라 후속 코드정리 후보로 잠근다.
- [x] `[AIPrompt0422] shadow 금지 고정 + canary 필요조건 정의` (`Due: 2026-04-22`, `Slot: PREOPEN`, `TimeWindow: 08:10~08:20`, `Track: Plan`) (`실행: 2026-04-22 07:27 KST`)
  - 판정 기준: 신규 프롬프트 실험은 shadow를 열지 않고 `canary 1축`으로만 진행한다. canary 조건은 `N_min`, `reject_rate`, `latency_p95`, `partial_fill_ratio`, `buy_drought_persist`를 명시한다.
  - 판정: 고정. 신규/보완 프롬프트 실험은 shadow 금지이며, 같은 날 `main-only buy_recovery_canary`와 병행하는 두 번째 행동 canary는 열지 않는다.
  - canary 필요조건: `N_min`은 판정 시점 `trade_count >= 50` 또는 `submitted_orders >= 20` 미달 시 hard pass/fail 금지, `reject_rate`는 `normal_only` baseline 대비 `+15.0%p` 이상 증가 시 OFF, `latency_p95`는 `gatekeeper_eval_ms_p95 > 15,900ms` 및 샘플 `>=50`이면 OFF, `partial_fill_ratio`는 baseline 대비 `+10.0%p` 이상 증가 시 경고이며 `loss_cap` 또는 `soft_stop_count/completed_trades >= 35.0%` 동반 시 OFF, `buy_drought_persist`는 canary 후에도 `ai_confirmed_buy_count`가 최근 main baseline 하위 3분위수보다 낮고 `blocked_ai_score_share`가 개선되지 않으면 OFF다.
  - 금지: `AI_WATCHING_75_PROMPT_SHADOW_ENABLED` 재개, dual-persona shadow 재개, counterfactual 손익 합산을 금지한다.
- [x] `[AIPrompt0422] 프로파일별 특화 프롬프트 1축 canary 적용 여부 결정` (`Due: 2026-04-22`, `Slot: PREOPEN`, `TimeWindow: 08:20~08:30`, `Track: AIPrompt`) (`실행: 2026-04-22 07:27 KST`)
  - 판정 기준: `shared` 의존 제거를 포함한 후보 중 1축만 선택해 ON/OFF를 결정하고, 미착수 시 보류 사유와 재시각을 남긴다.
  - 판정: 장전 즉시 착수는 하지 않는다. 오늘 장전에는 기존 `main-only buy_recovery_canary` 1축만 유지하고, 프로파일별 특화 프롬프트 신규 canary는 `12:20~12:30 KST`에 착수/미착수 중 하나로 최종판정한다.
  - 근거: 04-21 최신 preflight에서 `submitted_candidates=0`, `latency_block_candidates=40`, `latency_block_reason_breakdown=latency_state_danger 33 / latency_fallback_disabled 7`로 제출 병목이 먼저 확인됐다. 프로파일 특화 변경을 동시에 열면 `WAIT65~79 -> recheck -> submitted` 원인 귀속이 깨진다.
  - 정정: 이 항목은 장전 시점 `보류 확정`이 아니라 `12:20 KST 최종 go/no-go 대기`다. 오전 반나절(`09:00~12:00`) 관찰만 허용하고, `12:20~12:30`에 반드시 `watching 특화`, `holding 특화`, `exit 특화`, `shared 제거` 중 1축 착수 또는 미착수를 확정한다.
  - 다음 액션: `12:00~12:20` 스냅샷에서 `ai_prompt_type`, `action_schema`, `ai_confirmed->submitted`, `full/partial` 분리 집계를 잠근 뒤, `12:20~12:30`에 프로파일별 특화 프롬프트 1축 canary go/no-go를 닫는다.
- [x] `[LatencyPreflight0422] WAIT65~79 recheck/submitted 관측 경로 사전확인` (`Due: 2026-04-22`, `Slot: PREOPEN`, `TimeWindow: 08:30~08:40`, `Track: AIPrompt`) (`실행: 2026-04-22 07:27 KST`)
  - Source: [2026-04-21-auditor-performance-result-report.md](/home/ubuntu/KORStockScan/docs/2026-04-21-auditor-performance-result-report.md)
  - 판정 기준: `wait6579_ev_cohort.preflight`에서 `behavior_change=none`, `observability_passed=true`, `recovery_check_candidates`, `recovery_promoted_candidates`, `probe_applied_candidates`, `budget_pass_candidates`, `latency_block_candidates`, `submitted_candidates`, `submission_blocker_breakdown`이 모두 산출되는지 확인한다. 장전에는 latency/AI threshold 파라미터를 추가 완화하지 않는다.
  - 감사인 응답 반영: `latency_block_reason_breakdown`에서 `latency_state_danger`와 `latency_fallback_disabled`를 분리 확인한다. 특히 `latency_fallback_disabled=7` 경로가 구조적 버그인지 먼저 판정하고, bugfix가 아니면 `[AIPrompt0422]` 1차 판정 전 행동 canary를 추가로 열지 않는다.
  - 판정: 관측 경로 통과, 행동 변경 없음. `2026-04-22` 파일은 장전 시점에 아직 없어 `total_candidates=0`이지만, 최신 실측 파일 `2026-04-21` 재실행 결과 preflight 필드는 모두 산출됐다.
  - 최신 실측값: `total_candidates=54`, `recovery_check_candidates=8`, `recovery_promoted_candidates=0`, `probe_applied_candidates=0`, `budget_pass_candidates=40`, `latency_pass_candidates=0`, `latency_block_candidates=40`, `submitted_candidates=0`, `submission_blocker_breakdown=latency_block 40 / no_budget_pass 14`, `latency_block_reason_breakdown=latency_state_danger 33 / latency_fallback_disabled 7`, `observability_passed=true`, `behavior_change=none`.
  - 구조적 버그 판정: `latency_fallback_disabled=7`은 `SCALP_LATENCY_FALLBACK_ENABLED=false` 상태에서 CAUTION/fallback 경로를 차단하는 정책 경로로 확인했다. 코드상 `EntryPolicy.evaluate()`와 `sniper_entry_latency` 모두 동일 reason을 반환하므로 장전 bugfix 대상이 아니다.
  - 다음 액션: threshold/latency 파라미터 추가 완화 금지. 12:00 이후 첫 스냅샷에서 `WAIT65~79 -> recheck -> submitted -> full/partial` 연결 여부를 재판정한다.
- [ ] `[AIPrompt0422] 프로파일별 특화 프롬프트 canary 1차 계량 잠금` (`Due: 2026-04-22`, `Slot: INTRADAY`, `TimeWindow: 12:00~12:20`, `Track: AIPrompt`)
  - 판정 기준: `ai_confirmed_buy_count/share`, `WAIT 65/70/75~79`, `blocked_ai_score`, `ai_confirmed->submitted`, `full/partial` 분리, `COMPLETED+valid profit_rate`를 main-only로 잠근다.
- [ ] `[AIPrompt0422] 프로파일별 특화 프롬프트 1축 canary go/no-go 최종판정` (`Due: 2026-04-22`, `Slot: INTRADAY`, `TimeWindow: 12:20~12:30`, `Track: AIPrompt`)
  - 판정 기준: `12:00~12:20` 고정 스냅샷으로 `watching 특화`, `holding 특화`, `exit 특화`, `shared 제거` 중 기대값 개선 1축만 선택하거나 전부 미착수 처리한다. `후보비교 완료시` 같은 유예 문구는 금지한다.
  - 선택 우선순위: `watching`은 `WAIT65~79` 및 `ai_confirmed->submitted` 병목 개선 증거가 있을 때만, `holding/exit`은 오전 중 실제 보유/청산 AI 표본과 `GOOD_EXIT/capture_efficiency` 연결 필드가 있을 때만, `shared 제거`는 오전 중 실전 주문/보유/청산 의사결정에 `ai_prompt_type=scalping_shared`가 관측될 때만 live canary 후보로 본다.
  - 미관측 규칙: 오전 반나절(`09:00~12:00`)에 해당 후보가 관측되지 않으면 관찰축 정의가 잘못됐거나 live 영향이 없는 것으로 판정한다. 이 경우 canary로 열지 않고, 코드정리 또는 현행 유지로 닫는다.
- [ ] `[AIPrompt0422] shared 의존 제거 오전 관찰 종료판정` (`Due: 2026-04-22`, `Slot: INTRADAY`, `TimeWindow: 12:20~12:30`, `Track: AIPrompt`)
  - 판정 기준: `09:00~12:00` 실전 로그에서 `ai_prompt_type=scalping_shared`가 주문 제출, latency/budget gate, holding review, exit decision 중 어디에 연결됐는지 확인한다.
  - 실행 규칙: 관측되면 `shared 제거`를 live canary 후보로 올리되 같은 날 다른 행동 canary와 병행하지 않는다. 관측되지 않으면 `shared 제거`는 매매 영향 canary가 아니라 기본값/legacy 호출부 코드정리로 진행하고, live canary 미착수로 닫는다.
  - 시간 제한: 오전 반나절 이후 추가 관찰 유예 금지. `12:30 KST`까지 `live canary 후보`, `코드정리`, `현행 유지` 중 하나로 닫는다.
- [ ] `[AIPrompt0422] Gemini BUY recovery canary 1일차 판정` (`Due: 2026-04-22`, `Slot: INTRADAY`, `TimeWindow: 12:00~12:20`, `Track: AIPrompt`)
  - Source: [2026-04-21-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-21-stage2-todo-checklist.md)
  - 판정 기준: 04-22 오전 구간까지만 수집하고 `12:00` 이후 생성된 스냅샷을 고정 시점으로 사용한다. `ai_confirmed_buy_count/share`, `WAIT 65/70/75~79`, `blocked_ai_score`, `ai_confirmed->submitted`, `missed_winner_rate`, full/partial fill을 main-only로 판정한다.

## 장후 체크리스트 (15:30~)

- [x] `[AuditFix0422] same-symbol split-entry cooldown canary 1일차 착수 또는 보류 기록` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 15:30~15:40`, `Track: ScalpingLogic`) (`폐기: 2026-04-21 Plan Rebase 기준`)
  - 판정 기준: `rebase/즉시 재평가` 관찰축과 원인귀속이 분리될 때만 착수, 아니면 보류 사유와 재시각 기록
  - 선행 메모 (`2026-04-20 PREOPEN`): `D+2 이관 확정`. `rebase/즉시 재평가`와 독립 관찰 가능할 때만 착수
  - 폐기 사유: `fallback_scout/main`(탐색/본 주문 동시 fallback), `fallback_single`(단일 fallback), `latency fallback split-entry`(지연 상태 fallback 분할진입)는 영구 폐기되어 canary 착수/보류 판정 대상이 아니다.
- [ ] `[HoldingCtx0422] 보유 AI position_context 입력 1축 설계` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 15:40~15:50`, `Track: AIPrompt`)
  - Source: [workorder-0421-tuning-plan-rebase.md](/home/ubuntu/KORStockScan/docs/workorder-0421-tuning-plan-rebase.md)
  - 판정 기준: 더 빠른 `holding_exit` 축에서 `profit_rate`, `peak_profit`, `drawdown_from_peak`, `held_sec`, `buy_price`, `position_size_ratio`, `position_tag`를 Gemini 보유 프롬프트 입력으로 직접 전달하는 `position_context` 스키마를 확정한다.
  - 실행 메모: 운영 비교표에는 `schema 변경 효과`, `경량 프롬프트 효과`, `position_context 입력 효과`를 별도 컬럼으로 남긴다. 04-22에는 live 완화/추가진입과 묶지 않고 설계/테스트/로그 필드 고정까지만 1축으로 처리한다.
  - 검증 원칙: shadow/counterfactual 검증은 금지한다. 실전 검증은 별도 `holding_exit position_context canary` 1축으로만 열고, 같은 날 다른 보유/청산 완화축과 병행하지 않는다.
  - rollback guard: canary 적용 전 `N_min`, `loss_cap`, `missed_upside_rate`, `GOOD_EXIT`, `capture_efficiency`, `forced_exit/early_exit` 기준을 문서와 로그에 고정한다. 표본 미달이면 hard pass/fail 없이 방향성 판정으로만 남긴다.
- [ ] `[AuditFix0422] HOLDING 성과 최종판정(missed_upside_rate/capture_efficiency/GOOD_EXIT)` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 15:50~16:00`, `Track: AIPrompt`)
- [ ] `[HolidayCarry0419] AIPrompt 작업 10 HOLDING hybrid 적용` 확대 여부 최종판정 (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:10`, `Track: AIPrompt`)
  - 판정 기준: `missed_upside_rate/capture_efficiency/GOOD_EXIT`와 `holding_action_applied/holding_force_exit_triggered` 운영 로그가 모두 확보됐을 때만 확대 여부 결정
- [ ] `[AuditFix0422] HOLDING 지표 우선순위(primary/secondary) 고정 기록` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 16:10~16:20`, `Track: Plan`)
- [ ] `[PlanSync0422] AI 엔진 A/B 원격 preflight 체크리스트 항목 확정` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 16:20~16:30`, `Track: AIPrompt`)
  - 판정 기준: `2026-04-23 POSTCLOSE 15:35~15:50`에 수행할 원격 정합화 범위(설정값/관찰축/롤백가드)와 `2026-04-24 15:50~16:00` 착수 여부 판정 게이트를 문서 고정
- [ ] `[PlanRebase0422] buy_recovery_canary 1일차 종합판정 + 다음 액션 고정` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~17:00`, `Track: ScalpingLogic`)
  - Source: [audit-reports/2026-04-22-plan-rebase-central-audit-review.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-22-plan-rebase-central-audit-review.md)
  - 판정 기준: `12:00~12:20` 계량 결과와 장중 추가 표본을 합쳐 `buy_drought_persist`, `recovery_false_positive_rate`, `loss_cap`, `reject_rate`, `latency_p95`, `partial_fill_ratio`, `fallback_regression`을 대조한다.
  - 다음 액션: `유지`, `OFF+재시작`, `score/prompt 재교정`, `entry_filter_quality`로 전환 준비 중 하나를 `2026-04-22 17:00 KST`까지 확정한다.
- [ ] `[Governance0422] GPT 엔진 금지패턴 및 AI 생성 코드 체크게이트 문서 재확인` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:20`, `Track: AIPrompt`)
  - Source: [2026-04-22-ai-generated-code-governance.md](/home/ubuntu/KORStockScan/docs/2026-04-22-ai-generated-code-governance.md)
  - 판정 기준: `fallback_scout/main`(탐색/본 주문 동시 fallback) 동시 다중 leg 금지, 의도-구현 일치, 단위테스트, 운영자 수동승인, `ai_generated/design_reviewed` 라벨링, rollback guard가 실제 변경/운영 로그에서 위반되지 않았는지 확인한다.
- [x] `[VisibleResult0422] legacy shadow canary 1일차 결과 기반 live 승격/롤백 판정` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:40`, `Track: Plan`) (`폐기: 2026-04-21 Plan Rebase 기준`)
  - 판정 기준: `승격 1축` 또는 `롤백` 중 하나로 강제 종료하고, shadow 복귀는 금지
- [x] `[PlanSync0422] legacy shadow 잔여항목 0화 확인(미전환 shadow 없음)` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 16:40~16:50`, `Track: Plan`) (`폐기: 2026-04-21 Plan Rebase 기준`)
  - 판정 기준: 남은 shadow 항목이 있으면 `폐기` 또는 `기존 live 축 병합`으로 닫고 독립 shadow 상태를 남기지 않는다
  - 폐기 사유: 신규/보완축은 `shadow 금지`, `canary-only` 원칙으로 통일했다. 잔여 shadow 확인은 Plan Rebase 문서 정리로 흡수한다.
- [x] `[DataArch0422] 튜닝 모니터링 로그 저장구조 전환 작업지시서 확정 + Gemini 착수` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 16:50~17:00`, `Track: Plan`) (`실행: 2026-04-21 07:48 KST`)
  - Source: [workorder-gemini-tuning-monitoring-log-architecture-refactor.md](/home/ubuntu/KORStockScan/docs/archive/legacy-workorders/workorder-gemini-tuning-monitoring-log-architecture-refactor.md)
  - 판정 기준: `원본 jsonl 보관 + 분석 parquet/DuckDB + PostgreSQL 메타데이터` 3계층과 `shadow-only -> canary 1축` 순서를 문서 기준으로 고정한다.
  - 선행 완료: 개선작업 결과서 기준 완료 승인 가능 상태.
- [x] `[DataArch0422] DuckDB/Parquet 의존성 승인 여부 및 대안경로 확정` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:10`, `Track: Plan`) (`실행: 2026-04-21 07:48 KST`)
  - 판정 기준: 사용자 승인 전에는 패키지 설치를 진행하지 않고, 승인 실패 시 `JSONL+SQLite 임시분석` 대안 경로와 재판정 시각을 기록한다.
  - 선행 완료: 기존 `.venv` 의존성으로 처리, 신규 패키지 설치 없음.
- [x] `[DataArch0422] jsonl vs parquet shadow 집계 일치성 검증(거래수/퍼널/blocker/체결품질)` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 17:10~17:30`, `Track: Plan`) (`실행: 2026-04-21 07:44 KST`)
  - 판정 기준: 정수 집계 오차 0, `full/partial` 분리 유지, `COMPLETED + valid profit_rate` 규칙 위반 0건일 때만 다음 축 전환 검토
  - 선행 완료: `compare_tuning_shadow_diff --start 2026-04-01 --end 2026-04-20` 재실행 결과 `all_match=true`.
- [x] `[DataArch0422] 분석랩 2종(gemini/claude) 데이터 소스 우선순위 전환 및 shadow diff 기록` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 17:30~17:50`, `Track: Plan`) (`실행: 2026-04-21 07:48 KST`)
  - Source: [workorder-gemini-tuning-monitoring-log-architecture-refactor.md](/home/ubuntu/KORStockScan/docs/archive/legacy-workorders/workorder-gemini-tuning-monitoring-log-architecture-refactor.md)
  - 판정 기준: 두 분석랩의 `trade/funnel/sequence` 정수 집계 오차 0, `run_manifest`의 `data_source_mode` 기록, fallback 발생 시 사유+재실행시각 고정
  - 선행 완료: Gemini/Claude `run_manifest`에 `data_source_mode=duckdb_primary`, `history_coverage_ok=true` 기록.
- [x] `[DataArch0422] 과거 전체 누적 데이터 parquet/DuckDB 커버리지 검증` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 17:50~18:10`, `Track: Plan`) (`실행: 2026-04-21 07:44 KST`)
  - 판정 기준: `history_start~yesterday` 누락일 0건, DuckDB 기준 리포트/분석랩 실행 성공, `history_coverage_ok=true` 증적 기록
  - 선행 완료: `coverage_summary.json` 기준 `missing_in_parquet=[]`, DuckDB 직접 조회 `pipeline_events=2,857,648 rows`.
- [x] `[DataArch0422] legacy DB raw 테이블 제거 및 운영혼선 차단 확인` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 18:10~18:30`, `Track: Plan`) (`실행: 2026-04-21 07:48 KST`)
  - Source: [workorder-gemini-tuning-monitoring-log-architecture-refactor.md](/home/ubuntu/KORStockScan/docs/archive/legacy-workorders/workorder-gemini-tuning-monitoring-log-architecture-refactor.md)
  - 판정 기준: `dashboard_pipeline_events/dashboard_monitor_snapshots` 등 제거 대상 drop 완료, 메타 테이블만 유지, 제거 후 리포트 정상 동작 확인
  - 선행 완료: legacy raw 테이블 dry-run 기준 존재하지 않음. `KORSTOCKSCAN_ENABLE_LEGACY_DASHBOARD_DB` opt-in 없이는 재생성/쓰기 차단.
- [x] `[DataArch0422] 중복/불필요 cron 정리` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 18:20~18:30`, `Track: Plan`) (`실행: 2026-04-21 07:52 KST`)
  - 판정 기준: `TUNING_MONITORING_POSTCLOSE`와 중복되는 금요일 분석랩 cron 제거, 오래된 1회성 주석/중복 주석 정리, 유지 대상 운영 cron 확인
  - 선행 완료: `PATTERN_LAB_CLAUDE_FRI_POSTCLOSE`, `PATTERN_LAB_GEMINI_FRI_POSTCLOSE` 제거 및 `deploy/install_pattern_lab_cron.sh` cleanup shim 전환.
- [ ] `[DataArch0422] TUNING_MONITORING_POSTCLOSE 첫 자동실행 결과 확인` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 18:30~18:40`, `Track: Plan`)
  - Source: [workorder-gemini-tuning-monitoring-log-architecture-refactor-result.md](/home/ubuntu/KORStockScan/docs/archive/legacy-workorders/workorder-gemini-tuning-monitoring-log-architecture-refactor-result.md)
  - 판정 기준: `logs/tuning_monitoring_postclose_cron.log`에서 증분 parquet 생성, shadow diff `all_match=true`, Gemini/Claude `history_coverage_ok=true` 확인
  - 2026-04-21 사전 확인: `18:05 KST` cron 실행은 `pipeline_events` parquet 생성 중 OOM kill로 실패했다. `build_tuning_monitoring_parquet`를 원본 이벤트 즉시 축소 row 변환 방식으로 보수한 뒤 `19:23~19:26 KST` 수동 재실행 성공.
  - 2026-04-21 수동 복구 증적: `pipeline_events_20260421.parquet=421,220 rows`, `post_sell_20260421.parquet=9 rows`, `system_metric_samples_20260421.parquet=802 rows`, `shadow_diff all_match=true`, Gemini/Claude `history_coverage_ok=true`.
  - 2026-04-22 항목은 유지한다. 사유: 오늘은 수동 복구 성공이고, `TUNING_MONITORING_POSTCLOSE`의 첫 정상 자동실행 여부는 2026-04-22 장후 cron 로그로 별도 확인해야 한다.
- [ ] `[DataArch0422] monitor snapshot raw 압축/보존 정책 재판정` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 18:40~18:50`, `Track: Plan`)
  - Source: [workorder-gemini-tuning-monitoring-log-architecture-refactor-result.md](/home/ubuntu/KORStockScan/docs/archive/legacy-workorders/workorder-gemini-tuning-monitoring-log-architecture-refactor-result.md)
  - 판정 기준: `dashboard_db_archive` snapshot `skipped_unverified`를 허용 상태로 둘지, parquet/manifest 검증 기반 압축으로 전환할지 결정
- [ ] 미완료 시 `사유 + 다음 실행시각` 기록

## 참고 문서

- [2026-04-21-stage2-todo-checklist.md](./2026-04-21-stage2-todo-checklist.md)
- [2026-04-19-aiprompt-task8-task10-holiday-recheck.md](./archive/legacy-tuning-2026-04-06-to-2026-04-20/2026-04-19-aiprompt-task8-task10-holiday-recheck.md)
- [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md)
- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)
- [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md)
- [plan-korStockScanPerformanceOptimization.performance-report.md](./plan-korStockScanPerformanceOptimization.performance-report.md)
- [workorder-gemini-tuning-monitoring-log-architecture-refactor.md](./archive/legacy-workorders/workorder-gemini-tuning-monitoring-log-architecture-refactor.md)
