# 2026-04-20 Stage 2 To-Do Checklist

## 목적

- `2026-04-17 최고손실일`에서 확보한 고밀도 표본으로 `split-entry leakage` 1일차 판정을 먼저 닫는다.
- `split-entry` 3개 서브축은 감사표 권고대로 같은 날 병렬 가동하지 않고 `rebase -> 즉시 재평가 -> cooldown` 순차 도입 원칙을 유지한다.
- `HOLDING action schema / HOLDING critical` shadow-only 착수를 같은 날 밀어 다음주 수익전환 축을 연다.
- `latency/tag/threshold` 추가 완화는 `quote_stale` 우세와 `split-entry` 누수 분리 전에는 승격하지 않는다.
- `2026-04-18~2026-04-19(휴일)` 이관 항목을 장후 슬롯에서 우선 처리한다.
- `AIPrompt 작업 11 HOLDING critical 전용 경량 프롬프트 분리`를 착수한다.
- 속도 개선축을 정확도 개선축 뒤에 다시 미루지 않는다.
- 금요일 급손실 완화 목적의 `SCALPING_MAX_BUY_BUDGET_KRW 1,600,000` 단일축 canary를 판정한다.

## 장전 체크리스트 (08:00~09:00)

- [x] `[VisibleResult0420] split-entry rebase 수량 정합성 shadow 1일차 판정` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:00~08:10`, `Track: ScalpingLogic`) (`실행: 2026-04-20 08:33 KST`)
  - 판정: `승인(단독 shadow 유지)`. `2026-04-20` split-entry 활성 축은 `rebase`만 유지하고, 즉시 재평가/쿨다운은 예정대로 뒤 날짜로 이관.
  - 근거: [2026-04-18-nextweek-validation-axis-table-audited.md](/home/ubuntu/KORStockScan/docs/2026-04-18-nextweek-validation-axis-table-audited.md) 권고대로 3축 동시가동 금지. 오늘 [performance_tuning_2026-04-20.json](/home/ubuntu/KORStockScan/data/report/monitor_snapshots/performance_tuning_2026-04-20.json) 기준 `position_rebased_after_fill_events=0`, `order_bundle_submitted_events=0`.
  - 다음 액션: 장후에는 `split_entry_rebase_integrity_shadow` 누적 결과와 `position_rebased_after_fill_events`를 다시 확인해 `2026-04-21` 승격/보류 기준선으로 사용.
- [x] `[AuditFollowup0418] remote runtime 코드 적재 상태 점검(작업9 반영분)` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:00~08:05`, `Track: AIPrompt`) (`실행: 2026-04-20 08:33 KST`)
  - 판정: `완료`. 원격 runtime 적재와 Gemini 경로 유지 확인.
  - 근거: `songstockscan`에서 `src/engine/scalping_feature_packet.py` 존재, `PYTHONPATH=. .venv/bin/python -c "import src.engine.ai_engine"` 성공, `bot_main.py` 기동 확인, `logs/runtime_ai_router_info.log`에 `role=remote scalping_openai=off` 기록.
  - 다음 액션: A/B preflight 전까지 runtime 차이를 추가로 열지 않고 원격은 Gemini 기준선 유지.
- [x] `[AuditFix0420] split-entry 즉시 재평가 shadow D+1 이관 확정` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:10~08:15`, `Track: ScalpingLogic`) (`실행: 2026-04-20 08:33 KST`)
  - 판정: `이관 확정`. 오늘은 미활성 유지, earliest start는 `2026-04-21 POSTCLOSE` 판정 이후.
  - 근거: [2026-04-18-nextweek-validation-axis-table-audited.md](/home/ubuntu/KORStockScan/docs/2026-04-18-nextweek-validation-axis-table-audited.md) 에서 D+1 이관 권고. [2026-04-17-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-17-stage2-todo-checklist.md) 에는 `partial_then_expand|multi_rebase`, `90초` 설계만 확정.
  - 다음 액션: `2026-04-21` 체크리스트에서 `false_entry_rate` 상한과 `N_min/Δ_min` 충족 시에만 shadow 착수.
- [x] `[AuditFix0420] same-symbol split-entry cooldown shadow D+2 이관 확정` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:15~08:20`, `Track: ScalpingLogic`) (`실행: 2026-04-20 08:33 KST`)
  - 판정: `이관 확정`. `D+2` 이후만 허용.
  - 근거: [2026-04-17-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-17-stage2-todo-checklist.md) 에서 `same_symbol_soft_stop_cooldown_shadow` 20분 후보 고정, [2026-04-18-nextweek-validation-axis-table-audited.md](/home/ubuntu/KORStockScan/docs/2026-04-18-nextweek-validation-axis-table-audited.md) 에서 D+2 권고.
  - 다음 액션: `2026-04-22` 체크리스트에서 `rebase/즉시 재평가`와 독립 관찰 가능 여부를 확인한 뒤 최종 착수 판정.
- [x] `[AuditFix0420] 각 판정행 N_min/Δ_min/PrimaryMetric 확정` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:20~08:30`, `Track: Plan`) (`실행: 2026-04-20 08:33 KST`)
  - 판정: `확정`. `N_min=50`, `Δ_min=+3.0%p`, `PrimaryMetric=budget_pass_to_submitted_rate`.
  - 근거: 오늘 [performance_tuning_2026-04-20.json](/home/ubuntu/KORStockScan/data/report/monitor_snapshots/performance_tuning_2026-04-20.json) `sections.judgment_gate` 값으로 고정.
  - 다음 액션: `2026-04-21` 판정에서 `n_current < 50`이면 무조건 승격 보류.
- [x] `[VisibleResult0420] latency canary bugfix-only 재판정 및 tag 완화 보류/승인` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:30~08:35`, `Track: ScalpingLogic`) (`실행: 2026-04-20 08:33 KST`)
  - 판정: `추가 완화 보류`. bugfix-only 유지, `tag/min_score` 완화는 미승인.
  - 근거: [2026-04-17-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-17-stage2-todo-checklist.md) 장중 재판정에서 추가 완화가 아직 이르다고 결론. 오늘 [server_comparison_2026-04-20.md](/home/ubuntu/KORStockScan/data/report/server_comparison/server_comparison_2026-04-20.md) 도 양 서버 활동이 대부분 `0`으로 새 승인 근거가 없음.
  - 다음 액션: 다음 재판정에서도 baseline 관측창은 `직전 5영업일 동일 시간대 p50/p95`를 유지하고, `quote_stale=False` 표본과 `latency_danger_reasons` 분포를 함께 누적.
- [x] `[AuditFix0420] 공통 rollback trigger 수치표 확정` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:35~08:45`, `Track: ScalpingLogic`) (`실행: 2026-04-20 08:33 KST`)
  - 판정: `확정`. `reject_rate<=70.0`, `partial_fill_ratio<=65.0`, `latency_p95<=5000ms`, `reentry_freq<=180.0`.
  - 근거: 오늘 [performance_tuning_2026-04-20.json](/home/ubuntu/KORStockScan/data/report/monitor_snapshots/performance_tuning_2026-04-20.json) `sections.judgment_gate.rollback_limits` 기준으로 고정. 현재 스냅샷 값은 모두 `0.0`.
  - 다음 액션: POSTCLOSE 재판정과 성과보고서에도 동일한 필드명으로 재사용.
- [x] `[RiskSize0420] SCALPING_MAX_BUY_BUDGET_KRW=1,600,000 적용 상태/기동 반영 확인` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:40~08:45`, `Track: ScalpingLogic`) (`실행: 2026-04-20 08:33 KST`)
  - 판정: `코드 반영 확인 / 기동 반영 재확인 필요`.
  - 근거: [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py:79) 에 `SCALPING_MAX_BUY_BUDGET_KRW: int = 1_600_000` 반영. 다만 오늘 PREOPEN 스냅샷에서는 거래/주문 표본이 없어 주문 경로 샘플은 아직 없음.
  - 다음 액션: `bot_main.py` 재기동 후 첫 신규 진입 표본에서 예산 캡과 주문 수량 경로를 확인.
- [x] `[VisibleResult0420] HOLDING action schema shadow-only 착수` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:45~09:00`, `Track: AIPrompt`) (`실행: 2026-04-20 08:33 KST`)
  - 판정: `승인(shadow-only)`. 성과판정은 `2026-04-22 POSTCLOSE`.
  - 근거: 오늘 [performance_tuning_2026-04-20.json](/home/ubuntu/KORStockScan/data/report/monitor_snapshots/performance_tuning_2026-04-20.json) `sections.holding_axis`에 `holding_action_applied`, `holding_force_exit_triggered`, `holding_override_rule_version_count`가 모두 잡히며 baseline 필드가 정렬됨. 현재 값은 전부 `0`으로 clean baseline 상태.
  - 다음 액션: `2026-04-20 POSTCLOSE`에는 baseline/관측 lock만 수행하고, 확대 여부는 `2026-04-22`까지 보류.
- [x] `[VisibleResult0420] live 승격 후보는 split-entry leakage 1축만 유지 확인` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: Plan`) (`실행: 2026-04-20 08:33 KST`)
  - 판정: `확정`. live 승격 후보는 계속 `split-entry leakage` 1축만 유지.
  - 근거: [2026-04-17-midterm-tuning-performance-report.md](/home/ubuntu/KORStockScan/docs/2026-04-17-midterm-tuning-performance-report.md) 와 현재 체크리스트 모두 다음 live 변경을 `split-entry leakage` 우선으로 고정. `HOLDING`은 shadow-only + D+2 판정 축.
  - 다음 액션: 다음 live 변경도 `split-entry leakage` 단일축 canary부터 시작.
- [x] `[OpsGuard0420] 장전 run_monitor_snapshot full build 보호가드 적용` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:45~08:55`, `Track: Plan`) (`실행: 2026-04-20 08:47 KST`)
  - 판정: `완료`. 장전 시간대 `bot_main` 동작 중 full build 차단 + 실행락 적용.
  - 근거: [run_monitor_snapshot_safe.sh](/home/ubuntu/KORStockScan/deploy/run_monitor_snapshot_safe.sh) 추가, [run_monitor_snapshot_cron.sh](/home/ubuntu/KORStockScan/deploy/run_monitor_snapshot_cron.sh) 연결 전환. 로그에 `[SKIP] PREOPEN full build blocked while bot_main is running` 확인.
  - 다음 액션: 긴급 강행이 필요할 때만 `ALLOW_PREOPEN_FULL_BUILD_WITH_BOT=1`로 단발 실행.

## 장후 체크리스트 (15:30~)

- [ ] `[VisibleResult0420] partial-only timeout shadow 1일차 판정` (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 15:30~15:40`, `Track: ScalpingLogic`)
  - 실행 메모: timeout 후 `Δt=5분` 내 동일 종목·호가 체결 여부 counterfactual을 함께 기록
- [ ] `[AuditFollowup0418] main runtime OPENAI 라우팅/감사필드 실표본 확인` (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 15:40~15:50`, `Track: AIPrompt`)
  - 실행 메모: `ai_confirmed/ai_holding_review`에서 `scalp_feature_packet_version + 4개 *_sent` 키를 확인
- [ ] `[AuditFollowup0418] main runtime OpenAI 모델 식별자 검증/수정` (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 15:50~16:00`, `Track: AIPrompt`)
  - 실행 메모: `gpt-5.4-nano` 유효성 확인 또는 교정
- [ ] `[AuditFollowup0418] 작업 6/7 보류 유지 또는 착수 전환 재판정` (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:10`, `Track: AIPrompt`)
  - 실행 메모: `HOLDING action schema shadow-only` 선행 범위와 충돌 여부를 기준으로 판정
- [ ] `[HolidayCarry0418] AIPrompt 작업 9 정량형 수급 피처 이식 1차` 실표본 기준 1차 결과/확대 여부 판정 (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 16:10~16:20`, `Track: AIPrompt`)
  - 선행 메모 (`2026-04-18 10:27 KST`): 공통 helper + Gemini/OpenAI 공용 패킷 + OpenAI `analyze_target` 감사 필드 주입까지 반영 완료
- [ ] `[HolidayCarry0419] AIPrompt 작업 10 HOLDING hybrid 적용` 1차 결과 평가 / 확대 여부 판정 (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 16:20~16:30`, `Track: AIPrompt`)
  - 실행 메모: 휴일 재점검 기준 `2026-04-20`에는 `shadow-only 유지 / 확대 보류` 1차 판정을 우선한다.
  - 필수 관찰축: `holding_action_applied`, `holding_force_exit_triggered`, `holding_override_rule_version`, `FORCE_EXIT` shadow 표본, `trailing 충돌률`
  - 미충족 시 다음 액션: `2026-04-22 POSTCLOSE` 최종판정 항목으로 넘기고 보류 사유를 같은 제목으로 기록
- [ ] `[HolidayCarry0419] AIPrompt 작업 8 감사용 핵심값 3종 투입` 미완료 시 `사유 + 다음 실행시각` 기록 (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:40`, `Track: AIPrompt`)
  - 실행 메모: `buy_pressure_10t_sent`, `distance_from_day_high_pct_sent`, `intraday_range_pct_sent` 중 하나라도 확인되지 않으면 완료 처리 금지
  - 판정 기준: 값 주입 여부와 별도로 main runtime 감사 로그 3종이 모두 남아야 완료 후보로 본다
- [ ] `AIPrompt 작업 11 HOLDING critical 전용 경량 프롬프트 분리` 착수 (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 16:40~17:00`, `Track: AIPrompt`)
- [ ] `[VisibleResult0420] HOLDING shadow 1일차 missed_upside/capture_efficiency 판정 기준 고정` (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:10`, `Track: AIPrompt`)
- [ ] `[VisibleResult0420] 장후 리포트 우선지표 순서(거래수/퍼널/blocker/체결품질/missed_upside/손익) 준수 확인` (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 17:10~17:15`, `Track: Plan`)
- [ ] `[RiskSize0420] budget cap 1일차 효과 판정(거래수/퍼널/full vs partial fill/missed_upside)` (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 17:15~17:25`, `Track: ScalpingLogic`)
- [ ] `[RiskSize0420] 동적 튜닝 대상화 여부 확정(승격/보류+재시각)` (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 17:25~17:35`, `Track: Plan`)
- [ ] `[PerfRpt0420] 정기 성과측정보고서 첫 운영 업데이트` (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 17:35~17:45`, `Track: Plan`)
  - 판정 기준: `plan-korStockScanPerformanceOptimization.performance-report.md`에 `2026-04-20` 장후 실제값(`거래수/퍼널/blocker/체결품질/missed_upside/손익`)을 첫 운영본으로 반영
- [ ] `[Workorder0420] 실행 변경사항/성과보고 기준 문서를 workorder 소스 문맥에 연결` (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 17:45~17:50`, `Track: Plan`)
  - 실행 메모: 다음 `codex_daily_workorder` 생성 시 `execution-delta`, `performance-report`를 참조문서로 포함하도록 Source 문맥을 유지
- [ ] `[RCA0420] 07:30~09:30 서버 장애 구간 CPU/메모리/IO/프로세스 타임라인 확정` (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 17:50~18:00`, `Track: Plan`)
  - 실행 메모: `run_monitor_snapshot`/`bot_main` 동시실행 및 cron 충돌 여부를 분리 기록하고, 재발방지 항목(`락/타임아웃/시간대가드`)의 효과를 수치로 검증
- [x] `[PlanSync0420] 에이럭스 사례는 scale-in 단일 이슈로 단정하지 않고 4축 관찰(EntryGate/Latency/Liquidity/HoldingExit) 유지` (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 18:00~18:10`, `Track: Plan`) (`실행: 2026-04-20 10:18 KST`)
  - 판정: `확정`. 현재는 로직수정 없이 관찰축 유지.
  - 근거: 첫 거래는 `MISSED_UPSIDE`, 두 번째 거래는 `GOOD_EXIT`로 사후결과가 분리되어 단일 수량이슈로 환원 불가. `latency_block -> ALLOW_FALLBACK`, `blocked_liquidity`, `dynamic_strength_canary`를 독립 축으로 유지해야 원인 귀속 가능.
  - 다음 액션: `2026-04-21 POSTCLOSE`에 4축별 표본 누적과 `N_min/Δ_min/rollback trigger` 충족 여부를 먼저 판정하고, 충족 시에만 단일 축 canary 후보화.
- [ ] 미착수 시 `사유 + 다음 실행시각` 기록 (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 17:50~18:00`, `Track: AIPrompt`)

## 참고 문서

- [2026-04-19-stage2-todo-checklist.md](./2026-04-19-stage2-todo-checklist.md)
- [2026-04-19-aiprompt-task8-task10-holiday-recheck.md](./2026-04-19-aiprompt-task8-task10-holiday-recheck.md)
- [2026-04-17-stage2-todo-checklist.md](./2026-04-17-stage2-todo-checklist.md)
- [2026-04-17-midterm-tuning-performance-report.md](./2026-04-17-midterm-tuning-performance-report.md)
- [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md)
- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)
- [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md)
- [plan-korStockScanPerformanceOptimization.performance-report.md](./plan-korStockScanPerformanceOptimization.performance-report.md)
- [plan-korStockScanPerformanceOptimization.qna.md](./plan-korStockScanPerformanceOptimization.qna.md)

<!-- AUTO_SERVER_COMPARISON_START -->
### 본서버 vs songstockscan 자동 비교 (`2026-04-20 10:00:39`)

- 기준: `profit-derived metrics are excluded by default because fallback-normalized values such as NULL -> 0 can distort comparison`
- 상세 리포트: `data/report/server_comparison/server_comparison_2026-04-20.md`
- `Trade Review`: status=`ok`, differing_safe_metrics=`7`
  - holding_events local=1308 remote=0 delta=-1308.0; total_trades local=14 remote=1 delta=-13.0; entered_rows local=14 remote=1 delta=-13.0
- `Performance Tuning`: status=`ok`, differing_safe_metrics=`14`
  - holding_review_ms_p95 local=2866.0 remote=74603.0 delta=71737.0; gatekeeper_eval_ms_p95 local=30794.0 remote=13269.0 delta=-17525.0; gatekeeper_eval_ms_avg local=17085.54 remote=10369.44 delta=-6716.1
- `Post Sell Feedback`: status=`ok`, differing_safe_metrics=`2`
  - total_candidates local=13 remote=5 delta=-8.0; evaluated_candidates local=13 remote=5 delta=-8.0
- `Entry Pipeline Flow`: status=`ok`, differing_safe_metrics=`3`
  - total_events local=22081 remote=28445 delta=6364.0; blocked_stocks local=19 remote=22 delta=3.0; submitted_stocks local=1 remote=0 delta=-1.0
<!-- AUTO_SERVER_COMPARISON_END -->
